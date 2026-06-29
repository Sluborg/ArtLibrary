#!/usr/bin/env python3
"""Remove orphans and rebuild derived files (Cleanup workflow entrypoint).

Deletes orphan sidecars/thumbnails (whose parent asset is gone), then rebuilds
the index and report so the repo returns to a consistent state. Never touches
asset bytes. Thin wrapper over ``artlib`` discovery/indexing/reporting.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, discovery, gitutil, indexing, reporting  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean up orphans and rebuild.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--message", default="Cleanup repository")
    args = parser.parse_args()

    log = cli.setup_logging()
    repository, branch = cli.repo_branch_from_env()

    removed = []
    for orphan in discovery.find_orphan_sidecars(args.root) + discovery.find_orphan_thumbnails(args.root):
        full = os.path.join(args.root, orphan)
        try:
            os.remove(full)
            removed.append(orphan)
            log.info("Removed orphan %s", orphan)
        except OSError as exc:
            log.warning("Could not remove %s: %s", orphan, exc)

    # Rebuild derived state so a broken index self-heals.
    index = indexing.build_index(args.root, repository, branch)
    written = indexing.write_index(args.root, index)
    report = reporting.build_report(args.root)
    written.append(reporting.write_report(args.root, report))
    log.info("Removed %d orphan(s); rebuilt index + report", len(removed))

    if args.commit:
        gitutil.configure_bot()
        gitutil.stage_all()
        if gitutil.commit_if_changed(args.message):
            gitutil.push(branch)
            log.info("Committed cleanup to %s", branch)
        else:
            log.info("Nothing to clean up")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
