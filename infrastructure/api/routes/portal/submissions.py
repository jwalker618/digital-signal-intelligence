"""v8 Phase 6: /portal/submissions/* routes.

  GET  /portal/submissions/{code}            -> SubmissionDetailResponse
  GET  /portal/submissions/{code}/score      -> ScoreResponse
  GET  /portal/submissions/{code}/peers      -> PeersResponse
  GET  /portal/submissions/{code}/actions    -> ActionsResponse
  POST /portal/submissions                   -> InitiateSubmissionResponse (CLIENT-only)

Score / peers / actions delegate to the pure services from
Phases 2-4 (no business logic here, just wiring).
"""
from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.api.auth.permissions import (
    AuthContext,
    Permission,
    require_permission,
)
from infrastructure.db.config import get_async_db
from infrastructure.db.models import (
    ModelVersionRecord,
    Quote,
    Referral,
    Submission,
)
from infrastructure.models.compiler import get_config
from layers.cohort.queries import fetch_cohort_scores
from layers.cohort.service import (
    cohort_stats_from_scores,
    percentile_from_scores,
)
from layers.risk.impact_breakdown import compute_from_model_version
from layers.risk.remediation import build_remediation_plan

from .dependencies import require_portal_user, scoped_submission
from .schemas import (
    ActionsResponse,
    InitiateSubmissionRequest,
    InitiateSubmissionResponse,
    PeersResponse,
    QuoteEvolutionEntry,
    ReferralInfo,
    ScoreResponse,
    SubmissionDetailResponse,
)

router = APIRouter()


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

async def _latest_mv(
    submission: Submission, db: AsyncSession,
) -> Optional[ModelVersionRecord]:
    q = await db.execute(
        select(ModelVersionRecord).where(
            ModelVersionRecord.submission_id == submission.id,
            ModelVersionRecord.is_latest == True,  # noqa: E712
        )
    )
    return q.scalar_one_or_none()


# -----------------------------------------------------------------------------
# GET /portal/submissions/{code}/score
# -----------------------------------------------------------------------------

@router.get("/submissions/{submission_code}/score", response_model=ScoreResponse)
async def submission_score(
    submission: Submission = Depends(scoped_submission),
    db: AsyncSession = Depends(get_async_db),
) -> ScoreResponse:
    mv = await _latest_mv(submission, db)
    if mv is None:
        return ScoreResponse(
            submission_code=submission.submission_code,
            coverage=submission.coverage,
        )

    breakdown = compute_from_model_version(mv)
    return ScoreResponse(
        submission_code=submission.submission_code,
        coverage=submission.coverage,
        composite_score=mv.final_composite_score,
        tier=mv.final_tier,
        base_premium=mv.base_premium,
        final_premium=mv.final_premium,
        impact_breakdown=breakdown,
    )


# -----------------------------------------------------------------------------
# GET /portal/submissions/{code}/peers
# -----------------------------------------------------------------------------

@router.get("/submissions/{submission_code}/peers", response_model=PeersResponse)
async def submission_peers(
    submission: Submission = Depends(scoped_submission),
    db: AsyncSession = Depends(get_async_db),
) -> PeersResponse:
    mv = await _latest_mv(submission, db)
    if mv is None or mv.peer_cohort_id is None:
        return PeersResponse(
            submission_code=submission.submission_code,
            coverage=submission.coverage,
            note="No cohort data available for this submission",
        )

    # If cohort fields were populated at persistence time (Phase 2), use them
    # directly. Otherwise fall back to a fresh stats lookup.
    cohort_id = mv.peer_cohort_id
    scores = await fetch_cohort_scores(db, cohort_id)
    stats = cohort_stats_from_scores(cohort_id, scores)

    return PeersResponse(
        submission_code=submission.submission_code,
        coverage=submission.coverage,
        cohort_id=cohort_id,
        cohort_size=(len(scores) if scores else mv.peer_cohort_size),
        peer_percentile_rank=(
            percentile_from_scores(scores, mv.final_composite_score)
            if mv.final_composite_score is not None and scores
            else mv.peer_percentile_rank
        ),
        cohort_mean_score=(stats.mean if stats else mv.peer_cohort_mean_score),
        cohort_median_score=(stats.median if stats else mv.peer_cohort_median_score),
        entity_score=mv.final_composite_score,
        signal_ranking=None,  # v8.1: signal Z-score ranking requires per-signal cohort aggregation
        note=(None if stats else "Insufficient peers"),
    )


# -----------------------------------------------------------------------------
# GET /portal/submissions/{code}/actions
# -----------------------------------------------------------------------------

@router.get("/submissions/{submission_code}/actions", response_model=ActionsResponse)
async def submission_actions(
    submission: Submission = Depends(scoped_submission),
    db: AsyncSession = Depends(get_async_db),
) -> ActionsResponse:
    mv = await _latest_mv(submission, db)
    if mv is None:
        # No assessment yet -> empty plan
        return ActionsResponse(
            submission_code=submission.submission_code,
            coverage=submission.coverage,
            remediation_plan=build_remediation_plan(
                impact_breakdown=compute_from_model_version(_StubMV()),
                signal_remediation=None,
            ),
        )

    breakdown = compute_from_model_version(mv)
    try:
        cfg = get_config(submission.coverage, submission.configuration)
        rem_map = cfg.signal_remediation
    except Exception:
        rem_map = None

    plan = build_remediation_plan(
        impact_breakdown=breakdown,
        signal_remediation=rem_map,
    )
    return ActionsResponse(
        submission_code=submission.submission_code,
        coverage=submission.coverage,
        remediation_plan=plan,
    )


