"""
DSI Model Version Endpoints (Phase 11) - Database Backed

Endpoints for retrieving model versions.
Strictly integrated with PostgreSQL via SQLAlchemy AsyncSession.
"""

import logging

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    ModelVersionRecord,
    Submission
)

from ..types import (
    ModelVersionDBRecord,
    ModelVersionDBRecord_BaseOnly, 
    ModelVersionDBRecord_DetailOnly, 
    ModelVersionDBRecord_CommentaryOnly, 
    ModelVersionDBRecord_ExposureOnly,
    ModelVersionDBRecord_LossOnly
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

@router.get("/modelversion/{submission_code}/submissionshistory/all", response_model=ModelVersionDBRecord)
async def get_submission_modelversion_all(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record

@router.get("/modelversion/{submission_code}/submissionshistory/base", response_model=ModelVersionDBRecord_BaseOnly)
async def get_submission_modelversion_base(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> ModelVersionDBRecord_BaseOnly:
    """Get model version details by code."""
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

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
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

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
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

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
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

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
    query = (select(ModelVersionRecord).join(Submission, ModelVersionRecord.submission_id_id == Submission.id).where(Submission.submission_code_code == submission_code))

    row = (await db.execute(query)).first()
    if not row:
        raise HTTPException(status_code=404, detail="Model version not found")

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Model version not found")

    return record
