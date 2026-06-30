"""Image operations: dimensions, thumbnails, favicons, and in-band metadata.

All raster work uses Pillow. Every function degrades gracefully for formats it
cannot handle (returns None / does nothing / returns False) so the wider
pipeline never crashes on a non-image or unsupported asset.

Embedding stores the authored metadata JSON *inside* the asset container,
without ever recompressing the image:
  * PNG  -> an iTXt chunk keyed by ``constants.EMBED_KEY`` (lossless re-encode)
  * JPEG -> EXIF ImageDescription (tag 0x010E), saved with quality="keep" so the
            original quantization tables/coefficients are reused (no new loss)
  * SVG  -> a <metadata> element carrying the JSON (plain text)
WebP/TIFF/GIF cannot be updated without re-encoding, so they fall back to a
sidecar file (see metadata.py) rather than risk degrading the asset.
"""

from __future__ import annotations

import json
import os
import re

from . import constants
from .paths import ext_of

try:  # Pillow is the only third-party dependency.
    from PIL import Image, PngImagePlugin

    _PIL_OK = True
except Exception:  # pragma: no cover - import guard
    _PIL_OK = False

# EXIF tag used to carry our JSON in JPEG.
_EXIF_IMAGE_DESCRIPTION = 0x010E

# Formats we can embed metadata into in-band WITHOUT recompressing pixels.
# PNG re-encode is lossless; JPEG uses quality="keep" to reuse the original
# quantization tables (no generational loss); SVG is plain text. WebP, TIFF and
# GIF are intentionally NOT embeddable: Pillow cannot rewrite their metadata
# without re-encoding the image, which would alter pixels — so they fall back to
# a sidecar (handled by metadata.py). Anything else also falls back to sidecar.
_EMBED_PNG = frozenset({"png"})
_EMBED_JPEG = frozenset({"jpg", "jpeg"})
_EMBED_SVG = frozenset({"svg"})


def pillow_available() -> bool:
    return _PIL_OK


def can_embed(ext: str) -> bool:
    ext = ext.lower()
    return ext in (_EMBED_PNG | _EMBED_JPEG | _EMBED_SVG)


# --- Dimensions ------------------------------------------------------------


def get_dimensions(path: str) -> list[int] | None:
    """Return ``[width, height]`` or ``None`` for vector/unknown/unreadable.

    Tries Pillow first; falls back to parsing the SVG width/height/viewBox so
    vector assets still report dimensions where possible.
    """
    ext = ext_of(path)
    if ext == "svg":
        return _svg_dimensions(path)
    if not _PIL_OK or ext not in constants.RASTER_EXTENSIONS:
        return None
    try:
        with Image.open(path) as im:
            return [im.width, im.height]
    except Exception:
        return None


def _svg_dimensions(path: str) -> list[int] | None:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            head = f.read(4096)
    except OSError:
        return None
    w = re.search(r'\bwidth\s*=\s*"([\d.]+)', head)
    h = re.search(r'\bheight\s*=\s*"([\d.]+)', head)
    if w and h:
        return [int(float(w.group(1))), int(float(h.group(1)))]
    vb = re.search(r'\bviewBox\s*=\s*"[\d.\s-]*?([\d.]+)\s+([\d.]+)"', head)
    if vb:
        return [int(float(vb.group(1))), int(float(vb.group(2)))]
    return None


# --- Thumbnails & favicons -------------------------------------------------


def make_thumbnail(src: str, dst: str, size: tuple[int, int] = constants.THUMB_SIZE) -> bool:
    """Write a downscaled thumbnail. Returns False if the source isn't raster."""
    if not _PIL_OK or ext_of(src) not in constants.RASTER_EXTENSIONS:
        return False
    try:
        with Image.open(src) as im:
            im = im.convert("RGBA") if im.mode in ("P", "LA") else im
            im.thumbnail(size)
            _save_like(im, dst)
        return True
    except Exception:
        return False


def make_favicons(src: str, sizes=constants.FAVICON_SIZES, dst_paths=None) -> list[str]:
    """Write favicon PNGs at the given sizes. Returns the list of written paths."""
    if not _PIL_OK or ext_of(src) not in constants.RASTER_EXTENSIONS:
        return []
    from .paths import favicon_paths

    targets = dst_paths or favicon_paths(src)
    written: list[str] = []
    try:
        with Image.open(src) as im:
            base = im.convert("RGBA")
            for size, target in zip(sizes, targets):
                fav = base.copy()
                fav.thumbnail((size, size))
                fav.save(target, format="PNG")
                written.append(target)
    except Exception:
        return written
    return written


