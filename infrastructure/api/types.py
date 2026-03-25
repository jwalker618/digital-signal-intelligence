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
    Signal, SignalSource, SignalCache, ModelVersionSignal, SignalAuditRecord, AuditLog,
    CommercialTermsRecord, RiskTermsRecord,
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

# --- *. FRONT END API Requests & Action Payloads ---
class FrontendSubmissionPipeline(BaseModel):
    submission_code: str
    quote_code: str
    referral_code: Optional[str] = None
    version_code: str
    entity_name: str
    coverage_configuration: str
    created_at: datetime
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None
    pure_composite_score: Optional[float] = None
    final_tier: Optional[int] = None
    tier_label: Optional[str] = None
    decision: str

class FrontendRiskAssessment(BaseModel):
    signal_id: int
    score: Optional[float] = None
    weight: Optional[float] = None
    group_weight: Optional[float] = None
    contribution: Optional[float] = None
    group_code: Optional[str] = None
    proxy_tier: Optional[str] = None
    expectation_level: Optional[str] = None
    was_absent: bool = False
    code: str

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
    signal_code: str
    audited_value: float
    rationale: str
    evidence_reference: Optional[str] = None
    underwriter_id: Optional[str] = None

class LimitSelectionRequest(BaseModel):
    """Request to select a limit option and create a new model version."""
    selected_limit: int = Field(description="The limit to select from the ROL options")
    rationale: Optional[str] = Field(None, description="Why this limit was selected")
    underwriter_id: Optional[str] = None

class LimitSelectionResponse(BaseModel):
    """Response after selecting a limit option."""
    quote_code: str
    new_version_code: str
    previous_version_code: str
    selected_limit: int
    selected_premium: float
    selected_rol: float
    decision: str
    message: str

class Note(BaseModel):
    note: str
    source: str

# --- B. Pricing & 3-Pillar Component Blocks (JSONB structures) ---
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
    exposure_size_score: Optional[float] = None
    exposure_modifier: Optional[float] = None

# --- C. Composite Read Models (Aggregated Responses) ---
class SubmissionResponse(BaseModel):
    submission_code: str
    status: SubmissionStatus
    estimated_completion: Optional[datetime] = None
    job_id: Optional[str] = None

class QuoteResponse(BaseModel):
    """Heavy projection combining Quote + ModelVersionRecord + JSONB components."""
    quote_code: str
    submission_code: str
    version_code: Optional[str] = None
    status: QuoteStatus
    composite_score: int
    tier: int
    tier_label: str
    decision: DecisionType
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None
    base_premium: Optional[float] = None
    base_premium_derivation: Optional[Dict[str, Any]] = None
    premium_after_modifiers: Optional[float] = None
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)
    loss_propensity: Optional[LossPropensitySummary] = None
    exposure: Optional[ExposureSummary] = None
    discovery: Optional[DiscoverySummary] = None
    signal_summary: Optional[SignalSummary] = None
    referral_reasons: List[str] = Field(default_factory=list)
    referral_code: Optional[str] = None
    valid_until: Optional[datetime] = None
    created_at: datetime

class QuoteListItem(BaseModel):
    quote_code: str
    submission_code: str
    version_code: Optional[str] = None
    entity_name: str
    coverage: str
    status: QuoteStatus
    tier: int
    premium: float
    decision: DecisionType
    created_at: datetime

class SignalOverrideResponse(BaseModel):
    signal_code: str
    entity_code: str
    version_code: str
    original_score: float
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
    previous_version_code: str
    new_version_code: str


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
    signal_code: str
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
    entity_code: str
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

class HealthResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    components: Dict[str, str] = Field(default_factory=dict)

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

@maps_to(Submission, exclude=["id", "processing_started_at", "processing_completed_at","processing_duration_ms", "created_by", "updated_at"])
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
    error_message: Optional[str] = None
    created_at: datetime

@maps_to(Quote, exclude=["id", "submission_id", "model_version_id", "created_at", "updated_at"])
class QuoteRecord(BaseModel):
    quote_code: str
    status: QuoteStatus
    recommended_premium: Optional[float] = None
    recommended_limit: Optional[float] = None
    valid_from: datetime
    valid_until: Optional[datetime] = None
    bound_at: Optional[datetime] = None
    bound_by: Optional[str] = None
    policy_number: Optional[str] = None

@maps_to(Referral, exclude=["id", "quote_id", "assigned_to", "assigned_at", "reviewed_by", "reviewed_at", "updated_at"])
class ReferralRecord(BaseModel):
    referral_code: str
    status: ReferralStatus
    reasons: List[str] = Field(default_factory=list)
    priority: int = 5
    review_decision: Optional[str] = None
    review_notes: Optional[str] = None
    tier_override: Optional[int] = None
    premium_adjustment: Optional[float] = None
    adjustments: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

