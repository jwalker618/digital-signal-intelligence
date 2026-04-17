"""V6/E7 (stage 1.3) — /api/v1/admin/rate-filing/generate handler tests."""
from __future__ import annotations

import pytest
from fastapi import HTTPException

from infrastructure.api.admin.rate_filing_routes import (
    RateFilingRequest,
    generate_rate_filing,
)


def test_generates_all_five_artefacts():
    req = RateFilingRequest(coverage="cyber", config="cyber_general", state="IL")
    resp = generate_rate_filing(req)
    assert resp.coverage == "cyber"
    assert resp.config == "cyber_general"
    assert resp.state == "IL"
    assert set(resp.files.keys()) == {
        "filing_memo.md",
        "actuarial_justification.md",
        "rate_exhibit.csv",
        "model_governance_statement.md",
        "filing_cover.txt",
    }
    # Spot-check content shape
    assert "Rate Filing Memo" in resp.files["filing_memo.md"]
    assert resp.files["rate_exhibit.csv"].startswith("exposure_band,")


def test_state_is_normalised_to_upper():
    resp = generate_rate_filing(
        RateFilingRequest(coverage="cyber", config="cyber_general", state="il")
    )
    assert resp.state == "IL"


def test_invalid_state_code_rejected():
    with pytest.raises(HTTPException) as exc:
        generate_rate_filing(
            RateFilingRequest(coverage="cyber", config="cyber_general", state="USA")
        )
    assert exc.value.status_code == 422


def test_missing_coverage_raises_404():
    with pytest.raises(HTTPException) as exc:
        generate_rate_filing(
            RateFilingRequest(coverage="doesnotexist", config="x_general", state="IL")
        )
    assert exc.value.status_code == 404


def test_missing_config_raises_404():
    with pytest.raises(HTTPException) as exc:
        generate_rate_filing(
            RateFilingRequest(coverage="cyber", config="cyber_nope", state="IL")
        )
    assert exc.value.status_code == 404
