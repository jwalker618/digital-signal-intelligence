"""V7 Phase 7 — grade_calibration_store tests (mock + in-memory list).

We mock SQLAlchemy Session calls because the project's DB is postgres-only.
Logic-heavy tests (sampler picks, match flag computation, drift threshold)
run without a DB; behaviour-heavy paths (persist_samples idempotency,
expire_old) verify session.add/.update interactions.
"""
from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import MagicMock, PropertyMock

import pytest

from infrastructure.db.grade_calibration_store import (
    CalibrationStats,
    is_drifted,
    persist_samples,
    record_human_verdict,
    stats,
)
from infrastructure.db.models import (
    GradeCalibrationDecision,
    GradeCalibrationSample,
)
from signal_architecture.validation.sampler import (
    SamplingCandidate,
    SamplingTarget,
)


def _target(sid="x", grade="observed"):
    c = SamplingCandidate(
        submission_id=uuid.UUID(int=1),
        model_version_id=uuid.UUID(int=2),
        coverage="cyber",
        signal_id=sid,
        signal_weight=0.2,
        extractor_grade=grade,
        validator_grade=None,
    )
    return SamplingTarget(candidate=c, reason="stratified_random")


class TestPersistSamples:
    def test_inserts_when_absent(self):
        db = MagicMock()
        db.query.return_value.filter_by.return_value.one_or_none.return_value = None
        mv = uuid.UUID(int=99)
        sub = uuid.UUID(int=98)
        n = persist_samples(db, [_target("a"), _target("b")], mv_id=mv, submission_id=sub)
        assert n == 2
        assert db.add.call_count == 2
        for call in db.add.call_args_list:
            row = call[0][0]
            assert isinstance(row, GradeCalibrationSample)
            assert row.model_version_id == mv
            assert row.submission_id == sub
            assert row.state == "pending" or row.state is None  # default applied

    def test_skips_when_already_present(self):
        existing = GradeCalibrationSample(signal_id="a")
        db = MagicMock()
        # First lookup returns existing; second returns None
        side_effects = [existing, None]
        db.query.return_value.filter_by.return_value.one_or_none.side_effect = side_effects
        n = persist_samples(
            db, [_target("a"), _target("b")],
            mv_id=uuid.UUID(int=1), submission_id=uuid.UUID(int=2),
        )
        assert n == 1
        assert db.add.call_count == 1


class TestRecordHumanVerdict:
    def test_exact_match_flag_set(self):
        sample = GradeCalibrationSample(
            id=uuid.UUID(int=1),
            extractor_grade="observed",
            validator_grade="observed",
            state="pending",
        )
        db = MagicMock()
        db.query.return_value.get.return_value = sample
        d = record_human_verdict(
            db, sample_id=sample.id,
            human_grade="observed",
            decided_by=uuid.UUID(int=99),
        )
        assert d.exact_match_extractor is True
        assert d.exact_match_validator is True
        assert d.within_one_extractor is True
        assert sample.state == "decided"

    def test_within_one_flag_set(self):
        sample = GradeCalibrationSample(
            id=uuid.UUID(int=1),
            extractor_grade="observed",
            validator_grade=None,
            state="pending",
        )
        db = MagicMock()
        db.query.return_value.get.return_value = sample
        d = record_human_verdict(
            db, sample_id=sample.id,
            human_grade="corroborated",  # 1 rung higher
            decided_by=uuid.UUID(int=99),
        )
        assert d.exact_match_extractor is False
        assert d.exact_match_validator is None
        assert d.within_one_extractor is True

    def test_outside_one_flag_set(self):
        sample = GradeCalibrationSample(
            id=uuid.UUID(int=1),
            extractor_grade="inferred",
            validator_grade=None,
            state="pending",
        )
        db = MagicMock()
        db.query.return_value.get.return_value = sample
        d = record_human_verdict(
            db, sample_id=sample.id,
            human_grade="structured_attested",  # 3 rungs higher
            decided_by=uuid.UUID(int=99),
        )
        assert d.within_one_extractor is False

    def test_missing_sample_raises(self):
        db = MagicMock()
        db.query.return_value.get.return_value = None
        with pytest.raises(LookupError):
            record_human_verdict(
                db, sample_id=uuid.UUID(int=1),
                human_grade="observed", decided_by=uuid.UUID(int=99),
            )

    def test_already_decided_raises(self):
        sample = GradeCalibrationSample(
            id=uuid.UUID(int=1), extractor_grade="observed",
            validator_grade=None, state="decided",
        )
        db = MagicMock()
        db.query.return_value.get.return_value = sample
        with pytest.raises(RuntimeError):
            record_human_verdict(
                db, sample_id=sample.id,
                human_grade="observed", decided_by=uuid.UUID(int=99),
            )


