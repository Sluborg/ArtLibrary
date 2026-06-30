"""Duplicate detection by content hash.

Assets are grouped by their real SHA-256 (computed from bytes, never trusted
from metadata) so identical content uploaded under different names is found.
Duplicates are a warning, not an error: an AI may legitimately keep the same
image in several collections.
"""

from __future__ import annotations

from collections import defaultdict


def group_by_sha256(assets) -> dict[str, list]:
    groups: dict[str, list] = defaultdict(list)
    for asset in assets:
        groups[asset.sha256].append(asset)
    return groups


def find_duplicates(assets) -> dict[str, list]:
    """Return {sha256: [assets]} only for shas shared by more than one asset."""
    return {
        sha: items
        for sha, items in group_by_sha256(assets).items()
        if len(items) > 1
    }


def duplicate_records(assets) -> list[dict]:
    """Machine-readable duplicate summary for the index/report."""
    out = []
    for sha, items in sorted(find_duplicates(assets).items()):
        out.append({"sha256": sha, "paths": [a.rel_path for a in items]})
    return out
