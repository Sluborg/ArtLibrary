#!/usr/bin/env python3
"""Upload an asset from a JSON payload (Upload Asset workflow entrypoint).

Reconstructs a base64-chunked upload, verifies its hash, optimizes it, embeds
metadata, generates thumbnail/favicon on request, and commits the result.
All logic lives in ``artlib`` — this file only wires the steps together.

Payload is read from the ARTLIB_PAYLOAD environment variable (the workflow
passes the workflow_dispatch input through, avoiding writing it to disk).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from artlib import (  # noqa: E402
    cli,
    gitutil,
    hashing,
    imaging,
    metadata,
    optimize,
    paths,
    payload,
    urls,
)


def main() -> int:
    log = cli.setup_logging()
    repository, _ = cli.repo_branch_from_env()

    p = payload.parse_payload(os.environ.get("ARTLIB_PAYLOAD", ""))
    target = p.path

    if os.path.exists(target) and not p.allow_overwrite:
        log.error("Target already exists and allow_overwrite is false: %s", target)
        return 1

    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    data = payload.reconstruct_chunks(p.chunks)
    with open(target, "wb") as f:
        f.write(data)

    if p.sha256 and not hashing.verify_sha256(target, p.sha256):
        log.error("SHA-256 mismatch: expected %s got %s", p.sha256, hashing.sha256_file(target))
        return 1

    # Optimize BEFORE embedding so EXIF-stripping optimizers can't drop metadata.
    if p.optimize:
        res = optimize.optimize_file(target)
        if res["saved"]:
            log.info("Optimized %s with %s, saved %d bytes", target, res["tool"], res["saved"])

    meta = metadata.build_authored_metadata(
        target,
        user_meta=p.metadata,
        original_filename=os.path.basename(target),
    )
    location = metadata.write_asset_metadata(target, meta)
    log.info("Metadata stored: %s", location)

    committed_paths = [target]
    if location != "embedded":
        committed_paths.append(location)

    if p.thumbnail:
        thumb = paths.thumbnail_path(target)
        if imaging.make_thumbnail(target, thumb):
            committed_paths.append(thumb)
            log.info("Thumbnail: %s", thumb)

    if p.favicon:
        favicons = imaging.make_favicons(target)
        committed_paths.extend(favicons)
        if favicons:
            log.info("Favicons: %s", ", ".join(favicons))

    gitutil.configure_bot()
    gitutil.stage(committed_paths)
    # Asset commits are real content: do NOT skip CI — index/validate must run.
    if gitutil.commit_if_changed(p.commit_message, skip_ci=False):
        gitutil.push(p.branch)
        log.info("Committed and pushed to %s", p.branch)
    else:
        log.info("No changes to commit")

    sha = hashing.sha256_file(target)
    log.info("sha256=%s bytes=%d", sha, os.path.getsize(target))
    log.info("GitHub URL: %s", urls.github_url(repository, p.branch, target))
    log.info("Raw URL: %s", urls.raw_url(repository, p.branch, target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
