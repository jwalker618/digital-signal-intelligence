"""
Signal Categorizers

Pure, stateless mappers that categorise signal values and infer categorical features.
These are NOT utility functions - they do NOT apply modifiers, weights, or tier logic.

Design Principles:
1. NO hardcoded profiles - all thresholds/mappings passed at call time or from config
2. Stateless - same input always produces same output
3. Return categories and scores, NOT modifiers (modifiers come from config via utilities)
4. Work on signals or categorical features only

Categorizer Types:
1. ThresholdCategorizer - Numeric value → category based on threshold bands
2. StateCategorizer - Discrete state → category mapping
3. EntityRecognizer - Entity name → quality tier via fuzzy matching
4. RatioCategorizer - Value vs benchmark → performance category
5. DistributionCategorizer - Distribution → majority/dominant category
6. BinaryCategorizer - Boolean → category

Usage:
    Categorizers receive threshold/mapping definitions at call time (from config),
    NOT from hardcoded internal profiles.
    
    Example:
        bands = config["signal_features"]["safety_record"][0]["threshold_bands"]
        result = ThresholdCategorizer.categorize(value=8.5, bands=bands)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple, Union
from enum import Enum


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class CategorizationResult:
    """
    Standardized result from any categorizer.
    
    Note: Does NOT include modifiers - those come from config and are
    applied by utility functions after categorization.
    """
    category: str
    score: Optional[float] = None          # 0-100 normalized score
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "score": self.score,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


# =============================================================================
# THRESHOLD CATEGORIZER
# =============================================================================

class ThresholdCategorizer:
    """
    Categorizes numeric values into bands based on thresholds.
    
    Bands are passed at call time (from config), not hardcoded.
    
    Expected band format (from config):
    [
        {"max": 5, "category": "EXCELLENT", "score": 95},
        {"max": 10, "category": "GOOD", "score": 82},
        {"max": 15, "category": "AVERAGE", "score": 68},
        {"max": 20, "category": "BELOW_AVERAGE", "score": 50},
        {"max": null, "category": "POOR", "score": 30}  # null = infinity
    ]
    """
    
    @staticmethod
    def categorize(
        value: Optional[float],
        bands: List[Dict[str, Any]],
        inclusive_max: bool = True,
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Categorize a numeric value based on threshold bands.
        
        Args:
            value: The numeric value to categorize
            bands: List of band definitions from config (sorted by max ascending)
            inclusive_max: If True, value <= max matches; if False, value < max
            unknown_category: Category to return if value is None
            unknown_score: Score to return if value is None
        
        Returns:
            CategorizationResult with category and score
        """
        if value is None:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["No value provided"]
            )
        
        if not isinstance(value, (int, float)):
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=[f"Invalid value type: {type(value).__name__}"]
            )
        
        # Sort bands by max value (handle None as infinity)
        sorted_bands = sorted(
            bands,
            key=lambda b: float('inf') if b.get("max") is None else b.get("max", float('inf'))
        )
        
        for band in sorted_bands:
            max_val = band.get("max")
            
            # None means no upper limit (infinity)
            if max_val is None:
                return CategorizationResult(
                    category=band.get("category", "UNKNOWN"),
                    score=band.get("score"),
                    confidence=1.0,
                    evidence=[f"Value {value} in band (>{sorted_bands[-2].get('max') if len(sorted_bands) > 1 else 0})"],
                    metadata={"band": band, "value": value}
                )
            
            # Check if value falls in this band
            if inclusive_max:
                if value <= max_val:
                    return CategorizationResult(
                        category=band.get("category", "UNKNOWN"),
                        score=band.get("score"),
                        confidence=1.0,
                        evidence=[f"Value {value} <= {max_val}"],
                        metadata={"band": band, "value": value}
                    )
            else:
                if value < max_val:
                    return CategorizationResult(
                        category=band.get("category", "UNKNOWN"),
                        score=band.get("score"),
                        confidence=1.0,
                        evidence=[f"Value {value} < {max_val}"],
                        metadata={"band": band, "value": value}
                    )
        
        # Value outside all bands
        return CategorizationResult(
            category="OUT_OF_RANGE",
            score=unknown_score,
            confidence=0.5,
            evidence=[f"Value {value} outside defined bands"]
        )


