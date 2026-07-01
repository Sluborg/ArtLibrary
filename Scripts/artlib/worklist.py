"""Append-only, lossless worklist-row registration.

Worklist docs (``Games/<Project>/Buildings.md``, ``UI.md``, ``Resources.md``,
...) carry markdown tables that gain a row every time a visual is registered.
Lubot (a ChatGPT Custom GPT) can only *replace a whole file* through its GitHub
action and refuses to reconstruct a doc by hand, so it cannot safely append a
row. This module is the surgical alternative: it **splices** new rows in right
after a target table's last data row and changes nothing else — every byte
outside the spliced rows is preserved.

Guarantees (the whole point of this module):

  * **Additive / lossless.** The doc is never reconstructed or reformatted;
    only the new row lines are inserted. Everything else is byte-for-byte
    identical.
  * **Idempotent on slug.** A row whose stable slug (its first cell) already
    exists in the table is skipped and reported, never duplicated.
  * **Validated.** The file must exist, the table must be found, and every new
    row's column count must match the header — otherwise it fails cleanly with
    no write and no commit (never a malformed table).

Locating the table: pass ``table`` as either a machine-readable anchor key
(matches an ``<!-- worklist: <key> -->`` comment placed above the table) or a
heading substring (matches a ``#``-heading whose text contains it). The first
markdown table after the anchor/heading is the target.

Like the rest of ``artlib``, this is import-first: a workflow, an MCP server, or
the agent all call :func:`register` and get the same behaviour.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

from . import constants
from .paths import validate_branch, validate_repo_path


class WorklistError(ValueError):
    """A clean, user-facing failure: no file is written and no commit is made."""


# ``<!-- worklist: ui -->`` style anchor placed on its own line above a table.
_ANCHOR_RE = re.compile(r"<!--\s*worklist:\s*(?P<key>[^>]+?)\s*-->", re.IGNORECASE)
# A markdown ATX heading line, e.g. ``## Resource-icon worklist``.
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(?P<text>.*?)\s*#*\s*$")


@dataclass
class RegisterResult:
    """The machine-readable outcome of a registration run."""

    status: str
    worklist: str
    table: str
    branch: str
    commit_sha: str = ""
    rows_added: list = field(default_factory=list)
    rows_skipped: list = field(default_factory=list)
    note_added: bool = False
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "worklist": self.worklist,
            "table": self.table,
            "branch": self.branch,
            "commit_sha": self.commit_sha,
            "rows_added": self.rows_added,
            "rows_skipped": self.rows_skipped,
            "note_added": self.note_added,
            "error": self.error,
        }


# --- Text / table primitives ----------------------------------------------


def split_keepends(text: str) -> list[str]:
    """Split on ``\\n`` only, keeping the newline attached to each line.

    Unlike ``str.splitlines``, this never splits on other Unicode line
    boundaries (form feed, U+2028, ...), so ``"".join(split_keepends(t)) == t``
    for any text — the byte-preservation guarantee depends on it.
    """
    parts = text.split("\n")
    lines = [p + "\n" for p in parts[:-1]]
    if parts[-1] != "":
        lines.append(parts[-1])  # trailing content with no final newline
    return lines


def _newline_of(line: str) -> str:
    if line.endswith("\r\n"):
        return "\r\n"
    return "\n"


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|")


def split_cells(row: str) -> list[str]:
    """Split a markdown table row into its trimmed cell strings.

    Honours escaped pipes (``\\|``) so a cell may legitimately contain one.
    """
    s = row.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    cells = re.split(r"(?<!\\)\|", s)
    return [c.strip() for c in cells]


def column_count(row: str) -> int:
    return len(split_cells(row))


def is_separator(line: str) -> bool:
    """True for a header/body separator row like ``| --- | :--: |``."""
    if not is_table_row(line):
        return False
    cells = split_cells(line)
    return bool(cells) and all(re.fullmatch(r":?-{1,}:?", c) for c in cells)


def slug_of(row: str) -> str:
    """The stable slug = first cell, stripped of backticks/space, lowercased."""
    cells = split_cells(row)
    first = cells[0] if cells else ""
    return first.strip().strip("`").strip().lower()


def parse_rows(raw: str) -> list[str]:
    """Parse the ``rows`` input into a list of markdown row strings.

    Accepts either a JSON array of strings (``["| a | b |", ...]``) or one row
    per line. Blank lines are ignored.
    """
    if not raw:
        return []
    stripped = raw.strip()
    if not stripped:
        return []
    if stripped[0] == "[":
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    return [ln.strip() for ln in stripped.splitlines() if ln.strip()]


# --- Table location --------------------------------------------------------


@dataclass
class TableSpan:
    header_idx: int
    sep_idx: int
    last_data_idx: int  # == sep_idx when the table has no data rows yet


def _resolve_start(lines: list[str], table: str) -> int:
    """Return the line index to start scanning from for the target table.

    Tries an anchor-key match first (``<!-- worklist: <table> -->``), then a
    heading-substring match. Raises :class:`WorklistError` if neither is found.
    """
    key = table.strip().lower()
    for i, line in enumerate(lines):
        m = _ANCHOR_RE.search(line)
        if m and m.group("key").strip().lower() == key:
            return i + 1
    for i, line in enumerate(lines):
        m = _HEADING_RE.match(line)
        if m and key in m.group("text").lower():
            return i + 1
    raise WorklistError(
        f"table not found: no worklist anchor or heading matching {table!r}"
    )


def locate_table(lines: list[str], table: str) -> TableSpan:
    """Find the target table's header, separator, and last data-row indices.

    Scans forward from the resolved anchor/heading for the first ``header +
    separator`` pair. Stops at the next heading so a locator can never reach
    into an unrelated section's table.
    """
    start = _resolve_start(lines, table)
    j = start
    while j < len(lines) - 1:
        if _HEADING_RE.match(lines[j]):
            break  # ran into the next section without finding a table
        if is_table_row(lines[j]) and is_separator(lines[j + 1]):
            sep_idx = j + 1
            last = sep_idx
            k = sep_idx + 1
            while k < len(lines) and is_table_row(lines[k]) and not is_separator(lines[k]):
                last = k
                k += 1
            return TableSpan(header_idx=j, sep_idx=sep_idx, last_data_idx=last)
        j += 1
    raise WorklistError(
        f"table not found: no markdown table follows the location {table!r}"
    )


# --- Core operation --------------------------------------------------------


def register(
    *,
    worklist: str,
    rows: str,
    table: str,
    note: str = "",
    branch: str = "main",
    root: str = ".",
) -> tuple[RegisterResult, str | None]:
    """Splice ``rows`` into ``worklist``'s ``table``; append ``note`` once.

    Returns ``(result, new_text)``. ``new_text`` is the file's new contents when
    the document changed, or ``None`` when nothing changed (a pure dedupe no-op).
    The caller is responsible for writing/committing ``new_text`` — this function
    only touches disk to *read* the file, so a caller can preview a change.

    Raises :class:`WorklistError` on any validation failure (missing file,
    table not found, malformed/mismatched row) so the run fails cleanly with no
    write and no commit.
    """
    branch = validate_branch(branch)
    rel = validate_repo_path(worklist)
    if not table or not table.strip():
        raise WorklistError("table locator must be non-empty")

    full = os.path.join(root, rel)
    if not os.path.isfile(full):
        raise WorklistError(f"worklist file not found: {rel}")

    new_rows = parse_rows(rows)
    if not new_rows:
        raise WorklistError("rows must contain at least one markdown table row")

    with open(full, "r", encoding="utf-8", newline="") as f:
        text = f.read()
    lines = split_keepends(text)

    span = locate_table(lines, table)
    header_cols = column_count(lines[span.header_idx])

    # VALIDATE every incoming row up front — before any mutation — so a bad row
    # aborts the whole run and never produces a half-written / malformed table.
    for row in new_rows:
        if not is_table_row(row):
            raise WorklistError(f"not a markdown table row: {row!r}")
        cols = column_count(row)
        if cols != header_cols:
            raise WorklistError(
                f"row has {cols} column(s) but the table header has "
                f"{header_cols}: {row!r}"
            )

    existing_slugs = {
        slug_of(lines[i]) for i in range(span.sep_idx + 1, span.last_data_idx + 1)
    }

    result = RegisterResult(
        status="success", worklist=rel, table=table, branch=branch
    )
    to_insert: list[str] = []
    seen: set[str] = set()
    for row in new_rows:
        slug = slug_of(row)
        if slug in existing_slugs or slug in seen:
            result.rows_skipped.append(
                {"slug": slug, "reason": "duplicate slug already present"}
            )
            continue
        seen.add(slug)
        to_insert.append(row)
        result.rows_added.append({"slug": slug, "row": row.strip()})

    # Splice: insert the new row lines right after the last data row, changing
    # nothing else. Everything before and after is preserved byte-for-byte.
    if to_insert:
        newline = _newline_of(lines[span.header_idx])
        if not lines[span.last_data_idx].endswith("\n"):
            # Table is the last thing in a file with no trailing newline; give
            # the current final row a newline so the splice stays well-formed.
            lines[span.last_data_idx] = lines[span.last_data_idx] + newline
        insert_lines = [row.strip() + newline for row in to_insert]
        at = span.last_data_idx + 1
        lines = lines[:at] + insert_lines + lines[at:]

    new_text = "".join(lines)

    # NOTE: optional trailing text added exactly once (skipped if already
    # present anywhere in the doc). Appended at the end so it never disturbs the
    # table or any existing content.
    note_text = (note or "").strip()
    if note_text and note_text not in new_text:
        if new_text and not new_text.endswith("\n"):
            new_text += "\n"
        new_text += "\n" + note_text + "\n"
        result.note_added = True

    changed = new_text != text
    return result, (new_text if changed else None)


# --- Result sinks (mirrors summary.py for the upload flow) -----------------


def write_result_file(root: str, result: RegisterResult) -> str:
    """Persist the result to ``Reports/latest-worklist-result.json``.

    Like the upload result, the committed copy necessarily has an empty
    ``commit_sha`` (a commit cannot contain its own hash); the authoritative SHA
    is emitted to stdout and the step summary after the commit.
    """
    os.makedirs(os.path.join(root, constants.REPORTS_DIR), exist_ok=True)
    path = os.path.join(root, constants.WORKLIST_RESULT_JSON)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        f.write("\n")
    return constants.WORKLIST_RESULT_JSON


def render_step_summary_md(result: RegisterResult) -> str:
    """Render the GitHub Step Summary markdown for a registration result."""
    ok = result.status == "success"
    icon = "✅" if ok else "❌"
    lines = [
        "## Worklist registration",
        "",
        f"- **Status:** {icon} `{result.status}`",
        f"- **Worklist:** `{result.worklist}`",
        f"- **Table:** `{result.table}`",
        f"- **Branch:** `{result.branch}`",
        f"- **Commit:** `{result.commit_sha or '—'}`",
        f"- **Note added:** {'yes' if result.note_added else 'no'}",
        "",
    ]
    if result.error:
        lines += [f"> **Error:** {result.error}", ""]
    added = result.rows_added
    if added:
        lines += [f"### Rows added ({len(added)})", ""]
        lines += [f"- `{r['slug']}`" for r in added]
        lines.append("")
    skipped = result.rows_skipped
    if skipped:
        lines += [f"### Rows skipped ({len(skipped)})", ""]
        lines += [f"- `{r['slug']}` — {r['reason']}" for r in skipped]
        lines.append("")
    return "\n".join(lines) + "\n"


def write_step_summary(result: RegisterResult) -> str:
    """Append the rendered markdown to ``$GITHUB_STEP_SUMMARY`` when set."""
    md = render_step_summary_md(result)
    path = os.environ.get("GITHUB_STEP_SUMMARY")
    if path:
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(md)
        except OSError:
            pass
    return md
