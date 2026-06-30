"""Repository health reporting.

The repo continuously reports on itself so neither Lubot nor a human has to
remember maintenance tasks. The report covers counts, storage, governance gaps
(missing metadata), duplicates, newest/largest assets and per-extension stats.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import datetime, timezone

from . import constants, dedupe, metadata
from .discovery import discover_assets


def _human_bytes(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def build_report(root: str, top_n: int = 10, generated_at: str | None = None) -> dict:
    assets = discover_assets(root)
    total_bytes = sum(a.size for a in assets)

    missing_metadata = [a.rel_path for a in assets if not a.has_metadata]
    duplicates = dedupe.duplicate_records(assets)

    by_created = sorted(
        assets, key=lambda a: _created_key(a), reverse=True
    )[:top_n]
    by_size = sorted(assets, key=lambda a: a.size, reverse=True)[:top_n]

    ext_stats: dict[str, dict] = defaultdict(lambda: {"count": 0, "bytes": 0})
    for a in assets:
        ext_stats[a.ext]["count"] += 1
        ext_stats[a.ext]["bytes"] += a.size

    return {
        "generated_at": generated_at or datetime.now(timezone.utc).isoformat(),
        "asset_count": len(assets),
        "total_bytes": total_bytes,
        "missing_metadata": missing_metadata,
        "duplicate_count": len(duplicates),
        "duplicates": duplicates,
        "newest": [
            {"path": a.rel_path, "created": _created_str(a)} for a in by_created
        ],
        "largest": [
            {"path": a.rel_path, "bytes": a.size} for a in by_size
        ],
        "extensions": {
            ext: dict(stats) for ext, stats in sorted(ext_stats.items())
        },
    }


def _created_str(asset) -> str | None:
    meta = metadata.read_asset_metadata(asset.path)
    if meta and meta.get("created"):
        return meta["created"]
    try:
        return datetime.fromtimestamp(
            os.path.getmtime(asset.path), timezone.utc
        ).isoformat()
    except OSError:
        return None


def _created_key(asset) -> str:
    return _created_str(asset) or ""


def render_report_md(report: dict) -> str:
    lines = [
        "# Repository Report",
        "",
        f"_Generated {report['generated_at']}_",
        "",
        "## Summary",
        "",
        f"- **Assets:** {report['asset_count']}",
        f"- **Storage used:** {_human_bytes(report['total_bytes'])}",
        f"- **Missing metadata:** {len(report['missing_metadata'])}",
        f"- **Duplicate groups:** {report['duplicate_count']}",
        "",
        "## Extensions",
        "",
        "| Extension | Count | Size |",
        "| --- | --- | --- |",
    ]
    for ext, stats in report["extensions"].items():
        lines.append(f"| `.{ext}` | {stats['count']} | {_human_bytes(stats['bytes'])} |")

    lines += ["", "## Largest assets", "", "| Asset | Size |", "| --- | --- |"]
    for item in report["largest"]:
        lines.append(f"| `{item['path']}` | {_human_bytes(item['bytes'])} |")

    lines += ["", "## Newest assets", "", "| Asset | Created |", "| --- | --- |"]
    for item in report["newest"]:
        lines.append(f"| `{item['path']}` | {item['created'] or '—'} |")

    if report["missing_metadata"]:
        lines += ["", "## Missing metadata", ""]
        lines += [f"- `{p}`" for p in report["missing_metadata"]]

    if report["duplicates"]:
        lines += ["", "## Duplicates", ""]
        for d in report["duplicates"]:
            joined = ", ".join(f"`{p}`" for p in d["paths"])
            lines.append(f"- `{d['sha256'][:12]}` — {joined}")

    lines.append("")
    return "\n".join(lines)


def write_report(root: str, report: dict) -> str:
    os.makedirs(os.path.join(root, constants.REPORTS_DIR), exist_ok=True)
    path = os.path.join(root, constants.REPORT_MD)
    with open(path, "w", encoding="utf-8") as f:
        f.write(render_report_md(report))
    return constants.REPORT_MD
