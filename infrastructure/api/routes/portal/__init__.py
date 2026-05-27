"""v8 Phase 6: client portal API surface.

Mounted at /api/v1/portal/*. Consolidates the data products from
phases 2-5 (cohort, impact breakdown, remediation, broker query/reply)
behind a single role-scoped surface for BROKER and CLIENT users.

No new business logic in this module -- pure plumbing + role / scope
guards. Each submodule defines a thin router; this package's `router`
aggregates them.
"""
from fastapi import APIRouter

from . import (
    broker_intel,
    communications,
    overview,
    profile_and_actions,
    queries,
    submissions,
)

router = APIRouter()
router.include_router(overview.router)
router.include_router(submissions.router)
router.include_router(queries.router)
router.include_router(communications.router)
router.include_router(profile_and_actions.router)
router.include_router(broker_intel.router)

__all__ = ["router"]
