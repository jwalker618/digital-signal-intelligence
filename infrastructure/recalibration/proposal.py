"""
C-2g: ProposalGenerator + Persistence

Bundles SignalAnalyser + WeightOptimiser + TierAnalyser + ImpactAssessor
outputs into a RecalibrationProposalPayload and persists it as a
RecalibrationProposal row in DRAFT status.

The generator is stateless beyond the DB session it's given; the Engine
(engine.py) drives the analysers and feeds their outputs here.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.recalibration.types import (
    ImpactAssessment,
    ProposalStatus,
    RecalibrationProposalPayload,
    SignalReportCard,
    TierThresholdChange,
    WeightChange,
)

logger = logging.getLogger("dsi.recalibration.proposal")


class ProposalGenerator:
    """Assembles and persists RecalibrationProposal rows."""

    def __init__(self, db: Session):
        self.db = db

    def build(
        self,
        *,
        tenant_id: str,
        coverage: str,
        config_name: str,
        proposed_by: str = "system",
        trigger: str = "system",
        signal_report_cards: list[SignalReportCard],
        weight_changes: list[WeightChange],
        tier_threshold_changes: list[TierThresholdChange],
        impact: ImpactAssessment,
        statistical_evidence: Optional[dict] = None,
    ) -> RecalibrationProposalPayload:
        """Build a payload without persisting."""
        now = datetime.now(timezone.utc)
        return RecalibrationProposalPayload(
            tenant_id=tenant_id,
            coverage=coverage,
            config_name=config_name,
            proposed_at=now,
            proposed_by=proposed_by,
            trigger=trigger,
            status=ProposalStatus.DRAFT,
            signal_report_cards=signal_report_cards,
            weight_changes=weight_changes,
            tier_threshold_changes=tier_threshold_changes,
            impact_assessment=impact,
            statistical_evidence=statistical_evidence or {},
            sample_size=impact.assessments_evaluated,
        )

    def persist(self, payload: RecalibrationProposalPayload) -> str:
        """Insert the proposal into recalibration_proposals. Returns the id."""
        proposal_id = str(uuid.uuid4())
        self.db.execute(
            text(
                """
                INSERT INTO recalibration_proposals (
                    id, tenant_id, coverage, config_name,
                    proposed_at, proposed_by, trigger, status,
                    signal_report_cards, weight_changes, tier_threshold_changes,
                    impact_assessment, statistical_evidence, sample_size
                ) VALUES (
                    :id, :tenant_id, :coverage, :config_name,
                    :proposed_at, :proposed_by, :trigger, :status,
                    CAST(:cards AS jsonb), CAST(:weights AS jsonb), CAST(:tiers AS jsonb),
                    CAST(:impact AS jsonb), CAST(:evidence AS jsonb), :sample_size
                )
                """
            ),
            {
                "id": proposal_id,
                "tenant_id": payload.tenant_id,
                "coverage": payload.coverage,
                "config_name": payload.config_name,
                "proposed_at": payload.proposed_at,
                "proposed_by": payload.proposed_by,
                "trigger": payload.trigger,
                "status": payload.status.value,
                "cards": json.dumps([c.model_dump(mode="json") for c in payload.signal_report_cards]),
                "weights": json.dumps([w.model_dump(mode="json") for w in payload.weight_changes]),
                "tiers": json.dumps([t.model_dump(mode="json") for t in payload.tier_threshold_changes]),
                "impact": json.dumps(payload.impact_assessment.model_dump(mode="json")),
                "evidence": json.dumps(payload.statistical_evidence, default=str),
                "sample_size": payload.sample_size,
            },
        )
        payload.id = proposal_id
        logger.info(
            "ProposalGenerator: persisted %s (coverage=%s config=%s changes=%d)",
            proposal_id, payload.coverage, payload.config_name, len(payload.weight_changes),
        )
        return proposal_id