class TestStats:
    def _make_db_with_rows(self, rows):
        db = MagicMock()
        q = MagicMock()
        q.filter.return_value = q
        q.join.return_value = q
        q.all.return_value = rows
        db.query.return_value = q
        return db

    def test_empty_returns_zeros(self):
        s = stats(self._make_db_with_rows([]))
        assert s.decided == 0
        assert s.exact_match_extractor_rate == 0.0
        assert s.within_one_extractor_rate == 0.0
        assert s.exact_match_validator_rate is None

    def test_rate_math_correct(self):
        rows = [
            GradeCalibrationDecision(
                exact_match_extractor=True, exact_match_validator=True,
                within_one_extractor=True,
            ),
            GradeCalibrationDecision(
                exact_match_extractor=False, exact_match_validator=None,
                within_one_extractor=True,
            ),
            GradeCalibrationDecision(
                exact_match_extractor=True, exact_match_validator=False,
                within_one_extractor=True,
            ),
        ]
        s = stats(self._make_db_with_rows(rows))
        assert s.decided == 3
        assert s.exact_match_extractor_rate == pytest.approx(2 / 3)
        assert s.within_one_extractor_rate == pytest.approx(3 / 3)
        # 2 rows had a validator grade; 1 of those exact-matched -> 0.5
        assert s.exact_match_validator_rate == pytest.approx(0.5)


class TestIsDrifted:
    def test_drifted_when_below_threshold(self):
        s = CalibrationStats(
            window_days=30, decided=10,
            exact_match_extractor_rate=0.60,  # below 0.75
            exact_match_validator_rate=None,
            within_one_extractor_rate=0.90,
        )
        assert is_drifted(s) is True

    def test_not_drifted_at_threshold(self):
        s = CalibrationStats(
            window_days=30, decided=10,
            exact_match_extractor_rate=0.75,
            exact_match_validator_rate=None,
            within_one_extractor_rate=0.90,
        )
        assert is_drifted(s) is False

    def test_not_drifted_when_no_decisions(self):
        s = CalibrationStats(
            window_days=30, decided=0,
            exact_match_extractor_rate=0.0,
            exact_match_validator_rate=None,
            within_one_extractor_rate=0.0,
        )
        assert is_drifted(s) is False

    def test_not_drifted_for_lifetime_window(self):
        s = CalibrationStats(
            window_days=None, decided=10,
            exact_match_extractor_rate=0.60,
            exact_match_validator_rate=None,
            within_one_extractor_rate=0.90,
        )
        # Lifetime stat shouldn't fire drift; only rolling 30-day does.
        assert is_drifted(s) is False


# ---------------------------------------------------------------------------
# Alembic 025 shape
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/025_grade_calibration.py")


def _load_025():
    spec = importlib.util.spec_from_file_location("_v7_025", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic025:
    def test_revision_lineage(self):
        mod = _load_025()
        assert mod.revision == "025"
        assert mod.down_revision == "024"

    def test_creates_both_tables(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "grade_calibration_samples" in text
        assert "grade_calibration_decisions" in text

    def test_in_chain(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("025")
        assert rev is not None
        assert rev.down_revision == "024"
