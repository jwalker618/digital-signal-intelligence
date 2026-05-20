"""V7 Phase 14 — disclosure-packet DTOs."""
from __future__ import annotations

from typing import Any, Dict

from pydantic import BaseModel


class DisclosureResponse(BaseModel):
    """JSON form of the disclosure endpoint.

    `markdown` is the human-readable packet; `payload` is the underlying
    canonical-JSON used to produce it. Both are deterministic for a given
    model_version_id — same inputs always produce the same packet.
    """
    markdown: str
    payload: Dict[str, Any]
