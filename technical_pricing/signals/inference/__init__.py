"""
Inference Function Framework

This module provides the inference function framework for all coverage lines.
Inference functions orchestrate data extraction and aggregation to produce
signal scores (0-100) for each signal feature defined in config.

Design Principles:
1. One inference function per signal feature (referenced by name in config)
2. Inference functions return scores (0-100), NOT modifiers or tier decisions
3. Modifiers, weights, and tier logic are applied by utility functions
4. Inference functions are stateless - they receive context and return scores

Organisation:
- inference/base.py - Core classes, registry, and utilities
- inference/aerospace.py - Aerospace coverage inference functions
- inference/cyber.py - Cyber coverage inference functions
- inference/directors_officers.py - D&O coverage inference functions
- inference/energy.py - Energy coverage inference functions
- inference/financial_institutions.py - FI coverage inference functions
- inference/marine.py - Marine coverage inference functions
- inference/professional_indemnity.py - PI coverage inference functions
"""

from .base import (
    INFERENCE_REGISTRY,
    CATEGORICAL_INFERENCE_REGISTRY,
    register_inference,
    register_categorical_inference,
    get_inference_function,
    get_categorical_inference,
    list_inference_functions,
    InferenceResult,
    InferenceContext,
    run_signal_inference,
    run_categorical_inference,
    extract_scores,
)

__all__ = [
    "INFERENCE_REGISTRY",
    "CATEGORICAL_INFERENCE_REGISTRY", 
    "register_inference",
    "register_categorical_inference",
    "get_inference_function",
    "get_categorical_inference",
    "list_inference_functions",
    "InferenceResult",
    "InferenceContext",
    "run_signal_inference",
    "run_categorical_inference",
    "extract_scores",
]