# =============================================================================
# STATE CATEGORIZER
# =============================================================================

class StateCategorizer:
    """
    Maps discrete states to categories and scores.
    
    State mapping passed at call time (from config), not hardcoded.
    
    Expected mapping format (from config):
    {
        "ACTIVE": {"category": "ACTIVE", "score": 100},
        "ACTIVE_WITH_RESTRICTIONS": {"category": "RESTRICTED", "score": 70},
        "SUSPENDED": {"category": "SUSPENDED", "score": 20},
        "REVOKED": {"category": "REVOKED", "score": 5}
    }
    """
    
    @staticmethod
    def categorize(
        state: Optional[str],
        state_mapping: Dict[str, Dict[str, Any]],
        case_sensitive: bool = False,
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Categorize a discrete state value.
        
        Args:
            state: The state value to categorize
            state_mapping: Dict mapping states to category/score from config
            case_sensitive: Whether to match case-sensitively
            unknown_category: Category for unrecognized states
            unknown_score: Score for unrecognized states
        
        Returns:
            CategorizationResult with category and score
        """
        if state is None:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["No state provided"]
            )
        
        # Normalize state for matching
        lookup_state = state if case_sensitive else state.upper().strip()
        
        # Build normalized mapping if case-insensitive
        if case_sensitive:
            normalized_mapping = state_mapping
        else:
            normalized_mapping = {
                k.upper().strip(): v for k, v in state_mapping.items()
            }
        
        if lookup_state in normalized_mapping:
            mapping = normalized_mapping[lookup_state]
            return CategorizationResult(
                category=mapping.get("category", lookup_state),
                score=mapping.get("score"),
                confidence=1.0,
                evidence=[f"State '{state}' mapped"],
                metadata={"original_state": state, "mapping": mapping}
            )
        
        return CategorizationResult(
            category=unknown_category,
            score=unknown_score,
            confidence=0.0,
            evidence=[f"State '{state}' not in mapping"],
            metadata={"available_states": list(state_mapping.keys())}
        )


# =============================================================================
# ENTITY RECOGNIZER
# =============================================================================

class EntityRecognizer:
    """
    Recognizes entities and assigns quality tiers via fuzzy matching.
    
    Entity tiers passed at call time (from config), not hardcoded.
    
    Expected tier format (from config):
    [
        {"tier": "TIER_1", "score": 95, "entities": ["AerCap", "GECAS", "Avolon"]},
        {"tier": "TIER_2", "score": 80, "entities": ["BBAM", "NAC", "ACG"]},
        {"tier": "TIER_3", "score": 65, "entities": []},  # Default tier
    ]
    """
    
    @staticmethod
    def categorize(
        entity: Optional[str],
        tier_definitions: List[Dict[str, Any]],
        fuzzy_threshold: float = 0.8,
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Recognize an entity and assign quality tier.
        
        Args:
            entity: Entity name to recognize
            tier_definitions: List of tier definitions from config
            fuzzy_threshold: Minimum similarity for fuzzy matching (0-1)
            unknown_category: Category for unrecognized entities
            unknown_score: Score for unrecognized entities
        
        Returns:
            CategorizationResult with tier and score
        """
        if not entity or not isinstance(entity, str):
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["No entity provided"]
            )
        
        entity_lower = entity.lower().strip()
        
        # Try exact and substring matching in each tier
        for tier_def in tier_definitions:
            entities = tier_def.get("entities", [])
            
            for known_entity in entities:
                known_lower = known_entity.lower()
                
                # Exact match
                if entity_lower == known_lower:
                    return CategorizationResult(
                        category=tier_def.get("tier", "UNKNOWN"),
                        score=tier_def.get("score"),
                        confidence=1.0,
                        evidence=[f"Exact match: {known_entity}"],
                        metadata={"matched_entity": known_entity, "match_type": "exact"}
                    )
                
                # Substring match (entity contains known or vice versa)
                if entity_lower in known_lower or known_lower in entity_lower:
                    return CategorizationResult(
                        category=tier_def.get("tier", "UNKNOWN"),
                        score=tier_def.get("score"),
                        confidence=0.9,
                        evidence=[f"Substring match: {known_entity}"],
                        metadata={"matched_entity": known_entity, "match_type": "substring"}
                    )
        
        # Try fuzzy matching if no exact/substring match
        best_match = EntityRecognizer._fuzzy_match(entity_lower, tier_definitions, fuzzy_threshold)
        if best_match:
            tier_def, matched_entity, similarity = best_match
            return CategorizationResult(
                category=tier_def.get("tier", "UNKNOWN"),
                score=tier_def.get("score"),
                confidence=similarity,
                evidence=[f"Fuzzy match: {matched_entity} ({similarity:.0%})"],
                metadata={"matched_entity": matched_entity, "match_type": "fuzzy", "similarity": similarity}
            )
        
        # No match - return default tier (last tier with empty entities list) or unknown
        for tier_def in tier_definitions:
            if not tier_def.get("entities"):
                return CategorizationResult(
                    category=tier_def.get("tier", unknown_category),
                    score=tier_def.get("score", unknown_score),
                    confidence=0.5,
                    evidence=[f"Default tier for unrecognized entity: {entity}"],
                    metadata={"match_type": "default"}
                )
        
        return CategorizationResult(
            category=unknown_category,
            score=unknown_score,
            confidence=0.0,
            evidence=[f"Entity '{entity}' not recognized"]
        )
    
    @staticmethod
    def _fuzzy_match(
        entity: str,
        tier_definitions: List[Dict[str, Any]],
        threshold: float
    ) -> Optional[Tuple[Dict, str, float]]:
        """Simple fuzzy matching using character overlap ratio."""
        best_match = None
        best_similarity = threshold
        
        for tier_def in tier_definitions:
            for known_entity in tier_def.get("entities", []):
                known_lower = known_entity.lower()
                similarity = EntityRecognizer._similarity(entity, known_lower)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = (tier_def, known_entity, similarity)
        
        return best_match
    
    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """Calculate simple character-based similarity ratio."""
        if not s1 or not s2:
            return 0.0
        
        # Use set intersection for simple similarity
        set1, set2 = set(s1), set(s2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


# =============================================================================
# RATIO CATEGORIZER
# =============================================================================

class RatioCategorizer:
    """
    Categorizes a value relative to a benchmark (ratio/percentage).
    
    Bands passed at call time (from config), not hardcoded.
    
    Expected band format (from config):
    [
        {"max_pct": 50, "category": "EXCELLENT", "score": 98},
        {"max_pct": 80, "category": "GOOD", "score": 85},
        {"max_pct": 100, "category": "AVERAGE", "score": 70},
        {"max_pct": 150, "category": "BELOW_AVERAGE", "score": 50},
        {"max_pct": null, "category": "POOR", "score": 25}
    ]
    """
    
    @staticmethod
    def categorize(
        actual: Optional[float],
        benchmark: Optional[float],
        bands: List[Dict[str, Any]],
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Categorize a value relative to a benchmark.
        
        Args:
            actual: The actual value
            benchmark: The benchmark to compare against
            bands: List of percentage bands from config
            unknown_category: Category if values are missing
            unknown_score: Score if values are missing
        
        Returns:
            CategorizationResult with category and score
        """
        if actual is None or benchmark is None:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["Missing actual or benchmark value"]
            )
        
        if benchmark == 0:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["Benchmark is zero - cannot calculate ratio"]
            )
        
        pct_of_benchmark = (actual / benchmark) * 100
        
        # Sort bands by max_pct
        sorted_bands = sorted(
            bands,
            key=lambda b: float('inf') if b.get("max_pct") is None else b.get("max_pct", float('inf'))
        )
        
        for band in sorted_bands:
            max_pct = band.get("max_pct")
            
            if max_pct is None or pct_of_benchmark <= max_pct:
                return CategorizationResult(
                    category=band.get("category", "UNKNOWN"),
                    score=band.get("score"),
                    confidence=1.0,
                    evidence=[f"{pct_of_benchmark:.1f}% of benchmark"],
                    metadata={
                        "actual": actual,
                        "benchmark": benchmark,
                        "pct_of_benchmark": round(pct_of_benchmark, 2),
                        "band": band
                    }
                )
        
        return CategorizationResult(
            category="OUT_OF_RANGE",
            score=unknown_score,
            confidence=0.5,
            evidence=[f"Ratio {pct_of_benchmark:.1f}% outside defined bands"]
        )


# =============================================================================
# DISTRIBUTION CATEGORIZER
# =============================================================================

class DistributionCategorizer:
    """
    Analyzes a distribution to find the dominant/majority category.
    
    Useful for fleet composition, revenue mix, etc.
    """
    
    @staticmethod
    def categorize(
        distribution: Optional[Dict[str, float]],
        majority_threshold: float = 0.5,
        plurality_ok: bool = True
    ) -> CategorizationResult:
        """
        Find the dominant category in a distribution.
        
        Args:
            distribution: Dict mapping category to count/percentage
            majority_threshold: Minimum fraction for "majority" (default 50%)
            plurality_ok: If True, return largest even if below majority threshold
        
        Returns:
            CategorizationResult with dominant category
        """
        if not distribution:
            return CategorizationResult(
                category="UNKNOWN",
                score=None,
                confidence=0.0,
                evidence=["No distribution provided"]
            )
        
        total = sum(distribution.values())
        if total == 0:
            return CategorizationResult(
                category="EMPTY",
                score=None,
                confidence=0.0,
                evidence=["Distribution sums to zero"]
            )
        
        # Find maximum
        max_count = max(distribution.values())
        max_categories = [cat for cat, count in distribution.items() if count == max_count]
        max_fraction = max_count / total
        
        # Single clear winner
        if len(max_categories) == 1:
            category = max_categories[0]
            
            if max_fraction >= majority_threshold:
                return CategorizationResult(
                    category=category,
                    score=max_fraction * 100,
                    confidence=1.0,
                    evidence=[f"{category} is majority ({max_fraction:.1%})"],
                    metadata={"distribution": distribution, "fraction": max_fraction}
                )
            elif plurality_ok:
                return CategorizationResult(
                    category=category,
                    score=max_fraction * 100,
                    confidence=0.8,
                    evidence=[f"{category} is plurality ({max_fraction:.1%})"],
                    metadata={"distribution": distribution, "fraction": max_fraction}
                )
            else:
                return CategorizationResult(
                    category="MIXED",
                    score=max_fraction * 100,
                    confidence=0.6,
                    evidence=[f"No majority (largest: {category} at {max_fraction:.1%})"],
                    metadata={"distribution": distribution, "largest": category}
                )
        
        # Tie between multiple categories
        return CategorizationResult(
            category="MIXED",
            score=max_fraction * 100,
            confidence=0.5,
            evidence=[f"Tie between: {', '.join(max_categories)}"],
            metadata={"distribution": distribution, "tied_categories": max_categories}
        )


# =============================================================================
# BINARY CATEGORIZER
# =============================================================================

class BinaryCategorizer:
    """
    Categorizes boolean values.
    
    Category names passed at call time (from config), not hardcoded.
    """
    
    @staticmethod
    def categorize(
        value: Optional[bool],
        true_category: str = "YES",
        false_category: str = "NO",
        true_score: Optional[float] = None,
        false_score: Optional[float] = None,
        unknown_category: str = "UNKNOWN"
    ) -> CategorizationResult:
        """
        Categorize a boolean value.
        
        Args:
            value: Boolean to categorize
            true_category: Category name for True
            false_category: Category name for False
            true_score: Optional score for True
            false_score: Optional score for False
            unknown_category: Category for None/missing
        
        Returns:
            CategorizationResult with category
        """
        if value is None:
            return CategorizationResult(
                category=unknown_category,
                score=None,
                confidence=0.0,
                evidence=["No value provided"]
            )
        
        if not isinstance(value, bool):
            # Try to coerce
            value = bool(value)
        
        if value:
            return CategorizationResult(
                category=true_category,
                score=true_score,
                confidence=1.0,
                evidence=[f"Value is True → {true_category}"],
                metadata={"raw_value": True}
            )
        else:
            return CategorizationResult(
                category=false_category,
                score=false_score,
                confidence=1.0,
                evidence=[f"Value is False → {false_category}"],
                metadata={"raw_value": False}
            )


# =============================================================================
# COUNT CATEGORIZER
# =============================================================================

class CountCategorizer:
    """
    Categorizes count/quantity values into bands.
    
    Similar to ThresholdCategorizer but specifically for discrete counts.
    Bands passed at call time (from config).
    
    Expected band format:
    [
        {"min": 0, "max": 0, "category": "NONE", "score": 100},
        {"min": 1, "max": 2, "category": "FEW", "score": 80},
        {"min": 3, "max": 5, "category": "MODERATE", "score": 60},
        {"min": 6, "max": null, "category": "MANY", "score": 35}
    ]
    """
    
    @staticmethod
    def categorize(
        count: Optional[int],
        bands: List[Dict[str, Any]],
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Categorize a count value into bands.
        
        Args:
            count: The count to categorize
            bands: List of count bands from config
            unknown_category: Category for missing count
            unknown_score: Score for missing count
        
        Returns:
            CategorizationResult with category and score
        """
        if count is None:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["No count provided"]
            )
        
        if not isinstance(count, (int, float)):
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=[f"Invalid count type: {type(count).__name__}"]
            )
        
        count = int(count)
        
        for band in bands:
            min_val = band.get("min", 0)
            max_val = band.get("max")
            
            # None means no upper limit
            if max_val is None:
                if count >= min_val:
                    return CategorizationResult(
                        category=band.get("category", "UNKNOWN"),
                        score=band.get("score"),
                        confidence=1.0,
                        evidence=[f"Count {count} >= {min_val}"],
                        metadata={"band": band, "count": count}
                    )
            else:
                if min_val <= count <= max_val:
                    return CategorizationResult(
                        category=band.get("category", "UNKNOWN"),
                        score=band.get("score"),
                        confidence=1.0,
                        evidence=[f"Count {count} in [{min_val}, {max_val}]"],
                        metadata={"band": band, "count": count}
                    )
        
        return CategorizationResult(
            category="OUT_OF_RANGE",
            score=unknown_score,
            confidence=0.5,
            evidence=[f"Count {count} outside defined bands"]
        )


