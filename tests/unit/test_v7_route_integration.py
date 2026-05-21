"""V7 route-layer integration — additive carry-forward + helpers.

These tests cover the safe-additive bits of the route-layer follow-up:
  - WorkflowResult carries composite-grade fields out of run_workflow.
  - v7_persistence helpers build the right repo kwargs / quote dict.
  - workflow_result_to_quote includes the V7 evidence block.
  - WorkflowEngine.run_variant_loop_for_scored is a no-op without an LLM.
  - copy_to_new_version (signal-override re-version) propagates V7 fields.
"""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from layers.risk.types import (
    GroupGradeRollup,
    ScoringResult,
    SignalOutput,
    WorkflowResult,
)
from layers.risk.v7_persistence import (
    disclosure_packet_payload_from_result,
    mv_create_kwargs_from_result,
    quote_dict_evidence_fields,
    signal_records_from_outputs,
)


def _result_with_v7():
    return WorkflowResult(
        entity_id="acme",
        coverage="cyber",
        composite_score=82.0,
        confidence=0.9,
        tier=2,
        tier_label="STANDARD",
        composite_min_grade="observed",
        composite_weighted_mean_grade=2.4,
        composite_grade_distribution={"observed": 0.6, "structured_attested": 0.4},
        group_grade_rollups={
            "g1": {"min_grade": "observed", "weighted_mean_grade": 2.0, "distribution": {"observed": 1.0}},
        },
        primitive_grade_rollups={
            "cyber": {"min_grade": "observed", "weighted_mean_grade": 2.0, "distribution": {"observed": 1.0}},
        },
        referral_reasons=["normal reason"],
    )


# ---------------------------------------------------------------------------
# WorkflowResult carries composite-grade fields
# ---------------------------------------------------------------------------

class TestWorkflowResultV7Fields:
    def test_defaults_safe_for_pre_v7_callers(self):
        r = WorkflowResult()
        assert r.composite_min_grade is None
        assert r.composite_weighted_mean_grade is None
        assert r.composite_grade_distribution == {}
        assert r.group_grade_rollups == {}
        assert r.primitive_grade_rollups == {}

    def test_explicit_assignment(self):
        r = _result_with_v7()
        assert r.composite_min_grade == "observed"
        assert r.group_grade_rollups["g1"]["min_grade"] == "observed"
        assert r.primitive_grade_rollups["cyber"]["weighted_mean_grade"] == 2.0


# ---------------------------------------------------------------------------
# v7_persistence helpers
# ---------------------------------------------------------------------------

class TestMVCreateKwargs:
    def test_kwargs_include_v7_composite(self):
        kw = mv_create_kwargs_from_result(_result_with_v7())
        assert kw["composite_min_grade"] == "observed"
        assert kw["composite_weighted_mean_grade"] == 2.4
        assert kw["composite_grade_distribution"] == {"observed": 0.6, "structured_attested": 0.4}
        # And the pre-V7 keys still there.
        assert kw["coverage"] == "cyber"
        assert kw["pure_composite_score"] == 82.0
        assert kw["final_tier"] == 2

    def test_submission_id_not_included(self):
        # submission_id must be passed explicitly by the caller, not built
        # by this helper.
        kw = mv_create_kwargs_from_result(_result_with_v7())
        assert "submission_id" not in kw

    def test_version_type_overridable(self):
        kw = mv_create_kwargs_from_result(_result_with_v7(), version_type="referral_review")
        assert kw["version_type"] == "referral_review"


class TestSignalRecordsFromOutputs:
    def test_includes_v7_evidence_fields(self):
        outs = [
            SignalOutput(
                signal_id="sanctions_check",
                signal_name="sanctions",
                group_id="risk",
                raw_score=95.0,
                confidence=0.85,
                weighted_score=47.5,
                weight=0.5,
                evidence_grade="structured_attested",
                evidence_basis="OFAC + UK OFSI agreed",
                evidence_pro="multi-source",
                evidence_counter="US/UK only",
                evidence_tie_breaker="OFAC 24h refresh",
                absence_sub_type=None,
                primitive_type="regulatory",
            ),
        ]
        records = signal_records_from_outputs(outs, entity_code="acme")
        assert len(records) == 1
        r = records[0]
        assert r["signal_code"] == "sanctions_check"
        assert r["evidence_grade"] == "structured_attested"
        assert r["evidence_basis"] == "OFAC + UK OFSI agreed"
        assert r["evidence_pro"] == "multi-source"
        assert r["primitive_type"] == "regulatory"
        # Defaulted fields:
        assert r["was_absent"] is False
        assert r["evidence_sources"] == []

    def test_error_output_marked_absent(self):
        outs = [SignalOutput(
            signal_id="x", signal_name="x", group_id="g",
            raw_score=0, confidence=0, weighted_score=0, weight=1,
            error="fetch failed",
        )]
        r = signal_records_from_outputs(outs, entity_code="acme")[0]
        assert r["was_absent"] is True


class TestQuoteDictEvidenceFields:
    def test_includes_all_composite_pieces(self):
        ev = quote_dict_evidence_fields(_result_with_v7())
        assert ev["composite_min_grade"] == "observed"
        assert "composite_weighted_mean_grade" in ev
        assert "composite_grade_distribution" in ev
        assert "group_grade_rollups" in ev
        assert "primitive_grade_rollups" in ev

    def test_empty_for_pre_v7_result(self):
        ev = quote_dict_evidence_fields(WorkflowResult())
        assert ev["composite_min_grade"] is None
        assert ev["composite_grade_distribution"] == {}


