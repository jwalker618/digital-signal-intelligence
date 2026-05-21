"""V7 Phase 14 — mechanism-memory DTOs."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field


class MechanismDTO(BaseModel):
    """Read-side view of a stored mechanism (anonymous risk pattern)."""
    id: str
    summary: str
    primitive_type: str
    sector_tags: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    what_made_it_high_grade: str = ""
    recall_count: int = 0
