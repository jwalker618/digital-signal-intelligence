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

class Tenant(Base):
    """Isolated customer organisation.

    All tenant-scoped resources (users, submissions, etc.) carry a tenant_id
    FK back to this table. Multi-tenancy is enforced at the query layer via
    the tenant_middleware.
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    sso_provider = Column(String(20), nullable=False, default="NONE")  # NONE | SAML | OIDC
    sso_metadata = Column(JSONB, nullable=False, default=dict)
    settings = Column(JSONB, nullable=False, default=dict)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    users = relationship("User", back_populates="tenant", foreign_keys="User.tenant_id")
    roles = relationship("Role", back_populates="tenant", cascade="all, delete-orphan")
    sessions = relationship("UserSession", back_populates="tenant", cascade="all, delete-orphan")


class Role(Base):
    """Tenant-scoped role with a granular permission set.

    System roles (is_system_role=True) are seeded by migration and cannot
    be deleted. Custom roles can be created by admins per tenant.
    """
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    permissions = Column(JSONB, nullable=False, default=list)
    is_system_role = Column(Boolean, nullable=False, default=False)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    tenant = relationship("Tenant", back_populates="roles")
    users = relationship("User", back_populates="role", foreign_keys="User.role_id")

    __table_args__ = (
        Index("uq_roles_tenant_name", "tenant_id", "name", unique=True),
    )


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

    # Multi-tenant / role
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=True, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=True)

    # MFA
    mfa_secret = Column(String(255))  # Encrypted TOTP secret
    mfa_backup_codes = Column(JSONB)  # Encrypted list of single-use codes
    mfa_enabled = Column(Boolean, nullable=False, default=False)

    # Account security
    is_locked = Column(Boolean, nullable=False, default=False)
    failed_login_attempts = Column(Integer, nullable=False, default=0)
    password_reset_token_hash = Column(String(255))
    password_reset_expires_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))

    # Relationships
    api_keys = relationship("APIKey", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="created_by_user")
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    role = relationship("Role", back_populates="users", foreign_keys=[role_id])
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan", foreign_keys="UserSession.user_id")


class UserSession(Base):
    """Active JWT session with refresh token rotation.

    A session row exists per active refresh token. When a refresh token is
    used, the row is updated with a new hash (rotation). Revoking a session
    sets revoked_at and invalidates all tokens associated with it.
    """
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash = Column(String(255), unique=True, nullable=False, index=True)
    user_agent = Column(Text)
    ip_address = Column(String(45))
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True))
    last_activity_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions", foreign_keys=[user_id])
    tenant = relationship("Tenant", back_populates="sessions")


class APIKey(Base):
    """API key for programmatic access."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    key_prefix = Column(String(50), nullable=False)  # For identification
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
    submission_code = Column(String(50), unique=True, nullable=False, index=True)

    # Entity information
    entity_name = Column(String(500), nullable=False)
    domain_hint = Column(String(255))
    discovered_domain = Column(String(255))
    country_hint = Column(String(50))

    # Coverage
    coverage = Column(String(50), nullable=False, index=True)
    configuration = Column(String(100))
    locale = Column(String(50), default="US")

    # Status
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, index=True)

    # Submission data
    submission_data = Column(JSONB, default=dict)
    direct_query_responses = Column(JSONB, default=dict)

    # Discovery output (one-time per submission, not per model version)
    discovery_output = Column(JSONB)

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
    model_versions = relationship("ModelVersionRecord", back_populates="submission", cascade="all, delete-orphan")
    notes = relationship("SubmissionNote", back_populates="submission", cascade="all, delete-orphan", order_by="SubmissionNote.created_at")

    __table_args__ = (
        Index("ix_submissions_entity_coverage", "entity_name", "coverage"),
        Index("ix_submissions_created_at", "created_at"),
    )


class SubmissionNote(Base):
    """Individual note on a submission — workflow-generated or underwriter-added."""
    __tablename__ = "submission_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    note = Column(Text, nullable=False)
    source = Column(String(100), nullable=False)  # workflow, underwriter, system, etc.
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    submission = relationship("Submission", back_populates="notes")

    __table_args__ = (
        Index("ix_submission_notes_submission", "submission_id"),
    )


