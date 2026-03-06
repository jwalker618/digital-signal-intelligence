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
            submission_id=generate_id("sub"),
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

    async def get_by_id(self, submission_id: str) -> Optional[Submission]:
        """Get submission by submission_id."""
        result = await self.db.execute(
            select(Submission).where(Submission.submission_id == submission_id)
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
        submission_id: str,
        status: SubmissionStatus,
        error_message: Optional[str] = None,
    ) -> Optional[Submission]:
        """Update submission status."""
        await self.db.execute(
            update(Submission)
            .where(Submission.submission_id == submission_id)
            .values(
                status=status,
                error_message=error_message,
                processing_completed_at=datetime.utcnow() if status in [
                    SubmissionStatus.READY, SubmissionStatus.FAILED
                ] else None,
            )
        )
        return await self.get_by_id(submission_id)

    async def delete(self, submission_id: str) -> bool:
        """Delete a submission."""
        result = await self.db.execute(
            delete(Submission).where(Submission.submission_id == submission_id)
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
        premium_options: Dict[str, float],
        recommended_limit: Optional[float] = None,
        valid_days: int = 30,
        status: Optional[QuoteStatus] = None,
    ) -> Quote:
        """Create a new quote.

        Scoring / tier / decision data lives on the linked ModelVersionRecord.
        """
        quote = Quote(
            quote_id=generate_id("quo"),
            submission_id=submission_id,
            model_version_id=model_version_id,
            status=status or QuoteStatus.READY,
            recommended_premium=recommended_premium,
            recommended_limit=recommended_limit,
            premium_options=premium_options,
            valid_until=datetime.utcnow() + timedelta(days=valid_days),
        )
        self.db.add(quote)
        await self.db.flush()
        return quote

    async def get_by_id(self, quote_id: str) -> Optional[Quote]:
        """Get quote by quote_id."""
        result = await self.db.execute(
            select(Quote).where(Quote.quote_id == quote_id)
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
        quote_id: str,
        bound_by: uuid.UUID,
        policy_number: str,
    ) -> Optional[Quote]:
        """Bind a quote."""
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_id == quote_id)
            .values(
                status=QuoteStatus.BOUND,
                bound_at=datetime.utcnow(),
                bound_by=bound_by,
                policy_number=policy_number,
            )
        )
        return await self.get_by_id(quote_id)

    async def update_model_version_id(
        self,
        quote_id: str,
        model_version_id: uuid.UUID,
    ) -> Optional[Quote]:
        """Update the model version linked to a quote (Phase 8).

        Every signal override or manual tier/premium adjustment creates a new
        ModelVersionRecord.  The quote's FK must track the latest version so
        that GET /quotes/{id} returns current scoring data.
        """
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_id == quote_id)
            .values(model_version_id=model_version_id, updated_at=datetime.utcnow())
        )
        return await self.get_by_id(quote_id)

    async def update_status(
        self,
        quote_id: str,
        status: QuoteStatus,
    ) -> Optional[Quote]:
        """Update quote status (Phase 8).

        Used when a referral is approved (→ READY) or declined (→ DECLINED)
        so the quote record in the DB reflects the underwriter's decision.
        """
        await self.db.execute(
            update(Quote)
            .where(Quote.quote_id == quote_id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        return await self.get_by_id(quote_id)

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
            referral_id=generate_id("ref"),
            quote_id=quote_id,
            reasons=reasons,
            priority=priority,
            status=ReferralStatus.PENDING,
        )
        self.db.add(referral)
        await self.db.flush()
        return referral

    async def get_by_id(self, referral_id: str) -> Optional[Referral]:
        """Get referral by referral_id."""
        result = await self.db.execute(
            select(Referral).where(Referral.referral_id == referral_id)
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
        referral_id: str,
        assigned_to: uuid.UUID,
    ) -> Optional[Referral]:
        """Assign a referral to an underwriter."""
        await self.db.execute(
            update(Referral)
            .where(Referral.referral_id == referral_id)
            .values(
                assigned_to=assigned_to,
                assigned_at=datetime.utcnow(),
                status=ReferralStatus.IN_REVIEW,
            )
        )
        return await self.get_by_id(referral_id)

    async def review(
        self,
        referral_id: str,
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
            .where(Referral.referral_id == referral_id)
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
        return await self.get_by_id(referral_id)


class SignalCacheRepository:
    """Repository for SignalCache operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(
        self,
        entity_id: str,
        signal_id: str,
        source_name: str,
    ) -> Optional[SignalCache]:
        """Get cached signal data if valid."""
        result = await self.db.execute(
            select(SignalCache).where(
                and_(
                    SignalCache.entity_id == entity_id,
                    SignalCache.signal_id == signal_id,
                    SignalCache.source_name == source_name,
                    SignalCache.expires_at > datetime.utcnow(),
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_valid_cached(
        self,
        entity_id: str,
        signal_id: str,
        source_name: Optional[str] = None,
    ) -> Optional[SignalCache]:
        """
        Get valid (non-expired) cached signal data.
        TTL-aware retrieval that only returns data within validity window.
        """
        query = select(SignalCache).where(
            and_(
                SignalCache.entity_id == entity_id,
                SignalCache.signal_id == signal_id,
                SignalCache.expires_at > datetime.utcnow(),
            )
        )
        if source_name:
            query = query.where(SignalCache.source_name == source_name)

        result = await self.db.execute(query.order_by(SignalCache.extracted_at.desc()))
        return result.scalar_one_or_none()

    async def get_entity_signals(
        self,
        entity_id: str,
        include_expired: bool = False,
    ) -> List[SignalCache]:
        """Get all cached signals for an entity (for continuous monitoring)."""
        query = select(SignalCache).where(SignalCache.entity_id == entity_id)

        if not include_expired:
            query = query.where(SignalCache.expires_at > datetime.utcnow())

        result = await self.db.execute(query.order_by(SignalCache.signal_id, SignalCache.extracted_at.desc()))
        return list(result.scalars().all())

    async def set(
        self,
        entity_id: str,
        signal_id: str,
        source_name: str,
        data: Dict[str, Any],
        ttl_seconds: int,
        confidence: float = 1.0,
        extraction_time_ms: float = 0.0,
    ) -> SignalCache:
        """Cache signal data."""
        # Delete existing cache entry
        await self.db.execute(
            delete(SignalCache).where(
                and_(
                    SignalCache.entity_id == entity_id,
                    SignalCache.signal_id == signal_id,
                    SignalCache.source_name == source_name,
                )
            )
        )

        cache = SignalCache(
            entity_id=entity_id,
            signal_id=signal_id,
            source_name=source_name,
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
        entity_id: str,
        signal_id: Optional[str] = None,
    ) -> int:
        """Invalidate cache entries."""
        query = delete(SignalCache).where(SignalCache.entity_id == entity_id)

        if signal_id:
            query = query.where(SignalCache.signal_id == signal_id)

        result = await self.db.execute(query)
        return result.rowcount

    async def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        result = await self.db.execute(
            delete(SignalCache).where(SignalCache.expires_at < datetime.utcnow())
        )
        return result.rowcount


class SignalAuditRepository:
    """
    Repository for SignalAuditRecord operations (Phase 8).

    Manages signal override audit trail for deterministic referral management.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_override(
        self,
        signal_cache_id: uuid.UUID,
        model_version_id: uuid.UUID,
        signal_id: str,
        entity_id: str,
        inferred_value: Dict[str, Any],
        audited_value: Dict[str, Any],
        overridden_by: uuid.UUID,
        rationale: str,
        evidence_reference: Optional[str] = None,
        score_impact: Optional[float] = None,
        tier_impact: Optional[int] = None,
    ):
        """Create a signal audit record for an override."""
        from .models import SignalAuditRecord

        record = SignalAuditRecord(
            signal_cache_id=signal_cache_id,
            model_version_id=model_version_id,
            signal_id=signal_id,
            entity_id=entity_id,
            inferred_value=inferred_value,
            audited_value=audited_value,
            is_overridden=True,
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
        from .models import SignalAuditRecord

        result = await self.db.execute(
            select(SignalAuditRecord)
            .where(SignalAuditRecord.model_version_id == model_version_id)
            .order_by(SignalAuditRecord.created_at)
        )
        return list(result.scalars().all())

    async def get_entity_overrides(
        self,
        entity_id: str,
        signal_id: Optional[str] = None,
    ) -> List:
        """Get all signal overrides for an entity."""
        from .models import SignalAuditRecord

        query = select(SignalAuditRecord).where(
            SignalAuditRecord.entity_id == entity_id
        )
        if signal_id:
            query = query.where(SignalAuditRecord.signal_id == signal_id)

        query = query.order_by(SignalAuditRecord.created_at.desc())
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_audited_value(
        self,
        entity_id: str,
        signal_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the latest audited value for a signal (Phase 8).

        Returns None if no override exists, meaning inferred_value should be used.
        """
        from .models import SignalAuditRecord

        result = await self.db.execute(
            select(SignalAuditRecord)
            .where(
                and_(
                    SignalAuditRecord.entity_id == entity_id,
                    SignalAuditRecord.signal_id == signal_id,
                    SignalAuditRecord.is_overridden == True,
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
            version_id=generate_id("mv"),
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

    async def get_by_id(self, version_id: str) -> Optional[ModelVersionRecord]:
        """Get model version by version_id."""
        result = await self.db.execute(
            select(ModelVersionRecord).where(ModelVersionRecord.version_id == version_id)
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
        resource_id: Optional[str] = None,
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
            resource_id=resource_id,
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
        resource_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get audit logs for a resource."""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.resource_type == resource_type,
                    AuditLog.resource_id == resource_id,
                )
            )
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
