"""Autonomous image ingest — fetch an image by URL and land it as an asset.

This is the backend of the ``Ingest image`` workflow (repository_dispatch /
workflow_dispatch). The caller — typically Lubot's Custom GPT Action POSTing to
the GitHub dispatch API — supplies a *source* (an ``openaiFileIdRefs`` entry
whose signed ``download_link`` is valid for only ~5 minutes, a plain public
``image_url``, or a pre-staged in-repo ``source_path``) plus a slug and
authored metadata. This module downloads/loads the bytes, validates them, and
hands them to :func:`artlib.batch.process_upload`, so an ingested asset goes
through exactly the same optimize → embed-metadata → thumbnail → reindex →
validate → single-commit pipeline as a manual upload.

Observability contract: the dispatch API answers ``204`` with no run handle, so
``Reports/latest-ingest-result.json`` is committed on EVERY outcome (success /
noop / failure) with the caller's ``request_id`` echoed back. A poller matches
``request_id`` to tell a fresh result from a stale one; ``run_url`` links the
result to the Actions log.

Idempotency: the pipeline mutates bytes (optimization + metadata embed), so the
committed file's hash never equals the download's. The download hash is instead
stamped into the embedded metadata as ``source_sha256``; re-ingesting identical
bytes for an existing slug is detected there and reported as a ``noop`` success.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

from PIL import Image

from . import batch, constants, gitutil, paths, payload, urls

# Lowercase kebab, 1-64 chars, no leading/trailing/double reliance on regex:
# matches the worklist stable-ID style (ui-button-primary-stamp, home-keep).
SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,62}[a-z0-9])?$")

# A collection is exactly one directory segment under Assets/.
COLLECTION_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")

DEFAULT_COLLECTION = "AssetReport"
DEFAULT_LICENSE = "internal-game-art"
DEFAULT_GENERATOR = "lubot-dalle"

# Download retry cadence. The signed download_link dies ~5 minutes after
# ChatGPT mints it and the Actions queue has already eaten an unknown slice of
# that window, so retry fast and briefly — a slow backoff would outlive the
# link anyway.
RETRY_SLEEPS = (2, 5, 10)
DOWNLOAD_TIMEOUT = 30
_CHUNK = 1024 * 1024

# HTTP statuses that mean "the link itself is dead" — retrying cannot help;
# the caller must mint a fresh link (regenerate / resend the image).
_EXPIRED_STATUSES = {401, 403, 404, 410}


class IngestError(Exception):
    """An ingest failure with a machine-readable code for the result file."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass
class IngestRequest:
    slug: str
    collection: str = DEFAULT_COLLECTION
    title: str = ""
    description: str = ""
    prompt: str = ""
    tags: list = field(default_factory=list)
    kind: str = ""
    branch: str = "main"
    allow_overwrite: bool = False
    sha256: str = ""
    request_id: str = ""
    image_url: str = ""
    source_path: str = ""
    file_refs: list = field(default_factory=list)

    @property
    def source(self) -> str:
        """Which source will be used: staging > public URL > file refs."""
        if self.source_path:
            return "staging"
        if self.image_url:
            return "image_url"
        if self.file_refs:
            return "openaiFileIdRefs"
        return ""


# --------------------------------------------------------------------------
# Request parsing


def _parse_json_maybe(raw: str):
    """Parse env-supplied JSON, treating ''/'null' as absent.

    ``toJSON()`` of a missing client_payload key renders the string ``null`` —
    the workflow cannot distinguish that from real data, so we do it here.
    """
    raw = (raw or "").strip()
    if not raw or raw == "null":
        return None
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return raw  # plain string input (workflow_dispatch)


def parse_refs(raw: str) -> list:
    """Normalize ``openaiFileIdRefs`` into a list of download URLs.

    Tolerates every shape ChatGPT is known to send: a JSON array of objects
    (``{name, id, mime_type, download_link}``), an array of URL strings, a
    single object, or a single URL string.
    """
    data = _parse_json_maybe(raw)
    if data is None:
        return []
    if isinstance(data, (str, dict)):
        data = [data]
    if not isinstance(data, list):
        return []
    links = []
    for item in data:
        if isinstance(item, str) and item.strip():
            links.append(item.strip())
        elif isinstance(item, dict):
            link = str(item.get("download_link") or item.get("url") or "").strip()
            if link:
                links.append(link)
    return links


def parse_tags(raw: str) -> list:
    """Accept a JSON array (dispatch payload) or comma-separated string."""
    data = _parse_json_maybe(raw)
    if data is None:
        return []
    if isinstance(data, list):
        return [str(t).strip() for t in data if str(t).strip()]
    return [t.strip() for t in str(data).split(",") if t.strip()]


