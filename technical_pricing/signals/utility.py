"""
Technical pricing utility functions

Model-level operations that apply configuration values to signal scores.
These are NOT extractors/aggregators/categorizers - they operate at the model level.

Utility Function Types:
1. ConditionEvaluator - Evaluate signal scores against config-defined bands
2. CompositeScorer - Calculate weighted composite scores using config weights  
3. BooleanEvaluator - Process direct query (yes/no) responses
4. TierAssigner - Map composite scores to tiers using config thresholds
5. summarize_data - Aggregate results into final decision summary

Key Design Principle:
- All weights, bands, tier definitions come from configuration
- Utility functions never hardcode these values
- Instantiation is by configuration (e.g., "aerospace_general"), not coverage
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, Iterable, Union

# =============================================================================
# REGISTRY
# =============================================================================

UTILITY_REGISTRY: Dict[str, Type["UtilityFunction"]] = {}


def register_utility(cls: Type["UtilityFunction"]) -> Type["UtilityFunction"]:
    """Decorator to register utility function classes."""
    UTILITY_REGISTRY[cls.__name__] = cls
    return cls


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class UtilityResult:
    """Standardized result from any utility function."""
    category: Optional[str] = None
    score: Optional[float] = None
    modifier: Optional[float] = None
    criteria: List[str] = field(default_factory=list)
    action: Optional[str] = None
    override: Optional[int] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score,
            "modifier": self.modifier,
            "criteria": self.criteria,
            "action": self.action,
            "override": self.override,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# =============================================================================
# BASE UTILITY CLASS
# =============================================================================

class UtilityFunction(ABC):
    """
    Abstract base class for all utility functions.
    
    Utility functions operate at the model level, applying configuration values
    to signal scores. They are instantiated with a specific configuration
    (e.g., "aerospace_general"), not just a coverage.
    """

    def __init__(
        self, 
        coverage: str,              # e.g., "aerospace"
        cov_configuration: str,     # e.g., "aerospace_general"
        configuration: Dict[str, Any],  # The full config dict for this configuration
        **kwargs: Any
    ):
        self.coverage = coverage
        self.cov_configuration = cov_configuration
        self.configuration = configuration
        self.kwargs = kwargs

    @abstractmethod
    def evaluate(self, data: Dict[str, Any]) -> Union[UtilityResult, List[UtilityResult]]:
        """Process data and return utility result(s)."""
        raise NotImplementedError


# =============================================================================
# CONDITION EVALUATOR
# =============================================================================

@register_utility
class ConditionEvaluator(UtilityFunction):
    """
    Evaluates signal scores against condition bands defined in configuration.
    
    Checks both signal_groups and signal_features for score_condition=true,
    then evaluates the score against the config-defined bands.
    
    Returns actions (DECLINE, REFER, etc.) and tier overrides based on bands.
    """

    def evaluate(self, data: Dict[str, Any]) -> List[UtilityResult]:
        """
        Evaluate signal scores against config-defined bands.
        
        Args:
            data: Dict mapping signal_id to score (0-100)
                  e.g., {"accident_history": 35, "certificate_status": 85}
        
        Returns:
            List of UtilityResult for each band match (actions/overrides)
        """
        results: List[UtilityResult] = []

        group_defs: List[Dict[str, Any]] = self.configuration.get("signal_groups", [])
        feature_defs_map: Dict[str, List[Dict[str, Any]]] = self.configuration.get("signal_features", {})

        # Evaluate group-level conditions
        for group_def in group_defs:
            group_id = group_def.get("id")
            if not group_id:
                continue

            if group_def.get("score_condition") is True:
                group_score = data.get(group_id)
                bands = group_def.get("bands", [])
                inclusive_max = bool(group_def.get("inclusive_max", False))

                band = self._match_band(group_score, bands, inclusive_max)
                if band:
                    results.append(UtilityResult(
                        category=group_id,
                        score=group_score,
                        modifier=band.get("modifier"),
                        criteria=[band.get("note", f"Score {group_score} matched band")],
                        action=band.get("action"),
                        override=band.get("override"),
                        confidence=1.0,
                        metadata={"level": "group", "band": band}
                    ))

            # Evaluate feature-level conditions within this group
            for feature_def in feature_defs_map.get(group_id, []):
                feat_id = feature_def.get("id")
                if not feat_id:
                    continue

                if feature_def.get("score_condition") is True:
                    feat_score = data.get(feat_id)
                    feat_bands = feature_def.get("bands", [])
                    feat_inclusive_max = bool(feature_def.get("inclusive_max", False))

                    feat_band = self._match_band(feat_score, feat_bands, feat_inclusive_max)
                    if feat_band:
                        results.append(UtilityResult(
                            category=feat_id,
                            score=feat_score,
                            modifier=feat_band.get("modifier"),
                            criteria=[feat_band.get("note", f"Score {feat_score} matched band")],
                            action=feat_band.get("action"),
                            override=feat_band.get("override"),
                            confidence=1.0,
                            metadata={"level": "feature", "group": group_id, "band": feat_band}
                        ))

        return results

    def _match_band(
        self, 
        score: Any, 
        bands: List[Dict[str, Any]], 
        inclusive_max: bool
    ) -> Optional[Dict[str, Any]]:
        """
        Find the first matching band for the given score.
        
        Bands are sorted by 'max' ascending and matched in order.
        """
        if score is None or not isinstance(score, (int, float)):
            return None

        sorted_bands = sorted(bands, key=lambda b: b.get("max", float("inf")))
        
        for band in sorted_bands:
            max_val = band.get("max")
            if max_val is None:
                return band
            if inclusive_max:
                if score <= max_val:
                    return band
            else:
                if score < max_val:
                    return band
        
        return None


# =============================================================================
# COMPOSITE SCORER
# =============================================================================

@register_utility
class CompositeScorer(UtilityFunction):
    """
    Calculates weighted composite scores using weights from configuration.
    
    Two-level weighting:
    1. Feature weights within each signal group (must sum to 1.0)
    2. Group weights across all groups (must sum to 1.0)
    
    Formula:
        composite = Σ (group_weight × Σ (feature_weight × feature_score))
    """

    def evaluate(self, data: Dict[str, Any]) -> UtilityResult:
        """
        Calculate weighted composite score from signal scores.
        
        Args:
            data: Dict mapping signal_id to score (0-100)
                  e.g., {"alliance_membership": 88, "accident_history": 100, ...}
        
        Returns:
            UtilityResult with composite_score and breakdown metadata
        """
        group_defs: List[Dict[str, Any]] = self.configuration.get("signal_groups", [])
        feature_defs_map: Dict[str, List[Dict[str, Any]]] = self.configuration.get("signal_features", {})

        total_composite = 0.0
        group_contributions = []
        feature_contributions = []
        missing_signals = []

        for group_def in group_defs:
            group_id = group_def.get("id")
            group_weight = group_def.get("weight", 0)
            
            if not group_id or group_weight == 0:
                continue

            # Calculate group score from features
            feature_defs = feature_defs_map.get(group_id, [])
            group_score = 0.0
            group_feature_details = []

            for feature_def in feature_defs:
                feat_id = feature_def.get("id")
                feat_weight = feature_def.get("weight", 0)
                
                if not feat_id or feat_weight == 0:
                    continue

                feat_score = data.get(feat_id)
                
                if feat_score is None:
                    missing_signals.append({
                        "signal_id": feat_id,
                        "group_id": group_id,
                        "weight": feat_weight
                    })
                    # Use neutral score for missing signals
                    feat_score = 50.0

                contribution = feat_score * feat_weight
                group_score += contribution

                group_feature_details.append({
                    "feature_id": feat_id,
                    "score": feat_score,
                    "weight": feat_weight,
                    "contribution": round(contribution, 2)
                })

            # Calculate group contribution to total
            group_contribution = group_score * group_weight
            total_composite += group_contribution

            group_contributions.append({
                "group_id": group_id,
                "group_score": round(group_score, 2),
                "weight": group_weight,
                "contribution": round(group_contribution, 2),
                "features": group_feature_details
            })

            feature_contributions.extend(group_feature_details)

        # Scale to 0-1000 range (config uses 0-1000 for tier thresholds)
        composite_score_1000 = total_composite * 10

        return UtilityResult(
            category="COMPOSITE",
            score=round(composite_score_1000, 2),
            criteria=[f"Composite score: {round(composite_score_1000, 2)}/1000"],
            confidence=1.0 if not missing_signals else 0.8,
            metadata={
                "composite_score_100": round(total_composite, 2),
                "composite_score_1000": round(composite_score_1000, 2),
                "group_contributions": group_contributions,
                "missing_signals": missing_signals,
                "signal_count": len(feature_contributions),
                "missing_count": len(missing_signals)
            }
        )


# =============================================================================
# BOOLEAN EVALUATOR
# =============================================================================

@register_utility
class BooleanEvaluator(UtilityFunction):
    """
    Evaluates direct query (yes/no) responses against config-defined bands.
    
    Processes the direct_queries section of configuration, matching boolean
    responses to their configured actions/modifiers/overrides.
    """

    def evaluate(self, data: Dict[str, Any]) -> List[UtilityResult]:
        """
        Evaluate boolean responses to direct queries.
        
        Args:
            data: Dict mapping query_id to boolean response
                  e.g., {"pending_claims": True, "coverage_declined": False}
        
        Returns:
            List of UtilityResult for each query with matched band
        """
        results: List[UtilityResult] = []
        queries: List[Dict[str, Any]] = self.configuration.get("direct_queries", [])

        for query in queries:
            query_id = query.get("id")
            if not query_id:
                continue

            response = data.get(query_id)
            if response is None or not isinstance(response, bool):
                continue

            bands: List[Dict[str, Any]] = query.get("bands", [])
            
            # Find matching band for this boolean response
            matched_band = next(
                (b for b in bands if b.get("return") is response),
                None
            )

            if matched_band:
                results.append(UtilityResult(
                    category=query_id,
                    modifier=matched_band.get("modifier"),
                    criteria=[matched_band.get("note", f"{query_id} = {response}")],
                    action=matched_band.get("action"),
                    override=matched_band.get("override"),
                    confidence=1.0,
                    metadata={"query": query, "response": response, "band": matched_band}
                ))

        return results


# =============================================================================
# TIER ASSIGNER
# =============================================================================

@register_utility
class TierAssigner(UtilityFunction):
    """
    Maps composite scores to tiers using config-defined thresholds.
    
    Uses the tier_thresholds section of configuration to determine:
    - Tier assignment (1-5)
    - Auto-approve/decline status
    - Premium generation parameters
    """

    def evaluate(self, data: Dict[str, Any]) -> UtilityResult:
        """
        Assign tier based on composite score.
        
        Args:
            data: Dict with "composite_score" key (0-1000 scale)
                  e.g., {"composite_score": 847}
        
        Returns:
            UtilityResult with tier assignment and metadata
        """
        composite_score = data.get("composite_score")
        
        if composite_score is None:
            return UtilityResult(
                category="UNKNOWN",
                action="REFER",
                criteria=["No composite score provided"],
                confidence=0.0
            )

        tiers = self.configuration.get("tier_thresholds", {}).get("tiers", [])

        for tier_def in tiers:
            min_score = tier_def.get("min_score", 0)
            max_score = tier_def.get("max_score", 1000)
            
            if min_score <= composite_score <= max_score:
                # Determine action based on auto-approve/decline
                if tier_def.get("auto_decline"):
                    action = "DECLINE"
                elif tier_def.get("auto_approve"):
                    action = "APPROVE"
                else:
                    action = "REFER"

                return UtilityResult(
                    category=tier_def.get("label", f"TIER_{tier_def.get('id')}"),
                    score=composite_score,
                    criteria=[f"Score {composite_score} -> {tier_def.get('label')}"],
                    action=action,
                    override=tier_def.get("id"),
                    confidence=1.0,
                    metadata={
                        "tier_id": tier_def.get("id"),
                        "tier_label": tier_def.get("label"),
                        "description": tier_def.get("description"),
                        "auto_approve": tier_def.get("auto_approve"),
                        "auto_decline": tier_def.get("auto_decline"),
                        "base_premium": tier_def.get("base_premium"),
                        "premium_method": tier_def.get("premium_generation_method")
                    }
                )

        # Score outside all defined tiers
        return UtilityResult(
            category="UNKNOWN",
            score=composite_score,
            action="REFER",
            criteria=[f"Score {composite_score} outside defined tier ranges"],
            confidence=0.5
        )


# =============================================================================
# CATEGORICAL FEATURE EVALUATOR
# =============================================================================

@register_utility
class CategoricalFeatureEvaluator(UtilityFunction):
    """
    Evaluates categorical features and returns their config-defined modifiers.
    
    Processes the categorical_features section of configuration, matching
    inferred categories to their configured modifiers.
    """

    def evaluate(self, data: Dict[str, Any]) -> List[UtilityResult]:
        """
        Evaluate categorical features and return modifiers.
        
        Args:
            data: Dict mapping categorical_group_id to category value
                  e.g., {"operator_type": "MAJOR_AIRLINE", "fleet_size": "LARGE"}
        
        Returns:
            List of UtilityResult with modifiers for each matched category
        """
        results: List[UtilityResult] = []
        categorical_features = self.configuration.get("categorical_features", {})

        for group_id, categories in categorical_features.items():
            category_value = data.get(group_id)
            if not category_value:
                continue

            # Find matching category definition
            matched_cat = next(
                (c for c in categories if c.get("cat") == category_value),
                None
            )

            if matched_cat:
                results.append(UtilityResult(
                    category=category_value,
                    modifier=matched_cat.get("modifier", 1.0),
                    criteria=[f"{group_id}: {matched_cat.get('label', category_value)}"],
                    confidence=1.0,
                    metadata={
                        "group_id": group_id,
                        "category": category_value,
                        "label": matched_cat.get("label"),
                        "description": matched_cat.get("description")
                    }
                ))

        return results


# =============================================================================
# SUMMARY FUNCTION
# =============================================================================

def _iter_results(data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    """
    Yield all result-like items from any list in data.
    Handles both UtilityResult objects and raw dicts.
    """
    for value in data.values():
        if isinstance(value, list):
            for item in value:
                if isinstance(item, UtilityResult):
                    yield item.to_dict()
                elif isinstance(item, dict):
                    yield item


def summarize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Aggregate all utility results into a final decision summary.
    
    Processes results from all utility functions and produces:
    - max_override: Highest tier override triggered
    - declines: All DECLINE actions
    - refers: All REFER actions with their overrides
    - infos: Informational items
    - modifiers: All modifier adjustments
    - final_action: Resolved action (DECLINE > REFER > APPROVE)
    
    Args:
        data: Dict containing lists of utility results
              e.g., {"condition_results": [...], "boolean_results": [...]}
    
    Returns:
        Summary dict with categorized actions and final decision
    """
    max_override: Optional[int] = None
    declines: List[Dict[str, Any]] = []
    refers: List[Dict[str, Any]] = []
    infos: List[Dict[str, Any]] = []
    modifiers: List[Dict[str, Any]] = []

    for item in _iter_results(data):
        # Track maximum override
        override = item.get("override")
        if isinstance(override, int):
            if max_override is None or override > max_override:
                max_override = override

        action = item.get("action")
        if not isinstance(action, str):
            continue

        action_lower = action.lower()
        category = item.get("category")
        criteria = item.get("criteria", [])
        note = criteria[0] if criteria else ""

        if action_lower == "decline":
            declines.append({
                "category": category,
                "action": action,
                "override": override,
                "note": note,
            })
        elif action_lower == "refer":
            refers.append({
                "category": category,
                "action": action,
                "override": override,
                "note": note,
            })
        elif action_lower == "info":
            infos.append({
                "category": category,
                "action": action,
                "note": note,
            })
        elif action_lower == "modifier":
            modifiers.append({
                "category": category,
                "action": action,
                "modifier": item.get("modifier"),
                "note": note,
            })

    # Determine final action (DECLINE takes precedence)
    if declines:
        final_action = "DECLINE"
    elif refers:
        final_action = "REFER"
    else:
        final_action = "APPROVE"

    return {
        "max_override": max_override,
        "final_action": final_action,
        "declines": declines,
        "refers": refers,
        "infos": infos,
        "modifiers": modifiers,
        "decline_count": len(declines),
        "refer_count": len(refers),
    }


