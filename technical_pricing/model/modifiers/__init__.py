"""
DSI Traditional Pricing Modifiers (Phase 7)

Optional modifiers that integrate traditional actuarial data sources
with DSI's digital signal-based pricing. All inputs are optional -
modifiers return factor=1.0 when data is unavailable.

Modules:
- base: TraditionalModifier base class and result types
- loss_history: Experience rating based on loss history
- exposure: Exposure-based adjustments with STP mode
- external_rating: External rating integration
"""

from .base import (
    TraditionalModifier,
    TraditionalModifierResult,
    LossHistoryInput,
    PolicyYear,
    Claim,
    ExposureInput,
)
from .loss_history import LossHistoryModifier
from .exposure import ExposureModifier
from .external_rating import ExternalRatingModifier

__all__ = [
    # Base
    "TraditionalModifier",
    "TraditionalModifierResult",
    # Input types
    "LossHistoryInput",
    "PolicyYear",
    "Claim",
    "ExposureInput",
    # Modifiers
    "LossHistoryModifier",
    "ExposureModifier",
    "ExternalRatingModifier",
]
