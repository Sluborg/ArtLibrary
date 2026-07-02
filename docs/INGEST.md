# Autonomous image ingest — wiring, operations, and the Spike B protocol

How a Lubot-generated image travels from the ChatGPT sandbox into
`Assets/AssetReport/<slug>.png` with embedded metadata and a real `raw_url` —
autonomously, with no manual download/upload and no per-image API cost.

## The constraint set (why it's built this way)

- The **only** documented way a file leaves ChatGPT is a Custom GPT Action's
  outbound POST carrying the **`openaiFileIdRefs`** request parameter (up to 10
  conversation files, DALL·E images included). The Action's backend receives,
  per file, `{name, id, mime_type, download_link}` where **`download_link` is
  a signed URL valid for ~5 minutes** — the backend gets a pointer, not bytes.
- Dead ends, verified: base64 through an Action (the model truncates; payloads
  cap ≈ 75 KB of binary), the sandbox has no outbound network, model-visible
  image URLs are hallucinated, `sandbox:/mnt/data/...` has no public URL.
- GitHub's dispatch API (`POST /repos/Sluborg/ArtLibrary/dispatches`) accepts
  only `{event_type, client_payload}`, caps `client_payload` at **10 top-level
  properties / 64 KB**, and answers **204 with no run handle** — fire and
  forget. `repository_dispatch` only triggers workflows on the default branch.
- `openaiFileIdRefs` auto-population is known to be flaky — the model
  sometimes calls the Action without attaching the file. The pipeline signals
  this precisely (`refs_empty`) so the GPT can regenerate and resend.

## Architecture

**LIVE (confirmed 2026-07-02): Cloudflare Worker relay, not direct dispatch.**
Spike B proved ChatGPT does not substitute a real `download_link` into a
*nested* `openaiFileIdRefs` (see verdict below), so the Worker — which
receives the refs at the top level, the only shape that works — is the
production path, not a fallback.

```
Lubot (Custom GPT, relay Action)
  │  POST https://artlib-ingest.<account>.workers.dev/ingest
  │  auth: X-Artlib-Key header
  │  { openaiFileIdRefs: [...],   <- TOP-LEVEL: this is what gets substituted
  │    slug, title, description, prompt, tags, collection,
  │    request_id, allow_overwrite, branch }
  ▼
relay/worker.js  (Cloudflare Worker)
  │  fetch the signed download_link immediately (seconds, not minutes)
  │  validate magic bytes / size
  │  PUT /repos/.../contents/IngestStaging/<request_id>.<ext>  (contents API)
  │  POST /repos/.../dispatches  { event_type: "ingest-image",
  │                                client_payload: { source_path, asset, ... } }
  ▼
ingest-image.yml  (repository_dispatch, on main)
  │  Scripts/ingest_image.py -> artlib.ingest.run_ingest
  │    read staged bytes (no download, no expiry — already fetched by the Worker)
  │    validate (PNG/JPEG/WEBP, 30 MB cap, slug regex, optional sha256)
  │    dedupe   (embedded source_sha256 -> re-ingest of same bytes = noop)
  │    reuse artlib.batch.process_upload:
  │      optimize -> embed metadata (PNG iTXt) -> thumbnail ->
  │      rebuild asset-index.json / ASSET_INDEX.md / Metadata aggregate ->
  │      validate -> ONE commit (GITHUB_TOKEN) -> push (deletes the staged blob)
  ▼
Assets/AssetReport/<slug>.png  + index entry with a real raw_url
Reports/latest-ingest-result.json  (committed on EVERY outcome)
```

Deploy details: Worker `artlib-ingest`, deployed via Cloudflare's
GitHub-connected build reading the root [`wrangler.toml`](../wrangler.toml)
(→ `relay/worker.js`); secrets `GITHUB_PAT` and `ARTLIB_SHARED_SECRET` set in
the Worker's dashboard, never committed. Full deploy notes:
[`../relay/README.md`](../relay/README.md).

