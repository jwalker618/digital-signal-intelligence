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
from . import signals
from . import commercialterms
from . import riskterms

__all__ = [
    "submissions",
    "quotes",
    "referrals",
    "analytics",
    "frontend",
    "simulate",
    "modelversion",
    "commercialterms",
    "riskterms",
    "signals",
]
