"""
A-2e (part): State capture helpers for before/after audit snapshots.

Endpoints that modify resources use `capture_model(obj)` to snapshot the
resource state before and after mutation. The snapshot is a plain dict
suitable for JSONB storage in audit_logs.before_state / after_state.

Alternative: the StateCapture class provides a generic interface when the
caller only has (resource_type, resource_id) and needs to look up the
current state.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from sqlalchemy.orm import Session


def capture_model(obj: Any, exclude: Optional[set[str]] = None) -> dict:
    """Return a JSON-safe dict of a SQLAlchemy model's columns.

    Skips relationships, SQLA internals, and columns in `exclude`.
    Values are coerced to JSON-serialisable types:
      - UUID -> str
      - datetime -> ISO string
      - Decimal -> float
      - Enum -> value
    Nested dicts/lists are passed through unchanged.
    """
    if obj is None:
        return {}

    exclude = exclude or set()
    result: dict[str, Any] = {}

    # Use SQLA inspection to get only mapped columns (not relationships)
    try:
        from sqlalchemy import inspect as sqla_inspect

        mapper = sqla_inspect(obj).mapper
        column_names = [col.key for col in mapper.columns]
    except Exception:
        # Fallback for non-SQLA objects (e.g. Pydantic models)
        if hasattr(obj, "model_dump"):
            return obj.model_dump(mode="json")
        column_names = [k for k in vars(obj) if not k.startswith("_")]

    for name in column_names:
        if name in exclude:
            continue
        value = getattr(obj, name, None)
        result[name] = _serialise(value)

    return result


class StateCapture:
    """Generic resource state snapshotter.

    Registers per-resource-type capture functions. Endpoints can either use
    this class (when they only have resource_type + resource_id) or call
    capture_model() directly (when they have the ORM instance).
    """

    def __init__(self, db: Session):
        self.db = db
        self._handlers: dict[str, Any] = {}

    def register(self, resource_type: str, handler) -> None:
        """Register a loader for a resource_type.

        The handler signature: (session, resource_id) -> dict | None
        """
        self._handlers[resource_type] = handler

    def capture(self, resource_type: str, resource_id: str) -> Optional[dict]:
        """Return a snapshot of the resource, or None if no handler or not found."""
        handler = self._handlers.get(resource_type)
        if handler is None:
            return None
        try:
            return handler(self.db, resource_id)
        except Exception:
            return None


# =============================================================================
# Coercion helpers
# =============================================================================


def _serialise(value: Any) -> Any:
    """Convert a value to a JSON-serialisable form."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "value") and hasattr(type(value), "__members__"):
        # Enum
        return value.value
    if isinstance(value, dict):
        return {k: _serialise(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialise(v) for v in value]
    # Fallback: stringify
    return str(value)