**Superseded (kept for reference / re-testable):** the direct-dispatch path
below, where Lubot's GitHub Action itself carried `openaiFileIdRefs` nested
inside `client_payload`. This is what Spike B tested and disproved — the
`ingest-image` workflow still supports it (`image_url`/`openaiFileIdRefs`
inputs both still work), but Lubot's Action no longer sends it this way.

```
Lubot (Custom GPT, direct GitHub Action)
  │  POST /repos/Sluborg/ArtLibrary/dispatches      auth: fine-grained PAT
  │  { event_type: "ingest-image",
  │    client_payload: { openaiFileIdRefs: [...],   <- NOT substituted when nested
  │                      asset: {slug, title, ...},
  │                      request_id, allow_overwrite, branch } }
  ▼
ingest-image.yml  (same workflow, same pipeline as above)
```

## Secrets and auth

| Credential | Lives in | Used for |
| --- | --- | --- |
| Fine-grained PAT — **Contents: Read and write**, repository access **only `Sluborg/ArtLibrary`** | The ChatGPT Action auth field (API Key → Bearer). If the Worker fallback is deployed: also a Worker secret via `wrangler secret put GITHUB_PAT`. | The dispatch POST (write) and result polling (read). Lubot already dispatches `register-worklist`, so this PAT likely already exists — reuse it. |
| `ARTLIB_SHARED_SECRET` (Worker fallback only) | Worker secret + the Action's `X-Artlib-Key` header | Authenticating the GPT to the Worker |

**Nothing is committed to this repository.** The workflow itself runs on the
default `GITHUB_TOKEN` (`permissions: contents: write`) — no repo secrets need
creating.

## The dispatch contract

```jsonc
{
  "event_type": "ingest-image",
  "client_payload": {
    "openaiFileIdRefs": ["<populated by ChatGPT>"],   // OR "image_url": "https://..."
                                                      // OR "source_path": "IngestStaging/..."
    "asset": {
      "slug": "ui-button-primary-stamp",   // required; lowercase kebab-case
      "title": "Primary Stamp Button",
      "description": "...",
      "prompt": "...",                     // provenance
      "tags": ["ui", "button"],
      "kind": "",                          // optional; defaults from folder -> "asset"
      "collection": "AssetReport",         // default
      "sha256": ""                         // optional integrity check of ORIGINAL bytes
    },
    "allow_overwrite": false,
    "request_id": "ui-button-primary-stamp-20260702-1",  // fresh per attempt
    "branch": "main"
  }
}
```

Nesting under `asset` keeps `client_payload` at ≤ 6 top-level properties (the
API caps it at 10). The same fields exist as `workflow_dispatch` inputs for
manual/testing use — both trigger paths feed identical `ARTLIB_*` env to the
same script.

Manual test from a shell (this is also the post-merge Spike A confirmation):

```bash
curl -sS -X POST https://api.github.com/repos/Sluborg/ArtLibrary/dispatches \
  -H "Authorization: Bearer $PAT" -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"ingest-image","client_payload":{
        "image_url":"https://raw.githubusercontent.com/Sluborg/ArtLibrary/main/Illustrations/AssetReport/map-overworld.png",
        "asset":{"slug":"test-dispatch-proof","title":"Dispatch proof"},
        "request_id":"proof-1"}}'
# expect HTTP 204; then watch the Actions tab / poll the result file
```

## Observability — how a fire-and-forget caller learns the outcome

The dispatch API returns 204 and nothing else, so the run commits
**`Reports/latest-ingest-result.json` on every outcome**:

```jsonc
{
  "status": "success" | "noop" | "failure",
  "request_id": "...",        // echoed verbatim — the freshness check
  "error_code": null | "...", // see table below
  "error": "human-readable message",
  "slug": "...", "path": "Assets/AssetReport/....png",
  "raw_url": "...", "github_url": "...",
  "sha256": "...",            // committed file (post-optimize/embed)
  "source_sha256": "...",     // ORIGINAL downloaded bytes (dedupe key)
  "attempts": 1, "run_url": "https://github.com/.../actions/runs/<id>", ...
}
```

Lubot's polling loop (encode in the GPT instructions):

