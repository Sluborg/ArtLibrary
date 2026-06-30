"""ArtLibrary core library (``artlib``).

The single source of truth for every ArtLibrary operation. GitHub Actions
workflows call thin CLI wrappers in ``Scripts/`` that do nothing but parse
arguments and delegate here. A future MCP server, REST API, or the Lubot agent
itself imports this same package directly — so behaviour can never diverge
between "what the workflow does" and "what an agent does".

Public surface (import as ``from artlib import ...``):

    constants    naming/format/layout constants (change conventions here only)
    paths        path derivation + the repo-path security boundary
    hashing      SHA-256 content addressing
    urls         GitHub web/raw URL construction
    imaging      Pillow dimensions/thumbnails/favicons + in-band embedding
    metadata     the one reader/writer of asset metadata (embedded or sidecar)
    discovery    walk the repo, yield real assets, find orphans
    dedupe       duplicate detection by content hash
    optimize     lossless optimization (shared by Upload + Optimize-Repository)
    indexing     build asset-index.json / ASSET_INDEX.md / aggregate
    reporting    repository health report
    validation   push/PR validation gate
    gitutil      automated commit/push helpers
    payload      upload payload parsing + chunk reconstruction (single + batch)
    batch        upload orchestration shared by single + batch entrypoints
    summary      upload result summary, result file, and step summary
    cli          shared entrypoint helpers
"""

from . import (  # noqa: F401
    batch,
    cli,
    constants,
    dedupe,
    discovery,
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

__all__ = [
    "batch",
    "cli",
    "constants",
    "dedupe",
    "discovery",
    "gitutil",
    "hashing",
    "imaging",
    "indexing",
    "metadata",
    "optimize",
    "paths",
    "payload",
    "reporting",
    "summary",
    "urls",
    "validation",
]

__version__ = "1.0.0"
