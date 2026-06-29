"""Lossless asset optimization shared by Upload and Optimize-Repository.

Each format is optimized with the appropriate tool without changing how the
asset looks. Tools are invoked tolerantly: a missing tool or a file that
cannot be improved is skipped, never fatal.

IMPORTANT: jpegoptim --strip-all removes EXIF, which is where we embed JPEG
metadata. Callers that want to keep embedded metadata must read it before
optimizing and re-embed after (see Scripts/optimize_repo.py and upload flow).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess

from .paths import ext_of


def _run(cmd: list[str]) -> bool:
    try:
        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def optimize_file(path: str) -> dict:
    """Optimize a single file in place. Returns a result summary.

    Result: {path, tool, before, after, saved, ok}. ``saved`` may be 0 if the
    file was already optimal or no tool was available.
    """
    ext = ext_of(path)
    before = _size(path)
    tool = None
    ok = False

    if ext == "png":
        tool, ok = "optipng", _run(["optipng", "-quiet", "-o2", path])
    elif ext in ("jpg", "jpeg"):
        tool, ok = "jpegoptim", _run(
            ["jpegoptim", "--strip-all", "--all-progressive", path]
        )
    elif ext == "webp":
        tool, ok = "cwebp", _optimize_webp(path)
    elif ext == "svg":
        tool, ok = "svg", _optimize_svg(path)
    else:
        tool = "none"

    after = _size(path)
    return {
        "path": path,
        "tool": tool,
        "before": before,
        "after": after,
        "saved": max(0, before - after),
        "ok": ok,
    }


def _optimize_webp(path: str) -> bool:
    tmp = path + ".tmp.webp"
    if _run(["cwebp", "-quiet", "-lossless", path, "-o", tmp]) and os.path.exists(tmp):
        if _size(tmp) > 0 and _size(tmp) <= _size(path):
            shutil.move(tmp, path)
            return True
        os.remove(tmp)
    return False


def _optimize_svg(path: str) -> bool:
    if shutil.which("svgo"):
        return _run(["svgo", "--quiet", "-i", path, "-o", path])
    # Fallback: strip XML comments and collapse runs of whitespace between tags.
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        stripped = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
        stripped = re.sub(r">\s+<", "><", stripped)
        if stripped != text:
            with open(path, "w", encoding="utf-8") as f:
                f.write(stripped)
            return True
    except OSError:
        return False
    return False


def _size(path: str) -> int:
    try:
        return os.path.getsize(path)
    except OSError:
        return 0


def optimize_tree(assets) -> dict:
    """Optimize a list of discovery.Asset objects, preserving metadata.

    Reads each asset's embedded metadata first, optimizes, then re-embeds so
    EXIF-stripping optimizers do not drop governance data.
    """
    from . import metadata

    results = []
    total_saved = 0
    for asset in assets:
        meta = metadata.read_asset_metadata(asset.path)
        res = optimize_file(asset.path)
        if res["saved"] > 0 and meta is not None:
            metadata.write_asset_metadata(asset.path, meta)
        results.append(res)
        total_saved += res["saved"]
    return {"files": results, "total_saved": total_saved}
