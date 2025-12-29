"""
DSI Model Layer - Phase 4 Implementation

This module provides the model layer that connects the signal architecture
to the pricing workflow. It implements the 13-step DSI workflow:

1. Model Configuration Instantiation
2. Model Data File Creation
3. Minimum Viable Input Verification
4. Signal Extraction
5. Pure Composite Score Calculation
6. Signal Conditions Evaluation
7. Direct Query Response Evaluation
8. Maximum Tier Override Application
9. Final Tier Capture
10. Base Premium Generation
11. Modifier Application
12. Limit Band Scaling
13. Output Decision

Components:
- types: Core dataclasses for configuration and model data
- config_manager: Configuration hashing, storage, and parsing
- model_data: Model version tracking and audit trail
- scorer: Signal extraction and scoring (Steps 4-6)
- query_evaluator: Direct query evaluation (Step 7)
- pricer: Premium calculation (Steps 8-12)
- workflow: Complete 13-step orchestration

Usage:
    from technical_pricing.model import run_assessment, WorkflowResult

    result = run_assessment(
        entity_id="AIRLINE123",
        coverage="aerospace",
        submission_data={"limit": 100_000_000, "tiv": 500_000_000},
    )

    print(f"Score: {result.composite_score}")
    print(f"Tier: {result.tier} ({result.tier_label})")
    print(f"Decision: {result.decision.value}")
    print(f"Premium: ${result.recommended_premium:,.0f}")
"""

# Types
from .types import (
    # Enums
    DecisionType,
    ConditionAction,
    PremiumMethod,
    # Configuration types
    CoverageConfig,
    ConfigMetadata,
    SignalGroupConfig,
    SignalFeatureConfig,
    SignalCondition,
    DirectQueryConfig,
    DirectQueryImpact,
    CategoricalGroupConfig,
    CategoricalFeatureValue,
    TierConfig,
    LimitBandConfig,
    PricingConfig,
    ConfigVersion,
    # Model data types
    SignalOutput,
    CategoricalOutput,
    TriggeredCondition,
    AppliedModifier,
    ModelVersion,
    # Result types
    ScoringResult,
    QueryEvaluationResult,
    PricingResult,
    WorkflowResult,
)

# Config Manager
from .config_manager import (
    ConfigManager,
    ConfigParseError,
    ConfigNotFoundError,
    get_config_manager,
    load_coverage_config,
)

# Model Data Manager
from .model_data import (
    ModelDataManager,
    ModelNotFoundError,
    VersionNotFoundError,
    get_model_data_manager,
)

# Scorer
from .scorer import (
    ModelScorer,
    ScoringError,
    get_scorer,
)

# Query Evaluator
from .query_evaluator import (
    QueryEvaluator,
    get_query_evaluator,
)

# Pricer
from .pricer import (
    ModelPricer,
    PricingError,
    get_pricer,
)

# Workflow Engine
from .workflow import (
    WorkflowEngine,
    WorkflowError,
    MissingInputError,
    get_workflow_engine,
    run_assessment,
)

# Backward compatibility - re-export DSIPricingEngine from dsi_config_model
try:
    from .dsi_config_model import (
        DSIPricingEngine,
        DSIAssessment,
        ModelConfig,
        SignalInput,
        DirectInquiryInput,
    )
except ImportError:
    # dsi_config_model may not be available in all contexts
    pass

__all__ = [
    # Enums
    "DecisionType",
    "ConditionAction",
    "PremiumMethod",
    # Configuration types
    "CoverageConfig",
    "ConfigMetadata",
    "SignalGroupConfig",
    "SignalFeatureConfig",
    "SignalCondition",
    "DirectQueryConfig",
    "DirectQueryImpact",
    "CategoricalGroupConfig",
    "CategoricalFeatureValue",
    "TierConfig",
    "LimitBandConfig",
    "PricingConfig",
    "ConfigVersion",
    # Model data types
    "SignalOutput",
    "CategoricalOutput",
    "TriggeredCondition",
    "AppliedModifier",
    "ModelVersion",
    # Result types
    "ScoringResult",
    "QueryEvaluationResult",
    "PricingResult",
    "WorkflowResult",
    # Config Manager
    "ConfigManager",
    "ConfigParseError",
    "ConfigNotFoundError",
    "get_config_manager",
    "load_coverage_config",
    # Model Data Manager
    "ModelDataManager",
    "ModelNotFoundError",
    "VersionNotFoundError",
    "get_model_data_manager",
    # Scorer
    "ModelScorer",
    "ScoringError",
    "get_scorer",
    # Query Evaluator
    "QueryEvaluator",
    "get_query_evaluator",
    # Pricer
    "ModelPricer",
    "PricingError",
    "get_pricer",
    # Workflow Engine
    "WorkflowEngine",
    "WorkflowError",
    "MissingInputError",
    "get_workflow_engine",
    "run_assessment",
]
