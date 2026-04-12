"""Admin API routes (B-1 onwards).

Mounted at /api/v1/admin/. All endpoints require admin:system permission
(per-endpoint permission gates may be tighter).
"""

from infrastructure.api.admin.routes import router

__all__ = ["router"]
