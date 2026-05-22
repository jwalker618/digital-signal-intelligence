"""v8 Phase 5 -- verify alembic 032 is well-formed."""
from __future__ import annotations

import importlib.util
from pathlib import Path


MIGRATION = Path("alembic/versions/032_v8_referral_messages.py")


def _load():
    spec = importlib.util.spec_from_file_location("_v8_032", MIGRATION)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class TestRevisionLineage:
    def test_revision_id(self):
        assert _load().revision == "032"

    def test_parents_031(self):
        assert _load().down_revision == "031"

    def test_branch_labels_none(self):
        mod = _load()
        assert mod.branch_labels is None
        assert mod.depends_on is None


class TestUpgradeDowngradeShape:
    def test_upgrade_callable(self):
        assert callable(_load().upgrade)

    def test_downgrade_callable(self):
        assert callable(_load().downgrade)


class TestSchemaText:
    def test_adds_awaiting_broker_enum_value(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "ALTER TYPE referralstatus ADD VALUE" in text
        assert "awaiting_broker" in text

    def test_uses_idempotent_enum_add(self):
        # IF NOT EXISTS guards against re-run failure
        text = MIGRATION.read_text(encoding="utf-8")
        assert "IF NOT EXISTS" in text

    def test_uses_autocommit_block(self):
        # Postgres requires ALTER TYPE outside a transaction
        text = MIGRATION.read_text(encoding="utf-8")
        assert "autocommit_block" in text

    def test_adds_awaiting_party_to_referrals(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert '"referrals"' in text
        assert '"awaiting_party"' in text

    def test_creates_referral_messages(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert "create_table" in text
        assert '"referral_messages"' in text

    def test_referral_messages_has_required_columns(self):
        text = MIGRATION.read_text(encoding="utf-8")
        for col in (
            "referral_id",
            "direction",
            "author_user_id",
            "body",
            "signal_value_update",
            "triggered_reassessment",
            "new_quote_id",
            "request_signal_evidence",
        ):
            assert f'"{col}"' in text

    def test_cascade_on_referral_delete(self):
        text = MIGRATION.read_text(encoding="utf-8")
        # Messages cascade-delete with their referral
        assert "ondelete=" in text and "CASCADE" in text

    def test_author_fk_set_null(self):
        text = MIGRATION.read_text(encoding="utf-8")
        # Author and new_quote FKs SET NULL on delete -- audit history preserved
        assert "SET NULL" in text


class TestDowngrade:
    def test_drops_referral_messages(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert 'drop_table("referral_messages")' in text

    def test_drops_awaiting_party_column(self):
        text = MIGRATION.read_text(encoding="utf-8")
        assert 'drop_column("referrals", "awaiting_party")' in text


class TestAlembic032InChain:
    def test_032_present_with_correct_parent(self):
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        cfg = Config("alembic.ini")
        sd = ScriptDirectory.from_config(cfg)
        rev = sd.get_revision("032")
        assert rev is not None
        assert rev.down_revision == "031"


class TestModelsWiring:
    def test_referral_message_importable(self):
        from infrastructure.db.models import ReferralMessage
        assert ReferralMessage.__tablename__ == "referral_messages"

    def test_referral_message_columns(self):
        from infrastructure.db.models import ReferralMessage
        cols = {c.name for c in ReferralMessage.__table__.columns}
        assert {
            "referral_id",
            "direction",
            "author_user_id",
            "body",
            "signal_value_update",
            "triggered_reassessment",
            "new_quote_id",
            "request_signal_evidence",
        }.issubset(cols)

    def test_referral_has_messages_relationship(self):
        from infrastructure.db.models import Referral
        assert "messages" in Referral.__mapper__.relationships

    def test_referral_has_awaiting_party(self):
        from infrastructure.db.models import Referral
        cols = {c.name for c in Referral.__table__.columns}
        assert "awaiting_party" in cols

    def test_referral_status_has_awaiting_broker(self):
        from infrastructure.db.models import ReferralStatus
        assert ReferralStatus.AWAITING_BROKER.value == "awaiting_broker"

    def test_message_direction_enum(self):
        from infrastructure.db.models import MessageDirection
        assert MessageDirection.UNDERWRITER_TO_BROKER.value == "u2b"
        assert MessageDirection.BROKER_TO_UNDERWRITER.value == "b2u"
