"""V7 Phase 12 — mechanism extraction with eligibility gating + scrubber.

`is_eligible` is the locked gate. `extract_mechanism` calls the LLM,
scrubs the response best-effort, and returns either a Mechanism or None.

Eligibility (all must hold):
    validator_advanced       — Phase 6 advance=True
    evidence_grade           — in {structured_attested, behaviourally_validated}
    reproducibility          — exactly "stable" (Phase 8)
    metadata['cluster_id']   — present
    metadata['deterministic']— not False
"""
from __future__ import annotations

import json
import re
import uuid
from typing import Optional

from signal_architecture.signals.types import SignalResult

from .prompts import EXTRACTION_SYSTEM, build_extraction_user
from .types import Mechanism


# ---------------------------------------------------------------------------
# Eligibility
# ---------------------------------------------------------------------------

def is_eligible(sig: SignalResult, *, validator_advanced: bool) -> bool:
    """Locked Phase 12 D2 predicate. All five conditions must hold."""
    if not validator_advanced:
        return False
    if sig.evidence_grade not in ("structured_attested", "behaviourally_validated"):
        return False
    if sig.reproducibility != "stable":
        return False
    md = sig.metadata or {}
    if not md.get("cluster_id"):
        return False
    if md.get("deterministic") is False:
        return False
    return True


# ---------------------------------------------------------------------------
# Best-effort anonymisation scrubber
# ---------------------------------------------------------------------------

# 4-digit years (19xx or 20xx).
_YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
# Sequence of 2-4 capitalised words — heuristic for proper nouns.
_NAME_RE = re.compile(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b")
# Standalone all-caps tokens of length >=3 (company acronyms, list IDs).
_ACRONYM_RE = re.compile(r"\b[A-Z]{3,}\b")


def _strip_disallowed(text: str) -> str:
    """Belt-and-braces — strip patterns the LLM may have left behind.

    Sentinels are intentionally lowercase so they don't get clobbered by
    the all-caps acronym pass that runs after them.
    """
    if not text:
        return text
    text = _YEAR_RE.sub("<year>", text)
    text = _NAME_RE.sub("<name>", text)
    text = _ACRONYM_RE.sub("<acronym>", text)
    return text


_JSON_RE = re.compile(r"\{[\s\S]*\}")


def extract_mechanism(
    llm_callable,
    sig: SignalResult,
    *,
    sector_tags: list[str],
    cycle_id: str,
) -> Optional[Mechanism]:
    """Run the LLM, parse + scrub, return a Mechanism or None.

    `llm_callable` is the project's standard (system, user) -> str protocol.
    """
    md = sig.metadata or {}
    payload = {
        "primitive_type": sig.primitive_type,
        "fact_class": md.get("fact_class"),
        "cluster_size": len(md.get("symptoms") or []),
        "evidence_grade": sig.evidence_grade,
        "evidence_basis": _strip_disallowed(sig.evidence_basis or ""),
        "reproducibility": sig.reproducibility,
    }
    try:
        raw = llm_callable(
            system=EXTRACTION_SYSTEM,
            user=build_extraction_user(json.dumps(payload, sort_keys=True, default=str)),
        ) or ""
    except Exception:  # noqa: BLE001
        return None

    match = _JSON_RE.search(raw)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    summary = _strip_disallowed((data.get("summary") or "").strip())
    if not summary:
        return None

    return Mechanism(
        id=f"mech-{uuid.uuid4().hex[:10]}",
        summary=summary,
        primitive_type=sig.primitive_type or "unknown",
        sector_tags=list(sector_tags),
        tags=[t for t in (data.get("tags") or []) if isinstance(t, str)],
        keywords=[k for k in (data.get("keywords") or []) if isinstance(k, str)],
        what_made_it_high_grade=_strip_disallowed(
            data.get("what_made_it_high_grade") or ""
        ),
        source_cluster_id=str(md.get("cluster_id", "")),
        source_signal_id=sig.signal_id,
        source_cycle_id=cycle_id,
    )
