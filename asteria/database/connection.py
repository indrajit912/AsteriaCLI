"""
Database connection and session management for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from asteria.constants import APP_DIR, DATABASE_URL
from asteria.database.models.base import Base

logger = logging.getLogger("asteria.database")

# ─── Engine & Session Factory ─────────────────────────────────────────────────

_engine: Optional[Engine] = None
_SessionLocal: Optional[sessionmaker] = None


def _get_database_url() -> str:
    """Return the SQLite database URL, ensuring the directory exists."""
    APP_DIR.mkdir(parents=True, exist_ok=True)
    return DATABASE_URL


def get_engine(database_url: Optional[str] = None) -> Engine:
    """Get or create the SQLAlchemy engine singleton.

    Args:
        database_url: Optional override for the database URL.

    Returns:
        SQLAlchemy Engine instance.
    """
    global _engine
    if _engine is None:
        url = database_url or _get_database_url()
        _engine = create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        # Enable WAL mode and foreign keys for SQLite
        @event.listens_for(_engine, "connect")
        def _on_connect(dbapi_conn, connection_record):  # type: ignore
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON")
            cursor.execute("PRAGMA journal_mode = WAL")
            cursor.close()

        logger.debug("SQLAlchemy engine created: %s", url)

    return _engine


def get_session_factory(engine: Optional[Engine] = None) -> sessionmaker:
    """Get or create the session factory.

    Args:
        engine: Optional Engine override.

    Returns:
        sessionmaker instance.
    """
    global _SessionLocal
    if _SessionLocal is None:
        _engine = engine or get_engine()
        _SessionLocal = sessionmaker(
            bind=_engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session as a context manager.

    Yields:
        SQLAlchemy Session instance.

    Raises:
        Exception: Re-raises any exception after rolling back.
    """
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db(engine: Optional[Engine] = None) -> None:
    """Create all database tables if they do not exist.

    Args:
        engine: Optional Engine override (useful for testing).
    """
    eng = engine or get_engine()
    Base.metadata.create_all(bind=eng)
    logger.info("Database tables created/verified at %s", eng.url)


def drop_all_tables(engine: Optional[Engine] = None) -> None:
    """Drop all database tables (DESTRUCTIVE – use with caution).

    Args:
        engine: Optional Engine override.
    """
    eng = engine or get_engine()
    Base.metadata.drop_all(bind=eng)
    logger.warning("All database tables dropped.")


def reset_engine() -> None:
    """Reset the engine and session factory singletons (for testing)."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionLocal = None
