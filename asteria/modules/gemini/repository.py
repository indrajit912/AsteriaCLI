"""
Gemini repositories for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from asteria.database.models.gemini import (
    GeminiOutput,
    GeminiProject,
    GeminiPrompt,
    GeminiWorkspace,
)
from asteria.exceptions import DuplicateRecordError, RecordNotFoundError

logger = logging.getLogger("asteria.modules.gemini.repository")


# ─── Workspace Repository ─────────────────────────────────────────────────────


class WorkspaceRepository:
    """Data-access layer for GeminiWorkspace records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        path: str,
        name: str,
        description: Optional[str] = None,
    ) -> GeminiWorkspace:
        existing = self.get_by_path(path)
        if existing:
            raise DuplicateRecordError("GeminiWorkspace", path)
        ws = GeminiWorkspace(path=path, name=name, description=description)
        self.session.add(ws)
        self.session.flush()
        logger.info("Created workspace: %s at %s", name, path)
        return ws

    def get_by_id(self, workspace_id: str) -> Optional[GeminiWorkspace]:
        return self.session.get(GeminiWorkspace, workspace_id)

    def get_by_path(self, path: str) -> Optional[GeminiWorkspace]:
        return (
            self.session.query(GeminiWorkspace)
            .filter(GeminiWorkspace.path == path)
            .first()
        )

    def get_by_name(self, name: str) -> Optional[GeminiWorkspace]:
        return (
            self.session.query(GeminiWorkspace)
            .filter(GeminiWorkspace.name.ilike(name))
            .first()
        )

    def get_or_raise(self, workspace_id: str) -> GeminiWorkspace:
        ws = self.get_by_id(workspace_id)
        if ws is None:
            raise RecordNotFoundError("GeminiWorkspace", workspace_id)
        return ws

    def list_all(self) -> list[GeminiWorkspace]:
        return (
            self.session.query(GeminiWorkspace)
            .order_by(GeminiWorkspace.name)
            .all()
        )

    def delete(self, workspace_id: str) -> None:
        ws = self.get_or_raise(workspace_id)
        self.session.delete(ws)
        self.session.flush()

    def count(self) -> int:
        return self.session.query(GeminiWorkspace).count()


# ─── Project Repository ───────────────────────────────────────────────────────


