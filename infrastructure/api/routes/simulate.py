"""
DSI Simulation API (Phase 3)

Portfolio stress-testing endpoint backed by the Rust dsi-sim engine.
Accepts a portfolio snapshot and one or more shock parameters,
delegates to PyO3-compiled Rust for millisecond-scale parallel
simulation, and returns premium-adequacy metrics.

Usage:
    POST /api/v1/simulate
    {
        "portfolio_json": "{ ... }",
        "shocks": [{"signal_id": "active_cves", "shock_type": "multiplier", "value": 2.0}],
        "iterations": 1
    }
"""

import json
import logging
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..types import (
    SimulateRequest,
    SimulateResponse,
    SimulationStats,
    TierMigration,
)


logger = logging.getLogger("dsi.api.simulate")

router = APIRouter()


def _build_shock(params):
    """
    Build a dsi_sim.ShockParameter from request parameters.

    Falls back to a plain-dict representation when the Rust extension
    is not available (stub mode).
    """
    try:
        from dsi_sim import ShockParameter

        shock_type = params.shock_type.lower()
        if shock_type == "override":
            shock = ShockParameter.signal_override(
                params.signal_id,
                params.value,
            )
        elif shock_type == "multiplier":
            shock = ShockParameter.signal_multiplier(
                params.signal_id,
                params.value,
            )
        elif shock_type == "macro":
            shock = ShockParameter.macro_shock(
                params.signal_id,
                params.value,
            )
        else:
            shock = ShockParameter.signal_multiplier(
                params.signal_id,
                params.value,
            )

        # Apply filters
        if params.industry_filter:
            shock = shock.with_industry(params.industry_filter)
        if params.tier_filter is not None:
            shock = shock.with_tier(params.tier_filter)
            
        return shock

    except ImportError:
        # Stub mode: return dictionary representation
        return {
            "signal_id": params.signal_id,
            "shock_type": params.shock_type,
            "value": params.value,
            "filters": {
                "industry": params.industry_filter,
                "tier": params.tier_filter,
                "coverage": params.coverage_filter
            }
        }


@router.post("/simulate", response_model=SimulateResponse)
async def run_simulation(request: SimulateRequest) -> SimulateResponse:
    """
    Execute a portfolio simulation run.

    Passes the portfolio snapshot to the high-performance Rust engine,
    applies the requested shocks, and returns the aggregated impact.
    """
    start_time = time.time()
    simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

    logger.info(
        "Starting simulation %s with %d shocks (%d iterations)",
        simulation_id,
        len(request.shocks),
        request.iterations,
    )

    try:
        import dsi_sim

        # Parse portfolio and initialize Rust engine
        portfolio_data = json.loads(request.portfolio_json)
        engine = dsi_sim.SimulationEngine(portfolio_data)

        # Build and apply shocks
        rust_shocks = [_build_shock(s) for s in request.shocks]
        
        # Execute (releases GIL for heavy parallel processing)
        result = engine.run_simulation(rust_shocks, request.iterations)
        
        elapsed_ms = (time.time() - start_time) * 1000

        # Map TierMigrations 
        migrations = []
        if hasattr(result, "tier_migrations"):
            for m in result.tier_migrations:
                migrations.append(
                    TierMigration(
                        entity_id=m.entity_id,
                        old_tier=m.old_tier,
                        new_tier=m.new_tier,
                    )
                )

        # Map Stats
        stats_data = getattr(result, "stats", None)

        return SimulateResponse(
            simulation_id=simulation_id,
            status="completed",
            premium_adequacy=getattr(result, "premium_adequacy", 1.0),
            total_premium_impact=getattr(result, "total_premium_impact", 0.0),
            entities_affected=getattr(result, "entities_affected", 0),
            total_entities=getattr(result, "total_entities", 0),
            tier_migrations=migrations,
            stats=SimulationStats(
                mean_score_delta=getattr(stats_data, "mean_score_delta", 0.0),
                std_score_delta=getattr(stats_data, "std_score_delta", 0.0),
                entities_upgraded=getattr(stats_data, "entities_upgraded", 0),
                entities_downgraded=getattr(stats_data, "entities_downgraded", 0),
            ),
            execution_time_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc),
        )

    except ImportError:
        # Stub mode: dsi_sim not compiled, return synthetic response
        logger.warning("dsi_sim Rust extension not available, using stub response")

        elapsed_ms = (time.time() - start_time) * 1000

        return SimulateResponse(
            simulation_id=simulation_id,
            status="completed_stub",
            premium_adequacy=1.0,
            total_premium_impact=0.0,
            entities_affected=0,
            total_entities=0,
            tier_migrations=[],
            stats=SimulationStats(
                mean_score_delta=0.0,
                std_score_delta=0.0,
                entities_upgraded=0,
                entities_downgraded=0,
            ),
            execution_time_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc),
        )