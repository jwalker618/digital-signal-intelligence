"""
DSI Email Integration (Phase 12)

Email inbox monitoring and submission creation.
"""

from .base import EmailIntegration
from .parser import EmailParser, SubmissionParser

__all__ = [
    "EmailIntegration",
    "EmailParser",
    "SubmissionParser",
]
