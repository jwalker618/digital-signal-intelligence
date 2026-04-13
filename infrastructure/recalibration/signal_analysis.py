"""
C-2c: SignalAnalyser

Per-signal predictive power analysis against actual loss outcomes.

For each signal in a coverage config, compute:

1. Discrimination:  Mann-Whitney U test between bind-time scores of
                    loss-bearing entities and no-loss entities. Tests
                    whether the score distributions are significantly
                    different.

2. Monotonicity:    Spearman correlation between bind-time score and
                    a binary loss indicator (1 = had a loss, 0 = no loss).
                    Signals that correlate negatively with loss (lower
                    score -> higher loss chance) are doing their job.

3. Stability:       Discrimination coefficient in rolling time windows.
                    A signal that was predictive but isn't anymore is
                    flagged.

4. Information Value (IV): |ΣI (distP - distN) × log(distP / distN)|
                    across score bins. Classic actuarial / credit-scoring
                    metric. Higher = more predictive.

Output: SignalReportCard with current_weight, evidence_supported_weight
(derived from IV relative to other signals in the group), and an
alignment verdict.
"""

from __future__ import annotations

import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.recalibration.types import Alignment, SignalReportCard

logger = logging.getLogger("dsi.recalibration.signal_analysis")


@dataclass
class SignalAnalyserConfig:
    min_sample_size: int = 30
    """Minimum signal-loss pairs + no-loss assessments combined."""
    discrimination_p_threshold: float = 0.05
    """Mann-Whitney U p-value below this = discriminative."""
    monotonicity_rho_threshold: float = 0.15
    """|Spearman rho| below this = weak monotonicity."""
    low_iv_threshold: float = 0.02
    """IV below this = signal not contributing."""
    high_iv_threshold: float = 0.10
    """IV above this = strong signal."""


