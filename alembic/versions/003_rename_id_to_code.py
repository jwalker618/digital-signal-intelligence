"""Rename String(50) business code columns from _id to _code

Revision ID: 003
Revises: 002
Create Date: 2026-03-08

Changes:
- submissions: submission_id -> submission_code
- model_versions: version_id -> version_code, loss_cohort_id -> loss_cohort_code
- quotes: quote_id -> quote_code
- referrals: referral_id -> referral_code
- signal_cache: entity_id -> entity_code, signal_id -> signal_code
- model_version_signals: signal_id -> signal_code, entity_id -> entity_code, group_id -> group_code
- signal_audit_records: signal_id -> signal_code, entity_id -> entity_code
- audit_logs: resource_id -> resource_code

UUID foreign key columns (submission_id, quote_id, model_version_id, etc.) are NOT renamed.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003"
down_revision: str = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # submissions: submission_id -> submission_code (String(50) business code)
    # =========================================================================
    op.alter_column("submissions", "submission_id", new_column_name="submission_code")
    op.drop_index("ix_submissions_submission_id", "submissions")
    op.create_index("ix_submissions_submission_code", "submissions", ["submission_code"])

    # =========================================================================
    # model_versions: version_id -> version_code (String(50) business code)
    # =========================================================================
    op.alter_column("model_versions", "version_id", new_column_name="version_code")
    op.drop_index("ix_model_versions_version_id", "model_versions")
    op.create_index("ix_model_versions_version_code", "model_versions", ["version_code"])

    # model_versions: loss_cohort_id -> loss_cohort_code
    op.alter_column("model_versions", "loss_cohort_id", new_column_name="loss_cohort_code")

    # =========================================================================
    # quotes: quote_id -> quote_code (String(50) business code)
    # =========================================================================
    op.alter_column("quotes", "quote_id", new_column_name="quote_code")
    op.drop_index("ix_quotes_quote_id", "quotes")
    op.create_index("ix_quotes_quote_code", "quotes", ["quote_code"])

    # =========================================================================
    # referrals: referral_id -> referral_code (String(50) business code)
    # =========================================================================
    op.alter_column("referrals", "referral_id", new_column_name="referral_code")
    op.drop_index("ix_referrals_referral_id", "referrals")
    op.create_index("ix_referrals_referral_code", "referrals", ["referral_code"])

    # =========================================================================
    # signal_cache: entity_id -> entity_code, signal_id -> signal_code
    # =========================================================================
    op.alter_column("signal_cache", "entity_id", new_column_name="entity_code")
    op.alter_column("signal_cache", "signal_id", new_column_name="signal_code")
    op.drop_index("ix_signal_cache_lookup", "signal_cache")
    op.drop_index("ix_signal_cache_entity", "signal_cache")
    op.create_index("ix_signal_cache_lookup", "signal_cache", ["entity_code", "signal_code", "source_name"])
    op.create_index("ix_signal_cache_entity", "signal_cache", ["entity_code"])

    # =========================================================================
    # model_version_signals: signal_id -> signal_code, entity_id -> entity_code, group_id -> group_code
    # =========================================================================
    op.alter_column("model_version_signals", "signal_id", new_column_name="signal_code")
    op.alter_column("model_version_signals", "entity_id", new_column_name="entity_code")
    op.alter_column("model_version_signals", "group_id", new_column_name="group_code")
    op.drop_index("ix_mvs_lookup", "model_version_signals")
    op.create_index("ix_mvs_lookup", "model_version_signals", ["model_version_id", "signal_code"], unique=True)

    # =========================================================================
    # signal_audit_records: signal_id -> signal_code, entity_id -> entity_code
    # =========================================================================
    op.alter_column("signal_audit_records", "signal_id", new_column_name="signal_code")
    op.alter_column("signal_audit_records", "entity_id", new_column_name="entity_code")
    op.drop_index("ix_signal_audit_entity_signal", "signal_audit_records")
    op.create_index("ix_signal_audit_entity_signal", "signal_audit_records", ["entity_code", "signal_code"])

    # =========================================================================
    # audit_logs: resource_id -> resource_code
    # =========================================================================
    op.alter_column("audit_logs", "resource_id", new_column_name="resource_code")
    op.drop_index("ix_audit_logs_resource", "audit_logs")
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_code"])


def downgrade() -> None:
    # audit_logs
    op.drop_index("ix_audit_logs_resource", "audit_logs")
    op.alter_column("audit_logs", "resource_code", new_column_name="resource_id")
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])

    # signal_audit_records
    op.drop_index("ix_signal_audit_entity_signal", "signal_audit_records")
    op.alter_column("signal_audit_records", "signal_code", new_column_name="signal_id")
    op.alter_column("signal_audit_records", "entity_code", new_column_name="entity_id")
    op.create_index("ix_signal_audit_entity_signal", "signal_audit_records", ["entity_id", "signal_id"])

    # model_version_signals
    op.drop_index("ix_mvs_lookup", "model_version_signals")
    op.alter_column("model_version_signals", "signal_code", new_column_name="signal_id")
    op.alter_column("model_version_signals", "entity_code", new_column_name="entity_id")
    op.alter_column("model_version_signals", "group_code", new_column_name="group_id")
    op.create_index("ix_mvs_lookup", "model_version_signals", ["model_version_id", "signal_id"], unique=True)

    # signal_cache
    op.drop_index("ix_signal_cache_lookup", "signal_cache")
    op.drop_index("ix_signal_cache_entity", "signal_cache")
    op.alter_column("signal_cache", "entity_code", new_column_name="entity_id")
    op.alter_column("signal_cache", "signal_code", new_column_name="signal_id")
    op.create_index("ix_signal_cache_lookup", "signal_cache", ["entity_id", "signal_id", "source_name"])
    op.create_index("ix_signal_cache_entity", "signal_cache", ["entity_id"])

    # referrals
    op.drop_index("ix_referrals_referral_code", "referrals")
    op.alter_column("referrals", "referral_code", new_column_name="referral_id")
    op.create_index("ix_referrals_referral_id", "referrals", ["referral_id"])

    # quotes
    op.drop_index("ix_quotes_quote_code", "quotes")
    op.alter_column("quotes", "quote_code", new_column_name="quote_id")
    op.create_index("ix_quotes_quote_id", "quotes", ["quote_id"])

    # model_versions
    op.alter_column("model_versions", "loss_cohort_code", new_column_name="loss_cohort_id")
    op.drop_index("ix_model_versions_version_code", "model_versions")
    op.alter_column("model_versions", "version_code", new_column_name="version_id")
    op.create_index("ix_model_versions_version_id", "model_versions", ["version_id"])

    # submissions
    op.drop_index("ix_submissions_submission_code", "submissions")
    op.alter_column("submissions", "submission_code", new_column_name="submission_id")
    op.create_index("ix_submissions_submission_id", "submissions", ["submission_id"])
