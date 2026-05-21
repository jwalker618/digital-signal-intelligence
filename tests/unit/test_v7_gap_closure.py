"""V7 route-layer follow-up: gap closure (LLM factory, cluster_id
propagation, delta workflow runner, primary write path)."""
from __future__ import annotations

import os
import uuid as _uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Gap 3 — LLM client factory
# ---------------------------------------------------------------------------

class TestLLMClientFactory:
    def setup_method(self):
        from infrastructure.llm import reset_client_cache
        reset_client_cache()

    def test_default_provider_is_stub(self):
        from infrastructure.llm import get_llm_client
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("DSI_LLM_PROVIDER", None)
            c = get_llm_client()
        assert c(system="x", user="y") == "{}"

    def test_explicit_stub(self):
        from infrastructure.llm import get_llm_client, reset_client_cache
        reset_client_cache()
        with patch.dict(os.environ, {"DSI_LLM_PROVIDER": "stub"}):
            assert get_llm_client()(system="x", user="y") == "{}"

    def test_unknown_provider_falls_back_to_stub(self):
        from infrastructure.llm import get_llm_client, reset_client_cache
        reset_client_cache()
        with patch.dict(os.environ, {"DSI_LLM_PROVIDER": "made_up"}):
            assert get_llm_client()(system="x", user="y") == "{}"

    def test_anthropic_without_key_falls_back_to_stub(self):
        from infrastructure.llm import get_llm_client, reset_client_cache
        reset_client_cache()
        env = {"DSI_LLM_PROVIDER": "anthropic"}
        # Make sure no API key set.
        with patch.dict(os.environ, env, clear=False):
            os.environ.pop("ANTHROPIC_API_KEY", None)
            assert get_llm_client()(system="x", user="y") == "{}"

    def test_custom_callable_resolves(self):
        from infrastructure.llm import get_llm_client, reset_client_cache
        reset_client_cache()
        import sys, types
        mod = types.ModuleType("dsi_test_custom_llm")
        mod.fn = lambda system, user: f"custom:{user}"
        sys.modules["dsi_test_custom_llm"] = mod
        try:
            with patch.dict(os.environ, {
                "DSI_LLM_PROVIDER": "callable",
                "DSI_LLM_CALLABLE": "dsi_test_custom_llm.fn",
            }):
                out = get_llm_client()(system="x", user="hi")
            assert out == "custom:hi"
        finally:
            sys.modules.pop("dsi_test_custom_llm", None)

    def test_cache_persists_across_calls(self):
        from infrastructure.llm import get_llm_client, reset_client_cache
        reset_client_cache()
        with patch.dict(os.environ, {"DSI_LLM_PROVIDER": "stub"}):
            c1 = get_llm_client()
            c2 = get_llm_client()
        assert c1 is c2


# ---------------------------------------------------------------------------
# Gap 2 — cluster_id propagation through scorer + variant hook
# ---------------------------------------------------------------------------

