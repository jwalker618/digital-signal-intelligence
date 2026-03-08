"""
DSI Production API Module (Phase 11)

FastAPI-based REST API for the DSI pricing platform.

Usage:
    # Run with uvicorn
    uvicorn api.main:app --reload

    # Or import the app
    from api import app

Components:
- main: FastAPI application
- types: Request/response models
- routes: API endpoints
- auth: Authentication handlers
- middleware: Request processing middleware
"""

from .main import app
from .utils import generate_id
from .types import (
    # Request models
    SubmissionRequest,
    MultiCoverageRequest,
    ReferralDecision,
    TokenRequest,
    # Response models
    SubmissionResponse,
    SubmissionRecord,
    QuoteResponse,
    QuoteListItem,
    ReferralRecord,
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
