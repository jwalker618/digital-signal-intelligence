"""
DSI Submission Endpoints

Endpoints for creating and managing submissions.
Supports both database-backed persistence and in-memory fallback.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    Submission,
    SubmissionStatus
)

from ..utils import generate_id

from ..types import (
    SubmissionRequest,
    SubmissionResponse,
    SubmissionRecord,
    MultiCoverageRequest,
    MultiCoverageResponse,
    QuoteResponse,
    QuoteStatus,
    JobResponse,
    JobStatus,
)
from layers.risk.workflow import run_assessment
from layers.risk.types import WorkflowResult, DecisionType as WorkflowDecisionType

logger = logging.getLogger("dsi.api.submissions")

router = APIRouter()

# =============================================================================
# STORAGE BACKEND
# =============================================================================

class InMemoryStore:
    """In-memory storage fallback when database is unavailable."""

    def __init__(self) -> None:
        self.submissions: Dict[str, Dict[str, Any]] = {}
        self.quotes: Dict[str, Dict[str, Any]] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}

_memory = InMemoryStore()

def _db_available() -> bool:
    """Check if database is available via app state."""
    try:
        from ..main import app_state

        return app_state.db_connected
    except Exception:
        return False

async def _get_db_session() -> Optional[AsyncSession]:
    """Get a database session if DB is available, else None."""
    if not _db_available():
        return None
    try:
        from ...db.config import _get_async_session_factory

        factory = _get_async_session_factory()
        return factory()
    except Exception:
        return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def workflow_result_to_quote(
    result: WorkflowResult,
    submission_code: str,
    quote_code: str,
) -> Dict[str, Any]:
    """Convert WorkflowResult to quote dict."""
    now = datetime.utcnow()

    decision_map = {
        WorkflowDecisionType.APPROVE: "approve",
        WorkflowDecisionType.REFER: "refer",
        WorkflowDecisionType.DECLINE: "decline",
    }

    # V7 composite-grade rollup, surfaced in the quote dict so the
    # frontend has it without a follow-up GET. Empty dicts when the
    # workflow hasn't been re-run since V7 landed.
    from layers.risk.v7_persistence import quote_dict_evidence_fields
    v7_evidence = quote_dict_evidence_fields(result)

    return {
        "quote_code": quote_code,
        "submission_code": submission_code,
        "status": QuoteStatus.READY,
        "composite_score": result.composite_score,
        "confidence": result.confidence,
        "tier": result.tier,
        "tier_label": result.tier_label,
        "decision": decision_map.get(result.decision, "refer"),
        "auto_approve": result.auto_approve,
        "referral_reasons": result.referral_reasons,
        "recommended_premium": result.recommended_premium,
        "recommended_limit": result.recommended_limit,
        "discovery": (
            {
                "domain": result.discovered_domain,
                "confidence": result.discovery_confidence,
                "warnings": result.discovery_warnings,
            }
            if result.discovered_domain
            else None
        ),
        "notes": result.notes,
        "created_at": now,
        "valid_until": now + timedelta(days=30),
        # V7 composite evidence-grade rollup.
        "evidence": v7_evidence,
    }


def execute_workflow(
    submission_code: str,
    request: SubmissionRequest,
) -> WorkflowResult:
    """Execute the pricing workflow."""
    logger.info(f"Executing workflow for submission {submission_code}")
    start_time = time.time()

    try:
        result = run_assessment(
            entity_id=submission_code,
            coverage=request.coverage,
            submission_data=request.submission_data or {},
            direct_query_responses=request.direct_query_responses or {},
            entity_name=request.entity_name,
            domain_hint=request.domain_hint,
            country_hint=request.country_hint,
            skip_discovery=True,
        )

        duration = time.time() - start_time
        logger.info(
            "Workflow complete for %s: score=%.0f, tier=%s, decision=%s, duration=%.2fs",
            submission_code,
            result.composite_score,
            result.tier,
            result.decision.value,
            duration,
        )

        return result

    except Exception as e:
        logger.error(f"Workflow failed for {submission_code}: {e}")
        raise


async def _persist_submission(submission_code: str, request: SubmissionRequest) -> None:
    """Persist a submission to database if available, otherwise in-memory."""
    now = datetime.utcnow()
    data = {
        "submission_code": submission_code,
        "entity_name": request.entity_name,
        "domain_hint": request.domain_hint,
        "country_hint": request.country_hint,
        "coverage": request.coverage,
        "configuration": request.configuration or f"{request.coverage}_general",
        "status": SubmissionStatus.PENDING,
        "created_at": now,
        "updated_at": now,
        "quote_code": None,
        "submission_data": request.submission_data,
        "direct_query_responses": request.direct_query_responses,
    }

    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
                try:
                    repo = SubmissionRepository(session)
                    await repo.create(
                        entity_name=request.entity_name,
                        coverage=request.coverage,
                        domain_hint=request.domain_hint,
                        country_hint=request.country_hint,
                        configuration=request.configuration,
                        submission_data=request.submission_data or {},
                        direct_query_responses=request.direct_query_responses or {},
                    )
                    await session.commit()
                    logger.debug("Submission %s persisted to database", submission_code)
                    return
                finally:
                    await session.close()
        except Exception as e:
            logger.warning("DB persist failed, using in-memory: %s", e)

    _memory.submissions[submission_code] = data

async def _update_submission_status(
    submission_code: str,
    status: SubmissionStatus,
    quote_code: Optional[str] = None,
    error: Optional[str] = None,
    discovered_domain: Optional[str] = None,
) -> None:
    """Update submission status in the active storage backend."""
    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
                try:
                    repo = SubmissionRepository(session)
                    await repo.update_status(submission_code, status, error_message=error)
                    await session.commit()
                    return
                finally:
                    await session.close()
        except Exception as e:
            logger.warning("DB status update failed: %s", e)

    if submission_code in _memory.submissions:
        sub = _memory.submissions[submission_code]
        sub["status"] = status
        if quote_code:
            sub["quote_code"] = quote_code
        if error:
            sub["error"] = error
        if discovered_domain:
            sub["discovered_domain"] = discovered_domain


async def _persist_quote(quote_code: str, quote_data: Dict[str, Any]) -> None:
    """Persist a quote to the active storage backend."""
    if _db_available():
        try:
            from ...db.repositories import (
                QuoteRepository,
                SubmissionRepository,
                ModelVersionRepository,
            )
            session = await _get_db_session()
            if session:
                try:
                    sub_repo = SubmissionRepository(session)
                    sub = await sub_repo.get_by_code(quote_data["submission_code"])
                    if sub:
                        mv_repo = ModelVersionRepository(session)
                        mv = await mv_repo.get_latest(sub.id)
                        if mv:
                            repo = QuoteRepository(session)
                            await repo.create(
                                submission_id=sub.id,
                                model_version_id=mv.id,
                                recommended_premium=quote_data.get("recommended_premium", 0),
                                recommended_limit=quote_data.get("recommended_limit"),
                            )
                            await session.commit()
                    return
                finally:
                    await session.close()
        except Exception as e:
            logger.warning("DB quote persist failed, using in-memory: %s", e)

    _memory.quotes[quote_code] = quote_data


async def process_submission_async(
    submission_code: str,
    request: SubmissionRequest,
) -> None:
    """Background task to process a submission."""
    logger.info("Processing submission %s in background", submission_code)

    await _update_submission_status(submission_code, SubmissionStatus.PROCESSING)

    try:
        result = execute_workflow(submission_code, request)

        quote_code = generate_id("quo")
        quote = workflow_result_to_quote(result, submission_code, quote_code)
        await _persist_quote(quote_code, quote)
        await _update_submission_status(
            submission_code,
            SubmissionStatus.READY,
            quote_code=quote_code,
            discovered_domain=result.discovered_domain,
        )

        for job in _memory.jobs.values():
            if job.get("submission_code") == submission_code:
                job["status"] = JobStatus.COMPLETED
                job["result"] = {"quote_code": quote_code}
                job["completed_at"] = datetime.utcnow()

    except Exception as e:
        logger.error("Failed to process submission %s: %s", submission_code, e)
        await _update_submission_status(
            submission_code, SubmissionStatus.FAILED, error=str(e)
        )

        for job in _memory.jobs.values():
            if job.get("submission_code") == submission_code:
                job["status"] = JobStatus.FAILED
                job["error"] = str(e)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/submissions", response_model=SubmissionResponse)
async def create_submission(
    request: SubmissionRequest,
    background_tasks: BackgroundTasks,
) -> SubmissionResponse:
    """Create a new submission and trigger pricing."""
    submission_code = generate_id("sub")
    now = datetime.utcnow()
    estimated_completion = now + timedelta(seconds=30)

    await _persist_submission(submission_code, request)

    if request.async_mode:
        job_id = generate_id("job")
        _memory.jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "submission_code": submission_code,
            "created_at": now,
        }
        background_tasks.add_task(process_submission_async, submission_code, request)

        return SubmissionResponse(
            submission_code=submission_code,
            status=SubmissionStatus.PROCESSING,
            estimated_completion=estimated_completion,
            job_id=job_id,
        )

    try:
        await _update_submission_status(submission_code, SubmissionStatus.PROCESSING)
        result = execute_workflow(submission_code, request)
        quote_code = generate_id("quo")
        quote = workflow_result_to_quote(result, submission_code, quote_code)

        await _persist_quote(quote_code, quote)
        await _update_submission_status(
            submission_code,
            SubmissionStatus.READY,
            quote_code=quote_code,
            discovered_domain=result.discovered_domain,
        )

        return SubmissionResponse(
            submission_code=submission_code,
            status=SubmissionStatus.READY,
        )

    except Exception as e:
        await _update_submission_status(
            submission_code, SubmissionStatus.FAILED, error=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/submissions/{submission_code}", response_model=SubmissionRecord)
async def get_submission(
    submission_code: str,
    db: AsyncSession = Depends(get_async_db),
) -> SubmissionRecord:
    """Get submission details by code."""
    query = (
        select(Submission)
        .where(Submission.submission_code == submission_code)
        .options(selectinload(Submission.notes))
    )

    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Submission not found")

    return record

@router.delete("/submissions/{submission_code}")
async def cancel_submission(submission_code: str) -> Dict[str, Any]:
    """Cancel a pending submission."""
    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository

            session = await _get_db_session()
            if session:
                try:
                    repo = SubmissionRepository(session)
                    s = await repo.get_by_code(submission_code)
                    if s:
                        if s.status.value not in ["pending", "processing"]:
                            raise HTTPException(
                                status_code=400,
                                detail="Cannot cancel submission in current status",
                            )
                        await repo.delete(submission_code)
                        await session.commit()
                        return {
                            "message": "Submission cancelled",
                            "submission_code": submission_code,
                        }
                finally:
                    await session.close()
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("DB cancel failed, using in-memory: %s", e)

    if submission_code not in _memory.submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    s = _memory.submissions[submission_code]

    if s["status"] not in [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel submission in current status",
        )

    del _memory.submissions[submission_code]

    return {"message": "Submission cancelled", "submission_code": submission_code}

# =============================================================================
# MULTI-COVERAGE ENDPOINTS
# =============================================================================

@router.post("/submissions/multi", response_model=MultiCoverageResponse)
async def create_multi_coverage_submission(
    request: MultiCoverageRequest,
    background_tasks: BackgroundTasks,
) -> MultiCoverageResponse:
    """Create a multi-coverage submission."""
    result_id = generate_id("mcs")
    now = datetime.utcnow()
    start_time = time.time()

    coverages = request.coverages or ["cyber"]

    coverage_quotes: Dict[str, QuoteResponse] = {}
    failed_coverages: List[str] = []

    for coverage in coverages:
        try:
            submission_code = generate_id("sub")
            quote_code = generate_id("quo")

            sub_data = {
                "submission_code": submission_code,
                "entity_name": request.entity_name,
                "domain_hint": request.domain_hint,
                "coverage": coverage,
                "configuration": f"{coverage}_general",
                "status": SubmissionStatus.PROCESSING,
                "created_at": now,
                "updated_at": now,
                "quote_code": quote_code,
            }
            _memory.submissions[submission_code] = sub_data

            result = run_assessment(
                entity_id=submission_code,
                coverage=coverage,
                submission_data=request.submission_data or {},
                direct_query_responses=request.direct_query_responses or {},
                entity_name=request.entity_name,
                domain_hint=request.domain_hint,
                country_hint=request.country_hint,
                skip_discovery=True,
            )

            decision_map = {
                WorkflowDecisionType.APPROVE: "approve",
                WorkflowDecisionType.REFER: "refer",
                WorkflowDecisionType.DECLINE: "decline",
            }

            coverage_quotes[coverage] = QuoteResponse(
                quote_code=quote_code,
                submission_code=submission_code,
                version_code=None,
                status=QuoteStatus.READY,
                composite_score=int(result.composite_score),
                tier=result.tier,
                tier_label=result.tier_label,
                decision=decision_map.get(result.decision, "refer"),
                recommended_premium=result.recommended_premium,
                recommended_limit=result.recommended_limit,
                base_premium=None,
                premium_after_modifiers=None,
                modifiers_applied=[],
                loss_propensity=None,
                exposure=None,
                discovery=None,
                signal_summary=None,
                referral_reasons=[],
                referral_code=None,
                created_at=now,
                valid_until=now + timedelta(days=30),
            )

            _memory.submissions[submission_code]["status"] = SubmissionStatus.READY
            _memory.submissions[submission_code]["quote_code"] = quote_code

        except Exception as e:
            logger.error("Failed to price %s: %s", coverage, e)
            failed_coverages.append(coverage)

    successful = list(coverage_quotes.keys())
    discount = 0.0

    if len(successful) >= 2:
        discount = 0.05
        if len(successful) >= 3:
            discount = 0.10

    total = sum(
        q.recommended_premium or 0 for q in coverage_quotes.values()
    )
    savings = total * discount
    combined = total - savings

    duration = time.time() - start_time

    return MultiCoverageResponse(
        result_id=result_id,
        entity_name=request.entity_name,
        detected_locale=request.country_hint or "US",
        coverage_quotes=coverage_quotes,
        failed_coverages=failed_coverages,
        recommended_package=successful,
        package_discount=discount,
        combined_premium=combined,
        total_savings=savings,
        duration_seconds=duration,
        cache_hit_rate=0.0,
    )


# =============================================================================
# JOB ENDPOINTS
# =============================================================================

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str) -> JobResponse:
    """Get async job status."""
    if job_id not in _memory.jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _memory.jobs[job_id]

    submission_code = job.get("submission_code")
    if submission_code and submission_code in _memory.submissions:
        sub = _memory.submissions[submission_code]
        if sub["status"] == SubmissionStatus.READY:
            job["status"] = JobStatus.COMPLETED
            job["result"] = {"quote_code": sub.get("quote_code")}
        elif sub["status"] == SubmissionStatus.FAILED:
            job["status"] = JobStatus.FAILED
            job["error"] = sub.get("error", "Processing failed")

    return JobResponse(
        job_id=job["job_id"],
        status=job["status"],
        progress=1.0 if job["status"] == JobStatus.COMPLETED else 0.5,
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        completed_at=job.get("completed_at"),
    )
