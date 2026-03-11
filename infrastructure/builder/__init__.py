"""
DSI Coverage Builder Module (Phase 13)

LLM-assisted coverage creation with validation.

Components:
- CoverageBuilder: Main builder for creating coverages
- CoverageExpansionGenerator: Expansion pipeline for coverage phases
- SignalLibrary: Library of reusable signals
- ConfigValidator: Configuration validation
"""

from .types import (
    # Build types
    BuildStage,
    BuildProgress,
    CoverageSpec,
    CoverageBuildResult,
    # Analysis types
    IndustryAnalysis,
    SignalRecommendation,
    SignalSelection,
    # Validation types
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    # Code generation
    GeneratedCode,
    SignalTemplate,
)

from .expansion_types import (
    ExpansionSpec,
    ExpansionResult,
    ConfigurationSpec,
    SignalGroupSpec,
    SignalSpec,
)

from .expansion_generator import (
    CoverageExpansionGenerator,
    load_expansion_spec,
)

from .coverage_builder import CoverageBuilder
from .signal_library import SignalLibrary
from .validator import ConfigValidator, validate_coverage_config


__all__ = [
    # Build types
    "BuildStage",
    "BuildProgress",
    "CoverageSpec",
    "CoverageBuildResult",
    # Analysis types
    "IndustryAnalysis",
    "SignalRecommendation",
    "SignalSelection",
    # Validation types
    "ValidationResult",
    "ValidationIssue",
    "ValidationSeverity",
    # Code generation
    "GeneratedCode",
    "SignalTemplate",
    # Expansion types
    "ExpansionSpec",
    "ExpansionResult",
    "ConfigurationSpec",
    "SignalGroupSpec",
    "SignalSpec",
    # Components
    "CoverageBuilder",
    "CoverageExpansionGenerator",
    "load_expansion_spec",
    "SignalLibrary",
    "ConfigValidator",
    "validate_coverage_config",
]
