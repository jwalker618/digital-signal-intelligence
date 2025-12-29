"""
DSI Database Models

SQLAlchemy models for persistent storage of DSI data.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Index,
    Enum as SQLEnum,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .config import Base


# =============================================================================
# ENUMS
# =============================================================================

import enum


class SubmissionStatus(str, enum.Enum):
    """Submission processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuoteStatus(str, enum.Enum):
    """Quote status."""
    DRAFT = "draft"
    READY = "ready"
    BOUND = "bound"
    EXPIRED = "expired"
    DECLINED = "declined"


class DecisionType(str, enum.Enum):
    """Workflow decision outcomes."""
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class ReferralStatus(str, enum.Enum):
    """Referral review status."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DECLINED = "declined"
    MODIFIED = "modified"


# =============================================================================
# MODELS
# =============================================================================

class User(Base):
    """User account for API access."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    permissions = Column(JSONB, default=list)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="created_by_user")


class APIKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(20), nullable=False)  # For identification
    name = Column(String(255), nullable=False)
    permissions = Column(JSONB, default=list)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    last_used_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", back_populates="api_keys")

    __table_args__ = (
        Index("ix_api_keys_key_prefix", "key_prefix"),
    )


class Submission(Base):
    """Insurance submission record."""
    __tablename__ = "submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(String(50), unique=True, nullable=False, index=True)

    # Entity information
    entity_name = Column(String(500), nullable=False)
    domain_hint = Column(String(255))
    discovered_domain = Column(String(255))
    country_hint = Column(String(10))

    # Coverage
    coverage = Column(String(50), nullable=False, index=True)
    configuration = Column(String(100))
    locale = Column(String(10), default="US")

    # Status
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)

    # Submission data
    submission_data = Column(JSONB, default=dict)
    direct_query_responses = Column(JSONB, default=dict)

    # Processing metadata
    processing_started_at = Column(DateTime(timezone=True))
    processing_completed_at = Column(DateTime(timezone=True))
    processing_duration_ms = Column(Float)
    error_message = Column(Text)

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    created_by_user = relationship("User", back_populates="submissions")
    quotes = relationship("Quote", back_populates="submission", cascade="all, delete-orphan")
    model_versions = relationship("ModelVersion", back_populates="submission", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_submissions_entity_coverage", "entity_name", "coverage"),
        Index("ix_submissions_created_at", "created_at"),
    )


class Quote(Base):
    """Generated quote from pricing workflow."""
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id = Column(String(50), unique=True, nullable=False, index=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"))

    # Status
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.DRAFT, index=True)

    # Scoring
    composite_score = Column(Float)
    confidence = Column(Float)
    tier = Column(Integer)
    tier_label = Column(String(50))

    # Decision
    decision = Column(SQLEnum(DecisionType))
    auto_approve = Column(Boolean, default=False)
    referral_reasons = Column(JSONB, default=list)

    # Pricing
    base_premium = Column(Float)
    recommended_premium = Column(Float)
    recommended_limit = Column(Float)
    premium_options = Column(JSONB, default=dict)  # {limit: premium}

    # Validity
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))

    # Binding
    bound_at = Column(DateTime(timezone=True))
    bound_by = Column(UUID(as_uuid=True))
    policy_number = Column(String(100))

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="quotes")
    model_version = relationship("ModelVersion", back_populates="quote")
    referrals = relationship("Referral", back_populates="quote", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_quotes_status_valid", "status", "valid_until"),
    )


class Referral(Base):
    """Referral for underwriter review."""
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_id = Column(String(50), unique=True, nullable=False, index=True)
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)

    # Status
    status = Column(SQLEnum(ReferralStatus), default=ReferralStatus.PENDING, index=True)

    # Referral reasons
    reasons = Column(JSONB, default=list)
    priority = Column(Integer, default=5)  # 1=highest, 10=lowest

    # Assignment
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    assigned_at = Column(DateTime(timezone=True))

    # Review
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reviewed_at = Column(DateTime(timezone=True))
    review_decision = Column(String(50))
    review_notes = Column(Text)

    # Adjustments
    tier_override = Column(Integer)
    premium_adjustment = Column(Float)
    adjustments = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    quote = relationship("Quote", back_populates="referrals")


class ModelVersionRecord(Base):
    """Complete workflow execution snapshot for audit trail (database record)."""
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_id = Column(String(50), unique=True, nullable=False, index=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)

    # Version info
    version_number = Column(Integer, default=1)
    version_type = Column(String(50))  # initial, referral_review, amendment

    # Configuration
    config_hash = Column(String(64))
    coverage = Column(String(50))
    configuration_name = Column(String(100))

    # Discovery output
    discovery_output = Column(JSONB)

    # Signal outputs
    signal_outputs = Column(JSONB, default=list)
    categorical_outputs = Column(JSONB, default=list)
    group_scores = Column(JSONB, default=dict)

    # Scoring
    pure_composite_score = Column(Float)
    confidence = Column(Float)
    signal_coverage = Column(Float)

    # Conditions
    signal_conditions = Column(JSONB, default=list)
    query_conditions = Column(JSONB, default=list)

    # Tier
    tier_overrides = Column(JSONB, default=list)
    score_based_tier = Column(Integer)
    final_tier = Column(Integer)
    tier_label = Column(String(50))

    # Pricing
    base_premium = Column(Float)
    base_premium_method = Column(String(50))
    modifiers_applied = Column(JSONB, default=list)
    premium_after_modifiers = Column(Float)
    limit_premiums = Column(JSONB, default=dict)
    final_premium = Column(Float)

    # Decision
    decision = Column(SQLEnum(DecisionType))
    auto_approve = Column(Boolean, default=False)
    referral_reasons = Column(JSONB, default=list)
    notes = Column(JSONB, default=list)

    # Audit
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="model_versions")
    quote = relationship("Quote", back_populates="model_version", uselist=False)

    __table_args__ = (
        Index("ix_model_versions_submission", "submission_id", "version_number"),
    )


class SignalCache(Base):
    """Cache for extracted signal data."""
    __tablename__ = "signal_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cache key components
    entity_id = Column(String(255), nullable=False)
    signal_id = Column(String(100), nullable=False)
    source_name = Column(String(100), nullable=False)

    # Cached data
    data = Column(JSONB, nullable=False)
    confidence = Column(Float)

    # Validity
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ttl_seconds = Column(Integer)

    # Metadata
    extraction_time_ms = Column(Float)
    from_external_cache = Column(Boolean, default=False)

    __table_args__ = (
        Index("ix_signal_cache_lookup", "entity_id", "signal_id", "source_name"),
        Index("ix_signal_cache_entity", "entity_id"),
    )


class AuditLog(Base):
    """Audit log for compliance and debugging."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    event_action = Column(String(100), nullable=False)

    # Resource
    resource_type = Column(String(100))
    resource_id = Column(String(100))

    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Details
    details = Column(JSONB, default=dict)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
        Index("ix_audit_logs_user", "user_id", "created_at"),
    )
