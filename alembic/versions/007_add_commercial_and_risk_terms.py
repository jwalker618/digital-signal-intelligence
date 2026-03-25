"""Add commercial_terms and risk_terms tables

Revision ID: 007
Revises: 006
Create Date: 2026-03-25

Changes:
1. Create commercial_terms table — entity-level economics that transform
   technical premium (model_versions) into gross/reporting premium.
   Contains deductions (JSONB), taxes (JSONB), FX context, distribution
   structure, offered premium with underwriter discretion, and
   written/earned time values.

2. Create risk_terms table — deductible nuance and coverage structure
   for reporting (aggregate vs per-occurrence, SIR, waiting periods,
   sub-limits, reinstatements). Linked to commercial_terms because
   risk structure is entity-scoped.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = "007"
down_revision: str = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- commercial_terms ---
    op.create_table(
        "commercial_terms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("model_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("model_versions.id"), nullable=False),

        # Entity identification
        sa.Column("entity_id", sa.String(100), nullable=False),
        sa.Column("entity_name", sa.String(255)),
        sa.Column("entity_market", sa.String(50)),

        # Currency context
        sa.Column("base_currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("fx_rate_to_usd", sa.Float),
        sa.Column("fx_rate_source", sa.String(100)),
        sa.Column("fx_rate_date", sa.DateTime(timezone=True)),

        # Premium chain
        sa.Column("technical_premium_usd", sa.Float),
        sa.Column("technical_premium_local", sa.Float),

        # Distribution
        sa.Column("distribution_type", sa.String(50)),
        sa.Column("signed_line", sa.Float),
        sa.Column("role", sa.String(20)),
        sa.Column("lead_loading_factor", sa.Float, server_default="1.0"),
        sa.Column("net_premium", sa.Float),

        # Deductions (JSONB — brokerage, overrider, fronting, profit commission)
        sa.Column("deductions", JSONB, server_default="{}"),
        sa.Column("total_commission", sa.Float),

        # Taxes and levies (JSONB — IPT, stamp duty, regulatory, fire service)
        sa.Column("taxes_and_levies", JSONB, server_default="{}"),
        sa.Column("total_taxes", sa.Float),

        # Gross premium
        sa.Column("gross_premium", sa.Float),

        # Offered premium (underwriter discretion)
        sa.Column("offered_premium", sa.Float),
        sa.Column("offered_premium_discretion", sa.Float),
        sa.Column("offered_premium_rationale", sa.Text),
        sa.Column("offered_premium_set_by", UUID(as_uuid=True),
                  sa.ForeignKey("users.id")),
        sa.Column("offered_premium_set_at", sa.DateTime(timezone=True)),

        # Minimum premium
        sa.Column("minimum_gross_premium", sa.Float),
        sa.Column("at_minimum_premium", sa.Boolean, server_default="false"),

        # Written/earned (time values)
        sa.Column("written_date", sa.DateTime(timezone=True)),
        sa.Column("earned_start", sa.DateTime(timezone=True)),
        sa.Column("earned_end", sa.DateTime(timezone=True)),
        sa.Column("earned_method", sa.String(50)),

        # Audit
        sa.Column("created_by", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index("ix_commercial_terms_model_version", "commercial_terms",
                    ["model_version_id"])
    op.create_index("ix_commercial_terms_entity", "commercial_terms",
                    ["entity_id", "created_at"])

    # --- risk_terms ---
    op.create_table(
        "risk_terms",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("commercial_terms_id", UUID(as_uuid=True),
                  sa.ForeignKey("commercial_terms.id"), nullable=False),

        # Deductible structure
        sa.Column("deductible_type", sa.String(50)),
        sa.Column("deductible_amount", sa.Float),
        sa.Column("deductible_currency", sa.String(3), server_default="USD"),
        sa.Column("deductible_basis", sa.String(100)),

        # SIR
        sa.Column("sir_amount", sa.Float),
        sa.Column("sir_applies", sa.Boolean, server_default="false"),

        # Waiting period
        sa.Column("waiting_period_hours", sa.Float),
        sa.Column("waiting_period_type", sa.String(50)),

        # Aggregates
        sa.Column("aggregate_limit", sa.Float),
        sa.Column("aggregate_deductible", sa.Float),
        sa.Column("aggregate_basis", sa.String(100)),

        # Reinstatements
        sa.Column("reinstatements", sa.Integer),
        sa.Column("reinstatement_rate", sa.Float),

        # Layering
        sa.Column("attachment_point", sa.Float),
        sa.Column("layer_limit", sa.Float),

        # Sub-limits and coverage terms (JSONB)
        sa.Column("sub_limits", JSONB, server_default="[]"),
        sa.Column("coverage_terms", JSONB, server_default="{}"),

        # Audit
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )
    op.create_index("ix_risk_terms_commercial", "risk_terms",
                    ["commercial_terms_id"])


def downgrade() -> None:
    op.drop_table("risk_terms")
    op.drop_table("commercial_terms")
