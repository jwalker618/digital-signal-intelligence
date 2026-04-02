"""
DSI Model Version Endpoints (Phase 11) - Database Backed

Endpoints for retrieving model versions.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    ModelVersionRecord,
    Submission,
    SubmissionNote,
    ConfigSnapshot,
)

from ..types import (
    ModelVersionDBRecord,
    ModelVersionDBRecord_BaseOnly,
    ModelVersionDBRecord_DetailOnly,
    ModelVersionDBRecord_CommentaryOnly,
    ModelVersionDBRecord_ExposureOnly,
    ModelVersionDBRecord_LossOnly,
    ConfigSnapshotResponse,
    SubmissionNoteResponse,
)

logger = logging.getLogger("dsi.api.modelversions")
router = APIRouter()

# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/modelversion/{version_code}/all", response_model=ModelVersionDBRecord)
async def get_modelversion_all(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{version_code}/base", response_model=ModelVersionDBRecord_BaseOnly)
async def get_modelversion_base(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_BaseOnly:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{version_code}/detail", response_model=ModelVersionDBRecord_DetailOnly)
async def get_modelversion_detail(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_DetailOnly:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{version_code}/commentary", response_model=ModelVersionDBRecord_CommentaryOnly)
async def get_modelversion_commentary(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_CommentaryOnly:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{version_code}/loss", response_model=ModelVersionDBRecord_LossOnly)
async def get_modelversion_loss(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_LossOnly:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{version_code}/exposure", response_model=ModelVersionDBRecord_ExposureOnly)
async def get_modelversion_exposure(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_ExposureOnly:
    """Get model version details by code."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/all", response_model=list[ModelVersionDBRecord])
async def get_submission_modelversion_all(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> list[ModelVersionDBRecord]:
    """Get all model versions for a submission, ordered by version number descending."""
    query = (
        select(ModelVersionRecord)
        .join(Submission, ModelVersionRecord.submission_id == Submission.id)
        .where(Submission.submission_code == submission_code)
        .order_by(ModelVersionRecord.version_number.desc())
    )

    result = await db.execute(query)
    records = result.scalars().all()

    if not records:
        raise HTTPException(status_code=404, detail="No model versions found for submission")

    return records

@router.get("/modelversion/{submission_code}/submissionshistory/base", response_model=ModelVersionDBRecord_BaseOnly)
async def get_submission_modelversion_base(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_BaseOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id == Submission.id).where(Submission.submission_code == submission_code))

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/detail", response_model=ModelVersionDBRecord_DetailOnly)
async def get_submission_modelversion_detail(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_DetailOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id == Submission.id).where(Submission.submission_code == submission_code))

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/commentary", response_model=ModelVersionDBRecord_CommentaryOnly)
async def get_submission_modelversion_commentary(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_CommentaryOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id == Submission.id).where(Submission.submission_code == submission_code))

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/loss", response_model=ModelVersionDBRecord_LossOnly)
async def get_submission_modelversion_loss(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_LossOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id == Submission.id).where(Submission.submission_code == submission_code))

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/exposure", response_model=ModelVersionDBRecord_ExposureOnly)
async def get_submission_modelversion_exposure(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_ExposureOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id == Submission.id).where(Submission.submission_code == submission_code))

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record


# =============================================================================
# CONFIG SNAPSHOT
# =============================================================================

@router.get("/modelversion/{version_code}/config", response_model=ConfigSnapshotResponse)
async def get_modelversion_config(
    version_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ConfigSnapshotResponse:
    """Get the config snapshot for a model version, looked up via config_hash."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    if not record.config_hash:
        raise HTTPException(status_code=404, detail="No config snapshot linked to this model version")

    config_query = select(ConfigSnapshot).where(ConfigSnapshot.config_hash == record.config_hash)
    config_result = await db.execute(config_query)
    config = config_result.scalar_one_or_none()

    if not config:
        raise HTTPException(status_code=404, detail="Config snapshot not found")

    return config


# =============================================================================
# NOTES
# =============================================================================

class AddNoteRequest(BaseModel):
    note: str
    source: str = "underwriter"


@router.post("/modelversion/{version_code}/notes")
async def add_note(
    version_code: str,
    request: AddNoteRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """Add a note to the submission linked to this model version."""
    query = select(ModelVersionRecord).where(ModelVersionRecord.version_code == version_code)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    # Create a SubmissionNote on the parent submission
    submission_note = SubmissionNote(
        submission_id=record.submission_id,
        note=request.note,
        source=request.source,
    )
    db.add(submission_note)
    await db.commit()

    # Return all notes for this submission
    notes_query = (
        select(SubmissionNote)
        .where(SubmissionNote.submission_id == record.submission_id)
        .order_by(SubmissionNote.created_at)
    )
    notes_result = await db.execute(notes_query)
    notes = [
        {"note": n.note, "source": n.source, "created_at": str(n.created_at)}
        for n in notes_result.scalars().all()
    ]

    return {"status": "ok", "notes": notes}