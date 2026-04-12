"""
C-1d: Loss Data API Routes

Mounted at /api/v1/losses. All endpoints require authentication and tenant
scoping is enforced via the authenticated context.

Endpoints:
- POST   /losses              Create a single loss event (auto-links)
- POST   /losses/import       Bulk CSV/JSON import
- GET    /losses              List with filters + cursor pagination
- GET    /losses/{id}         Single event with linked assessment
- PUT    /losses/{id}         Update amounts, status, etc.
- POST   /losses/{id}/relink  Force re-link for this loss event
- POST   /losses/link-all     Batch retrospective link (admin)
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import and_, select
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
from infrastructure.db.models import LossEvent, ModelVersionRecord, SignalLossPair
from infrastructure.recalibration import SignalLossLinker

logger = logging.getLogger("dsi.api.losses")
router = APIRouter()


# =============================================================================
# Request / response schemas
# =============================================================================


class LossEventCreate(BaseModel):
    entity_name: str = Field(min_length=1, max_length=500)
    coverage: str = Field(min_length=1, max_length=50)
    loss_date: datetime
    loss_type: str = Field(min_length=1, max_length=100)
    incurred_amount: float = Field(ge=0.0)
    paid_amount: float = Field(default=0.0, ge=0.0)
    reserved_amount: float = Field(default=0.0, ge=0.0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    status: str = Field(default="OPEN")
    # Optional fields
    quote_id: Optional[UUID] = None
    policy_reference: Optional[str] = None
    claim_reference: Optional[str] = None
    notification_date: Optional[datetime] = None
    closed_date: Optional[datetime] = None
    config_name: Optional[str] = None
    cause_description: Optional[str] = None
    event_metadata: dict = Field(default_factory=dict)

    @field_validator("status")
    @classmethod
    def _status_enum(cls, v: str) -> str:
        v = v.upper()
        if v not in {"OPEN", "CLOSED", "REOPENED"}:
            raise ValueError("status must be OPEN, CLOSED, or REOPENED")
        return v


class LossEventUpdate(BaseModel):
    incurred_amount: Optional[float] = Field(default=None, ge=0.0)
    paid_amount: Optional[float] = Field(default=None, ge=0.0)
    reserved_amount: Optional[float] = Field(default=None, ge=0.0)
    status: Optional[str] = None
    closed_date: Optional[datetime] = None
    cause_description: Optional[str] = None
    event_metadata: Optional[dict] = None

    @field_validator("status")
    @classmethod
    def _status_enum(cls, v):
        if v is None:
            return v
        v = v.upper()
        if v not in {"OPEN", "CLOSED", "REOPENED"}:
            raise ValueError("status must be OPEN, CLOSED, or REOPENED")
        return v


class LossEventResponse(BaseModel):
    id: str
    tenant_id: str
    entity_name: str
    quote_id: Optional[str]
    policy_reference: Optional[str]
    claim_reference: Optional[str]
    loss_date: datetime
    notification_date: Optional[datetime]
    closed_date: Optional[datetime]
    loss_type: str
    coverage: str
    config_name: Optional[str]
    incurred_amount: float
    paid_amount: float
    reserved_amount: float
    currency: str
    status: str
    cause_description: Optional[str]
    event_metadata: dict
    linked_assessment_id: Optional[str]
    linker_run_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_row(cls, row: LossEvent) -> "LossEventResponse":
        return cls(
            id=str(row.id),
            tenant_id=str(row.tenant_id),
            entity_name=row.entity_name,
            quote_id=str(row.quote_id) if row.quote_id else None,
            policy_reference=row.policy_reference,
            claim_reference=row.claim_reference,
            loss_date=row.loss_date,
            notification_date=row.notification_date,
            closed_date=row.closed_date,
            loss_type=row.loss_type,
            coverage=row.coverage,
            config_name=row.config_name,
            incurred_amount=float(row.incurred_amount or 0.0),
            paid_amount=float(row.paid_amount or 0.0),
            reserved_amount=float(row.reserved_amount or 0.0),
            currency=row.currency,
            status=row.status,
            cause_description=row.cause_description,
            event_metadata=row.event_metadata or {},
            linked_assessment_id=str(row.linked_assessment_id) if row.linked_assessment_id else None,
            linker_run_at=row.linker_run_at,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class LossListResponse(BaseModel):
    losses: list[LossEventResponse]
    next_cursor: Optional[str] = None
    total: int


class LinkResultResponse(BaseModel):
    linked: bool
    loss_event_id: str
    assessment_id: Optional[str] = None
    pair_id: Optional[str] = None
    reason: Optional[str] = None
    signals_captured: int = 0


class BulkImportResponse(BaseModel):
    total: int
    imported: int
    skipped: int
    errors: list[dict]
    link_results: dict  # summary of retrospective linking after import


class RetrospectiveReportResponse(BaseModel):
    total_candidates: int
    newly_linked: int
    already_linked: int
    unlinked_no_quote: int
    unlinked_no_assessment: int
    errors: list[str]


# =============================================================================
# Helpers
# =============================================================================


def _broadcast_svc(db: Session) -> AuditService:
    return AuditService(
        db,
        broadcaster=get_connection_manager(),
        push_enabled=push_enabled(),
    )


def _apply_create(db: Session, tenant_id: str, user_id: str, body: LossEventCreate) -> LossEvent:
    loss = LossEvent(
        tenant_id=UUID(tenant_id),
        entity_name=body.entity_name,
        quote_id=body.quote_id,
        policy_reference=body.policy_reference,
        claim_reference=body.claim_reference,
        loss_date=body.loss_date,
        notification_date=body.notification_date,
        closed_date=body.closed_date,
        loss_type=body.loss_type,
        coverage=body.coverage,
        config_name=body.config_name,
        incurred_amount=body.incurred_amount,
        paid_amount=body.paid_amount,
        reserved_amount=body.reserved_amount,
        currency=body.currency.upper(),
        status=body.status,
        cause_description=body.cause_description,
        event_metadata=body.event_metadata,
        created_by=UUID(user_id) if user_id else None,
    )
    db.add(loss)
    db.flush()
    return loss


# =============================================================================
# Endpoints
# =============================================================================


@router.post(
    "/losses",
    response_model=LossEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_WRITE))],
)
def create_loss(
    body: LossEventCreate,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LossEventResponse:
    """Create a single loss event. Automatically attempts to link it."""
    loss = _apply_create(db, ctx.tenant_id, ctx.user_id, body)

    # Auto-link
    link_result = SignalLossLinker(db).link(str(loss.id))
    logger.info("Loss %s linked=%s reason=%s", loss.id, link_result.linked, link_result.reason)

    # Audit
    svc = _broadcast_svc(db)
    svc.record(
        audit_from_request(
            request,
            action_type=AuditActionType.ASSESSMENT_CREATE,
            resource_type="loss_event",
            resource_id=str(loss.id),
            after_state={
                "entity_name": loss.entity_name,
                "coverage": loss.coverage,
                "loss_type": loss.loss_type,
                "incurred_amount": float(loss.incurred_amount),
                "status": loss.status,
                "linked_assessment_id": str(loss.linked_assessment_id) if loss.linked_assessment_id else None,
            },
        )
    )

    db.commit()
    db.refresh(loss)
    return LossEventResponse.from_orm_row(loss)


@router.get(
    "/losses",
    response_model=LossListResponse,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def list_losses(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
    entity_name: Optional[str] = None,
    coverage: Optional[str] = None,
    status_filter: Optional[str] = Query(default=None, alias="status"),
    loss_type: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    cursor: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=500),
) -> LossListResponse:
    """Paginated loss list, tenant-scoped, with filter params."""
    import base64

    conditions = [LossEvent.tenant_id == UUID(ctx.tenant_id)]
    if entity_name:
        conditions.append(LossEvent.entity_name == entity_name)
    if coverage:
        conditions.append(LossEvent.coverage == coverage)
    if status_filter:
        conditions.append(LossEvent.status == status_filter.upper())
    if loss_type:
        conditions.append(LossEvent.loss_type == loss_type)
    if date_from:
        conditions.append(LossEvent.loss_date >= date_from)
    if date_to:
        conditions.append(LossEvent.loss_date <= date_to)

    if cursor:
        try:
            cursor_ts = datetime.fromisoformat(base64.urlsafe_b64decode(cursor.encode()).decode())
            conditions.append(LossEvent.created_at < cursor_ts)
        except Exception:
            pass  # ignore invalid cursor

    stmt = select(LossEvent).where(and_(*conditions)).order_by(LossEvent.created_at.desc()).limit(limit + 1)
    rows = db.execute(stmt).scalars().all()
    has_more = len(rows) > limit
    items = list(rows[:limit])

    next_cursor = None
    if has_more and items:
        next_cursor = base64.urlsafe_b64encode(items[-1].created_at.isoformat().encode()).decode()

    # Cheap count -- same filters without cursor/limit
    from sqlalchemy import func as sql_func

    count_conditions = [c for c in conditions if "created_at" not in str(c)]
    total = db.execute(
        select(sql_func.count()).select_from(LossEvent).where(and_(*count_conditions))
    ).scalar() or 0

    return LossListResponse(
        losses=[LossEventResponse.from_orm_row(r) for r in items],
        next_cursor=next_cursor,
        total=int(total),
    )


@router.get(
    "/losses/{loss_id}",
    response_model=LossEventResponse,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_READ))],
)
def get_loss(
    loss_id: UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LossEventResponse:
    loss = db.execute(
        select(LossEvent).where(
            LossEvent.id == loss_id, LossEvent.tenant_id == UUID(ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if loss is None:
        raise HTTPException(status_code=404, detail="Loss event not found")
    return LossEventResponse.from_orm_row(loss)


@router.put(
    "/losses/{loss_id}",
    response_model=LossEventResponse,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_WRITE))],
)
def update_loss(
    loss_id: UUID,
    body: LossEventUpdate,
    request: Request,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LossEventResponse:
    loss = db.execute(
        select(LossEvent).where(
            LossEvent.id == loss_id, LossEvent.tenant_id == UUID(ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if loss is None:
        raise HTTPException(status_code=404, detail="Loss event not found")

    before = {
        "incurred_amount": float(loss.incurred_amount),
        "paid_amount": float(loss.paid_amount),
        "reserved_amount": float(loss.reserved_amount),
        "status": loss.status,
        "closed_date": loss.closed_date.isoformat() if loss.closed_date else None,
    }

    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(loss, key, value)

    after = {
        "incurred_amount": float(loss.incurred_amount),
        "paid_amount": float(loss.paid_amount),
        "reserved_amount": float(loss.reserved_amount),
        "status": loss.status,
        "closed_date": loss.closed_date.isoformat() if loss.closed_date else None,
    }

    svc = _broadcast_svc(db)
    svc.record(
        audit_from_request(
            request,
            action_type=AuditActionType.ASSESSMENT_UPDATE,
            resource_type="loss_event",
            resource_id=str(loss.id),
            before_state=before,
            after_state=after,
        )
    )

    db.commit()
    db.refresh(loss)
    return LossEventResponse.from_orm_row(loss)


@router.post(
    "/losses/{loss_id}/relink",
    response_model=LinkResultResponse,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_WRITE))],
)
def relink_loss(
    loss_id: UUID,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> LinkResultResponse:
    """Force re-link a loss event. Used when the quote/assessment becomes
    available after initial ingestion."""
    loss = db.execute(
        select(LossEvent).where(
            LossEvent.id == loss_id, LossEvent.tenant_id == UUID(ctx.tenant_id)
        )
    ).scalar_one_or_none()
    if loss is None:
        raise HTTPException(status_code=404, detail="Loss event not found")

    # Clear existing link to force a fresh resolution
    loss.linked_assessment_id = None
    db.flush()
    result = SignalLossLinker(db).link(str(loss.id))
    db.commit()
    return LinkResultResponse(**result.__dict__)


@router.post(
    "/losses/link-all",
    response_model=RetrospectiveReportResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def link_all_losses(
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> RetrospectiveReportResponse:
    """Admin: batch-link every unlinked loss event in the tenant."""
    report = SignalLossLinker(db).link_all_unlinked(tenant_id=ctx.tenant_id)
    db.commit()
    return RetrospectiveReportResponse(**report.__dict__)


@router.post(
    "/losses/import",
    response_model=BulkImportResponse,
    dependencies=[Depends(require_permission(Permission.ASSESSMENT_WRITE))],
)
async def bulk_import(
    file: UploadFile = File(...),
    dry_run: bool = Query(default=False),
    request: Request = None,
    ctx: AuthContext = Depends(get_auth_context),
    db: Session = Depends(get_db),
) -> BulkImportResponse:
    """Bulk import loss events from CSV or JSON.

    CSV: header row required with column names matching LossEventCreate fields.
    JSON: array of objects matching LossEventCreate.

    Transactional: if `dry_run` is true the import runs but rolls back, only
    returning validation results. Otherwise all-or-nothing.
    """
    content = await file.read()
    filename = (file.filename or "").lower()

    # Parse rows
    try:
        rows = _parse_import(content, filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Parse error: {exc}")

    errors: list[dict] = []
    imported = 0
    skipped = 0
    created_ids: list[str] = []

    for idx, raw in enumerate(rows, start=1):
        try:
            body = LossEventCreate(**raw)
            loss = _apply_create(db, ctx.tenant_id, ctx.user_id, body)
            created_ids.append(str(loss.id))
            imported += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"row": idx, "error": str(exc), "raw": raw})
            skipped += 1

    # If any errors, abort the transaction (all-or-nothing)
    if errors or dry_run:
        db.rollback()
        return BulkImportResponse(
            total=len(rows),
            imported=0 if errors else imported,
            skipped=skipped + (imported if errors else 0),
            errors=errors,
            link_results={"skipped": True, "reason": "validation errors" if errors else "dry_run"},
        )

    # Run linker for all imported losses before commit
    linker = SignalLossLinker(db)
    link_summary = {"linked": 0, "unlinked": 0}
    for lid in created_ids:
        try:
            r = linker.link(lid)
            if r.linked:
                link_summary["linked"] += 1
            else:
                link_summary["unlinked"] += 1
        except Exception:
            link_summary["unlinked"] += 1

    # Audit summary event
    svc = _broadcast_svc(db)
    svc.record(
        audit_from_request(
            request,
            action_type=AuditActionType.ASSESSMENT_CREATE,
            resource_type="loss_event_bulk",
            resource_id=file.filename or "<stream>",
            after_state={"imported": imported, "link_summary": link_summary},
        )
    )

    db.commit()

    return BulkImportResponse(
        total=len(rows),
        imported=imported,
        skipped=skipped,
        errors=errors,
        link_results=link_summary,
    )


# =============================================================================
# Parsing helpers
# =============================================================================


_FLOAT_FIELDS = {"incurred_amount", "paid_amount", "reserved_amount"}
_DATE_FIELDS = {"loss_date", "notification_date", "closed_date"}


def _parse_import(content: bytes, filename: str) -> list[dict]:
    """Return a list of raw dicts suitable for LossEventCreate(**raw)."""
    text = content.decode("utf-8-sig")  # strip BOM if present

    if filename.endswith(".json") or text.lstrip().startswith("["):
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON import must be an array of objects")
        return [_coerce_types(r) for r in data]

    # Default: CSV
    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict] = []
    for raw in reader:
        rows.append(_coerce_types(raw))
    return rows


def _coerce_types(raw: dict) -> dict:
    """Coerce CSV string values to the right Python types for Pydantic."""
    out = {}
    for key, value in raw.items():
        if value is None or value == "":
            continue  # let defaults apply
        if key in _FLOAT_FIELDS:
            out[key] = float(value)
        elif key in _DATE_FIELDS:
            out[key] = datetime.fromisoformat(value) if isinstance(value, str) else value
        elif key == "event_metadata" and isinstance(value, str):
            out[key] = json.loads(value) if value else {}
        else:
            out[key] = value
    return out