class ConfigSnapshot(Base):
    """Frozen config at execution time — one row per unique config_hash.

    Enables client-side scenario recalculation without backend round-trips.
    Referenced by model_versions via config_hash.
    """
    __tablename__ = "config_snapshots"

    config_hash = Column(String(64), primary_key=True)
    coverage = Column(String(50), nullable=False)
    configuration_name = Column(String(100), nullable=False)

    # Tier & loss band config
    tier_band_interpretation = Column(JSONB)
    loss_band_interpretation = Column(JSONB)
    correlation_matrix_version = Column(String(100))

    # Exposure config
    exposure_assessment_method = Column(String(50))
    exposure_band_interpretation = Column(JSONB)

    # Scenario recalculation configs
    loss_correlation_config = Column(JSONB)
    ilf_curve_config = Column(JSONB)
    deductible_factor_table = Column(JSONB)
    exposure_modifier_config = Column(JSONB)
    guardrails_config = Column(JSONB)

    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Quote(Base):
    """
    Generated quote from pricing workflow.

    De-duplicated: scoring, tier, decision, and pricing details live on
    the linked ModelVersionRecord. Quote holds only quote-lifecycle fields
    (status, validity, binding) plus the recommended premium/limit for
    quick list queries.
    """
    __tablename__ = "quotes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_code = Column(String(50), unique=True, nullable=False, index=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)
    model_version_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id"), nullable=False)

    # Status
    status = Column(SQLEnum(QuoteStatus), default=QuoteStatus.DRAFT, index=True)

    # Pricing summary (denormalised for fast list queries)
    recommended_premium = Column(Float)
    recommended_limit = Column(Float)

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
    model_version = relationship("ModelVersionRecord", back_populates="quote")
    referrals = relationship("Referral", back_populates="quote", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_quotes_status_valid", "status", "valid_until"),
    )