class TestClusterIdPropagation:
    def test_signal_output_has_cluster_fields(self):
        from layers.risk.types import SignalOutput
        so = SignalOutput(
            signal_id="x", signal_name="x", group_id="g",
            raw_score=0, confidence=0, weighted_score=0, weight=0,
            cluster_id="C-abc", cluster_deterministic=True,
        )
        assert so.cluster_id == "C-abc"
        assert so.cluster_deterministic is True

    def test_scorer_propagates_cluster_id_from_result_metadata(self):
        """The scorer pulls cluster_id from result.metadata when
        constructing SignalOutput."""
        from infrastructure.models.config_schema import (
            ExpectationLevel,
            ProxyTier,
            SignalDefinition,
            ThreeLayerAssessment,
        )
        from layers.risk.scorer import ModelScorer
        from signal_architecture.signals.inference.registry import (
            register_inference_function,
        )
        from signal_architecture.signals.types import (
            InferenceContext,
            SignalResult,
        )

        # Register a fake inference function that returns a SignalResult
        # carrying cluster_id in metadata — the routed-signals pattern.
        def _fake_routed(entity_id, ctx):
            return SignalResult(
                signal_id="phase14_test_routed",
                score=80.0, confidence=0.9,
                evidence_grade="structured_attested",
                evidence_basis="multi-source",
                metadata={
                    "routing_type": "multi_source",
                    "cluster_id": "C-zzz",
                    "cluster_deterministic": True,
                },
            )
        register_inference_function("phase14_test_routed_basefunction", _fake_routed)

        scorer = ModelScorer()
        sig_def = SignalDefinition(
            id="phase14_test_routed",
            inference_utility_function="phase14_test_routed_basefunction",
            proxy_tier=ProxyTier.DIRECT_OBSERVABLE,
            expectation_level=ExpectationLevel.UNIVERSAL,
            three_layer_assessment=ThreeLayerAssessment(group_id="g"),
        )
        ctx = InferenceContext(configuration={}, coverage="cyber", config_name="cyber_general")
        out = scorer._extract_signal(
            entity_id="e", signal=sig_def, group_id="g", weight=0.5, context=ctx,
        )
        assert out.cluster_id == "C-zzz"
        assert out.cluster_deterministic is True

    def test_variant_hook_reads_cluster_id_from_signal_output(self):
        """run_variant_loop_for_scored now uses real cluster_id, not the
        is_trigger-rejecting stub from commit 1."""
        from layers.risk.types import ScoringResult, SignalOutput
        from layers.risk.workflow import WorkflowEngine

        engine = WorkflowEngine()
        sr = ScoringResult()
        sr.signal_outputs = [
            SignalOutput(
                signal_id="x", signal_name="x", group_id="g",
                raw_score=80, confidence=0.9, weighted_score=40, weight=0.5,
                evidence_grade="structured_attested",
                evidence_basis="b",
                primitive_type="regulatory",
                cluster_id="C-zzz",
                cluster_deterministic=True,
            ),
        ]
        # is_trigger now passes (real cluster) -> the loop will call
        # generate_variants_for. With a stub LLM that returns valid JSON,
        # we should get at least one query attempt.
        import json
        llm = MagicMock(return_value=json.dumps({
            "variants": [
                {"kind": "name_variant", "target_ref": "alt", "rationale": "test"},
            ],
        }))
        from signal_architecture.signals.types import SignalResult
        extractor = MagicMock(return_value=SignalResult(
            signal_id="x_alt", score=50, confidence=0.5,
            evidence_grade="observed", evidence_basis="alt",
        ))
        out = engine.run_variant_loop_for_scored(
            sr, validator_verdicts={"x": True},
            llm_callable=llm, extract_for_variant=extractor,
        )
        # Now we should get a variant signal.
        assert len(out) == 1
        assert out[0].variant_of == "x"


# ---------------------------------------------------------------------------
# Gap 4 — Delta workflow runner
# ---------------------------------------------------------------------------

