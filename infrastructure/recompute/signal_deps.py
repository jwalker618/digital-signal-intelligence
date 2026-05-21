"""V7 Phase 13 — declarative signal dependency graph.

`SIGNAL_DEPS[signal_id]` says:
    triggers      — which entity-event types cause this signal to be
                    re-extracted directly
    depends_on    — which other signals' values feed into this signal
                    (transitive downstream re-extraction)

Authors maintain this manually as new signals land. The `entries_for_prefix`
helper lets coverage maintainers declare bulk-prefix triggers without
listing every concrete signal_id.

Event types recognised:
    sanctions_update                  — OFAC / OFSI / etc. list change
    entity_filing                     — SEC / Companies House new filing
    entity_directorship               — director change
    human_calibration_disagreement    — Phase 7 sample with mismatch
    manual_recompute                  — operator request
"""
from __future__ import annotations

from typing import TypedDict


class SignalDep(TypedDict):
    triggers: list[str]
    depends_on: list[str]


# Concrete entries known at V7 launch. New signal_ids land here in PRs.
SIGNAL_DEPS: dict[str, SignalDep] = {
    "sanctions_screening_result": {
        "triggers": [
            "sanctions_update",
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "sanctions_check_routed": {
        "triggers": [
            "sanctions_update",
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "director_litigation_history": {
        "triggers": [
            "entity_directorship",
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "sec_filing_recency": {
        "triggers": [
            "entity_filing",
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "corporate_registry_routed": {
        "triggers": [
            "entity_filing",
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "breach_history_routed": {
        "triggers": [
            "manual_recompute",
            "human_calibration_disagreement",
        ],
        "depends_on": [],
    },
    "esg_score": {
        "triggers": ["manual_recompute", "human_calibration_disagreement"],
        "depends_on": ["sentiment_30d", "regulatory_actions_24m"],
    },
}


# Prefix-based fallback. When a signal_id isn't an explicit key in
# SIGNAL_DEPS, `triggers_for(event)` and `downstream_of` consult this
# table too. Order: most specific prefix first.
PREFIX_TRIGGER_MAP: list[tuple[str, list[str]]] = [
    ("sanctions_", ["sanctions_update", "manual_recompute", "human_calibration_disagreement"]),
    ("ofac_",      ["sanctions_update", "manual_recompute", "human_calibration_disagreement"]),
    ("pep_",       ["sanctions_update", "manual_recompute"]),
    ("director_",  ["entity_directorship", "manual_recompute"]),
    ("officer_",   ["entity_directorship", "manual_recompute"]),
    ("board_",     ["entity_directorship", "manual_recompute"]),
    ("sec_filing", ["entity_filing", "manual_recompute"]),
    ("filing_",    ["entity_filing", "manual_recompute"]),
    ("regulatory_actions", ["manual_recompute", "sanctions_update"]),
]


def triggers_for_signal(signal_id: str) -> set[str]:
    """All event types that would re-extract this signal.

    Explicit SIGNAL_DEPS entry beats the prefix map.
    """
    if signal_id in SIGNAL_DEPS:
        return set(SIGNAL_DEPS[signal_id]["triggers"])
    for prefix, events in PREFIX_TRIGGER_MAP:
        if signal_id.startswith(prefix):
            return set(events)
    # Default: only manual recompute reaches an unmapped signal.
    return {"manual_recompute"}


def triggers_for_event(event_type: str) -> set[str]:
    """All signal_ids in SIGNAL_DEPS whose `triggers` includes this event.

    Note: this only covers explicitly-mapped signals. Prefix-mapped signals
    are matched on the FORWARD side via `triggers_for_signal()` when the
    dispatcher iterates known signal_ids.
    """
    return {
        sig_id
        for sig_id, dep in SIGNAL_DEPS.items()
        if event_type in dep["triggers"]
    }


def downstream_of(signal_id: str) -> set[str]:
    """Transitive closure: every signal that depends on this one."""
    closure: set[str] = set()
    pending = {signal_id}
    while pending:
        sid = pending.pop()
        for downstream, dep in SIGNAL_DEPS.items():
            if sid in dep["depends_on"] and downstream not in closure:
                closure.add(downstream)
                pending.add(downstream)
    return closure
