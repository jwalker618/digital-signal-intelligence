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
    
    __table_args__ = (
        Index("ix_submissions_entity_coverage", "entity_name", "coverage"),
        Index("ix_submissions_created_at", "created_at"),
    )


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

    # =========================================================================
    # TIER BAND CONFIG SNAPSHOT (Phase A — rich config context)
    # =========================================================================
    tier_band_interpretation = Column(JSONB)          # Full tier band config: {action, bands, application, label}

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
    notes = Column(JSONB, default=list)

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
    correlation_matrix_version = Column(String(100))
    loss_band_interpretation = Column(JSONB)          # Full loss tier band config snapshot: {bands, constraints, frequency_modifier, severity_modifier}

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
    exposure_assessment_method = Column(String(50))   # config_band_lookup, signal_composite, etc.
    exposure_components = Column(JSONB)                # {size_factor, growth_factor, concentration_factor, ...}
    exposure_band_interpretation = Column(JSONB)       # Full exposure config snapshot: {size_bands, complexity_bands, weights}

    # =========================================================================
    # CONFIG SNAPSHOTS — for full client-side scenario recalculation
    # =========================================================================
    loss_correlation_config = Column(JSONB)    # Loss correlation groups, weights, band thresholds, multiplier maps
    ilf_curve_config = Column(JSONB)           # ILF curve type, params (q/b/alpha/k), anchor limit
    deductible_factor_table = Column(JSONB)    # {product_type: [{deductible, factor}, ...]}
    exposure_modifier_config = Column(JSONB)   # Size curve, growth/concentration thresholds
    guardrails_config = Column(JSONB)          # modifier_floor, modifier_cap, premium ratio caps

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
    """Audit log for compliance and debugging."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event info
    event_type = Column(String(100), nullable=False, index=True)
    event_action = Column(String(100), nullable=False)

    # Resource
    resource_type = Column(String(100))
    resource_code = Column(String(100))

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
        Index("ix_audit_logs_resource", "resource_type", "resource_code"),
        Index("ix_audit_logs_user", "user_id", "created_at"),
    )


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
    commercial_terms_id = Column(
        UUID(as_uuid=True),
        ForeignKey("commercial_terms.id"),
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
    commercial_terms = relationship("CommercialTermsRecord", backref="risk_terms")
