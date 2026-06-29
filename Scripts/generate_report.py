#!/usr/bin/env python3
"""Generate the repository health report (Generate Reports workflow entrypoint).

Writes Reports/latest-report.md and optionally commits it. Thin wrapper over
``artlib.reporting``.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, gitutil, reporting  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the repository report.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--message", default="Update repository report")
    args = parser.parse_args()

    log = cli.setup_logging()
    _, branch = cli.repo_branch_from_env()

    report = reporting.build_report(args.root)
    path = reporting.write_report(args.root, report)
    log.info(
        "Report: %d assets, %d missing metadata, %d duplicate groups -> %s",
        report["asset_count"],
        len(report["missing_metadata"]),
        report["duplicate_count"],
        path,
    )

    if args.commit:
        gitutil.configure_bot()
        gitutil.stage([path])
        if gitutil.commit_if_changed(args.message):
            gitutil.push(branch)
            log.info("Committed report to %s", branch)
        else:
            log.info("Report unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