class _StubMV:
    """Empty placeholder used when no MV exists yet."""
    modifiers_applied = []
    base_premium = 0.0
    final_premium = 0.0
    premium_after_modifiers = 0.0


# -----------------------------------------------------------------------------
# GET /portal/submissions/{code}
# -----------------------------------------------------------------------------

@router.get(
    "/submissions/{submission_code}",
    response_model=SubmissionDetailResponse,
)
async def submission_detail(
    submission: Submission = Depends(scoped_submission),
    db: AsyncSession = Depends(get_async_db),
) -> SubmissionDetailResponse:
    """Detail view: submission + quote history + open referral."""
    mvs_q = await db.execute(
        select(ModelVersionRecord)
        .where(ModelVersionRecord.submission_id == submission.id)
        .order_by(ModelVersionRecord.version_number.asc())
    )
    mvs = list(mvs_q.scalars().all())

    quotes_q = await db.execute(
        select(Quote)
        .where(Quote.submission_id == submission.id)
        .order_by(Quote.created_at.asc())
    )
    quotes = list(quotes_q.scalars().all())

    # Build a map from model_version_id -> MV for quote lookup
    mv_by_id = {mv.id: mv for mv in mvs}

    evolution = []
    for q in quotes:
        mv = mv_by_id.get(q.model_version_id)
        evolution.append(
            QuoteEvolutionEntry(
                quote_code=q.quote_code,
                version_number=(mv.version_number if mv else 0),
                composite_score=(mv.final_composite_score if mv else None),
                tier=(mv.final_tier if mv else None),
                final_premium=(mv.final_premium if mv else q.recommended_premium),
                created_at=q.created_at,
            )
        )

    # Pick the most recent referral
    referral_q = await db.execute(
        select(Referral)
        .join(Quote, Referral.quote_id == Quote.id)
        .where(Quote.submission_id == submission.id)
        .order_by(Referral.created_at.desc())
        .limit(1)
    )
    referral = referral_q.scalar_one_or_none()
    referral_info = (
        ReferralInfo(
            referral_code=referral.referral_code,
            status=referral.status.value,
            awaiting_party=referral.awaiting_party,
        )
        if referral
        else None
    )

    return SubmissionDetailResponse(
        submission_code=submission.submission_code,
        entity_name=submission.entity_name,
        coverage=submission.coverage,
        status=submission.status.value if submission.status else "unknown",
        created_at=submission.created_at,
        quotes=evolution,
        referral=referral_info,
    )


# -----------------------------------------------------------------------------
# POST /portal/submissions
# -----------------------------------------------------------------------------

@router.post(
    "/submissions",
    response_model=InitiateSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initiate_submission(
    payload: InitiateSubmissionRequest,
    db: AsyncSession = Depends(get_async_db),
    ctx: AuthContext = Depends(require_permission(Permission.PORTAL_CLIENT_SUBMIT)),
) -> InitiateSubmissionResponse:
    """Initiate a renewal / new submission from the client portal.

    Thin wrapper: persists a Submission row with broker_id derived from
    the client tenant's broker linkage (looked up on the user record),
    then the standard submission workflow runs asynchronously via the
    existing submissions route. v8 demo path runs synchronously via
    Phase 7's seed/reset.

    For the v8 cut, this endpoint creates the Submission row in the
    PENDING state and returns. Actual workflow execution is exercised
    by the standard /api/v1/submissions path when called against the
    same submission_code.
    """
    from infrastructure.db.models import SubmissionStatus
    from infrastructure.db.repositories import generate_id

    if not ctx.user_id:
        raise HTTPException(401, "Authenticated user required")

    try:
        user_uuid = uuid.UUID(ctx.user_id)
    except (ValueError, TypeError):
        raise HTTPException(400, "Malformed user id")

    user_q = await db.execute(select(User).where(User.id == user_uuid))  # type: ignore[name-defined]
    user = user_q.scalar_one_or_none()
    if user is None:
        raise HTTPException(401, "User record not found")

    submission_code = generate_id("sub")
    submission = Submission(
        submission_code=submission_code,
        entity_name=payload.entity_name,
        domain_hint=payload.domain_hint,
        country_hint=payload.country_hint,
        coverage=payload.coverage,
        configuration=payload.configuration or f"{payload.coverage}_general",
        status=SubmissionStatus.PENDING,
        submission_data=payload.submission_data or {},
        direct_query_responses=payload.direct_query_responses or {},
        broker_id=getattr(user, "broker_id", None),
        created_by=user_uuid,
    )
    db.add(submission)
    await db.flush()
    await db.commit()

    return InitiateSubmissionResponse(
        submission_code=submission_code,
        status=submission.status.value,
    )


# Lazy import after function defs to avoid circular references
from infrastructure.db.models import User  # noqa: E402
