"""
Pytest configuration and shared fixtures for AsteriaCLI tests.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typer.testing import CliRunner

from asteria.cli import app
from asteria.config.manager import ConfigManager, reset_config
from asteria.database.connection import reset_engine
from asteria.database.models.base import Base


@pytest.fixture(scope="function")
def in_memory_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(in_memory_engine):
    """Provide a database session backed by the in-memory engine."""
    SessionLocal = sessionmaker(bind=in_memory_engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture(scope="function")
def cli_runner():
    """Provide a Typer CLI test runner."""
    return CliRunner()


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset global singletons before each test."""
    reset_config()
    reset_engine()
    yield
    reset_config()
    reset_engine()