# =============================================================================
# AGE CATEGORIZER
# =============================================================================

class AgeCategorizer:
    """
    Categorizes age values (fleet age, company age, etc.).
    
    Bands passed at call time (from config).
    Supports both "younger is better" and "older is better" modes.
    """
    
    @staticmethod
    def categorize(
        age: Optional[float],
        bands: List[Dict[str, Any]],
        younger_is_better: bool = True,
        unknown_category: str = "UNKNOWN",
        unknown_score: float = 50.0
    ) -> CategorizationResult:
        """
        Categorize an age value.
        
        Uses ThresholdCategorizer internally with age-specific evidence.
        """
        if age is None:
            return CategorizationResult(
                category=unknown_category,
                score=unknown_score,
                confidence=0.0,
                evidence=["No age provided"]
            )
        
        result = ThresholdCategorizer.categorize(
            value=age,
            bands=bands,
            inclusive_max=True,
            unknown_category=unknown_category,
            unknown_score=unknown_score
        )
        
        # Enhance evidence with age-specific wording
        if result.category != unknown_category:
            result.evidence = [f"Age {age:.1f} years → {result.category}"]
        
        return result


# =============================================================================
# CATEGORICAL FEATURE INFERRER
# =============================================================================

class CategoricalFeatureInferrer:
    """
    Infers categorical features from signal data.
    
    Maps observable signals to categorical feature values defined in config.
    This bridges the gap between raw signals and categorical_features in config.
    
    Example: Infer operator_type from fleet size, route network, etc.
    """
    
    @staticmethod
    def infer(
        signals: Dict[str, Any],
        inference_rules: List[Dict[str, Any]]
    ) -> CategorizationResult:
        """
        Infer a categorical feature from signals using rules.
        
        Args:
            signals: Dict of signal values
            inference_rules: List of rules from config, each with:
                - conditions: Dict of signal_id -> {operator, value}
                - category: The category to assign if conditions match
                
        Expected rule format:
        [
            {
                "category": "MAJOR_AIRLINE",
                "conditions": {
                    "fleet_size": {"operator": ">=", "value": 100},
                    "alliance_membership": {"operator": "in", "value": ["STAR_ALLIANCE", "ONEWORLD", "SKYTEAM"]}
                }
            },
            ...
        ]
        
        Returns:
            CategorizationResult with inferred category
        """
        for rule in inference_rules:
            conditions = rule.get("conditions", {})
            
            if CategoricalFeatureInferrer._evaluate_conditions(signals, conditions):
                return CategorizationResult(
                    category=rule.get("category", "UNKNOWN"),
                    score=rule.get("score"),
                    confidence=rule.get("confidence", 0.9),
                    evidence=[f"Matched rule for {rule.get('category')}"],
                    metadata={"rule": rule, "matched_signals": list(conditions.keys())}
                )
        
        # No rules matched - return default/unknown
        return CategorizationResult(
            category="UNCATEGORIZED",
            score=None,
            confidence=0.0,
            evidence=["No inference rules matched"]
        )
    
    @staticmethod
    def _evaluate_conditions(signals: Dict[str, Any], conditions: Dict[str, Dict]) -> bool:
        """Evaluate all conditions against signals."""
        for signal_id, condition in conditions.items():
            signal_value = signals.get(signal_id)
            
            if signal_value is None:
                return False
            
            operator = condition.get("operator", "==")
            target = condition.get("value")
            
            if not CategoricalFeatureInferrer._evaluate_single(signal_value, operator, target):
                return False
        
        return True
    
    @staticmethod
    def _evaluate_single(value: Any, operator: str, target: Any) -> bool:
        """Evaluate a single condition."""
        try:
            if operator == "==":
                return value == target
            elif operator == "!=":
                return value != target
            elif operator == ">":
                return value > target
            elif operator == ">=":
                return value >= target
            elif operator == "<":
                return value < target
            elif operator == "<=":
                return value <= target
            elif operator == "in":
                return value in target
            elif operator == "not_in":
                return value not in target
            elif operator == "contains":
                return target in value
            elif operator == "startswith":
                return str(value).startswith(str(target))
            else:
                return False
        except (TypeError, ValueError):
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def categorize_numeric(
    value: float,
    bands: List[Dict[str, Any]],
    **kwargs
) -> CategorizationResult:
    """Convenience function for threshold categorization."""
    return ThresholdCategorizer.categorize(value, bands, **kwargs)