class Referral(Base):
    """Referral for underwriter review."""
    __tablename__ = "referrals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referral_code = Column(String(50), unique=True, nullable=False, index=True)
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
    """
    Complete workflow execution snapshot for audit trail (database record).

    This is the single source of truth for all scoring, pricing, and
    assessment data.  Quotes reference this via model_version_id.
    """
    __tablename__ = "model_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version_code = Column(String(50), unique=True, nullable=False, index=True)
    submission_id = Column(UUID(as_uuid=True), ForeignKey("submissions.id"), nullable=False)

    # Version info
    version_number = Column(Integer, default=1)
    version_type = Column(String(50))  # initial, referral_review, amendment
    is_latest = Column(Boolean, default=True, nullable=False)

    # Configuration
    config_hash = Column(String(64))
    coverage = Column(String(50))
    configuration_name = Column(String(100))

    # Signal outputs (signal_outputs removed — fully covered by model_version_signals join)
    # Discovery output moved to submissions table (one-time per submission)
    categorical_outputs = Column(JSONB, default=list)
    group_scores = Column(JSONB, default=dict)

    # Scoring
    pure_composite_score = Column(Float)
    final_composite_score = Column(Float)    # Score used for tier margin / distance calculations
    confidence = Column(Float)
    signal_coverage = Column(Float)

    # WE-4: Causal Adjustment Factor audit summary
    #   Full payload (precursors, trajectory, constraint regime) lives in
    #   we_causal_adjustments. These columns capture the at-a-glance state.
    caf_value = Column(Float, nullable=False, default=1.0, server_default="1.0")
    caf_confidence = Column(Float)
    caf_constrained = Column(Boolean, nullable=False, default=False, server_default="false")
    static_premium = Column(Float)  # P_static for CAF audit: P_final = P_static * CAF

    # Conditions
    signal_conditions = Column(JSONB, default=list)
    query_conditions = Column(JSONB, default=list)

    # Tier
    tier_overrides = Column(JSONB, default=list)
    score_based_tier = Column(Integer)
    final_tier = Column(Integer)
    tier_label = Column(String(50))

    # =========================================================================
    # TIER MARGIN CONTEXT (Phase A4)
    # =========================================================================
    tier_margin_percentile = Column(Float)           # 0.0 = at tier min, 1.0 = at tier max
    tier_margin_tier_min = Column(Float)              # Lower bound of current tier
    tier_margin_tier_max = Column(Float)              # Upper bound of current tier
    tier_margin_distance_better = Column(Float)       # Points from better tier boundary (null if best)
    tier_margin_distance_worse = Column(Float)        # Points from worse tier boundary (null if worst)
    tier_margin_adjacent_better = Column(Integer)     # ID of next better tier (null if best)
    tier_margin_adjacent_worse = Column(Integer)      # ID of next worse tier (null if worst)

    # tier_band_interpretation moved to config_snapshots table

    # Pricing
    base_premium = Column(Float)
    base_premium_method = Column(String(50))
    base_premium_derivation = Column(JSONB, default=dict)
    modifiers_applied = Column(JSONB, default=list)
    premium_after_modifiers = Column(Float)
    final_premium = Column(Float)
    final_premium_detail = Column(JSONB, default=dict)  # ILF/deductible breakdown for the selected limit
    uncapped_premium = Column(Float, nullable=True)

    # Guardrail detail
    guardrail_warnings = Column(JSONB, default=list)  # List[Note]-shaped: [{"note": ..., "source": ...}]
    premium_was_capped = Column(Boolean, default=False)

    # ILF (Increased Limit Factor) audit
    ilf_factor = Column(Float)                       # The ILF multiplier applied at the requested limit
    ilf_method = Column(String(50))                  # parametric curve type used
    ilf_anchor_limit = Column(Float)                 # The limit where ILF = 1.0 (e.g. 10_000_000)

    # =========================================================================
    # ROL RECOMMENDATION (Phase C — dual recommendation engine)
    # =========================================================================
    rol_upper_limit = Column(Float)                  # Upper recommendation: best ROL value limit
    rol_upper_premium = Column(Float)                # Premium at upper recommended limit
    rol_upper_rol = Column(Float)                    # ROL at upper recommended limit
    rol_upper_rationale = Column(Text)               # Why this limit was recommended
    rol_lower_limit = Column(Float)                  # Lower recommendation: minimum adequate limit
    rol_lower_premium = Column(Float)                # Premium at lower recommended limit
    rol_lower_rol = Column(Float)                    # ROL at lower recommended limit
    rol_lower_rationale = Column(Text)               # Why this limit was recommended
    rol_structure_type = Column(String(50))           # ground_up, tower, subscription

    # Decision
    decision = Column(SQLEnum(DecisionType))
    auto_approve = Column(Boolean, default=False)
    referral_reasons = Column(JSONB, default=list)
    # notes moved to submission_notes table

    # =========================================================================
    # LOSS PROPENSITY (Phase 16 - three-pillar: loss)
    # =========================================================================
    loss_propensity_score = Column(Float)            # 0-100 composite
    severity_propensity_score = Column(Float)        # 0-100 composite
    loss_propensity_band = Column(String(50))        # very_low .. high
    severity_propensity_band = Column(String(50))    # minimal .. catastrophic
    loss_confidence = Column(Float)
    loss_cohort_code = Column(String(100))
    loss_cohort_name = Column(String(255))
    loss_cohort_confidence = Column(Float)
    loss_frequency_multiplier = Column(Float)
    loss_severity_multiplier = Column(Float)
    loss_combined_modifier = Column(Float)
    loss_group_scores = Column(JSONB)                 # {group: {freq_score, sev_score, weight, ...}}
    loss_trend_direction = Column(String(50))        # improving / stable / deteriorating (combined)
    loss_frequency_trend_direction = Column(String(50))  # frequency-specific trend
    loss_severity_trend_direction = Column(String(50))   # severity-specific trend
    loss_previous_score = Column(Float)              # combined previous score (deprecated, kept for compat)
    loss_previous_frequency_score = Column(Float)    # previous period frequency propensity score
    loss_previous_severity_score = Column(Float)     # previous period severity propensity score
    loss_score_velocity = Column(Float)              # combined velocity (deprecated, kept for compat)
    loss_frequency_velocity = Column(Float)          # frequency score velocity (points/month)
    loss_severity_velocity = Column(Float)           # severity score velocity (points/month)
    loss_last_refresh = Column(DateTime(timezone=True))
    # correlation_matrix_version moved to config_snapshots
    # loss_band_interpretation moved to config_snapshots

    # =========================================================================
    # EXPOSURE ASSESSMENT (three-pillar: exposure)
    # =========================================================================
    exposure_value = Column(Float)                   # Primary exposure metric (TIV, revenue, etc.)
    exposure_band_id = Column(Integer)
    exposure_band_label = Column(String(100))
    exposure_band_boundaries = Column(JSONB)          # {min_value, max_value, modifier} — snapshot of band at execution time
    exposure_size_score = Column(Float)              # 0-100 normalised size score
    exposure_complexity_score = Column(Float)          # 0-100 normalised complexity score
    exposure_modifier = Column(Float)                 # Multiplier applied to premium
    # exposure_assessment_method moved to config_snapshots
    exposure_components = Column(JSONB)                # {size_factor, growth_factor, concentration_factor, ...}
    # exposure_band_interpretation moved to config_snapshots
    # Config snapshots (tier_band_interpretation, loss_band_interpretation,
    # loss_correlation_config, ilf_curve_config, deductible_factor_table,
    # exposure_modifier_config, guardrails_config) moved to config_snapshots table
    # — referenced via config_hash FK

    # Audit
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    submission = relationship("Submission", back_populates="model_versions")
    quote = relationship("Quote", back_populates="model_version", uselist=False)

    __table_args__ = (
        Index("ix_model_versions_submission", "submission_id", "version_number"),
        Index(
            "ix_model_versions_latest",
            "submission_id",
            unique=True,
            postgresql_where=Column("is_latest").is_(True),
        ),
    )


