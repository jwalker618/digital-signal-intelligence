"""v8 Phase 2 — verify alembic 031 is well-formed."""
from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION = Path("alembic/versions/031_v8_peer_cohort.py")


def _load():
    spec = importlib.util.spec_from_file_location("_v8_031", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestRevisionLineage:
    def test_revision_id(self):
        mod = _load()
        assert mod.revision == "031"

    def test_parents_030(self):
        mod = _load()
        assert mod.down_revision == "030"

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


class TestSchemaText:
    """Migration text references the expected schema names."""

    def test_creates_cohort_membership(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "cohort_membership" in text
        assert "create_table" in text

    def test_adds_peer_cohort_columns_to_model_versions(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "peer_cohort_id" in text
        assert "peer_cohort_size" in text
        assert "peer_percentile_rank" in text
        assert "peer_cohort_mean_score" in text
        assert "peer_cohort_median_score" in text

    def test_cohort_membership_has_unique_constraint(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "UniqueConstraint" in text
        # The unique key is (entity_key, coverage)
        assert "entity_key" in text
        assert "coverage" in text

    def test_cohort_id_index_for_fast_percentile(self):
        text = MIGRATION.read_text(encoding="utf-8")
        # The (cohort_id, composite_score) index powers percentile lookups
        assert "ix_cohort_membership_cohort" in text
        assert "composite_score" in text

    def test_model_version_fk_is_set_null(self):
        # cohort_membership keeps row when model_version is deleted;
        # the entity-coverage row should survive history pruning.
        text = MIGRATION.read_text(encoding="utf-8")
        assert "SET NULL" in text


class TestDowngrade:
    def test_drops_cohort_membership(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert 'drop_table("cohort_membership")' in text

    def test_drops_all_peer_cohort_columns(self):
        text = MIGRATION.read_text(encoding="utf-8")
        for col in (
            "peer_cohort_id",
            "peer_cohort_size",
            "peer_percentile_rank",
            "peer_cohort_mean_score",
            "peer_cohort_median_score",
        ):
            assert f'drop_column("model_versions", "{col}")' in text


class TestAlembic031InChain:
    def test_031_present_with_correct_parent(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("031")
        assert rev is not None
        assert rev.down_revision == "030"


class TestCohortMembershipModel:
    """The CohortMembership SQLAlchemy model is wired correctly."""

    def test_cohort_membership_importable(self):
        from infrastructure.db.models import CohortMembership
        assert CohortMembership.__tablename__ == "cohort_membership"

    def test_required_columns(self):
        from infrastructure.db.models import CohortMembership
        cols = {c.name for c in CohortMembership.__table__.columns}
        assert {
            "entity_key",
            "coverage",
            "cohort_id",
            "composite_score",
            "naics_section",
            "revenue_band",
            "model_version_id",
            "last_assessed_at",
        }.issubset(cols)

    def test_model_versions_has_peer_cohort_columns(self):
        from infrastructure.db.models import ModelVersionRecord
        cols = {c.name for c in ModelVersionRecord.__table__.columns}
        assert {
            "peer_cohort_id",
            "peer_cohort_size",
            "peer_percentile_rank",
            "peer_cohort_mean_score",
            "peer_cohort_median_score",
        }.issubset(cols)
