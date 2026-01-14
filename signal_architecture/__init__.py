"""
DSI Signal Architecture

This package contains all signal-related components:
    - signals: Core signal extraction pipeline (extractors, aggregators, categorizers, inference, routing)
    - discovery: Entity identification and website discovery (Step 0)
    - orchestration: Multi-coverage workflow coordination
"""

from signal_architecture import signals
from signal_architecture import discovery
from signal_architecture import orchestration

__all__ = ["signals", "discovery", "orchestration"]
