"""
Model utility functions
Standard functionalities required by all model builds - for example, how to allocate to a tier.

4 utility function types, 1 factory function:

1. ConditionEvaluator - Band-based signal evaluation
2. CompositeScoreCategorizer - Weighted composite scores
3. BooleanEvaluator - Yes/no responses to queries
4. TierCategorizer - Score to tier mapping

5f. def_summarize_data - runs through data file and extracts final midifiers etc.

"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypedDict, Iterable, Union

UTILITY_REGISTRY: Dict[str, Type["UtilityFunction"]] = {}

def register_utility(cls: Type["UtilityFunction"]) -> Type["UtilityFunction"]:
    UTILITY_REGISTRY[cls.__name__] = cls
    return cls

@dataclass
class UtilityResult:
    """Standardised result from any utility function."""
    category: Optional[str] = None
    score: Optional[float] = None
    modifier: Optional[float] = None
    criteria: List[str] = field(default_factory=list)
    action: Optional[str] = None
    override: Optional[int] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class SignalWeight(TypedDict):
    weight: float
    critical: bool
    critical_threshold: float

# =============================================================================
# BASE UTILITY CLASS
# =============================================================================

class UtilityFunction(ABC):
    """Abstract base class for all categorisers."""

    def __init__(self, coverage: str, cov_configuration: str, configuration: Dict[str, Any], **kwargs: Any):
        self.coverage = coverage                     # the actual coverage cohort, eg aerospace. 
        self.cov_configuration = cov_configuration   # the specific configuration file header under that coverage, eg aerospace_general
        self.configuration = configuration           # the specific configuration under the file header
        self.kwargs = kwargs

    @abstractmethod
    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        raise NotImplementedError

# =============================================================================
# UTILITY IMPLEMENTATIONS
# =============================================================================

@register_utility
class ConditionEvaluator(UtilityFunction):
    # Evaluates signal values against condition bands.

    def categorize(self, data: Dict[str, Any]) -> List[UtilityResult]:
        results: List[UtilityResult] = []

        group_defs: List[Dict[str, Any]] = self.configuration.get("signal_groups", [])
        feature_defs_map: Dict[str, List[Dict[str, Any]]] = self.configuration.get("signal_features", {})

        def match_band(score: Any, bands: List[Dict[str, Any]], inclusive_max: bool) -> Optional[Dict[str, Any]]:
            """Return the first matching band for the given score, honoring inclusive/exclusive max."""
            if score is None or not isinstance(score, (int, float)):
                return None

            # Sort bands by 'max' ascending for deterministic behavior.
            sorted_bands = sorted(bands, key=lambda b: b.get("max", float("inf")))
            for b in sorted_bands:
                max_val = b.get("max")
                if max_val is None:
                    return b
                if inclusive_max:
                    if score <= max_val:
                        return b
                else:
                    if score < max_val:
                        return b
            return None

        # Evaluate group-level signals 
        for group_def in group_defs:
            group_id = group_def.get("id")
            if not group_id:
                continue  # skip malformed entries

            score_condition = group_def.get("score_condition")
            # Only evaluate when the score_condition is explicitly True
            if score_condition is True:
                group_score = data.get(group_id)  # score is under the same ID in data
                bands = group_def.get("bands", [])
                inclusive_max = bool(group_def.get("inclusive_max", False))

                band = match_band(group_score, bands, inclusive_max)
                if band:
                    results.append(
                        UtilityResult(
                            category: group_id,
                            modifier: band.get("modifier"),
                            criteria: group_score,
                            action: band.get("action", "UNKNOWN),
                            override: band.get("override"),
                            confidence: float = 1.0,
                            metadata: {"group_def": bands}       
                        )
                    )

            # Always proceed to evaluate underlying features for this group (if any)
            for feature_def in feature_defs_map.get(group_id, []):
                feat_id = feature_def.get("id")
                if not feat_id:
                    continue

                feat_score_condition = feature_def.get("score_condition")
                if feat_score_condition is True:
                    feat_score = data.get(feat_id)
                    feat_bands = feature_def.get("bands", [])
                    feat_inclusive_max = bool(feature_def.get("inclusive_max", False))

                    feat_band = match_band(feat_score, feat_bands, feat_inclusive_max)
                    if feat_band:
                        results.append(
                            UtilityResult(
                                category: feat_id,
                                modifier: feat_band.get("modifier"),
                                criteria: feat_score,
                                action: feat_band.get("action", "UNKNOWN),
                                override: feat_band.get("override"),
                                confidence: float = 1.0,
                                metadata: {"group_def": feat_band} 
                            )
                        )

        return results

@register_utility
class CompositeScoreCategorizer(UtilityFunction):
    # Calculates weighted composite scores from signal groups.

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:

        group_defs: List[Dict[str, Any]] = self.configuration.get("signal_groups", [])
        feature_defs_map: Dict[str, List[Dict[str, Any]]] = self.configuration.get("signal_features", {})

        total_sum = 0.0
        group_sum = 0.0
        signal_contributions = []
        
        # Evaluate group-level signals
        for group_def in group_defs:
            group_id = group_def.get("id")
    
            for feature_def in feature_defs_map.get(group_id, []):
                signal_contributions.append(
                    {
                        "signal_group": group_id,
                        "signal_feature": feature_def.get("id"), 
                        "score": data.get("id"), 
                        "weight": feature_def.get("weight"), 
                        "contribution": data.get("id") * feature_def.get("weight")
                    }
                )
                #update running total 
                group_sum += ( data.get("id") * feature_def.get("weight") )

            #capture final group value
            signal.contributions.append(
                {
                    "signal_group": group_id,
                    "signal_feature": null,
                    "score": group_sum,
                    "weight": group_def.get("weight"),
                    "contribution": group_sum * group_def.get("weight")
                }
            )
            total_sum += ( group_sum * group_def.get("weight") )
            group_sum = 0.0

        return UtilityResult(
            composite_score=round(total_sum, 2),
            metadata={"signal_contributions": signal_contributions}
        )

@register_utility
class BooleanEvaluator(UtilityFunction):
    """Evaluates boolean returns."""

    def categorize(self, data: Dict[str, Any]) -> List[UtilityResult]:

        results: List[UtilityResult] = []
    
        queries: List[Dict[str, Any]] = self.configuration.get("direct_queries",[])

        for q in queries:
            qid: Optional[str] = q.get("id")
            if not qid:
                continue #malformed

            resp = data.get(qid)
            if resp is None:
                continue
            if not isinstance(resp, bool):
                continue

            bands: List[Dict[str, Any]] = q.get("bands",[])

            matched_band: Optional[Dict[str, Any]] = next(
                (b for b in bands if b.get("return") is resp),
                None
            )

            if matched_band:
                results.append(
                    UtilityResult(
                        category: qid
                        modifier: matched_band.get("modifier")
                        criteria: resp
                        action: matched_band.get("action", "UNKNOWN")
                        override: matched_band.get("override")
                        confidence: float = 1.0
                        metadata: {"query_def": q}   
                    )
                )
        return results

@register_utility
class TierCategorizer(UtilityFunction):
    """Maps composite scores to tier assignments."""

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        composite_score = data.get("composite_score")
        if composite_score is None:
            return UtilityResult(category="UNKNOWN", action="REFER", criteria=["No score provided"], confidence=0.0)

        # grab the models tier definition
        tiers = configuration.get("tier_thresholds",{}).get("tiers", [])

        for tier_def in tiers:
            if tier_def["min_score"] <= composite_score <= tier_def["max_score"]:
                return UtilityResult(
                    category=tier_def["label"],
                    score=composite_score, 
                    criteria=[f"Composite Score {composite_score} in tier {tier_def['tier']}"], 
                    confidence=1.0,
                    metadata={"tier_def": tier_def}     
                )
                
        return UtiltyResult(category="UNKNOWN", score=composite_score, criteria=[f"Composite Score {composite_score} outside defined tiers"], confidence=0.5, metadata={})

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def _iter_results(data: Dict[str, Any]) -> Iterable[Any]:
    """
    Yield all result-like items (UtilityResult or dict-like) from any list in `data`.
    Ignores non-lists and non-result items.
    """
    for value in data.values():
        if isinstance(value, list):
            for item in value:
                # Accept UtilityResult or dict-like with expected keys
                if isinstance(item, UtilityResult):
                    yield item
                elif isinstance(item, dict):
                    yield item
                else:
                    # add more types here as required
                    pass

def summarize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    single-pass summary:
      - max_override: int | None
      - declines:    List[Dict[str, Any]]  (category, action, note)
      - refers:      List[Dict[str, Any]]  (category, action, override, note)
      - infos:       List[Dict[str, Any]]  (category, action, note)
      - modifiers:   List[Dict[str, Any]]  (category, action, note)
    """
    max_override: Optional[int] = None
    declines: List[Dict[str, Any]] = []
    refers: List[Dict[str, Any]] = []
    infos: List[Dict[str, Any]] = []
    modifiers: List[Dict[str, Any]] = []

    for raw in _iter_results(data):

        # update max_override
        ov = data["override"]
        if isinstance(ov, int):
            if max_override is None or ov > max_override:
                max_override = ov

        action = data["action"]
        if not isinstance(action, str):
            # If action isn't present, skip classification into action buckets.
            continue

        action_lower = action.lower()

        if action_lower == "decline":
            declines.append({
                "category": data["category"],
                "action": action,
                "note": data["note"],
            })
        elif action_lower == "refer":
            refers.append({
                "category": data["category"],
                "action": action,
                "override": ov,   # include override specifically for REFER
                "note": data["note"],
            })
        elif action_lower == "info":
            infos.append({
                "category": data["category"],
                "action": action,
                "note": data["note"],
            })
        elif action_lower == "modifier":
            modifiers.append({
                "category": data["category"],
                "action": action,
                "note": data["note"],
            })
        else:
            # Unknown or unneeded actions: ignore (or collect under 'others' if desired)
            pass

    return {
        "max_override": max_override,
        "declines": declines,
        "refers": refers,
        "infos": infos,
        "modifiers": modifiers,
        
def get_categorizer(categorizer_type: str, coverage: str, cov_configuration: str, configuration: Dict[str, Any], **kwargs: Any) -> UtilityFunction:
    """Factory function to instantiate utility functions."""
    type_mapping = {
        "condition": ConditionEvaluator,
        "composite_score": CompositeScoreCategorizer,
        "boolean": BooleanEvaluator,
        "tier": TierCategorizer,
    }

    categorizer_class = type_mapping.get(categorizer_type.lower())
    if not categorizer_class:
        raise ValueError(f"Unknown categorizer type '{categorizer_type}'. Available: {list(type_mapping.keys())}")

    return categorizer_class(coverage=coverage, configuration=configuration, **kwargs)

# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":

    tier_data = {
        "tier_thresholds" [
            "tiers": [
                {"id": 1, "label": "PREFERRED", "min_score": 800, "max_score": 1000},
                {"id": 2, "label": "STANDARD_PLUS", "min_score": 650, "max_score": 799},
                {"id": 3, "label": "STANDARD", "min_score": 500, "max_score": 649},
                {"id": 4, "label": "SUBSTANDARD", "min_score": 350, "max_score": 499},
                {"id": 5, "label": "DECLINE", "min_score": 0, "max_score": 349},
            ]
        ]
    }
    
    # 4. TierCategorizer
    print("\n3. TierCategorizer (Score to Tier)")
    cat = get_categorizer("tier", "aerospace", "aerospace_general", tier_data)
    for score in [900, 750, 600, 450, 300]:
        result = cat.categorize({"score": score})
        print(f"   Score {score}: {result.category} (action={result.action})")

    # 5f summarize_data
    summarydata = {
        "funcA": [
            {"category": "regulatory_action", "override": 5, "action": "DECLINE", "note": "Test profiles"},
            {"category": "pending_claims", "override": None, "action": "REFER", "note": ">$1M pending"},
        ],
        "funcB": [
            {"category": "safety_record", "override": 4, "action": "REFER", "note": "Incidents > threshold"},
            {"category": "incident_history", "override": None, "action": "INFO", "note": "Reported minor events"},
        ],
        "funcC": [
            {"category": "sanctions", "override": 5, "action": "DECLINE", "note": "Sanctions hit"},
            {"category": "pilot_hours", "override": None, "action": "MODIFIER", "note": "Low hours modifier applied"},
        ],
    }
    
    summary = summarize(summarydata)
    
    print(summary["max_override"])  # -> 5
    
    print("DECLINES:", summary["declines"])
    # [{'category': 'sanctions', 'action': 'DECLINE', 'note': 'Sanctions hit'}]
    
    print("REFERS:", summary["refers"])
    # [
    #   {'category': 'pending_claims', 'action': 'REFER', 'override': None, 'note': '>$1M pending'},
    #   {'category': 'safety_record',  'action': 'REFER', 'override': 4,    'note': 'Incidents > threshold'}
    # ]
    
    print("INFOS:", summary["infos"])
    # [{'category': 'incident_history', 'action': 'INFO', 'note': 'Reported minor events'}]
    
    print("MODIFIERS:", summary["modifiers"])
    # [{'category': 'pilot_hours', 'action': 'MODIFIER', 'note': 'Low hours modifier applied'}]    
