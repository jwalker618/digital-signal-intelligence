"""
DSI Live Demo Server

A standalone demo server that runs the actual DSI workflow with stub extractors.
This provides a realistic simulation of the production system.

Usage:
    python -m demo.server

Then open http://localhost:8080 in your browser.
"""

import json
import os
import sys
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Import DSI components
from layers.risk.workflow import run_assessment
from layers.risk.types import WorkflowResult, DecisionType
from layers.risk.config_manager import ConfigManager


# =============================================================================
# CONFIGURATION
# =============================================================================

DEMO_PORT = int(os.getenv("DEMO_PORT", "8080"))
DEMO_HOST = os.getenv("DEMO_HOST", "0.0.0.0")

# Available coverages
COVERAGES = ["aerospace", "cyber", "do", "energy", "fi", "marine", "pi"]

# Sample companies for demos
SAMPLE_COMPANIES = [
    {"name": "Acme Technology Corp", "domain": "acmetech.com", "country": "US"},
    {"name": "Global Financial Services", "domain": "globalfs.com", "country": "US"},
    {"name": "Pacific Energy Holdings", "domain": "pacificenergy.com", "country": "US"},
    {"name": "Northern Airlines", "domain": "northernair.com", "country": "US"},
    {"name": "Maritime Shipping Co", "domain": "maritimeship.com", "country": "UK"},
    {"name": "Tech Consulting Partners", "domain": "techconsult.io", "country": "US"},
    {"name": "European Industrial Group", "domain": "eurindustrial.de", "country": "DE"},
    {"name": "Asia Pacific Insurance", "domain": "apinsurance.sg", "country": "SG"},
]


# =============================================================================
# API MODELS
# =============================================================================

class AssessmentRequest(BaseModel):
    """Request model for running an assessment."""
    entity_name: str
    domain_hint: Optional[str] = None
    country_hint: Optional[str] = "US"
    coverage: str = "cyber"
    submission_data: Optional[Dict[str, Any]] = None


class SignalOutput(BaseModel):
    """Signal output for display."""
    signal_id: str
    signal_name: str
    group_id: str
    raw_score: float
    weighted_score: float
    weight: float
    confidence: float


class AssessmentResult(BaseModel):
    """Simplified assessment result for demo display."""
    entity_id: str
    entity_name: str
    coverage: str

    # Discovery
    discovered_domain: Optional[str]
    discovery_confidence: Optional[str]

    # Scoring
    composite_score: float
    confidence: float
    tier: int
    tier_label: str

    # Decision
    decision: str
    auto_approve: bool
    referral_reasons: List[str]

    # Pricing
    recommended_premium: float
    premium_options: Dict[str, float]

    # Signals
    signals: List[SignalOutput]
    group_scores: Dict[str, float]

    # Timing
    processing_time_ms: float
    timestamp: str


class CoverageInfo(BaseModel):
    """Coverage configuration info."""
    name: str
    signal_count: int
    signal_groups: List[str]
    tier_count: int
    description: str


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="DSI Live Demo",
    description="Interactive demonstration of Digital Signal Intelligence",
    version="1.0.0",
)

# CORS for demo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# DEMO STATE
# =============================================================================

class DemoState:
    """Track demo statistics."""
    assessments_run: int = 0
    total_processing_time: float = 0
    tier_distribution: Dict[int, int] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    decision_distribution: Dict[str, int] = {"approve": 0, "refer": 0, "decline": 0}
    coverage_usage: Dict[str, int] = {c: 0 for c in COVERAGES}
    start_time: datetime = datetime.utcnow()


