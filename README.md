# ArtLibrary

**ArtLibrary is the long-term, self-maintaining visual backend for an AI
assistant ("Lubot") — its permanent visual memory.** It is a Git-native Digital
Asset Management (DAM) system purpose-built for AI-generated media: every visual
is governed, hashed, described by metadata, indexed, and discoverable. The
repository is designed to absorb thousands of visuals over years without becoming
chaotic, and to keep itself consistent with near-zero manual maintenance.

The **primary consumer is another AI**. Machine-readability comes first; human
browsing second. An agent should be able to understand the whole library by
reading one file (`asset-index.json`) and fetch any visual by its raw URL.

> **New here?** Start with [`Studio.md`](Studio.md) (Lubot's production
> responsibilities), [`WORKFLOW.md`](WORKFLOW.md) (the request → review → upload
> loop), and the canonical style guide in
> [`StyleGuides/`](StyleGuides/Fantasy-Strategy-v1.md). This README documents the
> backend that stores the results.

---

## Table of contents

- [Principles](#principles)
- [Architecture: truth vs. derived](#architecture-truth-vs-derived)
- [Folder layout](#folder-layout)
- [Metadata](#metadata)
- [The upload lifecycle](#the-upload-lifecycle)
- [Workflows](#workflows)
- [Automation & self-healing](#automation--self-healing)
- [Indexing](#indexing)
- [Validation](#validation)
- [Repair & cleanup](#repair--cleanup)
- [Releases](#releases)
- [How Lubot (or an MCP server / API) uses this repo](#how-lubot-uses-this-repo)
- [Local development](#local-development)

---

## Principles

1. **Everything is indexed.** Every asset is always discoverable through
   `asset-index.json`.
2. **Everything has metadata.** An asset without metadata is incomplete;
   validation fails on it.
3. **Everything is reproducible.** Metadata preserves the generation context
   (prompt, generator, timestamps, hashes, dimensions, lineage).
4. **AI-first.** Large machine-readable indexes are the point, not an
   afterthought.
5. **Modular automation.** Many small workflows, one shared Python library, no
   duplicated logic.
6. **Not images-only.** The design treats images as today's case, not the only
   case — icons, illustrations, textures, SVG, PDF, and future 3D / animation
   frames are first-class.

## Architecture: truth vs. derived

There are exactly two kinds of file in the repository:

| Layer | Files | Edited by | Rebuildable? |
| --- | --- | --- | --- |
| **Source of truth** | the asset bytes + their embedded metadata (or a `*.metadata.json` sidecar fallback) | uploads / authors | no — this is the data |
| **Derived** | `asset-index.json`, `ASSET_INDEX.md`, `Metadata/all-metadata.json`, `Reports/latest-report.md`, thumbnails, favicons | automation only | yes — `Repair` rebuilds all of it from the assets alone |

**All logic lives in one Python package, [`Scripts/artlib/`](Scripts/).** Every
GitHub Actions workflow is a thin wrapper that installs dependencies and calls a
small CLI in `Scripts/`, which calls the library. A future MCP server, REST API,
or Lubot itself imports the **same** library — so behaviour can never diverge
between "what the workflow does" and "what an agent does".

## Folder layout

```
Assets/         Icons/        Illustrations/   Wallpapers/
Textures/       Generated/                       <- asset folders (walked)
Metadata/       all-metadata.json                <- derived aggregate
Reports/        latest-report.md                 <- derived health report
Scripts/        artlib/ + *.py CLIs              <- the library + entrypoints
.github/        workflows/ + actions/            <- automation
asset-index.json  ASSET_INDEX.md                 <- derived index (machine + human)
```

Asset "kind" is inferred from the folder (`Icons/` → `icon`, `Textures/` →
`texture`, …) when the author doesn't specify one, but **metadata, not folder
location, is authoritative**. You can put any asset anywhere and tag it.

## Metadata

Metadata travels **inside the asset** wherever the format allows, so the file is
self-describing and portable — a game can grab the file and read its own
metadata with no extra files to ship.

| Format | Where metadata is stored |
| --- | --- |
| PNG | iTXt text chunk keyed `artlibrary` |
| JPEG / WebP / TIFF | EXIF `ImageDescription` |
| SVG | a `<metadata id="artlibrary">` element (CDATA JSON) |
| PDF / other | `<asset>.metadata.json` **sidecar** fallback |

Embedding only writes text — pixels are never altered, so appearance is
preserved. The **authored** metadata schema (`schema_version` 1):

```jsonc
{
  "schema_version": 1,
  "kind": "icon",                       // asset type (not images-only)
  "title": "Medieval Castle",
  "description": "...",
  "prompt": "a medieval castle icon, flat style",
  "generator": "dall-e-3",              // model / tool that created it
  "created": "2026-06-29T12:00:00+00:00",
  "license": "CC0",
  "tags": ["fantasy", "building"],
  "original_filename": "castle.png",
  "collection": "Fantasy/Buildings",    // lineage: grouping
  "derived_from": null,                 // lineage: parent/version
  "embeddings": null                    // reserved for future semantic search
}
```

Unknown extra keys are **preserved and only warned about**, never rejected, so
the schema can grow without breaking old assets. The index adds computed
technical fields (`sha256`, `bytes`, `dimensions`, `github_url`, `raw_url`,
`thumbnail`) on top of this block. `sha256` is deliberately **not** embedded —
embedding changes the file, which would change its own hash.

### Naming conventions (defined once in `artlib/constants.py`)

| Thing | Pattern | Example |
| --- | --- | --- |
| Thumbnail | `<stem>.thumb.<ext>` (256×256) | `castle.thumb.png` |
| Favicon | `<stem>-<size>.png` (16/32/48) | `castle-32.png` |
| Sidecar (fallback) | `<asset>.metadata.json` | `doc.pdf.metadata.json` |

## The upload lifecycle

Uploads run through the **Upload asset** workflow
(`workflow_dispatch`) with a JSON payload. The caller (an agent/API) base64-
encodes the asset and splits it into `chunks` to stay within input limits.

```jsonc
{
  "branch": "main",
  "path": "Icons/castle.png",
  "commit_message": "Add medieval castle icon",
  "sha256": "<optional integrity hash>",
  "chunks": ["<base64 part 1>", "<base64 part 2>"],
  "metadata": {
    "title": "Medieval Castle",
    "prompt": "a medieval castle icon, flat style",
    "generator": "dall-e-3",
    "tags": ["fantasy", "building"],
    "license": "CC0"
  },
  "options": {
    "optimize": true,
    "thumbnail": true,
    "favicon": false,
    "allow_overwrite": false
  }
}
```

The workflow then, entirely via `Scripts/upload_asset.py`:

1. validates the payload and the target path (security boundary — no `..`, no
   absolute paths, restricted charset),
2. reconstructs the chunks and writes the file (honouring `allow_overwrite`),
3. verifies the SHA-256 if one was provided,
4. **optimizes** the asset (before embedding, so EXIF-stripping optimizers
   can't drop metadata),
5. **embeds** the authored metadata,
6. optionally generates a thumbnail and favicons,
7. rebuilds the index and report and **commits them together with the asset**,
   then pushes.

The index/report are rebuilt inline (step 7) rather than relying on the push to
trigger **Asset Index**: GitHub does not start new workflow runs from a push
made with the default `GITHUB_TOKEN`, so an upload must index itself to stay
consistent. The push-driven workflows still cover direct human/PAT pushes.

### Batch upload (preferred for multiple assets)

When Lubot generates several visuals at once, dispatching the single **Upload
asset** workflow N times is inefficient and fragile: N runs, N commits, N chances
to half-fail, and no single place to learn what happened. The **Upload assets
(batch)** workflow (`upload-assets-batch.yml`) takes one `payload` input and
uploads **every visual in one run and one commit**:

```jsonc
{
  "branch": "main",
  "commit_message": "Upload asset batch",
  "assets": [
    {
      "path": "Generated/testA.png",
      "sha256": "<optional integrity hash>",
      "chunks": ["<base64 part 1>", "<base64 part 2>"],
      "metadata": { "title": "testA", "prompt": "...", "generator": "Lubot",
                    "kind": "test-image", "tags": ["test"], "license": "internal-test" },
      "options": { "optimize": true, "thumbnail": true, "favicon": true,
                   "allow_overwrite": true }
    }
    // ... more assets
  ]
}
```

`branch` and `commit_message` are shared by the batch; everything else is
per-asset and uses the **exact same** schema as a single upload. Each asset is
processed independently (reconstruct → verify → optimize → embed metadata →
thumbnail/favicon); **a failing asset is recorded and skipped, never fatal to the
others**. After all assets, the index/report are rebuilt once, validation runs,
and everything is committed together. If any asset failed, the workflow still
commits the ones that succeeded but exits non-zero.

Single and batch share one implementation (`artlib.batch.process_upload`) — a
single upload is simply a batch of one — so there is no duplicated logic and the
two can never drift.

**Why batch is preferred for multiple generated visuals:** one dispatch instead of
N, one atomic commit instead of N, one index rebuild instead of N, and one
machine-readable result describing the whole set — so Lubot can dispatch once,
wait once, and return verified URLs for everything it generated.

### Upload result (machine-readable completion)

Every upload (single or batch) writes the same result in three places: the
durable, committed `Reports/latest-upload-result.json`, the run's
`$GITHUB_STEP_SUMMARY` (the Actions UI), and stdout. The shape:

```jsonc
{
  "status": "success",                 // "failure" if any asset failed
  "branch": "main",
  "commit_sha": "...",                 // the upload commit (see note below)
  "uploaded": [
    {
      "path": "Generated/testA.png",
      "sha256": "...",
      "github_url": "...",
      "raw_url": "...",                 // the CDN URL Lubot returns to the user
      "thumbnail": "Generated/testA.thumb.png",  // null if not generated
      "favicons": ["Generated/testA-16.png", "Generated/testA-32.png", "Generated/testA-48.png"],
      "metadata": "embedded"           // "embedded" or "sidecar"
    }
  ],
  "failed": [],                        // [{path, error}] for any that failed
  "index_updated": true,
  "report_updated": true,
  "validation": "success"              // "failure" if the repo failed validation
}
```

> **Note on `commit_sha`:** the committed copy of
> `Reports/latest-upload-result.json` necessarily has an empty `commit_sha` (a
> commit cannot contain its own hash). The authoritative SHA is emitted to stdout
> and the step summary after the commit is made.

### Verifying a completed upload

`Scripts/verify_upload.py` is the machine-verifiable completion check. After an
upload finishes (and the branch is pulled), it confirms the expected assets
really landed:

```bash
python Scripts/verify_upload.py \
  --expected Generated/testA.png \
  --expected Generated/testB.png \
  --expected Generated/testC.png
```

For each expected asset it checks: the file exists, `asset-index.json` and
`ASSET_INDEX.md` include it, `Reports/latest-upload-result.json` lists it, and any
thumbnail/favicons the upload reported were produced exist. It prints a JSON
report and exits non-zero if anything is missing.

## Workflows

| Workflow | File | Trigger | Does |
| --- | --- | --- | --- |
| **Upload asset** | `upload-binary-file.yml` | manual (payload) | reconstruct → verify → optimize → embed metadata → thumbnail/favicon → rebuild index/report → commit → result summary |
| **Upload assets (batch)** | `upload-assets-batch.yml` | manual (payload) | same as Upload asset, for **many assets in one run and one commit**; continues past a failed asset and reports each |
| **Asset Index** | `asset-index.yml` | push to asset dirs | rebuild `asset-index.json` + `ASSET_INDEX.md` + aggregate, commit |
| **Validate Assets** | `validate-assets.yml` | push + PR | fail on broken/missing metadata, invalid JSON, orphans; warn on duplicates |
| **Optimize Repository** | `optimize-repository.yml` | manual | losslessly optimize every asset, preserve metadata, commit savings |
| **Generate Reports** | `generate-reports.yml` | manual + weekly | write `Reports/latest-report.md` |
| **Cleanup** | `cleanup.yml` | manual | remove orphan metadata/thumbnails, rebuild index + report |
| **Repair Repository** | `repair-repository.yml` | manual | rebuild ALL derived state from assets, no asset loss |
| **Release** | `release.yml` | manual + tag `v*` | package ZIP + index + metadata as Release Assets |

System image tools (ImageMagick, optipng, jpegoptim, webp) are installed by a
single composite action, `.github/actions/setup-image-tools`, so the install
line exists in exactly one place.

## Automation & self-healing

The repository maintains itself, by two complementary paths:

- **Uploads index themselves.** The Upload workflows (single and batch) rebuild
  the index/report in the same run and commit them with the asset(s) (see above)
  — because a `GITHUB_TOKEN` push cannot trigger another workflow.
- **Direct pushes are picked up by triggers.** When a human or a PAT pushes to
  an asset folder, **Asset Index** regenerates the index/aggregate and commits
  it, and **Validate Assets** checks integrity. Pull requests always run
  **Validate Assets** regardless of token.

To prevent derived-file commits from re-triggering the pipeline forever:

- automated commits carry a `[skip ci]` marker,
- push-triggered workflows skip runs where `github.actor` is the bot.

So a human/agent commits once; the repository converges on its own.

## Indexing

`asset-index.json` is the authoritative machine-readable view. Each entry merges
the asset's authored metadata with computed `sha256`, `bytes`, `dimensions`,
URLs, and thumbnail path; the top level carries `asset_count`, `total_bytes`,
and a `duplicates` map (assets sharing a SHA-256). `ASSET_INDEX.md` is the human
mirror. `Metadata/all-metadata.json` is the flat array of every record for bulk
consumption.

## Validation

`Validate Assets` **fails** on: missing metadata, invalid metadata JSON,
metadata missing required identity (`kind`), orphan sidecars/thumbnails. It
**warns** (without failing) on: duplicate content and forward-compatible
oddities (unknown keys, empty governance fields). Duplicates are intentionally
non-fatal — an AI may keep the same image in multiple collections.

## Repair & cleanup

- **Cleanup** is conservative: it deletes only *orphans* (derived files whose
  parent asset is gone) and rebuilds the index/report. It never touches assets.
- **Repair** is the recovery hammer: it rebuilds *everything* derived —
  metadata (synthesising or migrating where needed), thumbnails, index,
  aggregate, report — from the asset bytes alone, **without deleting any asset**.

## Releases

The repository's raw URLs are the primary delivery channel — a client fetches
exactly the file it needs. The **Release** workflow is a convenience layer that
bundles all assets plus the index and aggregated metadata into a ZIP attached as
a GitHub Release Asset, for bulk/offline grab (e.g. a game pulling a whole pack).
Trigger it manually or by pushing a `v*` tag.

## How Lubot uses this repo

Today the intended interaction is:

> "Generate a medieval castle icon and save it under Icons, tagged fantasy."

Lubot generates the image and calls the **Upload asset** workflow with a payload
like the one above. The repository then optimizes, embeds metadata, indexes,
validates, and reports automatically — Lubot only needs the returned raw URL.

> Only **approved** visuals should reach this step. The full request → review →
> upload loop lives in [`WORKFLOW.md`](WORKFLOW.md); this section covers the
> upload mechanics it calls into.

When Lubot generates **several** visuals in one go, it uses the **Upload assets
(batch)** workflow instead: one dispatch, one commit, one
`Reports/latest-upload-result.json` describing the whole set. The end-to-end loop
is:

1. dispatch **Upload assets (batch)** with all generated visuals in one payload,
2. wait for the run to finish,
3. read `Reports/latest-upload-result.json` (or the run's stdout/step summary) for
   the per-asset `raw_url`s and overall `status`,
4. optionally run `Scripts/verify_upload.py --expected <path> ...` to
   machine-verify the visuals, index and result all agree,
5. return the verified raw URLs to the user.

Because all logic is in `artlib`, the same operations are available
in-process. A future MCP server or REST API would `import artlib` and call
`metadata`, `indexing`, `validation`, etc. directly — no shelling out to
workflows. Designed-for-later hooks already exist: the reserved `embeddings`
field (semantic / visual-similarity search), `collection` / `derived_from`
(lineage and version history), and `kind` (arbitrary asset types).

## Local development

```bash
pip install -r Scripts/requirements.txt
# optional, for optimization/thumbnails locally:
sudo apt-get install -y imagemagick optipng jpegoptim webp

# rebuild the index / report / validate against the working tree:
python Scripts/build_index.py
python Scripts/generate_report.py
python Scripts/validate_assets.py
```

See [`Scripts/README.md`](Scripts/README.md) for the library/module reference.
