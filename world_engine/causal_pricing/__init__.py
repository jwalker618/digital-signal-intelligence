"""WE-4: Causal Graph Pricing.

Parallel pricing track. Evaluates entities against the validated causal
graph to produce a Causal Adjustment Factor (CAF) that enters the premium
formula as a multiplicative adjustment:

    P_final = P_static × CAF

Defaults to 1.0 (neutral) when maturity is below EMERGE, fewer than the
minimum relationships match, or confidence falls below the gate.
"""

from world_engine.causal_pricing.engine import CausalPricingEngine
from world_engine.causal_pricing.trajectory import TrajectoryEngine
from world_engine.causal_pricing.constraints import (
    ConstraintCalibrator,
    ConstraintRegime,
    ABSOLUTE_FLOOR,
    ABSOLUTE_CAP,
    ABSOLUTE_CONFIDENCE_MIN,
)

__all__ = [
    "CausalPricingEngine",
    "TrajectoryEngine",
    "ConstraintCalibrator",
    "ConstraintRegime",
    "ABSOLUTE_FLOOR",
    "ABSOLUTE_CAP",
    "ABSOLUTE_CONFIDENCE_MIN",
]
