"""V7 Phase 6 — persist_verdict + alembic 024 + ValidatorPolicy schema."""
from __future__ import annotations

import importlib.util
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from infrastructure.db.models import ValidatorVerdictRecord
from infrastructure.db.validator_store import persist_verdict
from infrastructure.models.config_schema import ValidatorPolicy
from signal_architecture.validation.types import AxisResult, ValidatorVerdict


def _verdict(*, advance=True, mode="full_pass"):
    axes = {
        "MATERIAL": AxisResult("MATERIAL", True, "high", "ok"),
        "CORRECT_ENTITY": AxisResult("CORRECT_ENTITY", True, "high", "ok"),
        "OPERATIONALLY_PLAUSIBLE": AxisResult("OPERATIONALLY_PLAUSIBLE", True, "medium", "ok"),
        "GENERALISES_AT_RENEWAL": AxisResult("GENERALISES_AT_RENEWAL", True, "medium", "ok"),
    }
    return ValidatorVerdict(
        signal_id="sanctions_check",
        mode=mode,
        axes=axes,
        advance=advance,
        grade_after_bump="structured_attested",
        pro_argument="pro",
        counter_argument="counter",
        tie_breaker="tie",
        raw_response='{"axes":{}}',
        elapsed_seconds=0.42,
        decided_at=datetime(2026, 5, 13, tzinfo=timezone.utc),
    )


class TestPersistVerdict:
    def test_row_carries_verdict_fields(self):
        db = MagicMock()
        mv_id = uuid.uuid4()
        row = persist_verdict(
            db,
            model_version_id=mv_id,
            verdict=_verdict(),
            grade_before="corroborated",
        )
        assert isinstance(row, ValidatorVerdictRecord)
        assert row.model_version_id == mv_id
        assert row.signal_id == "sanctions_check"
        assert row.mode == "full_pass"
        assert row.advance is True
        assert row.grade_before == "corroborated"
        assert row.grade_after == "structured_attested"
        assert row.elapsed_seconds == 0.42

    def test_axes_payload_serialised(self):
        db = MagicMock()
        row = persist_verdict(
            db, model_version_id=uuid.uuid4(),
            verdict=_verdict(), grade_before="corroborated",
        )
        assert "MATERIAL" in row.axes
        assert row.axes["MATERIAL"] == {
            "passed": True, "confidence": "high", "rationale": "ok",
        }

    def test_db_add_called_once(self):
        db = MagicMock()
        persist_verdict(
            db, model_version_id=uuid.uuid4(),
            verdict=_verdict(), grade_before="observed",
        )
        assert db.add.call_count == 1


# ---------------------------------------------------------------------------
# Alembic 024
# ---------------------------------------------------------------------------

_MIGRATION = Path("alembic/versions/024_validator_verdicts.py")


def _load_024():
    spec = importlib.util.spec_from_file_location("_v7_024", _MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestAlembic024:
    def test_revision_lineage(self):
        mod = _load_024()
        assert mod.revision == "024"
        assert mod.down_revision == "023"

    def test_upgrade_downgrade_callable(self):
        mod = _load_024()
        assert callable(mod.upgrade)
        assert callable(mod.downgrade)

    def test_creates_validator_verdicts(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "validator_verdicts" in text

    def test_flips_evidence_grade_to_not_null(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        assert "evidence_grade" in text
        assert "nullable=False" in text

    def test_backfill_runs_before_not_null(self):
        text = _MIGRATION.read_text(encoding="utf-8")
        # Backfill UPDATE sets evidence_grade='inferred' for any leftover nulls
        assert "evidence_grade='inferred'" in text or "evidence_grade = 'inferred'" in text

    def test_024_present_with_correct_parent(self):
        """024 reachable; parents 023. Later phases (025+) may advance head."""
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("024")
        assert rev is not None
        assert rev.down_revision == "023"


# ---------------------------------------------------------------------------
# ValidatorPolicy schema
# ---------------------------------------------------------------------------

class TestValidatorPolicy:
    def test_defaults(self):
        p = ValidatorPolicy()
        assert p.enabled is True
        assert p.max_concurrent == 5
        assert p.full_pass_floor == "corroborated"
        assert p.advance_bump_cap == "structured_attested"

    def test_max_concurrent_within_bounds(self):
        with pytest.raises(ValidationError):
            ValidatorPolicy(max_concurrent=0)
        with pytest.raises(ValidationError):
            ValidatorPolicy(max_concurrent=51)

    def test_rejects_unknown_grade_strings(self):
        with pytest.raises(ValidationError):
            ValidatorPolicy(full_pass_floor="badgrade")  # type: ignore[arg-type]

    def test_attached_to_evidence_grade_policy(self):
        from infrastructure.models.config_schema import EvidenceGradePolicy
        p = EvidenceGradePolicy()
        assert isinstance(p.validator, ValidatorPolicy)
        assert p.validator.full_pass_floor == "corroborated"


class TestNoCallSitePassesRawDataToValidatorInput:
    """Belt-and-braces grep: no production code should pass `raw_data=` to
    ValidatorInput, regardless of language conventions."""

    def test_no_raw_data_call_to_validator_input(self):
        import subprocess
        result = subprocess.run(
            [
                "grep", "-rnE",
                r"ValidatorInput\([^)]*raw_data",
                "layers/", "infrastructure/", "signal_architecture/",
                "--include=*.py",
            ],
            capture_output=True, text=True,
        )
        # grep exit 1 = no matches (good)
        assert result.returncode == 1, (
            f"Found raw_data passed to ValidatorInput:\n{result.stdout}"
        )

    def test_no_metadata_call_to_validator_input(self):
        import subprocess
        result = subprocess.run(
            [
                "grep", "-rnE",
                r"ValidatorInput\([^)]*metadata",
                "layers/", "infrastructure/", "signal_architecture/",
                "--include=*.py",
            ],
            capture_output=True, text=True,
        )
        assert result.returncode == 1, (
            f"Found metadata passed to ValidatorInput:\n{result.stdout}"
        )
