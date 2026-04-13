"""
DSI Database Configuration

Provides database engine, session management, and connection pooling.
Engines are lazily created to avoid import-time failures when PostgreSQL
is not available (e.g. during testing or local development without DB).
"""

import os
from typing import AsyncGenerator, Generator, Optional
from contextlib import contextmanager, asynccontextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.orm import sessionmaker, Session, declarative_base

# Environment variables with defaults
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://dsi_user:dsi_password@localhost:5432/dsi_db",
)
DATABASE_URL_SYNC = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://dsi_user:dsi_password@localhost:5432/dsi_db",
)

# Pool settings
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "10"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))

# Base class for models
Base = declarative_base()

# Lazy singletons - engines created on first use, not at import time
_async_engine: Optional[AsyncEngine] = None
_sync_engine: Optional[Engine] = None
_async_session_factory: Optional[async_sessionmaker] = None
_sync_session_factory: Optional[sessionmaker] = None


def get_async_engine() -> AsyncEngine:
    """Get or create the async engine."""
    global _async_engine
    if _async_engine is None:
        _async_engine = create_async_engine(
            DATABASE_URL,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=os.getenv("DSI_DEBUG", "false").lower() == "true",
        )
    return _async_engine


def get_sync_engine() -> Engine:
    """Get or create the sync engine."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            DATABASE_URL_SYNC,
            pool_size=POOL_SIZE,
            max_overflow=MAX_OVERFLOW,
            pool_timeout=POOL_TIMEOUT,
            pool_pre_ping=True,
            echo=os.getenv("DSI_DEBUG", "false").lower() == "true",
        )
    return _sync_engine


def _get_async_session_factory() -> async_sessionmaker:
    """Get or create the async session factory."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )
    return _async_session_factory


def _get_sync_session_factory() -> sessionmaker:
    """Get or create the sync session factory."""
    global _sync_session_factory
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=get_sync_engine(),
            autocommit=False,
            autoflush=False,
        )
    return _sync_session_factory


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async dependency for FastAPI endpoints.

    Usage:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_async_db)):
            ...
    """
    factory = _get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Sync dependency for non-async contexts.

    Usage:
        with get_db() as db:
            ...
    """
    factory = _get_sync_session_factory()
    db = factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@asynccontextmanager
