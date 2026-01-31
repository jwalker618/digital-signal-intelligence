"""
DSI Submission Endpoints

Endpoints for creating and managing submissions.
Supports both database-backed persistence and in-memory fallback.
"""

import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..types import (
    SubmissionRequest,
    SubmissionResponse,
    SubmissionDetail,
    SubmissionStatus,
    MultiCoverageRequest,
    MultiCoverageResponse,
    QuoteResponse,
    QuoteStatus,
    JobResponse,
    JobStatus,
    ListFilters,
)

# Import workflow engine
from ...model.workflow import run_assessment
from ...model.types import WorkflowResult, DecisionType

logger = logging.getLogger("dsi.api.submissions")

router = APIRouter()


# =============================================================================
# STORAGE BACKEND
# =============================================================================

class InMemoryStore:
    """In-memory storage fallback when database is unavailable."""

    def __init__(self):
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

def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def workflow_result_to_quote(
    result: WorkflowResult,
    submission_id: str,
    quote_id: str,
) -> Dict[str, Any]:
    """Convert WorkflowResult to quote dict."""
    now = datetime.utcnow()

    decision_map = {
        DecisionType.APPROVE: "approve",
        DecisionType.REFER: "refer",
        DecisionType.DECLINE: "decline",
    }

    return {
        "quote_id": quote_id,
        "submission_id": submission_id,
        "status": QuoteStatus.READY,
        "composite_score": result.composite_score,
        "confidence": result.confidence,
        "tier": result.tier,
        "tier_label": result.tier_label,
        "decision": decision_map.get(result.decision, "refer"),
        "auto_approve": result.auto_approve,
        "referral_reasons": result.referral_reasons,
        "premium_options": result.premium_options,
        "recommended_premium": result.recommended_premium,
        "recommended_limit": result.recommended_limit,
        "discovery": {
            "domain": result.discovered_domain,
            "confidence": result.discovery_confidence,
            "warnings": result.discovery_warnings,
        } if result.discovered_domain else None,
        "notes": result.notes,
        "created_at": now,
        "valid_until": now + timedelta(days=30),
    }


def execute_workflow(
    submission_id: str,
    request: SubmissionRequest,
) -> WorkflowResult:
    """Execute the pricing workflow."""
    logger.info(f"Executing workflow for submission {submission_id}")
    start_time = time.time()

    try:
        result = run_assessment(
            entity_id=submission_id,
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
            f"Workflow complete for {submission_id}: "
            f"score={result.composite_score:.0f}, tier={result.tier}, "
            f"decision={result.decision.value}, duration={duration:.2f}s"
        )

        return result

    except Exception as e:
        logger.error(f"Workflow failed for {submission_id}: {e}")
        raise


async def _persist_submission(submission_id: str, request: SubmissionRequest) -> None:
    """Persist a submission to database if available, otherwise in-memory."""
    now = datetime.utcnow()
    data = {
        "submission_id": submission_id,
        "entity_name": request.entity_name,
        "domain_hint": request.domain_hint,
        "country_hint": request.country_hint,
        "coverage": request.coverage,
        "configuration": request.configuration or f"{request.coverage}_general",
        "status": SubmissionStatus.PENDING,
        "created_at": now,
        "updated_at": now,
        "quote_id": None,
        "submission_data": request.submission_data,
        "direct_query_responses": request.direct_query_responses,
    }

    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
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
                await session.close()
                logger.debug(f"Submission {submission_id} persisted to database")
                return
        except Exception as e:
            logger.warning(f"DB persist failed, using in-memory: {e}")

    _memory.submissions[submission_id] = data


async def _update_submission_status(
    submission_id: str,
    status: SubmissionStatus,
    quote_id: Optional[str] = None,
    error: Optional[str] = None,
    discovered_domain: Optional[str] = None,
) -> None:
    """Update submission status in the active storage backend."""
    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
                repo = SubmissionRepository(session)
                await repo.update_status(submission_id, status, error_message=error)
                await session.commit()
                await session.close()
                return
        except Exception as e:
            logger.warning(f"DB status update failed: {e}")

    if submission_id in _memory.submissions:
        _memory.submissions[submission_id]["status"] = status
        if quote_id:
            _memory.submissions[submission_id]["quote_id"] = quote_id
        if error:
            _memory.submissions[submission_id]["error"] = error
        if discovered_domain:
            _memory.submissions[submission_id]["discovered_domain"] = discovered_domain