class ProjectRepository:
    """Data-access layer for GeminiProject records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        name: str,
        workspace_id: str,
        description: Optional[str] = None,
    ) -> GeminiProject:
        # Check for duplicate name within workspace
        existing = self.get_by_name_and_workspace(name, workspace_id)
        if existing:
            raise DuplicateRecordError("GeminiProject", f"{workspace_id}/{name}")
        project = GeminiProject(
            name=name, workspace_id=workspace_id, description=description
        )
        self.session.add(project)
        self.session.flush()
        logger.info("Created project: %s", name)
        return project

    def get_by_id(self, project_id: str) -> Optional[GeminiProject]:
        return self.session.get(GeminiProject, project_id)

    def get_by_name_and_workspace(
        self, name: str, workspace_id: str
    ) -> Optional[GeminiProject]:
        return (
            self.session.query(GeminiProject)
            .filter(
                GeminiProject.name.ilike(name),
                GeminiProject.workspace_id == workspace_id,
            )
            .first()
        )

    def get_or_raise(self, project_id: str) -> GeminiProject:
        project = self.get_by_id(project_id)
        if project is None:
            raise RecordNotFoundError("GeminiProject", project_id)
        return project

    def list_all(
        self, workspace_id: Optional[str] = None
    ) -> list[GeminiProject]:
        query = self.session.query(GeminiProject).options(
            joinedload(GeminiProject.workspace)
        )
        if workspace_id:
            query = query.filter(GeminiProject.workspace_id == workspace_id)
        return query.order_by(GeminiProject.name).all()

    def delete(self, project_id: str) -> None:
        project = self.get_or_raise(project_id)
        self.session.delete(project)
        self.session.flush()

    def count(self, workspace_id: Optional[str] = None) -> int:
        query = self.session.query(GeminiProject)
        if workspace_id:
            query = query.filter(GeminiProject.workspace_id == workspace_id)
        return query.count()


# ─── Prompt Repository ────────────────────────────────────────────────────────


class PromptRepository:
    """Data-access layer for GeminiPrompt records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        filename: str,
        filepath: str,
        project_id: str,
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> GeminiPrompt:
        prompt = GeminiPrompt(
            filename=filename,
            filepath=filepath,
            project_id=project_id,
            notes=notes,
        )
        prompt.tags = tags or []
        self.session.add(prompt)
        self.session.flush()
        logger.info("Created prompt: %s", filename)
        return prompt

    def get_by_id(self, prompt_id: str) -> Optional[GeminiPrompt]:
        return self.session.get(GeminiPrompt, prompt_id)

    def get_by_filename_and_project(
        self, filename: str, project_id: str
    ) -> Optional[GeminiPrompt]:
        return (
            self.session.query(GeminiPrompt)
            .filter(
                GeminiPrompt.filename.ilike(filename),
                GeminiPrompt.project_id == project_id,
            )
            .first()
        )

    def get_or_raise(self, prompt_id: str) -> GeminiPrompt:
        prompt = self.get_by_id(prompt_id)
        if prompt is None:
            raise RecordNotFoundError("GeminiPrompt", prompt_id)
        return prompt

    def list_all(
        self, project_id: Optional[str] = None
    ) -> list[GeminiPrompt]:
        query = self.session.query(GeminiPrompt).options(
            joinedload(GeminiPrompt.project).joinedload(GeminiProject.workspace)
        )
        if project_id:
            query = query.filter(GeminiPrompt.project_id == project_id)
        return query.order_by(GeminiPrompt.filename).all()

    def search(self, query: str) -> list[GeminiPrompt]:
        pattern = f"%{query}%"
        return (
            self.session.query(GeminiPrompt)
            .options(joinedload(GeminiPrompt.project))
            .filter(
                GeminiPrompt.filename.ilike(pattern)
                | GeminiPrompt._tags.ilike(pattern)
                | GeminiPrompt.notes.ilike(pattern)
            )
            .all()
        )

    def delete(self, prompt_id: str) -> None:
        prompt = self.get_or_raise(prompt_id)
        self.session.delete(prompt)
        self.session.flush()

    def count(self, project_id: Optional[str] = None) -> int:
        query = self.session.query(GeminiPrompt)
        if project_id:
            query = query.filter(GeminiPrompt.project_id == project_id)
        return query.count()


# ─── Output Repository ────────────────────────────────────────────────────────


class OutputRepository:
    """Data-access layer for GeminiOutput records."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        filename: str,
        filepath: str,
        prompt_id: str,
    ) -> GeminiOutput:
        output = GeminiOutput(
            filename=filename,
            filepath=filepath,
            prompt_id=prompt_id,
        )
        self.session.add(output)
        self.session.flush()
        logger.info("Created output: %s", filename)
        return output

    def get_by_id(self, output_id: str) -> Optional[GeminiOutput]:
        return self.session.get(GeminiOutput, output_id)

    def get_or_raise(self, output_id: str) -> GeminiOutput:
        output = self.get_by_id(output_id)
        if output is None:
            raise RecordNotFoundError("GeminiOutput", output_id)
        return output

    def get_by_prompt_id(self, prompt_id: str) -> list[GeminiOutput]:
        return (
            self.session.query(GeminiOutput)
            .filter(GeminiOutput.prompt_id == prompt_id)
            .order_by(GeminiOutput.created_at.desc())
            .all()
        )

    def list_all(
        self, prompt_id: Optional[str] = None
    ) -> list[GeminiOutput]:
        query = self.session.query(GeminiOutput).options(
            joinedload(GeminiOutput.prompt).joinedload(GeminiPrompt.project)
        )
        if prompt_id:
            query = query.filter(GeminiOutput.prompt_id == prompt_id)
        return query.order_by(GeminiOutput.created_at.desc()).all()

    def delete(self, output_id: str) -> None:
        output = self.get_or_raise(output_id)
        self.session.delete(output)
        self.session.flush()

    def count(self, prompt_id: Optional[str] = None) -> int:
        query = self.session.query(GeminiOutput)
        if prompt_id:
            query = query.filter(GeminiOutput.prompt_id == prompt_id)
        return query.count()
