#!/usr/bin/env python3
"""Validate the repository (Validate Assets workflow entrypoint).

Fails (exit 1) on errors: missing/broken metadata, invalid JSON, orphans.
Warns (exit 0) on duplicates and forward-compatible oddities. Thin wrapper
over ``artlib.validation``.
"""

from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, validation  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ArtLibrary assets.")
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    log = cli.setup_logging()
    result = validation.validate_repository(args.root)

    for warning in result.warnings:
        log.warning("WARN  %s", warning)
    for error in result.errors:
        log.error("ERROR %s", error)

    log.info(
        "Validation finished: %d error(s), %d warning(s)",
        len(result.errors),
        len(result.warnings),
    )
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