demo_state = DemoState()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def workflow_to_result(
    result: WorkflowResult,
    entity_name: str,
    processing_time: float,
) -> AssessmentResult:
    """Convert WorkflowResult to demo display format."""

    # Extract signals
    signals = []
    if result.model_version and result.model_version.signal_outputs:
        for output in result.model_version.signal_outputs:
            signals.append(SignalOutput(
                signal_id=output.signal_id,
                signal_name=output.signal_name,
                group_id=output.group_id,
                raw_score=output.raw_score,
                weighted_score=output.weighted_score,
                weight=output.weight,
                confidence=output.confidence,
            ))

    # Get group scores
    group_scores = {}
    if result.model_version:
        group_scores = result.model_version.group_scores or {}

    # Decision mapping
    decision_map = {
        DecisionType.APPROVE: "approve",
        DecisionType.REFER: "refer",
        DecisionType.DECLINE: "decline",
    }

    return AssessmentResult(
        entity_id=result.entity_id,
        entity_name=entity_name,
        coverage=result.coverage,
        discovered_domain=result.discovered_domain,
        discovery_confidence=result.discovery_confidence,
        composite_score=result.composite_score,
        confidence=result.confidence,
        tier=result.tier,
        tier_label=result.tier_label,
        decision=decision_map.get(result.decision, "refer"),
        auto_approve=result.auto_approve,
        referral_reasons=result.referral_reasons or [],
        recommended_premium=result.recommended_premium,
        premium_options=result.premium_options or {},
        signals=signals,
        group_scores=group_scores,
        processing_time_ms=processing_time * 1000,
        timestamp=datetime.utcnow().isoformat(),
    )


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main demo page."""
    demo_path = Path(__file__).parent / "index.html"
    if demo_path.exists():
        return FileResponse(demo_path)
    return HTMLResponse("<h1>DSI Demo</h1><p>Demo files not found.</p>")


@app.get("/api/info")
async def get_info():
    """Get demo server info."""
    uptime = (datetime.utcnow() - demo_state.start_time).total_seconds()
    avg_time = (
        demo_state.total_processing_time / demo_state.assessments_run
        if demo_state.assessments_run > 0 else 0
    )

    return {
        "name": "DSI Live Demo",
        "version": "1.0.0",
        "uptime_seconds": uptime,
        "assessments_run": demo_state.assessments_run,
        "average_processing_ms": avg_time * 1000,
        "tier_distribution": demo_state.tier_distribution,
        "decision_distribution": demo_state.decision_distribution,
        "coverage_usage": demo_state.coverage_usage,
        "available_coverages": COVERAGES,
        "sample_companies": SAMPLE_COMPANIES,
    }


@app.get("/api/coverages")
async def list_coverages():
    """List available coverages with details."""
    coverages = []
    config_manager = ConfigManager()

    coverage_descriptions = {
        "aerospace": "Aviation hull, liability, and space risks",
        "cyber": "First-party, third-party, and combined cyber coverage",
        "do": "Directors & Officers liability for corporate governance",
        "energy": "Upstream, midstream, and downstream energy operations",
        "fi": "Financial institutions professional liability",
        "marine": "Hull, cargo, and P&I coverage for maritime",
        "pi": "Professional indemnity for service providers",
    }

    for coverage in COVERAGES:
        try:
            config = config_manager.load_config(coverage)
            signal_groups = list(config.get("signal_groups", {}).keys())
            signals = config.get("signals", [])
            tiers = config.get("tiers", [])

            coverages.append(CoverageInfo(
                name=coverage,
                signal_count=len(signals),
                signal_groups=signal_groups,
                tier_count=len(tiers),
                description=coverage_descriptions.get(coverage, ""),
            ))
        except Exception as e:
            coverages.append(CoverageInfo(
                name=coverage,
                signal_count=0,
                signal_groups=[],
                tier_count=5,
                description=f"Error loading: {e}",
            ))

    return {"coverages": coverages}


@app.get("/api/coverage/{coverage}")
async def get_coverage_details(coverage: str):
    """Get detailed coverage configuration."""
    if coverage not in COVERAGES:
        raise HTTPException(status_code=404, detail=f"Coverage '{coverage}' not found")

    config_manager = ConfigManager()
    try:
        config = config_manager.load_config(coverage)
        return {
            "coverage": coverage,
            "signals": config.get("signals", []),
            "signal_groups": config.get("signal_groups", {}),
            "tiers": config.get("tiers", []),
            "direct_optional_queries": config.get("direct_optional_queries", []),
            "categorical_features": config.get("categorical_features", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/assess", response_model=AssessmentResult)
async def run_assessment_endpoint(request: AssessmentRequest):
    """Run a live DSI assessment."""
    if request.coverage not in COVERAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coverage. Must be one of: {COVERAGES}"
        )

    # Generate entity ID
    entity_id = f"demo_{int(time.time() * 1000)}"

    # Run assessment
    start_time = time.time()

    try:
        result = run_assessment(
            entity_id=entity_id,
            coverage=request.coverage,
            entity_name=request.entity_name,
            domain_hint=request.domain_hint,
            country_hint=request.country_hint,
            submission_data=request.submission_data or {},
            skip_discovery=True,  # Use stub extractors
            skip_input_validation=True,  # Demo doesn't require all inputs
        )

        processing_time = time.time() - start_time

        # Update demo stats
        demo_state.assessments_run += 1
        demo_state.total_processing_time += processing_time
        demo_state.tier_distribution[result.tier] = (
            demo_state.tier_distribution.get(result.tier, 0) + 1
        )
        decision = result.decision.value if result.decision else "refer"
        demo_state.decision_distribution[decision] = (
            demo_state.decision_distribution.get(decision, 0) + 1
        )
        demo_state.coverage_usage[request.coverage] = (
            demo_state.coverage_usage.get(request.coverage, 0) + 1
        )

        return workflow_to_result(result, request.entity_name, processing_time)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/batch-assess")
async def batch_assessment(
    coverage: str = Query(...),
    count: int = Query(10, ge=1, le=100),
):
    """Run batch assessments for statistical demonstration."""
    if coverage not in COVERAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid coverage. Must be one of: {COVERAGES}"
        )

    results = []

    for i, company in enumerate(SAMPLE_COMPANIES[:count]):
        entity_id = f"batch_{int(time.time() * 1000)}_{i}"

        start_time = time.time()
        result = run_assessment(
            entity_id=entity_id,
            coverage=coverage,
            entity_name=company["name"],
            domain_hint=company["domain"],
            country_hint=company["country"],
            skip_discovery=True,
            skip_input_validation=True,
        )
        processing_time = time.time() - start_time

        results.append(workflow_to_result(result, company["name"], processing_time))

    # Aggregate statistics
    scores = [r.composite_score for r in results]
    tiers = [r.tier for r in results]
    premiums = [r.recommended_premium for r in results]

    return {
        "count": len(results),
        "results": results,
        "statistics": {
            "avg_score": sum(scores) / len(scores),
            "min_score": min(scores),
            "max_score": max(scores),
            "avg_premium": sum(premiums) / len(premiums),
            "tier_distribution": {
                tier: tiers.count(tier) for tier in range(1, 6)
            },
            "decision_distribution": {
                "approve": sum(1 for r in results if r.decision == "approve"),
                "refer": sum(1 for r in results if r.decision == "refer"),
                "decline": sum(1 for r in results if r.decision == "decline"),
            },
        },
    }


@app.get("/api/samples")
async def get_sample_companies():
    """Get sample companies for testing."""
    return {"companies": SAMPLE_COMPANIES}


# =============================================================================
# STATIC FILES
# =============================================================================

# Mount static files if directory exists
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run the demo server."""
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                    DSI LIVE DEMO SERVER                          ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  Starting demo server...                                         ║
║                                                                  ║
║  Open in browser: http://localhost:{DEMO_PORT}                       ║
║                                                                  ║
║  API Endpoints:                                                  ║
║    GET  /api/info          - Server info & statistics            ║
║    GET  /api/coverages     - List available coverages            ║
║    GET  /api/coverage/{{id}} - Coverage configuration details     ║
║    POST /api/assess        - Run live assessment                 ║
║    POST /api/batch-assess  - Run batch assessments               ║
║    GET  /api/samples       - Sample companies                    ║
║                                                                  ║
║  Press Ctrl+C to stop                                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host=DEMO_HOST,
        port=DEMO_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
