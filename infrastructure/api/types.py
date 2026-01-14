"""
DSI Production API Types (Phase 11)

Request and response models for the REST API.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class SubmissionStatus(str, Enum):
    """Submission processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    DISCOVERY = "discovery"
    PRICING = "pricing"
    READY = "ready"
    REFERRED = "referred"
    FAILED = "failed"


class QuoteStatus(str, Enum):
    """Quote status."""
    PENDING = "pending"
    READY = "ready"
    REFERRED = "referred"
    EXPIRED = "expired"
    BOUND = "bound"
    DECLINED = "declined"


class ReferralDecisionType(str, Enum):
    """Referral decision types."""
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

    # Optional submission data
    submission_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Traditional pricing inputs (TIV, revenue, etc.)"
    )

    # Direct query responses
    direct_query_responses: Dict[str, Any] = Field(
        default_factory=dict,
        description="Pre-answered direct query responses"
    )

    # Options
    async_mode: bool = Field(False, description="Run asynchronously")
    callback_url: Optional[str] = Field(None, description="Webhook URL for completion")


class SubmissionResponse(BaseModel):
    """Response after creating a submission."""
    submission_id: str
    status: SubmissionStatus
    estimated_completion: Optional[datetime] = None
    job_id: Optional[str] = None


class SubmissionDetail(BaseModel):
    """Detailed submission information."""
    submission_id: str
    entity_name: str
    domain: Optional[str] = None
    coverage: str
    configuration: str
    status: SubmissionStatus
    created_at: datetime
    updated_at: datetime
    quote_id: Optional[str] = None
    error: Optional[str] = None


# =============================================================================
# QUOTE MODELS
# =============================================================================

class PremiumOption(BaseModel):
    """Premium option at a limit."""
    limit: float
    premium: float
    rate: float


class SignalSummary(BaseModel):
    """Summary of signal outputs."""
    total_signals: int
    signals_extracted: int
    top_factors: List[Dict[str, Any]]


class DiscoverySummary(BaseModel):
    """Discovery result summary."""
    domain: str
    confidence: str
    industry: Optional[str] = None
    employee_count: Optional[int] = None


class QuoteResponse(BaseModel):
    """Quote response with pricing details."""
    quote_id: str
    submission_id: str
    status: QuoteStatus

    # Scoring
    composite_score: int
    tier: int
    tier_label: str
    decision: str  # approve, refer, decline

    # Premium options
    premium_options: Dict[str, float] = Field(
        default_factory=dict,
        description="Premium by limit"
    )
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None

    # Details
    discovery: Optional[DiscoverySummary] = None
    signal_summary: Optional[SignalSummary] = None

    # Referral info
    referral_reasons: List[str] = Field(default_factory=list)
    referral_id: Optional[str] = None

    # Validity
    valid_until: Optional[datetime] = None
    created_at: datetime


class QuoteListItem(BaseModel):
    """Quote in a list."""
    quote_id: str
    submission_id: str
    entity_name: str
    coverage: str
    status: QuoteStatus
    tier: int
    premium: float
    created_at: datetime


# =============================================================================
# REFERRAL MODELS
# =============================================================================

class ReferralDecision(BaseModel):
    """Referral decision request."""
    decision: ReferralDecisionType
    adjustments: Optional[Dict[str, Any]] = None
    notes: List[str] = Field(default_factory=list)
    underwriter_id: Optional[str] = None


class ReferralDetail(BaseModel):
    """Referral information."""
    referral_id: str
    quote_id: str
    submission_id: str
    entity_name: str
    coverage: str

    # Status
    status: str  # pending, approved, declined
    reasons: List[str]

    # Original quote
    original_tier: int
    original_score: int
    original_premium: float

    # Resolution
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: List[str] = Field(default_factory=list)

    # Adjustments applied
    tier_override: Optional[int] = None
    premium_adjustment: Optional[float] = None

    created_at: datetime


class ReferralListItem(BaseModel):
    """Referral in a list."""
    referral_id: str
    entity_name: str
    coverage: str
    status: str
    reasons: List[str]
    age_hours: float
    created_at: datetime


# =============================================================================
# MULTI-COVERAGE MODELS
# =============================================================================

class MultiCoverageRequest(BaseModel):
    """Request for multi-coverage pricing."""
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = Field(None, description="Optional country/locale hint (e.g., US, UK, DE)")
    coverages: Optional[List[str]] = Field(None, description="Coverages to price (None = auto)")
    locales: Optional[List[str]] = Field(None, description="Locales to test (None = auto)")
    submission_data: Dict[str, Any] = Field(default_factory=dict)
    parallel: bool = True
    require_approval_above: int = 50


class MultiCoverageResponse(BaseModel):
    """Response for multi-coverage pricing."""
    result_id: str
    entity_name: str
    detected_locale: Optional[str] = None

    # Per-coverage results
    coverage_quotes: Dict[str, QuoteResponse] = Field(default_factory=dict)
    failed_coverages: List[str] = Field(default_factory=list)

    # Package info
    recommended_package: List[str] = Field(default_factory=list)
    package_discount: float = 0.0
    combined_premium: float = 0.0
    total_savings: float = 0.0

    # Metrics
    duration_seconds: float = 0.0
    cache_hit_rate: float = 0.0


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class PortfolioSummaryResponse(BaseModel):
    """Portfolio summary analytics."""
    as_of_date: datetime
    coverage: Optional[str] = None
    period: str

    # Volume
    total_submissions: int
    total_quotes: int
    total_binds: int
    total_declines: int

    # Premium
    gross_written_premium: float
    quoted_premium: float
    average_premium: float

    # Risk metrics
    average_score: float
    average_tier: float
    tier_distribution: Dict[int, int]

    # Rates
    quote_rate: float
    bind_rate: float
    decline_rate: float


class TurnaroundMetricsResponse(BaseModel):
    """Workflow turnaround metrics."""
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
    """Signal health metrics."""
    coverage: str
    period: str

    overall_coverage: float
    group_coverage: Dict[str, float]
    signal_coverage: Dict[str, float]

    issues: List[Dict[str, Any]]


# =============================================================================
# JOB MODELS
# =============================================================================

class JobStatus(str, Enum):
    """Async job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobResponse(BaseModel):
    """Async job status response."""
    job_id: str
    status: JobStatus
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# AUTH MODELS
# =============================================================================

class TokenRequest(BaseModel):
    """Token request."""
    username: str
    password: str


class TokenResponse(BaseModel):
    """Token response."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    permissions: List[str]


class APIKeyValidation(BaseModel):
    """API key validation result."""
    valid: bool
    client_id: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)
    rate_limit_tier: str = "standard"


# =============================================================================
# HEALTH & CONFIG MODELS
# =============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str] = Field(default_factory=dict)


class ConfigResponse(BaseModel):
    """Configuration response."""
    coverages: List[str]
    locales: List[str]
    rate_limits: Dict[str, int]
    features: Dict[str, bool]


# =============================================================================
# LIST/PAGINATION MODELS
# =============================================================================

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    page_size: int
    pages: int


class ListFilters(BaseModel):
    """Common list filters."""
    coverage: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = 1
    page_size: int = 20
