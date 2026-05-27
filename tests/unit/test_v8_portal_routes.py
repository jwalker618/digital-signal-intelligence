"""v8 Phase 6 -- portal router structure + role-gate behaviour.

End-to-end portal endpoint behaviour against real data is exercised by
Phase 7's seven-act smoke test (which seeds the DB and walks the demo).
These tests confirm the structural pieces:
  - router mounts cleanly and exposes the 8 documented paths
  - require_portal_user dependency rejects non-portal roles
  - Pydantic response schemas instantiate from typed inputs
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from infrastructure.api.auth.permissions import AuthContext
from infrastructure.api.routes.portal import router as portal_router
from infrastructure.api.routes.portal.dependencies import require_portal_user
from infrastructure.api.routes.portal.schemas import (
    ActionsResponse,
    BrokerInfo,
    BrokerOverviewResponse,
    BrokerQueriesResponse,
    ClientOverviewResponse,
    InitiateSubmissionResponse,
    OpenQueryEntry,
    PeersResponse,
    QuoteEvolutionEntry,
    ScoreResponse,
    SubmissionDetailResponse,
)
from layers.risk.impact_breakdown import ImpactBreakdown
from layers.risk.remediation import RemediationPlan


# =============================================================================
# Router structure
# =============================================================================

class TestRouterStructure:
    def test_router_mounts(self):
        assert portal_router is not None
        assert len(portal_router.routes) > 0

    def test_all_endpoints_present(self):
        paths = {r.path for r in portal_router.routes}
        expected = {
            "/overview",
            "/submissions",
            "/submissions/{submission_code}",
            "/submissions/{submission_code}/score",
            "/submissions/{submission_code}/peers",
            "/submissions/{submission_code}/actions",
            "/queries",
            "/queries/{referral_code}/reply",
            # v8 polish: role-aware communications
            "/communications",
            "/communications/{referral_code}",
            # v8.1: profile, coverage requests, broker recommendations
            "/profile",
            "/coverage-requests",
            "/recommendations",
            "/recommendations/send",
            # v8.2: broker intelligence -- carriers, market, book, aggregation
            "/verticals",
            "/carriers",
            "/carriers/{slug}",
            "/client-health",
            "/placement/{submission_code}",
            "/market/pulse",
            "/market/lines/{line}",
            "/book-health",
            "/aggregation",
        }
        assert expected.issubset(paths)


# =============================================================================
# require_portal_user dependency
# =============================================================================

class TestRequirePortalUser:
    @pytest.mark.asyncio
    async def test_broker_allowed(self):
        ctx = AuthContext(
            user_id="u1", tenant_id="t1", role="BROKER",
            permissions=["portal:broker:read"],
        )
        result = await require_portal_user(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    async def test_client_allowed(self):
        ctx = AuthContext(
            user_id="u1", tenant_id="t1", role="CLIENT",
            permissions=["portal:client:read"],
        )
        result = await require_portal_user(ctx=ctx)
        assert result is ctx

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "carrier_role",
        ["ADMIN", "UNDERWRITER", "SENIOR_UNDERWRITER", "ACTUARIAL", "READ_ONLY"],
    )
    async def test_carrier_roles_rejected(self, carrier_role):
        ctx = AuthContext(
            user_id="u1", tenant_id="t1", role=carrier_role,
            permissions=[],
        )
        with pytest.raises(HTTPException) as exc:
            await require_portal_user(ctx=ctx)
        assert exc.value.status_code == 403

    @pytest.mark.asyncio
    async def test_none_role_rejected(self):
        ctx = AuthContext(
            user_id="u1", tenant_id="t1", role=None, permissions=[],
        )
        with pytest.raises(HTTPException) as exc:
            await require_portal_user(ctx=ctx)
        assert exc.value.status_code == 403


# =============================================================================
# Pydantic response schema shapes
# =============================================================================

class TestSchemas:
    def test_broker_overview_minimum(self):
        r = BrokerOverviewResponse(
            broker=BrokerInfo(id="x", name="Marsh", slug="marsh"),
        )
        assert r.role == "BROKER"
        assert r.clients == []
        assert r.open_queries_count == 0

    def test_client_overview_minimum(self):
        r = ClientOverviewResponse(entity_name="Acme Industries")
        assert r.role == "CLIENT"
        assert r.broker is None
        assert r.active_coverages == []

    def test_score_response_with_breakdown(self):
        bd = ImpactBreakdown(
            base_premium=100_000, final_premium=92_000, total_modifier=0.92,
        )
        r = ScoreResponse(
            submission_code="sub_123",
            coverage="cyber",
            composite_score=685,
            tier=4,
            base_premium=100_000,
            final_premium=92_000,
            impact_breakdown=bd,
        )
        assert r.impact_breakdown is bd

    def test_peers_response_thin_cohort(self):
        r = PeersResponse(
            submission_code="sub_123",
            coverage="cyber",
            note="Insufficient peers",
        )
        assert r.peer_percentile_rank is None
        assert r.note == "Insufficient peers"

    def test_actions_response(self):
        plan = RemediationPlan()
        r = ActionsResponse(
            submission_code="sub_123",
            coverage="cyber",
            remediation_plan=plan,
        )
        assert r.remediation_plan is plan

    def test_submission_detail_with_evolution(self):
        from datetime import datetime, timezone

        ev = QuoteEvolutionEntry(
            quote_code="quo_1",
            version_number=1,
            composite_score=685,
            tier=4,
            final_premium=165_000,
            created_at=datetime.now(timezone.utc),
        )
        r = SubmissionDetailResponse(
            submission_code="sub_1",
            entity_name="Acme",
            coverage="cyber",
            status="ready",
            created_at=datetime.now(timezone.utc),
            quotes=[ev],
        )
        assert len(r.quotes) == 1

    def test_broker_queries_response(self):
        r = BrokerQueriesResponse(
            broker=BrokerInfo(id="b1", name="Marsh", slug="marsh"),
            open_queries=[
                OpenQueryEntry(
                    referral_code="ref_1",
                    submission_code="sub_1",
                    entity_name="Acme",
                    coverage="cyber",
                    request_signal_evidence="mfa_enabled",
                ),
            ],
        )
        assert len(r.open_queries) == 1
        assert r.broker.slug == "marsh"

    def test_initiate_submission_response(self):
        r = InitiateSubmissionResponse(submission_code="sub_x", status="pending")
        assert r.submission_code == "sub_x"


# =============================================================================
# Main app mounts the portal router with the right prefix
# =============================================================================

class TestAppMount:
    def test_portal_mounted_at_correct_prefix(self):
        from infrastructure.api.main import app
        paths = [route.path for route in app.routes if hasattr(route, "path")]
        portal_paths = [p for p in paths if "/portal" in p]
        assert any("/api/v1/portal/overview" in p for p in portal_paths)
        assert any("/api/v1/portal/queries" in p for p in portal_paths)
