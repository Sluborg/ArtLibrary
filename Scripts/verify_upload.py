#!/usr/bin/env python3
"""Verify that an expected upload landed correctly.

Machine-verifiable completion check for Lubot: after dispatching an upload
workflow and waiting for it to finish, run this against the (pulled) repository
to confirm the assets really arrived and the library is consistent.

For each expected asset it checks:
  * the asset file exists on disk,
  * its thumbnail / favicons exist when the upload produced them
    (derived from Reports/latest-upload-result.json),
  * asset-index.json includes the asset,
  * ASSET_INDEX.md includes the asset,
  * Reports/latest-upload-result.json exists and lists the asset.

Outputs a JSON report and exits non-zero if any check fails.

    python Scripts/verify_upload.py \\
      --expected Generated/testA.png \\
      --expected Generated/testB.png \\
      --expected Generated/testC.png
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import constants  # noqa: E402


def _load_json(path: str):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def verify(expected: list, root: str = ".") -> dict:
    """Return a structured verification report for the expected assets."""
    checks: list = []

    def record(name: str, ok: bool, detail: str = "") -> bool:
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        return ok

    index = _load_json(os.path.join(root, constants.INDEX_JSON))
    index_paths = (
        {a.get("path") for a in index.get("assets", [])} if isinstance(index, dict) else set()
    )
    record(
        f"{constants.INDEX_JSON} loads",
        isinstance(index, dict),
        "" if isinstance(index, dict) else "missing or invalid JSON",
    )

    md_text = ""
    md_path = os.path.join(root, constants.INDEX_MD)
    try:
        with open(md_path, "r", encoding="utf-8") as f:
            md_text = f.read()
        record(f"{constants.INDEX_MD} loads", True)
    except OSError:
        record(f"{constants.INDEX_MD} loads", False, "missing")

    result = _load_json(os.path.join(root, constants.UPLOAD_RESULT_JSON))
    record(
        f"{constants.UPLOAD_RESULT_JSON} loads",
        isinstance(result, dict),
        "" if isinstance(result, dict) else "missing or invalid JSON",
    )
    uploaded = result.get("uploaded", []) if isinstance(result, dict) else []
    uploaded_by_path = {u.get("path"): u for u in uploaded}

    for rel in expected:
        record(f"{rel}: asset exists", os.path.exists(os.path.join(root, rel)))
        record(f"{rel}: in {constants.INDEX_JSON}", rel in index_paths)
        record(f"{rel}: in {constants.INDEX_MD}", rel in md_text)

        record(f"{rel}: in upload result", rel in uploaded_by_path)
        rec = uploaded_by_path.get(rel)
        if rec:
            # Verify the derived files the upload reported it produced.
            thumb = rec.get("thumbnail")
            if thumb:
                record(
                    f"{rel}: thumbnail {thumb} exists",
                    os.path.exists(os.path.join(root, thumb)),
                )
            for fav in rec.get("favicons") or []:
                record(
                    f"{rel}: favicon {fav} exists",
                    os.path.exists(os.path.join(root, fav)),
                )

    ok = all(c["ok"] for c in checks)
    failures = [c for c in checks if not c["ok"]]
    return {
        "ok": ok,
        "expected": list(expected),
        "checks": checks,
        "failures": failures,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an expected upload landed.")
    parser.add_argument(
        "--expected",
        action="append",
        default=[],
        metavar="PATH",
        help="repo-relative asset path that must exist (repeatable)",
    )
    parser.add_argument("--root", default=".")
    args = parser.parse_args()

    if not args.expected:
        parser.error("at least one --expected PATH is required")

    report = verify(args.expected, args.root)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
