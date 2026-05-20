"""V7 Phase 14 — entity-event read DTO (Phase 13 stores them)."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EntityEventDTO(BaseModel):
    id: uuid.UUID
    event_type: str
    source_feed: str
    received_at: datetime
    dispatched_at: Optional[datetime] = None
    blast_radius: List[str] = Field(default_factory=list)
    resulting_model_version_id: Optional[uuid.UUID] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
