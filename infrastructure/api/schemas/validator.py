"""V7 Phase 14 — validator-verdict DTOs (read-only API surface)."""
from __future__ import annotations

from datetime import datetime
from typing import Dict, Literal, Optional

from pydantic import BaseModel, Field

Axis = Literal[
    "MATERIAL",
    "CORRECT_ENTITY",
    "OPERATIONALLY_PLAUSIBLE",
    "GENERALISES_AT_RENEWAL",
]


class AxisResultDTO(BaseModel):
    axis: Axis
    passed: bool
    confidence: Literal["high", "medium", "low"]
    rationale: str


class ValidatorVerdictDTO(BaseModel):
    signal_id: str
    mode: Literal["quick_pass", "full_pass"]
    advance: bool
    grade_before: Optional[str] = None
    grade_after: Optional[str] = None
    axes: Dict[Axis, AxisResultDTO] = Field(default_factory=dict)
    pro_argument: str
    counter_argument: str
    tie_breaker: str
    elapsed_seconds: Optional[float] = None
    decided_at: datetime
