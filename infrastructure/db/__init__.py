"""
DSI Database Layer

Provides database models, session management, and repositories
for persistent storage of submissions, quotes, and audit trails.
"""

from .config import get_db, get_async_db, get_async_engine, get_sync_engine, Base
from .models import (
    Submission,
    Quote,
    Referral,
    ModelVersionRecord,
    SignalCache,
    AuditLog,
    APIKey,
    User,
)
from .repositories import (
    SubmissionRepository,
    QuoteRepository,
    ReferralRepository,
    SignalCacheRepository,
)

__all__ = [
    # Config
    "get_db",
    "get_async_db",
    "get_async_engine",
    "get_sync_engine",
    "Base",
    # Models
    "Submission",
    "Quote",
    "Referral",
    "ModelVersionRecord",
    "SignalCache",
    "AuditLog",
    "APIKey",
    "User",
    # Repositories
    "SubmissionRepository",
    "QuoteRepository",
    "ReferralRepository",
    "SignalCacheRepository",
]
