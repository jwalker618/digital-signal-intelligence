"""Initial schema - users, submissions, quotes, referrals, model versions, signal cache, audit logs

Revision ID: 001
Revises: None
Create Date: 2026-01-31

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255)),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("is_superuser", sa.Boolean, default=False),
        sa.Column("permissions", JSONB, default=[]),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.Column("last_login", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("key_prefix", sa.String(20), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("permissions", JSONB, default=[]),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("last_used_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_api_keys_key_prefix", "api_keys", ["key_prefix"])

    # Submissions
    op.create_table(
        "submissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("submission_id", sa.String(50), unique=True, nullable=False),
        sa.Column("entity_name", sa.String(500), nullable=False),
        sa.Column("domain_hint", sa.String(255)),
        sa.Column("discovered_domain", sa.String(255)),
        sa.Column("country_hint", sa.String(10)),
        sa.Column("coverage", sa.String(50), nullable=False),
        sa.Column("configuration", sa.String(100)),
        sa.Column("locale", sa.String(10), default="US"),
        sa.Column(
            "status",
            sa.Enum("pending", "processing", "ready", "failed", "cancelled", name="submissionstatus"),
            default="pending",
        ),
        sa.Column("submission_data", JSONB, default={}),
        sa.Column("direct_query_responses", JSONB, default={}),
        sa.Column("processing_started_at", sa.DateTime(timezone=True)),
        sa.Column("processing_completed_at", sa.DateTime(timezone=True)),
        sa.Column("processing_duration_ms", sa.Float),
        sa.Column("error_message", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_submissions_submission_id", "submissions", ["submission_id"])
    op.create_index("ix_submissions_coverage", "submissions", ["coverage"])
    op.create_index("ix_submissions_status", "submissions", ["status"])
    op.create_index("ix_submissions_entity_coverage", "submissions", ["entity_name", "coverage"])
    op.create_index("ix_submissions_created_at", "submissions", ["created_at"])

    # Model Versions
    op.create_table(
        "model_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("version_id", sa.String(50), unique=True, nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("version_number", sa.Integer, default=1),
        sa.Column("version_type", sa.String(50)),
        sa.Column("config_hash", sa.String(64)),
        sa.Column("coverage", sa.String(50)),
        sa.Column("configuration_name", sa.String(100)),
        sa.Column("discovery_output", JSONB),
        sa.Column("signal_outputs", JSONB, default=[]),
        sa.Column("categorical_outputs", JSONB, default=[]),
        sa.Column("group_scores", JSONB, default={}),
        sa.Column("pure_composite_score", sa.Float),
        sa.Column("confidence", sa.Float),
        sa.Column("signal_coverage", sa.Float),
        sa.Column("signal_conditions", JSONB, default=[]),
        sa.Column("query_conditions", JSONB, default=[]),
        sa.Column("tier_overrides", JSONB, default=[]),
        sa.Column("score_based_tier", sa.Integer),
        sa.Column("final_tier", sa.Integer),
        sa.Column("tier_label", sa.String(50)),
        sa.Column("base_premium", sa.Float),
        sa.Column("base_premium_method", sa.String(50)),
        sa.Column("modifiers_applied", JSONB, default=[]),
        sa.Column("premium_after_modifiers", sa.Float),
        sa.Column("limit_premiums", JSONB, default={}),
        sa.Column("final_premium", sa.Float),
        sa.Column(
            "decision",
            sa.Enum("approve", "refer", "decline", name="decisiontype"),
        ),
        sa.Column("auto_approve", sa.Boolean, default=False),
        sa.Column("referral_reasons", JSONB, default=[]),
        sa.Column("notes", JSONB, default=[]),
        sa.Column("created_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_model_versions_version_id", "model_versions", ["version_id"])
    op.create_index("ix_model_versions_submission", "model_versions", ["submission_id", "version_number"])

    # Quotes
    op.create_table(
        "quotes",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("quote_id", sa.String(50), unique=True, nullable=False),
        sa.Column("submission_id", UUID(as_uuid=True), sa.ForeignKey("submissions.id"), nullable=False),
        sa.Column("model_version_id", UUID(as_uuid=True), sa.ForeignKey("model_versions.id")),
        sa.Column(
            "status",
            sa.Enum("draft", "ready", "bound", "expired", "declined", name="quotestatus"),
            default="draft",
        ),
        sa.Column("composite_score", sa.Float),
        sa.Column("confidence", sa.Float),
        sa.Column("tier", sa.Integer),
        sa.Column("tier_label", sa.String(50)),
        sa.Column(
            "decision",
            sa.Enum("approve", "refer", "decline", name="decisiontype"),
            nullable=True,
        ),
        sa.Column("auto_approve", sa.Boolean, default=False),
        sa.Column("referral_reasons", JSONB, default=[]),
        sa.Column("base_premium", sa.Float),
        sa.Column("recommended_premium", sa.Float),
        sa.Column("recommended_limit", sa.Float),
        sa.Column("premium_options", JSONB, default={}),
        sa.Column("valid_from", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("valid_until", sa.DateTime(timezone=True)),
        sa.Column("bound_at", sa.DateTime(timezone=True)),
        sa.Column("bound_by", UUID(as_uuid=True)),
        sa.Column("policy_number", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_quotes_quote_id", "quotes", ["quote_id"])
    op.create_index("ix_quotes_status_valid", "quotes", ["status", "valid_until"])

    # Referrals
    op.create_table(
        "referrals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("referral_id", sa.String(50), unique=True, nullable=False),
        sa.Column("quote_id", UUID(as_uuid=True), sa.ForeignKey("quotes.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum("pending", "in_review", "approved", "declined", "modified", name="referralstatus"),
            default="pending",
        ),
        sa.Column("reasons", JSONB, default=[]),
        sa.Column("priority", sa.Integer, default=5),
        sa.Column("assigned_to", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("assigned_at", sa.DateTime(timezone=True)),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("review_decision", sa.String(50)),
        sa.Column("review_notes", sa.Text),
        sa.Column("tier_override", sa.Integer),
        sa.Column("premium_adjustment", sa.Float),
        sa.Column("adjustments", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_referrals_referral_id", "referrals", ["referral_id"])
    op.create_index("ix_referrals_status", "referrals", ["status"])

    # Signal Cache
    op.create_table(
        "signal_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("entity_id", sa.String(255), nullable=False),
        sa.Column("signal_id", sa.String(100), nullable=False),
        sa.Column("source_name", sa.String(100), nullable=False),
        sa.Column("data", JSONB, nullable=False),
        sa.Column("confidence", sa.Float),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ttl_seconds", sa.Integer),
        sa.Column("extraction_time_ms", sa.Float),
        sa.Column("from_external_cache", sa.Boolean, default=False),
    )
    op.create_index("ix_signal_cache_lookup", "signal_cache", ["entity_id", "signal_id", "source_name"])
    op.create_index("ix_signal_cache_entity", "signal_cache", ["entity_id"])
    op.create_index("ix_signal_cache_expires", "signal_cache", ["expires_at"])

    # Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("event_action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100)),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("api_key_id", UUID(as_uuid=True), sa.ForeignKey("api_keys.id")),
        sa.Column("ip_address", sa.String(45)),
        sa.Column("user_agent", sa.String(500)),
        sa.Column("details", JSONB, default={}),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_audit_logs_event_type", "audit_logs", ["event_type"])
    op.create_index("ix_audit_logs_resource", "audit_logs", ["resource_type", "resource_id"])
    op.create_index("ix_audit_logs_user", "audit_logs", ["user_id", "created_at"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("signal_cache")
    op.drop_table("referrals")
    op.drop_table("quotes")
    op.drop_table("model_versions")
    op.drop_table("submissions")
    op.drop_table("api_keys")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS submissionstatus")
    op.execute("DROP TYPE IF EXISTS quotestatus")
    op.execute("DROP TYPE IF EXISTS decisiontype")
    op.execute("DROP TYPE IF EXISTS referralstatus")
