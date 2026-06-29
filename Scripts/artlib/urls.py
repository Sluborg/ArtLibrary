"""Construct the canonical GitHub web and raw URLs for an asset.

These strings are the asset's public delivery channel: the raw URL is what
Lubot, a game, or any client uses to fetch the bytes directly. Kept exactly
as the original upload workflow produced them.
"""

from __future__ import annotations


def github_url(repository: str, branch: str, path: str) -> str:
    """Human-facing blob URL on github.com."""
    return f"https://github.com/{repository}/blob/{branch}/{path}"


def raw_url(repository: str, branch: str, path: str) -> str:
    """Direct content URL on raw.githubusercontent.com (the CDN delivery URL)."""
    return f"https://raw.githubusercontent.com/{repository}/{branch}/{path}"
