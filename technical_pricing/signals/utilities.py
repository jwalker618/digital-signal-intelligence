"""
Model utility functions
These are standard functionalities required by all models - for example, how to allocate to a tier.

9 utility function types:
2. ConditionEvaluator - Band-based signal evaluation ##REVIEWED AND COMPLETED.
7. CompositeScoreCategorizer - Weighted composite scores ##REVIEWED AND COMPLETED
8. BooleanEvaluator - Yes/no responses to queries ##REVIEWED AND COMPLETED.
1. TierCategorizer - Score to tier mapping ##REVIEWED AND COMPLETED.



3. ModifierCalculator - Composite modifier from features
4. MajorityCategorizer - Dominant category from distribution
5. RateBenchmarkCategorizer - Compare rates vs benchmarks
6. QualityTierCategorizer - Quality tier assignment


9. ScoringLogicCategorizer - Discrete state to score mapping
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type, TypedDict

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
    override: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class SignalWeight(TypedDict):
    weight: float
    critical: bool
    critical_threshold: float

# =============================================================================
# CONFIGURATION PROFILES
# =============================================================================

MODIFIER_PROFILES: Dict[str, Dict[str, Dict[str, float]]] = {
    "marine": {
        "operator_type": {"MAJOR_LINER": 0.85, "REGIONAL_LINER": 0.92, "MAJOR_TANKER": 0.88, "INDEPENDENT_TANKER": 0.95, "MAJOR_BULK": 0.90, "TRAMP_OPERATOR": 1.05, "UNCATEGORIZED": 1.00},
        "vessel_category": {"container": 0.92, "tanker": 0.95, "bulk": 0.98, "lng": 0.90, "lpg": 0.92, "ro_ro": 1.02, "passenger": 1.08, "offshore": 1.05},
        "fleet_size": {"MICRO": 1.15, "SMALL": 1.10, "MEDIUM": 1.00, "LARGE": 0.95, "MAJOR": 0.90, "MEGA": 0.85},
        "flag_state_quality": {"WHITE": 0.95, "GREY": 1.05, "BLACK": 1.25},
    },
    "aerospace": {
        "operator_type": {"MAJOR_SCHEDULED": 0.82, "REGIONAL_SCHEDULED": 0.90, "LOW_COST_CARRIER": 0.92, "CHARTER_PASSENGER": 1.00, "CARGO_MAJOR": 0.88, "CARGO_REGIONAL": 0.95, "BUSINESS_AVIATION": 1.05, "HELICOPTER_OPERATOR": 1.12, "UNCATEGORIZED": 1.00},
        "fleet_size": {"MICRO": 1.20, "SMALL": 1.12, "MEDIUM": 1.00, "LARGE": 0.92, "MAJOR": 0.88, "MEGA": 0.82},
        "regulatory_framework": {"FAA": 0.92, "EASA": 0.90, "TCCA": 0.92, "CASA": 0.93, "OTHER": 1.08},
        "iosa_status": {"REGISTERED": 0.90, "EXPIRED": 1.05, "NEVER_REGISTERED": 1.12, "NOT_APPLICABLE": 1.00},
    },
    "cyber": {
        "employee_count": {"SMALL": 1.08, "MEDIUM": 1.00, "LARGE": 0.98, "ENTERPRISE": 0.95, "MAJOR_ENTERPRISE": 0.92},
        "industry_classification": {"HEALTHCARE": 1.15, "FINANCIAL_SERVICES": 1.12, "RETAIL_ECOMMERCE": 1.08, "TECHNOLOGY": 0.95, "MANUFACTURING": 1.00, "PROFESSIONAL_SERVICES": 0.98, "EDUCATION": 1.05, "OTHER": 1.00},
    },
    "d_and_o": {
        "company_type": {"PRIVATE_VENTURE_BACKED": 1.12, "PRIVATE_PE_BACKED": 1.08, "PRIVATE_FAMILY": 0.95, "PUBLIC_NYSE": 1.00, "PUBLIC_NASDAQ": 1.02, "PUBLIC_OTC": 1.15, "NON_PROFIT": 0.92, "SPAC": 1.25},
        "industry_classification": {"TECHNOLOGY": 1.10, "HEALTHCARE_PHARMA": 1.15, "FINANCIAL_SERVICES": 1.12, "MANUFACTURING": 0.95, "RETAIL": 1.00, "ENERGY": 1.08, "OTHER": 1.00},
    },
    "financial_institutions": {
        "asset_size": {"COMMUNITY": 1.08, "REGIONAL": 1.00, "SUPER_REGIONAL": 0.95, "LARGE": 0.90, "GSIB": 0.85},
        "institution_type": {"COMMERCIAL_BANK": 0.95, "CREDIT_UNION": 0.92, "INVESTMENT_BANK": 1.08, "BROKER_DEALER": 1.12, "FINTECH": 1.15, "CRYPTO_EXCHANGE": 1.30, "PAYMENT_PROCESSOR": 1.08, "BHC": 0.98},
    },
    "energy": {
        "operator_type": {"SUPER_MAJOR": 0.82, "MAJOR_IOC": 0.88, "LARGE_INDEPENDENT": 0.92, "MID_INDEPENDENT": 1.00, "SMALL_INDEPENDENT": 1.08, "NOC": 0.90, "SERVICE_COMPANY": 1.02},
        "operation_segment": {"UPSTREAM_CONVENTIONAL": 1.00, "UPSTREAM_UNCONVENTIONAL": 1.08, "UPSTREAM_OFFSHORE_DEEP": 1.15, "MIDSTREAM_PIPELINE": 0.92, "DOWNSTREAM_REFINING": 1.00, "RENEWABLES": 0.88},
    },
    "professional_indemnity": {
        "profession_type": {"ACCOUNTANT_BIG4": 0.85, "ACCOUNTANT_NATIONAL": 0.92, "ACCOUNTANT_REGIONAL": 1.00, "LAWYER_AMLAW50": 0.88, "LAWYER_AMLAW100": 0.92, "LAWYER_REGIONAL": 1.00, "LAWYER_BOUTIQUE": 1.05, "ARCHITECT_LARGE": 0.95, "ARCHITECT_SMALL": 1.08, "ENGINEER_LARGE": 0.95, "ENGINEER_SMALL": 1.08},
        "employee_count": {"SOLO": 1.15, "SMALL_FIRM": 1.08, "MID_FIRM": 1.00, "LARGE_FIRM": 0.95, "MAJOR_FIRM": 0.92},
    },
}

QUALITY_TIER_PROFILES: Dict[str, List[Dict[str, Any]]] = {
    "auditor": [
        {"tier": "BIG_4", "score": 95, "entities": ["deloitte", "pwc", "pricewaterhousecoopers", "ey", "ernst & young", "kpmg"]},
        {"tier": "NATIONAL", "score": 85, "entities": ["bdo", "rsm", "grant thornton", "crowe", "cbiz", "moss adams"]},
        {"tier": "REGIONAL", "score": 75, "entities": []},
        {"tier": "LOCAL", "score": 65, "entities": []},
    ],
    "classification_society": [
        {"tier": "TOP_IACS", "score": 95, "entities": ["lloyd's register", "dnv", "bureau veritas", "abs", "american bureau of shipping"]},
        {"tier": "IACS_MEMBER", "score": 88, "entities": ["class nk", "rina", "ccs", "korean register", "indian register"]},
        {"tier": "RECOGNIZED", "score": 75, "entities": []},
        {"tier": "OTHER", "score": 60, "entities": []},
    ],
    "p_and_i_club": [
        {"tier": "IG_TOP", "score": 95, "entities": ["gard", "britannia", "uk club", "north", "standard club", "west of england", "skuld"]},
        {"tier": "IG_MEMBER", "score": 88, "entities": ["american club", "japan club", "london club", "swedish club"]},
        {"tier": "QUALITY_FIXED", "score": 78, "entities": []},
        {"tier": "STANDARD", "score": 68, "entities": []},
    ],
    "credit_rating": [
        {"tier": "INVESTMENT_GRADE_HIGH", "score": 95, "entities": ["aaa", "aa+", "aa", "aa-"]},
        {"tier": "INVESTMENT_GRADE_MID", "score": 88, "entities": ["a+", "a", "a-"]},
        {"tier": "INVESTMENT_GRADE_LOW", "score": 78, "entities": ["bbb+", "bbb", "bbb-"]},
        {"tier": "SPECULATIVE_HIGH", "score": 65, "entities": ["bb+", "bb", "bb-"]},
        {"tier": "SPECULATIVE_LOW", "score": 35, "entities": ["b+", "b", "b-", "ccc+", "ccc"]},
        {"tier": "DEFAULT", "score": 15, "entities": ["d", "rd", "sd"]},
    ],
    "security_vendors": [
        {"tier": "TIER_1", "score": 92, "entities": ["crowdstrike", "palo alto", "fortinet", "cisco", "microsoft", "sentinelone", "zscaler", "okta"]},
        {"tier": "TIER_2", "score": 80, "entities": ["sophos", "trend micro", "mcafee", "symantec", "checkpoint", "proofpoint"]},
        {"tier": "REGIONAL", "score": 68, "entities": []},
        {"tier": "UNKNOWN", "score": 55, "entities": []},
    ],
}

SCORING_LOGIC_PROFILES: Dict[str, Dict[str, float]] = {
    "accident_history_5yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 50, "MAJOR_2_PLUS": 25, "FATAL": 10},
    "enforcement_actions_3yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 45, "MAJOR_2_PLUS": 20, "CONSENT_ORDER": 15},
    "capital_ratio_status": {"WELL_CAPITALIZED": 100, "ADEQUATELY_CAPITALIZED": 80, "UNDERCAPITALIZED": 50, "CRITICALLY_UNDERCAPITALIZED": 10},
    "breach_history_3yr": {"NONE": 100, "MINOR_1": 85, "MINOR_2_PLUS": 70, "MAJOR_1": 50, "MAJOR_2_PLUS": 25, "REGULATORY_NOTIFICATION": 40},
    "psc_detention_status": {"NONE_3YR": 100, "DETAINED_1_3YR": 75, "DETAINED_2_3YR": 55, "DETAINED_3_PLUS_3YR": 30, "BANNED": 5},
    "dark_activity_status": {"NONE": 100, "BRIEF_COASTAL": 90, "EXTENDED_COASTAL": 75, "OPEN_WATER_MINOR": 55, "OPEN_WATER_MAJOR": 25, "STS_SUSPECTED": 15},
    "iosa_status": {"REGISTERED_CURRENT": 100, "REGISTERED_RENEWAL_PENDING": 90, "EXPIRED_LESS_6MO": 70, "EXPIRED_6MO_PLUS": 45, "NEVER_REGISTERED_APPLICABLE": 30, "NOT_APPLICABLE": 75},
    "class_status": {"IN_CLASS_NO_CONDITIONS": 100, "IN_CLASS_MINOR_CONDITIONS": 85, "IN_CLASS_MAJOR_CONDITIONS": 60, "SUSPENDED": 25, "WITHDRAWN": 10, "NO_CLASS": 5},
    "malpractice_claims_5yr": {"NONE": 100, "CLAIM_1_NO_PAYMENT": 90, "CLAIM_1_WITH_PAYMENT": 75, "CLAIMS_2_3": 55, "CLAIMS_4_PLUS": 30, "LICENSE_ACTION": 15},
}

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

@register_utility
class ModifierCalculator(UtilityFunction):
    """Calculates composite modifier from multiple categorical features."""

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        coverage_modifiers = MODIFIER_PROFILES.get(self.coverage, {})
        if not coverage_modifiers:
            return UtilityResult(modifier=1.0, criteria=[f"No modifier profile for {self.coverage}"], confidence=0.0)

        composite_modifier = 1.0
        applied_modifiers = []
        criteria = []

        for feature_name, feature_value in data.items():
            if feature_name in coverage_modifiers:
                feature_modifiers = coverage_modifiers[feature_name]
                if feature_value in feature_modifiers:
                    mod = feature_modifiers[feature_value]
                    composite_modifier *= mod
                    applied_modifiers.append({"feature": feature_name, "value": feature_value, "modifier": mod})
                    criteria.append(f"{feature_name}={feature_value} -> {mod}")

        return UtilityResult(modifier=round(composite_modifier, 4), criteria=criteria, confidence=1.0 if applied_modifiers else 0.5, metadata={"applied_modifiers": applied_modifiers})


@register_utility
class MajorityCategorizer(UtilityFunction):
    """Determines the dominant category from a distribution."""

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        distribution = data.get("distribution", {})
        if not distribution:
            return UtilityResult(category="UNKNOWN", criteria=["No distribution provided"], confidence=0.0)

        total = sum(distribution.values())
        if total == 0:
            return UtilityResult(category="EMPTY", criteria=["Distribution sums to zero"], confidence=0.0)

        max_count = max(distribution.values())
        max_categories = [cat for cat, count in distribution.items() if count == max_count]

        if len(max_categories) == 1:
            majority_category = max_categories[0]
            majority_pct = (max_count / total) * 100
            return UtilityResult(
                category=majority_category, score=majority_pct,
                criteria=[f"{majority_category} is majority with {majority_pct:.1f}%"],
                confidence=1.0 if majority_pct > 50 else 0.8,
                metadata={"distribution": distribution, "total": total, "majority_pct": majority_pct}
            )
        else:
            return UtilityResult(category="MIXED", criteria=[f"Tie between: {', '.join(max_categories)}"], confidence=0.7, metadata={"tied_categories": max_categories})


@register_utility
class RateBenchmarkCategorizer(UtilityFunction):
    """Compares rates against industry benchmarks."""
    
    BENCHMARK_BANDS = [
        {"max_pct": 50, "score": 100, "label": "EXCELLENT"},
        {"max_pct": 75, "score": 85, "label": "GOOD"},
        {"max_pct": 100, "score": 70, "label": "AVERAGE"},
        {"max_pct": 150, "score": 50, "label": "BELOW_AVERAGE"},
        {"max_pct": 200, "score": 30, "label": "POOR"},
        {"max_pct": float("inf"), "score": 15, "label": "CRITICAL"},
    ]

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        actual = data.get("actual_rate")
        benchmark = data.get("benchmark_rate")

        if actual is None or benchmark is None:
            return UtilityResult(category="UNKNOWN", score=50, criteria=["Missing actual_rate or benchmark_rate"], confidence=0.0)

        if benchmark == 0:
            return UtilityResult(category="UNKNOWN", score=50, criteria=["Benchmark rate is zero"], confidence=0.0)

        pct_of_benchmark = (actual / benchmark) * 100

        for band in self.BENCHMARK_BANDS:
            if pct_of_benchmark <= band["max_pct"]:
                return UtilityResult(
                    category=band["label"], score=band["score"],
                    criteria=[f"Rate is {pct_of_benchmark:.1f}% of benchmark ({band['label']})"],
                    confidence=1.0, metadata={"actual_rate": actual, "benchmark_rate": benchmark, "pct_of_benchmark": pct_of_benchmark}
                )
        return UtilityResult(category="UNKNOWN", score=50, criteria=["Unable to categorize rate"], confidence=0.0)


@register_utility
class QualityTierCategorizer(UtilityFunction):
    """Assigns quality tiers based on entity identification."""

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        entity = data.get("entity", "").lower().strip()
        if not entity:
            return UtilityResult(category="UNKNOWN", score=50, criteria=["No entity provided"], confidence=0.0)

        profile = QUALITY_TIER_PROFILES.get(self.configuration)
        if not profile:
            return UtilityResult(category="UNKNOWN", score=50, criteria=[f"No quality tier profile for {self.configuration}"], confidence=0.0)

        for tier_def in profile:
            for known_entity in tier_def["entities"]:
                if known_entity.lower() in entity or entity in known_entity.lower():
                    return UtilityResult(
                        category=tier_def["tier"], score=tier_def["score"],
                        criteria=[f"Entity '{entity}' matched to {tier_def['tier']}"],
                        confidence=0.95, metadata={"matched_entity": known_entity}
                    )

        lowest_tier = profile[-1] if profile else None
        if lowest_tier:
            return UtilityResult(category=lowest_tier["tier"], score=lowest_tier["score"], criteria=[f"Entity '{entity}' assigned default tier"], confidence=0.6)
        return UtilityResult(category="UNKNOWN", score=50, criteria=[f"Unable to categorize entity '{entity}'"], confidence=0.0)

@register_utility
class ScoringLogicCategorizer(UtilityFunction):
    """Maps discrete states to scores based on predefined logic profiles."""

    def categorize(self, data: Dict[str, Any]) -> UtilityResult:
        state = data.get("state", "").upper()
        if not state:
            return UtilityResult(category="UNKNOWN", score=50, criteria=["No state provided"], confidence=0.0)

        profile = SCORING_LOGIC_PROFILES.get(self.configuration)
        if not profile:
            return UtilityResult(category="UNKNOWN", score=50, criteria=[f"No scoring logic profile for {self.configuration}"], confidence=0.0)

        score = profile.get(state)
        if score is not None:
            return UtilityResult(category=state, score=score, criteria=[f"{self.configuration} state '{state}' -> score {score}"], confidence=1.0, metadata={"profile": self.configuration, "state": state})

        available_states = list(profile.keys())
        return UtilityResult(category="UNKNOWN", score=50, criteria=[f"State '{state}' not found. Available: {available_states}"], confidence=0.0)


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def get_categorizer(categorizer_type: str, coverage: str, configuration: str, **kwargs: Any) -> UtilityFunction:
    """Factory function to instantiate utility functions."""
    type_mapping = {
        "tier": TierCategorizer,
        "condition": ConditionEvaluator,
        "modifier": ModifierCalculator,
        "majority": MajorityCategorizer,
        "rate_benchmark": RateBenchmarkCategorizer,
        "quality_tier": QualityTierCategorizer,
        "composite_score": CompositeScoreCategorizer,
        "boolean_flag": BooleanFlagCategorizer,
        "scoring_logic": ScoringLogicCategorizer,
    }

    categorizer_class = type_mapping.get(categorizer_type.lower())
    if not categorizer_class:
        raise ValueError(f"Unknown categorizer type '{categorizer_type}'. Available: {list(type_mapping.keys())}")

    return categorizer_class(coverage=coverage, configuration=configuration, **kwargs)


def list_available_profiles() -> Dict[str, List[str]]:
    """List all available configuration profiles."""
    return {
        "modifier_profiles": list(MODIFIER_PROFILES.keys()),
        "tier_profiles": list(TIER_PROFILES.keys()),
        "quality_tier_profiles": list(QUALITY_TIER_PROFILES.keys()),
        "condition_bands": list(CONDITION_BANDS.keys()),
        "signal_weight_profiles": list(SIGNAL_WEIGHT_PROFILES.keys()),
        "scoring_logic_profiles": list(SCORING_LOGIC_PROFILES.keys()),
    }


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CATEGORISERS MODULE - DEMONSTRATION")
    print("=" * 60)

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 1. TierCategorizer
    print("\n3. TierCategorizer (Score to Tier)")
    cat = get_categorizer("tier", "marine", "default")
    for score in [900, 750, 600, 450, 300]:
        result = cat.categorize({"score": score})
        print(f"   Score {score}: {result.category} (action={result.action})")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 2. ConditionEvaluator
    print("\n4. ConditionEvaluator (Safety Record)")
    cat = get_categorizer("condition", "marine", "safety_record_critical")
    for val in [15, 35, 55, 80]:
        result = cat.categorize({"value": val})
        print(f"   Safety score {val}: action={result.action}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 3. ModifierCalculator
    print("\n5. ModifierCalculator (Composite Marine Modifier)")
    cat = get_categorizer("modifier", "marine", "composite")
    data = {"operator_type": "MAJOR_LINER", "fleet_size": "LARGE", "flag_state_quality": "WHITE"}
    result = cat.categorize(data)
    print(f"   Features: {data}")
    print(f"   Composite modifier: {result.modifier}")

    ### DELETE = THIS IS A AGGREGATOR
    # 4. MajorityCategorizer
    print("\n6. MajorityCategorizer (Vessel Category)")
    cat = get_categorizer("majority", "marine", "vessel_category")
    result = cat.categorize({"distribution": {"container": 45, "bulk": 15, "tanker": 10}})
    print(f"   Majority: {result.category} ({result.score:.1f}%)")

    #### I DONT KNOW ABOUT THIS ONE YET
    # 6. QualityTierCategorizer
    print("\n7. QualityTierCategorizer (Auditor)")
    cat = get_categorizer("quality_tier", "financial_institutions", "auditor")
    for entity in ["Deloitte", "BDO USA", "Smith CPA"]:
        result = cat.categorize({"entity": entity})
        print(f"   '{entity}': {result.category} (score={result.score})")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 7. CompositeScoreCategorizer
    print("\n8. CompositeScoreCategorizer (Marine Signals)")
    cat = get_categorizer("composite_score", "marine", "default")
    signals = {"safety_compliance": 85, "operational_telemetry": 78, "sanctions_compliance": 92, "financial_stability": 70}
    result = cat.categorize({"signals": signals})
    print(f"   Composite score: {result.score}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 8. BooleanFlagCategorizer
    print("\n9. BooleanFlagCategorizer (IOSA Registered)")
    cat = get_categorizer("boolean_flag", "aerospace", "iosa_registered")
    for val in [True, False]:
        result = cat.categorize({"flag": val})
        print(f"   IOSA registered={val}: score={result.score}, modifier={result.modifier}")

    ### KEEP - THIS NEEDS ADJUSTMENT TO TAKE IN VALUES FROM CONFIG, BUT IS REQUIRED
    # 9. ScoringLogicCategorizer
    print("\n10. ScoringLogicCategorizer (PSC Detention)")
    cat = get_categorizer("scoring_logic", "marine", "psc_detention_status")
    for state in ["NONE_3YR", "DETAINED_1_3YR", "DETAINED_3_PLUS_3YR"]:
        result = cat.categorize({"state": state})
        print(f"    State '{state}': score={result.score}")
