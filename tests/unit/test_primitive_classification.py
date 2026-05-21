"""V7 Phase 9 — risk-primitive classification cascade + rollups."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from signal_architecture.signals.primitive_classification import (
    PRIMITIVES,
    classify,
    llm_fallback,
)


# ---------------------------------------------------------------------------
# Cascade ordering
# ---------------------------------------------------------------------------

class TestCascade:
    def test_yaml_override_wins(self):
        # YAML override beats the prefix map: sanctions_ would map to
        # 'regulatory', but the override forces 'crime'.
        result = classify(
            signal_id="sanctions_screening",
            coverage="aerospace",
            yaml_override="crime",
        )
        assert result == "crime"

    def test_invalid_yaml_override_ignored(self):
        # A junk override falls through to the prefix map.
        result = classify(
            signal_id="sanctions_screening",
            coverage="aerospace",
            yaml_override="not_a_primitive",
        )
        assert result == "regulatory"

    def test_prefix_map_beats_coverage_default(self):
        # 'sec_filing_recency' -> financial via prefix, even though the
        # cyber coverage default is 'cyber'.
        result = classify(signal_id="sec_filing_recency", coverage="cyber")
        assert result == "financial"

    def test_coverage_default_when_no_prefix_match(self):
        result = classify(signal_id="some_bespoke_signal", coverage="fi")
        assert result == "financial"

    def test_unknown_when_nothing_resolves(self):
        result = classify(signal_id="mystery_signal", coverage="nonexistent_cov")
        assert result == "unknown"


# ---------------------------------------------------------------------------
# Prefix map coverage — representative cases per primitive
# ---------------------------------------------------------------------------

class TestPrefixMap:
    @pytest.mark.parametrize("signal_id,expected", [
        ("sanctions_screening_result", "regulatory"),
        ("pep_match", "regulatory"),
        ("license_status", "regulatory"),
        ("director_litigation_history", "governance"),
        ("officer_tenure", "governance"),
        ("board_independence", "governance"),
        ("sec_filing_recency", "financial"),
        ("credit_rating_band", "financial"),
        ("leverage_ratio", "financial"),
        ("security_headers", "cyber"),
        ("vuln_density", "cyber"),
        ("breach_history_routed", "cyber"),
        ("tls_config", "cyber"),
        ("patch_cadence", "behavioural"),
        ("cert_rotation_history", "behavioural"),
        ("hiring_velocity", "human_capital"),
        ("workforce_size", "human_capital"),
        ("flood_zone", "climate"),
        ("wildfire_exposure", "climate"),
        ("crime_index", "crime"),
        ("aml_program_maturity", "crime"),
        ("tiv_concentration", "physical_asset"),
        ("fleet_age", "physical_asset"),
        ("alliance_membership", "counterparty"),
        ("supply_chain_resilience", "operational"),
        ("sentiment_30d", "reputational"),
        ("esg_score", "reputational"),
    ])
    def test_prefix_maps(self, signal_id, expected):
        # Use a coverage with no default so only the prefix map can resolve.
        assert classify(signal_id=signal_id, coverage="zzz_no_default") == expected

    def test_director_litigation_more_specific_than_director(self):
        # 'director_litigation' must be listed before the bare 'director_'
        # prefix — both map to 'governance' here, but the ordering invariant
        # matters when they'd differ. Confirm the specific prefix resolves.
        assert classify(signal_id="director_litigation_history", coverage="x") == "governance"


# ---------------------------------------------------------------------------
# LLM fallback (level 4)
# ---------------------------------------------------------------------------

class TestLLMFallback:
    def test_returns_valid_primitive(self):
        llm = MagicMock(return_value="  Cyber  ")  # whitespace + case
        result = llm_fallback(
            llm, signal_id="x", coverage="cyber", evidence_basis="b",
        )
        assert result == "cyber"

    def test_junk_response_returns_unknown(self):
        llm = MagicMock(return_value="banana")
        result = llm_fallback(
            llm, signal_id="x", coverage="cyber", evidence_basis="b",
        )
        assert result == "unknown"

    def test_llm_exception_returns_unknown(self):
        def boom(*, system, user):
            raise RuntimeError("network down")
        result = llm_fallback(
            boom, signal_id="x", coverage="cyber", evidence_basis="b",
        )
        assert result == "unknown"

    def test_empty_response_returns_unknown(self):
        llm = MagicMock(return_value="")
        result = llm_fallback(
            llm, signal_id="x", coverage="cyber", evidence_basis="b",
        )
        assert result == "unknown"


# ---------------------------------------------------------------------------
# Scorer integration: _build_primitive_rollups
# ---------------------------------------------------------------------------

class TestPrimitiveRollups:
    def test_buckets_by_primitive(self):
        from layers.risk.scorer import ModelScorer
        from layers.risk.types import SignalOutput

        def _so(sid, primitive, grade, weight=0.5):
            return SignalOutput(
                signal_id=sid, signal_name=sid, group_id="g",
                raw_score=50.0, confidence=1.0,
                weighted_score=25.0, weight=weight,
                evidence_grade=grade, evidence_basis="b" if grade else None,
                primitive_type=primitive,
            )

        scorer = ModelScorer()
        outs = [
            _so("a", "cyber", "observed"),
            _so("b", "cyber", "structured_attested"),
            _so("c", "financial", "inferred"),
        ]
        rollups = scorer._build_primitive_rollups(outs)
        assert set(rollups.keys()) == {"cyber", "financial"}
        assert rollups["cyber"].group_id == "primitive::cyber"
        # cyber min grade is the lower of observed / structured_attested
        assert rollups["cyber"].min_grade == "observed"
        assert rollups["financial"].min_grade == "inferred"

    def test_ungraded_primitive_excluded(self):
        from layers.risk.scorer import ModelScorer
        from layers.risk.types import SignalOutput

        scorer = ModelScorer()
        outs = [
            SignalOutput(
                signal_id="a", signal_name="a", group_id="g",
                raw_score=50.0, confidence=1.0, weighted_score=25.0, weight=0.5,
                evidence_grade=None, primitive_type="cyber",
            ),
        ]
        rollups = scorer._build_primitive_rollups(outs)
        # The single signal has no grade -> empty rollup -> excluded.
        assert rollups == {}

    def test_none_primitive_bucketed_as_unknown(self):
        from layers.risk.scorer import ModelScorer
        from layers.risk.types import SignalOutput

        scorer = ModelScorer()
        outs = [
            SignalOutput(
                signal_id="a", signal_name="a", group_id="g",
                raw_score=50.0, confidence=1.0, weighted_score=25.0, weight=0.5,
                evidence_grade="observed", evidence_basis="b",
                primitive_type=None,
            ),
        ]
        rollups = scorer._build_primitive_rollups(outs)
        assert "unknown" in rollups


# ---------------------------------------------------------------------------
# Alembic 027 shape
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/027_primitive_type.py")


def _load_027():
    spec = importlib.util.spec_from_file_location("_v7_027", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic027:
    def test_revision_lineage(self):
        mod = _load_027()
        assert mod.revision == "027"
        assert mod.down_revision == "026"

    def test_adds_primitive_columns(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "primitive_type" in text
        assert "model_version_signals" in text
        assert "signal_history" in text

    def test_in_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("027")
        assert rev is not None
        assert rev.down_revision == "026"


class TestPrimitivesList:
    def test_twelve_plus_unknown(self):
        # 12 real primitives + 'unknown' sentinel
        assert len(PRIMITIVES) == 13
        assert "unknown" in PRIMITIVES
