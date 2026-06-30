"""Upload orchestration shared by the single and batch upload entrypoints.

This is the single source of truth for *what an upload does*. ``upload_asset.py``
(single) and ``upload_assets_batch.py`` (batch) are both thin wrappers that parse
their payload into a list of :class:`payload.Payload` objects and hand it to
:func:`process_upload`. A single upload is simply a batch of one — there is no
duplicated upload logic anywhere.

Per-asset work (write → verify → optimize → embed metadata → thumbnail/favicon)
lives in :func:`process_one_asset`; the run-once work (rebuild index/report,
validate, commit, emit the result summary) lives in :func:`process_upload`.
"""

from __future__ import annotations

import os

from . import (
    constants,
    gitutil,
    hashing,
    imaging,
    indexing,
    metadata,
    optimize,
    paths,
    payload,
    reporting,
    summary,
    urls,
    validation,
)


class AssetError(Exception):
    """A recoverable per-asset failure: skip this asset, keep processing others."""


def process_one_asset(p: "payload.Payload", repository: str, log=None) -> dict:
    """Process a single asset in place and return its result record.

    Reconstructs the binary from chunks, verifies the SHA-256 (if supplied),
    optimizes, embeds (or sidecars) metadata, and generates thumbnail/favicons on
    request. Raises :class:`AssetError` on a hard per-asset problem (overwrite
    refused, hash mismatch) so the caller can record it and continue.

    The returned record is the per-file shape used in the result summary:
    ``{path, sha256, github_url, raw_url, thumbnail, favicons, metadata}``.
    """
    target = p.path

    if os.path.exists(target) and not p.allow_overwrite:
        raise AssetError(
            f"target already exists and allow_overwrite is false: {target}"
        )

    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    # Track every file this asset writes so we can roll it ALL back if anything
    # fails — a failed asset must never leave files behind that stage_all() would
    # commit, nor pollute the index/validation. This covers the SHA mismatch and
    # any unexpected error after the bytes are written (including an overwrite).
    created: list[str] = []
    try:
        data = payload.reconstruct_chunks(p.chunks)
        with open(target, "wb") as f:
            f.write(data)
        created.append(target)

        if p.sha256 and not hashing.verify_sha256(target, p.sha256):
            raise AssetError(
                f"SHA-256 mismatch for {target}: expected {p.sha256} "
                f"got {hashing.sha256_file(target)}"
            )

        # Optimize BEFORE embedding so EXIF-stripping optimizers can't drop metadata.
        if p.optimize:
            res = optimize.optimize_file(target)
            if log and res["saved"]:
                log.info("Optimized %s with %s, saved %d bytes", target, res["tool"], res["saved"])

        meta = metadata.build_authored_metadata(
            target,
            user_meta=p.metadata,
            original_filename=os.path.basename(target),
        )
        location = metadata.write_asset_metadata(target, meta)
        if location != "embedded":
            created.append(location)  # sidecar file
        if log:
            log.info("Metadata stored (%s): %s", location, target)

        thumbnail_rel = None
        if p.thumbnail:
            thumb = paths.thumbnail_path(target)
            if imaging.make_thumbnail(target, thumb):
                thumbnail_rel = thumb
                created.append(thumb)
                if log:
                    log.info("Thumbnail: %s", thumb)

        favicons: list[str] = []
        if p.favicon:
            favicons = imaging.make_favicons(target)
            created.extend(favicons)
            if favicons and log:
                log.info("Favicons: %s", ", ".join(favicons))

        sha = hashing.sha256_file(target)
        return {
            "path": target,
            "sha256": sha,
            "github_url": urls.github_url(repository, p.branch, target),
            "raw_url": urls.raw_url(repository, p.branch, target),
            "thumbnail": thumbnail_rel,
            "favicons": favicons,
            # "embedded" when the metadata lives in-band, else a sidecar was written.
            "metadata": "embedded" if location == "embedded" else "sidecar",
        }
    except Exception:
        for path in created:
            try:
                os.remove(path)
            except OSError:
                pass
        raise


def process_upload(
    payloads: list,
    branch: str,
    commit_message: str,
    repository: str,
    root: str = ".",
    log=None,
) -> tuple[dict, bool]:
    """Run a whole upload (one or many assets) and emit its result summary.

    Steps, exactly once for the run regardless of asset count:
      1. process every asset (continue past per-asset failures),
      2. rebuild ``asset-index.json`` / ``ASSET_INDEX.md`` / aggregate,
      3. regenerate the repository report,
      4. validate the repository (non-fatal — reported, not enforced here),
      5. write the result file and commit everything in ONE commit,
      6. write the GitHub step summary.

    Returns ``(summary, any_failed)``. ``any_failed`` is True if any asset failed,
    so the entrypoint can exit non-zero while still having committed the assets
    that did succeed.
    """
    uploaded: list = []
    failed: list = []
    for p in payloads:
        try:
            record = process_one_asset(p, repository, log)
            uploaded.append(record)
            if log:
                log.info("Uploaded %s", record["path"])
        except Exception as exc:  # AssetError or any unexpected per-asset error
            failed.append({"path": p.path, "error": str(exc)})
            if log:
                log.error("FAILED %s: %s", p.path, exc)

    # Rebuild all derived state INLINE from the assets now on disk. A push made
    # with the default GITHUB_TOKEN does not trigger the push-driven Asset Index
    # / Validate workflows, so the upload must index itself to stay consistent.
    index = indexing.build_index(root, repository, branch)
    indexing.write_index(root, index)
    report = reporting.build_report(root)
    reporting.write_report(root, report)

    val = validation.validate_repository(root)
    if log:
        for warning in val.warnings:
            log.warning("WARN  %s", warning)
        for error in val.errors:
            log.error("ERROR %s", error)

    # Whether the derived index/report actually changed (vs an idempotent rerun).
    # Join root so the dirty check points at the files we actually wrote when
    # process_upload runs against a non-cwd root.
    index_updated = gitutil.is_dirty(os.path.join(root, constants.INDEX_JSON))
    report_updated = gitutil.is_dirty(os.path.join(root, constants.REPORT_MD))

    status = "success" if not failed else "failure"
    result = summary.build_summary(
        status=status,
        branch=branch,
        commit_sha="",  # filled after the commit; see write_result_file note
        uploaded=uploaded,
        failed=failed,
        index_updated=index_updated,
        report_updated=report_updated,
        validation="success" if val.ok else "failure",
    )

    # Write the result file BEFORE committing so it lands in the same single
    # commit as the assets/index/report.
    summary.write_result_file(root, result)

    gitutil.configure_bot()
    gitutil.stage_all()
    commit_sha = ""
    if gitutil.commit_if_changed(commit_message, skip_ci=False):
        gitutil.push(branch)
        commit_sha = gitutil.head_sha()
        if log:
            log.info("Committed and pushed to %s (%s)", branch, commit_sha[:12])
    elif log:
        log.info("No changes to commit")

    # Surface the authoritative SHA on the ephemeral channels (stdout + step
    # summary); the committed result file keeps commit_sha empty by necessity.
    result["commit_sha"] = commit_sha
    summary.write_step_summary(result)

    return result, bool(failed)