class Signal(Base):
    """Reference table for signal codes. Auto-populated on first encounter."""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), unique=True, nullable=False, index=True)


class SignalSource(Base):
    """Reference table for signal source names. Auto-populated on first encounter."""
    __tablename__ = "signal_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)


class SignalCache(Base):
    """Cache for extracted signal data — pure, unadulterated signal extract."""
    __tablename__ = "signal_cache"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Cache key components
    entity_code = Column(String(255), nullable=False)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)
    source_id = Column(Integer, ForeignKey("signal_sources.id"), nullable=False)

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
        Index("ix_signal_cache_lookup", "entity_code", "signal_id", "source_id"),
        Index("ix_signal_cache_entity", "entity_code"),
    )


class ModelVersionSignal(Base):
    """
    Association table linking a ModelVersionRecord to the specific SignalCache
    entries it consumed during scoring.

    The bridge between the full signal repository (signal_cache) and what
    each individual model actually used. Populated at workflow execution time
    when the scorer iterates through config.signal_registry.
    """
    __tablename__ = "model_version_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # The model version that consumed this signal
    model_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id"),
        nullable=False,
    )

    # The cached signal that was consumed
    signal_cache_id = Column(
        UUID(as_uuid=True),
        ForeignKey("signal_cache.id"),
        nullable=False,
    )

    # Signal reference (integer FK for efficiency)
    signal_id = Column(Integer, ForeignKey("signals.id"), nullable=False)

    # Denormalised for fast queries without joining signal_cache
    entity_code = Column(String(255), nullable=False)

    # Snapshot of what the signal contributed at scoring time
    score = Column(Float)                          # The score used (inferred or audited)
    weight = Column(Float)                         # Signal weight within group (from config)
    group_weight = Column(Float)                   # Group weight toward composite (from config)
    contribution = Column(Float)                   # Weighted contribution to composite
    group_code = Column(String(100))               # Which group this signal belonged to
    proxy_tier = Column(String(50))                # DIRECT_OBSERVABLE / INFERRED_PROXY / COHORT_INFERENCE
    expectation_level = Column(String(50))         # UNIVERSAL / ENTERPRISE / etc.
    was_absent = Column(Boolean, default=False)    # Signal expected but not found

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_mvs_model_version", "model_version_id"),
        Index("ix_mvs_signal_cache", "signal_cache_id"),
        Index("ix_mvs_lookup", "model_version_id", "signal_id", unique=True),
    )


