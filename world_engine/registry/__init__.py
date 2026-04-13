"""World Engine Registry (WE-1c/d/e).

The single interface through which all DSI components access World Engine
intelligence. Exposes read operations to everyone, writes only to internal
Engine subsystems.
"""

from world_engine.registry.store import IntelligenceRegistry

__all__ = ["IntelligenceRegistry"]
