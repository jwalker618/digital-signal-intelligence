"""
DSI Database Repositories

Repository pattern implementation for database operations.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    Submission,
    Quote,
    Referral,
    ModelVersionRecord,
    ModelVersionSignal,
    Signal,
    SignalSource,
    SignalCache,
    SignalAuditRecord,
    AuditLog,
    SubmissionStatus,
    QuoteStatus,
    ReferralStatus,
    DecisionType,
)


def generate_id(prefix: str) -> str:
    """Generate a unique ID with prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class SubmissionRepository:
    """Repository for Submission operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        entity_name: str,
        coverage: str,
        domain_hint: Optional[str] = None,
        country_hint: Optional[str] = None,
        configuration: Optional[str] = None,
        submission_data: Optional[Dict[str, Any]] = None,
        direct_query_responses: Optional[Dict[str, bool]] = None,
        created_by: Optional[uuid.UUID] = None,
    ) -> Submission:
        """Create a new submission."""
        submission = Submission(
            submission_code=generate_id("sub"),
            entity_name=entity_name,
            domain_hint=domain_hint,
            country_hint=country_hint,
            coverage=coverage,
            configuration=configuration or f"{coverage}_general",
            submission_data=submission_data or {},
            direct_query_responses=direct_query_responses or {},
            created_by=created_by,
            status=SubmissionStatus.PENDING,
        )
        self.db.add(submission)
        await self.db.flush()
        return submission

    async def get_by_code(self, submission_code: str) -> Optional[Submission]:
        """Get submission by submission_code."""
        result = await self.db.execute(
            select(Submission).where(Submission.submission_code == submission_code)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, id: uuid.UUID) -> Optional[Submission]:
        """Get submission by UUID."""
        result = await self.db.execute(
            select(Submission).where(Submission.id == id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        coverage: Optional[str] = None,
        status: Optional[SubmissionStatus] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> List[Submission]:
        """List submissions with filters."""
        query = select(Submission)

        if coverage:
            query = query.where(Submission.coverage == coverage)
        if status:
            query = query.where(Submission.status == status)

        query = query.order_by(Submission.created_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_status(
        self,
        submission_code: str,
        status: SubmissionStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Submission]:
        """Update submission status."""
        await self.db.execute(
            update(Submission)
            .where(Submission.submission_code == submission_code)
            .values(
                status=status,
                error_message=error_message,
                processing_completed_at=datetime.utcnow() if status in [
                    SubmissionStatus.READY, SubmissionStatus.FAILED
                ] else None,
            )
        )
        return await self.get_by_code(submission_code)

    async def delete(self, submission_code: str) -> bool:
        """Delete a submission."""
        result = await self.db.execute(
            delete(Submission).where(Submission.submission_code == submission_code)
        )
        return result.rowcount > 0


class QuoteRepository:
    """Repository for Quote operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        submission_id: uuid.UUID,
        model_version_id: uuid.UUID,
        recommended_premium: float,
        recommended_limit: Optional[float] = None,
        valid_days: int = 30,
        status: Optional[QuoteStatus] = None,
    ) -> Quote:
        """Create a new quote.

        Scoring / tier / decision data lives on the linked ModelVersionRecord.
        """
        quote = Quote(
            quote_code=generate_id("quo"),
            submission_id=submission_id,
            model_version_id=model_version_id,
            status=status or QuoteStatus.READY,
            recommended_premium=recommended_premium,
            recommended_limit=recommended_limit,
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
        )
        self.db.add(quote)
        await self.db.flush()
        return quote

    async def get_by_code(self, quote_code: str) -> Optional[Quote]:
        """Get quote by quote_code."""
        result = await self.db.execute(
            select(Quote).where(Quote.quote_code == quote_code)
        )
        return result.scalar_one_or_none()

    async def get_by_submission(self, submission_id: uuid.UUID) -> List[Quote]:
        """Get all quotes for a submission."""
        result = await self.db.execute(
            select(Quote)
            .where(Quote.submission_id == submission_id)
            .order_by(Quote.created_at.desc())
        )
        return list(result.scalars().all())

    async def bind(
        self,
        quote_code: str,
        bound_by: uuid.UUID,
        policy_number: str,
    ) -> Optional[Quote]:
        """Bind a quote."""
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_code == quote_code)
            .values(
                status=QuoteStatus.BOUND,
                bound_at=datetime.utcnow(),
                bound_by=bound_by,
                policy_number=policy_number,
            )
        )
        return await self.get_by_code(quote_code)

    async def update_model_version_id(
        self,
        quote_code: str,
        model_version_id: uuid.UUID,
    ) -> Optional[Quote]:
        """Update the model version linked to a quote (Phase 8).

        Every signal override or manual tier/premium adjustment creates a new
        ModelVersionRecord.  The quote's FK must track the latest version so
        that GET /quotes/{code} returns current scoring data.
        """
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_code == quote_code)
            .values(model_version_id=model_version_id, updated_at=datetime.utcnow())
        )
        return await self.get_by_code(quote_code)

    async def update_status(
        self,
        quote_code: str,
        status: QuoteStatus,
    ) -> Optional[Quote]:
        """Update quote status (Phase 8).

        Used when a referral is approved (→ READY) or declined (→ DECLINED)
        so the quote record in the DB reflects the underwriter's decision.
        """
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_code == quote_code)
            .values(status=status, updated_at=datetime.utcnow())
        )
        return await self.get_by_code(quote_code)

    async def expire_old_quotes(self) -> int:
        """Mark expired quotes."""
        result = await self.db.execute(
            update(Quote)
            .where(
                and_(
                    Quote.status == QuoteStatus.READY,
                    Quote.valid_until < datetime.utcnow(),
                )
            )
            .values(status=QuoteStatus.EXPIRED)
        )
        return result.rowcount


