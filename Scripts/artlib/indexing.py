"""Build the machine-readable asset index — the AI's primary view of the library.

``asset-index.json`` is a first-class artifact: an AI (Lubot) reads it to reason
about everything in the repository without opening each file. ``ASSET_INDEX.md``
is the human mirror. ``Metadata/all-metadata.json`` is the flat aggregate of
every asset's record for bulk consumption.

All three are *derived* — regenerated from the assets, never hand-edited.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from . import constants, dedupe, metadata
from .discovery import discover_assets


def build_index(root: str, repository: str, branch: str, generated_at: str | None = None) -> dict:
    """Construct the full index dict from the assets currently on disk."""
    assets = discover_assets(root)
    records = [metadata.enrich_for_index(a, repository, branch) for a in assets]
    total_bytes = sum(r["bytes"] for r in records)
    duplicates = dedupe.duplicate_records(assets)

    return {
        "schema_version": constants.SCHEMA_VERSION,
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "branch": branch,
        "asset_count": len(records),
        "total_bytes": total_bytes,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        # Reserved so future semantic/visual search can attach vectors at the
        # top level without changing the schema shape consumers depend on.
        "embeddings": None,
        "assets": records,
    }


def write_index(root: str, index: dict) -> list[str]:
    """Write asset-index.json, ASSET_INDEX.md and the metadata aggregate.

    Returns the list of repo-relative paths written.
    """
    written = []

    json_path = os.path.join(root, constants.INDEX_JSON)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write("\n")
    written.append(constants.INDEX_JSON)

    md_path = os.path.join(root, constants.INDEX_MD)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(render_index_md(index))
    written.append(constants.INDEX_MD)

    os.makedirs(os.path.join(root, constants.METADATA_DIR), exist_ok=True)
    agg_path = os.path.join(root, constants.METADATA_AGGREGATE)
    with open(agg_path, "w", encoding="utf-8") as f:
        json.dump(index["assets"], f, indent=2, ensure_ascii=False)
        f.write("\n")
    written.append(constants.METADATA_AGGREGATE)

    return written


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def render_index_md(index: dict) -> str:
    lines = [
        "# Asset Index",
        "",
        "> Generated automatically — do not edit by hand. "
        "Run the Asset Index workflow or `Scripts/build_index.py` to regenerate.",
        "",
        f"- **Assets:** {index['asset_count']}",
        f"- **Total size:** {_human_bytes(index['total_bytes'])}",
        f"- **Duplicates:** {index['duplicate_count']}",
        f"- **Generated:** {index['generated_at']}",
        "",
        "| Asset | Kind | Dimensions | Size | SHA-256 | Links |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in index["assets"]:
        dims = "—"
        if r.get("dimensions"):
            dims = f"{r['dimensions'][0]}×{r['dimensions'][1]}"
        sha = (r.get("sha256") or "")[:12]
        links = f"[raw]({r['raw_url']}) · [view]({r['github_url']})"
        lines.append(
            f"| `{r['path']}` | {r.get('kind', '')} | {dims} | "
            f"{_human_bytes(r['bytes'])} | `{sha}` | {links} |"
        )
    if index["duplicates"]:
        lines += ["", "## Duplicates", ""]
        for d in index["duplicates"]:
            joined = ", ".join(f"`{p}`" for p in d["paths"])
            lines.append(f"- `{d['sha256'][:12]}` — {joined}")
    lines.append("")
    return "\n".join(lines)