def categorize_state(
    state: str,
    mapping: Dict[str, Dict[str, Any]],
    **kwargs
) -> CategorizationResult:
    """Convenience function for state categorization."""
    return StateCategorizer.categorize(state, mapping, **kwargs)


def categorize_entity(
    entity: str,
    tiers: List[Dict[str, Any]],
    **kwargs
) -> CategorizationResult:
    """Convenience function for entity recognition."""
    return EntityRecognizer.categorize(entity, tiers, **kwargs)


def categorize_ratio(
    actual: float,
    benchmark: float,
    bands: List[Dict[str, Any]],
    **kwargs
) -> CategorizationResult:
    """Convenience function for ratio categorization."""
    return RatioCategorizer.categorize(actual, benchmark, bands, **kwargs)


def categorize_count(
    count: int,
    bands: List[Dict[str, Any]],
    **kwargs
) -> CategorizationResult:
    """Convenience function for count categorization."""
    return CountCategorizer.categorize(count, bands, **kwargs)


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    print("=" * 70)
    print("DSI CATEGORIZERS - DEMO")
    print("=" * 70)
    
    # 1. Threshold Categorizer
    print("\n1. THRESHOLD CATEGORIZER (Fleet Age)")
    age_bands = [
        {"max": 5, "category": "NEW", "score": 95},
        {"max": 10, "category": "MODERN", "score": 85},
        {"max": 15, "category": "MATURE", "score": 70},
        {"max": 20, "category": "AGING", "score": 55},
        {"max": None, "category": "OLD", "score": 35},
    ]
    for age in [3, 8, 12, 18, 25]:
        result = ThresholdCategorizer.categorize(age, age_bands)
        print(f"   Age {age}: {result.category} (score={result.score})")
    
    # 2. State Categorizer
    print("\n2. STATE CATEGORIZER (Certificate Status)")
    cert_mapping = {
        "ACTIVE": {"category": "ACTIVE", "score": 100},
        "ACTIVE_WITH_RESTRICTIONS": {"category": "RESTRICTED", "score": 70},
        "SUSPENDED": {"category": "SUSPENDED", "score": 20},
        "REVOKED": {"category": "REVOKED", "score": 5},
    }
    for state in ["ACTIVE", "SUSPENDED", "unknown"]:
        result = StateCategorizer.categorize(state, cert_mapping)
        print(f"   {state}: {result.category} (score={result.score})")
    
    # 3. Entity Recognizer
    print("\n3. ENTITY RECOGNIZER (Lessor Quality)")
    lessor_tiers = [
        {"tier": "TIER_1", "score": 95, "entities": ["AerCap", "GECAS", "Avolon", "SMBC"]},
        {"tier": "TIER_2", "score": 80, "entities": ["BBAM", "NAC", "ACG", "BOC Aviation"]},
        {"tier": "TIER_3", "score": 65, "entities": []},  # Default
    ]
    for entity in ["AerCap", "BOC Aviation", "Regional Leasing Co"]:
        result = EntityRecognizer.categorize(entity, lessor_tiers)
        print(f"   {entity}: {result.category} (score={result.score}, conf={result.confidence})")
    
    # 4. Ratio Categorizer
    print("\n4. RATIO CATEGORIZER (Accident Rate vs Industry)")
    ratio_bands = [
        {"max_pct": 50, "category": "EXCELLENT", "score": 98},
        {"max_pct": 80, "category": "GOOD", "score": 85},
        {"max_pct": 120, "category": "AVERAGE", "score": 70},
        {"max_pct": 200, "category": "ELEVATED", "score": 45},
        {"max_pct": None, "category": "HIGH_RISK", "score": 20},
    ]
    for actual, benchmark in [(0.3, 1.0), (0.9, 1.0), (1.5, 1.0), (2.5, 1.0)]:
        result = RatioCategorizer.categorize(actual, benchmark, ratio_bands)
        print(f"   {actual}/{benchmark}: {result.category} (score={result.score})")
    
    # 5. Distribution Categorizer
    print("\n5. DISTRIBUTION CATEGORIZER (Fleet Composition)")
    distributions = [
        {"NARROWBODY": 80, "WIDEBODY": 20},
        {"NARROWBODY": 45, "WIDEBODY": 45, "REGIONAL": 10},
        {"NARROWBODY": 35, "WIDEBODY": 35, "REGIONAL": 30},
    ]
    for dist in distributions:
        result = DistributionCategorizer.categorize(dist)
        print(f"   {dist}: {result.category} (conf={result.confidence})")
    
    # 6. Count Categorizer
    print("\n6. COUNT CATEGORIZER (Enforcement Actions)")
    count_bands = [
        {"min": 0, "max": 0, "category": "CLEAN", "score": 100},
        {"min": 1, "max": 2, "category": "MINOR", "score": 80},
        {"min": 3, "max": 5, "category": "MODERATE", "score": 55},
        {"min": 6, "max": None, "category": "SIGNIFICANT", "score": 30},
    ]
    for count in [0, 1, 4, 8]:
        result = CountCategorizer.categorize(count, count_bands)
        print(f"   Count {count}: {result.category} (score={result.score})")
    
    # 7. Categorical Feature Inferrer
    print("\n7. CATEGORICAL FEATURE INFERRER (Operator Type)")
    inference_rules = [
        {
            "category": "MAJOR_AIRLINE",
            "conditions": {
                "fleet_size": {"operator": ">=", "value": 100},
                "has_alliance": {"operator": "==", "value": True}
            }
        },
        {
            "category": "REGIONAL_AIRLINE",
            "conditions": {
                "fleet_size": {"operator": ">=", "value": 20},
                "fleet_size": {"operator": "<", "value": 100}
            }
        },
        {
            "category": "SMALL_OPERATOR",
            "conditions": {
                "fleet_size": {"operator": "<", "value": 20}
            }
        },
    ]
    test_signals = [
        {"fleet_size": 150, "has_alliance": True},
        {"fleet_size": 50, "has_alliance": False},
        {"fleet_size": 10, "has_alliance": False},
    ]
    for signals in test_signals:
        result = CategoricalFeatureInferrer.infer(signals, inference_rules)
        print(f"   {signals}: {result.category}")
    
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)
