"""Shared helpers for the thin CLI entrypoints in Scripts/.

Keeps environment plumbing (repo/branch discovery, logging) out of every
entrypoint so they stay tiny and uniform.
"""

from __future__ import annotations

import logging
import os
import subprocess


def setup_logging() -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO, format="%(message)s"
    )
    return logging.getLogger("artlib")


def repo_branch_from_env() -> tuple[str, str]:
    """Resolve (repository, branch) from the GitHub Actions environment.

    Falls back to git for local runs so the CLIs are usable off-CI.
    """
    repository = os.environ.get("GITHUB_REPOSITORY") or _git_remote_slug()
    branch = (
        os.environ.get("ARTLIB_BRANCH")
        or os.environ.get("GITHUB_REF_NAME")
        or _git_current_branch()
    )
    return repository, branch


def _git_current_branch() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            text=True,
            capture_output=True,
        )
        return out.stdout.strip()
    except Exception:
        return "main"


def _git_remote_slug() -> str:
    try:
        out = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True,
            text=True,
            capture_output=True,
        )
        url = out.stdout.strip()
        slug = url.rsplit(":", 1)[-1].rsplit("/", 2)[-2:]
        return "/".join(slug).removesuffix(".git")
    except Exception:
        return "unknown/repo"


def repo_root() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        )
        return out.stdout.strip()
    except Exception:
        return os.getcwd()