def _parse_bool(raw: str) -> bool:
    return str(raw or "").strip().lower() in ("true", "1", "yes")


def request_from_env(environ) -> IngestRequest:
    """Build an :class:`IngestRequest` from the ``ARTLIB_*`` environment."""
    get = lambda key: (environ.get(key) or "").strip()  # noqa: E731
    return IngestRequest(
        slug=get("ARTLIB_SLUG").lower(),
        collection=get("ARTLIB_COLLECTION") or DEFAULT_COLLECTION,
        title=get("ARTLIB_TITLE"),
        description=get("ARTLIB_DESCRIPTION"),
        prompt=get("ARTLIB_PROMPT"),
        tags=parse_tags(environ.get("ARTLIB_TAGS", "")),
        kind=get("ARTLIB_KIND"),
        branch=get("ARTLIB_BRANCH") or "main",
        allow_overwrite=_parse_bool(environ.get("ARTLIB_ALLOW_OVERWRITE")),
        sha256=get("ARTLIB_SHA256").lower(),
        request_id=get("ARTLIB_REQUEST_ID") or environ.get("GITHUB_RUN_ID", ""),
        image_url=get("ARTLIB_IMAGE_URL"),
        source_path=get("ARTLIB_SOURCE_PATH"),
        file_refs=parse_refs(environ.get("ARTLIB_FILE_REFS", "")),
    )


def validate_request(req: IngestRequest) -> None:
    if not req.slug:
        raise IngestError("bad_request", "slug is required")
    if not SLUG_RE.match(req.slug):
        raise IngestError(
            "bad_slug",
            f"slug {req.slug!r} must be lowercase kebab-case "
            "(a-z, 0-9, single hyphens, 1-64 chars)",
        )
    if not COLLECTION_RE.match(req.collection):
        raise IngestError(
            "bad_request", f"collection {req.collection!r} is not a valid directory name"
        )
    paths.validate_branch(req.branch)
    if req.source_path:
        paths.validate_repo_path(req.source_path)
        if not req.source_path.startswith(constants.INGEST_STAGING_DIR + "/"):
            raise IngestError(
                "bad_request",
                f"source_path must live under {constants.INGEST_STAGING_DIR}/",
            )
    if not req.source:
        raise IngestError(
            "refs_empty",
            "no image source: openaiFileIdRefs was empty/missing and no "
            "image_url or source_path was given — the file was not attached "
            "to the action call; regenerate the image and resend",
        )


# --------------------------------------------------------------------------
# Download + validation


