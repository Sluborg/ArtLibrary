#!/usr/bin/env python3
"""Ingest a remote image as an asset (Ingest image workflow entrypoint).

Reads the request from ARTLIB_* environment variables (wired by
.github/workflows/ingest-image.yml from workflow_dispatch inputs or a
repository_dispatch client_payload) and delegates everything to
``artlib.ingest.run_ingest``. All logic lives in ``artlib`` — this file only
wires the steps together and reports the machine-readable result.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, ingest  # noqa: E402


def main() -> int:
    log = cli.setup_logging()
    result, exit_code = ingest.run_ingest(os.environ, log=log)

    # Machine-readable summary to stdout (logging goes to stderr).
    print(json.dumps(result, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
