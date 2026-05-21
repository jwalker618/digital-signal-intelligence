"""v8 Phase 2: peer cohort engine.

Public API surface for the cohort comparison feature that powers the
client portal's /peers view. See V8 Phase 2 doc for design.

Components:
  - bands: revenue band + NAICS section helpers (pure)
  - service: cohort key derivation + percentile math (pure)
  - queries: async DB helpers for upsert / lookup (impure)
"""
from .bands import (
    REVENUE_BANDS,
    band_for_revenue,
    naics_section_for,
)
from .service import (
    MIN_COHORT_SIZE,
    CohortKey,
    CohortStats,
    MissingCohortAttributesError,
    cohort_id_for,
    derive_cohort_key,
    normalize_entity_key,
    percentile_from_scores,
)

__all__ = [
    "REVENUE_BANDS",
    "band_for_revenue",
    "naics_section_for",
    "MIN_COHORT_SIZE",
    "CohortKey",
    "CohortStats",
    "MissingCohortAttributesError",
    "cohort_id_for",
    "derive_cohort_key",
    "normalize_entity_key",
    "percentile_from_scores",
]
