"""V7 Phase 11 — variant-loop trigger predicate, prompt, orchestrator."""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from signal_architecture.signals.types import SignalResult
from signal_architecture.variants import (
    VARIANT_KINDS,
    VariantQuery,
    generate_variants_for,
    is_trigger,
    run_variant_loop,
    select_triggers,
)


def _sig(
    sid="parent",
    grade="structured_attested",
    cluster_id="C1",
    deterministic=True,
    variant_of=None,
):
    md = {"cluster_id": cluster_id} if cluster_id else {}
    if deterministic is not None and cluster_id:
        md["deterministic"] = deterministic
    return SignalResult(
        signal_id=sid,
        score=80.0,
        confidence=0.85,
        evidence_grade=grade,
        evidence_basis="b",
        metadata=md,
        variant_of=variant_of,
    )


# ---------------------------------------------------------------------------
# is_trigger
# ---------------------------------------------------------------------------

class TestTriggerPredicate:
    def test_happy_path_advances(self):
        assert is_trigger(_sig(), validator_advanced=True) is True

    def test_below_grade_floor_does_not_trigger(self):
        assert is_trigger(_sig(grade="corroborated"), validator_advanced=True) is False
        assert is_trigger(_sig(grade="observed"), validator_advanced=True) is False
        assert is_trigger(_sig(grade="inferred"), validator_advanced=True) is False

    def test_behaviourally_validated_also_triggers(self):
        assert is_trigger(
            _sig(grade="behaviourally_validated"), validator_advanced=True,
        ) is True

    def test_not_advanced_blocks(self):
        assert is_trigger(_sig(), validator_advanced=False) is False
        assert is_trigger(_sig(), validator_advanced=None) is False

    def test_no_cluster_blocks(self):
        assert is_trigger(_sig(cluster_id=None), validator_advanced=True) is False

    def test_non_deterministic_cluster_blocks(self):
        assert is_trigger(
            _sig(deterministic=False), validator_advanced=True,
        ) is False

    def test_already_variant_blocks_second_hop(self):
        child = _sig(variant_of="some_parent")
        assert is_trigger(child, validator_advanced=True) is False


# ---------------------------------------------------------------------------
# select_triggers
# ---------------------------------------------------------------------------

class TestSelectTriggers:
    def test_picks_only_qualifying_signals(self):
        signals = [
            _sig(sid="a"),                              # qualifies
            _sig(sid="b", grade="observed"),            # below floor
            _sig(sid="c", cluster_id=None),             # no cluster
            _sig(sid="d", variant_of="x"),              # already variant
        ]
        verdicts = {s.signal_id: True for s in signals}  # all advanced
        triggers = select_triggers(signals, verdicts)
        assert [t.signal_id for t in triggers] == ["a"]

    def test_missing_verdict_treated_as_not_advanced(self):
        signals = [_sig(sid="a"), _sig(sid="b")]
        verdicts = {"a": True}  # b has no verdict
        triggers = select_triggers(signals, verdicts)
        assert [t.signal_id for t in triggers] == ["a"]

    def test_accepts_verdict_object_with_advance_attr(self):
        class V:
            def __init__(self, advance):
                self.advance = advance
        signals = [_sig(sid="a"), _sig(sid="b")]
        verdicts = {"a": V(True), "b": V(False)}
        triggers = select_triggers(signals, verdicts)
        assert [t.signal_id for t in triggers] == ["a"]


# ---------------------------------------------------------------------------
# generate_variants_for
# ---------------------------------------------------------------------------

def _llm_returning(payload: dict):
    return MagicMock(return_value=json.dumps(payload))


class TestPromptParsing:
    def test_returns_well_formed_queries(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "Acme Inc",
                 "rationale": "alternate spelling"},
                {"kind": "subsidiary", "target_ref": "Acme Holdings GmbH",
                 "rationale": "known sub"},
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert len(out) == 2
        assert out[0].kind == "name_variant"
        assert out[0].parent_signal_id == "parent"
        assert out[0].parent_cluster_id == "C1"

    def test_max_n_caps_output(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": f"alt_{i}",
                 "rationale": "r"} for i in range(10)
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=3)
        assert len(out) == 3

    def test_unknown_kind_dropped(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "made_up", "target_ref": "x", "rationale": "r"},
                {"kind": "name_variant", "target_ref": "y", "rationale": "r"},
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert [q.kind for q in out] == ["name_variant"]

    def test_empty_target_ref_dropped(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "", "rationale": "r"},
                {"kind": "name_variant", "target_ref": "y", "rationale": "r"},
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert [q.target_ref for q in out] == ["y"]

    def test_dedups_kind_plus_target(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "Acme", "rationale": "r"},
                {"kind": "name_variant", "target_ref": "Acme", "rationale": "r"},
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert len(out) == 1

    def test_no_cluster_no_variants(self):
        # Variants require a parent cluster_id.
        llm = _llm_returning({"variants": [
            {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
        ]})
        out = generate_variants_for(llm, _sig(cluster_id=None), max_n=5)
        assert out == []

    def test_llm_exception_returns_empty(self):
        def boom(*, system, user):
            raise RuntimeError("network")
        out = generate_variants_for(boom, _sig(), max_n=5)
        assert out == []

    def test_unparseable_json_returns_empty(self):
        llm = MagicMock(return_value="this is not json")
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert out == []

    def test_rationale_truncated_to_200_chars(self):
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "z" * 500},
            ],
        })
        out = generate_variants_for(llm, _sig(), max_n=5)
        assert len(out[0].rationale) == 200


