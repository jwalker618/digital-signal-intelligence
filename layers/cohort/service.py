"""v8 Phase 2: cohort key derivation + percentile math.

Pure functions. No DB access -- all DB work lives in queries.py.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field

from .bands import band_for_revenue, naics_section_for


# A cohort with fewer members than this returns None for percentile.
# 10 is the smallest sample size where a percentile carries any
# meaning; below it we surface "not enough peers" in the UI rather
# than a bogus number. See V8 Phase 2 doc, "Honest under thin data".
MIN_COHORT_SIZE: int = 10


@dataclass(frozen=True)
class CohortKey:
    """The triple that identifies a peer cohort."""
    coverage: str
    naics_section: str
    revenue_band: str


class CohortStats(BaseModel):
    """Summary statistics for a cohort. Always reflects current membership."""
    cohort_id: str
    size: int
    mean: float
    median: float
    p25: Optional[float] = None
    p75: Optional[float] = None


class SignalRankEntry(BaseModel):
    """One signal's standing relative to its cohort. Used by /peers view."""
    signal_id: str
    entity_value: float
    cohort_mean: float
    z_score: float


class SignalRanking(BaseModel):
    """Top strengths and bottom weaknesses, each truncated to length 3."""
    strengths: list[SignalRankEntry] = Field(default_factory=list)
    weaknesses: list[SignalRankEntry] = Field(default_factory=list)


class MissingCohortAttributesError(Exception):
    """Raised when an entity lacks NAICS or revenue and cannot be cohorted.

    Callers (the persistence layer) catch this and leave the
    peer_cohort_* fields NULL on the model version. Not a workflow
    failure -- just a "this entity opts out of peer comparison" signal.
    """


def normalize_entity_key(entity_name: str) -> str:
    """Canonical key for cohort_membership: lowercased, whitespace-stripped.

    Two submissions with entity_name 'Acme Industries' and
    ' acme industries ' produce the same key. Cross-tenant collisions
    (two different real companies with the same name) are accepted -- v8
    treats them as the same cohort member. v8.1 may introduce stronger
    identity if real-world deployment requires it.
    """
    return entity_name.strip().lower()


def derive_cohort_key(submission_data: dict[str, Any], coverage: str) -> CohortKey:
    """Build a CohortKey from a submission_data payload + coverage line.

    submission_data is the JSONB payload on infrastructure.db.models.Submission.
    Expected keys: 'naics' (str or int) and 'revenue' (numeric, in USD).
    Either may also appear under aliases ('naics_code', 'annual_revenue').

    Raises MissingCohortAttributesError if either attribute is absent
    or unparseable. Callers should treat this as "skip cohort assignment"
    rather than a workflow error.
    """
    if not submission_data:
        raise MissingCohortAttributesError(
            "submission_data is empty -- no NAICS or revenue available"
        )

    naics_raw = (
        submission_data.get("naics")
        or submission_data.get("naics_code")
        or submission_data.get("NAICS")
    )
    revenue_raw = (
        submission_data.get("revenue")
        or submission_data.get("annual_revenue")
        or submission_data.get("revenue_usd")
    )

    naics_section = naics_section_for(naics_raw)
    if naics_section is None:
        raise MissingCohortAttributesError(
            f"submission_data lacks usable NAICS (got {naics_raw!r})"
        )

    revenue_band = band_for_revenue(revenue_raw)
    if revenue_band is None:
        raise MissingCohortAttributesError(
            f"submission_data lacks usable revenue (got {revenue_raw!r})"
        )

    return CohortKey(
        coverage=coverage,
        naics_section=naics_section,
        revenue_band=revenue_band,
    )


def cohort_id_for(key: CohortKey) -> str:
    """Deterministic string form: '{coverage}:{naics}:{band}'.

    Used as the stored value in cohort_membership.cohort_id and
    model_versions.peer_cohort_id.
    """
    return f"{key.coverage}:{key.naics_section}:{key.revenue_band}"


def percentile_from_scores(scores: list[float], target: float) -> Optional[float]:
    """Percentile rank (0-100) of `target` within `scores`.

    Tie convention: ties get half credit (inclusive). A target tied
    with N members and below M members in a cohort of K gets
    (M + 0.5 * N) / K * 100.

    Returns None when the cohort is smaller than MIN_COHORT_SIZE.
    Returns 0.0 if target is below every score, 100.0 if target
    strictly exceeds every score.

    Pure function -- no DB access.
    """
    if len(scores) < MIN_COHORT_SIZE:
        return None
    below = sum(1 for s in scores if s < target)
    equal = sum(1 for s in scores if s == target)
    rank = (below + 0.5 * equal) / len(scores)
    return round(rank * 100.0, 1)


def cohort_stats_from_scores(cohort_id: str, scores: list[float]) -> Optional[CohortStats]:
    """Build a CohortStats from a sorted list of cohort composite scores.

    Returns None for cohorts below MIN_COHORT_SIZE.
    """
    if len(scores) < MIN_COHORT_SIZE:
        return None
    s_sorted = sorted(scores)
    n = len(s_sorted)
    return CohortStats(
        cohort_id=cohort_id,
        size=n,
        mean=round(statistics.fmean(s_sorted), 2),
        median=round(statistics.median(s_sorted), 2),
        p25=round(s_sorted[max(0, n // 4 - 1)], 2),
        p75=round(s_sorted[min(n - 1, (3 * n) // 4)], 2),
    )


def signal_ranking_from_values(
    entity_signals: dict[str, float],
    cohort_signals_by_id: dict[str, list[float]],
    *,
    top_n: int = 3,
) -> SignalRanking:
    """Compute strengths / weaknesses by Z-score against the cohort.

    Inputs:
      entity_signals: signal_id -> entity's score for that signal
      cohort_signals_by_id: signal_id -> list of cohort members' scores
        (excluding the entity itself if practical)

    For each signal that appears in both inputs, compute the entity's
    Z-score vs the cohort. Signals where the cohort sample is too thin
    (<5) or has zero standard deviation are skipped.

    Returns top_n strengths (highest positive Z) and top_n weaknesses
    (lowest negative Z). Empty lists if there's no usable data.
    """
    entries: list[SignalRankEntry] = []
    for signal_id, entity_value in entity_signals.items():
        cohort_values = cohort_signals_by_id.get(signal_id)
        if not cohort_values or len(cohort_values) < 5:
            continue
        try:
            mean = statistics.fmean(cohort_values)
            stddev = statistics.stdev(cohort_values)
        except statistics.StatisticsError:
            continue
        if stddev == 0:
            continue
        z = (entity_value - mean) / stddev
        entries.append(
            SignalRankEntry(
                signal_id=signal_id,
                entity_value=float(entity_value),
                cohort_mean=round(mean, 2),
                z_score=round(z, 2),
            )
        )

    entries_by_z_desc = sorted(entries, key=lambda e: e.z_score, reverse=True)
    strengths = [e for e in entries_by_z_desc if e.z_score > 0][:top_n]
    weaknesses_sorted = sorted(entries, key=lambda e: e.z_score)
    weaknesses = [e for e in weaknesses_sorted if e.z_score < 0][:top_n]
    return SignalRanking(strengths=strengths, weaknesses=weaknesses)