## NOTE: MODEL VERSION HAS MULTIPLE TABLES TO LOGICALLY COHORT DATA
@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at"])
class ModelVersionDBRecord(BaseModel):
    version_code: str
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

    tier_margin_percentile: Optional[float] = None 
    tier_margin_tier_min: Optional[float] = None
    tier_margin_tier_max: Optional[float] = None
    tier_margin_distance_better: Optional[float] = None
    tier_margin_distance_worse: Optional[float] = None
    tier_margin_adjacent_better: Optional[float] = None
    tier_margin_adjacent_worse: Optional[float] = None
    tier_band_interpretation: Dict[str, Any] = Field(default_factory=dict)

    base_premium: Optional[float] = None
    base_premium_method: Optional[str] = None
    base_premium_derivation: Dict[str, Any] = Field(default_factory=dict)
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)
    premium_after_modifiers: Optional[float] = None
    final_premium: Optional[float] = None
    final_premium_detail: Dict[str, Any] = Field(default_factory=dict)
    uncapped_premium: Optional[float] = None

    guardrail_warnings: List[Note] = Field(default_factory=list)

    ilf_factor: Optional[float] = None
    ilf_method: Optional[str] = None
    ilf_anchor_limit: Optional[float] = None

    rol_upper_limit: Optional[float] = None
    rol_upper_premium: Optional[float] = None
    rol_upper_rol: Optional[float] = None
    rol_upper_rationale: Optional[str] = None
    rol_lower_limit: Optional[float] = None
    rol_lower_premium: Optional[float] = None
    rol_lower_rol: Optional[float] = None
    rol_lower_rationale: Optional[str] = None
    rol_structure_type: Optional[str] = None

    decision: Optional[DecisionType] = None
    auto_approve: bool = False
    referral_reasons: List[str] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)

    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    severity_propensity_band: Optional[str] = None
    loss_confidence: Optional[float] = None
    loss_cohort_code: Optional[str] = None
    loss_cohort_name: Optional[str] = None
    loss_cohort_confidence: Optional[float] = None

    loss_frequency_multiplier: Optional[float] = None
    loss_severity_multiplier: Optional[float] = None
    loss_combined_modifier: Optional[float] = None
    loss_group_scores: Dict[str, Any] = Field(default_factory=dict)
    loss_trend_direction: Optional[str] = None
    loss_frequency_trend_direction: Optional[str] = None
    loss_severity_trend_direction: Optional[str] = None
    loss_previous_score: Optional[float] = None
    loss_previous_frequency_score: Optional[float] = None
    loss_previous_severity_score: Optional[float] = None

    loss_score_velocity: Optional[float] = None
    loss_frequency_velocity: Optional[float] = None
    loss_severity_velocity: Optional[float] = None
    loss_last_refresh: Optional[datetime] = None
    correlation_matrix_version: Optional[str] = None
    loss_band_interpretation: Dict[str, Any] = Field(default_factory=dict)

    exposure_value: Optional[float] = None
    exposure_band_id: Optional[int] = None
    exposure_band_label: Optional[str] = None
    exposure_band_boundaries: Dict[str, Any] = Field(default_factory=dict)
    exposure_size_score: Optional[float] = None
    exposure_complexity_score: Optional[float] = None
    exposure_modifier: Optional[float] = None
    exposure_assessment_method: Optional[str] = None
    exposure_components: Dict[str, Any] = Field(default_factory=dict)
    exposure_band_interpretation: Dict[str, Any] = Field(default_factory=dict)

    # Config snapshots for client-side scenario recalculation
    loss_correlation_config: Dict[str, Any] = Field(default_factory=dict)
    ilf_curve_config: Dict[str, Any] = Field(default_factory=dict)
    deductible_factor_table: Dict[str, Any] = Field(default_factory=dict)
    exposure_modifier_config: Dict[str, Any] = Field(default_factory=dict)
    guardrails_config: Dict[str, Any] = Field(default_factory=dict)

