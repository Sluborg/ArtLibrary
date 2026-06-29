#!/usr/bin/env python3
"""Rebuild everything from the assets (Repair Repository workflow entrypoint).

Reconstructs all derived state from the asset bytes alone, WITHOUT losing
assets:
  * ensure every asset has metadata (synthesize a minimal block if missing,
    migrate legacy sidecars into embedded form where supported),
  * regenerate thumbnails that are missing,
  * rebuild the index, aggregate and report.

Use this to recover from a corrupted index or partial history. Thin wrapper
over ``artlib``.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, discovery, gitutil, imaging, indexing, metadata, paths, reporting  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild all derived state.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--thumbnails", action="store_true", help="regenerate missing thumbnails")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--message", default="Repair repository")
    args = parser.parse_args()

    log = cli.setup_logging()
    repository, branch = cli.repo_branch_from_env()

    assets = discovery.discover_assets(args.root)
    repaired_meta = 0
    for asset in assets:
        meta = metadata.read_asset_metadata(asset.path)
        if meta is None:
            meta = metadata.build_authored_metadata(asset.rel_path)
            metadata.write_asset_metadata(asset.path, meta)
            repaired_meta += 1
        else:
            # Re-persist to migrate legacy sidecars into the current shape.
            metadata.write_asset_metadata(asset.path, meta)

    rebuilt_thumbs = 0
    if args.thumbnails:
        for asset in assets:
            if not asset.has_thumbnail:
                thumb = os.path.join(args.root, paths.thumbnail_path(asset.rel_path))
                if imaging.make_thumbnail(asset.path, thumb):
                    rebuilt_thumbs += 1

    index = indexing.build_index(args.root, repository, branch)
    indexing.write_index(args.root, index)
    report = reporting.build_report(args.root)
    reporting.write_report(args.root, report)
    log.info(
        "Repair complete: %d assets, %d metadata repaired, %d thumbnails rebuilt",
        len(assets),
        repaired_meta,
        rebuilt_thumbs,
    )

    if args.commit:
        gitutil.configure_bot()
        gitutil.stage_all()
        if gitutil.commit_if_changed(args.message):
            gitutil.push(branch)
            log.info("Committed repair to %s", branch)
        else:
            log.info("Nothing to repair")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
