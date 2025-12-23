"""
inference/base.py - Core Inference Framework

Provides base classes, registries, and utilities for all inference functions.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import random

# =============================================================================
# REGISTRIES
# =============================================================================

INFERENCE_REGISTRY: Dict[str, Callable] = {}
CATEGORICAL_INFERENCE_REGISTRY: Dict[str, Callable] = {}


def register_inference(name: str):
    """Decorator to register signal inference functions by name."""
    def decorator(func: Callable) -> Callable:
        INFERENCE_REGISTRY[name] = func
        return func
    return decorator


def register_categorical_inference(name: str):
    """Decorator to register categorical inference functions by name."""
    def decorator(func: Callable) -> Callable:
        CATEGORICAL_INFERENCE_REGISTRY[name] = func
        return func
    return decorator


def get_inference_function(name: str) -> Optional[Callable]:
    """Retrieve a signal inference function by name."""
    return INFERENCE_REGISTRY.get(name)


def get_categorical_inference(name: str) -> Optional[Callable]:
    """Retrieve a categorical inference function by name."""
    return CATEGORICAL_INFERENCE_REGISTRY.get(name)


def list_inference_functions(coverage: Optional[str] = None) -> Dict[str, List[str]]:
    """List all registered inference functions, optionally filtered by coverage prefix."""
    signal_funcs = list(INFERENCE_REGISTRY.keys())
    categorical_funcs = list(CATEGORICAL_INFERENCE_REGISTRY.keys())
    
    if coverage:
        prefix = f"{coverage}_"
        signal_funcs = [f for f in signal_funcs if f.startswith(prefix)]
        categorical_funcs = [f for f in categorical_funcs if f.startswith(prefix)]
    
    return {
        "signal_inference": sorted(signal_funcs),
        "categorical_inference": sorted(categorical_funcs)
    }


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class InferenceResult:
    """
    Standardized result from an inference function.
    
    Note: Does NOT include modifiers or weights - those come from config
    and are applied by utility functions.
    """
    signal_id: str
    score: float                          # 0-100 scale
    category: Optional[str] = None        # e.g., "EXCELLENT", "STAR_ALLIANCE"
    raw_value: Any = None                 # Original value before scoring
    evidence: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source: Optional[str] = None          # Data source name
    source_timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "score": self.score,
            "category": self.category,
            "raw_value": self.raw_value,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "source": self.source,
            "source_timestamp": self.source_timestamp.isoformat() if self.source_timestamp else None,
            "metadata": self.metadata,
        }


@dataclass
class CategoricalResult:
    """Result from categorical feature inference."""
    feature_id: str
    category: str                         # The categorical value
    confidence: float = 1.0
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "category": self.category,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
        }


@dataclass
class InferenceContext:
    """
    Context passed to inference functions.
    
    Contains entity identification and any pre-fetched data that can be
    shared across multiple inference functions.
    """
    entity_id: str                        # Primary identifier
    entity_name: Optional[str] = None     # Human-readable name
    domain: Optional[str] = None          # Website domain if applicable
    coverage: str = ""                    # e.g., "aerospace"
    cov_configuration: str = ""           # e.g., "aerospace_general"
    
    # Additional identifiers
    identifiers: Dict[str, str] = field(default_factory=dict)  # e.g., {"icao": "DAL", "iata": "DL"}
    
    # Pre-fetched/cached data from extractors
    cached_data: Dict[str, Any] = field(default_factory=dict)
    
    # Geographic context
    country: Optional[str] = None
    region: Optional[str] = None


# =============================================================================
# SIMULATION UTILITIES
# =============================================================================

def get_seeded_random(entity_id: str, salt: str = "") -> random.Random:
    """
    Get a seeded random generator for reproducible simulation.
    Same entity_id + salt always produces same random sequence.
    """
    seed_str = f"{entity_id}:{salt}"
    seed = int(hashlib.md5(seed_str.encode()).hexdigest()[:8], 16)
    return random.Random(seed)


def simulate_score(
    entity_id: str,
    signal_id: str,
    base_score: float = 70,
    variance: float = 25,
    min_score: float = 0,
    max_score: float = 100
) -> float:
    """
    Generate a simulated score with seeded randomness.
    Same entity_id + signal_id always produces same score.
    """
    rng = get_seeded_random(entity_id, signal_id)
    score = base_score + rng.uniform(-variance, variance)
    return max(min_score, min(max_score, round(score, 1)))


def simulate_choice(
    entity_id: str,
    signal_id: str,
    choices: List[Any],
    weights: Optional[List[float]] = None
) -> Any:
    """
    Select from choices with seeded randomness.
    Same entity_id + signal_id always produces same choice.
    """
    rng = get_seeded_random(entity_id, signal_id)
    if weights:
        return rng.choices(choices, weights=weights)[0]
    return rng.choice(choices)


def simulate_count(
    entity_id: str,
    signal_id: str,
    max_count: int = 5,
    zero_weight: float = 0.5
) -> int:
    """
    Generate a simulated count with bias toward zero.
    """
    rng = get_seeded_random(entity_id, signal_id)
    if rng.random() < zero_weight:
        return 0
    return rng.randint(0, max_count)


def simulate_percentage(
    entity_id: str,
    signal_id: str,
    mean: float = 50,
    std: float = 20
) -> float:
    """
    Generate a simulated percentage (0-100).
    """
    rng = get_seeded_random(entity_id, signal_id)
    value = rng.gauss(mean, std)
    return max(0, min(100, round(value, 1)))


def simulate_rate(
    entity_id: str,
    signal_id: str,
    mean: float = 1.0,
    std: float = 0.5
) -> float:
    """
    Generate a simulated rate (non-negative).
    """
    rng = get_seeded_random(entity_id, signal_id)
    value = rng.gauss(mean, std)
    return max(0, round(value, 3))


def simulate_boolean(
    entity_id: str,
    signal_id: str,
    true_probability: float = 0.7
) -> bool:
    """
    Generate a simulated boolean.
    """
    rng = get_seeded_random(entity_id, signal_id)
    return rng.random() < true_probability


def simulate_tier(
    entity_id: str,
    signal_id: str,
    tiers: List[str],
    weights: Optional[List[float]] = None
) -> str:
    """
    Select a tier from options.
    Default weights favor higher tiers.
    """
    if weights is None:
        # Default: favor tier 1 > tier 2 > tier 3 > tier 4
        n = len(tiers)
        weights = [1.0 / (i + 1) for i in range(n)]
    return simulate_choice(entity_id, signal_id, tiers, weights)


# =============================================================================
# SCORE MAPPING UTILITIES
# =============================================================================

def map_tier_to_score(tier: str, tier_scores: Dict[str, float], default: float = 50) -> float:
    """Map a tier string to a score."""
    return tier_scores.get(tier, tier_scores.get(tier.upper(), default))


def map_count_to_score(
    count: int,
    bands: List[Tuple[int, int, float]]  # (min, max, score) tuples
) -> float:
    """
    Map a count to a score using bands.
    bands: [(0, 0, 100), (1, 2, 80), (3, 5, 55), (6, 999, 30)]
    """
    for min_val, max_val, score in bands:
        if min_val <= count <= max_val:
            return score
    return 50  # Default


def map_rate_to_score(
    rate: float,
    benchmark: float,
    bands: List[Tuple[float, float]]  # (max_ratio, score) tuples
) -> Tuple[float, str]:
    """
    Map a rate relative to benchmark to a score.
    Returns (score, category).
    """
    if benchmark == 0:
        return 50, "UNKNOWN"
    
    ratio = rate / benchmark
    
    for max_ratio, score in bands:
        if ratio <= max_ratio:
            if score >= 90:
                return score, "EXCELLENT"
            elif score >= 75:
                return score, "GOOD"
            elif score >= 60:
                return score, "AVERAGE"
            elif score >= 40:
                return score, "BELOW_AVERAGE"
            else:
                return score, "POOR"
    
    return bands[-1][1], "POOR"


def map_boolean_to_score(
    value: bool,
    true_score: float,
    false_score: float,
    true_category: str = "YES",
    false_category: str = "NO"
) -> Tuple[float, str]:
    """Map a boolean to score and category."""
    if value:
        return true_score, true_category
    return false_score, false_category


# =============================================================================
# BATCH INFERENCE
# =============================================================================

def run_signal_inference(
    ctx: InferenceContext,
    signal_features: Dict[str, List[Dict[str, Any]]]
) -> Dict[str, InferenceResult]:
    """
    Run inference for all signal features defined in configuration.
    
    Args:
        ctx: InferenceContext with entity information
        signal_features: Signal features from configuration
            {group_id: [{id, inference_function, ...}, ...]}
    
    Returns:
        Dict mapping signal_id to InferenceResult
    """
    results = {}
    
    for group_id, features in signal_features.items():
        for feature in features:
            signal_id = feature.get("id")
            inference_func_name = feature.get("inference_function")
            
            if not signal_id:
                continue
            
            # Try to find inference function
            if inference_func_name:
                inference_func = get_inference_function(inference_func_name)
            else:
                # Convention: {coverage}_{signal_id}_inference
                default_name = f"{ctx.coverage}_{signal_id}_inference"
                inference_func = get_inference_function(default_name)
            
            if inference_func:
                try:
                    result = inference_func(ctx)
                    results[signal_id] = result
                except Exception as e:
                    results[signal_id] = InferenceResult(
                        signal_id=signal_id,
                        score=50,
                        category="ERROR",
                        evidence=[f"Inference error: {str(e)}"],
                        confidence=0.0
                    )
            else:
                # No inference function - return default
                results[signal_id] = InferenceResult(
                    signal_id=signal_id,
                    score=50,
                    category="NOT_IMPLEMENTED",
                    evidence=[f"No inference function for {signal_id}"],
                    confidence=0.0
                )
    
    return results


def run_categorical_inference(
    ctx: InferenceContext,
    categorical_groups: List[Dict[str, Any]]
) -> Dict[str, CategoricalResult]:
    """
    Run inference for all categorical groups defined in configuration.
    
    Args:
        ctx: InferenceContext with entity information
        categorical_groups: Categorical groups from configuration
            [{id, inference_function, ...}, ...]
    
    Returns:
        Dict mapping group_id to CategoricalResult
    """
    results = {}
    
    for group in categorical_groups:
        group_id = group.get("id")
        inference_func_name = group.get("inference_function")
        
        if not group_id:
            continue
        
        # Try to find inference function
        if inference_func_name:
            inference_func = get_categorical_inference(inference_func_name)
        else:
            # Convention: {coverage}_{group_id}_inference
            default_name = f"{ctx.coverage}_{group_id}_inference"
            inference_func = get_categorical_inference(default_name)
        
        if inference_func:
            try:
                result = inference_func(ctx)
                results[group_id] = result
            except Exception as e:
                results[group_id] = CategoricalResult(
                    feature_id=group_id,
                    category="UNKNOWN",
                    confidence=0.0,
                    evidence=[f"Inference error: {str(e)}"]
                )
        else:
            results[group_id] = CategoricalResult(
                feature_id=group_id,
                category="UNKNOWN",
                confidence=0.0,
                evidence=[f"No inference function for {group_id}"]
            )
    
    return results


def extract_scores(inference_results: Dict[str, InferenceResult]) -> Dict[str, float]:
    """Extract just the scores from inference results for utility functions."""
    return {signal_id: result.score for signal_id, result in inference_results.items()}


def extract_categories(categorical_results: Dict[str, CategoricalResult]) -> Dict[str, str]:
    """Extract just the categories from categorical results."""
    return {group_id: result.category for group_id, result in categorical_results.items()}
