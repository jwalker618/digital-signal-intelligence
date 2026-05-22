"""v8 Phase 6: client portal API surface.

Mounted at /api/v1/portal/*. Consolidates the data products from
phases 2-5 (cohort, impact breakdown, remediation, broker query/reply)
behind a single role-scoped surface for BROKER and CLIENT users.

No new business logic in this module -- pure plumbing + role / scope
guards. Each submodule defines a thin router; this package's `router`
aggregates them.
"""
from fastapi import APIRouter

from . import overview, submissions, queries

router = APIRouter()
router.include_router(overview.router)
router.include_router(submissions.router)
router.include_router(queries.router)

__all__ = ["router"]
