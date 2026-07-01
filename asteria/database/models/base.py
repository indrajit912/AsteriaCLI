"""
Database base model for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Import the single authoritative "now" function so that all database
# timestamps are stored in the local machine timezone.
from asteria.utils.dt import local_now


def utcnow() -> datetime:
    """Backward-compatible alias for :func:`local_now`.

    .. deprecated::
        Use :func:`asteria.utils.dt.local_now` directly.  This alias exists
        only to avoid breaking any external code that imported ``utcnow``
        from this module before the local-timezone migration.
    """
    return local_now()


def new_uuid() -> str:
    """Generate a new UUID4 string."""
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


class TimestampMixin:
    """Mixin adding ``created_at`` and ``updated_at`` timestamps to models.

    Both columns store a **timezone-aware** datetime in the machine's local
    timezone (provided by :func:`asteria.utils.dt.local_now`).
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=local_now,
        nullable=False,
        doc="Local-timezone timestamp when this record was created.",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=local_now,
        onupdate=local_now,
        nullable=False,
        doc="Local-timezone timestamp when this record was last updated.",
    )


class UUIDMixin:
    """Mixin adding a UUID4 primary key to models."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=new_uuid,
        doc="UUID4 primary key.",
    )

