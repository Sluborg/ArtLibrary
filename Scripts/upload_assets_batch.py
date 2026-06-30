#!/usr/bin/env python3
"""Upload many assets in one run (Upload assets (batch) workflow entrypoint).

Parses a batch payload (one branch + commit_message, many assets) and hands the
per-asset payloads to ``artlib.batch.process_upload`` — the same code path the
single upload uses. Every asset is processed (a failing asset is recorded and
skipped, not fatal), then the index/report are rebuilt, the repository is
validated, and everything is committed in a single commit.

Payload is read from the ARTLIB_PAYLOAD environment variable (the workflow
passes the workflow_dispatch input through, avoiding writing it to disk).
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import batch, cli, payload  # noqa: E402


def main() -> int:
    log = cli.setup_logging()
    repository, _ = cli.repo_branch_from_env()

    bp = payload.parse_batch_payload(os.environ.get("ARTLIB_PAYLOAD", ""))
    log.info("Batch upload: %d asset(s) -> %s", len(bp.assets), bp.branch)

    result, any_failed = batch.process_upload(
        bp.assets, bp.branch, bp.commit_message, repository, log=log
    )

    # Machine-readable summary to stdout (logging goes to stderr).
    print(json.dumps(result, indent=2))
    return 1 if any_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
