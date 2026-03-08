"""
DSI Production API Types (Phase 11)

Request and response models for the REST API.
Divided strictly into Bespoke API Projections and Aligned ORM DTOs.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Type
from pydantic import BaseModel, Field

# Import ORM models for alignment mapping
from infrastructure.db.models import (
    User, APIKey, Submission, Quote, Referral, ModelVersionRecord, 
    SignalCache, ModelVersionSignal, SignalAuditRecord, AuditLog
)

def maps_to(orm_model: Type, exclude: List[str] = None):
    """
    Decorator to explicitly link a Pydantic DTO to an ORM model.
    'exclude' documents fields intentionally hidden from the API payload (e.g. raw UUIDs, passwords).
    """
    def decorator(cls):
        cls.__orm_model__ = orm_model
        cls.__orm_exclude__ = exclude or []
        
        if hasattr(cls, "model_config"):
            cls.model_config["from_attributes"] = True  # Pydantic v2
        else:
            cls.Config.orm_mode = True  # Pydantic v1 fallback
        return cls
    return decorator


# =============================================================================
# SHARED ENUMERATIONS
# =============================================================================

class SubmissionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"

class QuoteStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    BOUND = "bound"
    EXPIRED = "expired"
    DECLINED = "declined"

class DecisionType(str, Enum):
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"

class ReferralStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DECLINED = "declined"
    MODIFIED = "modified"

class ReferralDecisionType(str, Enum):
    APPROVE = "approve"
    DECLINE = "decline"
    MODIFY = "modify"

class Permission(str, Enum):
    SUBMIT = "submit"
    QUOTE = "quote"
    REFERRAL = "referral"
    ANALYTICS = "analytics"
    ADMIN = "admin"

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# PART 1: BESPOKE API MODELS & PROJECTIONS
# These models do NOT map 1:1 to a database table. They are aggregated read 
# models, JSONB nested structures, or specific request payloads.
# =============================================================================

# --- A. API Requests & Action Payloads ---
class SubmissionRequest(BaseModel):
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = None
    coverage: str
    configuration: Optional[str] = None
    submission_data: Dict[str, Any] = Field(default_factory=dict)
    direct_query_responses: Dict[str, Any] = Field(default_factory=dict)
    async_mode: bool = False
    callback_url: Optional[str] = None

class ReferralDecision(BaseModel):
    decision: ReferralDecisionType
    adjustments: Optional[Dict[str, Any]] = None
    notes: List[str] = Field(default_factory=list)
    underwriter_id: Optional[str] = None

class SignalOverrideRequest(BaseModel):
    signal_cache_id: str  
    signal_id: str
    audited_value: float
    rationale: str
    evidence_reference: Optional[str] = None
    underwriter_id: Optional[str] = None

# --- B. Pricing & 3-Pillar Component Blocks (JSONB structures) ---
class PremiumOption(BaseModel):
    limit: float
    premium: float
    rate: float

class SignalSummary(BaseModel):
    total_signals: int
    signals_extracted: int
    top_factors: List[Dict[str, Any]]

class DiscoverySummary(BaseModel):
    domain: str
    confidence: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None

class LossPropensitySummary(BaseModel):
    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    severity_propensity_band: Optional[str] = None
    loss_confidence: Optional[float] = None
    loss_combined_modifier: Optional[float] = None
    loss_cohort_name: Optional[str] = None
    loss_trend_direction: Optional[str] = None

class ExposureSummary(BaseModel):
    exposure_value: Optional[float] = None
    exposure_band_label: Optional[str] = None
    exposure_magnitude_score: Optional[float] = None
    exposure_modifier: Optional[float] = None

class SignalValue(BaseModel):
    signal_id: str
    inferred_value: float
    audited_value: Optional[float] = None
    is_overridden: bool = False
    confidence: float = 1.0

    @property
    def effective_value(self) -> float:
        return self.audited_value if self.is_overridden and self.audited_value is not None else self.inferred_value


# --- C. Composite Read Models (Aggregated Responses) ---
class SubmissionResponse(BaseModel):
    submission_id: str
    status: SubmissionStatus
    estimated_completion: Optional[datetime] = None
    job_id: Optional[str] = None

class QuoteResponse(BaseModel):
    """Heavy projection combining Quote + ModelVersionRecord + JSONB components."""
    quote_id: str
    submission_id: str
    model_version_id: Optional[str] = None
    status: QuoteStatus
    composite_score: int
    tier: int
    tier_label: str
    decision: DecisionType 
    premium_options: Dict[str, float] = Field(default_factory=dict)
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None
    base_premium: Optional[float] = None
    premium_after_modifiers: Optional[float] = None
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)
    loss_propensity: Optional[LossPropensitySummary] = None
    exposure: Optional[ExposureSummary] = None
    discovery: Optional[DiscoverySummary] = None
    signal_summary: Optional[SignalSummary] = None
    referral_reasons: List[str] = Field(default_factory=list)
    referral_id: Optional[str] = None
    valid_until: Optional[datetime] = None
    created_at: datetime

class QuoteListItem(BaseModel):
    quote_id: str
    submission_id: str
    model_version_id: Optional[str] = None
    entity_name: str
    coverage: str
    status: QuoteStatus
    tier: int
    premium: float
    decision: DecisionType
    created_at: datetime

class ReferralListItem(BaseModel):
    referral_id: str
    entity_name: str
    coverage: str
    status: ReferralStatus
    reasons: List[str]
    age_hours: float
    created_at: datetime

class ModelVersionResponse(BaseModel):
    version_id: str
    version_number: int
    version_type: str
    composite_score: float
    tier: int
    tier_label: str
    confidence: float
    signal_count: int
    overridden_signals: List[str] = Field(default_factory=list)
    created_by: str
    created_at: datetime
    notes: List[str] = Field(default_factory=list)

class ReferralSignalDetail(BaseModel):
    """Projection joining Bridge -> Cache -> Audit tables."""
    signal_cache_id: str
    signal_id: str
    signal_name: str
    group_id: str
    group_name: str
    score: float
    inferred_value: float
    audited_value: Optional[float] = None
    is_overridden: bool = False
    weight: float
    contribution_to_score: float
    is_flagged: bool = False
    flag_reason: Optional[str] = None
    confidence: float
    data_sources: List[str] = Field(default_factory=list)
    extracted_at: datetime
    raw_data: Optional[Dict[str, Any]] = None
    in_model: bool = True                       
    proxy_tier: Optional[str] = None            
    expectation_level: Optional[str] = None     
    was_absent: bool = False                    
    used_audited_value: bool = False            
    override_rationale: Optional[str] = None
    evidence_reference: Optional[str] = None
    score_impact: Optional[float] = None
    tier_impact: Optional[int] = None

class ReferralSignalsResponse(BaseModel):
    referral_id: Optional[str] = None
    model_version_id: str
    configuration_name: Optional[str] = None
    coverage: Optional[str] = None
    signals: List[ReferralSignalDetail]
    flagged_count: int
    overridden_count: int
    total_signals: int
    model_signal_count: int = 0
    signal_coverage: float
    average_confidence: float

class SignalOverrideResponse(BaseModel):
    signal_id: str
    entity_id: str
    model_version_id: str
    inferred_value: float
    audited_value: float
    score_impact: float
    tier_impact: int
    new_composite_score: float
    new_tier: int
    new_tier_label: str
    overridden_by: str
    overridden_at: datetime
    override_rationale: str
    evidence_reference: Optional[str] = None
    previous_model_version: str
    new_model_version: str


# --- D. Multi-Coverage (Phase 11) ---
class MultiCoverageRequest(BaseModel):
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = None
    coverages: Optional[List[str]] = None
    locales: Optional[List[str]] = None
    submission_data: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = True
    require_approval_above: int = 50

class MultiCoverageResponse(BaseModel):
    result_id: str
    entity_name: str
    detected_locale: Optional[str] = None
    coverage_quotes: Dict[str, QuoteResponse] = Field(default_factory=dict)
    failed_coverages: List[str] = Field(default_factory=list)
    recommended_package: List[str] = Field(default_factory=list)
    package_discount: float = 0.0
    combined_premium: float = 0.0
    total_savings: float = 0.0
    duration_seconds: float = 0.0
    cache_hit_rate: float = 0.0


# --- E. Analytics & Dashboards ---
class PortfolioSummaryResponse(BaseModel):
    as_of_date: datetime
    coverage: Optional[str] = None
    period: str
    total_submissions: int
    total_quotes: int
    total_binds: int
    total_declines: int
    gross_written_premium: float
    quoted_premium: float
    average_premium: float
    average_score: float
    average_tier: float
    tier_distribution: Dict[int, int]
    quote_rate: float
    bind_rate: float
    decline_rate: float

class TurnaroundMetricsResponse(BaseModel):
    period: str
    sample_size: int
    avg_time_to_quote: float
    avg_time_to_decision: float
    p50_time_to_quote: float
    p90_time_to_quote: float
    p95_time_to_quote: float
    sla_target_hours: float
    sla_compliance_rate: float
    time_by_tier: Dict[int, float]

class SignalHealthResponse(BaseModel):
    coverage: str
    period: str
    overall_coverage: float
    group_coverage: Dict[str, float]
    signal_coverage: Dict[str, float]
    issues: List[Dict[str, Any]]


# --- F. Simulation Engine (Phase 3) ---
class ShockParameterRequest(BaseModel):
    signal_id: str
    shock_type: str = "multiplier"
    value: float
    industry_filter: Optional[str] = None
    tier_filter: Optional[int] = None
    coverage_filter: Optional[str] = None

class SimulateRequest(BaseModel):
    portfolio_json: str
    shocks: List[ShockParameterRequest]
    config_path: Optional[str] = None
    iterations: int = 1

class TierMigration(BaseModel):
    entity_id: str
    old_tier: int
    new_tier: int

class SimulationStats(BaseModel):
    mean_score_delta: float
    std_score_delta: float
    entities_upgraded: int
    entities_downgraded: int
    max_premium_increase_pct: float = 0.0
    max_premium_decrease_pct: float = 0.0

class SimulateResponse(BaseModel):
    simulation_id: str
    status: str = "completed"
    premium_adequacy: float
    total_premium_impact: float
    entities_affected: int
    total_entities: int
    tier_migrations: List[TierMigration] = Field(default_factory=list)
    stats: SimulationStats
    execution_time_ms: float
    created_at: datetime


# --- G. System, Auth & Jobs ---
class TokenRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    permissions: List[str]

class APIKeyValidation(BaseModel):
    valid: bool
    client_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    rate_limit_tier: str = "standard"

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str] = Field(default_factory=dict)

class ConfigResponse(BaseModel):
    coverages: List[str]
    locales: List[str]
    rate_limits: Dict[str, int]
    features: Dict[str, bool]

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int

class ListFilters(BaseModel):
    coverage: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20

class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# PART 2: ALIGNED ORM DTOs
# These models strictly map 1:1 to their underlying database tables. 
# Internal Postgres UUIDs (id) and sensitive raw foreign keys are excluded 
# by design to prevent data leaks.
# =============================================================================

@maps_to(User, exclude=["id", "hashed_password"])
class UserRecord(BaseModel):
    email: str
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    permissions: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

@maps_to(APIKey, exclude=["id", "user_id", "key_hash"])
class APIKeyRecord(BaseModel):
    key_prefix: str
    name: str
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None

@maps_to(Submission, exclude=["id"])
class SubmissionRecord(BaseModel):
    submission_code: str
    entity_name: str
    domain_hint: Optional[str] = None
    discovered_domain: Optional[str] = None
    country_hint: Optional[str] = None
    coverage: str
    configuration: Optional[str] = None
    locale: str = "US"
    status: SubmissionStatus
    submission_data: Dict[str, Any] = Field(default_factory=dict)
    direct_query_responses: Dict[str, Any] = Field(default_factory=dict)
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
    processing_duration_ms: Optional[float] = None
    error_message: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None

@maps_to(Quote, exclude=["id"])
class QuoteRecord(BaseModel):
    quote_code: str
    submission_id: str
    model_version_id: str
    status: QuoteStatus
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None
    premium_options: Dict[str, Any] = Field(default_factory=dict)
    valid_from: datetime
    valid_until: Optional[datetime] = None
    bound_at: Optional[datetime] = None
    bound_by: Optional[str] = None
    policy_number: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

@maps_to(Referral, exclude=["id"])
class ReferralRecord(BaseModel):
    referral_code: str
    quote_id: str
    status: ReferralStatus
    reasons: List[str] = Field(default_factory=list)
    priority: int = 5
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    tier_override: Optional[int] = None
    premium_adjustment: Optional[float] = None
    adjustments: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None

@maps_to(ModelVersionRecord, exclude=["id"])
class ModelVersionDBRecord(BaseModel):
    version_code: str
    submission_id: str
    version_number: int
    version_type: Optional[str] = None
    is_latest: bool
    config_hash: Optional[str] = None
    coverage: Optional[str] = None
    configuration_name: Optional[str] = None
    discovery_output: Optional[Dict[str, Any]] = None
    signal_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    categorical_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    group_scores: Dict[str, Any] = Field(default_factory=dict)
    pure_composite_score: Optional[float] = None
    confidence: Optional[float] = None
    signal_coverage: Optional[float] = None
    signal_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    query_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    tier_overrides: List[Dict[str, Any]] = Field(default_factory=list)
    score_based_tier: Optional[int] = None
    final_tier: Optional[int] = None
    tier_label: Optional[str] = None
    base_premium: Optional[float] = None
    base_premium_method: Optional[str] = None
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)
    premium_after_modifiers: Optional[float] = None
    limit_premiums: Dict[str, Any] = Field(default_factory=dict)
    final_premium: Optional[float] = None
    decision: Optional[DecisionType] = None
    auto_approve: bool = False
    referral_reasons: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    severity_propensity_band: Optional[str] = None
    loss_confidence: Optional[float] = None
    loss_cohort_id: Optional[str] = None
    loss_cohort_name: Optional[str] = None
    loss_cohort_confidence: Optional[float] = None
    loss_frequency_multiplier: Optional[float] = None
    loss_severity_multiplier: Optional[float] = None
    loss_combined_modifier: Optional[float] = None
    loss_trend_direction: Optional[str] = None
    loss_previous_score: Optional[float] = None
    loss_score_velocity: Optional[float] = None
    loss_last_refresh: Optional[datetime] = None
    correlation_matrix_version: Optional[str] = None
    exposure_value: Optional[float] = None
    exposure_band_id: Optional[int] = None
    exposure_band_label: Optional[str] = None
    exposure_magnitude_score: Optional[float] = None
    exposure_modifier: Optional[float] = None
    exposure_assessment_method: Optional[str] = None
    created_by: str
    created_at: datetime

@maps_to(SignalCache, exclude=["id"])
class SignalCacheRecord(BaseModel):
    entity_code: str
    signal_code: str
    source_name: str
    data: Dict[str, Any]
    confidence: Optional[float] = None
    extracted_at: datetime
    expires_at: datetime
    ttl_seconds: Optional[int] = None
    extraction_time_ms: Optional[float] = None
    from_external_cache: bool = False
    inferred_value: Optional[Dict[str, Any]] = None
    audited_value: Optional[Dict[str, Any]] = None
    is_overridden: bool = False
    audit_trail: List[Dict[str, Any]] = Field(default_factory=list)

@maps_to(ModelVersionSignal, exclude=["id"])
class ModelVersionSignalRecord(BaseModel):
    model_version_id: str
    signal_cache_id: str
    signal_code: str
    entity_code: str
    score: Optional[float] = None
    weight: Optional[float] = None
    contribution: Optional[float] = None
    group_code: Optional[str] = None
    proxy_tier: Optional[str] = None
    expectation_level: Optional[str] = None
    was_absent: bool = False
    used_audited_value: bool = False
    created_at: datetime

@maps_to(SignalAuditRecord, exclude=["id"])
class SignalAuditDBRecord(BaseModel):
    signal_cache_id: str
    model_version_id: str
    signal_code: str
    entity_code: str
    inferred_value: Dict[str, Any]
    audited_value: Optional[Dict[str, Any]] = None
    is_overridden: bool = False
    overridden_by: Optional[str] = None
    overridden_at: Optional[datetime] = None
    override_rationale: Optional[str] = None
    evidence_reference: Optional[str] = None
    score_impact: Optional[float] = None
    tier_impact: Optional[int] = None
    created_at: datetime

@maps_to(AuditLog, exclude=["id", "user_id", "api_key_id"])
class AuditLogRecord(BaseModel):
    event_type: str
    event_action: str
    resource_type: Optional[str] = None
    resource_code: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime