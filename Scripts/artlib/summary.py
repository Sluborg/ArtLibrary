"""Upload observability — the machine- and human-readable result of an upload.

Both upload entrypoints (single and batch) go through here so they report
completion identically. There are three sinks, fed from one summary dict:

  * ``Reports/latest-upload-result.json`` — the durable, committed record of the
    most recent upload workflow result (what Lubot reads to verify completion).
  * ``$GITHUB_STEP_SUMMARY`` — the human-facing run summary in the Actions UI.
  * the returned dict — printed to stdout by the entrypoint for the caller.

The summary shape is the contract Lubot depends on; keep it stable.
"""

from __future__ import annotations

import json
import os

from . import constants


def build_summary(
    *,
    status: str,
    branch: str,
    commit_sha: str,
    uploaded: list,
    failed: list,
    index_updated: bool,
    report_updated: bool,
    validation: str,
) -> dict:
    """Assemble the canonical upload result summary.

    Each ``uploaded`` entry is ``{path, sha256, github_url, raw_url, thumbnail,
    favicons, metadata}`` (see ``batch.process_one_asset``); each ``failed``
    entry is ``{path, error}``.
    """
    return {
        "status": status,
        "branch": branch,
        "commit_sha": commit_sha,
        "uploaded": uploaded,
        "failed": failed,
        "index_updated": index_updated,
        "report_updated": report_updated,
        "validation": validation,
    }


def write_result_file(root: str, summary: dict) -> str:
    """Persist the summary to ``Reports/latest-upload-result.json``.

    Returns the repo-relative path written.

    Note: this file is committed in the same single commit as the upload, so its
    ``commit_sha`` is necessarily empty in the committed copy — a commit cannot
    contain its own hash. The authoritative SHA is emitted to stdout and the
    step summary after the commit is made.
    """
    os.makedirs(os.path.join(root, constants.REPORTS_DIR), exist_ok=True)
    path = os.path.join(root, constants.UPLOAD_RESULT_JSON)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return constants.UPLOAD_RESULT_JSON


def render_step_summary_md(summary: dict) -> str:
    """Render the GitHub Step Summary markdown for an upload result."""
    ok = summary["status"] == "success"
    icon = "✅" if ok else "❌"
    lines = [
        "## Upload result",
        "",
        f"- **Status:** {icon} `{summary['status']}`",
        f"- **Branch:** `{summary['branch']}`",
        f"- **Commit:** `{summary['commit_sha'] or '—'}`",
        f"- **Index updated:** {'yes' if summary['index_updated'] else 'no'}",
        f"- **Report updated:** {'yes' if summary['report_updated'] else 'no'}",
        f"- **Validation:** `{summary['validation']}`",
        "",
    ]

    uploaded = summary.get("uploaded") or []
    if uploaded:
        lines += [
            f"### Uploaded ({len(uploaded)})",
            "",
            "| Asset | SHA-256 | Metadata | Thumbnail | Favicons | Links |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for u in uploaded:
            sha = (u.get("sha256") or "")[:12]
            thumb = f"`{u['thumbnail']}`" if u.get("thumbnail") else "—"
            favs = str(len(u.get("favicons") or [])) if u.get("favicons") else "—"
            links = f"[raw]({u['raw_url']}) · [view]({u['github_url']})"
            lines.append(
                f"| `{u['path']}` | `{sha}` | {u.get('metadata', '—')} | "
                f"{thumb} | {favs} | {links} |"
            )
        lines.append("")

    failed = summary.get("failed") or []
    if failed:
        lines += [f"### Failed ({len(failed)})", "", "| Asset | Error |", "| --- | --- |"]
        for f in failed:
            lines.append(f"| `{f.get('path', '?')}` | {f.get('error', '')} |")
        lines.append("")

    return "\n".join(lines) + "\n"


def write_step_summary(summary: dict) -> str:
    """Append the rendered markdown to ``$GITHUB_STEP_SUMMARY`` when set.

    Returns the markdown so callers can also log it locally. A no-op (still
    returns the markdown) when the env var is absent, e.g. local runs.
    """
    md = render_step_summary_md(summary)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(md)
        except OSError:
            pass
    return md