def _save_like(im, dst: str) -> None:
    ext = ext_of(dst)
    if ext in ("jpg", "jpeg") and im.mode in ("RGBA", "P", "LA"):
        im = im.convert("RGB")
    im.save(dst)


# --- Metadata embedding ----------------------------------------------------


def embed(path: str, meta: dict) -> bool:
    """Embed ``meta`` (as JSON) inside the asset in-band. Returns success."""
    if not _PIL_OK:
        return False
    ext = ext_of(path)
    payload = json.dumps(meta, ensure_ascii=False, separators=(",", ":"))
    try:
        if ext in _EMBED_PNG:
            return _embed_png(path, payload)
        if ext in _EMBED_JPEG:
            return _embed_jpeg(path, payload)
        if ext in _EMBED_SVG:
            return _embed_svg(path, payload)
    except Exception:
        return False
    return False


def read_embedded(path: str) -> dict | None:
    """Read embedded metadata JSON, or ``None`` if absent/unreadable."""
    ext = ext_of(path)
    try:
        if ext in _EMBED_SVG:
            return _read_svg(path)
        if not _PIL_OK:
            return None
        if ext in _EMBED_PNG:
            return _read_png(path)
        if ext in _EMBED_JPEG:
            return _read_jpeg(path)
    except Exception:
        return None
    return None


def _embed_png(path: str, payload: str) -> bool:
    with Image.open(path) as im:
        im.load()
        info = PngImagePlugin.PngInfo()
        # Preserve any pre-existing text chunks except our own key.
        for k, v in (im.text or {}).items():
            if k != constants.EMBED_KEY:
                info.add_text(k, v)
        info.add_itxt(constants.EMBED_KEY, payload)
        params = {"pnginfo": info}
        if "transparency" in im.info:
            params["transparency"] = im.info["transparency"]
        im.save(path, **params)
    return True


def _read_png(path: str) -> dict | None:
    with Image.open(path) as im:
        text = getattr(im, "text", None) or {}
        raw = text.get(constants.EMBED_KEY) or im.info.get(constants.EMBED_KEY)
    return json.loads(raw) if raw else None


def _embed_jpeg(path: str, payload: str) -> bool:
    with Image.open(path) as im:
        if im.format != "JPEG":
            # Extension lied about the format; don't risk recompressing it.
            return False
        im.load()
        exif = im.getexif()
        exif[_EXIF_IMAGE_DESCRIPTION] = constants.EMBED_KEY + ":" + payload
        # quality="keep" reuses the source's quantization tables, so the DCT
        # coefficients are preserved and the pixels are not recompressed — we
        # are only rewriting the EXIF block. Keep subsampling as-is too.
        im.save(path, "JPEG", quality="keep", subsampling="keep", exif=exif)
    return True


def _read_jpeg(path: str) -> dict | None:
    with Image.open(path) as im:
        exif = im.getexif()
        raw = exif.get(_EXIF_IMAGE_DESCRIPTION)
    if not raw:
        return None
    prefix = constants.EMBED_KEY + ":"
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "ignore")
    if raw.startswith(prefix):
        return json.loads(raw[len(prefix):])
    return None


_SVG_META_RE = re.compile(
    r'<metadata id="%s"[^>]*>(.*?)</metadata>' % re.escape(constants.EMBED_KEY),
    re.DOTALL,
)


def _embed_svg(path: str, payload: str) -> bool:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    # JSON wrapped in CDATA so it survives XML parsing.
    block = (
        f'<metadata id="{constants.EMBED_KEY}"><![CDATA[{payload}]]></metadata>'
    )
    if _SVG_META_RE.search(text):
        text = _SVG_META_RE.sub(block, text)
    else:
        # Insert right after the opening <svg ...> tag.
        m = re.search(r"<svg\b[^>]*>", text)
        if not m:
            return False
        idx = m.end()
        text = text[:idx] + block + text[idx:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return True


def _read_svg(path: str) -> dict | None:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()
    m = _SVG_META_RE.search(text)
    if not m:
        return None
    inner = m.group(1).strip()
    inner = re.sub(r"^<!\[CDATA\[|\]\]>$", "", inner).strip()
    return json.loads(inner) if inner else None
