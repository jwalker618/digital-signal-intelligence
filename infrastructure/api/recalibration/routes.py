"""
C-3: Recalibration Governance API routes.

Propose-and-approve governance UI backend. Consumes C-2's
recalibration_proposals rows, exposes them for actuarial review, and
deploys approved proposals via the B-2 ConfigService pipeline.

Endpoints (all tenant-scoped):

    GET  /recalibration/proposals                          List with filters
    GET  /recalibration/proposals/{id}                     Full proposal detail
    POST /recalibration/proposals/{id}/approve             Mandatory rationale
    POST /recalibration/proposals/{id}/reject              Mandatory rationale
    POST /recalibration/proposals/{id}/deploy              Via B-2 pipeline
    POST /recalibration/proposals/{id}/simulate            Dry-run impact review
    POST /recalibration/trigger                            Manually trigger engine

Permissions:
    recalibration:view    for GETs + simulate
    recalibration:approve for approve / reject / deploy / trigger
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from infrastructure.api.audit import (
    AuditActionType,
    AuditService,
    audit_from_request,
    push_enabled,
)
from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    get_auth_context,
    require_permission,
)
from infrastructure.api.websocket import get_connection_manager
from infrastructure.db.config import get_db
from infrastructure.recalibration import (
    DeploymentError,
    ProposalDeployer,
    RecalibrationEngine,
)

logger = logging.getLogger("dsi.api.recalibration")
router = APIRouter()


# =============================================================================
# Schemas
# =============================================================================


class ProposalSummary(BaseModel):
    id: str
    coverage: str
    config_name: str
    status: str
    proposed_at: datetime
    proposed_by: str
    trigger: str
    sample_size: int
    weight_change_count: int
    tier_change_count: int
    reviewer_id: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    deployed_at: Optional[datetime] = None


class ApproveRequest(BaseModel):
    rationale: str = Field(min_length=1, max_length=10_000)


class RejectRequest(BaseModel):
    rationale: str = Field(min_length=1, max_length=10_000)


class TriggerRequest(BaseModel):
    coverage: str
    config_name: str
    current_weights: dict[str, float]
    tier_boundaries: list[list[float]] = Field(default_factory=list)
    # e.g. [[1, 0, 300], [2, 300, 600], [3, 600, 1000]]


# =============================================================================
# Helpers
# =============================================================================


def _broadcast_svc(db: Session) -> AuditService:
    return AuditService(
        db,
        broadcaster=get_connection_manager(),
        push_enabled=push_enabled(),
    )


def _load_proposal_row(db: Session, tenant_id: str, proposal_id: str) -> dict:
    row = db.execute(
        text(
            """
            SELECT id::text, tenant_id::text, coverage, config_name,
                   status, proposed_at, proposed_by, trigger, sample_size,
                   signal_report_cards, weight_changes, tier_threshold_changes,
                   impact_assessment, statistical_evidence,
                   reviewer_id::text, review_decision, review_rationale,
                   reviewed_at, deployed_config_version_id::text, deployed_at,
                   updated_at
            FROM recalibration_proposals
            WHERE id = :id AND tenant_id = :tenant_id
            """
        ),
        {"id": proposal_id, "tenant_id": tenant_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Proposal not found")
    return dict(row)


def _to_summary(row: dict) -> ProposalSummary:
    return ProposalSummary(
        id=row["id"],
        coverage=row["coverage"],
        config_name=row["config_name"],
        status=row["status"],
        proposed_at=row["proposed_at"],
        proposed_by=row["proposed_by"],
        trigger=row["trigger"],
        sample_size=int(row["sample_size"] or 0),
        weight_change_count=len(row["weight_changes"] or []),
        tier_change_count=len(row["tier_threshold_changes"] or []),
        reviewer_id=row.get("reviewer_id"),
        reviewed_at=row.get("reviewed_at"),
        deployed_at=row.get("deployed_at"),
    )


# =============================================================================
# List + detail
# =============================================================================


@router.get(
    "/recalibration/proposals",
    response_model=list[ProposalSummary],
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_VIEW))],
)
def list_proposals(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    coverage: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(default=100, ge=1, le=500),
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> list[ProposalSummary]:
    conditions = ["tenant_id = :tenant_id"]
    params: dict = {"tenant_id": ctx.tenant_id, "limit": limit}
    if status_filter:
        conditions.append("status = :status")
        params["status"] = status_filter
    if coverage:
        conditions.append("coverage = :coverage")
        params["coverage"] = coverage
    if date_from:
        conditions.append("proposed_at >= :date_from")
        params["date_from"] = date_from
    if date_to:
        conditions.append("proposed_at <= :date_to")
        params["date_to"] = date_to

    where = " WHERE " + " AND ".join(conditions)
    rows = db.execute(
        text(
            f"""
            SELECT id::text, coverage, config_name, status,
                   proposed_at, proposed_by, trigger, sample_size,
                   weight_changes, tier_threshold_changes,
                   reviewer_id::text, reviewed_at, deployed_at
            FROM recalibration_proposals{where}
            ORDER BY proposed_at DESC LIMIT :limit
            """
        ),
        params,
    ).mappings().all()
    return [_to_summary(dict(r)) for r in rows]


@router.get(
    "/recalibration/proposals/{proposal_id}",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_VIEW))],
)
def get_proposal(
    proposal_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_proposal_row(db, ctx.tenant_id, proposal_id)
    # Convert datetimes and JSONB to plain dict for response
    return {
        "id": row["id"],
        "coverage": row["coverage"],
        "config_name": row["config_name"],
        "status": row["status"],
        "proposed_at": row["proposed_at"].isoformat() if row["proposed_at"] else None,
        "proposed_by": row["proposed_by"],
        "trigger": row["trigger"],
        "sample_size": int(row["sample_size"] or 0),
        "signal_report_cards": row["signal_report_cards"] or [],
        "weight_changes": row["weight_changes"] or [],
        "tier_threshold_changes": row["tier_threshold_changes"] or [],
        "impact_assessment": row["impact_assessment"] or {},
        "statistical_evidence": row["statistical_evidence"] or {},
        "reviewer_id": row.get("reviewer_id"),
        "review_decision": row.get("review_decision"),
        "review_rationale": row.get("review_rationale"),
        "reviewed_at": row["reviewed_at"].isoformat() if row.get("reviewed_at") else None,
        "deployed_config_version_id": row.get("deployed_config_version_id"),
        "deployed_at": row["deployed_at"].isoformat() if row.get("deployed_at") else None,
    }


# =============================================================================
# Simulate (dry-run)
# =============================================================================


@router.post(
    "/recalibration/proposals/{proposal_id}/simulate",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_VIEW))],
)
def simulate_proposal(
    proposal_id: str,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """What-if dry-run: return the proposed YAML + impact summary without persisting."""
    _load_proposal_row(db, ctx.tenant_id, proposal_id)  # tenant check
    return ProposalDeployer(db).simulate(proposal_id)


# =============================================================================
# Approve / Reject
# =============================================================================


@router.post(
    "/recalibration/proposals/{proposal_id}/approve",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_APPROVE))],
)
def approve_proposal(
    proposal_id: str,
    body: ApproveRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_proposal_row(db, ctx.tenant_id, proposal_id)
    if row["status"] not in ("DRAFT", "PENDING_REVIEW"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve proposal in status {row['status']}",
        )

    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            UPDATE recalibration_proposals
            SET status = 'APPROVED',
                reviewer_id = :reviewer_id,
                review_decision = 'APPROVED',
                review_rationale = :rationale,
                reviewed_at = :now,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {
            "id": proposal_id,
            "reviewer_id": ctx.user_id,
            "rationale": body.rationale,
            "now": now,
        },
    )

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.RECALIBRATION_APPROVE,
            resource_type="recalibration_proposal",
            resource_id=proposal_id,
            before_state={"status": row["status"]},
            after_state={"status": "APPROVED", "rationale": body.rationale},
        )
    )
    db.commit()
    return {
        "id": proposal_id,
        "status": "APPROVED",
        "reviewer_id": ctx.user_id,
        "reviewed_at": now.isoformat(),
    }


@router.post(
    "/recalibration/proposals/{proposal_id}/reject",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_APPROVE))],
)
def reject_proposal(
    proposal_id: str,
    body: RejectRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_proposal_row(db, ctx.tenant_id, proposal_id)
    if row["status"] not in ("DRAFT", "PENDING_REVIEW", "APPROVED"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject proposal in status {row['status']}",
        )

    now = datetime.now(timezone.utc)
    db.execute(
        text(
            """
            UPDATE recalibration_proposals
            SET status = 'REJECTED',
                reviewer_id = :reviewer_id,
                review_decision = 'REJECTED',
                review_rationale = :rationale,
                reviewed_at = :now,
                updated_at = :now
            WHERE id = :id
            """
        ),
        {
            "id": proposal_id,
            "reviewer_id": ctx.user_id,
            "rationale": body.rationale,
            "now": now,
        },
    )

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.RECALIBRATION_REJECT,
            resource_type="recalibration_proposal",
            resource_id=proposal_id,
            before_state={"status": row["status"]},
            after_state={"status": "REJECTED", "rationale": body.rationale},
        )
    )
    db.commit()
    return {
        "id": proposal_id,
        "status": "REJECTED",
        "reviewer_id": ctx.user_id,
        "reviewed_at": now.isoformat(),
    }


# =============================================================================
# Deploy
# =============================================================================


@router.post(
    "/recalibration/proposals/{proposal_id}/deploy",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_APPROVE))],
)
def deploy_proposal(
    proposal_id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    row = _load_proposal_row(db, ctx.tenant_id, proposal_id)
    try:
        result = ProposalDeployer(db).deploy(
            proposal_id=proposal_id, deployer_id=ctx.user_id
        )
    except DeploymentError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.RECALIBRATION_DEPLOY,
            resource_type="recalibration_proposal",
            resource_id=proposal_id,
            before_state={"status": row["status"]},
            after_state={
                "status": "DEPLOYED",
                "config_version_id": result.config_version_id,
                "coverage": result.coverage,
                "config_name": result.config_name,
            },
        )
    )
    db.commit()
    return {
        "proposal_id": proposal_id,
        "status": "DEPLOYED",
        "config_version_id": result.config_version_id,
        "coverage": result.coverage,
        "config_name": result.config_name,
        "deployed_at": result.deployed_at.isoformat(),
    }


# =============================================================================
# Manual trigger
# =============================================================================


@router.post(
    "/recalibration/trigger",
    dependencies=[Depends(require_permission(Permission.RECALIBRATION_APPROVE))],
)
def trigger_recalibration(
    body: TriggerRequest,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """Manually trigger the recalibration engine to produce a new proposal.

    Normally the engine runs on a schedule -- this endpoint lets an
    actuarial user force a run when they have reason to expect the
    recommendation has changed (e.g. just ingested fresh loss data)."""
    tier_boundaries = [
        (int(tb[0]), float(tb[1]), float(tb[2])) for tb in body.tier_boundaries
    ]
    payload = RecalibrationEngine(db).run(
        tenant_id=ctx.tenant_id,
        coverage=body.coverage,
        config_name=body.config_name,
        current_weights=body.current_weights,
        current_tier_boundaries=tier_boundaries,
        proposed_by=ctx.user_id or "system",
        trigger="manual",
    )
    db.commit()
    if payload is None:
        return {"created": False, "reason": "Insufficient sample size"}
    return {
        "created": True,
        "proposal_id": payload.id,
        "coverage": payload.coverage,
        "config_name": payload.config_name,
        "weight_changes": len(payload.weight_changes),
        "tier_changes": len(payload.tier_threshold_changes),
        "sample_size": payload.sample_size,
    }
