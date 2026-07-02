# Ingest relay (Cloudflare Worker) — Spike B fallback

Deploy this **only if** the direct-dispatch path fails — that is, if ChatGPT
will not populate `openaiFileIdRefs` when it is nested inside a
`repository_dispatch` `client_payload` (the "Spike B" verdict in
[`docs/INGEST.md`](../docs/INGEST.md)). If the direct path works, nothing in
this directory is used.

## What it does

The Worker becomes the Custom GPT Action endpoint (instead of
`api.github.com`). Flow per ingest:

1. Receives `POST /ingest` with **top-level** `openaiFileIdRefs` — the exact
   shape OpenAI documents — plus flat `slug/title/description/prompt/tags/
   collection/allow_overwrite/request_id`.
2. Fetches the signed `download_link` immediately. The Worker runs within
   seconds of ChatGPT minting the link, which structurally removes the
   5-minute-expiry risk that the GitHub-Actions-queue path carries.
3. Sanity-checks the bytes (PNG/JPEG/WEBP magic, 30 MB cap).
4. Stages them via the GitHub contents API as `IngestStaging/<request_id>.<ext>`
   (`[skip ci]`; the indexer ignores `IngestStaging/` by design).
5. Dispatches the `ingest-image` workflow with `source_path` pointing at the
   staged blob. The workflow runs the full optimize → metadata → thumbnail →
   index pipeline and **deletes the staged file in the same commit** that adds
   the final asset.
6. Returns a synchronous `200 {accepted, request_id, poll}` to ChatGPT — a
   real ack the pure-dispatch path can never give. The GPT then polls
   `GET /result` (the Worker proxies the committed
   `Reports/latest-ingest-result.json` through the contents API, so one
   Action server and one auth cover the whole loop) and matches `request_id`.

Cost: free tier (100k requests/day). Two commits per ingest (stage + final)
instead of one — the accepted cost of the fallback path.

## Deploy

```bash
cd relay
npx wrangler login                       # once
npx wrangler secret put GITHUB_PAT       # fine-grained PAT: Contents RW, Sluborg/ArtLibrary ONLY
npx wrangler secret put ARTLIB_SHARED_SECRET   # any long random string
npx wrangler deploy                      # prints https://artlib-ingest.<account>.workers.dev
```

Then switch the Lubot Action to
[`docs/lubot-action-relay.yaml`](../docs/lubot-action-relay.yaml), set its
server URL to the printed `workers.dev` URL, and set the Action auth to
API Key → custom header `X-Artlib-Key` → the shared secret value.

## Secrets handling

- `GITHUB_PAT` and `ARTLIB_SHARED_SECRET` live **only** in Worker secrets
  (`wrangler secret put`) and the ChatGPT Action auth field. Nothing in this
  repository ever contains them.
- The PAT is fine-grained and scoped to this single repository with Contents
  read/write — the minimum that covers the contents PUT, the dispatch POST,
  and the result-file GET.

## Rejected alternatives (why stage-then-dispatch)

- **Bytes through the dispatch payload / workflow inputs:** both are capped at
  64 KB total — a real image cannot fit. Dead end.
- **Worker PUTs the final asset directly + index rebuild:** skips the
  pipeline (optimize, in-band metadata, thumbnail, validation) and duplicates
  logic the repo already has in `artlib`. Staging keeps the Worker dumb and
  the pipeline authoritative.
- **Re-hosting via R2/presigned URL + `image_url` dispatch:** extra infra and
  another expiring URL for no gain over in-repo staging.
