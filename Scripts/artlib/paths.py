"""Path conventions and the repository-path security boundary.

This module is the single home for:
  * deriving sibling paths (thumbnail / favicon / sidecar) from an asset path,
  * classifying any repo file as asset / thumbnail / favicon / sidecar / derived,
  * validating an externally-supplied repo-relative path (security-critical).

The path-safety check is lifted verbatim from the original upload workflow and
MUST NOT be loosened: it is the boundary that prevents path traversal and
writes outside the repository when an AI/agent supplies an upload target.
"""

from __future__ import annotations

import os
import re

from . import constants

# Security boundary: only these characters, never a leading "/", never "..".
_SAFE_PATH_RE = re.compile(r"^[A-Za-z0-9._/\-]+$")


def validate_repo_path(path: str) -> str:
    """Return ``path`` unchanged if it is a safe repo-relative path, else raise.

    Mirrors the original workflow's validation exactly.
    """
    if not path:
        raise ValueError("path must be non-empty")
    if not _SAFE_PATH_RE.match(path):
        raise ValueError("path contains unsupported characters")
    if path.startswith("/") or ".." in path.split("/"):
        raise ValueError("path must be repository-relative and may not contain '..'")
    return path


def validate_branch(branch: str) -> str:
    """Return ``branch`` unchanged if safe, else raise (same charset as paths)."""
    if not branch or not _SAFE_PATH_RE.match(branch):
        raise ValueError("branch contains unsupported characters")
    return branch


def ext_of(path: str) -> str:
    """Lower-case extension without the dot ('' if none)."""
    return os.path.splitext(path)[1].lstrip(".").lower()


def stem_of(path: str) -> str:
    """Filename without directory or final extension."""
    return os.path.splitext(os.path.basename(path))[0]


def thumbnail_path(asset_path: str) -> str:
    """Derive '<dir>/<stem>.thumb.<ext>' for an asset."""
    directory = os.path.dirname(asset_path)
    stem = stem_of(asset_path)
    ext = ext_of(asset_path)
    name = f"{stem}{constants.THUMB_INFIX}.{ext}" if ext else f"{stem}{constants.THUMB_INFIX}"
    return os.path.join(directory, name) if directory else name


def favicon_paths(asset_path: str) -> list[str]:
    """Derive the list of '<dir>/<stem>-<size>.png' favicon paths."""
    directory = os.path.dirname(asset_path)
    stem = stem_of(asset_path)
    out = []
    for size in constants.FAVICON_SIZES:
        name = f"{stem}-{size}.png"
        out.append(os.path.join(directory, name) if directory else name)
    return out


def sidecar_path(asset_path: str) -> str:
    """Derive the fallback '<asset>.metadata.json' sidecar path."""
    return asset_path + constants.SIDECAR_SUFFIX


def is_sidecar(path: str) -> bool:
    return path.endswith(constants.SIDECAR_SUFFIX)


def is_thumbnail(path: str) -> bool:
    stem = stem_of(path)
    return stem.endswith(constants.THUMB_INFIX)


_FAVICON_RE = re.compile(
    r"-(?:%s)$" % "|".join(str(s) for s in constants.FAVICON_SIZES)
)


def is_favicon(path: str, root: str = ".") -> bool:
    """A '<stem>-<size>.png' is a favicon only if a sibling asset exists.

    This avoids misclassifying a legitimately-named asset like 'logo-32.png'
    that has no parent: with no parent asset present, it is a real asset.
    """
    if ext_of(path) != "png":
        return False
    stem = stem_of(path)
    m = _FAVICON_RE.search(stem)
    if not m:
        return False
    parent_stem = stem[: m.start()]
    directory = os.path.dirname(path)
    abs_dir = os.path.join(root, directory) if directory else root
    try:
        siblings = os.listdir(abs_dir)
    except OSError:
        return False
    # A sibling whose stem == parent_stem and which is itself an asset.
    for name in siblings:
        if stem_of(name) == parent_stem and ext_of(name) in constants.ASSET_EXTENSIONS:
            if not is_thumbnail(name) and not is_sidecar(name):
                return True
    return False


def is_in_ignored_dir(rel_path: str) -> bool:
    top = rel_path.replace("\\", "/").split("/", 1)[0]
    return top in constants.IGNORED_DIRS


def classify(rel_path: str, root: str = ".") -> str:
    """Classify a repo-relative path.

    Returns one of: 'sidecar', 'thumbnail', 'favicon', 'derived', 'asset',
    or 'ignored' (infrastructure / unknown / non-asset extension).
    """
    norm = rel_path.replace("\\", "/")
    if norm in constants.DERIVED_FILES:
        return "derived"
    if is_in_ignored_dir(norm):
        return "ignored"
    if is_sidecar(norm):
        return "sidecar"
    if is_thumbnail(norm):
        return "thumbnail"
    if is_favicon(norm, root):
        return "favicon"
    if ext_of(norm) in constants.ASSET_EXTENSIONS:
        return "asset"
    return "ignored"


def parent_asset_of_sidecar(sidecar: str) -> str:
    """'<asset>.metadata.json' -> '<asset>'."""
    return sidecar[: -len(constants.SIDECAR_SUFFIX)]


def parent_asset_candidates_of_thumbnail(thumb: str) -> str:
    """'<dir>/<stem>.thumb.<ext>' -> '<dir>/<stem>.<ext>'."""
    directory = os.path.dirname(thumb)
    stem = stem_of(thumb)  # 'name.thumb'
    base_stem = stem[: -len(constants.THUMB_INFIX)]
    ext = ext_of(thumb)
    name = f"{base_stem}.{ext}" if ext else base_stem
    return os.path.join(directory, name) if directory else name
