# Scripts — the `artlib` library and CLI entrypoints

All ArtLibrary behaviour lives in the `artlib` package. The `*.py` files in this
folder are thin command-line wrappers that GitHub Actions invokes; each one only
parses arguments and delegates to the library. **Put logic in `artlib/`, never
in a workflow or a CLI wrapper.**

## Why one shared library

A workflow and an agent must behave identically. By keeping every operation in
`artlib`, a future MCP server, REST API, or the Lubot agent can `import artlib`
and perform exactly what the CI pipeline does — uploading, indexing, validating,
reporting — with no reimplementation and no drift.

```python
import artlib
index = artlib.indexing.build_index(".", "owner/repo", "main")
result = artlib.validation.validate_repository(".")
```

## Library modules (`artlib/`)

| Module | Responsibility |
| --- | --- |
| `constants.py` | The single home for naming conventions, folder layout, extension sets, schema version. Change a convention here and nowhere else. |
| `paths.py` | Derive sibling paths (thumbnail/favicon/sidecar); classify any file; **`validate_repo_path` — the path-traversal security boundary**. |
| `hashing.py` | Streamed SHA-256 over real bytes. |
| `urls.py` | Canonical GitHub web + raw URLs. |
| `imaging.py` | Pillow dimensions, thumbnails, favicons, and in-band metadata embed/read per format. Degrades gracefully on non-images. |
| `metadata.py` | The **only** reader/writer of asset metadata (embedded first, sidecar fallback). Builds the authored schema, enriches index records, migrates legacy sidecars, validates. |
| `discovery.py` | Walk the repo, yield real `Asset`s (never thumbnails/derived files), find orphans. |
| `dedupe.py` | Group/duplicate detection by content hash. |
| `optimize.py` | Lossless optimization shared by Upload + Optimize-Repository; re-embeds metadata after EXIF-stripping. |
| `indexing.py` | Build `asset-index.json`, `ASSET_INDEX.md`, `Metadata/all-metadata.json`. |
| `reporting.py` | Build and render `Reports/latest-report.md`. |
| `validation.py` | Structured `Result(errors, warnings)` for the push/PR gate. |
| `gitutil.py` | Bot identity, "nothing to commit" guard, `[skip ci]` loop guard, push, HEAD SHA, dirty-path check. |
| `payload.py` | Single + **batch** payload parse and base64 chunk reconstruction. |
| `batch.py` | **Upload orchestration shared by single + batch.** `process_one_asset` (write→verify→optimize→embed→thumbnail/favicon) and `process_upload` (loop assets, rebuild index/report, validate, commit once, emit result). A single upload is a batch of one. |
| `summary.py` | The upload result summary: builds the canonical dict, writes `Reports/latest-upload-result.json`, and writes the GitHub `$GITHUB_STEP_SUMMARY`. |
| `worklist.py` | **Append-only, lossless worklist-row registration.** Locates a target table (anchor or heading), splices `rows` in after its last data row (byte-preserving elsewhere), dedupes on slug, validates column count; writes `Reports/latest-worklist-result.json` + step summary. |
| `cli.py` | Shared entrypoint helpers (repo/branch discovery, logging). |

## CLI entrypoints

| Script | Workflow | Key flags |
| --- | --- | --- |
| `upload_asset.py` | Upload asset | reads `ARTLIB_PAYLOAD` env (single-asset payload) |
| `upload_assets_batch.py` | Upload assets (batch) | reads `ARTLIB_PAYLOAD` env (batch payload) |
| `register_worklist.py` | Register worklist row | reads `ARTLIB_WORKLIST` / `ARTLIB_ROWS` / `ARTLIB_TABLE` / `ARTLIB_NOTE` / `ARTLIB_MESSAGE` env |
| `verify_upload.py` | — (verification helper) | `--expected PATH` (repeatable), `--root` |
| `build_index.py` | Asset Index | `--commit`, `--message`, `--root` |
| `validate_assets.py` | Validate Assets | `--root` (exit 1 on errors) |
| `optimize_repo.py` | Optimize Repository | `--commit`, `--root` |
| `generate_report.py` | Generate Reports | `--commit`, `--root` |
| `cleanup_repo.py` | Cleanup | `--commit`, `--root` |
| `repair_repo.py` | Repair Repository | `--commit`, `--thumbnails`, `--root` |

`--commit` stages, commits (with `[skip ci]`) and pushes; without it the script
only writes files, which is handy for local inspection.

Both upload entrypoints share `artlib.batch.process_upload`, so single and batch
behave identically. Each writes a machine-readable result to
`Reports/latest-upload-result.json` and a `$GITHUB_STEP_SUMMARY`, prints the
result JSON to stdout, and exits non-zero if any asset failed. `verify_upload.py`
confirms a completed upload from outside the workflow:

```bash
python Scripts/verify_upload.py \
  --expected Generated/testA.png \
  --expected Generated/testB.png \
  --expected Generated/testC.png
```

It checks each asset exists, that the index (`asset-index.json` + `ASSET_INDEX.md`)
and `Reports/latest-upload-result.json` list it, and that any thumbnail/favicons
the upload reported were produced exist on disk. It prints a JSON report and
exits non-zero on any failure.

## Environment

The CLIs resolve the repository slug and branch from `GITHUB_REPOSITORY` /
`GITHUB_REF_NAME` (set by Actions) or `ARTLIB_BRANCH`, falling back to local
`git` config so they also run off-CI.

## Requirements

`pip install -r requirements.txt` (just Pillow). Optimization, thumbnails and
favicons additionally need the system tools installed by
`.github/actions/setup-image-tools` (ImageMagick, optipng, jpegoptim, webp);
the library degrades gracefully if they are absent.

## Extending

- **New asset type:** add its extension to the relevant set in `constants.py`
  (and a `DIR_TO_KIND` mapping if it gets its own folder). Discovery, indexing,
  validation and reporting pick it up automatically; image-only steps skip it.
- **New metadata field:** just start writing it. Unknown keys are preserved and
  warned, not rejected. Promote it to `AUTHORED_FIELDS` in `metadata.py` when it
  becomes standard, and bump `SCHEMA_VERSION` only on breaking changes.
- **Semantic search / embeddings:** the `embeddings` key is reserved in both the
  metadata block and the index top level — populate it without a schema change.
