"""V7 Phase 5 — verify alembic 023 is well-formed.

A live DB roundtrip isn't possible in CI without postgres; this test
asserts the migration module loads, has upgrade/downgrade functions,
and declares the right revision lineage.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION = Path("alembic/versions/023_evidence_grade.py")


def _load():
    spec = importlib.util.spec_from_file_location("_v7_023", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestRevisionLineage:
    def test_revision_id(self):
        mod = _load()
        assert mod.revision == "023"

    def test_parents_022(self):
        mod = _load()
        assert mod.down_revision == "022"

    def test_branch_labels_none(self):
        mod = _load()
        assert mod.branch_labels is None
        assert mod.depends_on is None


class TestUpgradeDowngradeShape:
    def test_upgrade_callable(self):
        mod = _load()
        assert callable(mod.upgrade)

    def test_downgrade_callable(self):
        mod = _load()
        assert callable(mod.downgrade)


class TestKnownTablesAndColumns:
    """Migration text references the expected schema names."""

    def test_creates_signal_history(self):
        assert "signal_history" in MIGRATION.read_text(encoding="utf-8")

    def test_creates_signal_commitments(self):
        assert "signal_commitments" in MIGRATION.read_text(encoding="utf-8")

    def test_creates_compliance_audit_logs(self):
        assert "compliance_audit_logs" in MIGRATION.read_text(encoding="utf-8")

    def test_adds_evidence_grade_to_mvs(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "model_version_signals" in text
        assert "evidence_grade" in text

    def test_adds_composite_columns_to_mv(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "composite_min_grade" in text
        assert "composite_grade_distribution" in text


class TestAlembicHeadIs023:
    def test_head_revision_is_023(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        head = sd.get_current_head()
        assert head == "023"
