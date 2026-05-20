"""V7 Phase 13 — blast-radius computation for delta-aware recompute.

Pure function. No DB, no I/O. Given an event type and an optional hinted
signal_id, returns the set of signals that should be re-extracted:

    1. Direct triggers — signals whose `triggers` list includes event_type.
    2. The hinted signal (when supplied).
    3. The transitive downstream closure of (1) + (2).
"""
from __future__ import annotations

from typing import Optional

from .signal_deps import SIGNAL_DEPS, downstream_of, triggers_for_event


def compute_blast_radius(
    *,
    event_type: str,
    hinted_signal_id: Optional[str] = None,
) -> set[str]:
    """Set of signal_ids the dispatcher should re-extract for this event."""
    direct: set[str] = set(triggers_for_event(event_type))
    if hinted_signal_id and hinted_signal_id in SIGNAL_DEPS:
        direct.add(hinted_signal_id)
    closure = set(direct)
    for sid in list(direct):
        closure |= downstream_of(sid)
    return closure
