"""
Agy SQLAlchemy model for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import json
from typing import Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from asteria.database.models.base import Base, TimestampMixin, UUIDMixin


class AgyConversation(Base, UUIDMixin, TimestampMixin):
    """Represents a saved Gemini Antigravity CLI conversation.

    Attributes:
        id: UUID4 primary key.
        title: Short descriptive title for the conversation.
        description: Optional longer description.
        category: Category label (e.g., 'Coding', 'Research').
        conversation_id: The Antigravity CLI conversation UUID.
        tags: JSON-encoded list of tag strings.
        notes: Free-form notes about this conversation.
        created_at: UTC timestamp of creation.
        updated_at: UTC timestamp of last update.
    """

    __tablename__ = "agy_conversations"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Short descriptive title.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Longer description of the conversation.",
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="General",
        index=True,
        doc="Category label.",
    )
    conversation_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
        doc="Antigravity CLI conversation identifier.",
    )
    _tags: Mapped[Optional[str]] = mapped_column(
        "tags",
        Text,
        nullable=True,
        doc="JSON-encoded list of tags.",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Free-form notes.",
    )

    # ─── Tag Helpers ──────────────────────────────────────────────────────────

    @property
    def tags(self) -> list[str]:
        """Return tags as a Python list."""
        if self._tags:
            try:
                return json.loads(self._tags)
            except json.JSONDecodeError:
                return []
        return []

    @tags.setter
    def tags(self, value: list[str]) -> None:
        """Set tags from a Python list."""
        self._tags = json.dumps(value) if value else None

    @property
    def tags_display(self) -> str:
        """Return tags as a comma-separated string."""
        return ", ".join(self.tags) if self.tags else "—"

    def to_dict(self) -> dict:
        """Serialize model to a plain dictionary.

        Returns:
            Dictionary representation of the conversation.
        """
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "conversation_id": self.conversation_id,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<AgyConversation id={self.id!r} "
            f"title={self.title!r} "
            f"category={self.category!r}>"
        )
