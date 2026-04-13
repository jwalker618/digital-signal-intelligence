"""
World Engine Registry API (WE-1e)

Read-only FastAPI router for querying World Engine intelligence. Mounted at
/api/v1/world-engine/ by infrastructure/api/main.py.

The registry's write API is NOT exposed via HTTP -- writes are performed only
by internal Engine subsystems in Python.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from infrastructure.db.config import get_db
from world_engine.registry.store import IntelligenceRegistry
from world_engine.registry.types import (
    AcknowledgeResponse,
    DriftAlertListResponse,
    EngineStatsResponse,
    PortfolioConcentrationsResponse,
    RelationshipListResponse,
)
from world_engine.types import (
    CausalAdjustmentFactor,
    ConsistencyScore,
    DiscoveredRelationship,
    DriftSeverity,
    LifecycleState,
    MaturityState,
)

logger = logging.getLogger("dsi.api.world_engine")
router = APIRouter()


def get_registry(db: Session = Depends(get_db)) -> IntelligenceRegistry:
    """FastAPI dependency: yields an IntelligenceRegistry bound to a sync session."""
    return IntelligenceRegistry(db)


# ---------------------------------------------------------------------------
# Maturity
# ---------------------------------------------------------------------------


@router.get("/maturity", response_model=MaturityState)
def get_maturity(registry: IntelligenceRegistry = Depends(get_registry)) -> MaturityState:
    """Current World Engine maturity stage and capability flags."""
    return registry.get_maturity_state()


# ---------------------------------------------------------------------------
# Relationships
# ---------------------------------------------------------------------------


@router.get("/relationships", response_model=RelationshipListResponse)
def list_relationships(
    state: Optional[LifecycleState] = None,
    source_signal: Optional[str] = None,
    target_signal: Optional[str] = None,
    coverage: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    registry: IntelligenceRegistry = Depends(get_registry),
) -> RelationshipListResponse:
    """List discovered relationships, filterable by state/signal/coverage."""
    items, total = registry.list_relationships(
        state=state,
        source_signal=source_signal,
        target_signal=target_signal,
        coverage=coverage,
        limit=limit,
        offset=offset,
    )
    return RelationshipListResponse(relationships=items, total=total)


@router.get("/relationships/{relationship_id}", response_model=DiscoveredRelationship)
def get_relationship(
    relationship_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
) -> DiscoveredRelationship:
    """Single relationship with full state history."""
    rel = registry.get_relationship(relationship_id)
    if rel is None:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel


# ---------------------------------------------------------------------------
# Consistency
# ---------------------------------------------------------------------------


@router.get("/consistency/{assessment_id}", response_model=ConsistencyScore)
def get_consistency(
    assessment_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
) -> ConsistencyScore:
    """Consistency score for a specific assessment."""
    score = registry.get_consistency_score(assessment_id)
    if score is None:
        raise HTTPException(status_code=404, detail="No consistency score for this assessment")
    return score


# ---------------------------------------------------------------------------
# CAF
# ---------------------------------------------------------------------------


@router.get("/caf/{assessment_id}", response_model=CausalAdjustmentFactor)
def get_caf(
    assessment_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
) -> CausalAdjustmentFactor:
    """Causal Adjustment Factor for a specific assessment."""
    caf = registry.get_caf(assessment_id)
    if caf is None:
        raise HTTPException(status_code=404, detail="No CAF for this assessment")
    return caf


# ---------------------------------------------------------------------------
# Portfolio
# ---------------------------------------------------------------------------


@router.get(
    "/portfolio/{entity_id}/concentrations",
    response_model=PortfolioConcentrationsResponse,
)
def get_portfolio_concentrations(
    entity_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
) -> PortfolioConcentrationsResponse:
    """Portfolio concentrations for a commercial entity."""
    concentrations = registry.get_portfolio_concentrations(entity_id)
    return PortfolioConcentrationsResponse(
        entity_id=entity_id, concentrations=concentrations
    )


# ---------------------------------------------------------------------------
# Portfolio Graph + simulation (WE-5)
# ---------------------------------------------------------------------------


@router.get("/portfolio/{entity_id}/graph")
def get_portfolio_graph(
    entity_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
):
    """Return the full Portfolio Graph for a commercial entity (WE-5a)."""
    from world_engine.portfolio import PortfolioGraphBuilder

    graph = PortfolioGraphBuilder(registry.db).build(entity_id)
    return graph


@router.get("/portfolio/{entity_id}/graph/systemic-nodes")
def get_systemic_nodes(
    entity_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
):
    """Return only the systemic nodes (top portfolio-PageRank)."""
    from world_engine.portfolio import PortfolioGraphBuilder

    graph = PortfolioGraphBuilder(registry.db).build(entity_id)
    return {"entity_id": entity_id, "systemic_nodes": graph.systemic_nodes}


@router.post("/portfolio/{entity_id}/detect-concentrations")
def detect_concentrations(
    entity_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
):
    """Build the portfolio and run concentration detection. Persists alerts."""
    from world_engine.portfolio import (
        ConcentrationDetector,
        PortfolioGraphBuilder,
    )

    db = registry.db
    graph = PortfolioGraphBuilder(db).build(entity_id)
    alerts = ConcentrationDetector(db).detect(graph)
    for a in alerts:
        registry.store_concentration(a)
    db.commit()
    return {
        "entity_id": entity_id,
        "entity_count": graph.entity_count,
        "concentrations_detected": len(alerts),
        "alerts": alerts,
    }


class MarginalImpactRequest(BaseModel):
    """Body for /portfolio/{entity_id}/marginal-impact."""

    prospective_entity_name: str
    prospective_signals: dict[str, float]


@router.post("/portfolio/{entity_id}/marginal-impact")
def marginal_impact(
    entity_id: str,
    body: "MarginalImpactRequest",
    registry: IntelligenceRegistry = Depends(get_registry),
):
    """Evaluate the portfolio impact of accepting a prospective submission (WE-5e)."""
    from world_engine.portfolio import MarginalImpactAnalyser

    result = MarginalImpactAnalyser(registry.db).analyse(
        prospective_entity_name=body.prospective_entity_name,
        prospective_signals=body.prospective_signals,
        commercial_entity_id=entity_id,
    )
    return result


class SimulateRequest(BaseModel):
    """Body for /portfolio/{entity_id}/simulate."""

    name: str
    description: Optional[str] = None
    shocks: list[dict]   # free-form; coerced to ScenarioShock


@router.post("/portfolio/{entity_id}/simulate")
def simulate(
    entity_id: str,
    body: "SimulateRequest",
    registry: IntelligenceRegistry = Depends(get_registry),
):
    """Run a scenario simulation on the portfolio (WE-5f)."""
    from world_engine.portfolio import (
        PortfolioGraphBuilder,
        ScenarioDefinition,
        ScenarioShock,
        ScenarioSimulator,
    )

    graph = PortfolioGraphBuilder(registry.db).build(entity_id)
    scenario = ScenarioDefinition(
        name=body.name,
        description=body.description,
        shocks=[ScenarioShock(**s) for s in body.shocks],
    )
    return ScenarioSimulator().simulate(scenario, graph)


@router.get("/portfolio/{entity_id}/simulate/presets")
def simulation_presets(entity_id: str):
    """Pre-defined scenario templates for the frontend scenario panel."""
    return {
        "entity_id": entity_id,
        "presets": [
            {
                "name": "Cloud provider outage",
                "description": "A major cloud provider experiences a regional outage.",
                "shocks": [{
                    "target_type": "signal", "target_id": "cloud_provider",
                    "magnitude": 0.0, "propagation": "full_cascade", "decay_rate": 0.5,
                }],
            },
            {
                "name": "Regulatory change",
                "description": "Regulator tightens requirements in a single jurisdiction.",
                "shocks": [{
                    "target_type": "signal", "target_id": "jurisdiction",
                    "magnitude": -30.0, "propagation": "one_hop", "decay_rate": 0.4,
                }],
            },
            {
                "name": "Supply chain disruption",
                "description": "A shared supplier fails.",
                "shocks": [{
                    "target_type": "signal", "target_id": "supplier",
                    "magnitude": -50.0, "propagation": "full_cascade", "decay_rate": 0.6,
                }],
            },
            {
                "name": "Vulnerability disclosure",
                "description": "Critical CVE published in a widely-used dependency.",
                "shocks": [{
                    "target_type": "external_event", "target_id": "critical_cve",
                    "magnitude": -25.0, "propagation": "one_hop", "decay_rate": 0.3,
                }],
            },
        ],
    }


# ---------------------------------------------------------------------------
# Drift alerts
# ---------------------------------------------------------------------------


@router.get("/drift-alerts", response_model=DriftAlertListResponse)
def list_drift_alerts(
    severity: Optional[DriftSeverity] = None,
    since: Optional[datetime] = None,
    unacknowledged_only: bool = False,
    limit: int = Query(100, ge=1, le=1000),
    registry: IntelligenceRegistry = Depends(get_registry),
) -> DriftAlertListResponse:
    """List drift alerts, filterable by severity/date/acknowledged status."""
    alerts = registry.get_drift_alerts(
        severity=severity,
        since=since,
        unacknowledged_only=unacknowledged_only,
        limit=limit,
    )
    return DriftAlertListResponse(alerts=alerts, total=len(alerts))


@router.post("/drift-alerts/{alert_id}/acknowledge", response_model=AcknowledgeResponse)
def acknowledge_drift_alert(
    alert_id: str,
    registry: IntelligenceRegistry = Depends(get_registry),
) -> AcknowledgeResponse:
    """Mark a drift alert as acknowledged."""
    ack_at = registry.acknowledge_drift_alert(alert_id)
    if ack_at is None:
        raise HTTPException(
            status_code=404, detail="Alert not found or already acknowledged"
        )
    return AcknowledgeResponse(id=alert_id, acknowledged=True, acknowledged_at=ack_at)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------


@router.get("/stats", response_model=EngineStatsResponse)
def get_engine_stats(
    registry: IntelligenceRegistry = Depends(get_registry),
) -> EngineStatsResponse:
    """Engine statistics: relationship counts by state, scan history, maturity."""
    stats = registry.get_engine_stats()
    maturity = registry.get_maturity_state()
    return EngineStatsResponse(
        maturity=maturity,
        relationships_by_state=stats["relationships_by_state"],
        scan_runs_total=stats["scan_runs_total"],
        scan_runs_last_7_days=stats["scan_runs_last_7_days"],
        drift_alerts_unacknowledged=stats["drift_alerts_unacknowledged"],
        consistency_scores_total=stats["consistency_scores_total"],
        caf_computations_total=stats["caf_computations_total"],
        evaluated_at=maturity.evaluated_at,
    )
