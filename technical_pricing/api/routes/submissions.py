"""
DSI Submission Endpoints (Phase 11)

Endpoints for creating and managing submissions.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

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


logger = logging.getLogger("dsi.api.submissions")

router = APIRouter()


# =============================================================================
# IN-MEMORY STORAGE (Replace with database)
# =============================================================================

_submissions: dict = {}
_jobs: dict = {}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_id(prefix: str) -> str:
    """Generate a unique ID."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def process_submission(submission_id: str, request: SubmissionRequest):
    """Background task to process a submission."""
    logger.info(f"Processing submission {submission_id}")

    # Update status
    if submission_id in _submissions:
        _submissions[submission_id]["status"] = SubmissionStatus.PROCESSING

    # Simulate processing
    # In production, this would:
    # 1. Run discovery
    # 2. Execute workflow
    # 3. Generate quote

    # For now, create a mock result
    quote_id = generate_id("quo")

    if submission_id in _submissions:
        _submissions[submission_id]["status"] = SubmissionStatus.READY
        _submissions[submission_id]["quote_id"] = quote_id
        _submissions[submission_id]["updated_at"] = datetime.utcnow()


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

    # Store submission
    _submissions[submission_id] = {
        "submission_id": submission_id,
        "entity_name": request.entity_name,
        "domain_hint": request.domain_hint,
        "coverage": request.coverage,
        "configuration": request.configuration or f"{request.coverage}_general",
        "status": SubmissionStatus.PENDING,
        "created_at": now,
        "updated_at": now,
        "quote_id": None,
        "submission_data": request.submission_data,
        "direct_query_responses": request.direct_query_responses,
    }

    # Estimate completion time
    estimated_completion = now + timedelta(seconds=30)

    if request.async_mode:
        # Create job for tracking
        job_id = generate_id("job")
        _jobs[job_id] = {
            "job_id": job_id,
            "status": JobStatus.PENDING,
            "submission_id": submission_id,
            "created_at": now,
        }

        # Process in background
        background_tasks.add_task(process_submission, submission_id, request)

        return SubmissionResponse(
            submission_id=submission_id,
            status=SubmissionStatus.PROCESSING,
            estimated_completion=estimated_completion,
            job_id=job_id,
        )
    else:
        # Process synchronously (simplified)
        await process_submission(submission_id, request)

        return SubmissionResponse(
            submission_id=submission_id,
            status=_submissions[submission_id]["status"],
            estimated_completion=None,
        )


@router.get("/submissions", response_model=List[SubmissionDetail])
async def list_submissions(
    coverage: Optional[str] = Query(None, description="Filter by coverage"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
):
    """
    List submissions with optional filtering.
    """
    results = list(_submissions.values())

    # Apply filters
    if coverage:
        results = [s for s in results if s["coverage"] == coverage]

    if status:
        results = [s for s in results if s["status"].value == status]

    # Sort by created_at descending
    results.sort(key=lambda s: s["created_at"], reverse=True)

    # Paginate
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
    """
    Get submission details by ID.
    """
    if submission_id not in _submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    s = _submissions[submission_id]

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
    """
    Cancel a pending submission.
    """
    if submission_id not in _submissions:
        raise HTTPException(status_code=404, detail="Submission not found")

    s = _submissions[submission_id]

    if s["status"] not in [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot cancel submission in current status"
        )

    del _submissions[submission_id]

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

    Prices multiple coverages and/or locales from a single submission.
    """
    result_id = generate_id("mcs")
    now = datetime.utcnow()

    # Determine coverages
    coverages = request.coverages or ["cyber"]  # Default

    # Create individual submissions for each coverage
    coverage_quotes = {}
    failed_coverages = []

    for coverage in coverages:
        try:
            submission_id = generate_id("sub")
            quote_id = generate_id("quo")

            # Store submission
            _submissions[submission_id] = {
                "submission_id": submission_id,
                "entity_name": request.entity_name,
                "domain_hint": request.domain_hint,
                "coverage": coverage,
                "configuration": f"{coverage}_general",
                "status": SubmissionStatus.READY,
                "created_at": now,
                "updated_at": now,
                "quote_id": quote_id,
            }

            # Create mock quote
            coverage_quotes[coverage] = QuoteResponse(
                quote_id=quote_id,
                submission_id=submission_id,
                status=QuoteStatus.READY,
                composite_score=750,
                tier=2,
                tier_label="STANDARD",
                decision="approve",
                premium_options={
                    "1000000": 12500,
                    "2000000": 18750,
                    "5000000": 31250,
                },
                recommended_premium=18750,
                recommended_limit=2000000,
                created_at=now,
                valid_until=now + timedelta(days=30),
            )

        except Exception as e:
            logger.error(f"Failed to price {coverage}: {e}")
            failed_coverages.append(coverage)

    # Calculate package discount
    successful = list(coverage_quotes.keys())
    discount = 0.0
    combined = 0.0

    if len(successful) >= 2:
        discount = 0.05  # 5% for 2+ coverages
        if len(successful) >= 3:
            discount = 0.10  # 10% for 3+ coverages

    total = sum(q.recommended_premium or 0 for q in coverage_quotes.values())
    savings = total * discount
    combined = total - savings

    return MultiCoverageResponse(
        result_id=result_id,
        entity_name=request.entity_name,
        detected_locale="US",
        coverage_quotes=coverage_quotes,
        failed_coverages=failed_coverages,
        recommended_package=successful,
        package_discount=discount,
        combined_premium=combined,
        total_savings=savings,
        duration_seconds=2.5,
        cache_hit_rate=0.35,
    )


# =============================================================================
# JOB ENDPOINTS
# =============================================================================

@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    """
    Get async job status.
    """
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = _jobs[job_id]

    # Check submission status
    submission_id = job.get("submission_id")
    if submission_id and submission_id in _submissions:
        sub = _submissions[submission_id]
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
