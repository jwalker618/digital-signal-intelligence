"""Admin API routes (B-1 onwards).

Mounted at /api/v1/admin/. Per-endpoint permission gating is applied via
Depends(require_permission(...)) -- the package has no tenant-level
catch-all gate so individual endpoints can express their own minimum
permission.
"""

from fastapi import APIRouter

from infrastructure.api.admin.routes import router as health_router
from infrastructure.api.admin.config_routes import router as config_router
from infrastructure.api.admin.user_routes import router as user_router

# Aggregate router that mounts all sub-routers at the same prefix. This
# keeps the main app's include_router call simple.
router = APIRouter()
router.include_router(health_router)
router.include_router(config_router)
router.include_router(user_router)

__all__ = ["router"]
