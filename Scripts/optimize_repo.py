#!/usr/bin/env python3
"""Optimize every asset losslessly (Optimize Repository workflow entrypoint).

Re-runs the same optimizers Upload uses across the whole library, preserving
embedded metadata, and commits the savings. Thin wrapper over
``artlib.optimize``.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, discovery, gitutil, optimize  # noqa: E402


def _human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def main() -> int:
    parser = argparse.ArgumentParser(description="Optimize all assets.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--message", default="Optimize assets")
    args = parser.parse_args()

    log = cli.setup_logging()
    _, branch = cli.repo_branch_from_env()

    assets = discovery.discover_assets(args.root)
    summary = optimize.optimize_tree(assets)
    improved = [r for r in summary["files"] if r["saved"] > 0]
    for r in improved:
        log.info("%s: -%s via %s", r["path"], _human(r["saved"]), r["tool"])
    log.info(
        "Optimized %d/%d assets, saved %s total",
        len(improved),
        len(assets),
        _human(summary["total_saved"]),
    )

    if args.commit:
        gitutil.configure_bot()
        gitutil.stage_all()
        if gitutil.commit_if_changed(args.message):
            gitutil.push(branch)
            log.info("Committed optimizations to %s", branch)
        else:
            log.info("Nothing to optimize")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
