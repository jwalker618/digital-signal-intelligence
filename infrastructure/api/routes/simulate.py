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
            shock = ShockParameter.signal_override(params.signal_id, params.value)
        elif shock_type == "multiplier":
            shock = ShockParameter.signal_multiplier(params.signal_id, params.value)
        else:
            shock = ShockParameter.signal_multiplier(params.signal_id, params.value)

        if params.industry_filter:
            shock.filter_industry(params.industry_filter)
        if params.tier_filter:
            shock.filter_tier(params.tier_filter)
        if params.coverage_filter:
            shock.filter_coverage(params.coverage_filter)

        return shock

    except ImportError:
        # Stub mode: return dict representation
        return {
            "signal_id": params.signal_id,
            "shock_type": params.shock_type,
            "value": params.value,
            "industry_filter": params.industry_filter,
            "tier_filter": params.tier_filter,
            "coverage_filter": params.coverage_filter,
        }


@router.post("/simulate", response_model=SimulateResponse)
async def run_simulation(request: SimulateRequest):
    """
    Run a portfolio stress-test simulation.

    Sends the portfolio and shock parameters to the Rust dsi-sim engine
    for high-performance parallel computation. Returns premium adequacy
    metrics, tier migration details, and statistical summary.
    """
    simulation_id = str(uuid.uuid4())[:12]
    start_time = time.time()

    # Validate JSON
    try:
        json.loads(request.portfolio_json)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=422, detail=f"Invalid portfolio_json: {e}")

    try:
        # Attempt to use Rust dsi-sim engine
        from dsi_sim import Simulator

        sim = Simulator()

        # Load config if provided
        if request.config_path:
            sim.load_config(request.config_path)

        # Load portfolio
        sim.load_portfolio_json(request.portfolio_json)

        # Build shocks and run
        for shock_params in request.shocks:
            shock = _build_shock(shock_params)
            result = sim.run_simulation(shock, request.iterations)

        elapsed_ms = (time.time() - start_time) * 1000

        # Parse results from Rust
        tier_migrations = []
        if hasattr(result, "tier_migration"):
            for tm in result.tier_migration:
                tier_migrations.append(TierMigration(
                    entity_id=tm.get("entity_id", ""),
                    old_tier=tm.get("old_tier", 0),
                    new_tier=tm.get("new_tier", 0),
                ))

        stats_data = result.stats if hasattr(result, "stats") else {}

        return SimulateResponse(
            simulation_id=simulation_id,
            status="completed",
            premium_adequacy=result.premium_adequacy,
            total_premium_impact=result.total_premium_impact,
            entities_affected=result.entities_affected,
            total_entities=sim.entity_count(),
            tier_migrations=tier_migrations,
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

    except Exception as e:
        logger.error(f"Simulation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Simulation failed: {e}")