class TestDeltaWorkflowRunner:
    def test_raises_without_submission_id(self):
        from layers.risk.delta_recompute import _do_delta_recompute
        db = MagicMock()
        with pytest.raises(ValueError):
            _do_delta_recompute(
                db,
                event_id=_uuid.uuid4(),
                submission_id=None,
                entity_id="acme",
                signal_filter={"x"},
            )

    def test_raises_without_prior_mv(self):
        from layers.risk.delta_recompute import _do_delta_recompute

        db = MagicMock()
        # mv lookup returns None.
        db.query.return_value.filter.return_value.first.return_value = None
        with pytest.raises(ValueError):
            _do_delta_recompute(
                db,
                event_id=_uuid.uuid4(),
                submission_id=_uuid.uuid4(),
                entity_id="acme",
                signal_filter={"x"},
            )

    def test_carries_forward_unchanged_signals(self):
        """A signal NOT in the filter set keeps its prior history row."""
        from infrastructure.db.models import (
            ModelVersionRecord,
            SignalHistory,
        )
        from layers.risk.delta_recompute import _do_delta_recompute

        prev_mv = ModelVersionRecord(
            id=_uuid.uuid4(),
            submission_id=_uuid.uuid4(),
            version_number=1,
            is_latest=True,
            coverage="cyber",
            pure_composite_score=50.0,
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 1.0},
        )
        prior_hist = [
            SignalHistory(
                id=_uuid.uuid4(),
                model_version_id=prev_mv.id,
                submission_id=prev_mv.submission_id,
                signal_id="unchanged_signal",
                recorded_at=datetime.now(timezone.utc),
                score=75.0,
                evidence_grade="corroborated",
                evidence_basis="prev value",
            ),
        ]

        db = MagicMock()
        # First query: ModelVersionRecord lookup.
        # Second query: SignalHistory ordered list.
        # Third query: update is_latest -> chained .filter().update()
        chain_mv = MagicMock()
        chain_mv.filter.return_value.first.return_value = prev_mv

        chain_hist = MagicMock()
        chain_hist.filter.return_value.order_by.return_value.all.return_value = prior_hist

        chain_update = MagicMock()
        chain_update.filter.return_value.update = MagicMock()

        # Cycle through the mocks per query call.
        db.query.side_effect = [chain_mv, chain_hist, chain_update]

        added_rows = []
        db.add.side_effect = lambda r: added_rows.append(r)
        db.flush = MagicMock()

        new_mv_id = _do_delta_recompute(
            db,
            event_id=_uuid.uuid4(),
            submission_id=prev_mv.submission_id,
            entity_id="acme",
            signal_filter=set(),  # NOTHING to re-extract -> all carry-forward
        )
        assert isinstance(new_mv_id, _uuid.UUID)

        # We expect: 1 new ModelVersionRecord + 1 carry-forward SignalHistory.
        mv_added = [r for r in added_rows if isinstance(r, ModelVersionRecord)]
        hist_added = [r for r in added_rows if isinstance(r, SignalHistory)]
        assert len(mv_added) == 1
        assert mv_added[0].version_type == "delta_recompute"
        assert mv_added[0].version_number == 2
        assert mv_added[0].is_latest is True
        # composite-grade fields carried forward.
        assert mv_added[0].composite_min_grade == "observed"
        # signal_history carry-forward — same signal_id + same score.
        assert len(hist_added) == 1
        assert hist_added[0].signal_id == "unchanged_signal"
        assert hist_added[0].score == 75.0
        assert hist_added[0].history_metadata["carried_forward"] is True

    def test_reextract_or_carry_falls_back_when_fn_missing(self):
        from infrastructure.db.models import SignalHistory
        from layers.risk.delta_recompute import _reextract_or_carry

        prev = SignalHistory(
            id=_uuid.uuid4(),
            signal_id="z",
            score=99.0,
            evidence_grade="observed",
            evidence_basis="prev",
        )
        out = _reextract_or_carry(
            MagicMock(),
            signal_id="nonexistent_signal_xyz",
            entity_id="e",
            prev_hist=prev,
        )
        # Inference fn missing -> returns the previous row unchanged.
        assert out is prev


# ---------------------------------------------------------------------------
# Gap 1 — Primary write path
# ---------------------------------------------------------------------------

