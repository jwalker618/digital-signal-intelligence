"""V7 Phase 12 — mechanism-memory types.

A Mechanism is an ABSTRACT risk pattern extracted from a verified signal.
It deliberately strips entity names, addresses, dates, jurisdictions and
case identifiers so the pattern can apply to OTHER entities on future
cycles.

Mechanisms are persisted append-only (JSONL) per tenant. Idempotency is
by `canonical_signature`: the same primitive_type + summary always
produces the same signature, so re-extracting an equivalent mechanism
is a no-op rather than a duplicate row.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Mechanism:
    """One abstract risk pattern with provenance back to its source cluster.

    `recall_count` and `last_recalled_at` are mutated by `update_recall`
    when this mechanism is returned from a recall query; the JSONL store
    rewrites the file on update.
    """
    id: str
    summary: str                  # one-sentence abstract mechanism; no PII
    primitive_type: str           # e.g. "governance"
    sector_tags: list[str]        # ["fi", "do"] — coverages where this could recur
    tags: list[str]               # mechanism-level tags (snake_case)
    keywords: list[str]           # bag for recall
    what_made_it_high_grade: str  # brief explanation of why it earned its grade
    source_cluster_id: str        # cluster_id of the originating signal
    source_signal_id: str
    source_cycle_id: str          # model_version_id of the origin cycle
    first_seen: float = field(default_factory=time.time)
    last_recalled_at: float = 0.0
    recall_count: int = 0

    @property
    def canonical_signature(self) -> str:
        """Deterministic dedup key — primitive_type + summary."""
        key = f"{self.primitive_type}::{self.summary.strip().lower()}"
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "summary": self.summary,
            "primitive_type": self.primitive_type,
            "sector_tags": list(self.sector_tags),
            "tags": list(self.tags),
            "keywords": list(self.keywords),
            "what_made_it_high_grade": self.what_made_it_high_grade,
            "source_cluster_id": self.source_cluster_id,
            "source_signal_id": self.source_signal_id,
            "source_cycle_id": self.source_cycle_id,
            "first_seen": self.first_seen,
            "last_recalled_at": self.last_recalled_at,
            "recall_count": self.recall_count,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Mechanism":
        return cls(
            id=d["id"],
            summary=d["summary"],
            primitive_type=d["primitive_type"],
            sector_tags=list(d.get("sector_tags", [])),
            tags=list(d.get("tags", [])),
            keywords=list(d.get("keywords", [])),
            what_made_it_high_grade=d.get("what_made_it_high_grade", ""),
            source_cluster_id=d.get("source_cluster_id", ""),
            source_signal_id=d.get("source_signal_id", ""),
            source_cycle_id=d.get("source_cycle_id", ""),
            first_seen=float(d.get("first_seen", time.time())),
            last_recalled_at=float(d.get("last_recalled_at", 0.0)),
            recall_count=int(d.get("recall_count", 0)),
        )