async def _persist_quote(quote_id: str, quote_data: Dict[str, Any]) -> None:
    """Persist a quote to the active storage backend."""
    if _db_available():
        try:
            from ...db.repositories import QuoteRepository, SubmissionRepository
            from ...db.models import DecisionType as DBDecisionType
            session = await _get_db_session()
            if session:
                sub_repo = SubmissionRepository(session)
                sub = await sub_repo.get_by_id(quote_data["submission_id"])
                if sub:
                    decision_map = {
                        "approve": DBDecisionType.APPROVE,
                        "refer": DBDecisionType.REFER,
                        "decline": DBDecisionType.DECLINE,
                    }
                    repo = QuoteRepository(session)
                    await repo.create(
                        submission_id=sub.id,
                        composite_score=quote_data.get("composite_score", 0),
                        tier=quote_data.get("tier", 3),
                        tier_label=quote_data.get("tier_label", ""),
                        decision=decision_map.get(
                            quote_data.get("decision", "refer"),
                            DBDecisionType.REFER,
                        ),
                        recommended_premium=quote_data.get("recommended_premium", 0),
                        premium_options=quote_data.get("premium_options", {}),
                        confidence=quote_data.get("confidence", 1.0),
                        referral_reasons=quote_data.get("referral_reasons", []),
                    )
                    await session.commit()
                    await session.close()
                    return
        except Exception as e:
            logger.warning(f"DB quote persist failed: {e}")

    _memory.quotes[quote_id] = quote_data


