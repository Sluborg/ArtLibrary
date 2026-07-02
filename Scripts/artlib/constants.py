"""Central constants for ArtLibrary.

Every naming convention, directory name, extension set, and generated-file
name lives here exactly once. All workflows and CLI entrypoints import these
so they cannot drift apart. If you need to change "what a thumbnail is named"
or "which folders hold assets", change it here and nowhere else.
"""

from __future__ import annotations

# --- Metadata schema -------------------------------------------------------

# Bump when the authored metadata shape changes in a backward-incompatible way.
# Readers tolerate older versions; `metadata.migrate_legacy` upgrades them.
SCHEMA_VERSION = 1

# Key used to store the embedded metadata JSON inside image containers
# (PNG text chunk name, EXIF/XMP marker, SVG <metadata> id, ...).
EMBED_KEY = "artlibrary"

# Sidecar suffix, used ONLY as a fallback for formats that cannot embed
# metadata in-band (PDF, raw binaries, future 3D formats, ...).
SIDECAR_SUFFIX = ".metadata.json"

# --- Naming conventions ----------------------------------------------------

# Thumbnails are written as "<stem>.thumb.<ext>" next to the asset.
THUMB_INFIX = ".thumb"
THUMB_SIZE = (256, 256)

# Favicons are written as "<stem>-<size>.png" next to the asset.
FAVICON_SIZES = (16, 32, 48)

# --- Directory layout ------------------------------------------------------

# Folders that hold real assets (walked by discovery).
ASSET_DIRS = (
    "Assets",
    "Icons",
    "Illustrations",
    "Wallpapers",
    "Textures",
    "Generated",
)

# Folders/files that are never assets (infrastructure & derived output).
# IngestStaging holds relay-staged blobs in transit (see INGEST_STAGING_DIR);
# ignoring it keeps the orphan-sidecar/thumbnail scanners and cleanup away
# from files that exist only between a relay PUT and the ingest run.
IGNORED_DIRS = frozenset(
    {".git", ".github", "Scripts", "Reports", "Metadata", "node_modules", "IngestStaging"}
)

# --- Generated (derived) artifacts -----------------------------------------

INDEX_JSON = "asset-index.json"
INDEX_MD = "ASSET_INDEX.md"
METADATA_DIR = "Metadata"
METADATA_AGGREGATE = "Metadata/all-metadata.json"
REPORTS_DIR = "Reports"
REPORT_MD = "Reports/latest-report.md"

# Machine-readable result of the most recent upload workflow run (single or
# batch). Always overwritten so it represents the latest upload. Lives under the
# ignored Reports/ dir so it is never treated as an asset.
UPLOAD_RESULT_JSON = "Reports/latest-upload-result.json"

# Machine-readable result of the most recent worklist registration run (rows
# added/skipped). Overwritten each effective run so a caller can verify what a
# dispatch did. Also lives under the ignored Reports/ dir.
WORKLIST_RESULT_JSON = "Reports/latest-worklist-result.json"

# Machine-readable result of the most recent image-ingest run. Committed on
# EVERY outcome (success / noop / failure) because the dispatch API only ever
# answers 204 — this file is the caller's sole confirmation channel. The
# echoed request_id is how a poller tells a fresh result from a stale one.
INGEST_RESULT_JSON = "Reports/latest-ingest-result.json"

# Staging area used by the relay fallback: bytes are PUT here via the contents
# API, then the ingest run moves them to their final asset path. Deliberately
# NOT in ASSET_DIRS so discovery/indexing/validation never see staged blobs.
INGEST_STAGING_DIR = "IngestStaging"

# Ingest download safety limits.
INGEST_MAX_BYTES = 30 * 1024 * 1024
# Pillow format name -> file extension for formats DALL·E / ChatGPT can emit.
INGEST_FORMATS = {"PNG": "png", "JPEG": "jpg", "WEBP": "webp"}

# Top-level derived files that must never be treated as assets.
DERIVED_FILES = frozenset({INDEX_JSON, INDEX_MD})

# --- Extension sets --------------------------------------------------------

# Raster image formats Pillow can open for dimensions/thumbnails/favicons.
RASTER_EXTENSIONS = frozenset(
    {"png", "jpg", "jpeg", "webp", "gif", "bmp", "tiff", "tif"}
)

# Vector/document formats we track but do not raster-process.
VECTOR_EXTENSIONS = frozenset({"svg"})
DOCUMENT_EXTENSIONS = frozenset({"pdf"})

# Everything we recognise as an asset. New AI-generated media types
# (3D refs, animation frames, sprites, ...) are added here over time.
ASSET_EXTENSIONS = (
    RASTER_EXTENSIONS
    | VECTOR_EXTENSIONS
    | DOCUMENT_EXTENSIONS
    | frozenset({"ico", "avif", "json", "txt", "md", "glb", "gltf", "obj"})
)

# Formats whose metadata can be embedded in-band without recompressing pixels
# (else we fall back to a sidecar). PNG re-encode is lossless, JPEG uses
# quality="keep", SVG is text. WebP/TIFF/GIF would require re-encoding, so they
# use sidecars. Authoritative check lives in imaging.can_embed().
EMBEDDABLE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "svg"})

# Formats we know how to losslessly optimize.
OPTIMIZABLE_EXTENSIONS = frozenset({"png", "jpg", "jpeg", "webp", "svg"})

# --- Asset "kind" taxonomy -------------------------------------------------

# Default kind inferred from the containing folder when the author does not
# supply one. Keeps the library navigable for an AI without forcing a schema.
DIR_TO_KIND = {
    "Icons": "icon",
    "Illustrations": "illustration",
    "Wallpapers": "wallpaper",
    "Textures": "texture",
    "Generated": "generated",
    "Assets": "asset",
}

DEFAULT_KIND = "asset"

# Identifies metadata/index records produced by this pipeline.
SOURCE = "github-actions-artlibrary"

# Git identity for automated commits.
BOT_NAME = "github-actions"
BOT_EMAIL = "github-actions@github.com"

# Marker appended to bot commits so push-triggered workflows can skip them.
SKIP_CI_MARKER = "[skip ci]"