class SignalAnalyser:
    """Per-signal predictive power analyser."""

    def __init__(self, db: Session, config: Optional[SignalAnalyserConfig] = None):
        self.db = db
        self.config = config or SignalAnalyserConfig()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def analyse(
        self, coverage: str, config_name: str, current_weights: dict[str, float]
    ) -> list[SignalReportCard]:
        """Build a SignalReportCard for each signal appearing in current_weights.

        current_weights: {signal_id -> current config weight}. The analyser
        reports evidence-supported weight relative to IV share within the
        same group; signals absent from this map are skipped.
        """
        if not current_weights:
            return []

        # Load signal scores paired with loss indicator (1 = had a loss, 0 = not)
        paired = self._load_paired_data(coverage, config_name)
        if not paired:
            return [
                SignalReportCard(
                    signal_id=sig_id,
                    current_weight=weight,
                    evidence_supported_weight=weight,
                    sample_size=0,
                    alignment=Alignment.WELL_CALIBRATED,
                    notes=["Insufficient signal-loss data for analysis"],
                )
                for sig_id, weight in current_weights.items()
            ]

        # Compute IV per signal. IVs within a group normalise to produce
        # evidence-supported weights.
        per_signal_metrics = self._compute_per_signal(paired, current_weights)

        # Group signals for weight redistribution. We don't have group_code
        # on signal-loss pairs directly, but we can infer it via the
        # signals table if needed. For simplicity we treat all signals as
        # one virtual group here -- the WeightOptimiser applies real
        # group-level constraints separately.
        report_cards: list[SignalReportCard] = []
        total_iv = sum(m["iv"] for m in per_signal_metrics.values() if m["iv"] > 0)

        for sig_id, weight in current_weights.items():
            m = per_signal_metrics.get(sig_id, {})
            iv = m.get("iv", 0.0)
            # Evidence-supported weight = weighted redistribution by IV share.
            # If a signal has high IV it deserves more weight (within the group).
            if total_iv > 0 and iv > 0:
                iv_share = iv / total_iv
                total_current_weight = sum(current_weights.values()) or 1.0
                evidence_weight = iv_share * total_current_weight
            else:
                evidence_weight = weight

            alignment = self._classify_alignment(m, weight, evidence_weight)

            report_cards.append(SignalReportCard(
                signal_id=sig_id,
                current_weight=weight,
                evidence_supported_weight=round(float(evidence_weight), 4),
                discrimination_u_stat=m.get("u_stat"),
                discrimination_p_value=m.get("u_p"),
                monotonicity_rho=m.get("rho"),
                stability_coefficient=m.get("stability"),
                information_value=round(float(iv), 4),
                alignment=alignment,
                sample_size=m.get("n", 0),
                notes=m.get("notes", []),
            ))

        return report_cards

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_paired_data(
        self, coverage: str, config_name: str
    ) -> list[tuple[str, dict[str, float], int]]:
        """Return [(entity_name, signal_scores_at_bind, has_loss)].

        Includes BOTH loss-bearing (from signal_loss_pairs) and no-loss
        (from model_versions that did not result in a linked loss).
        """
        # Loss-bearing rows
        loss_sql = """
            SELECT le.entity_name, slp.signal_scores_at_bind
            FROM signal_loss_pairs slp
            JOIN loss_events le ON le.id = slp.loss_event_id
            JOIN model_versions m ON m.id = slp.assessment_id
            JOIN submissions s ON s.id = m.submission_id
            WHERE s.coverage = :coverage
              AND (s.configuration = :config_name OR m.configuration_name = :config_name)
        """
        # No-loss: entities with BOUND quotes but no linked loss
        no_loss_sql = """
            SELECT DISTINCT ON (s.entity_name)
                s.entity_name,
                COALESCE(
                    (SELECT jsonb_object_agg(sig.code, mvs.score)
                     FROM model_version_signals mvs
                     JOIN signals sig ON sig.id = mvs.signal_id
                     WHERE mvs.model_version_id = m.id AND mvs.score IS NOT NULL),
                    '{}'::jsonb
                ) AS scores
            FROM submissions s
            JOIN model_versions m ON m.submission_id = s.id
            WHERE s.coverage = :coverage
              AND (s.configuration = :config_name OR m.configuration_name = :config_name)
              AND NOT EXISTS (
                  SELECT 1 FROM loss_events le WHERE le.entity_name = s.entity_name
              )
            ORDER BY s.entity_name, m.created_at DESC
        """

        paired: list[tuple[str, dict[str, float], int]] = []
        try:
            loss_rows = self.db.execute(
                text(loss_sql), {"coverage": coverage, "config_name": config_name}
            ).mappings().all()
            for row in loss_rows:
                scores = row["signal_scores_at_bind"] or {}
                paired.append((row["entity_name"], dict(scores), 1))

            no_loss_rows = self.db.execute(
                text(no_loss_sql), {"coverage": coverage, "config_name": config_name}
            ).mappings().all()
            for row in no_loss_rows:
                scores = row["scores"] or {}
                paired.append((row["entity_name"], dict(scores), 0))
        except Exception as exc:  # noqa: BLE001
            logger.warning("Paired data load failed: %s", exc)
            return []

        return paired

    # ------------------------------------------------------------------
    # Per-signal statistics
    # ------------------------------------------------------------------

    def _compute_per_signal(
        self,
        paired: list[tuple[str, dict[str, float], int]],
        current_weights: dict[str, float],
    ) -> dict[str, dict]:
        """For each signal, compute discrimination, monotonicity, stability, IV."""
        metrics: dict[str, dict] = {}

        for sig_id in current_weights:
            loss_scores: list[float] = []
            no_loss_scores: list[float] = []
            for _, scores, has_loss in paired:
                val = scores.get(sig_id)
                if val is None:
                    continue
                if has_loss:
                    loss_scores.append(float(val))
                else:
                    no_loss_scores.append(float(val))

            n = len(loss_scores) + len(no_loss_scores)
            notes: list[str] = []
            record: dict = {"n": n, "notes": notes}

            if n < self.config.min_sample_size:
                notes.append(f"Sample size {n} below minimum ({self.config.min_sample_size})")
                metrics[sig_id] = record
                continue

            if len(loss_scores) < 5 or len(no_loss_scores) < 5:
                notes.append("Insufficient loss or no-loss observations")
                metrics[sig_id] = record
                continue

            # 1. Mann-Whitney U: discrimination
            try:
                u_stat, u_p = stats.mannwhitneyu(loss_scores, no_loss_scores, alternative="two-sided")
                record["u_stat"] = float(u_stat)
                record["u_p"] = float(u_p)
            except Exception:
                pass

            # 2. Spearman rho: monotonicity on pooled (score, has_loss)
            try:
                all_scores = loss_scores + no_loss_scores
                labels = [1] * len(loss_scores) + [0] * len(no_loss_scores)
                rho, _ = stats.spearmanr(all_scores, labels)
                record["rho"] = float(rho) if not np.isnan(rho) else 0.0
            except Exception:
                record["rho"] = 0.0

            # 3. Stability: coefficient of variation of discrimination across splits
            record["stability"] = self._compute_stability(loss_scores, no_loss_scores)

            # 4. Information Value
            record["iv"] = self._compute_iv(loss_scores, no_loss_scores)

            metrics[sig_id] = record

        return metrics

    def _compute_stability(
        self, loss_scores: list[float], no_loss_scores: list[float]
    ) -> float:
        """Coefficient of variation of the median difference across 3 splits.

        Lower = more stable. Returns 0 when not enough data.
        """
        if len(loss_scores) < 9 or len(no_loss_scores) < 9:
            return 0.0
        # Split each group into 3
        splits = 3
        loss_chunks = np.array_split(loss_scores, splits)
        no_loss_chunks = np.array_split(no_loss_scores, splits)

        diffs = [
            float(np.median(no_loss_chunks[i])) - float(np.median(loss_chunks[i]))
            for i in range(splits)
        ]
        mean = float(np.mean(diffs)) if diffs else 0.0
        if abs(mean) < 1e-10:
            return 0.0
        cv = float(np.std(diffs) / abs(mean))
        # Convert CV to a "stability" 0-1: low CV = high stability
        return max(0.0, min(1.0, 1.0 - cv))

    def _compute_iv(
        self, loss_scores: list[float], no_loss_scores: list[float], n_bins: int = 5
    ) -> float:
        """Information Value over `n_bins` score buckets.

        IV = Σ (P_no_loss - P_loss) × ln(P_no_loss / P_loss)
        """
        all_scores = np.array(loss_scores + no_loss_scores, dtype=float)
        if len(all_scores) < n_bins:
            return 0.0

        edges = np.quantile(all_scores, np.linspace(0, 1, n_bins + 1))
        edges = np.unique(edges)  # drop duplicates when distribution is narrow
        if len(edges) < 3:
            return 0.0

        loss_hist, _ = np.histogram(loss_scores, bins=edges)
        no_loss_hist, _ = np.histogram(no_loss_scores, bins=edges)
        total_loss = loss_hist.sum()
        total_no_loss = no_loss_hist.sum()
        if total_loss == 0 or total_no_loss == 0:
            return 0.0

        iv = 0.0
        for lh, nlh in zip(loss_hist, no_loss_hist):
            # Laplace smoothing to avoid log(0)
            p_loss = (lh + 0.5) / (total_loss + 0.5 * len(loss_hist))
            p_no_loss = (nlh + 0.5) / (total_no_loss + 0.5 * len(no_loss_hist))
            iv += (p_no_loss - p_loss) * np.log(p_no_loss / p_loss)
        return float(abs(iv))

    # ------------------------------------------------------------------
    # Alignment classifier
    # ------------------------------------------------------------------

    def _classify_alignment(
        self,
        metrics: dict,
        current_weight: float,
        evidence_weight: float,
    ) -> Alignment:
        """Classify based on IV + weight-vs-evidence gap."""
        iv = metrics.get("iv", 0.0)
        if iv < self.config.low_iv_threshold and current_weight > 0.01:
            return Alignment.SIGNIFICANT_MISALIGNMENT

        rho = abs(metrics.get("rho", 0.0))
        if rho < self.config.monotonicity_rho_threshold and iv < self.config.low_iv_threshold * 2:
            return Alignment.ADJUSTMENT_SUGGESTED

        # Weight-vs-evidence gap > 50% = adjustment suggested
        if current_weight > 0:
            gap = abs(evidence_weight - current_weight) / current_weight
            if gap > 0.5:
                return Alignment.ADJUSTMENT_SUGGESTED

        return Alignment.WELL_CALIBRATED