1. Send a **fresh `request_id`** per attempt (e.g. `<slug>-<timestamp>`).
2. After the 204, wait ~90 s, then call `getIngestResult`
   (`GET /repos/Sluborg/ArtLibrary/contents/Reports/latest-ingest-result.json`
   — the **contents API**, deliberately not `raw.githubusercontent.com`, whose
   CDN caches ~5 minutes and would routinely return the previous result).
3. `request_id` mismatch → the run hasn't finished (or never started): wait
   45 s and retry, up to 4 polls (~4.5 min — a typical run takes 60–120 s).
4. Match + `success`/`noop` → report the `raw_url`. Match + `failure` → act on
   `error_code`. No match after 4 polls → the dispatch never started a run;
   check the Actions tab.

### Error codes

| `error_code` | Meaning | Lubot's action |
| --- | --- | --- |
| `refs_empty` | ChatGPT called the Action without attaching the file (the known flakiness), and no `image_url` was given | Regenerate the image, resend with a new `request_id` |
| `link_expired` | The signed download link answered 401/403/404/410 — dead, no retry can help | Regenerate + resend (links die ~5 min after minting) |
| `download_failed` | Transient network/5xx failure survived 4 fast attempts | Resend; if persistent, check the run log |
| `too_large` / `not_an_image` / `unsupported_format` | Bytes failed validation (30 MB cap; PNG/JPEG/WEBP only) | Regenerate |
| `sha256_mismatch` | Caller-supplied hash didn't match the downloaded bytes | Resend / drop the sha256 field |
| `bad_slug` / `bad_request` | Slug not lowercase-kebab, bad collection, or no source given | Fix the payload |
| `exists_conflict` | Slug already exists with **different** content and `allow_overwrite` is false | Confirm intent, resend with `allow_overwrite: true` |
| `pipeline_failed` | Rare in-pipeline error after a good download (run log has details) | Check `run_url` |

Re-ingesting **identical** bytes for an existing slug is not an error: the run
reports `status: "noop"` and points at the existing asset (dedupe key: the
original bytes' hash, stamped into the embedded metadata as `source_sha256` —
the on-disk file's own hash changes when metadata is embedded, so it can't be
compared directly).

### Residual blind spots (accepted + documented)

- A dispatch that dies **before checkout** (bad payload at the API level, a
  workflow-file error) commits nothing — the poll then keeps returning the
  *previous* `request_id`. That staleness IS the signal; the Actions tab is
  the fallback channel.
- The result file is last-writer-wins. Concurrent ingests are serialized per
  branch by the workflow's `concurrency` group, so a poller can still see a
  *newer* run's result if it dispatches twice quickly — always match
  `request_id`, never assume.

## The 5-minute window (risk & mitigation)

The `download_link` dies ~5 minutes after ChatGPT mints it, and the Actions
queue eats an unknown slice before `ingest_image.py` even starts. Mitigations:
the download starts as the job's first real step after checkout/deps; retries
are fast and bounded (4 attempts over ~17 s — slow backoff would outlive the
link anyway); expired-link statuses fail immediately as `link_expired` with a
"regenerate and resend" instruction. Typical queue latency on this repo is
seconds, so the window holds in practice — but a cold-cache runner spike can
lose a link; the retry-by-resend loop (fresh link each time) is the answer.

If this proves flaky in practice, the Worker fallback removes the risk
entirely (it fetches within seconds of minting), even if Spike B succeeds.

## Spike B — will ChatGPT populate `openaiFileIdRefs` nested in `client_payload`?

