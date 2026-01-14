"""
DSI Technical Pricing Framework (Backwards Compatibility Shim)

This module provides backwards compatibility for code using the old
`technical_pricing` import paths. All functionality has been moved to
root-level packages as part of Phase 18 restructuring.

New import paths:
    - from signals import ...        (was: from technical_pricing.signals import ...)
    - from layers.risk import ...    (was: from technical_pricing.model import ...)
    - from coverages import ...      (was: from technical_pricing.coverages import ...)
    - from discovery import ...      (was: from technical_pricing.discovery import ...)

This shim re-exports the moved modules for backwards compatibility.
New code should import directly from the root packages.
"""

__version__ = "0.1.0"

# Backwards compatibility: re-export signals module
import signals as signals

# Backwards compatibility: re-export model as layers.risk
from layers import risk as model

# Backwards compatibility: re-export coverages
import coverages as coverages

# Backwards compatibility: re-export discovery
import discovery as discovery
