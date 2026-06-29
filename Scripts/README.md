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
| `gitutil.py` | Bot identity, "nothing to commit" guard, `[skip ci]` loop guard, push. |
| `payload.py` | Upload payload parse + base64 chunk reconstruction (original workflow semantics). |
| `cli.py` | Shared entrypoint helpers (repo/branch discovery, logging). |

## CLI entrypoints

| Script | Workflow | Key flags |
| --- | --- | --- |
| `upload_asset.py` | Upload asset | reads `ARTLIB_PAYLOAD` env |
| `build_index.py` | Asset Index | `--commit`, `--message`, `--root` |
| `validate_assets.py` | Validate Assets | `--root` (exit 1 on errors) |
| `optimize_repo.py` | Optimize Repository | `--commit`, `--root` |
| `generate_report.py` | Generate Reports | `--commit`, `--root` |
| `cleanup_repo.py` | Cleanup | `--commit`, `--root` |
| `repair_repo.py` | Repair Repository | `--commit`, `--thumbnails`, `--root` |

`--commit` stages, commits (with `[skip ci]`) and pushes; without it the script
only writes files, which is handy for local inspection.

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