@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at", "config_hash", 
                                        "discovery_output", "signal_outputs", "categorical_outputs", "group_scores",

                                        "referral_reasons", "notes",
                                        
                                        "loss_propensity_score", "severity_propensity_score", "loss_propensity_band", "severity_propensity_band",
                                        "loss_confidence", "loss_cohort_code", "loss_cohort_name", "loss_cohort_confidence", "loss_frequency_multiplier",
                                        "loss_severity_multiplier", "loss_combined_modifier", "loss_group_scores",
                                        "loss_trend_direction", "loss_frequency_trend_direction", "loss_severity_trend_direction",
                                        "loss_previous_score", "loss_previous_frequency_score", "loss_previous_severity_score",
                                        "loss_score_velocity", "loss_frequency_velocity", "loss_severity_velocity",
                                        "loss_last_refresh","correlation_matrix_version", 
                                        
                                        "exposure_value", "exposure_band_id", "exposure_band_label", "exposure_band_boundaries",
                                        "exposure_size_score", "exposure_modifier", "exposure_assessment_method",
                                      ])
class ModelVersionDBRecord_BaseOnly(BaseModel):
    version_code: str
    version_number: int
    version_type: Optional[str] = None
    is_latest: bool
    coverage: Optional[str] = None
    configuration_name: Optional[str] = None
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
    base_premium_derivation: Dict[str, Any] = Field(default_factory=dict)
    modifiers_applied: List[Dict[str, Any]] = Field(default_factory=list)
    premium_after_modifiers: Optional[float] = None
    final_premium: Optional[float] = None
    final_premium_detail: Dict[str, Any] = Field(default_factory=dict)
    uncapped_premium: Optional[float] = None
    ilf_factor: Optional[float] = None
    ilf_method: Optional[str] = None
    ilf_anchor_limit: Optional[float] = None
    decision: Optional[DecisionType] = None
    auto_approve: bool = False

@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at", "config_hash",
                                        "version_number", "version_type", "is_latest", "coverage", "configuration_name",
                                        "pure_composite_score", "confidence", "signal_coverage", "signal_conditions",
                                        "query_conditions", "tier_overrides", "score_based_tier", "final_tier", "tier_label",
                                        "base_premium", "base_premium_method", "modifiers_applied", "premium_after_modifiers",
                                        "limit_premiums", "final_premium", "final_premium_detail", "ilf_factor","ilf_method","ilf_anchor_limit",
                                        "decision","auto_approve", "base_premium_derivation",
   
                                        "referral_reasons", "notes",
                                        
                                        "loss_propensity_score", "severity_propensity_score", "loss_propensity_band", "severity_propensity_band",
                                        "loss_confidence", "loss_cohort_code", "loss_cohort_name", "loss_cohort_confidence", "loss_frequency_multiplier",
                                        "loss_severity_multiplier", "loss_combined_modifier", "loss_group_scores",
                                        "loss_trend_direction", "loss_frequency_trend_direction", "loss_severity_trend_direction",
                                        "loss_previous_score", "loss_previous_frequency_score", "loss_previous_severity_score",
                                        "loss_score_velocity", "loss_frequency_velocity", "loss_severity_velocity",
                                        "loss_last_refresh","correlation_matrix_version",  
                                        
                                        "exposure_value", "exposure_band_id", "exposure_band_label", "exposure_band_boundaries",
                                        "exposure_size_score", "exposure_modifier", "exposure_assessment_method",
                                        ])
class ModelVersionDBRecord_DetailOnly(BaseModel):
    version_code: str
    discovery_output: Optional[Dict[str, Any]] = None
    signal_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    categorical_outputs: List[Dict[str, Any]] = Field(default_factory=list)
    group_scores: Dict[str, Any] = Field(default_factory=dict)

@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at", "config_hash", 
                                        "version_number", "version_type", "is_latest", "coverage", "configuration_name",
                                        "pure_composite_score", "confidence", "signal_coverage", "signal_conditions",
                                        "query_conditions", "tier_overrides", "score_based_tier", "final_tier", "tier_label",
                                        "base_premium", "base_premium_method", "modifiers_applied", "premium_after_modifiers",
                                        "limit_premiums", "final_premium", "final_premium_detail", "ilf_factor","ilf_method","ilf_anchor_limit",
                                        "decision","auto_approve", "base_premium_derivation",

                                        "discovery_output", "signal_outputs", "categorical_outputs", "group_scores",
                                        
                                        "loss_propensity_score", "severity_propensity_score", "loss_propensity_band", "severity_propensity_band",
                                        "loss_confidence", "loss_cohort_code", "loss_cohort_name", "loss_cohort_confidence", "loss_frequency_multiplier",
                                        "loss_severity_multiplier", "loss_combined_modifier", "loss_group_scores",
                                        "loss_trend_direction", "loss_frequency_trend_direction", "loss_severity_trend_direction",
                                        "loss_previous_score", "loss_previous_frequency_score", "loss_previous_severity_score",
                                        "loss_score_velocity", "loss_frequency_velocity", "loss_severity_velocity",
                                        "loss_last_refresh","correlation_matrix_version", 
                                        
                                        "exposure_value", "exposure_band_id", "exposure_band_label", "exposure_band_boundaries",
                                        "exposure_size_score", "exposure_modifier", "exposure_assessment_method",
                                      ])
