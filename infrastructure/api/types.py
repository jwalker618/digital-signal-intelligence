"""
DSI Production API Types (Phase 11)

Request and response models for the REST API.
Strictly aligned with infrastructure/db/models.py
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS (Strictly mapped to db/models.py)
# =============================================================================

class SubmissionStatus(str, Enum):
    """Submission processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QuoteStatus(str, Enum):
    """Quote status."""
    DRAFT = "draft"
    READY = "ready"
    BOUND = "bound"
    EXPIRED = "expired"
    DECLINED = "declined"


class DecisionType(str, Enum):
    """Workflow decision outcomes (From DB)."""
    APPROVE = "approve"
    REFER = "refer"
    DECLINE = "decline"


class ReferralStatus(str, Enum):
    """Referral review status (From DB)."""
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    DECLINED = "declined"
    MODIFIED = "modified"


class ReferralDecisionType(str, Enum):
    """Action taken by the underwriter in the request payload."""
    APPROVE = "approve"
    DECLINE = "decline"
    MODIFY = "modify"


class Permission(str, Enum):
    """API permissions."""
    SUBMIT = "submit"
    QUOTE = "quote"
    REFERRAL = "referral"
    ANALYTICS = "analytics"
    ADMIN = "admin"


# =============================================================================
# SUBMISSION MODELS
# =============================================================================

class SubmissionRequest(BaseModel):
    """Request to create a new submission."""
    entity_name: str = Field(..., description="Name of the entity to price")
    domain_hint: Optional[str] = Field(None, description="Optional domain hint for discovery")
    country_hint: Optional[str] = Field(None, description="Optional country/locale hint (e.g., US, UK, DE)")
    coverage: str = Field(..., description="Coverage type (e.g., fi, cyber, do)")
    configuration: Optional[str] = Field(None, description="Specific configuration to use")

    submission_data: Dict[str, Any] = Field(default_factory=dict, description="Traditional pricing inputs")
    direct_query_responses: Dict[str, Any] = Field(default_factory=dict, description="Pre-answered direct query responses")

    async_mode: bool = Field(False, description="Run asynchronously")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion")


class SubmissionResponse(BaseModel):
    """Response after creating a submission."""
    submission_id: str
    status: SubmissionStatus
    estimated_completion: Optional[datetime] = None
    job_id: Optional[str] = None


class SubmissionDetail(BaseModel):
    """Detailed submission information aligned with DB."""
    submission_id: str
    entity_name: str
    domain_hint: Optional[str] = None
    discovered_domain: Optional[str] = None
    country_hint: Optional[str] = None
    coverage: str
    configuration: Optional[str] = None
    status: SubmissionStatus
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    quote_id: Optional[str] = None


# =============================================================================
# QUOTE MODELS
# =============================================================================

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


class QuoteResponse(BaseModel):
    """Quote response with pricing details."""
    quote_id: str
    submission_id: str
    model_version_id: Optional[str] = None
    status: QuoteStatus

    # Scoring (sourced from model_version)
    composite_score: int
    tier: int
    tier_label: str
    decision: DecisionType 

    # Premium options
    premium_options: Dict[str, float] = Field(default_factory=dict)
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None

    # Pricing breakdown (sourced from model_version)
    base_premium: Optional[float] = None
    premium_after_modifiers: Optional[float] = None
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)

    # Three-pillar assessment summaries
    loss_propensity: Optional[LossPropensitySummary] = None
    exposure: Optional[ExposureSummary] = None

    # Details
    discovery: Optional[DiscoverySummary] = None
    signal_summary: Optional[SignalSummary] = None

    # Referral info (sourced from model_version)
    referral_reasons: List[str] = Field(default_factory=list)
    referral_id: Optional[str] = None

    # Validity
    valid_until: Optional[datetime] = None
    created_at: datetime


class QuoteListItem(BaseModel):
    """Quote in a list."""
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


# =============================================================================
# REFERRAL MODELS
# =============================================================================

class ReferralDecision(BaseModel):
    """Referral decision request payload."""
    decision: ReferralDecisionType
    adjustments: Optional[Dict[str, Any]] = None
    notes: List[str] = Field(default_factory=list)
    underwriter_id: Optional[str] = None


class ReferralDetail(BaseModel):
    """Referral information, strictly matching DB columns."""
    referral_id: str
    quote_id: str
    submission_id: str
    entity_name: str
    coverage: str

    # Status
    status: ReferralStatus
    reasons: List[str]

    # Original quote metadata
    original_tier: int
    original_score: int
    original_premium: float

    # Resolution (Aligned to DB fields)
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: List[str] = Field(default_factory=list)

    # Adjustments applied
    tier_override: Optional[int] = None
    premium_adjustment: Optional[float] = None

    created_at: datetime


class ReferralListItem(BaseModel):
    """Referral in a list."""
    referral_id: str
    entity_name: str
    coverage: str
    status: ReferralStatus
    reasons: List[str]
    age_hours: float
    created_at: datetime


# =============================================================================
# MULTI-COVERAGE MODELS
# =============================================================================

class MultiCoverageRequest(BaseModel):
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = Field(None, description="Optional country/locale hint (e.g., US, UK, DE)")
    coverages: Optional[List[str]] = Field(None, description="Coverages to price (None = auto)")
    locales: Optional[List[str]] = Field(None, description="Locales to test (None = auto)")
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


# =============================================================================
# ANALYTICS & JOB MODELS
# =============================================================================

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


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# AUTH & CONFIG MODELS
# =============================================================================

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


# =============================================================================
# PHASE 8: SIGNAL OVERRIDE MODELS
# =============================================================================

class SignalValue(BaseModel):
    signal_id: str
    inferred_value: float
    audited_value: Optional[float] = None
    is_overridden: bool = False
    confidence: float = 1.0

    @property
    def effective_value(self) -> float:
        return self.audited_value if self.is_overridden and self.audited_value is not None else self.inferred_value


class SignalOverrideRequest(BaseModel):
    signal_id: str
    audited_value: float
    rationale: str
    evidence_reference: Optional[str] = None
    underwriter_id: Optional[str] = None


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
    override_rationale: str  # Fixed to match DB
    evidence_reference: Optional[str] = None
    previous_model_version: str
    new_model_version: str


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


class ReferralSignalsRequest(BaseModel):
    include_all: bool = False
    include_raw_data: bool = False


class ReferralSignalDetail(BaseModel):
    signal_id: str
    signal_name: str
    group_id: str
    group_name: str
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

    # Configuration context: was this signal actually used by the model?
    in_model: bool = True                       # True if signal was used by this model version
    proxy_tier: Optional[str] = None            # DIRECT_OBSERVABLE / INFERRED_PROXY / COHORT_INFERENCE
    expectation_level: Optional[str] = None     # UNIVERSAL / ENTERPRISE / etc.
    was_absent: bool = False                    # Signal expected by config but not found
    used_audited_value: bool = False            # True if model used audited rather than inferred


class ReferralSignalsResponse(BaseModel):
    referral_id: str
    model_version_id: str
    configuration_name: Optional[str] = None    # Which config produced this model version
    coverage: Optional[str] = None              # Coverage type
    signals: List[ReferralSignalDetail]
    flagged_count: int
    overridden_count: int
    total_signals: int                          # Total signals in signal_cache for entity
    model_signal_count: int = 0                 # Signals actually used by this model version
    signal_coverage: float
    average_confidence: float


# =============================================================================
# SIMULATION TYPES (Phase 3)
# =============================================================================

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