class TestPrimaryWritePath:
    @pytest.mark.asyncio
    async def test_persist_quote_creates_mv_when_missing(self):
        """When no ModelVersion exists for the submission, _persist_quote
        creates one from the workflow_result."""
        from infrastructure.api.routes import submissions as subs_mod
        from layers.risk.types import WorkflowResult

        # Build a workflow_result with V7 fields.
        wr = WorkflowResult(
            entity_id="acme",
            coverage="cyber",
            composite_score=80.0,
            tier=2,
            tier_label="STANDARD",
            confidence=0.9,
            composite_min_grade="observed",
            composite_grade_distribution={"observed": 0.5, "structured_attested": 0.5},
        )

        # Fake session + repos.
        mv_id = _uuid.uuid4()
        sub = MagicMock(id=_uuid.uuid4(), code="sub-1")
        sub_repo_inst = MagicMock(get_by_code=AsyncMock(return_value=sub))
        mv_repo_inst = MagicMock(
            get_latest=AsyncMock(return_value=None),
            create=AsyncMock(return_value=MagicMock(id=mv_id)),
        )
        mvs_repo_inst = MagicMock(bulk_record=AsyncMock(return_value=[]))
        quote_inst = MagicMock(id=_uuid.uuid4())
        quote_repo_inst = MagicMock(create=AsyncMock(return_value=quote_inst))
        session = MagicMock()
        session.commit = AsyncMock()
        session.close = AsyncMock()
        # No referrals exist on this quote.
        execute_result = MagicMock()
        execute_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=execute_result)

        with patch.object(subs_mod, "_db_available", return_value=True), \
             patch.object(subs_mod, "_get_db_session", AsyncMock(return_value=session)), \
             patch("infrastructure.db.repositories.SubmissionRepository",
                   return_value=sub_repo_inst), \
             patch("infrastructure.db.repositories.ModelVersionRepository",
                   return_value=mv_repo_inst), \
             patch("infrastructure.db.repositories.ModelVersionSignalRepository",
                   return_value=mvs_repo_inst), \
             patch("infrastructure.db.repositories.QuoteRepository",
                   return_value=quote_repo_inst):
            await subs_mod._persist_quote(
                "quo-1",
                {"submission_code": "sub-1", "recommended_premium": 1000, "recommended_limit": 100000},
                workflow_result=wr,
            )

        # mv_repo.create was called with V7 kwargs.
        mv_repo_inst.create.assert_awaited_once()
        kw = mv_repo_inst.create.await_args.kwargs
        assert kw["composite_min_grade"] == "observed"
        assert kw["coverage"] == "cyber"
        # Quote was created referencing the new MV.
        quote_repo_inst.create.assert_awaited_once()
        assert quote_repo_inst.create.await_args.kwargs["model_version_id"] == mv_id
        session.commit.assert_awaited()

    @pytest.mark.asyncio
    async def test_persist_quote_skips_mv_create_when_no_workflow_result(self):
        """Backward compat: pre-V7 callers (no workflow_result) still
        fall through to the existing path."""
        from infrastructure.api.routes import submissions as subs_mod

        sub = MagicMock(id=_uuid.uuid4())
        sub_repo_inst = MagicMock(get_by_code=AsyncMock(return_value=sub))
        mv_repo_inst = MagicMock(get_latest=AsyncMock(return_value=None))
        session = MagicMock(commit=AsyncMock(), close=AsyncMock())

        with patch.object(subs_mod, "_db_available", return_value=True), \
             patch.object(subs_mod, "_get_db_session", AsyncMock(return_value=session)), \
             patch("infrastructure.db.repositories.SubmissionRepository",
                   return_value=sub_repo_inst), \
             patch("infrastructure.db.repositories.ModelVersionRepository",
                   return_value=mv_repo_inst):
            await subs_mod._persist_quote(
                "quo-1",
                {"submission_code": "sub-1", "recommended_premium": 0},
                workflow_result=None,
            )

        # No mv_repo.create was attempted.
        mv_repo_inst.create.assert_not_called()


# ---------------------------------------------------------------------------
# Gap 5 — beat schedule registration
# ---------------------------------------------------------------------------

class TestBeatScheduleWired:
    def test_v7_tasks_in_celery_app_include(self):
        from infrastructure.workers.celery_app import celery_app
        includes = celery_app.conf.include or []
        assert "infrastructure.workers.v7_tasks" in includes

    def test_v7_beat_schedule_entries_registered(self):
        from infrastructure.workers.celery_app import celery_app
        bs = dict(celery_app.conf.beat_schedule or {})
        assert "v7-dispatch-due-events" in bs
        assert "v7-refresh-stability-matview" in bs
        assert "v7-prune-mechanism-memory" in bs

    def test_v7_dispatch_runs_every_30s(self):
        from infrastructure.workers.celery_app import celery_app
        bs = dict(celery_app.conf.beat_schedule or {})
        assert bs["v7-dispatch-due-events"]["schedule"] == 30.0
