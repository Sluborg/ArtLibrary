/**
 * ArtLibrary ingest relay — Cloudflare Worker (Spike B fallback).
 *
 * Deploy ONLY if the direct-dispatch path fails, i.e. ChatGPT will not
 * populate `openaiFileIdRefs` nested inside a repository_dispatch
 * `client_payload` (see docs/INGEST.md, "Spike B"). This Worker is then the
 * Custom GPT Action endpoint instead: it receives `openaiFileIdRefs` at the
 * TOP LEVEL of the request body (the shape OpenAI documents), fetches the
 * signed download_link immediately — within seconds of ChatGPT minting it,
 * which structurally defuses the 5-minute expiry — stages the bytes into the
 * repo via the contents API, and dispatches the ingest-image workflow with a
 * `source_path` pointing at the staged blob. The workflow then runs the full
 * optimize/metadata/thumbnail/index pipeline and deletes the staged file in
 * the same commit that adds the asset (or in the result-only commit when the
 * ingest ends in noop/failure).
 *
 * Validation mirrors the workflow side (slug/collection rules from
 * Scripts/artlib/ingest.py) so a bad request is rejected BEFORE a blob is
 * staged — otherwise every downstream rejection would first commit a blob.
 *
 * Secrets (wrangler secret put <NAME>):
 *   GITHUB_PAT           fine-grained PAT, Contents: Read and write,
 *                        Sluborg/ArtLibrary only. Never committed.
 *   ARTLIB_SHARED_SECRET the API key the GPT Action sends as X-Artlib-Key.
 */

const REPO = "Sluborg/ArtLibrary";
const STAGING_DIR = "IngestStaging";
const MAX_BYTES = 30 * 1024 * 1024;

// Mirror Scripts/artlib/ingest.py: SLUG_RE / COLLECTION_RE / branch charset.
const SLUG_RE = /^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$/;
const COLLECTION_RE = /^[A-Za-z0-9_-]{1,64}$/;
const BRANCH_RE = /^[A-Za-z0-9._/-]+$/;

// Magic bytes for the formats the ingest pipeline accepts.
const SIGNATURES = [
  { ext: "png", bytes: [0x89, 0x50, 0x4e, 0x47] },
  { ext: "jpg", bytes: [0xff, 0xd8, 0xff] },
  { ext: "webp", bytes: [0x52, 0x49, 0x46, 0x46] }, // RIFF (checked with WEBP below)
];

function json(status, body) {
  return new Response(JSON.stringify(body, null, 2), {
    status,
    headers: { "content-type": "application/json" },
  });
}

function detectExt(buf) {
  const view = new Uint8Array(buf);
  for (const sig of SIGNATURES) {
    if (sig.bytes.every((b, i) => view[i] === b)) {
      if (sig.ext === "webp") {
        const tag = String.fromCharCode(...view.slice(8, 12));
        if (tag !== "WEBP") continue;
      }
      return sig.ext;
    }
  }
  return null;
}

function base64(buf) {
  const view = new Uint8Array(buf);
  if (typeof view.toBase64 === "function") return view.toBase64(); // native, fast
  const parts = [];
  const chunk = 0x8000;
  for (let i = 0; i < view.length; i += chunk) {
    parts.push(String.fromCharCode(...view.subarray(i, i + chunk)));
  }
  return btoa(parts.join(""));
}

