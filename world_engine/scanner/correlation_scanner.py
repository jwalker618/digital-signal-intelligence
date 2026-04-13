"""
WE-3a: Correlation Scanner

First stage of the discovery pipeline. For every pair of signal features
across the assessed population, compute Spearman's rho and filter to
statistically significant candidates.

Key design decisions:
- Coverage-agnostic: an entity assessed for both cyber and D&O contributes
  signals from both. Cross-coverage correlations are the highest-value
  discoveries (no single coverage config would encode them).
- Spearman's rho (not Pearson): handles non-linear monotonic relationships
  without assuming normality.
- Same-group pairs excluded: signals in the same signal group are designed
  to correlate; their agreement is expected, not a discovery.
- Runs against the latest ModelVersionRecord per entity (one row per entity)
  to build a clean entity × signal matrix.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import CandidateRelationship

logger = logging.getLogger("dsi.world_engine.scanner")


@dataclass
class ScannerConfig:
    """Tunable parameters for CorrelationScanner."""

    min_entities: int = 50
    """Minimum distinct entities required for meaningful correlation."""

    min_observations_per_pair: int = 30
    """For a given signal pair, both signals must have been observed in at
    least this many entities. Drops pairs where most entities have only
    one of the two signals."""

    rho_threshold: float = 0.3
    """Minimum |rho| to flag as a candidate."""

    p_threshold: float = 0.01
    """Maximum p-value to flag as a candidate."""


class CorrelationScanner:
    """Mines the assessment database for cross-signal correlations."""

    def __init__(self, config: Optional[ScannerConfig] = None):
        self.config = config or ScannerConfig()

    def scan(self, db: Session) -> list[CandidateRelationship]:
        """Return candidate relationships discovered in the current assessment database.

        Does not commit -- the caller is read-only on the DB side.
        """
        matrix, signal_codes, signal_groups, entity_coverages = self._build_matrix(db)
        if matrix is None:
            logger.info("Scanner: insufficient data, aborting scan")
            return []

        n_entities, n_signals = matrix.shape
        logger.info(
            "Scanner: matrix loaded -- %d entities × %d signals", n_entities, n_signals
        )

        candidates: list[CandidateRelationship] = []

        # Iterate over all signal pairs
        for i in range(n_signals):
            col_i = matrix[:, i]
            # Mask: entities where signal i has a value
            mask_i = ~np.isnan(col_i)

            for j in range(i + 1, n_signals):
                # Skip same-group pairs (these are designed to correlate)
                if signal_groups.get(signal_codes[i]) == signal_groups.get(signal_codes[j]):
                    continue

                col_j = matrix[:, j]
                mask_j = ~np.isnan(col_j)
                both = mask_i & mask_j

                n_obs = int(both.sum())
                if n_obs < self.config.min_observations_per_pair:
                    continue

                rho, p = stats.spearmanr(col_i[both], col_j[both])
                if np.isnan(rho) or np.isnan(p):
                    continue

                if abs(rho) < self.config.rho_threshold or p >= self.config.p_threshold:
                    continue

                # Coverage scope = union of coverages among the contributing entities
                contributing_entities = np.where(both)[0]
                coverage_scope = self._coverage_scope(contributing_entities, entity_coverages)

                candidates.append(
                    CandidateRelationship(
                        source_signal=signal_codes[i],
                        target_signal=signal_codes[j],
                        correlation_rho=float(rho),
                        p_value=float(p),
                        population_size=n_obs,
                        coverage_scope=coverage_scope,
                    )
                )

        logger.info("Scanner: %d candidates survived filtering", len(candidates))
        return candidates

    # ------------------------------------------------------------------
    # Matrix construction
    # ------------------------------------------------------------------

    def _build_matrix(self, db: Session):
        """Load ModelVersionSignal scores into an entity × signal numpy matrix.

        Returns (matrix, signal_codes_list, signal_group_map, entity_coverage_map)
        or (None, None, None, None) if the population is below threshold.

        Each entity is represented by its LATEST model version -- the
        current signal state. We don't attempt to average or weight by
        vintage here; that would require the temporal design of WE-3b.
        """
        # Step 1: for each entity, get the most recent model version
        entity_sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name,
                m.id        AS model_version_id,
                s.coverage
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            ORDER BY s.entity_name, m.created_at DESC
        """
        entity_rows = db.execute(text(entity_sql)).mappings().all()
        if len(entity_rows) < self.config.min_entities:
            logger.info(
                "Scanner: only %d entities (< %d required)",
                len(entity_rows),
                self.config.min_entities,
            )
            return None, None, None, None

        entity_name_to_row = {
            row["entity_name"]: idx for idx, row in enumerate(entity_rows)
        }
        entity_coverages: dict[int, set[str]] = {
            idx: {row["coverage"]} for idx, row in enumerate(entity_rows)
        }
        model_version_ids = [row["model_version_id"] for row in entity_rows]

        # Step 2: load all signal scores for those model versions
        scores_sql = """
            SELECT
                mv.model_version_id::text AS mv_id,
                sig.code                  AS signal_code,
                mv.group_code             AS group_code,
                mv.score
            FROM model_version_signals mv
            JOIN signals sig ON mv.signal_id = sig.id
            WHERE mv.model_version_id = ANY(:mv_ids)
              AND mv.score IS NOT NULL
        """
        score_rows = db.execute(
            text(scores_sql), {"mv_ids": model_version_ids}
        ).mappings().all()

        if not score_rows:
            logger.info("Scanner: no signal scores found for model versions")
            return None, None, None, None

        # Step 3: build the signal dimension + group map
        signal_codes_ordered: list[str] = []
        signal_code_to_col: dict[str, int] = {}
        signal_group_map: dict[str, str] = {}
        for row in score_rows:
            code = row["signal_code"]
            if code not in signal_code_to_col:
                signal_code_to_col[code] = len(signal_codes_ordered)
                signal_codes_ordered.append(code)
            if row["group_code"] and code not in signal_group_map:
                signal_group_map[code] = row["group_code"]

        # Step 4: fill the entity × signal matrix (NaN = missing)
        matrix = np.full(
            (len(entity_rows), len(signal_codes_ordered)), np.nan, dtype=np.float64
        )

        mv_to_entity_idx: dict = {
            str(row["model_version_id"]): idx for idx, row in enumerate(entity_rows)
        }

        for row in score_rows:
            entity_idx = mv_to_entity_idx.get(row["mv_id"])
            if entity_idx is None:
                continue
            col = signal_code_to_col[row["signal_code"]]
            matrix[entity_idx, col] = float(row["score"])

        return matrix, signal_codes_ordered, signal_group_map, entity_coverages

    def _coverage_scope(
        self, entity_indices: np.ndarray, entity_coverages: dict[int, set[str]]
    ) -> list[str]:
        """Union of coverage lines contributing to a signal pair."""
        scope: set[str] = set()
        for idx in entity_indices:
            scope.update(entity_coverages.get(int(idx), set()))
        return sorted(scope)