class TestDisclosurePacketCaching:
    def test_no_grade_referral_returns_none(self):
        r = _result_with_v7()  # has a non-grade referral_reason
        assert disclosure_packet_payload_from_result(r, model_version_id=uuid.uuid4()) is None

    def test_grade_referral_produces_packet(self):
        r = _result_with_v7()
        r.referral_reasons = ["[evidence_grade] only 30% of weight at observed+"]
        out = disclosure_packet_payload_from_result(r, model_version_id=uuid.uuid4())
        assert out is not None
        assert "markdown" in out
        assert "payload" in out
        # Composite distribution surfaces in the markdown body.
        assert "observed" in out["markdown"]

    def test_packet_deterministic_for_same_inputs(self):
        from datetime import datetime, timezone
        from signal_architecture.disclosure import PacketSection, build_packet
        # Direct call to build_packet to confirm determinism guarantee
        # still holds end-to-end.
        pinned = datetime(2026, 5, 13, tzinfo=timezone.utc)
        kw = dict(
            model_version_id=uuid.UUID(int=1),
            composite_min_grade="observed",
            composite_distribution={"observed": 1.0},
            referral_reasons=["[evidence_grade] test"],
            sections=[],
            generated_at=pinned,
        )
        md1, p1 = build_packet(**kw)
        md2, p2 = build_packet(**kw)
        assert md1 == md2 and p1 == p2


# ---------------------------------------------------------------------------
# WorkflowEngine.run_variant_loop_for_scored
# ---------------------------------------------------------------------------

class TestVariantHook:
    def test_no_llm_returns_empty(self):
        from layers.risk.workflow import WorkflowEngine
        engine = WorkflowEngine()
        sr = ScoringResult()
        out = engine.run_variant_loop_for_scored(sr)
        assert out == []

    def test_with_llm_and_extractor_returns_list(self):
        # Even with both supplied, the current scoring doesn't carry
        # cluster_id onto SignalOutput, so is_trigger refuses every
        # signal -> empty list. This documents the integration boundary
        # — once Phase 10's cluster_id propagation lands, this test will
        # naturally start picking up variants.
        from layers.risk.workflow import WorkflowEngine
        engine = WorkflowEngine()
        sr = ScoringResult()
        sr.signal_outputs = [
            SignalOutput(
                signal_id="x", signal_name="x", group_id="g",
                raw_score=50, confidence=1.0, weighted_score=50, weight=1.0,
                evidence_grade="structured_attested",
                evidence_basis="b",
                primitive_type="regulatory",
            ),
        ]
        llm = MagicMock(return_value="{}")
        extractor = MagicMock(return_value=None)
        out = engine.run_variant_loop_for_scored(
            sr, validator_verdicts={"x": True},
            llm_callable=llm, extract_for_variant=extractor,
        )
        # Hook runs without error; produces no variants because cluster_id
        # isn't propagated from aggregator metadata yet.
        assert isinstance(out, list)


# ---------------------------------------------------------------------------
# copy_to_new_version V7 propagation
# ---------------------------------------------------------------------------

class TestCopyToNewVersion:
    @pytest.mark.asyncio
    async def test_propagates_v7_fields(self):
        """End-to-end via mocked async session — confirm the new rows
        carry the V7 evidence fields verbatim."""
        from infrastructure.db.models import ModelVersionSignal
        from infrastructure.db.repositories import ModelVersionSignalRepository

        src = ModelVersionSignal(
            model_version_id=uuid.UUID(int=1),
            signal_cache_id=uuid.UUID(int=10),
            signal_id=42,
            entity_code="acme",
            score=72.0,
            weight=0.5,
            contribution=36.0,
            evidence_grade="structured_attested",
            evidence_basis="OFAC + OFSI",
            evidence_pro="agreed",
            evidence_counter="US/UK",
            absence_sub_type=None,
            primitive_type="regulatory",
        )
        db = MagicMock()
        db.add_all = MagicMock()
        db.flush = AsyncMock()

        repo = ModelVersionSignalRepository(db)
        repo.get_by_model_version = AsyncMock(return_value=[src])
        new_rows = await repo.copy_to_new_version(
            source_model_version_id=uuid.UUID(int=1),
            target_model_version_id=uuid.UUID(int=2),
        )
        assert len(new_rows) == 1
        nr = new_rows[0]
        assert nr.evidence_grade == "structured_attested"
        assert nr.evidence_basis == "OFAC + OFSI"
        assert nr.evidence_pro == "agreed"
        assert nr.primitive_type == "regulatory"


# ---------------------------------------------------------------------------
# workflow_result_to_quote includes V7 evidence block
# ---------------------------------------------------------------------------

class TestQuoteDictBuilder:
    def test_evidence_key_present(self):
        from infrastructure.api.routes.submissions import workflow_result_to_quote
        d = workflow_result_to_quote(_result_with_v7(), "sub-1", "quo-1")
        assert "evidence" in d
        assert d["evidence"]["composite_min_grade"] == "observed"
        # Pre-V7 keys still there.
        assert d["composite_score"] == 82.0
        assert d["recommended_premium"] == 0.0
