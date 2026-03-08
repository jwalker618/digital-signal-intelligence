"""
DSI Workbench Endpoints (CQRS Read Models)

Highly optimized, read-only SQL queries designed specifically to 
flatten relational data and serve it directly to frontend data tables.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db
from infrastructure.db.models import Submission, ModelVersionRecord, AuditLog

logger = logging.getLogger("dsi.api.workbench")
router = APIRouter()


# Reuse the same DB-availability helpers as submissions.py, but localised here
def _db_available() -> bool:
    try:
        from ..main import app_state

        return app_state.db_connected
    except Exception:
        return False


async def _get_db_session() -> Optional[AsyncSession]:
    if not _db_available():
        return None
    try:
        from ...db.config import _get_async_session_factory

        factory = _get_async_session_factory()
        return factory()
    except Exception:
        return None


@router.get("/workbench-data")
async def get_workbench_data(
    created_after: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """
    Returns a unified flat-file projection of the entire pricing pipeline.
    Explicitly provides both internal UUIDs and public String Codes for UX routing.
    """
    if _db_available():
        try:
            session = await _get_db_session()
            if session:
                try:
                    """Primary Read Model for the Pipeline UI grids."""
                    if created_after is None:
                        created_after = datetime.utcnow() - timedelta(days=30)

                    query = text("""
                        SELECT
                            s.id AS submission_id,
                            q.id AS quote_id,
                            r.referral_id AS referral_id,
                            mv.id AS model_version_id,
                            s.submission_id AS submission_code,
                            q.quote_id AS quote_code,
                            r.referral_id AS referral_code,
                            mv.version_id AS version_code,
                            s.entity_name,
                            COALESCE(s.coverage, '') || ' / ' || COALESCE(s.configuration, '') AS coverage_configuration,
                            s.created_at,
                            q.status,
                            q.recommended_premium,
                            q.recommended_limit,
                            mv.pure_composite_score,
                            mv.confidence AS pure_composite_score_confidence,
                            mv.signal_coverage,
                            mv.final_tier,
                            mv.tier_label,
                            mv.decision
                        FROM submissions s
                        LEFT JOIN quotes q ON s.id = q.submission_id
                        LEFT JOIN referrals r on r.quote_id = q.id
                        LEFT JOIN model_versions mv ON mv.submission_id = s.id AND mv.id = q.model_version_id
                        WHERE mv.is_latest = true
                            AND (
                                    CAST(s.status AS TEXT) ILIKE 'draft'
                                    OR s.created_at >= :created_after
                                )
                    """)

                    result = await session.execute(query, {"created_after": created_after})
                    rows = result.mappings().all()
                                        
                    return [dict(row) for row in rows]
                finally:
                    await session.close()
        except Exception as e:
            logger.warning("DB get workbench data failed: %s", e)
    return []

@router.get("/submissions/{submission_id}/model_versions")
async def get_model_versions(submission_id: str) -> Dict[str, Any]:
    """Fetch the lineage of model versions for a submission."""
    if _db_available():
        try:
            session = await _get_db_session()
            if session:
                try:
                    sub_q = select(Submission).where(
                        Submission.submission_id == submission_id
                    )
                    sub = (await session.execute(sub_q)).scalar_one_or_none()

                    if not sub:
                        raise HTTPException(status_code=404, detail="Submission not found")

                    mv_q = (
                        select(ModelVersionRecord)
                        .where(ModelVersionRecord.submission_id == sub.id)
                        .order_by(ModelVersionRecord.version_number.desc())
                    )

                    versions = (await session.execute(mv_q)).scalars().all()

                    return {
                        "versions": [
                            {
                                "version_id": v.version_id,
                                "version_number": v.version_number,
                                "version_type": v.version_type,
                                "is_latest": v.is_latest,
                                "composite_score": v.pure_composite_score,
                                "tier": v.final_tier,
                                "tier_label": v.tier_label,
                                "created_by": v.created_by,
                                "created_at": v.created_at.isoformat()
                                if v.created_at
                                else None,
                            }
                            for v in versions
                        ]
                    }
                finally:
                    await session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("DB get model_versions failed: %s", e)

    return {"versions": []}


@router.get("/submissions/{submission_id}/audit_logs")
async def get_audit_logs(submission_id: str) -> Dict[str, Any]:
    """Fetch the chronological ledger of events for this submission."""
    if _db_available():
        try:
            session = await _get_db_session()
            if session:
                try:
                    log_q = (
                        select(AuditLog)
                        .where(AuditLog.resource_id == submission_id)
                        .order_by(AuditLog.created_at.desc())
                    )

                    logs = (await session.execute(log_q)).scalars().all()

                    return {
                        "logs": [
                            {
                                "id": str(log.id),
                                "event_type": log.event_type,
                                "event_action": log.event_action,
                                "details": log.details,
                                "ip_address": log.ip_address,
                                "created_at": log.created_at.isoformat()
                                if log.created_at
                                else None,
                            }
                            for log in logs
                        ]
                    }
                finally:
                    await session.close()
        except Exception as e:
            logger.warning("DB get audit_logs failed: %s", e)

    return {"logs": []}