"""
B-2d: Admin config management API.

Endpoints mounted under /api/v1/admin/configs:

    GET  /configs                                        List + statuses
    GET  /configs/{coverage}/{config_name}               Latest content
    GET  /configs/{coverage}/{config_name}/history       Version history
    GET  /configs/versions/{version_id}                  Single version detail
    GET  /configs/versions/{version_id}/diff/{other_id}  Structured diff

    POST /configs/{coverage}/{config_name}               Create a DRAFT
    POST /configs/versions/{version_id}/validate         Run validator
    POST /configs/versions/{version_id}/calibrate        Run calibration harness
    POST /configs/versions/{version_id}/deploy           Promote to DEPLOYED
    POST /configs/{coverage}/{config_name}/rollback      Restore previous deployed

Permissions:
    config:read  for all GETs + DRAFT creation
    config:write for validate / calibrate
    config:deploy for deploy / rollback (highest privilege)
"""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from infrastructure.admin import ConfigDiffEngine, ConfigService
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

logger = logging.getLogger("dsi.api.admin.configs")
router = APIRouter()


# =============================================================================
# Request / response schemas
# =============================================================================


class CreateDraftRequest(BaseModel):
    content: str = Field(min_length=1)
    notes: Optional[str] = None


class ConfigVersionResponse(BaseModel):
    id: str
    coverage: str
    config_name: str
    version_number: int
    config_hash: str
    status: str
    notes: Optional[str]
    author_id: Optional[str]
    created_at: str
    updated_at: str
    has_validation_report: bool
    has_calibration_report: bool


def _to_version_response(row) -> ConfigVersionResponse:
    return ConfigVersionResponse(
        id=row.id,
        coverage=row.coverage,
        config_name=row.config_name,
        version_number=row.version_number,
        config_hash=row.config_hash,
        status=row.status,
        notes=row.notes,
        author_id=row.author_id,
        created_at=row.created_at.isoformat() if row.created_at else "",
        updated_at=row.updated_at.isoformat() if row.updated_at else "",
        has_validation_report=row.validation_report is not None,
        has_calibration_report=row.calibration_report is not None,
    )


def _broadcast_svc(db: Session) -> AuditService:
    return AuditService(
        db,
        broadcaster=get_connection_manager(),
        push_enabled=push_enabled(),
    )


# =============================================================================
# Read endpoints
# =============================================================================