# =============================================================================
# MODIFIER CALCULATOR
# =============================================================================

def calculate_final_modifier(
    categorical_modifiers: List[UtilityResult],
    boolean_modifiers: List[UtilityResult]
) -> Dict[str, Any]:
    """
    Calculate the final composite modifier from all sources.
    
    Modifiers are multiplicative:
        final_modifier = Π (all individual modifiers)
    
    Args:
        categorical_modifiers: Results from CategoricalFeatureEvaluator
        boolean_modifiers: Results from BooleanEvaluator with modifiers
    
    Returns:
        Dict with final_modifier and breakdown
    """
    composite_modifier = 1.0
    modifier_breakdown = []

    for result in categorical_modifiers:
        if result.modifier is not None:
            composite_modifier *= result.modifier
            modifier_breakdown.append({
                "source": "categorical",
                "category": result.category,
                "modifier": result.modifier
            })

    for result in boolean_modifiers:
        if result.modifier is not None:
            composite_modifier *= result.modifier
            modifier_breakdown.append({
                "source": "boolean",
                "category": result.category,
                "modifier": result.modifier
            })

    return {
        "final_modifier": round(composite_modifier, 4),
        "modifier_breakdown": modifier_breakdown,
        "modifier_count": len(modifier_breakdown)
    }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_utility(
    utility_type: str,
    coverage: str,
    cov_configuration: str,
    configuration: Dict[str, Any],
    **kwargs: Any
) -> UtilityFunction:
    """
    Factory function to instantiate utility functions.
    
    Args:
        utility_type: Type of utility ("condition", "composite", "boolean", "tier", "categorical")
        coverage: Coverage cohort (e.g., "aerospace")
        cov_configuration: Specific configuration (e.g., "aerospace_general")
        configuration: The full configuration dict
        **kwargs: Additional arguments passed to utility
    
    Returns:
        Instantiated UtilityFunction
    
    Raises:
        ValueError: If utility_type is unknown
    """
    type_mapping = {
        "condition": ConditionEvaluator,
        "composite": CompositeScorer,
        "boolean": BooleanEvaluator,
        "tier": TierAssigner,
        "categorical": CategoricalFeatureEvaluator,
    }

    utility_class = type_mapping.get(utility_type.lower())
    if not utility_class:
        raise ValueError(
            f"Unknown utility type '{utility_type}'. "
            f"Available: {list(type_mapping.keys())}"
        )

    return utility_class(
        coverage=coverage,
        cov_configuration=cov_configuration,
        configuration=configuration,
        **kwargs
    )


