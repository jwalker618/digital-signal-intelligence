"""
WE-3e: Drift Detection

Detects structural changes in the signal landscape that neither the
scanner nor lifecycle manager catch individually. Four detection modes:

1. Relationship shift   -- an ACTIVE relationship's rho changed > threshold
                           since the previous scan.
2. Correlation inversion -- sign flip in a previously stable correlation
                           (already surfaced per-relationship by stability,
                           but this mode is population-wide monitoring).
3. Signal regime change -- a signal's population distribution shifted
                           materially vs. the historical distribution
                           (KS test p < threshold).
4. Emergence burst      -- unusually high number of new candidates in the
                           current scan (> 2 std devs above historical mean).

Each detection produces a DriftAlert persisted via the registry.
"""

from __future__ import annotations

import logging
import statistics
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

import numpy as np
from scipy import stats
from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.registry import IntelligenceRegistry
from world_engine.types import (
    CandidateRelationship,
    DriftAlert,
    DriftSeverity,
    LifecycleState,
)

logger = logging.getLogger("dsi.world_engine.drift")


@dataclass
class DriftConfig:
    relationship_shift_threshold: float = 0.15
    """|rho_new - rho_prev| above this triggers a relationship_shift alert."""

    regime_ks_p_threshold: float = 0.01
    """KS test p-value below this triggers a signal_regime_change alert."""

    emergence_burst_std_devs: float = 2.0
    """New-candidate count > this many std devs above historical mean."""

    min_historical_scans_for_burst: int = 3
    """Need at least this many prior scans to compute a meaningful std dev."""

    min_historical_observations_for_regime: int = 50
    """Need this many prior observations of a signal to run KS test."""