# ---------------------------------------------------------------------------
# run_variant_loop
# ---------------------------------------------------------------------------

def _query(parent="parent", kind="name_variant", target="X", cluster="C1"):
    return VariantQuery(
        kind=kind, target_ref=target, rationale="r",
        parent_signal_id=parent, parent_cluster_id=cluster,
    )


def _produced_child(sid):
    return SignalResult(
        signal_id=sid, score=70.0, confidence=0.7,
        evidence_grade="observed", evidence_basis="b",
    )


class TestRunLoop:
    def test_per_trigger_cap(self):
        triggers = [_sig()]
        # LLM offers 7; max_per_trigger=2 -> only 2 queries built.
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": f"t{i}", "rationale": "r"}
                for i in range(7)
            ],
        })
        produced_ids = iter(["child_1", "child_2"])
        ex = MagicMock(side_effect=lambda q: _produced_child(next(produced_ids)))
        new_signals, results = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex,
            max_per_trigger=2, max_per_entity_per_cycle=100,
        )
        assert len(results) == 2
        assert len(new_signals) == 2

    def test_per_entity_cap_binds(self):
        triggers = [_sig(sid=f"p{i}", cluster_id=f"C{i}") for i in range(10)]
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
            ],
        })
        ex = MagicMock(return_value=_produced_child("child"))
        new_signals, results = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex,
            max_per_trigger=5, max_per_entity_per_cycle=3,
        )
        # Per-entity cap binds before per-trigger.
        assert len(results) == 3

    def test_variant_of_tagged_on_child(self):
        triggers = [_sig(sid="parent")]
        llm = _llm_returning({
            "variants": [
                {"kind": "subsidiary", "target_ref": "subco", "rationale": "r"},
            ],
        })
        ex = MagicMock(return_value=_produced_child("child_a"))
        new_signals, _ = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex,
        )
        assert new_signals[0].variant_of == "parent"
        assert new_signals[0].metadata["variant_kind"] == "subsidiary"
        assert new_signals[0].metadata["variant_target_ref"] == "subco"
        assert new_signals[0].metadata["variant_parent_cluster_id"] == "C1"

    def test_child_cannot_spawn_grandchild(self):
        """The child SignalResult carries variant_of -> is_trigger returns
        False on it. Single-hop is provable from data without runtime
        state."""
        triggers = [_sig(sid="parent")]
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
            ],
        })
        ex = MagicMock(return_value=_produced_child("child"))
        new_signals, _ = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex,
        )
        child = new_signals[0]
        # Even if we lie and claim it's structured_attested + advanced,
        # is_trigger refuses because variant_of is set.
        child.evidence_grade = "structured_attested"
        child.metadata = {**(child.metadata or {}), "cluster_id": "C2"}
        assert is_trigger(child, validator_advanced=True) is False

    def test_no_op_when_extractor_returns_none(self):
        triggers = [_sig()]
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
            ],
        })
        ex = MagicMock(return_value=None)
        new_signals, results = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex,
        )
        assert new_signals == []
        assert results[0].success is False
        assert results[0].note == "no_result"

    def test_extractor_exception_recorded_as_no_op(self):
        triggers = [_sig()]
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
            ],
        })
        def boom(q):
            raise RuntimeError("oops")
        new_signals, results = run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=boom,
        )
        assert new_signals == []
        assert results[0].success is False
        assert "error" in results[0].note

    def test_audit_callback_invoked(self):
        triggers = [_sig()]
        llm = _llm_returning({
            "variants": [
                {"kind": "name_variant", "target_ref": "x", "rationale": "r"},
                {"kind": "subsidiary", "target_ref": "y", "rationale": "r"},
            ],
        })
        produced = iter([_produced_child("child_a"), None])
        ex = MagicMock(side_effect=lambda q: next(produced))
        events = []
        audit = lambda et, sid, p: events.append((et, sid, p))
        run_variant_loop(
            triggers, llm_callable=llm, extract_for_variant=ex, audit=audit,
        )
        event_types = [e[0] for e in events]
        assert "variant_generated" in event_types
        assert "variant_extracted" in event_types
        assert "variant_no_op" in event_types


class TestPolicyDefaults:
    def test_policy_block_default_loads(self):
        from infrastructure.models.config_schema import VariantLoopPolicy
        p = VariantLoopPolicy()
        assert p.enabled is True
        assert p.max_per_trigger == 5
        assert p.max_per_entity_per_cycle == 25

    def test_policy_field_validation(self):
        from pydantic import ValidationError
        from infrastructure.models.config_schema import VariantLoopPolicy
        with pytest.raises(ValidationError):
            VariantLoopPolicy(max_per_trigger=-1)
        with pytest.raises(ValidationError):
            VariantLoopPolicy(max_per_entity_per_cycle=999)

    def test_attached_to_evidence_grade_policy(self):
        from infrastructure.models.config_schema import (
            EvidenceGradePolicy, VariantLoopPolicy,
        )
        p = EvidenceGradePolicy()
        assert isinstance(p.variant_loop, VariantLoopPolicy)


class TestSignalResultVariantOfField:
    def test_default_none(self):
        sig = SignalResult(signal_id="x")
        assert sig.variant_of is None

    def test_accepts_parent_signal_id(self):
        sig = SignalResult(signal_id="child", variant_of="parent")
        assert sig.variant_of == "parent"
