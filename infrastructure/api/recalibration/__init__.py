"""C-3: Recalibration Governance API.

Mounted at /api/v1/recalibration/. Permission-gated by recalibration:view
and recalibration:approve (the latter for approve/reject/deploy).
"""

from infrastructure.api.recalibration.routes import router

__all__ = ["router"]