async def process_submission_async(
    submission_id: str,
    request: SubmissionRequest,
):
    """Background task to process a submission."""
    logger.info(f"Processing submission {submission_id} in background")

    await _update_submission_status(submission_id, SubmissionStatus.PROCESSING)

    try:
        result = execute_workflow(submission_id, request)

        quote_id = generate_id("quo")
        quote = workflow_result_to_quote(result, submission_id, quote_id)
        await _persist_quote(quote_id, quote)
        await _update_submission_status(
            submission_id,
            SubmissionStatus.READY,
            quote_id=quote_id,
            discovered_domain=result.discovered_domain,
        )

        # Update job if exists
        for job_id, job in _memory.jobs.items():
            if job.get("submission_id") == submission_id:
                job["status"] = JobStatus.COMPLETED
                job["result"] = {"quote_id": quote_id}
                job["completed_at"] = datetime.utcnow()

    except Exception as e:
        logger.error(f"Failed to process submission {submission_id}: {e}")
        await _update_submission_status(
            submission_id, SubmissionStatus.FAILED, error=str(e)
        )

        for job_id, job in _memory.jobs.items():
            if job.get("submission_id") == submission_id:
                job["status"] = JobStatus.FAILED
                job["error"] = str(e)


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/submissions", response_model=SubmissionResponse)
async def create_submission(
    request: SubmissionRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a new submission and trigger pricing.

    The submission will be processed asynchronously if async_mode is True,
    otherwise it will block until complete.
    """
    submission_id = generate_id("sub")
    now = datetime.utcnow()
    estimated_completion = now + timedelta(seconds=30)

    await _persist_submission(submission_id, request)

    if request.async_mode:
        job_id = generate_id("job")
        _memory.jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "submission_id": submission_id,
            "created_at": now,
        }

        background_tasks.add_task(process_submission_async, submission_id, request)

        return SubmissionResponse(
            submission_id=submission_id,
            status=SubmissionStatus.PROCESSING,
            estimated_completion=estimated_completion,
            job_id=job_id,
        )
    else:
        try:
            await _update_submission_status(submission_id, SubmissionStatus.PROCESSING)

            result = execute_workflow(submission_id, request)

            quote_id = generate_id("quo")
            quote = workflow_result_to_quote(result, submission_id, quote_id)
            await _persist_quote(quote_id, quote)
            await _update_submission_status(
                submission_id,
                SubmissionStatus.READY,
                quote_id=quote_id,
                discovered_domain=result.discovered_domain,
            )

            return SubmissionResponse(
                submission_id=submission_id,
                status=SubmissionStatus.READY,
                quote_id=quote_id,
            )

        except Exception as e:
            await _update_submission_status(
                submission_id, SubmissionStatus.FAILED, error=str(e)
            )
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/submissions", response_model=List[SubmissionDetail])
async def list_submissions(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """List submissions with optional filtering."""

    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            from ...db.models import SubmissionStatus as DBSubmissionStatus
            session = await _get_db_session()
            if session:
                repo = SubmissionRepository(session)
                db_status = None
                if status:
                    db_status = DBSubmissionStatus(status)
                subs = await repo.list(
                    coverage=coverage, status=db_status,
                    limit=limit, offset=offset,
                )
                await session.close()
                return [
                    SubmissionDetail(
                        submission_id=s.submission_id,
                        entity_name=s.entity_name,
                        domain=s.domain_hint,
                        coverage=s.coverage,
                        configuration=s.configuration,
                        status=SubmissionStatus(s.status.value),
                        created_at=s.created_at,
                        updated_at=s.updated_at or s.created_at,
                        quote_id=None,
                    )
                    for s in subs
                ]
        except Exception as e:
            logger.warning(f"DB list failed, using in-memory: {e}")

    results = list(_memory.submissions.values())

    if coverage:
        results = [s for s in results if s["coverage"] == coverage]
    if status:
        results = [s for s in results if s["status"].value == status]

    results.sort(key=lambda s: s["created_at"], reverse=True)
    results = results[offset:offset + limit]

    return [
        SubmissionDetail(
            submission_id=s["submission_id"],
            entity_name=s["entity_name"],
            domain=s.get("domain_hint"),
            coverage=s["coverage"],
            configuration=s["configuration"],
            status=s["status"],
            created_at=s["created_at"],
            updated_at=s["updated_at"],
            quote_id=s.get("quote_id"),
        )
        for s in results
    ]


@router.get("/submissions/{submission_id}", response_model=SubmissionDetail)
async def get_submission(submission_id: str):
    """Get submission details by ID."""

    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
                repo = SubmissionRepository(session)
                s = await repo.get_by_id(submission_id)
                await session.close()
                if s:
                    return SubmissionDetail(
                        submission_id=s.submission_id,
                        entity_name=s.entity_name,
                        domain=s.domain_hint,
                        coverage=s.coverage,
                        configuration=s.configuration,
                        status=SubmissionStatus(s.status.value),
                        created_at=s.created_at,
                        updated_at=s.updated_at or s.created_at,
                        quote_id=None,
                        error=s.error_message,
                    )
        except Exception as e:
            logger.warning(f"DB get failed, using in-memory: {e}")

    if submission_id not in _memory.submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    s = _memory.submissions[submission_id]

    return SubmissionDetail(
        submission_id=s["submission_id"],
        entity_name=s["entity_name"],
        domain=s.get("domain_hint"),
        coverage=s["coverage"],
        configuration=s["configuration"],
        status=s["status"],
        created_at=s["created_at"],
        updated_at=s["updated_at"],
        quote_id=s.get("quote_id"),
        error=s.get("error"),
    )


@router.delete("/submissions/{submission_id}")
async def cancel_submission(submission_id: str):
    """Cancel a pending submission."""

    if _db_available():
        try:
            from ...db.repositories import SubmissionRepository
            session = await _get_db_session()
            if session:
                repo = SubmissionRepository(session)
                s = await repo.get_by_id(submission_id)
                if s:
                    if s.status.value not in ["pending", "processing"]:
                        raise HTTPException(
                            status_code=400,
                            detail="Cannot cancel submission in current status",
                        )
                    await repo.delete(submission_id)
                    await session.commit()
                    await session.close()
                    return {
                        "message": "Submission cancelled",
                        "submission_id": submission_id,
                    }
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"DB cancel failed, using in-memory: {e}")

    if submission_id not in _memory.submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    s = _memory.submissions[submission_id]

    if s["status"] not in [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel submission in current status",
        )

    del _memory.submissions[submission_id]

    return {"message": "Submission cancelled", "submission_id": submission_id}


# =============================================================================
# MULTI-COVERAGE ENDPOINTS
# =============================================================================

@router.post("/submissions/multi", response_model=MultiCoverageResponse)
async def create_multi_coverage_submission(
    request: MultiCoverageRequest,
    background_tasks: BackgroundTasks,
):
    """
    Create a multi-coverage submission.

    Prices multiple coverages from a single submission using the
    actual workflow engine.
    """
    result_id = generate_id("mcs")
    now = datetime.utcnow()
    start_time = time.time()

    coverages = request.coverages or ["cyber"]

    coverage_quotes: Dict[str, QuoteResponse] = {}
    failed_coverages: List[str] = []

    for coverage in coverages:
        try:
            submission_id = generate_id("sub")
            quote_id = generate_id("quo")

            sub_data = {
                "submission_id": submission_id,
                "entity_name": request.entity_name,
                "domain_hint": request.domain_hint,
                "coverage": coverage,
                "configuration": f"{coverage}_general",
                "status": SubmissionStatus.PROCESSING,
                "created_at": now,
                "updated_at": now,
                "quote_id": None,
            }
            _memory.submissions[submission_id] = sub_data

            result = run_assessment(
                entity_id=submission_id,
                coverage=coverage,
                submission_data=request.submission_data or {},
                direct_query_responses=request.direct_query_responses or {},
                entity_name=request.entity_name,
                domain_hint=request.domain_hint,
                country_hint=request.country_hint,
                skip_discovery=True,
            )

            decision_map = {
                DecisionType.APPROVE: "approve",
                DecisionType.REFER: "refer",
                DecisionType.DECLINE: "decline",
            }

            coverage_quotes[coverage] = QuoteResponse(
                quote_id=quote_id,
                submission_id=submission_id,
                status=QuoteStatus.READY,
                composite_score=result.composite_score,
                tier=result.tier,
                tier_label=result.tier_label,
                decision=decision_map.get(result.decision, "refer"),
                premium_options=result.premium_options,
                recommended_premium=result.recommended_premium,
                recommended_limit=result.recommended_limit,
                created_at=now,
                valid_until=now + timedelta(days=30),
            )

            _memory.submissions[submission_id]["status"] = SubmissionStatus.READY
            _memory.submissions[submission_id]["quote_id"] = quote_id

        except Exception as e:
            logger.error(f"Failed to price {coverage}: {e}")
            failed_coverages.append(coverage)

    successful = list(coverage_quotes.keys())
    discount = 0.0

    if len(successful) >= 2:
        discount = 0.05
        if len(successful) >= 3:
            discount = 0.10

    total = sum(q.recommended_premium or 0 for q in coverage_quotes.values())
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
async def get_job_status(job_id: str):
    """Get async job status."""
    if job_id not in _memory.jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _memory.jobs[job_id]

    submission_id = job.get("submission_id")
    if submission_id and submission_id in _memory.submissions:
        sub = _memory.submissions[submission_id]
        if sub["status"] == SubmissionStatus.READY:
            job["status"] = JobStatus.COMPLETED
            job["result"] = {"quote_id": sub.get("quote_id")}
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


# =============================================================================
# QUOTE RETRIEVAL (convenience endpoint)
# =============================================================================

@router.get("/submissions/{submission_id}/quote", response_model=QuoteResponse)
async def get_submission_quote(submission_id: str):
    """Get the quote for a submission."""
    if submission_id not in _memory.submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub = _memory.submissions[submission_id]

    if sub["status"] != SubmissionStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"Submission not ready (status: {sub['status'].value})",
        )

    quote_id = sub.get("quote_id")
    if not quote_id or quote_id not in _memory.quotes:
        raise HTTPException(status_code=404, detail="Quote not found")

    q = _memory.quotes[quote_id]

    return QuoteResponse(
        quote_id=q["quote_id"],
        submission_id=q["submission_id"],
        status=q["status"],
        composite_score=q["composite_score"],
        tier=q["tier"],
        tier_label=q["tier_label"],
        decision=q["decision"],
        premium_options=q["premium_options"],
        recommended_premium=q["recommended_premium"],
        recommended_limit=q.get("recommended_limit"),
        discovery=q.get("discovery"),
        created_at=q["created_at"],
        valid_until=q["valid_until"],
    )
