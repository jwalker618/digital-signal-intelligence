"""
WE-3g: World Engine Scheduler

Orchestrates the full discovery-validation-lifecycle pipeline:

    maturity check -> scan -> infer -> confound -> holdout -> register
                                                                  |
                                                                  v
                                          lifecycle -> drift -> population

Runs as a batch process, completely separate from the real-time
assessment pipeline. Never blocks or impacts pricing performance.

Trigger conditions (should_run):
- Engine maturity >= LEARN (discovery requires minimum population)
- AND (new_assessments_since_last_run > threshold  OR  time_since_last > max_interval)
- AND minimum_population met (50 entities with temporal data)

Every scan writes a ScanRunReport to we_scan_runs with full statistics
and any errors encountered. Failures in one stage do not abort the
pipeline -- errors are captured and the scan continues.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from world_engine.drift import DriftDetector
from world_engine.inferencer import CausalInferencer, ConfoundController
from world_engine.lifecycle import LifecycleManager
from world_engine.maturity import MaturityEvaluator
from world_engine.population import PopulationIntelligence
from world_engine.registry import IntelligenceRegistry
from world_engine.scanner import CorrelationScanner
from world_engine.types import (
    DiscoveredRelationship,
    LifecycleState,
    MaturityStage,
    ScanRunReport,
    StateTransition,
)
from world_engine.validator import HoldoutValidator

logger = logging.getLogger("dsi.world_engine.scheduler")


@dataclass
class SchedulerConfig:
    min_new_assessments: int = 100
    max_days_between_runs: int = 7
    min_entities_for_discovery: int = 50


class WorldEngineScheduler:
    """Orchestrates the discovery-validation-lifecycle pipeline."""

    def __init__(
        self,
        db: Session,
        config: Optional[SchedulerConfig] = None,
        scanner: Optional[CorrelationScanner] = None,
        inferencer: Optional[CausalInferencer] = None,
        confound_controller: Optional[ConfoundController] = None,
        holdout_validator: Optional[HoldoutValidator] = None,
        lifecycle_manager: Optional[LifecycleManager] = None,
        drift_detector: Optional[DriftDetector] = None,
        population_intel: Optional[PopulationIntelligence] = None,
    ):
        self.db = db
        self.config = config or SchedulerConfig()
        self.registry = IntelligenceRegistry(db)

        self.scanner = scanner or CorrelationScanner()
        self.inferencer = inferencer or CausalInferencer()
        self.confound_controller = confound_controller or ConfoundController()
        self.holdout_validator = holdout_validator or HoldoutValidator()
        self.lifecycle = lifecycle_manager or LifecycleManager(self.registry)
        self.drift_detector = drift_detector or DriftDetector()
        self.population_intel = population_intel or PopulationIntelligence(self.registry)

    # ==================================================================
    # should_run
    # ==================================================================

    def should_run(self) -> tuple[bool, str]:
        """Return (should_run, reason). Reason is useful for operational logs."""
        maturity = self.registry.get_maturity_state()
        if maturity.stage == MaturityStage.SEED:
            return False, "Maturity SEED -- discovery gated until LEARN"

        if maturity.entities_with_temporal_data < self.config.min_entities_for_discovery:
            return False, (
                f"Insufficient temporal data: {maturity.entities_with_temporal_data} "
                f"< {self.config.min_entities_for_discovery} entities"
            )

        last_run = self._last_scan_completed_at()
        if last_run is None:
            return True, "No prior scan -- first run"

        days_since = (datetime.now(timezone.utc) - last_run).days
        if days_since >= self.config.max_days_between_runs:
            return True, f"Last scan was {days_since}d ago (max {self.config.max_days_between_runs})"

        new_assessments = self._new_assessments_since(last_run)
        if new_assessments >= self.config.min_new_assessments:
            return True, f"{new_assessments} new assessments since last scan"

        return False, (
            f"Only {new_assessments} new assessments ({days_since}d since last scan)"
        )

    # ==================================================================
    # run_cycle
    # ==================================================================

    def run_cycle(self) -> ScanRunReport:
        """Execute a full discovery + validation + lifecycle + drift cycle."""
        maturity = self.registry.get_maturity_state()
        run_id = f"scan_{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc)
        errors: list[str] = []

        report = ScanRunReport(
            run_id=run_id,
            started_at=started_at,
            completed_at=started_at,  # updated at end
            maturity_stage=maturity.stage,
        )

        # Stage 1: Scan
        try:
            candidates = self.scanner.scan(self.db)
            report.candidates_found = len(candidates)
            report.entities_scanned = maturity.assessed_entity_count
            report.pairs_tested = self._infer_pairs_tested(candidates)
            logger.info("[%s] scan: %d candidates", run_id, len(candidates))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"scan: {exc}")
            candidates = []
            logger.exception("[%s] scan failed", run_id)

        # Stage 2: Inference
        try:
            directed = self.inferencer.infer(candidates, self.db)
            report.candidates_after_inference = len(directed)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"inferencer: {exc}")
            directed = []

        # Stage 3: Confound control
        try:
            confound_filtered = self.confound_controller.filter(directed, self.db)
            report.candidates_after_confound = len(confound_filtered)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"confound_control: {exc}")
            confound_filtered = directed

        # Stage 4: Holdout validation (pre-register gate)
        validated: list = []
        for cand in confound_filtered:
            try:
                result = self.holdout_validator.validate(cand, self.db)
                if result.passed:
                    validated.append((cand, result))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"holdout:{cand.source_signal}->{cand.target_signal}: {exc}")
        report.candidates_after_holdout = len(validated)

        # Stage 5: Register surviving candidates
        for cand, holdout_result in validated:
            try:
                rel = self._build_relationship(cand, holdout_result)
                # Skip if relationship already exists for this pair+direction
                if not self._relationship_already_registered(
                    cand.source_signal, cand.target_signal
                ):
                    self.registry.register_candidate(rel)
                    report.new_registrations += 1
            except Exception as exc:  # noqa: BLE001
                errors.append(f"register:{cand.source_signal}->{cand.target_signal}: {exc}")

        # Commit registrations so subsequent stages can see them
        self.db.commit()

        # Stage 6: Lifecycle evaluation
        try:
            lifecycle_report = self.lifecycle.evaluate_all()
            report.state_transitions = lifecycle_report.transitions
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"lifecycle: {exc}")

        # Stage 7: Drift detection
        try:
            drift_alerts = self.drift_detector.detect(self.registry, candidates)
            report.drift_alerts_raised = len(drift_alerts)
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            errors.append(f"drift: {exc}")

        # Stage 8: Population intelligence (read-only rollup)
        try:
            pop_report = self.population_intel.compute_all()
            logger.info(
                "[%s] population: %d active with horizon %s",
                run_id,
                pop_report.predictive_horizon.get("with_lag_count", 0),
                pop_report.predictive_horizon.get("median_months"),
            )
        except Exception as exc:  # noqa: BLE001
            errors.append(f"population: {exc}")

        report.completed_at = datetime.now(timezone.utc)
        report.errors = errors

        # Persist the scan run record
        try:
            self.registry.store_scan_run(report)
            self.db.commit()
        except Exception as exc:  # noqa: BLE001
            logger.exception("[%s] failed to persist scan run: %s", run_id, exc)

        logger.info(
            "[%s] cycle complete in %.1fs: candidates=%d registered=%d transitions=%d drift=%d errors=%d",
            run_id,
            (report.completed_at - report.started_at).total_seconds(),
            report.candidates_found,
            report.new_registrations,
            len(report.state_transitions),
            report.drift_alerts_raised,
            len(errors),
        )
        return report

    # ==================================================================
    # Helpers
    # ==================================================================

    def _last_scan_completed_at(self) -> Optional[datetime]:
        try:
            row = self.db.execute(
                text(
                    "SELECT completed_at FROM we_scan_runs "
                    "WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1"
                )
            ).scalar_one_or_none()
            return row
        except Exception:
            return None

    def _new_assessments_since(self, since: datetime) -> int:
        try:
            return int(
                self.db.execute(
                    text("SELECT COUNT(*) FROM model_versions WHERE created_at > :since"),
                    {"since": since},
                ).scalar()
                or 0
            )
        except Exception:
            return 0

    def _infer_pairs_tested(self, candidates: list) -> int:
        """Approximate: we don't capture all tested pairs, only those that
        survived thresholds. A reasonable upper bound is 2 * candidates given
        that only a small fraction of pairs pass -- scheduler logs it as a
        best-effort figure, not ground truth."""
        return len(candidates) * 20  # rough scale factor for pairs tested

    def _relationship_already_registered(self, source: str, target: str) -> bool:
        """Check whether this source+target pair already has a non-deprecated
        relationship row."""
        row = self.db.execute(
            text(
                """
                SELECT id FROM we_relationships
                WHERE source_signal = :source
                  AND target_signal = :target
                  AND lifecycle_state != 'deprecated'
                LIMIT 1
                """
            ),
            {"source": source, "target": target},
        ).scalar_one_or_none()
        return row is not None

    def _build_relationship(self, directed, holdout_result) -> DiscoveredRelationship:
        now = datetime.now(timezone.utc)
        return DiscoveredRelationship(
            id=str(uuid.uuid4()),
            source_signal=directed.source_signal,
            target_signal=directed.target_signal,
            direction=directed.direction,
            lag_months=directed.lag_months,
            correlation_rho=directed.correlation_rho,
            granger_f_statistic=directed.granger_f_statistic,
            granger_p_value=directed.granger_p_value,
            effect_size=directed.effect_size,
            confounders_tested=directed.confounders_tested,
            holdout_rho=holdout_result.holdout_rho,
            holdout_p_value=holdout_result.holdout_p_value,
            predictive_hit_rate=None,
            population_size=directed.population_size,
            coverage_scope=directed.coverage_scope,
            lifecycle_state=LifecycleState.CANDIDATE,
            state_entered_at=now,
            state_history=[],
            influence_weight=0.0,
            created_at=now,
            updated_at=now,
        )