class _HttpsOnlyRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if urllib.parse.urlparse(newurl).scheme != "https":
            raise IngestError(
                "download_failed", f"refusing redirect to non-https URL: {newurl}"
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _fetch_once(url: str, max_bytes: int) -> bytes:
    opener = urllib.request.build_opener(_HttpsOnlyRedirects())
    request = urllib.request.Request(url, headers={"User-Agent": "artlibrary-ingest"})
    chunks = []
    total = 0
    with opener.open(request, timeout=DOWNLOAD_TIMEOUT) as resp:
        while True:
            chunk = resp.read(_CHUNK)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise IngestError(
                    "too_large", f"download exceeded {max_bytes} bytes limit"
                )
            chunks.append(chunk)
    return b"".join(chunks)


def download(url: str, max_bytes: int = constants.INGEST_MAX_BYTES, log=None):
    """Fetch ``url`` with a fast bounded retry. Returns ``(bytes, attempts)``.

    Expired/forbidden links (401/403/404/410) fail immediately as
    ``link_expired`` — the signed download_link cannot recover, only a fresh
    dispatch can. Transient errors (timeouts, 5xx, 429) retry on a short
    cadence sized to the 5-minute link window.
    """
    if urllib.parse.urlparse(url).scheme != "https":
        raise IngestError("bad_request", f"image URL must be https: {url}")

    last_error = None
    for attempt in range(1, len(RETRY_SLEEPS) + 2):
        try:
            return _fetch_once(url, max_bytes), attempt
        except IngestError:
            raise
        except urllib.error.HTTPError as exc:
            if exc.code in _EXPIRED_STATUSES:
                raise IngestError(
                    "link_expired",
                    f"download link rejected with HTTP {exc.code} — the signed "
                    "link is expired or invalid; regenerate the image and resend",
                ) from exc
            if exc.code not in (429,) and exc.code < 500:
                raise IngestError(
                    "download_failed", f"download failed with HTTP {exc.code}"
                ) from exc
            last_error = f"HTTP {exc.code}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
        if attempt <= len(RETRY_SLEEPS):
            if log:
                log.warning(
                    "Download attempt %d failed (%s), retrying in %ds",
                    attempt,
                    last_error,
                    RETRY_SLEEPS[attempt - 1],
                )
            time.sleep(RETRY_SLEEPS[attempt - 1])
    raise IngestError(
        "download_failed",
        f"download failed after {len(RETRY_SLEEPS) + 1} attempts: {last_error}",
    )


def validate_image(data: bytes) -> str:
    """Verify ``data`` is a decodable PNG/JPEG/WEBP; return its extension."""
    if not data:
        raise IngestError("download_failed", "downloaded zero bytes")
    if len(data) > constants.INGEST_MAX_BYTES:
        raise IngestError(
            "too_large", f"image exceeds {constants.INGEST_MAX_BYTES} bytes limit"
        )
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.verify()
        with Image.open(io.BytesIO(data)) as img:
            detected = img.format or ""
    except Exception as exc:
        raise IngestError("not_an_image", f"payload is not a decodable image: {exc}")
    ext = constants.INGEST_FORMATS.get(detected)
    if not ext:
        raise IngestError(
            "unsupported_format",
            f"image format {detected or 'unknown'} not supported "
            f"(allowed: {', '.join(sorted(constants.INGEST_FORMATS))})",
        )
    return ext


# --------------------------------------------------------------------------
# Result file + commits


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_result(req: IngestRequest, status: str, **extra) -> dict:
    run_id = os.environ.get("GITHUB_RUN_ID", "")
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    repository = os.environ.get("GITHUB_REPOSITORY", "")
    result = {
        "status": status,
        "request_id": req.request_id,
        "error_code": None,
        "error": None,
        "slug": req.slug,
        "path": "",
        "raw_url": "",
        "github_url": "",
        "sha256": "",
        "source_sha256": "",
        "source": req.source,
        "branch": req.branch,
        "commit_sha": "",
        "attempts": 0,
        "finished_at": _utc_now_iso(),
        "run_id": run_id,
        "run_url": f"{server}/{repository}/actions/runs/{run_id}"
        if run_id and repository
        else "",
    }
    result.update(extra)
    return result


def write_result_file(result: dict, root: str = ".") -> str:
    os.makedirs(os.path.join(root, constants.REPORTS_DIR), exist_ok=True)
    path = os.path.join(root, constants.INGEST_RESULT_JSON)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return constants.INGEST_RESULT_JSON


def _commit_result_only(result: dict, message: str, root: str = ".", log=None) -> None:
    """Commit ONLY the ingest result file (noop / pre-pipeline failure paths).

    Never ``stage_all`` here — a failed ingest must not sweep unrelated
    working-tree state into a commit. Push errors are swallowed: the result
    file is best-effort observability, the run log is the fallback channel.
    """
    try:
        write_result_file(result, root)
        gitutil.configure_bot()
        gitutil.stage([constants.INGEST_RESULT_JSON])
        if gitutil.commit_if_changed(message, skip_ci=True):
            gitutil.push(result["branch"])
    except Exception as exc:  # pragma: no cover - depends on git/network state
        if log:
            log.error("Could not commit ingest result file: %s", exc)


# --------------------------------------------------------------------------
# Orchestration


def _existing_same_slug(req: IngestRequest, ext: str, root: str) -> tuple[str, str]:
    """Return (existing_rel_path, its source_sha256) for this slug, if any.

    Checks the exact target first, then sibling extensions, so a slug cannot
    silently exist twice with different formats.
    """
    from . import metadata  # local import to avoid cycles at module load

    candidates = [f"Assets/{req.collection}/{req.slug}.{ext}"] + [
        f"Assets/{req.collection}/{req.slug}.{other}"
        for other in sorted(set(constants.INGEST_FORMATS.values()) - {ext})
    ]
    for rel in candidates:
        full = os.path.join(root, rel)
        if os.path.exists(full):
            meta = metadata.read_asset_metadata(full) or {}
            return rel, str(meta.get("source_sha256") or "")
    return "", ""


def load_source_bytes(req: IngestRequest, root: str, log=None) -> tuple[bytes, int]:
    """Materialize the image bytes from whichever source the request carries."""
    if req.source_path:
        full = os.path.join(root, req.source_path)
        if not os.path.exists(full):
            raise IngestError(
                "bad_request", f"staged file not found: {req.source_path}"
            )
        with open(full, "rb") as f:
            return f.read(), 0
    url = req.image_url or req.file_refs[0]
    return download(url, log=log)


def run_ingest(environ, log=None, root: str = ".") -> tuple[dict, int]:
    """Execute one ingest end to end. Returns ``(result, exit_code)``."""
    started_at = _utc_now_iso()
    req = request_from_env(environ)
    repository = environ.get("GITHUB_REPOSITORY", "unknown/repo")

    try:
        validate_request(req)
    except IngestError as exc:
        # Branch may be unvalidated here; only commit the result when it is safe.
        result = build_result(
            req, "failure", error_code=exc.code, error=str(exc), started_at=started_at
        )
        try:
            paths.validate_branch(req.branch)
        except Exception:
            write_result_file(result, root)  # observable via run log/artifact only
        else:
            _commit_result_only(
                result, f"Ingest {req.slug or 'request'} failed: {exc.code}", root, log
            )
        return result, 1

    try:
        data, attempts = load_source_bytes(req, root, log)
        ext = validate_image(data)
        src_sha = hashlib.sha256(data).hexdigest()
        if req.sha256 and req.sha256 != src_sha:
            raise IngestError(
                "sha256_mismatch",
                f"caller-supplied sha256 {req.sha256} does not match "
                f"downloaded bytes {src_sha}",
            )

        target = f"Assets/{req.collection}/{req.slug}.{ext}"
        paths.validate_repo_path(target)

        existing_rel, existing_src_sha = _existing_same_slug(req, ext, root)
        if existing_rel and existing_src_sha == src_sha:
            result = build_result(
                req,
                "noop",
                path=existing_rel,
                source_sha256=src_sha,
                attempts=attempts,
                started_at=started_at,
                raw_url=urls.raw_url(repository, req.branch, existing_rel),
                github_url=urls.github_url(repository, req.branch, existing_rel),
                error=f"identical bytes already ingested as {existing_rel}",
            )
            _commit_result_only(
                result, f"Ingest {req.slug}: no-op (already present)", root, log
            )
            return result, 0
        if existing_rel and not req.allow_overwrite:
            raise IngestError(
                "exists_conflict",
                f"{existing_rel} already exists with different content; "
                "set allow_overwrite to replace it",
            )
        if existing_rel and existing_rel != target:
            # Same slug, different format: replace, don't accumulate.
            os.remove(os.path.join(root, existing_rel))
    except IngestError as exc:
        result = build_result(
            req, "failure", error_code=exc.code, error=str(exc), started_at=started_at
        )
        _commit_result_only(result, f"Ingest {req.slug} failed: {exc.code}", root, log)
        return result, 1

    if req.source_path:
        # The final commit both adds the asset and removes the staged blob.
        os.remove(os.path.join(root, req.source_path))

    user_meta = {
        "title": req.title or req.slug,
        "description": req.description,
        "prompt": req.prompt,
        "generator": DEFAULT_GENERATOR,
        "license": DEFAULT_LICENSE,
        "tags": req.tags,
        "collection": req.collection,
        "source_sha256": src_sha,
        "ingest_source": req.source,
    }
    if req.kind:
        user_meta["kind"] = req.kind

    p = payload.Payload(
        branch=req.branch,
        path=target,
        commit_message=f"Ingest {req.slug} [request {req.request_id}]",
        chunks=[base64.b64encode(data).decode("ascii")],
        metadata=user_meta,
        options={"thumbnail": True, "allow_overwrite": bool(existing_rel)},
    )

    outcome = {}

    def on_summary(upload_summary: dict) -> None:
        # Runs inside process_upload after its result file is written and
        # before staging — so this file joins the same single commit.
        if upload_summary["failed"]:
            outcome.update(
                build_result(
                    req,
                    "failure",
                    error_code="pipeline_failed",
                    error=upload_summary["failed"][0].get("error", "upload failed"),
                    source_sha256=src_sha,
                    attempts=attempts,
                    started_at=started_at,
                )
            )
        else:
            record = upload_summary["uploaded"][0]
            outcome.update(
                build_result(
                    req,
                    "success",
                    path=record["path"],
                    raw_url=record["raw_url"],
                    github_url=record["github_url"],
                    sha256=record["sha256"],
                    source_sha256=src_sha,
                    attempts=attempts,
                    started_at=started_at,
                )
            )
        write_result_file(outcome, root)

    upload_result, any_failed = batch.process_upload(
        [p],
        req.branch,
        p.commit_message,
        repository,
        root=root,
        log=log,
        on_summary=on_summary,
    )
    outcome["commit_sha"] = upload_result.get("commit_sha", "")
    return outcome, 1 if any_failed else 0