@router.get(
    "/admin/configs",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def list_configs(db: Session = Depends(get_db)) -> dict:
    """List every (coverage, config) pair with its active version + status."""
    return {"configs": ConfigService(db).list_configs()}


@router.get(
    "/admin/configs/{coverage}/{config_name}",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def get_config(
    coverage: str, config_name: str, db: Session = Depends(get_db)
) -> dict:
    """Return the DB latest version's content, or the on-disk YAML if none."""
    svc = ConfigService(db)
    latest = svc.get_latest_version(coverage, config_name)
    if latest is None:
        content = svc.get_active_deployment_content(coverage, config_name)
        if not content:
            raise HTTPException(status_code=404, detail="Config not found")
        return {
            "coverage": coverage,
            "config_name": config_name,
            "source": "on_disk_only",
            "content": content,
            "version_number": 0,
            "status": "DISK_ONLY",
        }
    return {
        "coverage": coverage,
        "config_name": config_name,
        "source": "db",
        "content": latest.content,
        "version_number": latest.version_number,
        "status": latest.status,
        "config_hash": latest.config_hash,
        "notes": latest.notes,
        "validation_report": latest.validation_report,
        "calibration_report": latest.calibration_report,
    }


@router.get(
    "/admin/configs/{coverage}/{config_name}/history",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def get_config_history(
    coverage: str, config_name: str, limit: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)
) -> dict:
    rows = ConfigService(db).list_history(coverage, config_name, limit=limit)
    return {
        "coverage": coverage,
        "config_name": config_name,
        "versions": [_to_version_response(r) for r in rows],
    }


@router.get(
    "/admin/configs/versions/{version_id}",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def get_version(version_id: str, db: Session = Depends(get_db)) -> dict:
    row = ConfigService(db).get_version(version_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {
        **_to_version_response(row).model_dump(),
        "content": row.content,
        "validation_report": row.validation_report,
        "calibration_report": row.calibration_report,
    }


@router.get(
    "/admin/configs/versions/{version_id}/diff/{other_id}",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def diff_versions(
    version_id: str,
    other_id: str,
    db: Session = Depends(get_db),
) -> dict:
    svc = ConfigService(db)
    a = svc.get_version(version_id)
    b = svc.get_version(other_id)
    if a is None or b is None:
        raise HTTPException(status_code=404, detail="One or both versions not found")

    engine = ConfigDiffEngine()
    result = engine.diff(
        a.content, b.content,
        label_a=f"v{a.version_number} ({a.status})",
        label_b=f"v{b.version_number} ({b.status})",
    )
    return {
        "version_a": {"id": a.id, "version_number": a.version_number, "status": a.status},
        "version_b": {"id": b.id, "version_number": b.version_number, "status": b.status},
        "total_changes": result.total_changes,
        "signals_added": result.signals_added,
        "signals_removed": result.signals_removed,
        "signals_changed": result.signals_changed,
        "groups_changed": result.groups_changed,
        "tiers_changed": result.tiers_changed,
        "score_conditions_changed": result.score_conditions_changed,
        "metadata_changes": result.metadata_changes,
        "raw_text_unified": result.raw_text_unified,
    }


# =============================================================================
# Mutation endpoints
# =============================================================================


@router.post(
    "/admin/configs/{coverage}/{config_name}",
    dependencies=[Depends(require_permission(Permission.CONFIG_READ))],
)
def create_draft(
    coverage: str,
    config_name: str,
    body: CreateDraftRequest,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    """Create a DRAFT version. Requires config:read; upgrade to
    config:write or config:deploy to progress it further."""
    svc = ConfigService(db)
    try:
        row = svc.create_draft(
            coverage=coverage,
            config_name=config_name,
            content=body.content,
            author_id=ctx.user_id,
            notes=body.notes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.CONFIG_EDIT,
            resource_type="config_version",
            resource_id=row.id,
            after_state={
                "coverage": coverage,
                "config_name": config_name,
                "version_number": row.version_number,
                "config_hash": row.config_hash,
            },
        )
    )
    db.commit()
    return _to_version_response(row).model_dump()


@router.post(
    "/admin/configs/versions/{version_id}/validate",
    dependencies=[Depends(require_permission(Permission.CONFIG_WRITE))],
)
def validate_version(
    version_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    svc = ConfigService(db)
    try:
        report = svc.validate(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.CONFIG_EDIT,
            resource_type="config_version",
            resource_id=version_id,
            after_state={"action": "validate", "valid": report.get("valid")},
        )
    )
    db.commit()
    return report


@router.post(
    "/admin/configs/versions/{version_id}/calibrate",
    dependencies=[Depends(require_permission(Permission.CONFIG_WRITE))],
)
def calibrate_version(
    version_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict:
    svc = ConfigService(db)
    try:
        report = svc.calibrate(version_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.CONFIG_EDIT,
            resource_type="config_version",
            resource_id=version_id,
            after_state={"action": "calibrate", "success": report.get("success", True)},
        )
    )
    db.commit()
    return report


@router.post(
    "/admin/configs/versions/{version_id}/deploy",
    dependencies=[Depends(require_permission(Permission.CONFIG_DEPLOY))],
)
def deploy_version(
    version_id: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    svc = ConfigService(db)
    try:
        result = svc.deploy(version_id, deployed_by=ctx.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.CONFIG_DEPLOY,
            resource_type="config_version",
            resource_id=version_id,
            after_state=result,
        )
    )
    db.commit()
    return result


@router.post(
    "/admin/configs/{coverage}/{config_name}/rollback",
    dependencies=[Depends(require_permission(Permission.CONFIG_DEPLOY))],
)
def rollback_config(
    coverage: str,
    config_name: str,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> dict:
    svc = ConfigService(db)
    try:
        result = svc.rollback(coverage, config_name, rolled_back_by=ctx.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _broadcast_svc(db).record(
        audit_from_request(
            request,
            action_type=AuditActionType.CONFIG_ROLLBACK,
            resource_type="config",
            resource_id=f"{coverage}/{config_name}",
            after_state=result,
        )
    )
    db.commit()
    return result
