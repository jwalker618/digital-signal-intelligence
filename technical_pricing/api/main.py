"""
DSI Production API (Phase 11)

FastAPI application for the DSI pricing platform.
"""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .types import HealthResponse


logger = logging.getLogger("dsi.api")


# =============================================================================
# APPLICATION STATE
# =============================================================================

class AppState:
    """Application state container."""
    start_time: datetime = datetime.utcnow()
    version: str = "1.0.0"
    request_count: int = 0


app_state = AppState()


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting DSI API...")
    app_state.start_time = datetime.utcnow()

    # Initialize components
    # TODO: Initialize database connections, caches, etc.

    yield

    # Shutdown
    logger.info("Shutting down DSI API...")
    # TODO: Cleanup resources


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="DSI Pricing API",
    description="Digital Signal Intelligence - Insurance Pricing Platform",
    version=app_state.version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """Log all requests."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id

    # Log request
    logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Log response
        duration = time.time() - start_time
        logger.info(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> {response.status_code} ({duration:.3f}s)"
        )

        # Add request ID header
        response.headers["X-Request-ID"] = request_id
        return response

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> ERROR ({duration:.3f}s): {e}"
        )
        raise


@app.middleware("http")
async def count_requests(request: Request, call_next):
    """Count all requests."""
    app_state.request_count += 1
    return await call_next(request)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": getattr(request.state, 'request_id', None),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "request_id": getattr(request.state, 'request_id', None),
        },
    )


# =============================================================================
# HEALTH ENDPOINTS
# =============================================================================

@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns API status and component health.
    """
    uptime = (datetime.utcnow() - app_state.start_time).total_seconds()

    return HealthResponse(
        status="healthy",
        version=app_state.version,
        uptime_seconds=uptime,
        components={
            "api": "healthy",
            "database": "healthy",  # TODO: Actual check
            "cache": "healthy",  # TODO: Actual check
        },
    )


@app.get("/api/v1/health/ready", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe."""
    return {"ready": True}


@app.get("/api/v1/health/live", tags=["Health"])
async def liveness_check():
    """Kubernetes liveness probe."""
    return {"alive": True}


# =============================================================================
# ROOT ENDPOINTS
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint."""
    return {
        "name": "DSI Pricing API",
        "version": app_state.version,
        "docs": "/api/docs",
    }


@app.get("/api/v1", tags=["Root"])
async def api_info():
    """API information."""
    return {
        "version": "v1",
        "endpoints": {
            "submissions": "/api/v1/submissions",
            "quotes": "/api/v1/quotes",
            "referrals": "/api/v1/referrals",
            "analytics": "/api/v1/analytics",
            "health": "/api/v1/health",
        },
    }


# =============================================================================
# INCLUDE ROUTERS
# =============================================================================

# Import routers after app is created to avoid circular imports
from .routes import submissions, quotes, referrals, analytics

app.include_router(submissions.router, prefix="/api/v1", tags=["Submissions"])
app.include_router(quotes.router, prefix="/api/v1", tags=["Quotes"])
app.include_router(referrals.router, prefix="/api/v1", tags=["Referrals"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])


# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.get("/api/v1/metrics", tags=["Monitoring"])
async def get_metrics():
    """Get API metrics (for Prometheus, etc.)."""
    uptime = (datetime.utcnow() - app_state.start_time).total_seconds()

    return {
        "uptime_seconds": uptime,
        "request_count": app_state.request_count,
        "version": app_state.version,
    }
