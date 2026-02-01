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


async def init_db() -> None:
    """Initialize database tables."""
    eng = get_async_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


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
