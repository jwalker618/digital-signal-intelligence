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
    ModelVersion,
    SignalCache,
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
        composite_score: float,
        tier: int,
        tier_label: str,
        decision: DecisionType,
        recommended_premium: float,
        premium_options: Dict[str, float],
        model_version_id: Optional[uuid.UUID] = None,
        confidence: float = 1.0,
        referral_reasons: Optional[List[str]] = None,
        valid_days: int = 30,
    ) -> Quote:
        """Create a new quote."""
        quote = Quote(
            quote_id=generate_id("quo"),
            submission_id=submission_id,
            model_version_id=model_version_id,
            status=QuoteStatus.READY,
            composite_score=composite_score,
            confidence=confidence,
            tier=tier,
            tier_label=tier_label,
            decision=decision,
            auto_approve=decision == DecisionType.APPROVE,
            referral_reasons=referral_reasons or [],
            recommended_premium=recommended_premium,
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
