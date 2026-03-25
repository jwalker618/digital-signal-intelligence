"""
DSI Configuration Adapter (Version 4 - Phase 1)

Bridges the new Pydantic config models with the existing dataclass-based
types in layers/risk/types.py.

This adapter enables incremental migration:
1. New code can use compiled Pydantic configs directly
2. Legacy code continues using dataclass types
3. The adapter converts between formats as needed

Usage:
    from infrastructure.models.adapter import adapt_config_for_scorer
    from infrastructure.models import get_config

    # Get compiled Pydantic config
    pydantic_config = get_config("cyber", "cyber_general")

    # Convert to legacy format for scorer
    legacy_config = adapt_config_for_scorer(pydantic_config)
    result = scorer.score_entity(entity_id, legacy_config)
"""

from typing import Any, Dict, List, Optional

from .config_schema import (
    CoverageConfig as PydanticCoverageConfig,
    SignalDefinition,
    ThreeLayerAssessmentGroup,
    ScoreCondition,
    ScoreConditionAction,
    CorrelationDirection,
)


def adapt_score_conditions(conditions: Optional[List[ScoreCondition]]) -> List[Dict[str, Any]]:
    """Convert Pydantic score conditions to legacy format."""
    if not conditions:
        return []

    result = []
    for cond in conditions:
        result.append({
            "condition_type": "threshold",
            "condition_value": cond.threshold,
            "comparison": cond.comparison.value,
            "action": cond.action.value,
            "action_value": cond.applied or cond.override or cond.note,
            "applied": cond.applied,
            "note": cond.note or "",
        })
    return result


def adapt_signal_group(
    group: ThreeLayerAssessmentGroup,
    signals: List[SignalDefinition]
) -> Dict[str, Any]:
    """
    Convert a Pydantic three-layer assessment group to legacy signal group format.

    Legacy format:
        {
            "id": str,
            "name": str,
            "weight": float,
            "features": [...],
            "score_condition": bool,
            "conditions": [...]
        }
    """
    # Collect signals that belong to this group
    group_signals = [
        sig for sig in signals
        if sig.three_layer_assessment and sig.three_layer_assessment.group_id == group.id
    ]

    # Build features list
    features = []
    for sig in group_signals:
        tla = sig.three_layer_assessment
        if tla and tla.risk:
            features.append({
                "id": sig.id,
                "name": sig.id.replace("_", " ").title(),
                "weight": tla.risk.weight,
                "inference_function": sig.inference_utility_function,
                "correlation_direction": tla.risk.correlation_direction.value,
                "score_condition": tla.risk.score_conditions is not None,
                "conditions": adapt_score_conditions(tla.risk.score_conditions),
                "expectation_level": sig.expectation_level.value,
            })

    # Group-level conditions
    group_conditions = []
    has_group_condition = False
    if group.risk and group.risk.score_conditions:
        has_group_condition = True
        group_conditions = adapt_score_conditions(group.risk.score_conditions)

    return {
        "id": group.id,
        "name": group.label or group.id.replace("_", " ").title(),
        "weight": group.risk.weight if group.risk else 0.0,
        "features": features,
        "score_condition": has_group_condition,
        "conditions": group_conditions,
    }


def adapt_categorical_group(
    group_id: str,
    signals: List[SignalDefinition]
) -> Optional[Dict[str, Any]]:
    """
    Convert categorical signals to legacy categorical group format.

    Legacy format:
        {
            "id": str,
            "name": str,
            "inference_function": str,
            "values": [{"category": str, "label": str, "modifier": float}]
        }
    """
    # Find signals with this categorical group
    cat_signals = [
        sig for sig in signals
        if sig.categories and sig.categories.group_id == group_id
    ]

    if not cat_signals:
        return None

    # Use first signal (groups typically have one categorical signal)
    sig = cat_signals[0]
    cat = sig.categories

    values = []
    for feat in cat.features:
        values.append({
            "category": feat.cat,
            "label": feat.label or feat.cat,
            "modifier": feat.applied if feat.applied else 1.0,
            "value": feat.value,
        })

    return {
        "id": group_id,
        "name": group_id.replace("_", " ").title(),
        "inference_function": sig.inference_utility_function,
        "values": values,
    }


