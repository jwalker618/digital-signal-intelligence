"""Normalise signal tables — reference tables, remove audit bloat

Revision ID: 004
Revises: 003
Create Date: 2026-03-08

Changes:
1. Create `signals` reference table (id INTEGER PK, code VARCHAR UNIQUE)
2. Create `signal_sources` reference table (id INTEGER PK, name VARCHAR UNIQUE)
3. signal_cache: replace signal_code/source_name text with signal_id/source_id
   integer FKs; drop inferred_value, audited_value, is_overridden, audit_trail
4. model_version_signals: replace signal_code text with signal_id integer FK;
   drop used_audited_value
5. signal_audit_records: replace signal_cache_id, model_version_id, signal_code,
   entity_code, inferred_value, is_overridden with single
   model_version_signal_id FK; change audited_value from JSONB to Float
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1. Create reference tables
    # =========================================================================
    op.create_table(
        "signals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("code", sa.String(100), unique=True, nullable=False, index=True),
    )
    op.create_table(
        "signal_sources",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(100), unique=True, nullable=False, index=True),
    )

    # =========================================================================
    # 2. Populate reference tables from existing data
    # =========================================================================
    op.execute("""
        INSERT INTO signals (code)
        SELECT DISTINCT signal_code FROM signal_cache
        UNION
        SELECT DISTINCT signal_code FROM model_version_signals
        ON CONFLICT DO NOTHING
    """)
    op.execute("""
        INSERT INTO signal_sources (name)
        SELECT DISTINCT source_name FROM signal_cache
        ON CONFLICT DO NOTHING
    """)

    # =========================================================================
    # 3. signal_cache: add FK columns, migrate data, drop old columns
    # =========================================================================
    op.add_column("signal_cache", sa.Column("signal_id", sa.Integer))
    op.add_column("signal_cache", sa.Column("source_id", sa.Integer))

    op.execute("""
        UPDATE signal_cache sc
        SET signal_id = s.id
        FROM signals s
        WHERE sc.signal_code = s.code
    """)
    op.execute("""
        UPDATE signal_cache sc
        SET source_id = ss.id
        FROM signal_sources ss
        WHERE sc.source_name = ss.name
    """)

    op.alter_column("signal_cache", "signal_id", nullable=False)
    op.alter_column("signal_cache", "source_id", nullable=False)
    op.create_foreign_key("fk_signal_cache_signal_id", "signal_cache", "signals", ["signal_id"], ["id"])
    op.create_foreign_key("fk_signal_cache_source_id", "signal_cache", "signal_sources", ["source_id"], ["id"])

    # Drop old indexes and columns
    op.drop_index("ix_signal_cache_lookup", "signal_cache")
    op.drop_column("signal_cache", "signal_code")
    op.drop_column("signal_cache", "source_name")
    op.drop_column("signal_cache", "inferred_value")
    op.drop_column("signal_cache", "audited_value")
    op.drop_column("signal_cache", "is_overridden")
    op.drop_column("signal_cache", "audit_trail")

    op.create_index("ix_signal_cache_lookup", "signal_cache", ["entity_code", "signal_id", "source_id"])

    # =========================================================================
    # 4. model_version_signals: replace signal_code with signal_id FK,
    #    drop used_audited_value
    # =========================================================================
    op.add_column("model_version_signals", sa.Column("signal_id", sa.Integer))

    op.execute("""
        UPDATE model_version_signals mvs
        SET signal_id = s.id
        FROM signals s
        WHERE mvs.signal_code = s.code
    """)

    op.alter_column("model_version_signals", "signal_id", nullable=False)
    op.create_foreign_key("fk_mvs_signal_id", "model_version_signals", "signals", ["signal_id"], ["id"])

    op.drop_index("ix_mvs_lookup", "model_version_signals")
    op.drop_column("model_version_signals", "signal_code")
    op.drop_column("model_version_signals", "used_audited_value")

    op.create_index("ix_mvs_lookup", "model_version_signals", ["model_version_id", "signal_id"], unique=True)

    # =========================================================================
    # 5. signal_audit_records: restructure around model_version_signal_id FK
    # =========================================================================
    op.add_column(
        "signal_audit_records",
        sa.Column("model_version_signal_id", UUID(as_uuid=True)),
    )

    # Best-effort backfill: match on signal_code+entity_code+model_version_id
    op.execute("""
        UPDATE signal_audit_records sar
        SET model_version_signal_id = mvs.id
        FROM model_version_signals mvs
        JOIN signals s ON mvs.signal_id = s.id
        WHERE s.code = sar.signal_code
          AND mvs.entity_code = sar.entity_code
          AND mvs.model_version_id = sar.model_version_id
    """)

    # Drop rows that couldn't be matched (orphans)
    op.execute("DELETE FROM signal_audit_records WHERE model_version_signal_id IS NULL")

    op.alter_column("signal_audit_records", "model_version_signal_id", nullable=False)
    op.create_foreign_key(
        "fk_sar_mvs_id", "signal_audit_records", "model_version_signals",
        ["model_version_signal_id"], ["id"],
    )
    op.create_index("ix_signal_audit_mvs", "signal_audit_records", ["model_version_signal_id"])

    # Convert audited_value from JSONB to Float
    op.add_column("signal_audit_records", sa.Column("audited_value_float", sa.Float))
    op.execute("""
        UPDATE signal_audit_records
        SET audited_value_float = (audited_value->>'score')::float
        WHERE audited_value IS NOT NULL
    """)
    op.drop_column("signal_audit_records", "audited_value")
    op.alter_column("signal_audit_records", "audited_value_float", new_column_name="audited_value")
    op.alter_column("signal_audit_records", "audited_value", nullable=False)

    # Drop redundant columns and indexes
    op.drop_index("ix_signal_audit_entity_signal", "signal_audit_records")
    op.drop_index("ix_signal_audit_model_version", "signal_audit_records")
    op.drop_column("signal_audit_records", "signal_cache_id")
    op.drop_column("signal_audit_records", "model_version_id")
    op.drop_column("signal_audit_records", "signal_code")
    op.drop_column("signal_audit_records", "entity_code")
    op.drop_column("signal_audit_records", "inferred_value")
    op.drop_column("signal_audit_records", "is_overridden")


def downgrade() -> None:
    # =========================================================================
    # 5. signal_audit_records: restore original structure
    # =========================================================================
    op.add_column("signal_audit_records", sa.Column("is_overridden", sa.Boolean, server_default="true"))
    op.add_column("signal_audit_records", sa.Column("inferred_value", JSONB))
    op.add_column("signal_audit_records", sa.Column("entity_code", sa.String(255)))
    op.add_column("signal_audit_records", sa.Column("signal_code", sa.String(100)))
    op.add_column("signal_audit_records", sa.Column("model_version_id", UUID(as_uuid=True)))
    op.add_column("signal_audit_records", sa.Column("signal_cache_id", UUID(as_uuid=True)))

    # Backfill from model_version_signals
    op.execute("""
        UPDATE signal_audit_records sar
        SET signal_code = s.code,
            entity_code = mvs.entity_code,
            model_version_id = mvs.model_version_id,
            signal_cache_id = mvs.signal_cache_id,
            inferred_value = jsonb_build_object('score', mvs.score)
        FROM model_version_signals mvs
        JOIN signals s ON mvs.signal_id = s.id
        WHERE sar.model_version_signal_id = mvs.id
    """)

    # Convert audited_value Float back to JSONB
    op.add_column("signal_audit_records", sa.Column("audited_value_jsonb", JSONB))
    op.execute("""
        UPDATE signal_audit_records
        SET audited_value_jsonb = jsonb_build_object('score', audited_value)
        WHERE audited_value IS NOT NULL
    """)
    op.drop_column("signal_audit_records", "audited_value")
    op.alter_column("signal_audit_records", "audited_value_jsonb", new_column_name="audited_value")

    op.drop_index("ix_signal_audit_mvs", "signal_audit_records")
    op.drop_constraint("fk_sar_mvs_id", "signal_audit_records", type_="foreignkey")
    op.drop_column("signal_audit_records", "model_version_signal_id")

    op.create_index("ix_signal_audit_entity_signal", "signal_audit_records", ["entity_code", "signal_code"])
    op.create_index("ix_signal_audit_model_version", "signal_audit_records", ["model_version_id"])

    # =========================================================================
    # 4. model_version_signals: restore signal_code, used_audited_value
    # =========================================================================
    op.add_column("model_version_signals", sa.Column("used_audited_value", sa.Boolean, server_default="false"))
    op.add_column("model_version_signals", sa.Column("signal_code", sa.String(100)))

    op.execute("""
        UPDATE model_version_signals mvs
        SET signal_code = s.code
        FROM signals s
        WHERE mvs.signal_id = s.id
    """)

    op.drop_index("ix_mvs_lookup", "model_version_signals")
    op.drop_constraint("fk_mvs_signal_id", "model_version_signals", type_="foreignkey")
    op.drop_column("model_version_signals", "signal_id")

    op.create_index("ix_mvs_lookup", "model_version_signals", ["model_version_id", "signal_code"], unique=True)

    # =========================================================================
    # 3. signal_cache: restore text columns
    # =========================================================================
    op.add_column("signal_cache", sa.Column("audit_trail", JSONB, server_default="[]"))
    op.add_column("signal_cache", sa.Column("is_overridden", sa.Boolean, server_default="false"))
    op.add_column("signal_cache", sa.Column("audited_value", JSONB))
    op.add_column("signal_cache", sa.Column("inferred_value", JSONB))
    op.add_column("signal_cache", sa.Column("source_name", sa.String(100)))
    op.add_column("signal_cache", sa.Column("signal_code", sa.String(100)))

    op.execute("""
        UPDATE signal_cache sc
        SET signal_code = s.code
        FROM signals s
        WHERE sc.signal_id = s.id
    """)
    op.execute("""
        UPDATE signal_cache sc
        SET source_name = ss.name
        FROM signal_sources ss
        WHERE sc.source_id = ss.id
    """)

    op.drop_index("ix_signal_cache_lookup", "signal_cache")
    op.drop_constraint("fk_signal_cache_signal_id", "signal_cache", type_="foreignkey")
    op.drop_constraint("fk_signal_cache_source_id", "signal_cache", type_="foreignkey")
    op.drop_column("signal_cache", "signal_id")
    op.drop_column("signal_cache", "source_id")

    op.create_index("ix_signal_cache_lookup", "signal_cache", ["entity_code", "signal_code", "source_name"])

    # =========================================================================
    # 1. Drop reference tables
    # =========================================================================
    op.drop_table("signal_sources")
    op.drop_table("signals")