class ModelVersionDBRecord_CommentaryOnly(BaseModel):
    version_code: str 
    referral_reasons: List[str] = Field(default_factory=list)
    notes: List[Note] = Field(default_factory=list)

@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at", "config_hash", 
                                        "version_number", "version_type", "is_latest", "coverage", "configuration_name",
                                        "pure_composite_score", "confidence", "signal_coverage", "signal_conditions",
                                        "query_conditions", "tier_overrides", "score_based_tier", "final_tier", "tier_label",
                                        "base_premium", "base_premium_method", "modifiers_applied", "premium_after_modifiers",
                                        "limit_premiums", "final_premium", "final_premium_detail", "ilf_factor","ilf_method","ilf_anchor_limit",
                                        "decision","auto_approve", "base_premium_derivation",

                                        "discovery_output", "signal_outputs", "categorical_outputs", "group_scores",

                                        "referral_reasons", "notes",
                                
                                        "exposure_value", "exposure_band_id", "exposure_band_label", "exposure_band_boundaries",
                                        "exposure_size_score", "exposure_modifier", "exposure_assessment_method",
                                      ])
class ModelVersionDBRecord_LossOnly(BaseModel):
    version_code: str 
    loss_propensity_score: Optional[float] = None
    severity_propensity_score: Optional[float] = None
    loss_propensity_band: Optional[str] = None
    severity_propensity_band: Optional[str] = None
    loss_confidence: Optional[float] = None
    loss_cohort_code: Optional[str] = None
    loss_cohort_name: Optional[str] = None
    loss_cohort_confidence: Optional[float] = None
    loss_frequency_multiplier: Optional[float] = None
    loss_severity_multiplier: Optional[float] = None
    loss_combined_modifier: Optional[float] = None
    loss_group_scores: Dict[str, Any] = Field(default_factory=dict)
    loss_trend_direction: Optional[str] = None
    loss_frequency_trend_direction: Optional[str] = None
    loss_severity_trend_direction: Optional[str] = None
    loss_previous_score: Optional[float] = None
    loss_previous_frequency_score: Optional[float] = None
    loss_previous_severity_score: Optional[float] = None
    loss_score_velocity: Optional[float] = None
    loss_frequency_velocity: Optional[float] = None
    loss_severity_velocity: Optional[float] = None
    loss_last_refresh: Optional[datetime] = None
    correlation_matrix_version: Optional[str] = None

@maps_to(ModelVersionRecord, exclude=["id", "submission_id", "created_by", "created_at", "config_hash", 
                                        "version_number", "version_type", "is_latest", "coverage", "configuration_name",
                                        "pure_composite_score", "confidence", "signal_coverage", "signal_conditions",
                                        "query_conditions", "tier_overrides", "score_based_tier", "final_tier", "tier_label",
                                        "base_premium", "base_premium_method", "modifiers_applied", "premium_after_modifiers",
                                        "limit_premiums", "final_premium", "final_premium_detail", "ilf_factor","ilf_method","ilf_anchor_limit",
                                        "decision","auto_approve", "base_premium_derivation",

                                        "discovery_output", "signal_outputs", "categorical_outputs", "group_scores",

                                        "referral_reasons", "notes",
                                        
                                        "loss_propensity_score", "severity_propensity_score", "loss_propensity_band", "severity_propensity_band",
                                        "loss_confidence", "loss_cohort_code", "loss_cohort_name", "loss_cohort_confidence", "loss_frequency_multiplier",
                                        "loss_severity_multiplier", "loss_combined_modifier", "loss_group_scores",
                                        "loss_trend_direction", "loss_frequency_trend_direction", "loss_severity_trend_direction",
                                        "loss_previous_score", "loss_previous_frequency_score", "loss_previous_severity_score",
                                        "loss_score_velocity", "loss_frequency_velocity", "loss_severity_velocity",
                                        "loss_last_refresh","correlation_matrix_version", 
                                      ])
class ModelVersionDBRecord_ExposureOnly(BaseModel):
    version_code: str
    exposure_value: Optional[float] = None
    exposure_band_id: Optional[int] = None
    exposure_band_label: Optional[str] = None
    exposure_band_boundaries: Dict[str, Any] = Field(default_factory=dict)
    exposure_size_score: Optional[float] = None
    exposure_modifier: Optional[float] = None
    exposure_assessment_method: Optional[str] = None

