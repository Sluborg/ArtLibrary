#!/usr/bin/env python3
"""Rebuild the asset index (Asset Index workflow entrypoint).

Regenerates asset-index.json, ASSET_INDEX.md and Metadata/all-metadata.json
from the assets on disk, then optionally commits them. Thin wrapper over
``artlib.indexing``.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, gitutil, indexing  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the asset index.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--commit", action="store_true", help="commit + push the result")
    parser.add_argument("--message", default="Rebuild asset index")
    args = parser.parse_args()

    log = cli.setup_logging()
    repository, branch = cli.repo_branch_from_env()

    index = indexing.build_index(args.root, repository, branch)
    written = indexing.write_index(args.root, index)
    log.info("Indexed %d assets -> %s", index["asset_count"], ", ".join(written))

    if args.commit:
        gitutil.configure_bot()
        gitutil.stage(written)
        if gitutil.commit_if_changed(args.message):
            gitutil.push(branch)
            log.info("Committed updated index to %s", branch)
        else:
            log.info("Index already up to date")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
