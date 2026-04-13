"""C-3: Recalibration route schemas and pure helpers (no DB required)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from infrastructure.api.recalibration.routes import (
    ApproveRequest,
    ProposalSummary,
    RejectRequest,
    TriggerRequest,
    _to_summary,
)


class TestApproveRejectSchemas:
    def test_approve_requires_rationale(self):
        with pytest.raises(ValidationError):
            ApproveRequest(rationale="")

    def test_reject_requires_rationale(self):
        with pytest.raises(ValidationError):
            RejectRequest(rationale="")

    def test_approve_with_rationale(self):
        r = ApproveRequest(rationale="Looks good — aligns with Q1 loss data.")
        assert r.rationale.startswith("Looks good")

    def test_rationale_max_length(self):
        with pytest.raises(ValidationError):
            ApproveRequest(rationale="x" * 10_001)


class TestTriggerRequestSchema:
    def test_minimal_valid_payload(self):
        t = TriggerRequest(
            coverage="PI",
            config_name="default",
            current_weights={"s1": 0.5, "s2": 0.5},
        )
        assert t.coverage == "PI"
        assert t.tier_boundaries == []

    def test_tier_boundaries_accepted(self):
        t = TriggerRequest(
            coverage="PI",
            config_name="default",
            current_weights={},
            tier_boundaries=[[1, 0, 300], [2, 300, 700]],
        )
        assert t.tier_boundaries[0] == [1, 0, 300]


class TestToSummary:
    def _base_row(self) -> dict:
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "coverage": "PI",
            "config_name": "default",
            "status": "PENDING_REVIEW",
            "proposed_at": datetime(2026, 4, 12, tzinfo=timezone.utc),
            "proposed_by": "engine",
            "trigger": "scheduled",
            "sample_size": 250,
            "weight_changes": [{"signal_id": "s1", "proposed_weight": 0.3}],
            "tier_threshold_changes": [{"band_id": 2, "boundary": "min", "proposed_value": 350}],
            "reviewer_id": None,
            "reviewed_at": None,
            "deployed_at": None,
        }

    def test_counts_changes(self):
        summary = _to_summary(self._base_row())
        assert summary.weight_change_count == 1
        assert summary.tier_change_count == 1
        assert summary.sample_size == 250
        assert summary.reviewer_id is None

    def test_null_changes_default_to_zero(self):
        row = self._base_row()
        row["weight_changes"] = None
        row["tier_threshold_changes"] = None
        summary = _to_summary(row)
        assert summary.weight_change_count == 0
        assert summary.tier_change_count == 0

    def test_sample_size_none_coerced_to_zero(self):
        row = self._base_row()
        row["sample_size"] = None
        summary = _to_summary(row)
        assert summary.sample_size == 0

    def test_propagates_reviewer_fields(self):
        row = self._base_row()
        row["reviewer_id"] = "user-abc"
        row["reviewed_at"] = datetime(2026, 4, 12, 13, tzinfo=timezone.utc)
        summary = _to_summary(row)
        assert summary.reviewer_id == "user-abc"
        assert summary.reviewed_at is not None


class TestProposalSummaryRoundTrip:
    def test_pydantic_roundtrip(self):
        s = ProposalSummary(
            id="x",
            coverage="PI",
            config_name="default",
            status="APPROVED",
            proposed_at=datetime(2026, 4, 12, tzinfo=timezone.utc),
            proposed_by="u1",
            trigger="manual",
            sample_size=100,
            weight_change_count=2,
            tier_change_count=0,
        )
        d = s.model_dump()
        assert d["status"] == "APPROVED"
        assert d["weight_change_count"] == 2
        assert d["reviewer_id"] is None
