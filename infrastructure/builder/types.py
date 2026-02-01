"""
DSI Coverage Builder Types (Phase 13 → v2.0 Overhaul)

Data structures for coverage building aligned with v2.0 config schema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class BuildStage(str, Enum):
    """Coverage building stages."""
    ANALYSIS = "analysis"
    SIGNAL_SELECTION = "signal_selection"
    CONFIG_GENERATION = "config_generation"
    VALIDATION = "validation"
    CODE_GENERATION = "code_generation"
    COMPLETE = "complete"


class ValidationSeverity(str, Enum):
    """Validation issue severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ProxyTier(str, Enum):
    """Signal proxy tier classification."""
    DIRECT_OBSERVABLE = "DIRECT_OBSERVABLE"
    INFERRED_PROXY = "INFERRED_PROXY"
    COHORT_INFERENCE = "COHORT_INFERENCE"


@dataclass
class CoverageSpec:
    """Input specification for new coverage."""
    name: str
    description: str
    industry: str
    target_market: str  # "US mid-market", "Global enterprise", etc.
    risk_factors: List[str] = field(default_factory=list)
    example_companies: List[str] = field(default_factory=list)
    base_coverage: Optional[str] = None  # Extend from existing
    notes: Optional[str] = None

    # Product configuration
    product_types: List[str] = field(default_factory=list)
    applicable_markets: List[str] = field(default_factory=lambda: ["us"])
    min_premium: int = 5000
    default_currency: str = "USD"

    # Advanced options
    locale: str = "US"
    tier_strategy: str = "standard"  # standard, conservative, aggressive
    min_signals: int = 15
    max_signals: int = 40


@dataclass
class IndustryAnalysis:
    """Result of industry analysis."""
    industry: str
    key_risk_factors: List[str]
    relevant_categories: List[str]
    specific_considerations: List[str]
    regulatory_requirements: List[str] = field(default_factory=list)
    data_availability: Dict[str, str] = field(default_factory=dict)
    confidence: float = 0.8


@dataclass
class SignalRecommendation:
    """Recommendation for a signal."""
    signal_id: str
    signal_name: str
    group_id: str
    relevance_score: float  # 0-1
    suggested_weight: float
    proxy_tier: str = "INFERRED_PROXY"
    customization_notes: Optional[str] = None
    requires_new_implementation: bool = False


@dataclass
class SignalSelection:
    """Selected signal with configuration for v2.0 signal_registry."""
    signal_id: str
    signal_name: str
    group_id: str
    weight: float
    direction: str = "positive"  # positive, negative
    proxy_tier: str = "INFERRED_PROXY"
    inference_function: Optional[str] = None
    is_categorical: bool = False
    categories: Optional[List[Dict[str, Any]]] = None
    enabled: bool = True
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SignalTemplate:
    """Template for signal implementation."""
    signal_id: str
    signal_name: str
    description: str
    extractor_template: str
    aggregator_template: str
    inference_template: str
    test_template: str
    dependencies: List[str] = field(default_factory=list)


@dataclass
class ValidationIssue:
    """Validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    path: Optional[str] = None
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of configuration validation."""
    valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    test_results: Dict[str, bool] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)


@dataclass
class GeneratedCode:
    """Generated code files."""
    files: Dict[str, str] = field(default_factory=dict)  # path -> content
    entry_point: Optional[str] = None
    test_files: Dict[str, str] = field(default_factory=dict)


@dataclass
class CoverageBuildResult:
    """Output from coverage building."""
    success: bool
    coverage_name: str
    config_yaml: str
    config_path: str
    generated_files: Dict[str, str] = field(default_factory=dict)
    validation_results: Optional[ValidationResult] = None
    warnings: List[str] = field(default_factory=list)
    human_review_required: List[str] = field(default_factory=list)
    build_duration_seconds: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def needs_review(self) -> bool:
        return len(self.human_review_required) > 0


@dataclass
class BuildProgress:
    """Progress tracking for build."""
    stage: BuildStage
    progress: float  # 0-1
    message: str
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_stages: List[BuildStage] = field(default_factory=list)


# =============================================================================
# SIGNAL LIBRARY TYPES
# =============================================================================

@dataclass
class SignalGroupDefinition:
    """Definition of a signal group."""
    group_id: str
    name: str
    description: str
    signals: List[str]
    applicable_industries: List[str] = field(default_factory=list)
    default_weight: float = 0.10


@dataclass
class IndustryProfile:
    """Industry-specific configuration profile."""
    industry: str
    primary_groups: List[str]
    secondary_groups: List[str]
    excluded_signals: List[str] = field(default_factory=list)
    weight_adjustments: Dict[str, float] = field(default_factory=dict)
    risk_focus: List[str] = field(default_factory=list)


# =============================================================================
# LLM TYPES
# =============================================================================

@dataclass
class LLMPrompt:
    """LLM prompt template."""
    name: str
    system_prompt: str
    user_prompt_template: str
    expected_format: str  # json, yaml, text
    max_tokens: int = 4000
    temperature: float = 0.7


@dataclass
class LLMResponse:
    """LLM response."""
    content: str
    parsed: Optional[Dict[str, Any]] = None
    tokens_used: int = 0
    model: str = ""
    success: bool = True
    error: Optional[str] = None
