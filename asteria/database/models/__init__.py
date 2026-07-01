"""
Database models package for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

from asteria.database.models.base import Base, TimestampMixin, UUIDMixin, new_uuid, utcnow
from asteria.database.models.agy import AgyConversation
from asteria.database.models.gemini import (
    GeminiWorkspace,
    GeminiProject,
    GeminiPrompt,
    GeminiOutput,
)
from asteria.utils.dt import local_now  # canonical "now"; utcnow is a compat alias

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDMixin",
    "new_uuid",
    "local_now",   # preferred
    "utcnow",      # backward-compatible alias
    "AgyConversation",
    "GeminiWorkspace",
    "GeminiProject",
    "GeminiPrompt",
    "GeminiOutput",
]

