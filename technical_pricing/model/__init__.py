"""
DSI Model Layer

Runtime engine for executing the 13-step model workflow:
1. Config instantiation (content-addressable storage)
2. Model data file creation
3. Input verification
4-6. Signal scoring + conditions
7. Direct query evaluation
8-9. Tier resolution
10-12. Premium calculation
13. Decision output

All configuration comes from YAML - nothing hardcoded.
"""

from .types import (
    # Enums
    DecisionType,
    VersionType,
    ConditionAction,
    PremiumMethod,
    
    # Config types
    SignalCondition,
    SignalConfig,
    SignalGroupConfig,
    DirectQueryImpact,
    DirectQueryConfig,
    TierConfig,
    LimitBand,
    CoverageConfig,
    ConfigVersion,
    
    # Signal types
    SignalOutput,
    ScoringResult,
    
    # Query types
    QueryEvaluationResult,
    
    # Pricing types
    ModifierApplication,
    PricingResult,
    
    # Model types
    ModelVersion,
    WorkflowResult,
    SubmissionRequest,
)

from .config_manager import ConfigManager
from .model_data import ModelDataManager
from .scorer import ModelScorer
from .query_evaluator import QueryEvaluator
from .pricer import ModelPricer
from .workflow import WorkflowEngine, create_workflow_engine, run_model

__all__ = [
    # Enums
    "DecisionType",
    "VersionType",
    "ConditionAction",
    "PremiumMethod",
    
    # Config types
    "SignalCondition",
    "SignalConfig",
    "SignalGroupConfig",
    "DirectQueryImpact",
    "DirectQueryConfig",
    "TierConfig",
    "LimitBand",
    "CoverageConfig",
    "ConfigVersion",
    
    # Signal types
    "SignalOutput",
    "ScoringResult",
    
    # Query types
    "QueryEvaluationResult",
    
    # Pricing types
    "ModifierApplication",
    "PricingResult",
    
    # Model types
    "ModelVersion",
    "WorkflowResult",
    "SubmissionRequest",
    
    # Managers/Engines
    "ConfigManager",
    "ModelDataManager",
    "ModelScorer",
    "QueryEvaluator",
    "ModelPricer",
    "WorkflowEngine",
    
    # Factory functions
    "create_workflow_engine",
    "run_model",
]
