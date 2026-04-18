"""V6/E7 — Rate-Filing admin endpoint.

`POST /api/v1/admin/rate-filing/generate` produces a SERFF-ready pack
for a (coverage, config, state) triple. The pack is identical to the
CLI output (`python -m infrastructure.admin.rate_filing`) — the
endpoint exists so tenant admins can generate filings from the UI
without shell access.

Gated by `Permission.ADMIN_SYSTEM`. The response returns the generated
artefacts as a single JSON bundle; the admin UI saves each section.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel, Field

from infrastructure.admin.rate_filing import FilingArtefacts, generate_filing
from infrastructure.api.auth.permissions import Permission, require_permission
from infrastructure.models.compiler import get_config, ConfigNotFoundError

logger = logging.getLogger("dsi.api.admin.rate_filing")
router = APIRouter()


class RateFilingRequest(BaseModel):
    coverage: str = Field(..., description="Coverage id, e.g. 'cyber'")
    config: str = Field(..., description="Sub-config id, e.g. 'cyber_general'")
    state: str = Field(..., description="US state code, e.g. 'IL'")


class RateFilingResponse(BaseModel):
    coverage: str
    config: str
    state: str
    files: Dict[str, str]


@router.post(
    "/admin/rate-filing/generate",
    response_model=RateFilingResponse,
    dependencies=[Depends(require_permission(Permission.ADMIN_SYSTEM))],
)
def generate_rate_filing(
    payload: RateFilingRequest = Body(...),
) -> RateFilingResponse:
    """Generate the SERFF-ready filing pack.

    Returns the five rendered artefacts as strings. The admin UI saves
    each into the filer's working directory. No files are written on
    the server — the endpoint is stateless.
    """
    # Validate coverage + config exist.
    try:
        get_config(payload.coverage, payload.config, allow_quarantined=True)
    except ConfigNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    state = payload.state.upper().strip()
    if len(state) != 2 or not state.isalpha():
        raise HTTPException(
            status_code=422,
            detail=f"state must be a two-letter code, got {payload.state!r}",
        )

    artefacts: FilingArtefacts = generate_filing(
        payload.coverage, payload.config, state,
    )
    return RateFilingResponse(
        coverage=payload.coverage,
        config=payload.config,
        state=state,
        files={
            "filing_memo.md": artefacts.filing_memo,
            "actuarial_justification.md": artefacts.actuarial_justification,
            "rate_exhibit.csv": artefacts.rate_exhibit_csv,
            "model_governance_statement.md": artefacts.model_governance,
            "filing_cover.txt": artefacts.cover_page,
        },
    )
