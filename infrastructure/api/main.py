"""
DSI Production API (Phase 11)

FastAPI application for the DSI pricing platform.
"""

import logging
import os
import time
import uuid

from pydantic import BaseModel
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .types import HealthResponse
from .observability.logging_config import configure_logging
from .observability.metrics import metrics, get_metrics_response
from .observability.rate_limiter import RateLimitMiddleware, set_redis_limiter

# Configure structured logging before anything else
configure_logging()
logger = logging.getLogger("dsi.api")


# =============================================================================
# CONFIGURATION
# =============================================================================

class Settings:
    """Application settings from environment."""

    # Environment
    env: str = os.getenv("DSI_ENV", "development")
    debug: bool = os.getenv("DSI_DEBUG", "false").lower() == "true"

    # Server
    host: str = os.getenv("DSI_HOST", "0.0.0.0")
    port: int = int(os.getenv("DSI_PORT", "8000"))

    # CORS - parse comma-separated origins
    cors_origins: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:8080" if os.getenv("DSI_ENV") != "production" else ""
        ).split(",")
        if origin.strip()
    ]
    cors_allow_credentials: bool = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"

    # Feature flags
    use_stubs: bool = os.getenv("FEATURE_USE_STUBS", "true").lower() == "true"
    enable_discovery: bool = os.getenv("FEATURE_DISCOVERY", "true").lower() == "true"
    enable_multi_coverage: bool = os.getenv("FEATURE_MULTI_COVERAGE", "true").lower() == "true"

    @property
    def is_production(self) -> bool:
        return self.env == "production"


settings = Settings()

class DecisionPayload(BaseModel):
    decision: str

# =============================================================================
# APPLICATION STATE
# =============================================================================

class AppState:
    """Application state container."""
    start_time: datetime = datetime.utcnow()
    version: str = "1.0.0"
    request_count: int = 0
    db_connected: bool = False
    cache_connected: bool = False


app_state = AppState()

# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info(f"Starting DSI API (env={settings.env}, debug={settings.debug})...")
    app_state.start_time = datetime.utcnow()
    metrics.set_info(version=app_state.version, environment=settings.env)

    # Initialize database (if available)
    try:
        from ..db.config import init_db
        await init_db()
        app_state.db_connected = True
        metrics.db_connected.set(1)
        logger.info("Database connected")
    except Exception as e:
        logger.warning(f"Database not available: {e}")
        app_state.db_connected = False
        metrics.db_connected.set(0)

    # Initialize Redis cache (if available)
    try:
        import redis.asyncio as redis
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url)
        await redis_client.ping()
        app.state.redis = redis_client
        app_state.cache_connected = True
        metrics.cache_connected.set(1)
        # Upgrade rate limiter to Redis backend
        set_redis_limiter(redis_client)
        logger.info("Redis cache connected (rate limiter upgraded to Redis)")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        app_state.cache_connected = False
        metrics.cache_connected.set(0)

    # Initialize extractor factory mode from feature flag
    try:
        from signal_architecture.signals.extractors.resolver import register_stubs_with_factory
        from signal_architecture.signals.extractors.production.factory import set_default_mode
        from signal_architecture.signals.extractors.production import register_all_extractors

        # Register production extractors (available via factory)
        register_all_extractors()

        # Register stubs as fallbacks
        register_stubs_with_factory()

        # Set mode based on feature flag
        if settings.use_stubs:
            set_default_mode("stub")
            logger.info("Extractor mode: stub (FEATURE_USE_STUBS=true)")
        else:
            set_default_mode("hybrid")
            logger.info("Extractor mode: hybrid (FEATURE_USE_STUBS=false)")
    except Exception as e:
        logger.warning(f"Extractor factory init skipped: {e}")

    # Run configuration health gate — quarantine mis-calibrated configs
    try:
        from infrastructure.models.compiler import initialize_health_gate
        health_results = initialize_health_gate()
        quarantined = {k: v for k, v in health_results.items() if not v.passed}
        if quarantined:
            logger.warning(
                "Health gate: %d config(s) QUARANTINED — they cannot process "
                "live submissions until fixed: %s",
                len(quarantined), list(quarantined.keys()),
            )
        else:
            logger.info("Health gate: all %d configs healthy", len(health_results))
    except Exception as e:
        logger.error(f"Health gate initialization failed: {e}")

    yield

    # Shutdown
    logger.info("Shutting down DSI API...")

    # Close database
    try:
        from ..db.config import close_db
        await close_db()
    except Exception:
        pass

    # Close Redis
    if hasattr(app.state, 'redis'):
        await app.state.redis.close()


# =============================================================================
# APPLICATION
# =============================================================================

