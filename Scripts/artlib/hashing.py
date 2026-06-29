"""SHA-256 helpers — content addressing for assets.

Hashes are always computed from real file bytes, never trusted from metadata,
so duplicate detection and integrity checks stay correct even if an embedded
block or sidecar is stale.
"""

from __future__ import annotations

import hashlib

_CHUNK = 1024 * 1024


def sha256_file(path: str) -> str:
    """Stream a file and return its hex SHA-256 digest."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(_CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of an in-memory buffer."""
    return hashlib.sha256(data).hexdigest()


def verify_sha256(path: str, expected: str) -> bool:
    """True if the file's digest equals ``expected`` (case-insensitive)."""
    if not expected:
        return True
    return sha256_file(path).lower() == expected.strip().lower()