> **VERDICT (2026-07-02): NO. Direct-dispatch nesting does not work — the
> Worker relay is the production path, confirmed working end to end.**
>
> Negative half: two live attempts (request_ids `spike-b-1`, `spike-b-2`,
> [run 28603160619](https://github.com/Sluborg/ArtLibrary/actions/runs/28603160619))
> reached the workflow with a nested ref present but **unsubstituted**: the
> model wrote the raw file id (`file_0000...`) on the first attempt and the
> sandbox path (`/mnt/data/...`) on the second — never a signed
> `download_link`. The platform's link-substitution only engages for a
> top-level `openaiFileIdRefs`, confirming the direct-dispatch variant cannot
> carry images.
>
> Positive half: the Worker relay (`../relay/`, deployed via Cloudflare's
> GitHub-connected build against the root `wrangler.toml`) with
> `docs/lubot-action-relay.yaml` was then wired up and tested — request_id
> `spike-b-3` returned `status: success`, `source: "staging"`, and a working
> `raw_url` ([run 28613695557](https://github.com/Sluborg/ArtLibrary/actions/runs/28613695557),
> asset committed in `23194f3`). **This is the standing architecture**: the
> GitHub Action keeps `getFileContent`/`getAuthenticatedUser`/etc. for repo
> reads and the worklist workflows; the separate relay Action
> (`lubot-action-relay.yaml`, auth header `X-Artlib-Key`) is the only path
> that carries images. The protocol below is retained for re-testing if
> OpenAI ever changes the nested-substitution behavior.

OpenAI documents `openaiFileIdRefs` only as a **top-level** request-body
property. GitHub's dispatch API allows nothing at the top level except
`event_type`/`client_payload`. Whether ChatGPT populates the parameter one
level deep is **undocumented and only testable live** — this is the one thing
code cannot decide.

**Protocol (run in ChatGPT, ~10 minutes):**

1. Merge this PR (the workflow must be on `main` for `repository_dispatch`).
2. In Lubot → Configure → Actions, add
   [`lubot-action-dispatch.yaml`](lubot-action-dispatch.yaml) (Variant 1).
   Auth: API Key → Bearer → the PAT.
3. Prompt: *"Generate a small test image of a red wax seal. Then send it to
   ArtLibrary with slug `test-spike-b`, request_id `spike-b-1`."*
4. Read the verdict:

| Observation | Verdict |
| --- | --- |
| Run fires, result file: `status: success`, real `raw_url` | **Nesting works — all-GitHub relay wins. Done; no Worker needed.** |
| Run fires, result file: `error_code: refs_empty` | ChatGPT dropped the nested refs → **deploy the Worker fallback** ([`../relay/README.md`](../relay/README.md)), switch the Action to [`lubot-action-relay.yaml`](lubot-action-relay.yaml) |
| No run at all (poll stays stale, Actions tab empty) | ChatGPT refused/stripped the call → same verdict: **Worker fallback** |
| `link_expired` | Not a verdict — the link aged out (long chat before confirming). Retry the prompt fresh. |

The probe is cheap to repeat; `refs_empty` on 2–3 consecutive attempts is a
reliable negative given the documented flakiness baseline.

## Troubleshooting — debug layer by layer

An ingest crosses five layers; each fails differently. Work top-down and stop
at the first layer that misbehaves.

**Layer 0 — what did Lubot actually send?** Lubot's own Pre-Flight shows the
payload before the call — check `event_type: "ingest-image"` and the
`client_payload` structure there. Caveat: `openaiFileIdRefs` is populated by
ChatGPT *at call time*, not by the model, so the preview may legitimately show
it empty or as a placeholder — an empty preview is NOT proof it wasn't sent.
After a failure, ask Lubot: *"Show me the exact JSON body of the last
ingestImage call and the HTTP status you received."*

**Layer 1 — the dispatch call itself (Lubot reports a non-204).**
- `401` — PAT invalid/expired. Recreate it, update the Action auth.
- `403`/`404` — token can't see the repo: fine-grained PAT must have
  repository access to `Sluborg/ArtLibrary` with **Contents: Read and write**.
- `422` — payload shape: `client_payload` over 10 top-level properties, or
  malformed JSON. Compare against the contract above.

**Layer 2 — 204 received but no run appears.** Check the
[Actions tab](https://github.com/Sluborg/ArtLibrary/actions) filtered to
"Ingest image". No run means GitHub accepted but nothing listened:
`event_type` misspelled (must be exactly `ingest-image`), or the workflow file
is missing from `main` (`repository_dispatch` only triggers workflows on the
default branch). Sanity-check the trigger independently of ChatGPT with the
one-line `curl` from "The dispatch contract" — if the curl fires a run and
Lubot doesn't, the problem is on the ChatGPT side by elimination.

**Layer 3 — run appears but is red / result says failure.** Open the run: the
"Ingest image" step log prints the download attempts, validation, and the
final result JSON. Match `error_code` against the table above. The committed
`Reports/latest-ingest-result.json` carries the same info plus `run_url`.
Specifically for `refs_empty`: the file wasn't attached to the call — the
known ChatGPT flakiness (retry) or, if it happens on every attempt, the
Spike B negative verdict (deploy `relay/`).

**Layer 4 — run green but Lubot reports "no match" / stale request_id.**
The run finished after Lubot gave up (slow runner — just ask it to poll once
more), or Lubot polled wrong. It must GET
`/repos/Sluborg/ArtLibrary/contents/Reports/latest-ingest-result.json`
(the contents API, base64-decode `content`) — polling the raw URL instead
returns a cached copy for up to ~5 minutes. Verify by opening the
[file on GitHub](https://github.com/Sluborg/ArtLibrary/blob/main/Reports/latest-ingest-result.json)
and comparing `request_id` yourself.

**Layer 5 — success reported but the asset looks wrong.** `raw_url` 404s:
check the file exists under `Assets/AssetReport/` on `main` (the commit named
`Ingest <slug> [request <id>]`). Viewer doesn't show it: hard-refresh
(the manifest fetch is no-store, but the thumbnail may be CDN-cached).
Unexpected `noop`: identical bytes were already ingested for that slug —
that's the dedupe working; use a different image or `allow_overwrite`.

When stuck, capture three things and hand them to a Claude session: the run
URL, the decoded result JSON, and Lubot's reported request body. That triple
localizes any failure in this pipeline.

## Post-merge checklist (operator)

1. ☑ Spike A confirmation: direct dispatch with a public image URL lands a
   committed, indexed asset with a matching result file (proven pre-merge on
   the feature branch, `spike-a-1`..`spike-a-5c`).
2. ☑ Spike B: direct-dispatch nesting does **not** substitute real download
   links (`spike-b-1`, `spike-b-2`) → Worker relay deployed and confirmed
   working end to end (`spike-b-3`, `status: success`). Verdict recorded above.
3. ☑ Worker relay is live: Cloudflare Worker `artlib-ingest`, GitHub-connected
   build from this repo's root `wrangler.toml` → `relay/worker.js`, secrets
   (`GITHUB_PAT`, `ARTLIB_SHARED_SECRET`) set in the Worker's dashboard.
   Lubot's GitHub Action no longer carries `ingestImage`; the relay Action
   (`lubot-action-relay.yaml`) does, auth header `X-Artlib-Key`.
4. ☐ Delete the test assets (`test-spike-b`, and `test-dispatch-proof` if it
   was created) via a normal commit, or re-ingest real art over them with
   `allow_overwrite`.
5. ☐ Optional: Settings → Pages → deploy `main /docs` to serve the viewer.

## Spike A evidence (feature branch, pre-merge)

The full matrix ran on this PR's branch via a temporary push-triggered harness
(the identical `ARTLIB_*` → `ingest_image.py` code path; the true
`repository_dispatch` trigger can only exist post-merge — step 1 above):

| Test | Result |
| --- | --- |
| Happy path (`image_url`, slug `test-ingest-smoke`) | ✅ committed asset + thumbnail + index entry with raw_url; result `success`, `request_id` echoed — [run 28585394301](https://github.com/Sluborg/ArtLibrary/actions/runs/28585394301) |
| Re-dispatch, identical bytes | ✅ `noop`, no asset/index change — [run 28585624995](https://github.com/Sluborg/ArtLibrary/actions/runs/28585624995) |
| Same slug, different image, no overwrite | ✅ `failure/exists_conflict`, result committed, asset untouched |
| Same + `allow_overwrite: true` | ✅ replaced, index updated |
| Non-image URL / dead URL / unreachable host | ✅ `not_an_image` / `link_expired` (single attempt) / `download_failed` (4 attempts) |

Smoke-test artifacts were removed before review; the index was rebuilt clean.