def adapt_config_for_scorer(config: PydanticCoverageConfig) -> Dict[str, Any]:
    """
    Convert a compiled Pydantic CoverageConfig to legacy scorer format.

    This enables the existing ModelScorer to work with compiled configs
    until it's fully migrated to use Pydantic models directly.

    Args:
        config: Compiled Pydantic CoverageConfig

    Returns:
        Dictionary in legacy CoverageConfig format compatible with scorer
    """
    # Build signal groups from three_layer_assessment groups
    signal_groups = []
    for group in config.groups.three_layer_assessment:
        signal_groups.append(adapt_signal_group(group, config.signal_registry))

    # Build categorical groups
    categorical_groups = []
    for cat_group in config.groups.categories:
        adapted = adapt_categorical_group(cat_group.id, config.signal_registry)
        if adapted:
            categorical_groups.append(adapted)

    # Build tier bands
    tier_bands = []
    for band in config.risk_tier_bands.bands:
        tier_bands.append({
            "id": band.id,
            "label": band.label,
            "min_score": band.interpretation.bands.min,
            "max_score": band.interpretation.bands.max,
            "action": band.interpretation.action.value,
            "method": band.interpretation.application.method.value,
            "value": band.interpretation.application.value,
            "applied": band.interpretation.application.applied,
            "basis": band.interpretation.application.basis,
        })

    return {
        "coverage": config.metadata.name.split("_")[0],
        "configuration": config.metadata.name,
        "version": config.metadata.version,
        "min_premium": config.metadata.min_premium,
        "default_currency": config.metadata.default_currency,
        "product_types": config.metadata.product_types,
        "signal_groups": signal_groups,
        "categorical_groups": categorical_groups,
        "tier_bands": tier_bands,
        "pricing": {
            "base_limit_reference": config.pricing.base_limit_reference,
            "base_deductible_reference": config.pricing.base_deductible_reference,
            "by_product_type": {
                pt: {
                    "ilf_curve": {
                        "anchor_limit": pricing.ilf_curve.anchor_limit,
                        "curve": pricing.ilf_curve.curve,
                        "params": pricing.ilf_curve.params or {},
                    },
                    "deductible_factors": [
                        {"deductible": f.deductible, "factor": f.factor}
                        for f in pricing.deductible_factors
                    ],
                }
                for pt, pricing in config.pricing.by_product_type.items()
            },
        },
    }


class TypedConfigWrapper:
    """
    Wrapper that provides O(1) typed attribute access to compiled configs.

    This wrapper allows both dot notation (new style) and dict-like access
    (legacy compatibility) to work with the same config.

    Example:
        wrapper = TypedConfigWrapper(pydantic_config)

        # New style - O(1) attribute access
        base_limit = wrapper.pricing.base_limit_reference

        # Legacy style - still works
        base_limit = wrapper.raw["pricing"]["base_limit_reference"]
    """

    def __init__(self, config: PydanticCoverageConfig):
        self._config = config
        self._raw = None  # Lazy conversion

    @property
    def raw(self) -> Dict[str, Any]:
        """Get raw dictionary representation (lazy, cached)."""
        if self._raw is None:
            self._raw = adapt_config_for_scorer(self._config)
        return self._raw

    # Delegate attribute access to Pydantic model
    def __getattr__(self, name: str) -> Any:
        return getattr(self._config, name)

    # Convenience methods forwarding to Pydantic model
    def get_tier_for_score(self, score: float) -> int:
        return self._config.get_tier_for_score(score)

    def get_ilf(self, product_type: str, limit: int) -> float:
        return self._config.get_ilf(product_type, limit)

    def get_deductible_factor(self, product_type: str, deductible: int) -> float:
        return self._config.get_deductible_factor(product_type, deductible)