async def async_session_scope() -> AsyncGenerator[AsyncSession, None]:
    """Async context manager for manual session management."""
    factory = _get_async_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """Sync context manager for manual session management."""
    factory = _get_sync_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _bootstrap_migration_only_tables(sync_conn) -> None:
    """Create tables that live only in alembic migrations, not in models.py.

    ``Base.metadata.create_all`` only creates tables declared as SQLAlchemy
    models. The world-engine tables (we_*, migration 011) are managed as raw
    alembic DDL and have no ORM model, so in environments that bootstrap via
    ``init_db`` rather than ``alembic upgrade head`` they'd be missing and
    every world-engine query would raise ``UndefinedTable``.

    This function issues idempotent ``CREATE TABLE IF NOT EXISTS`` statements
    that mirror the schema in ``alembic/versions/011_world_engine_tables.py``.
    Safe to run on every startup: existing tables are untouched.
    """
    ddl_statements = [
        # we_relationships
        """
        CREATE TABLE IF NOT EXISTS we_relationships (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            source_signal VARCHAR(200) NOT NULL,
            target_signal VARCHAR(200) NOT NULL,
            direction VARCHAR(30) NOT NULL,
            lag_months FLOAT,
            correlation_rho FLOAT NOT NULL,
            granger_f_statistic FLOAT,
            granger_p_value FLOAT,
            effect_size FLOAT NOT NULL,
            confounders_tested JSONB NOT NULL DEFAULT '[]'::jsonb,
            holdout_rho FLOAT,
            holdout_p_value FLOAT,
            predictive_hit_rate FLOAT,
            population_size INTEGER NOT NULL,
            coverage_scope JSONB NOT NULL DEFAULT '[]'::jsonb,
            lifecycle_state VARCHAR(30) NOT NULL,
            state_entered_at TIMESTAMPTZ NOT NULL,
            influence_weight FLOAT NOT NULL DEFAULT 0.0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_relationships_state_signals ON we_relationships (lifecycle_state, source_signal, target_signal)",
        "CREATE INDEX IF NOT EXISTS ix_we_relationships_lifecycle ON we_relationships (lifecycle_state)",
        # we_state_transitions
        """
        CREATE TABLE IF NOT EXISTS we_state_transitions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            relationship_id UUID NOT NULL REFERENCES we_relationships(id) ON DELETE CASCADE,
            from_state VARCHAR(30) NOT NULL,
            to_state VARCHAR(30) NOT NULL,
            transitioned_at TIMESTAMPTZ NOT NULL,
            reason TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_state_transitions_relationship ON we_state_transitions (relationship_id)",
        # we_consistency_scores
        """
        CREATE TABLE IF NOT EXISTS we_consistency_scores (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id VARCHAR(200) NOT NULL,
            assessment_id VARCHAR(200) NOT NULL,
            overall_consistency FLOAT NOT NULL,
            signal_pair_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            cross_group_scores JSONB NOT NULL DEFAULT '{}'::jsonb,
            cross_layer_divergence JSONB NOT NULL DEFAULT '{}'::jsonb,
            divergent_pairs JSONB NOT NULL DEFAULT '[]'::jsonb,
            computed_at TIMESTAMPTZ NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_consistency_scores_entity ON we_consistency_scores (entity_id, computed_at)",
        "CREATE INDEX IF NOT EXISTS ix_we_consistency_scores_assessment ON we_consistency_scores (assessment_id)",
        # we_population_consistency
        """
        CREATE TABLE IF NOT EXISTS we_population_consistency (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            coverage VARCHAR(50),
            period VARCHAR(50),
            mean_consistency FLOAT,
            median_consistency FLOAT,
            p10_consistency FLOAT,
            p90_consistency FLOAT,
            sample_size INTEGER NOT NULL,
            metrics JSONB NOT NULL DEFAULT '{}'::jsonb,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_population_consistency_period ON we_population_consistency (coverage, period)",
        # we_causal_adjustments
        """
        CREATE TABLE IF NOT EXISTS we_causal_adjustments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id VARCHAR(200) NOT NULL,
            assessment_id VARCHAR(200) NOT NULL,
            caf_value FLOAT NOT NULL,
            confidence FLOAT NOT NULL,
            active_precursors JSONB NOT NULL DEFAULT '[]'::jsonb,
            trajectory JSONB NOT NULL DEFAULT '{}'::jsonb,
            relationships_evaluated INTEGER NOT NULL DEFAULT 0,
            constrained BOOLEAN NOT NULL DEFAULT false,
            raw_caf FLOAT NOT NULL DEFAULT 1.0,
            constraint_regime VARCHAR(50) NOT NULL DEFAULT 'initial',
            computed_at TIMESTAMPTZ NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_causal_adjustments_assessment ON we_causal_adjustments (assessment_id)",
        "CREATE INDEX IF NOT EXISTS ix_we_causal_adjustments_entity ON we_causal_adjustments (entity_id, computed_at)",
        # we_portfolio_concentrations
        """
        CREATE TABLE IF NOT EXISTS we_portfolio_concentrations (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            entity_id VARCHAR(200) NOT NULL,
            dimension VARCHAR(50) NOT NULL,
            detail TEXT NOT NULL,
            severity FLOAT NOT NULL,
            affected_entities JSONB NOT NULL DEFAULT '[]'::jsonb,
            computed_at TIMESTAMPTZ NOT NULL
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_portfolio_concentrations_entity_dim ON we_portfolio_concentrations (entity_id, dimension)",
        # we_drift_alerts
        """
        CREATE TABLE IF NOT EXISTS we_drift_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            alert_type VARCHAR(50) NOT NULL,
            severity VARCHAR(20) NOT NULL,
            source_signal VARCHAR(200),
            target_signal VARCHAR(200),
            relationship_id UUID REFERENCES we_relationships(id) ON DELETE SET NULL,
            description TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
            detected_at TIMESTAMPTZ NOT NULL,
            acknowledged BOOLEAN NOT NULL DEFAULT false,
            acknowledged_at TIMESTAMPTZ
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_drift_alerts_severity_detected ON we_drift_alerts (severity, detected_at)",
        "CREATE INDEX IF NOT EXISTS ix_we_drift_alerts_relationship ON we_drift_alerts (relationship_id)",
        # we_scan_runs
        """
        CREATE TABLE IF NOT EXISTS we_scan_runs (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            run_id VARCHAR(100) UNIQUE NOT NULL,
            started_at TIMESTAMPTZ NOT NULL,
            completed_at TIMESTAMPTZ,
            maturity_stage VARCHAR(30) NOT NULL,
            entities_scanned INTEGER NOT NULL DEFAULT 0,
            pairs_tested INTEGER NOT NULL DEFAULT 0,
            candidates_found INTEGER NOT NULL DEFAULT 0,
            candidates_after_inference INTEGER NOT NULL DEFAULT 0,
            candidates_after_confound INTEGER NOT NULL DEFAULT 0,
            candidates_after_holdout INTEGER NOT NULL DEFAULT 0,
            new_registrations INTEGER NOT NULL DEFAULT 0,
            drift_alerts_raised INTEGER NOT NULL DEFAULT 0,
            stats JSONB NOT NULL DEFAULT '{}'::jsonb,
            errors JSONB NOT NULL DEFAULT '[]'::jsonb
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_scan_runs_started ON we_scan_runs (started_at)",
        # we_constraint_history
        """
        CREATE TABLE IF NOT EXISTS we_constraint_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            regime_name VARCHAR(50) NOT NULL,
            caf_floor FLOAT NOT NULL,
            caf_cap FLOAT NOT NULL,
            confidence_gate FLOAT NOT NULL,
            min_relationships INTEGER NOT NULL,
            effective_from TIMESTAMPTZ NOT NULL,
            effective_to TIMESTAMPTZ,
            evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """,
        "CREATE INDEX IF NOT EXISTS ix_we_constraint_history_effective ON we_constraint_history (effective_from)",
    ]

    from sqlalchemy import text as _text

    for stmt in ddl_statements:
        sync_conn.execute(_text(stmt))

    # Seed the initial CAF constraint regime only if the table is empty.
    seeded = sync_conn.execute(
        _text("SELECT COUNT(*) FROM we_constraint_history")
    ).scalar()
    if not seeded:
        sync_conn.execute(
            _text(
                "INSERT INTO we_constraint_history "
                "(regime_name, caf_floor, caf_cap, confidence_gate, min_relationships, effective_from, evidence) "
                "VALUES ('initial', 0.80, 1.50, 0.6, 2, NOW(), "
                "'{\"note\": \"Initial constraints at launch\"}'::jsonb)"
            )
        )


async def init_db() -> None:
    """Initialize database tables."""
    eng = get_async_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_bootstrap_migration_only_tables)


async def close_db() -> None:
    """Close database connections."""
    global _async_engine, _sync_engine, _async_session_factory, _sync_session_factory
    if _async_engine is not None:
        await _async_engine.dispose()
        _async_engine = None
        _async_session_factory = None
    if _sync_engine is not None:
        _sync_engine.dispose()
        _sync_engine = None
        _sync_session_factory = None
