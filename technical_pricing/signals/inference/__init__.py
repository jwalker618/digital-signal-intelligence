"""
DSI Inference Functions

Inference functions orchestrate the full pipeline for specific signals
or categorical features: Extractor(s) → Aggregator(s) → Categorizer.

Components:
    - registry: Maps YAML inference_utility_function names to implementations
    - functions/: Domain-specific inference function implementations

Usage:
    from signals.inference import get_inference_function
    
    func = get_inference_function("alliance_membership_basefunction")
    result = func(entity_id, context)
"""

from .registry import (
    register_inference_function,
    get_inference_function,
    list_inference_functions,
    InferenceFunctionNotFoundError,
)

__all__ = [
    "register_inference_function",
    "get_inference_function",
    "list_inference_functions",
    "InferenceFunctionNotFoundError",
]
