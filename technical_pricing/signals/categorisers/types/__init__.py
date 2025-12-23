"""
DSI Reusable Categorizer Types

This module contains generic, reusable categorizer implementations
that can be parameterized for different signals.

Score Categorizers (return 0-100 score):
    - ThresholdBucketCategorizer: Map numeric values to scores via thresholds
    - InverseThresholdBucketCategorizer: Higher input = lower score
    - BooleanScoreCategorizer: Map boolean to score
    - PresenceScoreCategorizer: Score based on value presence/absence
    - MultiBooleanScoreCategorizer: Weighted scoring of multiple booleans
    - WeightedCompositeCategorizer: Combine multiple fields with weights
    - LinearScaleCategorizer: Scale numeric value to score range
    - AverageScoreCategorizer: Average multiple score fields

Category Categorizers (return category string):
    - CategoryMapperCategorizer: Rule-based category assignment
    - DirectMappingCategorizer: Simple value-to-category mapping
    - RangeCategorizer: Map numeric ranges to categories
    - MultiFieldCategorizer: Category from multiple fields with priority
"""

from .threshold_bucket import (
    ThresholdBucketCategorizer,
    InverseThresholdBucketCategorizer,
)

from .boolean_score import (
    BooleanScoreCategorizer,
    PresenceScoreCategorizer,
    MultiBooleanScoreCategorizer,
)

from .weighted_composite import (
    WeightedCompositeCategorizer,
    LinearScaleCategorizer,
    AverageScoreCategorizer,
)

from .category_mapper import (
    CategoryMapperCategorizer,
    DirectMappingCategorizer,
    RangeCategorizer,
    MultiFieldCategorizer,
)

__all__ = [
    # Threshold-based scoring
    "ThresholdBucketCategorizer",
    "InverseThresholdBucketCategorizer",
    # Boolean scoring
    "BooleanScoreCategorizer",
    "PresenceScoreCategorizer",
    "MultiBooleanScoreCategorizer",
    # Composite scoring
    "WeightedCompositeCategorizer",
    "LinearScaleCategorizer",
    "AverageScoreCategorizer",
    # Category mapping
    "CategoryMapperCategorizer",
    "DirectMappingCategorizer",
    "RangeCategorizer",
    "MultiFieldCategorizer",
]
