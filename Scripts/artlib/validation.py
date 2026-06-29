"""Repository validation — the gate that runs on every push and PR.

Errors fail the build (broken/missing metadata, invalid JSON, orphans, hash
mismatches). Duplicates and forward-compatible oddities are warnings. The
result is structured so the CLI can print it and set an exit code.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from . import constants, dedupe, metadata
from .discovery import (
    discover_assets,
    find_orphan_sidecars,
    find_orphan_thumbnails,
)


@dataclass
class Result:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def error(self, msg: str) -> None:
        self.errors.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)


def validate_repository(root: str = ".") -> Result:
    result = Result()
    assets = discover_assets(root)

    for asset in assets:
        meta = metadata.read_asset_metadata(asset.path)
        if meta is None:
            result.error(f"{asset.rel_path}: missing metadata")
            continue
        errors, warnings = metadata.validate_metadata(meta)
        for e in errors:
            result.error(f"{asset.rel_path}: {e}")
        for w in warnings:
            result.warn(f"{asset.rel_path}: {w}")

    # Any sidecar present must contain valid JSON.
    for full, rel in _all_sidecars(root):
        try:
            with open(full, "r", encoding="utf-8") as f:
                json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            result.error(f"{rel}: invalid metadata JSON ({exc})")

    for orphan in find_orphan_sidecars(root):
        result.error(f"{orphan}: orphan sidecar (no parent asset)")
    for orphan in find_orphan_thumbnails(root):
        result.error(f"{orphan}: orphan thumbnail (no parent asset)")

    duplicates = dedupe.duplicate_records(assets)
    for d in duplicates:
        joined = ", ".join(d["paths"])
        result.warn(f"duplicate content {d['sha256'][:12]}: {joined}")

    return result


def _all_sidecars(root: str):
    from .paths import is_sidecar, is_in_ignored_dir

    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = "" if rel_dir == "." else rel_dir.replace("\\", "/").split("/", 1)[0]
        if top in constants.IGNORED_DIRS:
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in constants.IGNORED_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            if is_sidecar(rel) and not is_in_ignored_dir(rel):
                yield full, rel
