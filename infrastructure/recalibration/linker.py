"""
C-1c: Signal-Loss Linker

Links LossEvent rows back to the ModelVersionRecord that was active at
bind time, and snapshots the full signal score profile into SignalLossPair.

Two resolution strategies are supported:
1. quote_id is set: follow LossEvent.quote_id -> Quote.model_version_id
   This is the precise path when the loss is tied to an internal quote.
2. quote_id is null: search for the most recent BOUND Quote for the
   entity+coverage whose bind date precedes loss_date. Used for imported
   historical data where the external policy id does not map to a quote.

Either strategy may return None (no matching assessment). In that case
the loss event remains UNLINKED; it can be linked later once the data is
available.

Signal snapshot: for the resolved assessment, we pull every
ModelVersionSignal row and flatten {signal_code -> score} into the
signal_scores_at_bind JSONB field.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from infrastructure.db.models import (
    LossEvent,
    ModelVersionRecord,
    ModelVersionSignal,
    Quote,
    QuoteStatus,
    Signal,
    SignalLossPair,
    Submission,
)

logger = logging.getLogger("dsi.recalibration.linker")


@dataclass
class LinkResult:
    """Outcome of linking a loss event."""

    linked: bool
    loss_event_id: str
    assessment_id: Optional[str] = None
    pair_id: Optional[str] = None
    reason: Optional[str] = None  # human-readable if not linked
    signals_captured: int = 0


@dataclass
class RetrospectiveReport:
    """Summary of a retrospective batch link run."""

    total_candidates: int = 0
    newly_linked: int = 0
    already_linked: int = 0
    unlinked_no_quote: int = 0
    unlinked_no_assessment: int = 0
    errors: list[str] = field(default_factory=list)


class SignalLossLinker:
    """Links loss events to their bind-time signal profile."""

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Single-loss linking
    # ------------------------------------------------------------------

    def link(self, loss_event_id: str) -> LinkResult:
        """Link one loss event. Returns a LinkResult describing the outcome.

        Does not commit -- the caller owns the transaction.
        """
        loss = self.db.execute(
            select(LossEvent).where(LossEvent.id == loss_event_id)
        ).scalar_one_or_none()
        if loss is None:
            return LinkResult(linked=False, loss_event_id=loss_event_id, reason="loss_event not found")

        # Short-circuit: already linked
        if loss.linked_assessment_id is not None:
            existing = self.db.execute(
                select(SignalLossPair).where(
                    SignalLossPair.loss_event_id == loss.id,
                    SignalLossPair.assessment_id == loss.linked_assessment_id,
                )
            ).scalar_one_or_none()
            if existing is not None:
                return LinkResult(
                    linked=True,
                    loss_event_id=str(loss.id),
                    assessment_id=str(loss.linked_assessment_id),
                    pair_id=str(existing.id),
                    reason="already linked",
                    signals_captured=len(existing.signal_scores_at_bind or {}),
                )

        # Resolve the assessment
        assessment, bind_date = self._resolve_assessment(loss)
        if assessment is None:
            reason = "no quote linked and no matching BOUND assessment found"
            return LinkResult(linked=False, loss_event_id=str(loss.id), reason=reason)

        # Build the signal snapshot
        snapshot = self._snapshot_signals(assessment.id)

        # Compute time-to-loss
        time_to_loss_days = None
        if bind_date is not None:
            # Normalise tz -- loss_date is tz-aware, bind_date may be naive
            bd = bind_date if bind_date.tzinfo else bind_date.replace(tzinfo=timezone.utc)
            ld = loss.loss_date if loss.loss_date.tzinfo else loss.loss_date.replace(tzinfo=timezone.utc)
            time_to_loss_days = max(0, (ld - bd).days)

        # Create / upsert the signal-loss pair
        pair = self.db.execute(
            select(SignalLossPair).where(
                SignalLossPair.assessment_id == assessment.id,
                SignalLossPair.loss_event_id == loss.id,
            )
        ).scalar_one_or_none()

        if pair is None:
            pair = SignalLossPair(
                tenant_id=loss.tenant_id,
                assessment_id=assessment.id,
                loss_event_id=loss.id,
                signal_scores_at_bind=snapshot,
                composite_score_at_bind=assessment.final_composite_score or assessment.pure_composite_score,
                tier_at_bind=assessment.final_tier,
                loss_propensity_at_bind=assessment.loss_propensity_score,
                confidence_at_bind=assessment.confidence,
                bind_date=bind_date,
                time_to_loss_days=time_to_loss_days,
            )
            self.db.add(pair)
        else:
            pair.signal_scores_at_bind = snapshot
            pair.composite_score_at_bind = assessment.final_composite_score or assessment.pure_composite_score
            pair.tier_at_bind = assessment.final_tier
            pair.loss_propensity_at_bind = assessment.loss_propensity_score
            pair.confidence_at_bind = assessment.confidence
            pair.bind_date = bind_date
            pair.time_to_loss_days = time_to_loss_days

        # Tag the loss event with the resolved assessment
        loss.linked_assessment_id = assessment.id
        loss.linker_run_at = datetime.now(timezone.utc)

        self.db.flush()  # ensure pair.id is generated
        return LinkResult(
            linked=True,
            loss_event_id=str(loss.id),
            assessment_id=str(assessment.id),
            pair_id=str(pair.id),
            signals_captured=len(snapshot),
        )

    # ------------------------------------------------------------------
    # Batch retrospective linking
    # ------------------------------------------------------------------

    def link_all_unlinked(
        self, tenant_id: Optional[str] = None, limit: Optional[int] = None
    ) -> RetrospectiveReport:
        """Link every LossEvent that is not yet linked. Non-commit -- caller commits.

        Returns a RetrospectiveReport summarising outcomes. Used by the
        seed script and by admin-triggered batch relink operations.
        """
        report = RetrospectiveReport()

        stmt = select(LossEvent).where(LossEvent.linked_assessment_id.is_(None))
        if tenant_id:
            stmt = stmt.where(LossEvent.tenant_id == tenant_id)
        if limit:
            stmt = stmt.limit(limit)

        losses = self.db.execute(stmt).scalars().all()
        report.total_candidates = len(losses)

        for loss in losses:
            try:
                result = self.link(str(loss.id))
                if result.linked:
                    report.newly_linked += 1
                elif result.reason and "already linked" in result.reason:
                    report.already_linked += 1
                elif loss.quote_id is None:
                    report.unlinked_no_quote += 1
                else:
                    report.unlinked_no_assessment += 1
            except Exception as exc:  # noqa: BLE001
                report.errors.append(f"{loss.id}: {exc}")
                logger.warning("Link failed for %s: %s", loss.id, exc)

        return report

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _resolve_assessment(
        self, loss: LossEvent
    ) -> tuple[Optional[ModelVersionRecord], Optional[datetime]]:
        """Find the ModelVersionRecord active at loss bind time.

        Returns (assessment, bind_date) or (None, None).
        """
        # Strategy 1: direct quote linkage
        if loss.quote_id is not None:
            quote = self.db.execute(
                select(Quote).where(Quote.id == loss.quote_id)
            ).scalar_one_or_none()
            if quote and quote.model_version_id:
                assessment = self.db.execute(
                    select(ModelVersionRecord).where(ModelVersionRecord.id == quote.model_version_id)
                ).scalar_one_or_none()
                if assessment:
                    return assessment, quote.created_at

        # Strategy 2: find the most recent BOUND quote for this entity+coverage
        #             whose creation precedes the loss_date.
        stmt = (
            select(Quote)
            .join(Submission, Quote.submission_id == Submission.id)
            .where(
                Submission.entity_name == loss.entity_name,
                Submission.coverage == loss.coverage,
                Quote.status == QuoteStatus.BOUND,
                Quote.created_at <= loss.loss_date,
            )
            .order_by(Quote.created_at.desc())
            .limit(1)
        )
        quote = self.db.execute(stmt).scalar_one_or_none()
        if quote and quote.model_version_id:
            assessment = self.db.execute(
                select(ModelVersionRecord).where(ModelVersionRecord.id == quote.model_version_id)
            ).scalar_one_or_none()
            if assessment:
                return assessment, quote.created_at

        return None, None

    def _snapshot_signals(self, model_version_id) -> dict[str, float]:
        """Flatten all ModelVersionSignal rows for an assessment into
        {signal_code -> score}. Returns a JSON-safe dict."""
        # Join ModelVersionSignal -> Signal to get the stable signal code
        stmt = (
            select(Signal.code, ModelVersionSignal.score)
            .select_from(ModelVersionSignal)
            .join(Signal, ModelVersionSignal.signal_id == Signal.id)
            .where(ModelVersionSignal.model_version_id == model_version_id)
        )
        result = self.db.execute(stmt).all()
        return {code: (float(score) if score is not None else None) for code, score in result}
