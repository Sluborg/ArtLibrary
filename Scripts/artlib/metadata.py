"""The single reader/writer of asset metadata.

Metadata lives *inside* the asset where the format allows (see ``imaging``);
otherwise it falls back to a ``<asset>.metadata.json`` sidecar. Nothing else in
the codebase reads or writes metadata directly — every workflow goes through
this facade so the storage decision (embedded vs sidecar) lives in one place.

Two shapes exist:
  * **authored** metadata — what a human/AI supplies plus a few stamped fields
    (schema_version, kind, created, original_filename). This is what we store.
  * **index record** — authored metadata enriched with freshly computed
    technical fields (sha256, bytes, dimensions, urls, thumbnail). This is
    derived at index time and never stored in the asset (sha would be circular).
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from . import constants, imaging, urls
from .paths import ext_of, sidecar_path, stem_of

# Authored fields the schema defines. Unknown extra keys are preserved and only
# warned about (forward compatibility) — never rejected.
AUTHORED_FIELDS = (
    "schema_version",
    "kind",
    "title",
    "description",
    "prompt",
    "generator",
    "created",
    "license",
    "tags",
    "original_filename",
    "collection",
    "derived_from",
)

# Fields a human/AI may meaningfully supply at upload time.
USER_FIELDS = (
    "kind",
    "title",
    "description",
    "prompt",
    "generator",
    "license",
    "tags",
    "collection",
    "derived_from",
)


def supports_embedding(path: str) -> bool:
    return imaging.can_embed(ext_of(path))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def infer_kind(rel_path: str, supplied: str | None) -> str:
    if supplied:
        return supplied
    top = rel_path.replace("\\", "/").split("/", 1)[0]
    return constants.DIR_TO_KIND.get(top, constants.DEFAULT_KIND)


def build_authored_metadata(
    rel_path: str,
    user_meta: dict | None = None,
    original_filename: str | None = None,
    created: str | None = None,
) -> dict:
    """Construct the authored metadata block stored inside the asset.

    Pulls recognised fields from ``user_meta`` and stamps schema_version, kind,
    created and original_filename. Any extra keys in ``user_meta`` are carried
    through verbatim so the schema stays forward-compatible.
    """
    user_meta = dict(user_meta or {})
    meta: dict = {
        "schema_version": constants.SCHEMA_VERSION,
        "kind": infer_kind(rel_path, user_meta.get("kind")),
        "title": user_meta.get("title", stem_of(rel_path)),
        "description": user_meta.get("description", ""),
        "prompt": user_meta.get("prompt", ""),
        "generator": user_meta.get("generator", ""),
        "created": created or user_meta.get("created") or _utc_now_iso(),
        "license": user_meta.get("license", ""),
        "tags": list(user_meta.get("tags", []) or []),
        "original_filename": original_filename or os.path.basename(rel_path),
        "collection": user_meta.get("collection"),
        "derived_from": user_meta.get("derived_from"),
        # Reserved for future semantic / visual-similarity search. Kept null so
        # consumers can rely on the key existing without restructuring later.
        "embeddings": user_meta.get("embeddings"),
    }
    # Carry through any author-supplied keys we don't model explicitly.
    for k, v in user_meta.items():
        if k not in meta and k not in ("created",):
            meta[k] = v
    return meta


def write_asset_metadata(asset_path: str, meta: dict) -> str:
    """Persist authored metadata for an asset.

    Embeds in-band when the format supports it; otherwise writes a sidecar.
    Returns the storage location used ('embedded' or the sidecar path).
    """
    if supports_embedding(asset_path) and imaging.embed(asset_path, meta):
        return "embedded"
    return write_sidecar(asset_path, meta)


def write_sidecar(asset_path: str, meta: dict) -> str:
    path = sidecar_path(asset_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return path


def read_asset_metadata(asset_path: str) -> dict | None:
    """Read authored metadata: embedded first, then sidecar fallback.

    Legacy sidecars (old upload-workflow shape) are migrated on read.
    """
    embedded = imaging.read_embedded(asset_path)
    if embedded is not None:
        return migrate_legacy(embedded)
    side = sidecar_path(asset_path)
    if os.path.exists(side):
        with open(side, "r", encoding="utf-8") as f:
            return migrate_legacy(json.load(f))
    return None


def has_metadata(asset_path: str) -> bool:
    return read_asset_metadata(asset_path) is not None


def enrich_for_index(asset, repository: str, branch: str) -> dict:
    """Build a full index record: authored metadata + computed technical fields.

    ``asset`` is a discovery.Asset. The computed fields (sha256, bytes,
    dimensions, urls, thumbnail) are derived fresh and never stored in-band.
    """
    authored = read_asset_metadata(asset.path) or build_authored_metadata(
        asset.rel_path
    )
    record = dict(authored)
    record.update(
        {
            "path": asset.rel_path,
            "repository": repository,
            "branch": branch,
            "sha256": asset.sha256,
            "bytes": asset.size,
            "dimensions": imaging.get_dimensions(asset.path),
            "github_url": urls.github_url(repository, branch, asset.rel_path),
            "raw_url": urls.raw_url(repository, branch, asset.rel_path),
            "thumbnail": asset.thumbnail_rel if asset.has_thumbnail else None,
            "has_embedded_metadata": imaging.read_embedded(asset.path) is not None,
            "source": constants.SOURCE,
        }
    )
    return record


def validate_metadata(meta: dict | None) -> tuple[list[str], list[str]]:
    """Return (errors, warnings) for an authored metadata block.

    Missing required identity fields are errors; unknown extra keys and empty
    governance fields are warnings (forward-compatible, never fatal).
    """
    errors: list[str] = []
    warnings: list[str] = []
    if meta is None:
        return (["metadata missing"], warnings)
    if not isinstance(meta, dict):
        return (["metadata is not an object"], warnings)

    if "schema_version" not in meta:
        warnings.append("missing schema_version")
    elif meta["schema_version"] > constants.SCHEMA_VERSION:
        warnings.append(
            f"schema_version {meta['schema_version']} newer than supported "
            f"{constants.SCHEMA_VERSION}"
        )
    if not meta.get("kind"):
        errors.append("missing kind")
    if meta.get("tags") is not None and not isinstance(meta["tags"], list):
        errors.append("tags must be a list")

    for governance in ("prompt", "generator", "license"):
        if not meta.get(governance):
            warnings.append(f"empty {governance}")

    known = set(AUTHORED_FIELDS) | {"embeddings"}
    for k in meta:
        if k not in known:
            warnings.append(f"unknown metadata key '{k}' (preserved)")
    return (errors, warnings)


def migrate_legacy(meta: dict) -> dict:
    """Upgrade an old upload-workflow sidecar into the current authored shape.

    The original workflow wrote: path, repository, branch, sha256, bytes,
    created_at, source, user_metadata{...}, raw_url, github_url. We lift the
    nested user_metadata up and stamp the new required fields, without losing
    any original information.
    """
    if not isinstance(meta, dict):
        return meta
    if meta.get("schema_version") == constants.SCHEMA_VERSION and "kind" in meta:
        return meta  # already current

    if "user_metadata" in meta:
        user = meta.get("user_metadata") or {}
        merged = dict(user)
        merged.setdefault("created", meta.get("created_at"))
        rel = meta.get("path", "")
        upgraded = build_authored_metadata(
            rel,
            user_meta=merged,
            original_filename=os.path.basename(rel) if rel else None,
            created=meta.get("created_at"),
        )
        # Preserve any unexpected top-level legacy keys for traceability.
        for k, v in meta.items():
            if k not in (
                "path",
                "repository",
                "branch",
                "sha256",
                "bytes",
                "created_at",
                "source",
                "user_metadata",
                "raw_url",
                "github_url",
            ):
                upgraded.setdefault(k, v)
        return upgraded

    # Unknown shape: ensure the required stamps exist without discarding data.
    meta.setdefault("schema_version", constants.SCHEMA_VERSION)
    meta.setdefault("kind", constants.DEFAULT_KIND)
    return meta
