"""WE-2: Consistency Scorer.

Computes cross-signal and cross-layer consistency for every assessment
(inline) and population-level aggregates (batch). Produces immediate
anti-gaming value and generates structured divergence data that the
discovery engine (WE-3) consumes.
"""

from world_engine.consistency.scorer import (
    ConsistencyInputs,
    ConsistencyScorer,
    SignalScore,
)
from world_engine.consistency.population import PopulationConsistencyAggregator

__all__ = [
    "ConsistencyScorer",
    "ConsistencyInputs",
    "SignalScore",
    "PopulationConsistencyAggregator",
]
