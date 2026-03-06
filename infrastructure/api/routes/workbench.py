"""
DSI Workbench Endpoints (CQRS Read Models)

Highly optimized, read-only SQL queries designed specifically to 
flatten relational data and serve it directly to frontend data tables.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.db.config import get_async_db

logger = logging.getLogger("dsi.api.workbench")
router = APIRouter()

@router.get("/workbench-data")
async def get_workbench_data(
    created_after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_async_db)
):
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

    result = await db.execute(query, {"created_after": created_after})
    rows = result.mappings().all()
    return [dict(row) for row in rows]


@router.get("/referral-queue")
async def get_referral_queue(db: AsyncSession = Depends(get_async_db)):
    """Read Model for pending referral lists."""
    query = text("""
        SELECT 
            r.referral_id, r.status as ref_status, r.priority, r.reasons, r.created_at,
            q.recommended_premium, q.tier, q.decision,
            s.entity_name, s.coverage
        FROM referrals r
        JOIN quotes q ON r.quote_id = q.id
        JOIN submissions s ON q.submission_id = s.id
        WHERE r.status IN ('pending', 'in_review')
        ORDER BY r.priority ASC, r.created_at DESC
    """)
    
    result = await db.execute(query)
    data = []
    for row in result.mappings().all():
        row_dict = dict(row)
        if row_dict.get("created_at"):
            row_dict["created_at"] = row_dict["created_at"].isoformat()
            
        data.append({
            "id": str(row_dict["referral_id"]),
            "status": row_dict["ref_status"],
            "priority": row_dict["priority"],
            "reasons": row_dict["reasons"],
            "created_at": row_dict["created_at"],
            "entity_name": row_dict["entity_name"],
            "coverage": row_dict["coverage"],
            "premium": row_dict["recommended_premium"],
            "tier": row_dict["tier"],
            "decision": row_dict["decision"]
        })
    return data


@router.get("/audit-trail")
async def get_audit_trail(db: AsyncSession = Depends(get_async_db)):
    """Read Model for the global audit log UI."""
    events = []
    
    # 1. Fetch Underwriter Signal Overrides
    override_query = text("""
        SELECT 
            sar.id, sar.created_at, sar.entity_id, sar.signal_id, 
            sar.override_rationale, u.email as user_email
        FROM signal_audit_records sar
        LEFT JOIN users u ON sar.overridden_by = u.id
    """)
    
    result_overrides = await db.execute(override_query)
    for row in result_overrides.mappings().all():
        events.append({
            "id": str(row["id"]),
            "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
            "type": "Manual Override",
            "entity": row["entity_id"],
            "action": f"Modified Signal: {row['signal_id']}",
            "details": row["override_rationale"] or "No rationale provided.",
            "actor": row["user_email"] or "Underwriter"
        })
        
    # 2. Fetch Automated System Logs
    log_query = text("""
        SELECT 
            al.id, al.created_at, al.event_type, al.event_action, 
            al.resource_id, al.details, u.email as user_email
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
    """)
    
    result_logs = await db.execute(log_query)
    for row in result_logs.mappings().all():
        details_str = str(row["details"])
        if len(details_str) > 100:
            details_str = details_str[:97] + "..."
            
        events.append({
            "id": str(row["id"]),
            "timestamp": row["created_at"].isoformat() if row["created_at"] else None,
            "type": "System Event",
            "entity": row["resource_id"] or "System",
            "action": f"{row['event_type']} ({row['event_action']})",
            "details": details_str,
            "actor": row["user_email"] or "Automated Engine"
        })
        
    events.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return events