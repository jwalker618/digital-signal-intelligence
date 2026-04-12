"""WE-3c: Validation Engine.

Three validators apply successive statistical gates to discovered
relationships before they can be promoted:

- HoldoutValidator:       replication in an unseen 30% split
- TemporalStabilityTracker: persistence across rolling time windows
- PredictiveValidator:    out-of-sample forward prediction hit rate
"""

from world_engine.validator.holdout import HoldoutValidator
from world_engine.validator.stability import TemporalStabilityTracker
from world_engine.validator.predictive import PredictiveValidator

__all__ = [
    "HoldoutValidator",
    "TemporalStabilityTracker",
    "PredictiveValidator",
]
