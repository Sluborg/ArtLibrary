"""Git helpers for automated commits from workflows.

Centralizes the bot identity, the "nothing to commit" guard, and the
``[skip ci]`` marker that keeps derived-file commits from retriggering the
push-driven workflows (the self-healing loop guard).
"""

from __future__ import annotations

import subprocess

from . import constants


def _git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], check=check, text=True, capture_output=True)


def configure_bot() -> None:
    _git("config", "user.name", constants.BOT_NAME)
    _git("config", "user.email", constants.BOT_EMAIL)


def stage(paths) -> None:
    paths = [p for p in paths if p]
    if paths:
        _git("add", "--", *paths)


def stage_all() -> None:
    _git("add", "-A")


def has_staged_changes() -> bool:
    # `git diff --cached --quiet` exits 1 when there are staged changes.
    return _git("diff", "--cached", "--quiet", check=False).returncode != 0


def commit_if_changed(message: str, skip_ci: bool = True) -> bool:
    """Commit staged changes if any exist. Returns True if a commit was made."""
    if not has_staged_changes():
        return False
    if skip_ci and constants.SKIP_CI_MARKER not in message:
        message = f"{message} {constants.SKIP_CI_MARKER}"
    _git("commit", "-m", message)
    return True


def push(branch: str) -> None:
    _git("push", "origin", branch)
