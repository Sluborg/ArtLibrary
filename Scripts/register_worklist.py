#!/usr/bin/env python3
"""Append a worklist row atomically and losslessly (Register worklist entrypoint).

Lubot (or a human) dispatches the **Register worklist row** workflow to add a
row to a worklist table without reconstructing the whole doc. This thin wrapper
reads the dispatch inputs from the environment, calls
``artlib.worklist.register`` (which splices the row in and preserves everything
else byte-for-byte), then commits + pushes the change and writes the same
machine-readable result in three places (committed JSON, step summary, stdout).

Inputs, read from the environment (the workflow maps both ``workflow_dispatch``
inputs and ``repository_dispatch`` client_payload onto these):

    ARTLIB_WORKLIST   target doc path, e.g. Games/AssetReport/UI.md
    ARTLIB_ROWS       one or more markdown rows (JSON array or one per line)
    ARTLIB_TABLE      table locator: anchor key or heading substring
    ARTLIB_NOTE       optional trailing text to add once (may be empty)
    ARTLIB_MESSAGE    commit message
    ARTLIB_BRANCH     target branch (defaults to main)

Exit code is non-zero on any clean validation failure (missing file, table not
found, malformed/mismatched row) — and no commit is made in that case.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import cli, gitutil, worklist  # noqa: E402


def main() -> int:
    log = cli.setup_logging()
    _, branch = cli.repo_branch_from_env()

    worklist_path = os.environ.get("ARTLIB_WORKLIST", "").strip()
    rows = os.environ.get("ARTLIB_ROWS", "")
    table = os.environ.get("ARTLIB_TABLE", "").strip()
    note = os.environ.get("ARTLIB_NOTE", "")
    message = os.environ.get("ARTLIB_MESSAGE", "").strip() or "Register worklist row(s)"

    try:
        result, new_text = worklist.register(
            worklist=worklist_path,
            rows=rows,
            table=table,
            note=note,
            branch=branch,
        )
    except worklist.WorklistError as exc:
        # Fail cleanly: no file written, no commit. Report on every channel.
        failure = worklist.RegisterResult(
            status="failure",
            worklist=worklist_path,
            table=table,
            branch=branch,
            error=str(exc),
        )
        log.error("Registration failed: %s", exc)
        worklist.write_step_summary(failure)
        print(json.dumps(failure.to_dict(), indent=2))
        return 1

    if new_text is None:
        # Pure dedupe no-op: nothing changed in the doc, so nothing to commit.
        log.info(
            "No change: %d row(s) already present, nothing to commit",
            len(result.rows_skipped),
        )
        worklist.write_step_summary(result)
        print(json.dumps(result.to_dict(), indent=2))
        return 0

    # The doc changed — write it, record the result, and commit both in one go.
    # result.worklist is the validated, repo-relative path returned by register.
    with open(result.worklist, "w", encoding="utf-8", newline="") as f:
        f.write(new_text)
    result_rel = worklist.write_result_file(".", result)

    gitutil.configure_bot()
    gitutil.stage([result.worklist, result_rel])
    if gitutil.commit_if_changed(message, skip_ci=True):
        gitutil.push(branch)
        result.commit_sha = gitutil.head_sha()
        log.info(
            "Added %d row(s), skipped %d; pushed to %s (%s)",
            len(result.rows_added),
            len(result.rows_skipped),
            branch,
            result.commit_sha[:12],
        )
        # Rewrite the committed result file with the SHA on stdout only; the
        # committed copy keeps commit_sha empty (a commit can't hold its own hash).
    else:
        log.info("No changes to commit")

    worklist.write_step_summary(result)
    print(json.dumps(result.to_dict(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
