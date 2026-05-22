"""v8 Phase 1 — verify alembic 030 is well-formed.

A live DB roundtrip isn't possible in CI without postgres; this test
asserts the migration module loads, has upgrade/downgrade functions,
declares the right revision lineage, and references the expected
schema names.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION = Path("alembic/versions/030_v8_broker_data_model.py")


def _load():
    spec = importlib.util.spec_from_file_location("_v8_030", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestRevisionLineage:
    def test_revision_id(self):
        mod = _load()
        assert mod.revision == "030"

    def test_parents_029(self):
        mod = _load()
        assert mod.down_revision == "029"

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

    def test_creates_brokers_table(self):
        assert "create_table" in MIGRATION.read_text(encoding="utf-8")
        assert '"brokers"' in MIGRATION.read_text(encoding="utf-8")

    def test_adds_broker_id_to_users(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert '"users"' in text
        assert '"broker_id"' in text

    def test_adds_broker_id_to_submissions(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert '"submissions"' in text
        # broker_id appears on both users and submissions
        assert text.count('"broker_id"') >= 2

    def test_brokers_has_tenant_fk(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "tenants.id" in text
        assert "CASCADE" in text  # brokers cascades on tenant delete

    def test_users_broker_fk_is_set_null(self):
        # Users keep their row when their broker is deleted
        text = MIGRATION.read_text(encoding="utf-8")
        assert "SET NULL" in text

    def test_seeds_broker_role(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "'BROKER'" in text
        assert "portal:broker:read" in text
        assert "portal:broker:reply" in text

    def test_seeds_client_role(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "'CLIENT'" in text
        assert "portal:client:read" in text
        assert "portal:client:submit" in text

    def test_seed_is_idempotent(self):
        # The INSERTs guard against re-running by checking NOT EXISTS
        text = MIGRATION.read_text(encoding="utf-8")
        assert "NOT EXISTS" in text


class TestDowngrade:
    def test_drops_brokers_table(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert 'drop_table("brokers")' in text

    def test_drops_broker_id_columns(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert 'drop_column("users", "broker_id")' in text
        assert 'drop_column("submissions", "broker_id")' in text

    def test_removes_seeded_portal_roles(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "DELETE FROM roles" in text
        assert "'BROKER'" in text
        assert "'CLIENT'" in text


class TestAlembic030InChain:
    """030 must exist in the revision chain and parent 029."""

    def test_030_present_with_correct_parent(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("030")
        assert rev is not None
        assert rev.down_revision == "029"
