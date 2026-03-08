"""
DSI API Routes (Phase 11)

Route modules for the REST API.
"""

from . import submissions
from . import quotes
from . import referrals
from . import analytics
from . import frontend
from . import simulate
from . import modelversion

__all__ = [
    "submissions",
    "quotes",
    "referrals",
    "analytics",
    "frontend",
    "simulate",
    "modelversion",
]
