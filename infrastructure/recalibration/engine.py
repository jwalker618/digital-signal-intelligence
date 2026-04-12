"""
C-2g: RecalibrationEngine

Main orchestrator. Runs as a batch job (manual trigger or scheduled)
against a single coverage + config. Produces and persists a
RecalibrationProposal in DRAFT status, ready for governance review (C-3).

    SignalAnalyser -> WeightOptimiser -> TierAnalyser -> ImpactAssessor
                                     \-> ProposalGenerator.persist(...)

Triggers (should_run):
- New loss events since last run > threshold
- OR time since last run > max interval
- OR explicit manual trigger

Non-destructive: the engine never modifies configs. It only proposes.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.recalibration.impact import ImpactAssessor
from infrastructure.recalibration.proposal import ProposalGenerator
from infrastructure.recalibration.signal_analysis import SignalAnalyser
from infrastructure.recalibration.tier_analysis import TierAnalyser
from infrastructure.recalibration.types import RecalibrationProposalPayload
from infrastructure.recalibration.weight_optimiser import WeightOptimiser

logger = logging.getLogger("dsi.recalibration.engine")


@dataclass
class RecalibrationEngineConfig:
    min_new_losses_for_trigger: int = 50
    max_days_between_runs: int = 90
    min_sample_size: int = 30
    """Minimum combined loss + no-loss assessments required to run at all."""


class RecalibrationEngine:
    """End-to-end orchestrator for experience-based recalibration."""

    def __init__(
        self,
        db: Session,
        config: Optional[RecalibrationEngineConfig] = None,
    ):
        self.db = db
        self.config = config or RecalibrationEngineConfig()
        self.signal_analyser = SignalAnalyser(db)
        self.weight_optimiser = WeightOptimiser()
        self.tier_analyser = TierAnalyser(db)
        self.impact_assessor = ImpactAssessor(db)
        self.proposal_generator = ProposalGenerator(db)

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def should_run(self, coverage: str, config_name: str) -> tuple[bool, str]:
        """Return (should_run, reason)."""
        last_run = self._last_proposal_at(coverage, config_name)
        if last_run is None:
            return True, "No prior proposal -- first run"

        days_since = (datetime.now(timezone.utc) - last_run).days
        if days_since >= self.config.max_days_between_runs:
            return True, f"Last proposal {days_since}d ago"

        new_losses = self._loss_events_since(last_run, coverage, config_name)
        if new_losses >= self.config.min_new_losses_for_trigger:
            return True, f"{new_losses} new losses since last proposal"

        return False, f"{new_losses} new losses, {days_since}d since last run"

    def run(
        self,
        *,
        tenant_id: str,
        coverage: str,
        config_name: str,
        current_weights: dict[str, float],
        current_tier_boundaries: list[tuple[int, float, float]],
        proposed_by: str = "system",
        trigger: str = "system",
        persist: bool = True,
    ) -> Optional[RecalibrationProposalPayload]:
        """Execute a full recalibration cycle.

        Returns the proposal payload (with `id` populated if persisted) or
        None if preconditions are not met.
        """
        logger.info(
            "RecalibrationEngine: starting cycle coverage=%s config=%s",
            coverage, config_name,
        )

        # Sanity: minimum sample size
        sample_size = self._total_eligible_assessments(coverage, config_name)
        if sample_size < self.config.min_sample_size:
            logger.info(
                "Skipping run: sample size %d below minimum %d",
                sample_size, self.config.min_sample_size,
            )
            return None

        # 1. Signal analysis
        cards = self.signal_analyser.analyse(
            coverage=coverage,
            config_name=config_name,
            current_weights=current_weights,
        )

        # 2. Weight optimisation
        weight_changes = self.weight_optimiser.optimise(cards)

        # 3. Tier analysis
        tier_changes = self.tier_analyser.analyse(
            coverage=coverage,
            config_name=config_name,
            current_tier_boundaries=current_tier_boundaries,
        )

        # 4. Impact assessment
        impact = self.impact_assessor.assess(
            coverage=coverage,
            config_name=config_name,
            current_weights=current_weights,
            weight_changes=weight_changes,
            tier_threshold_changes=tier_changes,
            tier_boundaries=current_tier_boundaries,
        )

        # 5. Proposal
        evidence = {
            "engine_config": {
                "min_new_losses_for_trigger": self.config.min_new_losses_for_trigger,
                "max_days_between_runs": self.config.max_days_between_runs,
            },
            "run_at": datetime.now(timezone.utc).isoformat(),
            "signal_count": len(cards),
            "weight_change_count": len(weight_changes),
            "tier_change_count": len(tier_changes),
        }

        payload = self.proposal_generator.build(
            tenant_id=tenant_id,
            coverage=coverage,
            config_name=config_name,
            proposed_by=proposed_by,
            trigger=trigger,
            signal_report_cards=cards,
            weight_changes=weight_changes,
            tier_threshold_changes=tier_changes,
            impact=impact,
            statistical_evidence=evidence,
        )

        if persist:
            proposal_id = self.proposal_generator.persist(payload)
            logger.info(
                "RecalibrationEngine: proposal %s persisted (%d weight changes, %d tier changes)",
                proposal_id, len(weight_changes), len(tier_changes),
            )

        return payload

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _last_proposal_at(
        self, coverage: str, config_name: str
    ) -> Optional[datetime]:
        try:
            row = self.db.execute(
                text(
                    """
                    SELECT proposed_at FROM recalibration_proposals
                    WHERE coverage = :coverage AND config_name = :config_name
                    ORDER BY proposed_at DESC LIMIT 1
                    """
                ),
                {"coverage": coverage, "config_name": config_name},
            ).scalar_one_or_none()
            return row
        except Exception:
            return None

    def _loss_events_since(
        self, since: datetime, coverage: str, config_name: str
    ) -> int:
        try:
            return int(
                self.db.execute(
                    text(
                        """
                        SELECT COUNT(*) FROM loss_events
                        WHERE created_at > :since
                          AND coverage = :coverage
                          AND (config_name = :config_name OR config_name IS NULL)
                        """
                    ),
                    {"since": since, "coverage": coverage, "config_name": config_name},
                ).scalar() or 0
            )
        except Exception:
            return 0

    def _total_eligible_assessments(
        self, coverage: str, config_name: str
    ) -> int:
        try:
            return int(
                self.db.execute(
                    text(
                        """
                        SELECT COUNT(DISTINCT s.entity_name)
                        FROM submissions s
                        JOIN model_versions m ON m.submission_id = s.id
                        WHERE s.coverage = :coverage
                          AND (s.configuration = :config_name OR m.configuration_name = :config_name)
                        """
                    ),
                    {"coverage": coverage, "config_name": config_name},
                ).scalar() or 0
            )
        except Exception:
            return 0
