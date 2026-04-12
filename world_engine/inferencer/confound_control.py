"""
WE-3b (part 2): Confound Controller

Eliminates spurious relationships explained by obvious confounders. For
each directed candidate, compute partial correlation between the source
and target signals while controlling for each confounder. If the partial
correlation drops below a threshold after controlling, the relationship
is discarded as spurious.

Confounders considered (when the data is available):
- entity_size_band
- industry_code
- geography (country_hint)
- assessment_vintage (binned by quarter)

At LEARN maturity most entities have simple demographics, so not every
confounder will be testable. Whatever is testable is recorded in
confounders_tested for audit.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.types import DirectedCandidate

logger = logging.getLogger("dsi.world_engine.inferencer.confound_control")


CONFOUNDERS = [
    "entity_size_band",
    "industry_code",
    "geography",
    "assessment_vintage",
]

PARTIAL_RHO_THRESHOLD = 0.2


class ConfoundController:
    """Filters out spurious relationships via partial correlation."""

    def __init__(self, partial_rho_threshold: float = PARTIAL_RHO_THRESHOLD):
        self.partial_rho_threshold = partial_rho_threshold

    def filter(
        self, candidates: list[DirectedCandidate], db: Session
    ) -> list[DirectedCandidate]:
        """Drop candidates whose correlation vanishes after controlling for confounders."""
        if not candidates:
            return []

        # Load the entity × (signal + confounder) matrix once
        entity_data = self._load_entity_data(db)
        if entity_data is None:
            # No data -- return candidates unchanged but tag that we tried
            for cand in candidates:
                cand.confounders_tested = []
            return candidates

        signal_matrix, signal_cols, confounder_matrix, confounder_cols = entity_data

        survivors: list[DirectedCandidate] = []
        for cand in candidates:
            confounders_used: list[str] = []
            passed = True

            src_col = signal_cols.get(cand.source_signal)
            tgt_col = signal_cols.get(cand.target_signal)
            if src_col is None or tgt_col is None:
                # Signal not in matrix (edge case) -- skip controlling
                cand.confounders_tested = []
                survivors.append(cand)
                continue

            for confounder, col in confounder_cols.items():
                partial_rho = self._partial_correlation(
                    signal_matrix[:, src_col],
                    signal_matrix[:, tgt_col],
                    confounder_matrix[:, col],
                )
                if partial_rho is None:
                    continue
                confounders_used.append(confounder)
                if abs(partial_rho) < self.partial_rho_threshold:
                    passed = False
                    break

            cand.confounders_tested = confounders_used
            if passed:
                survivors.append(cand)

        logger.info(
            "ConfoundController: %d candidates -> %d survivors",
            len(candidates),
            len(survivors),
        )
        return survivors

    # ------------------------------------------------------------------
    # Matrix construction
    # ------------------------------------------------------------------

    def _load_entity_data(self, db: Session):
        """Return (signal_matrix, signal_cols, confounder_matrix, confounder_cols)
        or None if insufficient data.

        Signal matrix: entity × signal (latest model version per entity).
        Confounder matrix: entity × encoded confounder.
        """
        entity_sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name,
                s.coverage,
                s.country_hint,
                m.id AS mv_id,
                m.created_at
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            ORDER BY s.entity_name, m.created_at DESC
        """
        entity_rows = db.execute(text(entity_sql)).mappings().all()
        if len(entity_rows) < 10:
            return None

        mv_ids = [row["mv_id"] for row in entity_rows]

        # Signal matrix
        scores_sql = """
            SELECT
                mvs.model_version_id::text AS mv_id,
                sig.code AS signal_code,
                mvs.score
            FROM model_version_signals mvs
            JOIN signals sig ON sig.id = mvs.signal_id
            WHERE mvs.model_version_id = ANY(:mv_ids)
              AND mvs.score IS NOT NULL
        """
        score_rows = db.execute(text(scores_sql), {"mv_ids": mv_ids}).mappings().all()
        if not score_rows:
            return None

        signal_cols: dict[str, int] = {}
        for row in score_rows:
            code = row["signal_code"]
            if code not in signal_cols:
                signal_cols[code] = len(signal_cols)

        signal_matrix = np.full((len(entity_rows), len(signal_cols)), np.nan, dtype=float)
        mv_to_idx = {str(row["mv_id"]): idx for idx, row in enumerate(entity_rows)}
        for row in score_rows:
            ei = mv_to_idx.get(row["mv_id"])
            if ei is None:
                continue
            signal_matrix[ei, signal_cols[row["signal_code"]]] = float(row["score"])

        # Confounder matrix -- label-encoded (integers) then normalised
        confounder_cols: dict[str, int] = {}
        confounder_raw: dict[str, list] = {}

        # geography = country_hint (string -> integer label)
        geos = [row.get("country_hint") or "" for row in entity_rows]
        if len(set(geos)) > 1:
            confounder_cols["geography"] = len(confounder_cols)
            confounder_raw["geography"] = geos

        # assessment_vintage -- quarter bucket of created_at
        vintages = [
            f"{row['created_at'].year}Q{(row['created_at'].month - 1) // 3 + 1}"
            if row["created_at"] else ""
            for row in entity_rows
        ]
        if len(set(vintages)) > 1:
            confounder_cols["assessment_vintage"] = len(confounder_cols)
            confounder_raw["assessment_vintage"] = vintages

        # entity_size_band + industry_code live in submission_data (JSONB)
        # which requires a separate read. Skip for now unless populated
        # via an explicit confounder table in later phases.
        # Leaving hooks in place for a later enrichment pass.

        if not confounder_cols:
            # No confounders testable -- return an empty confounder matrix
            return signal_matrix, signal_cols, np.zeros((len(entity_rows), 0)), {}

        confounder_matrix = np.zeros((len(entity_rows), len(confounder_cols)), dtype=float)
        for name, col in confounder_cols.items():
            values = confounder_raw[name]
            unique = {v: i for i, v in enumerate(sorted(set(values)))}
            confounder_matrix[:, col] = [unique[v] for v in values]

        return signal_matrix, signal_cols, confounder_matrix, confounder_cols

    # ------------------------------------------------------------------
    # Partial correlation
    # ------------------------------------------------------------------

    def _partial_correlation(
        self, x: np.ndarray, y: np.ndarray, z: np.ndarray
    ) -> Optional[float]:
        """Compute partial correlation of x and y controlling for z.

        Partial rho = (r_xy - r_xz * r_yz) / sqrt((1 - r_xz^2)(1 - r_yz^2))
        """
        mask = ~(np.isnan(x) | np.isnan(y) | np.isnan(z))
        if mask.sum() < 10:
            return None
        x_m, y_m, z_m = x[mask], y[mask], z[mask]

        # Guard against zero-variance series
        if np.std(x_m) < 1e-10 or np.std(y_m) < 1e-10 or np.std(z_m) < 1e-10:
            return None

        r_xy = np.corrcoef(x_m, y_m)[0, 1]
        r_xz = np.corrcoef(x_m, z_m)[0, 1]
        r_yz = np.corrcoef(y_m, z_m)[0, 1]

        denom = np.sqrt((1 - r_xz**2) * (1 - r_yz**2))
        if denom < 1e-10:
            return None

        return float((r_xy - r_xz * r_yz) / denom)