@maps_to(SignalCache, exclude=["id"])
class SignalCacheRecord(BaseModel):
    entity_code: str
    signal_id: int
    source_id: int
    data: Dict[str, Any]
    confidence: Optional[float] = None
    extracted_at: datetime
    expires_at: datetime
    ttl_seconds: Optional[int] = None
    extraction_time_ms: Optional[float] = None
    from_external_cache: bool = False

maps_to(Signal, exclude=["id"])
class SignalRecord(BaseModel):
    code: str

@maps_to(ModelVersionSignal, exclude=["id"])
class ModelVersionSignalRecord(BaseModel):
    model_version_id: str
    signal_cache_id: str
    signal_id: int
    entity_code: str
    score: Optional[float] = None
    weight: Optional[float] = None
    group_weight: Optional[float] = None
    contribution: Optional[float] = None
    group_code: Optional[str] = None
    proxy_tier: Optional[str] = None
    expectation_level: Optional[str] = None
    was_absent: bool = False
    created_at: datetime

@maps_to(SignalAuditRecord, exclude=["id"])
class SignalAuditDBRecord(BaseModel):
    model_version_signal_id: str
    audited_value: float
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


# =============================================================================
# COMMERCIAL TERMS
# =============================================================================

@maps_to(CommercialTermsRecord, exclude=["id", "offered_premium_set_by"])
class CommercialTermsDBRecord(BaseModel):
    """Full commercial terms projection for API responses."""
    model_version_id: str
    entity_id: str
    entity_name: Optional[str] = None
    entity_market: Optional[str] = None
    base_currency: str = "USD"
    fx_rate_to_usd: Optional[float] = None
    fx_rate_source: Optional[str] = None
    fx_rate_date: Optional[datetime] = None
    technical_premium_usd: Optional[float] = None
    technical_premium_local: Optional[float] = None
    distribution_type: Optional[str] = None
    signed_line: Optional[float] = None
    role: Optional[str] = None
    lead_loading_factor: Optional[float] = 1.0
    net_premium: Optional[float] = None
    deductions: Dict[str, Any] = Field(default_factory=dict)
    total_commission: Optional[float] = None
    taxes_and_levies: Dict[str, Any] = Field(default_factory=dict)
    total_taxes: Optional[float] = None
    gross_premium: Optional[float] = None
    offered_premium: Optional[float] = None
    offered_premium_discretion: Optional[float] = None
    offered_premium_rationale: Optional[str] = None
    offered_premium_set_at: Optional[datetime] = None
    minimum_gross_premium: Optional[float] = None
    at_minimum_premium: bool = False
    written_date: Optional[datetime] = None
    earned_start: Optional[datetime] = None
    earned_end: Optional[datetime] = None
    earned_method: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class OfferedPremiumRequest(BaseModel):
    """Request to set/update the offered premium on commercial terms."""
    offered_premium: float = Field(gt=0, description="Offered premium amount")
    offered_premium_rationale: Optional[str] = Field(
        default=None, description="Rationale for the premium adjustment"
    )


class OfferedPremiumResponse(BaseModel):
    """Response after setting offered premium."""
    commercial_terms_id: str
    offered_premium: float
    offered_premium_discretion: float
    gross_premium: float
    offered_premium_rationale: Optional[str] = None
    offered_premium_set_at: datetime


class EarnedPeriodRequest(BaseModel):
    """Request to set the earned period on commercial terms."""
    written_date: Optional[datetime] = None
    earned_start: datetime
    earned_end: datetime
    earned_method: str = Field(
        default="pro_rata",
        description="Earning method: pro_rata, risks_attaching, losses_occurring"
    )


@maps_to(RiskTermsRecord, exclude=["id", "commercial_terms_id"])
class RiskTermsDBRecord(BaseModel):
    """Risk terms projection for API responses."""
    deductible_type: Optional[str] = None
    deductible_amount: Optional[float] = None
    deductible_currency: str = "USD"
    deductible_basis: Optional[str] = None
    sir_amount: Optional[float] = None
    sir_applies: bool = False
    waiting_period_hours: Optional[float] = None
    waiting_period_type: Optional[str] = None
    aggregate_limit: Optional[float] = None
    aggregate_deductible: Optional[float] = None
    aggregate_basis: Optional[str] = None
    reinstatements: Optional[int] = None
    reinstatement_rate: Optional[float] = None
    attachment_point: Optional[float] = None
    layer_limit: Optional[float] = None
    sub_limits: list = Field(default_factory=list)
    coverage_terms: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None