"""
Loss Correlation Layer (Phase 16)

Loss propensity scoring, cohort analysis, continuous monitoring,
and pricing integration.

This layer extends DSI from risk quality assessment to loss prediction
by correlating observable signals with historical loss outcomes.
"""

# Types and enums
from .types import (
    # Enums
    CorrelationType,
    CorrelationDirection,
    LossPropensityBand,
    SeverityPropensityBand,
    TrendDirection,
    # Signal results
    LossSignalResult,
    # Configuration types
    LossCorrelationFeatureConfig,
    LossCorrelationGroupConfig,
    PropensityBandConfig,
    CohortDefinition,
    MonitoringConfig,
    LossCorrelationConfig,
    # Result types
    LossPropensityResult,
    # Correlation matrix types
    CorrelationMatrixEntry,
    CorrelationMatrix,
    # Monitoring types
    DeteriorationAlert,
    MonitoringResult,
)

# Scorer
from .scorer import LossCorrelationScorer

# Correlation matrix
from .matrix import CorrelationMatrixManager

# Monitoring
from .monitoring import LossMonitoringEngine

# Pricing integration
from .integration import (
    PricingIntegrationMethod,
    PricingIntegrationConfig,
    LossPricingResult,
    LossPricingIntegration,
    create_default_pricing_grid,
    calculate_combined_modifier,
)


__all__ = [
    # Enums
    'CorrelationType',
    'CorrelationDirection',
    'LossPropensityBand',
    'SeverityPropensityBand',
    'TrendDirection',
    # Signal results
    'LossSignalResult',
    # Configuration types
    'LossCorrelationFeatureConfig',
    'LossCorrelationGroupConfig',
    'PropensityBandConfig',
    'CohortDefinition',
    'MonitoringConfig',
    'LossCorrelationConfig',
    # Result types
    'LossPropensityResult',
    # Correlation matrix types
    'CorrelationMatrixEntry',
    'CorrelationMatrix',
    # Monitoring types
    'DeteriorationAlert',
    'MonitoringResult',
    # Classes
    'LossCorrelationScorer',
    'CorrelationMatrixManager',
    'LossMonitoringEngine',
    # Pricing integration
    'PricingIntegrationMethod',
    'PricingIntegrationConfig',
    'LossPricingResult',
    'LossPricingIntegration',
    'create_default_pricing_grid',
    'calculate_combined_modifier',
]