app = FastAPI(
    title="DSI Pricing API",
    description="Digital Signal Intelligence - Insurance Pricing Platform",
    version=app_state.version,
    lifespan=lifespan,
    docs_url="/api/docs" if not settings.is_production else None,
    redoc_url="/api/redoc" if not settings.is_production else None,
    openapi_url="/api/openapi.json" if not settings.is_production else None,
)


# =============================================================================
# MIDDLEWARE
# =============================================================================

# CORS - configured from environment
if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-API-Key"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
elif not settings.is_production:
    # Development: allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def request_logging(request: Request, call_next):
    """Log all requests with timing and Prometheus instrumentation."""
    request_id = str(uuid.uuid4())[:8]
    start_time = time.time()

    # Add request ID to request state
    request.state.request_id = request_id
    app_state.request_count += 1

    # Log request (skip health checks in production)
    is_health = "/health" in request.url.path
    if not (settings.is_production and is_health):
        logger.info(f"[{request_id}] {request.method} {request.url.path}")

    try:
        response = await call_next(request)

        # Record metrics
        duration = time.time() - start_time
        if not is_health:
            metrics.observe_request(
                request.method, request.url.path,
                response.status_code, duration,
            )

        if not (settings.is_production and is_health):
            logger.info(
                f"[{request_id}] {request.method} {request.url.path} "
                f"-> {response.status_code} ({duration:.3f}s)"
            )

        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration:.3f}s"
        return response

    except Exception as e:
        duration = time.time() - start_time
        metrics.observe_request(
            request.method, request.url.path, 500, duration,
        )
        metrics.record_error(type(e).__name__)
        logger.error(
            f"[{request_id}] {request.method} {request.url.path} "
            f"-> ERROR ({duration:.3f}s): {e}"
        )
        raise


# Rate limiting middleware
app.add_middleware(RateLimitMiddleware)


# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
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

    # Don't expose internal errors in production
    detail = str(exc) if settings.debug else "Internal server error"

    return JSONResponse(
        status_code=500,
        content={
            "error": detail,
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

    components = {
        "api": "healthy",
        "database": "healthy" if app_state.db_connected else "unavailable",
        "cache": "healthy" if app_state.cache_connected else "unavailable",
    }

    # Overall status
    status = "healthy" if all(v == "healthy" for v in components.values()) else "degraded"

    return HealthResponse(
        status=status,
        version=app_state.version,
        uptime_seconds=uptime,
        components=components,
    )


@app.get("/api/v1/health/ready", tags=["Health"])
async def readiness_check():
    """Kubernetes readiness probe."""
    # Ready if we can process requests (even without DB)
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
        "environment": settings.env,
        "docs": "/api/docs" if not settings.is_production else None,
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
            "frontend": "/api/v1/frontend",
            "simulate": "/api/v1/simulate",
            "modelversion": "/api/v1/modelversion",
            "signals": "/api/v1/signals",
            "health": "/api/v1/health",
        },
        "features": {
            "discovery": settings.enable_discovery,
            "multi_coverage": settings.enable_multi_coverage,
            "using_stubs": settings.use_stubs,
        },
    }


# =============================================================================
# INCLUDE ROUTERS
# =============================================================================

# Import routers after app is created to avoid circular imports
from .routes import submissions, quotes, referrals, analytics, simulate, modelversion, frontend, signals

app.include_router(submissions.router, prefix="/api/v1", tags=["Submissions"])
app.include_router(quotes.router, prefix="/api/v1", tags=["Quotes"])
app.include_router(referrals.router, prefix="/api/v1", tags=["Referrals"])
app.include_router(analytics.router, prefix="/api/v1", tags=["Analytics"])
app.include_router(simulate.router, prefix="/api/v1", tags=["Simulate"])
app.include_router(frontend.router, prefix="/api/v1", tags=["Frontend"])
app.include_router(modelversion.router, prefix="/api/v1", tags=["ModelVersion"])
app.include_router(signals.router, prefix="/api/v1", tags=["Signals"])

# =============================================================================
# METRICS ENDPOINT
# =============================================================================

@app.get("/metrics", tags=["Monitoring"], include_in_schema=False)
async def prometheus_metrics():
    """Prometheus scrape endpoint (text format)."""
    return get_metrics_response()


@app.get("/api/v1/metrics", tags=["Monitoring"])
async def get_metrics_json():
    """Get API metrics (JSON summary for dashboards)."""
    uptime = (datetime.utcnow() - app_state.start_time).total_seconds()

    return {
        "uptime_seconds": uptime,
        "request_count": app_state.request_count,
        "version": app_state.version,
        "environment": settings.env,
        "database_connected": app_state.db_connected,
        "cache_connected": app_state.cache_connected,
    }