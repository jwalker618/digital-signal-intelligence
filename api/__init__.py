"""
DSI Production API Module (Phase 11)

FastAPI-based REST API for the DSI pricing platform.

Usage:
    # Run with uvicorn
    uvicorn technical_pricing.api.main:app --reload

    # Or import the app
    from technical_pricing.api import app

Components:
- main: FastAPI application
- types: Request/response models
- routes: API endpoints
- auth: Authentication handlers
- middleware: Request processing middleware
"""

from .main import app
from .types import (
    # Request models
    SubmissionRequest,
    MultiCoverageRequest,
    ReferralDecision,
    TokenRequest,
    # Response models
    SubmissionResponse,
    SubmissionDetail,
    QuoteResponse,
    QuoteListItem,
    ReferralDetail,
    MultiCoverageResponse,
    PortfolioSummaryResponse,
    HealthResponse,
    JobResponse,
    # Enums
    SubmissionStatus,
    QuoteStatus,
    Permission,
)


__all__ = [
    # Application
    "app",
    # Request models
    "SubmissionRequest",
    "MultiCoverageRequest",
    "ReferralDecision",
    "TokenRequest",
    # Response models
    "SubmissionResponse",
    "SubmissionDetail",
    "QuoteResponse",
    "QuoteListItem",
    "ReferralDetail",
    "MultiCoverageResponse",
    "PortfolioSummaryResponse",
    "HealthResponse",
    "JobResponse",
    # Enums
    "SubmissionStatus",
    "QuoteStatus",
    "Permission",
]
