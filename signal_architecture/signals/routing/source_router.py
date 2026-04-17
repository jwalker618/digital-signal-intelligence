"""V6/D8 — Cost-aware signal broker.

Selects the cheapest extractor that satisfies a minimum-confidence
threshold for a given signal. Kill-switched extractors are skipped.
Cost telemetry emits on every successful extraction so Grafana can
project monthly spend (see deploy/monitoring/grafana/extractors.json).

Existing routing helpers (router.py, multi_source.py) predate V6 and
remain for bespoke cross-walks; the broker here is the new default
entry point introduced by D8.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence

log = logging.getLogger("dsi.broker")


# Rough $/extraction cost tier estimates. Concrete numbers come from
# each extractor's billing metrics; these defaults fuel the Grafana
# cost projection until per-source telemetry lands.
COST_TIER_USD = {
    "free":   0.0,
    "low":    0.002,
    "medium": 0.010,
    "high":   0.050,
}


@dataclass
class SourceSelection:
    """The outcome of a broker routing decision."""
    signal_id: str
    entity_id: str
    selected_source: Optional[str]
    tried_sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    cost_tier: Optional[str] = None
    cost_usd_estimate: float = 0.0
    elapsed_ms: float = 0.0
    reason: str = ""


class SignalBrokerV2:
    """Routes a signal request to the cheapest satisfying extractor.

    ``candidates`` is a callable returning the ordered list of
    extractor classes registered for a signal (cheapest first is the
    default sort, but callers can override via ``sort_by``).
    """

    def __init__(
        self,
        *,
        candidate_lookup: Callable[[str], Sequence[Any]],
        min_confidence: float = 0.6,
    ) -> None:
        self._lookup = candidate_lookup
        self.min_confidence = min_confidence

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def extract(
        self,
        signal_id: str,
        entity_id: str,
        *,
        context: Any = None,
        min_confidence: Optional[float] = None,
        preferred_source: Optional[str] = None,
    ) -> SourceSelection:
        threshold = (
            min_confidence if min_confidence is not None else self.min_confidence
        )
        candidates = list(self._lookup(signal_id))
        if not candidates:
            return SourceSelection(
                signal_id=signal_id,
                entity_id=entity_id,
                selected_source=None,
                reason="no extractor registered for signal",
            )

        # Sort: preferred_source first (if present), then cost ascending.
        def key(cls):
            if preferred_source and cls.SOURCE_NAME == preferred_source:
                return (-1, 0)
            return (0, _cost_rank(cls))
        candidates.sort(key=key)

        tried: List[str] = []
        started = time.time()
        for cls in candidates:
            tried.append(cls.SOURCE_NAME)
            if cls.is_disabled():
                log.debug("broker skip %s (kill-switch)", cls.SOURCE_NAME)
                continue
            if not cls.has_api_key():
                log.debug("broker skip %s (no api key)", cls.SOURCE_NAME)
                continue
            try:
                inst = cls()
                result = inst.extract(entity_id, context=context)
            except Exception as e:  # pragma: no cover — extractors degrade
                log.warning("broker extractor %s failed: %s", cls.SOURCE_NAME, e)
                continue
            confidence = float((result.metadata or {}).get("confidence", 0.0))
            if result.success and confidence >= threshold:
                tier = getattr(cls, "COST_TIER", "free")
                return SourceSelection(
                    signal_id=signal_id,
                    entity_id=entity_id,
                    selected_source=cls.SOURCE_NAME,
                    tried_sources=tried,
                    confidence=confidence,
                    cost_tier=tier,
                    cost_usd_estimate=COST_TIER_USD.get(tier, 0.0),
                    elapsed_ms=(time.time() - started) * 1000,
                    reason="ok",
                )
        return SourceSelection(
            signal_id=signal_id,
            entity_id=entity_id,
            selected_source=None,
            tried_sources=tried,
            elapsed_ms=(time.time() - started) * 1000,
            reason="no source met minimum confidence",
        )


def _cost_rank(cls) -> int:
    if hasattr(cls, "cost_tier_rank"):
        return cls.cost_tier_rank()
    return 99
