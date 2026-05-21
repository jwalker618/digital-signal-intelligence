"""V7 Phase 14 — server-side disclosure packet generator.

Bundles signal + grade + pro/counter/tie-breaker + sources + commitment
digest + cluster symptoms + recalled mechanisms into a Markdown packet
and a canonical-JSON payload.

Determinism (D5): same backing rows -> byte-identical Markdown + identical
JSON payload (after canonical-key sorting). `generated_at` is the only
field that legitimately differs run-to-run; callers can pin it for tests.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from jinja2 import BaseLoader, Environment

from .templates import MARKDOWN_TEMPLATE


# Jinja env at module level so template parsing cost is paid once.
_ENV = Environment(
    loader=BaseLoader(),
    autoescape=False,
    trim_blocks=True,
    lstrip_blocks=True,
)
_TEMPLATE = _ENV.from_string(MARKDOWN_TEMPLATE)


@dataclass
class PacketSection:
    """One section of the packet — typically one referral-driving signal."""
    title: str
    signal_id: str
    grade: str
    grade_referral_reasons: list[str] = field(default_factory=list)
    pro: str = ""
    counter: str = ""
    tie_breaker: str = ""
    sources: list[dict] = field(default_factory=list)
    cluster_symptoms: list[dict] = field(default_factory=list)
    recalled_mechanisms: list[dict] = field(default_factory=list)
    commitment_digest: str = ""
    reproducibility: Optional[str] = None


def build_packet(
    *,
    model_version_id: uuid.UUID,
    composite_min_grade: Optional[str],
    composite_distribution: dict[str, float],
    referral_reasons: list[str],
    sections: list[PacketSection],
    generated_at: Optional[datetime] = None,
) -> tuple[str, dict[str, Any]]:
    """Render the packet. Returns (markdown, canonical_json_payload).

    `generated_at` is the only field that's non-deterministic by default;
    pin it for tests via the keyword argument.
    """
    generated_at = generated_at or datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "generated_at": generated_at.isoformat(),
        "model_version_id": str(model_version_id),
        "composite_min_grade": composite_min_grade,
        "composite_distribution": composite_distribution,
        "referral_reasons": referral_reasons,
        "sections": [s.__dict__ for s in sections],
    }
    md = _TEMPLATE.render(p=payload)
    # Canonicalise via round-trip so the returned payload is
    # exactly what the caller would persist (sort_keys, default=str).
    canonical = json.loads(
        json.dumps(payload, sort_keys=True, default=str)
    )
    return md, canonical