class SignalAuditRecord(Base):
    """
    Signal audit record for underwriter overrides.

    The existence of a record implies the signal was overridden.
    All signal/entity/model context is derived via the model_version_signal FK.
    """
    __tablename__ = "signal_audit_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Single FK — all context (signal, entity, model version, cache) derivable from here
    model_version_signal_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_version_signals.id"),
        nullable=False,
        index=True,
    )

    # The audited value (float score set by underwriter)
    audited_value = Column(Float, nullable=False)

    # Override metadata
    overridden_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    overridden_at = Column(DateTime(timezone=True))
    override_rationale = Column(Text)
    evidence_reference = Column(String(500))

    # Impact tracking
    score_impact = Column(Float)  # Delta to composite score
    tier_impact = Column(Integer)  # Change in tier (if any)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Audit log for compliance and debugging.

    Extended in A-2 with action_type (granular enum), before/after state,
    tenant scoping, session linkage, and request correlation.
    """
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    event_action = Column(String(100), nullable=False)
    action_type = Column(String(50), index=True)  # AuditActionType enum value

    # Scoping (A-2)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"))
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id", ondelete="SET NULL"))
    request_id = Column(String(50), index=True)

    # Resource
    resource_type = Column(String(100))
    resource_code = Column(String(100))

    # Actor
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    api_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"))
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # State change (A-2)
    before_state = Column(JSONB)
    after_state = Column(JSONB)

    # Additional details
    details = Column(JSONB, default=dict)
    duration_ms = Column(Float)

    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    __table_args__ = (
        Index("ix_audit_logs_resource", "resource_type", "resource_code"),
        Index("ix_audit_logs_user", "user_id", "created_at"),
        Index("ix_audit_logs_tenant_created", "tenant_id", "created_at"),
    )


class UserSessionActivity(Base):
    """Per-request activity log within a user session.

    Records every authenticated API request the user makes. Feeds session
    duration, page-view, and activity metrics for the admin backend (B-1).
    Distinct from AuditLog -- this is low-cardinality request metadata,
    not business events.
    """
    __tablename__ = "user_session_activity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("user_sessions.id", ondelete="SET NULL"), nullable=True)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer)
    duration_ms = Column(Float)
    request_id = Column(String(50))
    occurred_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



# =============================================================================
# COMMERCIAL TERMS — entity-level economics applied to technical premium
# =============================================================================

class CommercialTermsRecord(Base):
    """Commercial terms for a pricing entity.

    Captures the entity-level economics that transform technical premium
    into gross/reporting premium. Linked to model_version (which holds
    the technical premium) to form the complete pricing picture.

    model_versions = technical premium (actuarial)
    commercial_terms = gross/reporting premium (commercial)
    """
    __tablename__ = "commercial_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id"),
        nullable=False,
        index=True,
    )

    # Entity identification
    entity_id = Column(String(100), nullable=False, index=True)
    entity_name = Column(String(255))
    entity_market = Column(String(50))  # lloyds, us, eu, apac

    # Currency context
    base_currency = Column(String(3), nullable=False, default="USD")
    fx_rate_to_usd = Column(Float)  # Rate used at execution time
    fx_rate_source = Column(String(100))  # static, ecb, bloomberg
    fx_rate_date = Column(DateTime(timezone=True))

    # Technical premium (USD) — snapshot from model_version for convenience
    technical_premium_usd = Column(Float)

    # Technical premium in entity currency
    technical_premium_local = Column(Float)

    # Distribution structure
    distribution_type = Column(String(50))  # SUBSCRIPTION, TOWER, BUNDLED, DECOUPLED, DIRECT
    signed_line = Column(Float)  # Participation fraction (1.0 = ground-up/100%)
    role = Column(String(20))  # LEAD, FOLLOW
    lead_loading_factor = Column(Float, default=1.0)

    # Net premium = technical × signed_line × lead_loading
    net_premium = Column(Float)

    # Deductions — JSONB because there are many types and they vary by entity
    # Structure: {"brokerage": {"rate": 0.20, "amount": 1234.56},
    #             "overrider": {"rate": 0.025, "amount": ...},
    #             "fronting_fee": {"rate": 0.05, "amount": ...},
    #             "profit_commission": {"rate": 0.15, "threshold": 0.70, "amount": ...}}
    deductions = Column(JSONB, default=dict)
    total_commission = Column(Float)

    # Taxes and levies — JSONB for same reasons as deductions
    # Structure: {"ipt": {"rate": 0.12, "amount": ...},
    #             "stamp_duty": {"rate": 0.005, "amount": ...},
    #             "regulatory_levy": {"rate": 0.01, "amount": ...}}
    taxes_and_levies = Column(JSONB, default=dict)
    total_taxes = Column(Float)

    # Gross premium = net + commission + taxes
    gross_premium = Column(Float)

    # Offered premium — underwriter discretion applied to gross
    offered_premium = Column(Float)
    offered_premium_discretion = Column(Float)  # ±% discretion applied
    offered_premium_rationale = Column(Text)  # Why this discretion was chosen
    offered_premium_set_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    offered_premium_set_at = Column(DateTime(timezone=True))

    # Minimum premium enforcement
    minimum_gross_premium = Column(Float)
    at_minimum_premium = Column(Boolean, default=False)

    # Written/earned — time values
    written_date = Column(DateTime(timezone=True))  # When premium is written
    earned_start = Column(DateTime(timezone=True))  # Earning period start (inception)
    earned_end = Column(DateTime(timezone=True))  # Earning period end (expiry)
    earned_method = Column(String(50))  # pro_rata, risks_attaching, etc.

    # Audit
    created_by = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    model_version = relationship("ModelVersionRecord", backref="commercial_terms")

    __table_args__ = (
        Index("ix_commercial_terms_entity", "entity_id", "created_at"),
    )


# =============================================================================
# RISK TERMS — deductible nuance and reporting-side risk structure
# =============================================================================

class RiskTermsRecord(Base):
    """Risk terms capturing deductible and coverage nuance for reporting.

    This is the reporting/market-facing view of the risk structure.
    The pricer handles deductible factors via interpolation; this table
    captures the contractual nuance that matters for claims, bordereaux,
    and regulatory reporting.

    Linked to commercial_terms because risk structure is an entity-level
    concern (different entities may write the same risk with different terms).
    """
    __tablename__ = "risk_terms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    model_version_id = Column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id"),
        nullable=False,
        index=True,
    )

    # Deductible structure
    deductible_type = Column(String(50))  # per_occurrence, aggregate, franchise, nil
    deductible_amount = Column(Float)
    deductible_currency = Column(String(3), default="USD")
    deductible_basis = Column(String(100))  # each_and_every_loss, per_policy_period, etc.

    # Self-Insured Retention (SIR) — distinct from deductible
    sir_amount = Column(Float)
    sir_applies = Column(Boolean, default=False)

    # Waiting period (time-based deductible, common in cyber/BI)
    waiting_period_hours = Column(Float)
    waiting_period_type = Column(String(50))  # business_interruption, contingent_bi, etc.

    # Aggregate limits/deductibles
    aggregate_limit = Column(Float)
    aggregate_deductible = Column(Float)
    aggregate_basis = Column(String(100))  # per_policy_period, per_location, etc.

    # Reinstatement provisions
    reinstatements = Column(Integer)  # Number of reinstatements (0 = none)
    reinstatement_rate = Column(Float)  # % of premium per reinstatement

    # Co-insurance / layering context
    attachment_point = Column(Float)  # For excess layers
    layer_limit = Column(Float)  # Limit of this specific layer

    # Sub-limits — JSONB for flexibility
    # Structure: [{"peril": "flood", "sub_limit": 5000000, "sub_deductible": 100000}, ...]
    sub_limits = Column(JSONB, default=list)

    # Coverage extensions/exclusions — JSONB
    # Structure: {"extensions": ["cyber_terrorism", "social_engineering"],
    #             "exclusions": ["war", "nuclear"]}
    coverage_terms = Column(JSONB, default=dict)

    # Audit
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    model_version = relationship("ModelVersionRecord", backref="risk_terms")


class LossEvent(Base):
    """Actual loss event -- a claim or incident reported after a policy is bound.

    Loss events are linked to a specific ModelVersionRecord (the assessment
    active at bind time) via the SignalLossLinker. The linked assessment
    is the source of signal scores that feed recalibration analysis (C-2).
    """
    __tablename__ = "loss_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)

    # Entity
    entity_name = Column(String(500), nullable=False)

    # Policy linkage
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id", ondelete="SET NULL"))
    policy_reference = Column(String(100))
    claim_reference = Column(String(100))

    # Timeline
    loss_date = Column(DateTime(timezone=True), nullable=False)
    notification_date = Column(DateTime(timezone=True))
    closed_date = Column(DateTime(timezone=True))

    # Classification
    loss_type = Column(String(100), nullable=False)
    coverage = Column(String(50), nullable=False)
    config_name = Column(String(100))

    # Financial
    incurred_amount = Column(Float, nullable=False, default=0.0)
    paid_amount = Column(Float, nullable=False, default=0.0)
    reserved_amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(3), nullable=False, default="USD")

    # Status + cause
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN | CLOSED | REOPENED
    cause_description = Column(Text)
    event_metadata = Column("metadata", JSONB, nullable=False, default=dict)  # reserved 'metadata' is the column name

    # Link to assessment at bind time (populated by linker)
    linked_assessment_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="SET NULL"))
    linker_run_at = Column(DateTime(timezone=True))

    # Audit
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    quote = relationship("Quote", foreign_keys=[quote_id])
    linked_assessment = relationship("ModelVersionRecord", foreign_keys=[linked_assessment_id])
    signal_loss_pairs = relationship("SignalLossPair", back_populates="loss_event", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_loss_events_entity_date", "entity_name", "loss_date"),
        Index("ix_loss_events_coverage_status", "coverage", "status"),
    )


class SignalLossPair(Base):
    """Pairs a bind-time signal profile with the actual loss outcome.

    This is the primary input to the C-2 recalibration engine: for every
    loss, a snapshot of exactly the signal scores the model used at bind,
    so we can back-test which signals actually predicted the loss.
    """
    __tablename__ = "signal_loss_pairs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    loss_event_id = Column(UUID(as_uuid=True), ForeignKey("loss_events.id", ondelete="CASCADE"), nullable=False, index=True)

    # Signal profile at bind time (dict of signal_code -> score)
    signal_scores_at_bind = Column(JSONB, nullable=False, default=dict)

    # Composite metrics at bind time
    composite_score_at_bind = Column(Float)
    tier_at_bind = Column(Integer)
    loss_propensity_at_bind = Column(Float)
    confidence_at_bind = Column(Float)

    # Temporal
    bind_date = Column(DateTime(timezone=True))
    time_to_loss_days = Column(Integer)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    assessment = relationship("ModelVersionRecord", foreign_keys=[assessment_id])
    loss_event = relationship("LossEvent", back_populates="signal_loss_pairs", foreign_keys=[loss_event_id])

    __table_args__ = (
        Index("uq_signal_loss_pair_composite", "assessment_id", "loss_event_id", unique=True),
    )



class RecalibrationProposal(Base):
    """A recalibration proposal awaiting review + deployment (C-2).

    Generated by the recalibration engine, reviewed by actuarial users in
    the governance UI (C-3), deployed via the B-2 config management pipeline.
    """
    __tablename__ = "recalibration_proposals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)

    coverage = Column(String(50), nullable=False)
    config_name = Column(String(100), nullable=False)

    proposed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    proposed_by = Column(String(100), nullable=False)
    trigger = Column(String(50), nullable=False, default="system")

    status = Column(String(20), nullable=False, default="DRAFT")

    signal_report_cards = Column(JSONB, nullable=False, default=list)
    weight_changes = Column(JSONB, nullable=False, default=list)
    tier_threshold_changes = Column(JSONB, nullable=False, default=list)
    impact_assessment = Column(JSONB, nullable=False, default=dict)
    statistical_evidence = Column(JSONB, nullable=False, default=dict)
    sample_size = Column(Integer, nullable=False, default=0)

    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    review_decision = Column(String(20))
    review_rationale = Column(Text)
    reviewed_at = Column(DateTime(timezone=True))

    deployed_config_version_id = Column(UUID(as_uuid=True))
    deployed_at = Column(DateTime(timezone=True))

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)



class ExtractorHealth(Base):
    """Per-extractor health metrics for the admin dashboard (B-1)."""
    __tablename__ = "extractor_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    extractor_id = Column(String(200), nullable=False, index=True)
    coverage = Column(String(50), index=True)
    signal_type = Column(String(100))

    success_count_24h = Column(Integer, nullable=False, default=0)
    error_count_24h = Column(Integer, nullable=False, default=0)
    avg_latency_ms = Column(Float)

    last_success_at = Column(DateTime(timezone=True))
    last_error_at = Column(DateTime(timezone=True))
    last_error_message = Column(Text)

    ttl_seconds = Column(Integer)
    data_freshness_score = Column(Float)  # 0-1

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MetricSnapshot(Base):
    """Periodic pipeline metric rollups for trend analysis (B-1)."""
    __tablename__ = "metric_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    snapshot_type = Column(String(20), nullable=False)  # hourly | daily
    captured_at = Column(DateTime(timezone=True), nullable=False)
    coverage = Column(String(50))
    metrics = Column(JSONB, nullable=False, default=dict)

