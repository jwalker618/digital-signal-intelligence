"""
Exposure Layer - Exposure magnitude and complexity assessment (v2.0)

Evaluates exposure tier bands from coverage configurations to
produce pricing modifiers based on insured exposure size.

Works in parallel with risk and loss layers per the three-layer
assessment architecture.
"""

from .types import (
    ExposureAssessmentResult,
    ExposureBandLabel,
    ExposureBandResult,
    ExposureMethod,
    ExposureSignalOutput,
)
from .scorer import ExposureScorer

__all__ = [
    "ExposureAssessmentResult",
    "ExposureBandLabel",
    "ExposureBandResult",
    "ExposureMethod",
    "ExposureScorer",
    "ExposureSignalOutput",
]
