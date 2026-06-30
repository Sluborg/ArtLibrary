"""Upload payload parsing — the contract between the caller and the Upload flow.

Preserves the original workflow's payload schema and validation semantics
exactly: required keys, path/branch character safety, chunk reconstruction.
The caller is typically an AI agent or API submitting a base64-chunked asset.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field

from .paths import validate_branch, validate_repo_path

REQUIRED_KEYS = ("branch", "path", "commit_message", "chunks")

# A batch payload shares branch + commit_message across many assets; each asset
# carries the per-file fields (path, chunks, sha256, metadata, options).
BATCH_REQUIRED_KEYS = ("branch", "commit_message", "assets")
ASSET_REQUIRED_KEYS = ("path", "chunks")


@dataclass
class Payload:
    branch: str
    path: str
    commit_message: str
    chunks: list
    sha256: str = ""
    metadata: dict = field(default_factory=dict)
    options: dict = field(default_factory=dict)

    def option(self, key: str, default):
        value = self.options.get(key, default)
        return value

    @property
    def optimize(self) -> bool:
        return bool(self.options.get("optimize", True))

    @property
    def thumbnail(self) -> bool:
        return bool(self.options.get("thumbnail", False))

    @property
    def favicon(self) -> bool:
        return bool(self.options.get("favicon", False))

    @property
    def allow_overwrite(self) -> bool:
        return bool(self.options.get("allow_overwrite", False))


def parse_payload(raw: str) -> Payload:
    """Parse and validate a JSON upload payload, raising ValueError on problems."""
    if not raw:
        raise ValueError("Missing workflow payload")

    data = json.loads(raw)
    for key in REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    chunks = data["chunks"]
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("chunks must be a non-empty array")

    path = validate_repo_path(data["path"])
    branch = validate_branch(data["branch"])

    meta = data.get("metadata", {}) or {}
    if not isinstance(meta, dict):
        raise ValueError("metadata must be an object when provided")

    options = data.get("options", {}) or {}
    if not isinstance(options, dict):
        raise ValueError("options must be an object when provided")

    return Payload(
        branch=branch,
        path=path,
        commit_message=data["commit_message"],
        chunks=chunks,
        sha256=data.get("sha256", "") or "",
        metadata=meta,
        options=options,
    )


@dataclass
class BatchPayload:
    """A batch upload: one branch + commit_message, many per-asset payloads.

    Each entry in ``assets`` is a fully-formed :class:`Payload` carrying the
    shared ``branch`` / ``commit_message`` so the single-asset processing code
    can consume batch and single uploads through the exact same type.
    """

    branch: str
    commit_message: str
    assets: list  # list[Payload]


def parse_batch_payload(raw: str) -> BatchPayload:
    """Parse and validate a JSON batch upload payload, raising ValueError on problems.

    Reuses the single-asset validation (path safety, chunk shape, metadata /
    options types) for every entry so batch and single uploads enforce an
    identical contract.
    """
    if not raw:
        raise ValueError("Missing workflow payload")

    data = json.loads(raw)
    for key in BATCH_REQUIRED_KEYS:
        if key not in data:
            raise ValueError(f"Missing required key: {key}")

    branch = validate_branch(data["branch"])
    commit_message = data["commit_message"]

    assets = data["assets"]
    if not isinstance(assets, list) or not assets:
        raise ValueError("assets must be a non-empty array")

    payloads: list = []
    for i, asset in enumerate(assets):
        if not isinstance(asset, dict):
            raise ValueError(f"assets[{i}] must be an object")
        for key in ASSET_REQUIRED_KEYS:
            if key not in asset:
                raise ValueError(f"assets[{i}] missing required key: {key}")

        chunks = asset["chunks"]
        if not isinstance(chunks, list) or not chunks:
            raise ValueError(f"assets[{i}].chunks must be a non-empty array")

        path = validate_repo_path(asset["path"])

        meta = asset.get("metadata", {}) or {}
        if not isinstance(meta, dict):
            raise ValueError(f"assets[{i}].metadata must be an object when provided")

        options = asset.get("options", {}) or {}
        if not isinstance(options, dict):
            raise ValueError(f"assets[{i}].options must be an object when provided")

        payloads.append(
            Payload(
                branch=branch,
                path=path,
                commit_message=commit_message,
                chunks=chunks,
                sha256=asset.get("sha256", "") or "",
                metadata=meta,
                options=options,
            )
        )

    return BatchPayload(branch=branch, commit_message=commit_message, assets=payloads)


def reconstruct_chunks(chunks: list) -> bytes:
    """Join base64 chunk fragments and decode to the original bytes."""
    joined = "".join(chunks)
    return base64.b64decode(joined)
