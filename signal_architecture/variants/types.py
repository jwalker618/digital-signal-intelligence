"""V7 Phase 11 — variant-loop types.

Within-cycle amplification: when a high-grade signal is confirmed AND its
root-cause cluster has a deterministic contributor, the variant loop
generates up to N sibling queries that hunt for related findings on the
SAME entity (alternate spellings, subsidiaries, common officers, common
addresses, alternate jurisdictions).

Hard rules baked into the types:
  - Single-hop only. A variant signal carries variant_of=<parent
    signal_id> and a metadata flag the loop reads to refuse second-hop
    spawning.
  - Per-cycle cap. Enforced by the loop runner using
    EvidenceGradePolicy.variant_loop.max_per_entity_per_cycle.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

VariantKind = Literal[
    "name_variant",
    "subsidiary",
    "common_officer",
    "common_address",
    "alternate_jurisdiction",
]

VARIANT_KINDS: tuple[VariantKind, ...] = (
    "name_variant",
    "subsidiary",
    "common_officer",
    "common_address",
    "alternate_jurisdiction",
)


@dataclass(frozen=True)
class VariantQuery:
    """One generated query: a typed, bounded sibling-search recipe.

    The loop runner builds these from the validator-confirmed parent
    signal + its root-cause cluster, dispatches them to the appropriate
    inference function, and tags any resulting SignalResult with
    variant_of=parent_signal_id so single-hop is provable from the data.
    """
    kind: VariantKind
    target_ref: str           # the candidate entity/officer/address/etc.
    rationale: str            # <=200 chars, from the LLM
    parent_signal_id: str
    parent_cluster_id: str


@dataclass
class VariantResult:
    """Outcome of one variant query."""
    query: VariantQuery
    success: bool
    signal_id: Optional[str]  # if a signal was actually produced
    grade: Optional[str]      # EvidenceGrade literal of the produced signal
    note: str = ""
