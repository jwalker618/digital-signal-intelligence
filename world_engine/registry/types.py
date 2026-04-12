"""Registry API request/response types (WE-1d/e).

Thin wrappers around core World Engine types for API payloads, plus
list-response and filter models.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from world_engine.types import (
    CausalAdjustmentFactor,
    ConsistencyScore,
    DiscoveredRelationship,
    DriftAlert,
    DriftSeverity,
    LifecycleState,
    MaturityState,
    PortfolioConcentration,
)


class RelationshipListResponse(BaseModel):
    relationships: list[DiscoveredRelationship]
    total: int


class DriftAlertListResponse(BaseModel):
    alerts: list[DriftAlert]
    total: int


class PortfolioConcentrationsResponse(BaseModel):
    entity_id: str
    concentrations: list[PortfolioConcentration]


class EngineStatsResponse(BaseModel):
    maturity: MaturityState
    relationships_by_state: dict[str, int]
    scan_runs_total: int
    scan_runs_last_7_days: int
    drift_alerts_unacknowledged: int
    consistency_scores_total: int
    caf_computations_total: int
    evaluated_at: datetime


class AcknowledgeResponse(BaseModel):
    id: str
    acknowledged: bool
    acknowledged_at: datetime