async function github(env, method, path, body) {
  const resp = await fetch(`https://api.github.com${path}`, {
    method,
    headers: {
      authorization: `Bearer ${env.GITHUB_PAT}`,
      accept: "application/vnd.github+json",
      "user-agent": "artlibrary-ingest-relay",
      "x-github-api-version": "2022-11-28",
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`GitHub ${method} ${path} -> ${resp.status}: ${text.slice(0, 300)}`);
  }
  return resp;
}

// The contents API requires the current blob sha to overwrite an existing
// path (else 422) — a retry that reuses a request_id would otherwise 500.
async function stagingSha(env, path, branch) {
  const resp = await fetch(
    `https://api.github.com/repos/${REPO}/contents/${path}?ref=${encodeURIComponent(branch)}`,
    {
      headers: {
        authorization: `Bearer ${env.GITHUB_PAT}`,
        accept: "application/vnd.github+json",
        "user-agent": "artlibrary-ingest-relay",
      },
    }
  );
  if (!resp.ok) return undefined;
  const data = await resp.json();
  return data.sha;
}

async function handleIngest(request, env) {
  let body;
  try {
    body = await request.json();
  } catch {
    return json(400, { error_code: "bad_request", error: "request body must be JSON" });
  }

  // Tolerate a bare string/object where an array is documented.
  let refs = body.openaiFileIdRefs;
  if (refs && !Array.isArray(refs)) refs = [refs];
  const first = (refs || [])[0];
  const link = typeof first === "string" ? first : first && first.download_link;
  if (!link) {
    // The documented ChatGPT flakiness: the model called the action without
    // attaching the file. Tell it precisely, so it regenerates and resends.
    return json(422, {
      error_code: "refs_empty",
      error:
        "openaiFileIdRefs was empty — the image was not attached; " +
        "regenerate the image and call the action again",
    });
  }

  // Reject bad requests BEFORE staging a blob (mirrors the workflow's rules).
  const slug = String(body.slug || "").toLowerCase();
  const collection = String(body.collection || "AssetReport");
  const branch = String(body.branch || "main");
  if (!SLUG_RE.test(slug)) {
    return json(422, {
      error_code: "bad_slug",
      error: `slug ${JSON.stringify(body.slug || "")} must be lowercase kebab-case (a-z, 0-9, single hyphens, 1-64 chars)`,
    });
  }
  if (!COLLECTION_RE.test(collection) || !BRANCH_RE.test(branch)) {
    return json(422, { error_code: "bad_request", error: "invalid collection or branch" });
  }
  // request_id becomes a repo path segment — keep it to the safe charset.
  let requestId = String(body.request_id || `${Date.now()}-${slug}`)
    .replace(/[^A-Za-z0-9._-]/g, "-")
    .slice(0, 64);
  if (!requestId.replace(/[.-]/g, "")) requestId = `${Date.now()}-${slug}`.slice(0, 64);

  // Fetch inside the 5-minute window — we are within seconds of minting.
  const imgResp = await fetch(link);
  if (!imgResp.ok) {
    return json(502, {
      error_code: "link_expired",
      error: `download_link fetch failed with HTTP ${imgResp.status}`,
    });
  }
  const buf = await imgResp.arrayBuffer();
  if (buf.byteLength === 0 || buf.byteLength > MAX_BYTES) {
    return json(422, {
      error_code: buf.byteLength ? "too_large" : "download_failed",
      error: `image is ${buf.byteLength} bytes (limit ${MAX_BYTES})`,
    });
  }
  const ext = detectExt(buf);
  if (!ext) {
    return json(422, {
      error_code: "not_an_image",
      error: "payload does not look like PNG/JPEG/WEBP",
    });
  }

  const stagedPath = `${STAGING_DIR}/${requestId}.${ext}`;

  // Stage the bytes (contents API handles up to ~100MB; DALL·E images are
  // a few MB). IngestStaging/ is ignored by the indexer by design.
  await github(env, "PUT", `/repos/${REPO}/contents/${stagedPath}`, {
    message: `Stage ingest ${requestId} [skip ci]`,
    content: base64(buf),
    branch,
    sha: await stagingSha(env, stagedPath, branch), // present only on re-stage
  });

  // Hand off to the ingest workflow: it moves the blob to its final asset
  // path, runs the full pipeline, and deletes the staged file.
  await github(env, "POST", `/repos/${REPO}/dispatches`, {
    event_type: "ingest-image",
    client_payload: {
      source_path: stagedPath,
      asset: {
        slug,
        title: body.title || "",
        description: body.description || "",
        prompt: body.prompt || "",
        tags: body.tags || [],
        kind: body.kind || "",
        collection,
        sha256: body.sha256 || "",
      },
      allow_overwrite: !!body.allow_overwrite,
      request_id: requestId,
      branch,
    },
  });

  // A real synchronous ack — something the pure-dispatch path can never
  // give. The GPT then polls GET /result and matches request_id.
  return json(200, { accepted: true, request_id: requestId, staged: stagedPath });
}

async function handleResult(request, env) {
  const ref = new URL(request.url).searchParams.get("ref") || "main";
  if (!BRANCH_RE.test(ref)) {
    return json(422, { error_code: "bad_request", error: "invalid ref" });
  }
  const resp = await github(
    env,
    "GET",
    `/repos/${REPO}/contents/Reports/latest-ingest-result.json?ref=${encodeURIComponent(ref)}`
  );
  const data = await resp.json();
  return json(200, JSON.parse(atob(data.content.replace(/\n/g, ""))));
}

export default {
  async fetch(request, env) {
    if (request.headers.get("x-artlib-key") !== env.ARTLIB_SHARED_SECRET) {
      return json(401, { error: "bad or missing X-Artlib-Key" });
    }
    const path = new URL(request.url).pathname;
    try {
      if (request.method === "GET" && path === "/result") {
        return await handleResult(request, env);
      }
      if (request.method === "POST" && path === "/ingest") {
        return await handleIngest(request, env);
      }
    } catch (err) {
      // Structured error instead of an opaque 500 — the GPT reads this.
      return json(502, { error_code: "relay_failed", error: String(err).slice(0, 400) });
    }
    return json(404, { error: "POST /ingest or GET /result only" });
  },
};