class ReferralRepository:
    """Repository for Referral operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        quote_id: uuid.UUID,
        reasons: List[str],
        priority: int = 5,
    ) -> Referral:
        """Create a new referral."""
        referral = Referral(
            referral_code=generate_id("ref"),
            quote_id=quote_id,
            reasons=reasons,
            priority=priority,
            status=ReferralStatus.PENDING,
        )
        self.db.add(referral)
        await self.db.flush()
        return referral

    async def get_by_code(self, referral_code: str) -> Optional[Referral]:
        """Get referral by referral_code."""
        result = await self.db.execute(
            select(Referral).where(Referral.referral_code == referral_code)
        )
        return result.scalar_one_or_none()

    async def list_pending(
        self,
        assigned_to: Optional[uuid.UUID] = None,
        limit: int = 20,
    ) -> List[Referral]:
        """List pending referrals."""
        query = select(Referral).where(
            Referral.status.in_([ReferralStatus.PENDING, ReferralStatus.IN_REVIEW])
        )

        if assigned_to:
            query = query.where(Referral.assigned_to == assigned_to)

        query = query.order_by(Referral.priority, Referral.created_at)
        query = query.limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def assign(
        self,
        referral_code: str,
        assigned_to: uuid.UUID,
    ) -> Optional[Referral]:
        """Assign a referral to an underwriter."""
        await self.db.execute(
            update(Referral)
            .where(Referral.referral_code == referral_code)
            .values(
                assigned_to=assigned_to,
                assigned_at=datetime.utcnow(),
                status=ReferralStatus.IN_REVIEW,
            )
        )
        return await self.get_by_code(referral_code)

    async def review(
        self,
        referral_code: str,
        reviewed_by: uuid.UUID,
        decision: str,
        notes: Optional[str] = None,
        tier_override: Optional[int] = None,
        premium_adjustment: Optional[float] = None,
    ) -> Optional[Referral]:
        """Complete referral review."""
        status_map = {
            "approve": ReferralStatus.APPROVED,
            "decline": ReferralStatus.DECLINED,
            "modify": ReferralStatus.MODIFIED,
        }

        await self.db.execute(
            update(Referral)
            .where(Referral.referral_code == referral_code)
            .values(
                status=status_map.get(decision, ReferralStatus.APPROVED),
                reviewed_by=reviewed_by,
                reviewed_at=datetime.utcnow(),
                review_decision=decision,
                review_notes=notes,
                tier_override=tier_override,
                premium_adjustment=premium_adjustment,
            )
        )
        return await self.get_by_code(referral_code)


class SignalCacheRepository:
    """Repository for SignalCache operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_signal_id(self, signal_code: str) -> int:
        """Get or create a Signal reference row, returning its integer id."""
        result = await self.db.execute(
            select(Signal.id).where(Signal.code == signal_code)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        sig = Signal(code=signal_code)
        self.db.add(sig)
        await self.db.flush()
        return sig.id

    async def _resolve_source_id(self, source_name: str) -> int:
        """Get or create a SignalSource reference row, returning its integer id."""
        result = await self.db.execute(
            select(SignalSource.id).where(SignalSource.name == source_name)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        src = SignalSource(name=source_name)
        self.db.add(src)
        await self.db.flush()
        return src.id

    async def get(
        self,
        entity_code: str,
        signal_code: str,
        source_name: str,
    ) -> Optional[SignalCache]:
        """Get cached signal data if valid."""
        result = await self.db.execute(
            select(SignalCache)
            .join(Signal, SignalCache.signal_id == Signal.id)
            .join(SignalSource, SignalCache.source_id == SignalSource.id)
            .where(
                and_(
                    SignalCache.entity_code == entity_code,
                    Signal.code == signal_code,
                    SignalSource.name == source_name,
                    SignalCache.expires_at > datetime.utcnow(),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_valid_cached(
        self,
        entity_code: str,
        signal_code: str,
        source_name: Optional[str] = None,
    ) -> Optional[SignalCache]:
        """
        Get valid (non-expired) cached signal data.
        TTL-aware retrieval that only returns data within validity window.
        """
        query = (
            select(SignalCache)
            .join(Signal, SignalCache.signal_id == Signal.id)
            .where(
                and_(
                    SignalCache.entity_code == entity_code,
                    Signal.code == signal_code,
                    SignalCache.expires_at > datetime.utcnow(),
                )
            )
        )
        if source_name:
            query = query.join(SignalSource, SignalCache.source_id == SignalSource.id).where(
                SignalSource.name == source_name
            )

        result = await self.db.execute(query.order_by(SignalCache.extracted_at.desc()))
        return result.scalar_one_or_none()

    async def get_entity_signals(
        self,
        entity_code: str,
        include_expired: bool = False,
    ) -> List[SignalCache]:
        """Get all cached signals for an entity (for continuous monitoring)."""
        query = select(SignalCache).where(SignalCache.entity_code == entity_code)

        if not include_expired:
            query = query.where(SignalCache.expires_at > datetime.utcnow())

        result = await self.db.execute(query.order_by(SignalCache.signal_id, SignalCache.extracted_at.desc()))
        return list(result.scalars().all())

    async def set(
        self,
        entity_code: str,
        signal_code: str,
        source_name: str,
        data: Dict[str, Any],
        ttl_seconds: int,
        confidence: float = 1.0,
        extraction_time_ms: float = 0.0,
    ) -> SignalCache:
        """Cache signal data."""
        signal_id = await self._resolve_signal_id(signal_code)
        source_id = await self._resolve_source_id(source_name)

        # Delete existing cache entry
        await self.db.execute(
            delete(SignalCache).where(
                and_(
                    SignalCache.entity_code == entity_code,
                    SignalCache.signal_id == signal_id,
                    SignalCache.source_id == source_id,
                )
            )
        )

        cache = SignalCache(
            entity_code=entity_code,
            signal_id=signal_id,
            source_id=source_id,
            data=data,
            confidence=confidence,
            ttl_seconds=ttl_seconds,
            expires_at=datetime.utcnow() + timedelta(seconds=ttl_seconds),
            extraction_time_ms=extraction_time_ms,
        )
        self.db.add(cache)
        await self.db.flush()
        return cache

    async def invalidate(
        self,
        entity_code: str,
        signal_code: Optional[str] = None,
    ) -> int:
        """Invalidate cache entries."""
        query = delete(SignalCache).where(SignalCache.entity_code == entity_code)

        if signal_code:
            sig_id_subq = select(Signal.id).where(Signal.code == signal_code).scalar_subquery()
            query = query.where(SignalCache.signal_id == sig_id_subq)

        result = await self.db.execute(query)
        return result.rowcount

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        result = await self.db.execute(
            delete(SignalCache).where(SignalCache.expires_at < datetime.utcnow())
        )
        return result.rowcount


class ModelVersionSignalRepository:
    """
    Repository for ModelVersionSignal operations.

    Manages the association between model versions and the specific
    signal_cache entries they consumed during scoring.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _resolve_signal_id(self, signal_code: str) -> int:
        """Get or create a Signal reference row, returning its integer id."""
        result = await self.db.execute(
            select(Signal.id).where(Signal.code == signal_code)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return row
        sig = Signal(code=signal_code)
        self.db.add(sig)
        await self.db.flush()
        return sig.id

    async def record_signal_usage(
        self,
        model_version_id: uuid.UUID,
        signal_cache_id: uuid.UUID,
        signal_code: str,
        entity_code: str,
        score: Optional[float] = None,
        weight: Optional[float] = None,
        contribution: Optional[float] = None,
        group_code: Optional[str] = None,
        proxy_tier: Optional[str] = None,
        expectation_level: Optional[str] = None,
        was_absent: bool = False,
        # V7 Phase 5/9 evidence-grade fields. All optional; existing callers
        # remain compatible.
        evidence_grade: Optional[str] = None,
        evidence_basis: Optional[str] = None,
        evidence_sources: Optional[List[Dict[str, Any]]] = None,
        evidence_pro: Optional[str] = None,
        evidence_counter: Optional[str] = None,
        evidence_tie_breaker: Optional[str] = None,
        absence_sub_type: Optional[str] = None,
        primitive_type: Optional[str] = None,
    ) -> ModelVersionSignal:
        """Record that a model version consumed a specific signal."""
        signal_id = await self._resolve_signal_id(signal_code)
        record = ModelVersionSignal(
            model_version_id=model_version_id,
            signal_cache_id=signal_cache_id,
            signal_id=signal_id,
            entity_code=entity_code,
            score=score,
            weight=weight,
            contribution=contribution,
            group_code=group_code,
            proxy_tier=proxy_tier,
            expectation_level=expectation_level,
            was_absent=was_absent,
            evidence_grade=evidence_grade,
            evidence_basis=evidence_basis,
            evidence_sources=evidence_sources or [],
            evidence_pro=evidence_pro,
            evidence_counter=evidence_counter,
            evidence_tie_breaker=evidence_tie_breaker,
            absence_sub_type=absence_sub_type,
            primitive_type=primitive_type,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def bulk_record(
        self,
        model_version_id: uuid.UUID,
        signals: List[Dict[str, Any]],
    ) -> List[ModelVersionSignal]:
        """Record multiple signal usages in one call.

        V7 Phase 5: each `signals[i]` dict may carry additional keys —
        `evidence_grade`, `evidence_basis`, `evidence_sources`,
        `evidence_pro`, `evidence_counter`, `evidence_tie_breaker`,
        `absence_sub_type`. They map straight through to the ORM columns.
        """
        records = []
        for sig in signals:
            signal_id = await self._resolve_signal_id(sig["signal_code"])
            record = ModelVersionSignal(
                model_version_id=model_version_id,
                signal_cache_id=sig["signal_cache_id"],
                signal_id=signal_id,
                entity_code=sig["entity_code"],
                score=sig.get("score"),
                weight=sig.get("weight"),
                contribution=sig.get("contribution"),
                group_code=sig.get("group_code"),
                proxy_tier=sig.get("proxy_tier"),
                expectation_level=sig.get("expectation_level"),
                was_absent=sig.get("was_absent", False),
                evidence_grade=sig.get("evidence_grade"),
                evidence_basis=sig.get("evidence_basis"),
                evidence_sources=sig.get("evidence_sources", []),
                evidence_pro=sig.get("evidence_pro"),
                evidence_counter=sig.get("evidence_counter"),
                evidence_tie_breaker=sig.get("evidence_tie_breaker"),
                absence_sub_type=sig.get("absence_sub_type"),
                primitive_type=sig.get("primitive_type"),
            )
            records.append(record)
        self.db.add_all(records)
        await self.db.flush()
        return records

    async def get_by_model_version(
        self,
        model_version_id: uuid.UUID,
    ) -> List[ModelVersionSignal]:
        """Get all signal usages for a model version — the configuration manifest."""
        result = await self.db.execute(
            select(ModelVersionSignal)
            .where(ModelVersionSignal.model_version_id == model_version_id)
            .order_by(ModelVersionSignal.group_code, ModelVersionSignal.signal_id)
        )
        return list(result.scalars().all())

    async def get_signal_codes_for_version(
        self,
        model_version_id: uuid.UUID,
    ) -> List[str]:
        """Get just the signal codes used by a model version (lightweight query)."""
        result = await self.db.execute(
            select(Signal.code)
            .join(ModelVersionSignal, ModelVersionSignal.signal_id == Signal.id)
            .where(ModelVersionSignal.model_version_id == model_version_id)
        )
        return [row[0] for row in result.all()]

    async def copy_to_new_version(
        self,
        source_model_version_id: uuid.UUID,
        target_model_version_id: uuid.UUID,
        override_signal_id: Optional[int] = None,
        override_values: Optional[Dict[str, Any]] = None,
    ) -> List[ModelVersionSignal]:
        """
        Copy signal associations from one model version to another.

        Used during signal overrides: the new v2+ model version inherits
        all signal bindings from v1, with optional overrides for the
        signal being audited.
        """
        source_records = await self.get_by_model_version(source_model_version_id)
        new_records = []
        for src in source_records:
            values = {
                "model_version_id": target_model_version_id,
                "signal_cache_id": src.signal_cache_id,
                "signal_id": src.signal_id,
                "entity_code": src.entity_code,
                "score": src.score,
                "weight": src.weight,
                "contribution": src.contribution,
                "group_code": src.group_code,
                "proxy_tier": src.proxy_tier,
                "expectation_level": src.expectation_level,
                "was_absent": src.was_absent,
                # V7 evidence-grade fields propagate to the new version so
                # an underwriter override doesn't drop the audit-grade
                # context that earned the original signal its place.
                "evidence_grade": src.evidence_grade,
                "evidence_basis": src.evidence_basis,
                "evidence_sources": src.evidence_sources or [],
                "evidence_pro": src.evidence_pro,
                "evidence_counter": src.evidence_counter,
                "evidence_tie_breaker": src.evidence_tie_breaker,
                "absence_sub_type": src.absence_sub_type,
                "primitive_type": src.primitive_type,
            }
            # Apply override for the audited signal
            if override_signal_id and src.signal_id == override_signal_id and override_values:
                values.update(override_values)

            new_records.append(ModelVersionSignal(**values))

        self.db.add_all(new_records)
        await self.db.flush()
        return new_records


class SignalAuditRepository:
    """
    Repository for SignalAuditRecord operations.

    Manages signal override audit trail for deterministic referral management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_override(
        self,
        model_version_signal_id: uuid.UUID,
        audited_value: float,
        overridden_by: uuid.UUID,
        rationale: str,
        evidence_reference: Optional[str] = None,
        score_impact: Optional[float] = None,
        tier_impact: Optional[int] = None,
    ):
        """Create a signal audit record for an override."""
        record = SignalAuditRecord(
            model_version_signal_id=model_version_signal_id,
            audited_value=audited_value,
            overridden_by=overridden_by,
            overridden_at=datetime.utcnow(),
            override_rationale=rationale,
            evidence_reference=evidence_reference,
            score_impact=score_impact,
            tier_impact=tier_impact,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def get_by_model_version(
        self,
        model_version_id: uuid.UUID,
    ) -> List:
        """Get all signal audit records for a model version."""
        result = await self.db.execute(
            select(SignalAuditRecord)
            .join(ModelVersionSignal, SignalAuditRecord.model_version_signal_id == ModelVersionSignal.id)
            .where(ModelVersionSignal.model_version_id == model_version_id)
            .order_by(SignalAuditRecord.created_at)
        )
        return list(result.scalars().all())

    async def get_entity_overrides(
        self,
        entity_code: str,
        signal_code: Optional[str] = None,
    ) -> List:
        """Get all signal overrides for an entity."""
        query = (
            select(SignalAuditRecord)
            .join(ModelVersionSignal, SignalAuditRecord.model_version_signal_id == ModelVersionSignal.id)
            .where(ModelVersionSignal.entity_code == entity_code)
        )
        if signal_code:
            query = query.join(Signal, ModelVersionSignal.signal_id == Signal.id).where(
                Signal.code == signal_code
            )

        query = query.order_by(SignalAuditRecord.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_audited_value(
        self,
        entity_code: str,
        signal_code: str,
    ) -> Optional[float]:
        """
        Get the latest audited value for a signal.

        Returns None if no override exists, meaning inferred score should be used.
        """
        result = await self.db.execute(
            select(SignalAuditRecord)
            .join(ModelVersionSignal, SignalAuditRecord.model_version_signal_id == ModelVersionSignal.id)
            .join(Signal, ModelVersionSignal.signal_id == Signal.id)
            .where(
                and_(
                    ModelVersionSignal.entity_code == entity_code,
                    Signal.code == signal_code,
                )
            )
            .order_by(SignalAuditRecord.created_at.desc())
            .limit(1)
        )
        record = result.scalar_one_or_none()
        return record.audited_value if record else None


class ModelVersionRepository:
    """Repository for ModelVersionRecord operations with is_latest management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        submission_id: uuid.UUID,
        version_type: str = "initial",
        **kwargs,
    ) -> ModelVersionRecord:
        """Create a new model version, marking it as latest.

        Automatically clears is_latest on any previous version for the
        same submission.
        """
        # Clear is_latest on existing versions for this submission
        await self.db.execute(
            update(ModelVersionRecord)
            .where(
                and_(
                    ModelVersionRecord.submission_id == submission_id,
                    ModelVersionRecord.is_latest == True,
                )
            )
            .values(is_latest=False)
        )

        # Determine version number
        result = await self.db.execute(
            select(ModelVersionRecord.version_number)
            .where(ModelVersionRecord.submission_id == submission_id)
            .order_by(ModelVersionRecord.version_number.desc())
            .limit(1)
        )
        last_number = result.scalar_one_or_none()
        next_number = (last_number or 0) + 1

        mv = ModelVersionRecord(
            version_code=generate_id("mv"),
            submission_id=submission_id,
            version_number=next_number,
            version_type=version_type,
            is_latest=True,
            **kwargs,
        )
        self.db.add(mv)
        await self.db.flush()
        return mv

    async def get_latest(self, submission_id: uuid.UUID) -> Optional[ModelVersionRecord]:
        """Get the latest model version for a submission (O(1) via partial index)."""
        result = await self.db.execute(
            select(ModelVersionRecord).where(
                and_(
                    ModelVersionRecord.submission_id == submission_id,
                    ModelVersionRecord.is_latest == True,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_by_code(self, version_code: str) -> Optional[ModelVersionRecord]:
        """Get model version by version_code."""
        result = await self.db.execute(
            select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)
        )
        return result.scalar_one_or_none()

    async def get_by_uuid(self, id: uuid.UUID) -> Optional[ModelVersionRecord]:
        """Get model version by UUID."""
        result = await self.db.execute(
            select(ModelVersionRecord).where(ModelVersionRecord.id == id)
        )
        return result.scalar_one_or_none()

    async def list_for_submission(
        self, submission_id: uuid.UUID
    ) -> List[ModelVersionRecord]:
        """List all model versions for a submission, ordered by version number."""
        result = await self.db.execute(
            select(ModelVersionRecord)
            .where(ModelVersionRecord.submission_id == submission_id)
            .order_by(ModelVersionRecord.version_number)
        )
        return list(result.scalars().all())


class AuditLogRepository:
    """Repository for AuditLog operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        event_type: str,
        event_action: str,
        resource_type: Optional[str] = None,
        resource_code: Optional[str] = None,
        user_id: Optional[uuid.UUID] = None,
        api_key_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create audit log entry."""
        log = AuditLog(
            event_type=event_type,
            event_action=event_action,
            resource_type=resource_type,
            resource_code=resource_code,
            user_id=user_id,
            api_key_id=api_key_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        self.db.add(log)
        await self.db.flush()
        return log

    async def get_for_resource(
        self,
        resource_type: str,
        resource_code: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs for a resource."""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_code == resource_code,
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