# =============================================================================
# DEMO / TESTING
# =============================================================================

if __name__ == "__main__":
    # Sample aerospace_general configuration (subset)
    sample_config = {
        "tier_thresholds": {
            "tiers": [
                {"id": 1, "label": "PREFERRED", "min_score": 800, "max_score": 1000, 
                 "auto_approve": True, "auto_decline": False, "base_premium": 1200},
                {"id": 2, "label": "STANDARD_PLUS", "min_score": 650, "max_score": 799,
                 "auto_approve": True, "auto_decline": False, "base_premium": 1800},
                {"id": 3, "label": "STANDARD", "min_score": 500, "max_score": 649,
                 "auto_approve": False, "auto_decline": False, "base_premium": 2800},
                {"id": 4, "label": "SUBSTANDARD", "min_score": 350, "max_score": 499,
                 "auto_approve": False, "auto_decline": False, "base_premium": 4500},
                {"id": 5, "label": "DECLINE", "min_score": 0, "max_score": 349,
                 "auto_approve": False, "auto_decline": True, "base_premium": 8000},
            ]
        },
        "direct_queries": [
            {
                "id": "pending_claims",
                "question": "Are there any pending aviation liability claims exceeding $1M?",
                "bands": [
                    {"return": True, "action": "REFER", "note": "Pending claims >$1M"}
                ]
            },
            {
                "id": "coverage_declined",
                "question": "Has aviation coverage been declined in the past 3 years?",
                "bands": [
                    {"return": True, "override": 5, "action": "DECLINE", "note": "Prior declination"}
                ]
            },
        ],
        "categorical_features": {
            "operator_type": [
                {"cat": "MAJOR_AIRLINE", "label": "Major Airline", "modifier": 0.85},
                {"cat": "CHARTER_OPERATOR", "label": "Charter Operator", "modifier": 1.25},
            ],
            "fleet_size": [
                {"cat": "LARGE", "label": "Large Fleet (51-150)", "modifier": 0.95},
                {"cat": "SMALL", "label": "Small Fleet (6-20)", "modifier": 1.10},
            ],
        },
        "signal_groups": [
            {"id": "safety_record", "weight": 0.30, "score_condition": True,
             "bands": [{"max": 30, "override": 5, "action": "DECLINE", "note": "Unacceptable safety"}]},
            {"id": "regulatory_compliance", "weight": 0.20, "score_condition": False},
        ],
        "signal_features": {
            "safety_record": [
                {"id": "accident_history", "weight": 0.30, "score_condition": True,
                 "bands": [{"max": 25, "override": 5, "action": "DECLINE", "note": "Severe accidents"}]},
                {"id": "fatality_history", "weight": 0.20, "score_condition": True,
                 "bands": [{"max": 30, "override": 5, "action": "DECLINE", "note": "Fatal accidents"}]},
            ],
        },
    }

    print("=" * 70)
    print("DSI UTILITY FUNCTIONS - DEMO")
    print("=" * 70)

    # 1. TierAssigner
    print("\n1. TIER ASSIGNER")
    tier_util = get_utility("tier", "aerospace", "aerospace_general", sample_config)
    for score in [850, 720, 580, 420, 280]:
        result = tier_util.evaluate({"composite_score": score})
        print(f"   Score {score}: {result.category} ({result.action})")

    # 2. BooleanEvaluator
    print("\n2. BOOLEAN EVALUATOR")
    bool_util = get_utility("boolean", "aerospace", "aerospace_general", sample_config)
    results = bool_util.evaluate({"pending_claims": True, "coverage_declined": False})
    for r in results:
        print(f"   {r.category}: action={r.action}, override={r.override}")

    # 3. CategoricalFeatureEvaluator
    print("\n3. CATEGORICAL FEATURE EVALUATOR")
    cat_util = get_utility("categorical", "aerospace", "aerospace_general", sample_config)
    results = cat_util.evaluate({"operator_type": "MAJOR_AIRLINE", "fleet_size": "LARGE"})
    for r in results:
        print(f"   {r.category}: modifier={r.modifier}")

    # 4. ConditionEvaluator
    print("\n4. CONDITION EVALUATOR")
    cond_util = get_utility("condition", "aerospace", "aerospace_general", sample_config)
    results = cond_util.evaluate({"accident_history": 20, "fatality_history": 25})
    for r in results:
        print(f"   {r.category}: action={r.action}, override={r.override}")

    # 5. Summary
    print("\n5. SUMMARIZE DATA")
    all_results = {
        "boolean_results": [
            {"category": "pending_claims", "action": "REFER", "override": None, "criteria": ["Pending >$1M"]},
        ],
        "condition_results": [
            {"category": "accident_history", "action": "DECLINE", "override": 5, "criteria": ["Severe accidents"]},
        ],
    }
    summary = summarize_data(all_results)
    print(f"   Final action: {summary['final_action']}")
    print(f"   Max override: {summary['max_override']}")
    print(f"   Declines: {len(summary['declines'])}")
    print(f"   Refers: {len(summary['refers'])}")

    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
