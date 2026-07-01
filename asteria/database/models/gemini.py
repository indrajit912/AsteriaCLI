"""
Gemini SQLAlchemy models for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import json
from typing import Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from asteria.database.models.base import Base, TimestampMixin, UUIDMixin


class GeminiWorkspace(Base, UUIDMixin, TimestampMixin):
    """Represents a registered Gemini workspace directory.

    Attributes:
        id: UUID4 primary key.
        path: Absolute filesystem path to the workspace.
        name: Human-readable workspace name.
        description: Optional description.
        projects: Related GeminiProject instances.
    """

    __tablename__ = "gemini_workspaces"

    path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        unique=True,
        index=True,
        doc="Absolute path to the workspace directory.",
    )
    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Human-readable workspace name.",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional workspace description.",
    )

    projects: Mapped[list["GeminiProject"]] = relationship(
        "GeminiProject",
        back_populates="workspace",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """Serialize model to a plain dictionary."""
        return {
            "id": self.id,
            "path": self.path,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<GeminiWorkspace id={self.id!r} name={self.name!r} path={self.path!r}>"


class GeminiProject(Base, UUIDMixin, TimestampMixin):
    """Represents a Gemini project within a workspace.

    A project organises prompts and outputs under a named subdirectory
    of its parent workspace.

    Attributes:
        id: UUID4 primary key.
        name: Project name (becomes the subdirectory name).
        description: Optional project description.
        workspace_id: FK to the parent GeminiWorkspace.
        workspace: Related GeminiWorkspace instance.
        prompts: Related GeminiPrompt instances.
    """

    __tablename__ = "gemini_projects"

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
        doc="Project name (subdirectory name).",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Optional project description.",
    )
    workspace_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("gemini_workspaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to parent workspace.",
    )

    workspace: Mapped["GeminiWorkspace"] = relationship(
        "GeminiWorkspace",
        back_populates="projects",
    )
    prompts: Mapped[list["GeminiPrompt"]] = relationship(
        "GeminiPrompt",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def to_dict(self) -> dict:
        """Serialize model to a plain dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "workspace_id": self.workspace_id,
            "workspace_name": self.workspace.name if self.workspace else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<GeminiProject id={self.id!r} name={self.name!r}>"


class GeminiPrompt(Base, UUIDMixin, TimestampMixin):
    """Represents a Gemini prompt file.

    Attributes:
        id: UUID4 primary key.
        filename: Name of the prompt file (e.g., 'input1.txt').
        filepath: Absolute path to the prompt file.
        project_id: FK to the parent GeminiProject.
        project: Related GeminiProject instance.
        _tags: JSON-encoded list of tags.
        notes: Free-form notes.
        outputs: Related GeminiOutput instances.
    """

    __tablename__ = "gemini_prompts"

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Prompt filename.",
    )
    filepath: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        doc="Absolute path to prompt file.",
    )
    project_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("gemini_projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="FK to parent project.",
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

    project: Mapped["GeminiProject"] = relationship(
        "GeminiProject",
        back_populates="prompts",
    )
    output: Mapped["GeminiOutput"] = relationship(
        "GeminiOutput",
        uselist=False,
        back_populates="prompt",
        cascade="all, delete-orphan",
    )

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
        """Serialize model to a plain dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "project_id": self.project_id,
            "project_name": self.project.name if self.project else None,
            "tags": self.tags,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<GeminiPrompt id={self.id!r} filename={self.filename!r}>"


class GeminiOutput(Base, UUIDMixin, TimestampMixin):
    """Represents a Gemini output file generated from a prompt.

    Attributes:
        id: UUID4 primary key.
        filename: Name of the output file.
        filepath: Absolute path to the output file.
        prompt_id: FK to the originating GeminiPrompt.
        prompt: Related GeminiPrompt instance.
    """

    __tablename__ = "gemini_outputs"

    filename: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
        doc="Output filename.",
    )
    filepath: Mapped[str] = mapped_column(
        String(2000),
        nullable=False,
        doc="Absolute path to output file.",
    )
    prompt_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("gemini_prompts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        unique=True,
        doc="FK to the originating prompt (one-to-one).",
    )

    prompt: Mapped["GeminiPrompt"] = relationship(
        "GeminiPrompt",
        back_populates="output",
    )

    def to_dict(self) -> dict:
        """Serialize model to a plain dictionary."""
        return {
            "id": self.id,
            "filename": self.filename,
            "filepath": self.filepath,
            "prompt_id": self.prompt_id,
            "prompt_filename": self.prompt.filename if self.prompt else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<GeminiOutput id={self.id!r} filename={self.filename!r}>"
