"""
DSI API Routes (Phase 11)

Route modules for the REST API.
"""

from . import submissions
from . import quotes
from . import referrals
from . import analytics
from . import workbench
from . import simulate

__all__ = [
    "submissions",
    "quotes",
    "referrals",
    "analytics",
    "workbench",
    "simulate"
]