class DriftDetector:
    """Raises DriftAlert rows when structural changes are detected.

    V6/E6 (stage 1.2): alert observers. After alerts are persisted the
    detector fans out to registered observers (e.g. the
    DriftReferralBridge that routes alerts into the referrals queue).
    Observers are invoked synchronously but isolated — one observer's
    failure does not block the rest.
    """

    def __init__(self, config: Optional[DriftConfig] = None):
        self.config = config or DriftConfig()
        # V6/E6 — observers registered via `on_alert`. Callable takes
        # a single DriftAlert.
        self._observers: list = []

    def on_alert(self, observer) -> None:
        """Register an observer called for each alert after persist."""
        self._observers.append(observer)

    def _fan_out(self, alerts: list) -> None:
        if not self._observers:
            return
        for alert in alerts:
            for obs in self._observers:
                try:
                    obs(alert)
                except Exception as e:  # pragma: no cover — isolated
                    logger.warning(
                        "DriftDetector observer failed (non-blocking): %s", e,
                    )

    def detect(
        self,
        registry: IntelligenceRegistry,
        new_candidates: list[CandidateRelationship],
    ) -> list[DriftAlert]:
        """Run all four detection modes. Persists alerts via registry
        and dispatches to registered observers (V6/E6)."""
        db = registry.db
        alerts: list[DriftAlert] = []

        alerts.extend(self._detect_relationship_shifts(registry))
        alerts.extend(self._detect_signal_regime_changes(db))
        alerts.extend(self._detect_emergence_burst(db, len(new_candidates)))
        # correlation_inversion is handled by StabilityValidator already;
        # we re-surface it at population level by looking for sign_flip_detected
        # evidence in recent lifecycle transitions.
        alerts.extend(self._detect_correlation_inversions(db))

        for alert in alerts:
            registry.store_drift_alert(alert)

        self._fan_out(alerts)

        logger.info("DriftDetector: raised %d alerts", len(alerts))
        return alerts

    # ==================================================================
    # Mode 1: relationship shift
    # ==================================================================

    def _detect_relationship_shifts(
        self, registry: IntelligenceRegistry
    ) -> list[DriftAlert]:
        """For each ACTIVE relationship, compare current rho to the rho
        recorded at its most recent state transition. Large shifts =
        structural change."""
        from scipy import stats as _stats

        actives, _ = registry.list_relationships(
            state=LifecycleState.ACTIVE, limit=10_000
        )
        alerts: list[DriftAlert] = []

        for rel in actives:
            current_rho = self._current_rho(
                registry.db, rel.source_signal, rel.target_signal
            )
            if current_rho is None:
                continue

            shift = abs(current_rho - rel.correlation_rho)
            if shift < self.config.relationship_shift_threshold:
                continue

            severity = (
                DriftSeverity.CRITICAL
                if shift > 0.3
                else DriftSeverity.WARNING
                if shift > 0.2
                else DriftSeverity.INFO
            )

            alerts.append(DriftAlert(
                id=str(uuid.uuid4()),
                alert_type="relationship_shift",
                severity=severity,
                source_signal=rel.source_signal,
                target_signal=rel.target_signal,
                relationship_id=rel.id,
                description=(
                    f"Active relationship rho shifted {shift:.2f} "
                    f"(was {rel.correlation_rho:.2f}, now {current_rho:.2f})"
                ),
                evidence={
                    "prior_rho": rel.correlation_rho,
                    "current_rho": current_rho,
                    "shift": shift,
                },
                detected_at=datetime.now(timezone.utc),
            ))

        return alerts

    def _current_rho(
        self, db: Session, source: str, target: str
    ) -> Optional[float]:
        """Compute Spearman rho for this pair over the latest assessment per entity."""
        sql = """
            WITH latest AS (
                SELECT DISTINCT ON (s.entity_name) s.entity_name, m.id AS mv_id
                FROM submissions s
                JOIN model_versions m ON m.submission_id = s.id
                ORDER BY s.entity_name, m.created_at DESC
            )
            SELECT l.entity_name, sig.code AS signal_code, mvs.score
            FROM latest l
            JOIN model_version_signals mvs ON mvs.model_version_id = l.mv_id
            JOIN signals sig ON sig.id = mvs.signal_id
            WHERE sig.code IN (:source, :target) AND mvs.score IS NOT NULL
        """
        rows = db.execute(
            text(sql), {"source": source, "target": target}
        ).mappings().all()

        per_entity: dict = {}
        for row in rows:
            per_entity.setdefault(row["entity_name"], {})[row["signal_code"]] = float(
                row["score"]
            )
        xs, ys = [], []
        for signals in per_entity.values():
            if source in signals and target in signals:
                xs.append(signals[source])
                ys.append(signals[target])
        if len(xs) < 15:
            return None
        rho, _ = stats.spearmanr(xs, ys)
        return None if np.isnan(rho) else float(rho)

    # ==================================================================
    # Mode 2: correlation inversions (surface stability sign-flips)
    # ==================================================================

    def _detect_correlation_inversions(self, db: Session) -> list[DriftAlert]:
        """Look for recent state transitions whose evidence includes a
        stability sign flip. These are already recorded per-relationship;
        this mode elevates them to population-level drift alerts."""
        sql = """
            SELECT relationship_id, transitioned_at, evidence
            FROM we_state_transitions
            WHERE transitioned_at >= :since
              AND (evidence->>'stability_sign_flip')::boolean = true
        """
        since = datetime.now(timezone.utc) - timedelta(days=30)
        rows = db.execute(text(sql), {"since": since}).mappings().all()
        alerts: list[DriftAlert] = []
        for row in rows:
            alerts.append(DriftAlert(
                id=str(uuid.uuid4()),
                alert_type="correlation_inversion",
                severity=DriftSeverity.WARNING,
                relationship_id=str(row["relationship_id"]),
                description="Relationship's correlation sign inverted across time windows",
                evidence=row["evidence"] or {},
                detected_at=datetime.now(timezone.utc),
            ))
        return alerts

    # ==================================================================
    # Mode 3: signal regime change
    # ==================================================================

    def _detect_signal_regime_changes(self, db: Session) -> list[DriftAlert]:
        """For each signal, split assessments into "recent" and "historical"
        and compare distributions via KS test. Small p-value = distribution
        shifted."""
        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=90)

        sql = """
            SELECT
                sig.code AS signal_code,
                m.created_at,
                mvs.score
            FROM model_version_signals mvs
            JOIN model_versions m ON m.id = mvs.model_version_id
            JOIN signals sig      ON sig.id = mvs.signal_id
            WHERE mvs.score IS NOT NULL
        """
        rows = db.execute(text(sql)).mappings().all()

        by_signal: dict[str, dict[str, list[float]]] = {}
        for row in rows:
            ts = row["created_at"]
            bucket = "recent" if ts >= recent_cutoff else "historical"
            by_signal.setdefault(row["signal_code"], {"recent": [], "historical": []})[
                bucket
            ].append(float(row["score"]))

        alerts: list[DriftAlert] = []
        for code, buckets in by_signal.items():
            recent = buckets["recent"]
            historical = buckets["historical"]
            if (
                len(recent) < 15
                or len(historical) < self.config.min_historical_observations_for_regime
            ):
                continue

            ks_stat, p = stats.ks_2samp(recent, historical)
            if p >= self.config.regime_ks_p_threshold:
                continue

            # Distribution has shifted. Use median shift as a magnitude hint.
            median_shift = float(np.median(recent) - np.median(historical))
            severity = (
                DriftSeverity.CRITICAL
                if abs(median_shift) > 15
                else DriftSeverity.WARNING
                if abs(median_shift) > 5
                else DriftSeverity.INFO
            )

            alerts.append(DriftAlert(
                id=str(uuid.uuid4()),
                alert_type="signal_regime_change",
                severity=severity,
                source_signal=code,
                description=(
                    f"Signal {code} distribution shifted "
                    f"(median +{median_shift:.1f}, KS p={p:.4f})"
                ),
                evidence={
                    "ks_statistic": float(ks_stat),
                    "ks_p_value": float(p),
                    "recent_n": len(recent),
                    "historical_n": len(historical),
                    "median_shift": median_shift,
                },
                detected_at=datetime.now(timezone.utc),
            ))

        return alerts

    # ==================================================================
    # Mode 4: emergence burst
    # ==================================================================

    def _detect_emergence_burst(
        self, db: Session, new_candidate_count: int
    ) -> list[DriftAlert]:
        """If the current scan discovered far more new candidates than the
        historical mean, something structural has changed."""
        historical_sql = """
            SELECT candidates_found FROM we_scan_runs
            WHERE completed_at IS NOT NULL
            ORDER BY started_at DESC
            LIMIT 20
        """
        historical_counts = [
            int(r) for r in db.execute(text(historical_sql)).scalars().all()
        ]
        if len(historical_counts) < self.config.min_historical_scans_for_burst:
            return []

        mean = statistics.mean(historical_counts)
        stdev = statistics.stdev(historical_counts) if len(historical_counts) > 1 else 0.0
        threshold = mean + self.config.emergence_burst_std_devs * stdev

        if stdev < 0.5 or new_candidate_count <= threshold:
            return []

        return [DriftAlert(
            id=str(uuid.uuid4()),
            alert_type="emergence_burst",
            severity=DriftSeverity.WARNING,
            description=(
                f"Emergence burst: {new_candidate_count} new candidates this scan "
                f"(historical mean {mean:.1f} ± {stdev:.1f})"
            ),
            evidence={
                "current_count": new_candidate_count,
                "historical_mean": mean,
                "historical_stdev": stdev,
                "threshold": threshold,
            },
            detected_at=datetime.now(timezone.utc),
        )]
