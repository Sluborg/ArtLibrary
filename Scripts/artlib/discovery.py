"""Walk the repository and yield real assets (never thumbnails/derived files).

``discover_assets`` is the one function every consumer (index, validate,
report, cleanup, repair) uses to enumerate assets, guaranteeing they all agree
on what counts as an asset. Orphan finders locate derived files whose parent
asset has disappeared.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from . import constants, metadata, paths
from .hashing import sha256_file


@dataclass
class Asset:
    """A discovered asset plus its derived sibling paths.

    ``sha256`` is computed lazily (it requires reading the whole file) so cheap
    operations like counting assets don't pay for hashing.
    """

    path: str  # absolute or root-relative filesystem path
    rel_path: str  # repository-relative POSIX path
    root: str = "."
    _sha256: str | None = field(default=None, repr=False)

    @property
    def ext(self) -> str:
        return paths.ext_of(self.rel_path)

    @property
    def size(self) -> int:
        try:
            return os.path.getsize(self.path)
        except OSError:
            return 0

    @property
    def sha256(self) -> str:
        if self._sha256 is None:
            self._sha256 = sha256_file(self.path)
        return self._sha256

    @property
    def kind(self) -> str:
        meta = metadata.read_asset_metadata(self.path)
        if meta and meta.get("kind"):
            return meta["kind"]
        return metadata.infer_kind(self.rel_path, None)

    @property
    def thumbnail_rel(self) -> str:
        return paths.thumbnail_path(self.rel_path)

    @property
    def thumbnail_path(self) -> str:
        return os.path.join(self.root, self.thumbnail_rel)

    @property
    def has_thumbnail(self) -> bool:
        return os.path.exists(self.thumbnail_path)

    @property
    def favicon_rels(self) -> list[str]:
        return paths.favicon_paths(self.rel_path)

    @property
    def has_metadata(self) -> bool:
        return metadata.has_metadata(self.path)

    @property
    def sidecar_rel(self) -> str:
        return paths.sidecar_path(self.rel_path)


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        top = "" if rel_dir == "." else rel_dir.replace("\\", "/").split("/", 1)[0]
        if top in constants.IGNORED_DIRS:
            dirnames[:] = []
            continue
        # Prune ignored subdirs early.
        dirnames[:] = [d for d in dirnames if d not in constants.IGNORED_DIRS]
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace("\\", "/")
            yield full, rel


def discover_assets(root: str = ".") -> list[Asset]:
    """Return all real assets under the asset folders, sorted by path."""
    assets: list[Asset] = []
    for full, rel in _iter_files(root):
        top = rel.split("/", 1)[0]
        if top not in constants.ASSET_DIRS:
            continue
        if paths.classify(rel, root) != "asset":
            continue
        assets.append(Asset(path=full, rel_path=rel, root=root))
    assets.sort(key=lambda a: a.rel_path)
    return assets


def asset_rel_set(root: str = ".") -> set[str]:
    return {a.rel_path for a in discover_assets(root)}


def find_orphan_sidecars(root: str = ".") -> list[str]:
    """Sidecar files whose parent asset no longer exists."""
    orphans = []
    for full, rel in _iter_files(root):
        if not paths.is_sidecar(rel):
            continue
        parent = paths.parent_asset_of_sidecar(full)
        if not os.path.exists(parent):
            orphans.append(rel)
    return sorted(orphans)


def find_orphan_thumbnails(root: str = ".") -> list[str]:
    """Thumbnail files whose parent asset no longer exists."""
    orphans = []
    for full, rel in _iter_files(root):
        if not paths.is_thumbnail(rel):
            continue
        parent = paths.parent_asset_candidates_of_thumbnail(full)
        if not os.path.exists(parent):
            orphans.append(rel)
    return sorted(orphans)
