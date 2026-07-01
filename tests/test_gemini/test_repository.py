"""
Unit tests for the Gemini repository module.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import pytest

from asteria.database.models.gemini import GeminiProject, GeminiWorkspace
from asteria.modules.gemini.repository import (
    OutputRepository,
    ProjectRepository,
    PromptRepository,
    WorkspaceRepository,
)
from asteria.exceptions import DuplicateRecordError, RecordNotFoundError


class TestWorkspaceRepository:
    """Tests for WorkspaceRepository."""

    def test_create_workspace(self, db_session):
        repo = WorkspaceRepository(db_session)
        ws = repo.create(path="/tmp/my_workspace", name="My Workspace")
        db_session.commit()
        assert ws.id is not None
        assert ws.name == "My Workspace"
        assert ws.path == "/tmp/my_workspace"

    def test_create_duplicate_path_raises(self, db_session):
        repo = WorkspaceRepository(db_session)
        repo.create(path="/tmp/ws1", name="WS1")
        db_session.commit()
        with pytest.raises(DuplicateRecordError):
            repo.create(path="/tmp/ws1", name="WS2")

    def test_get_by_id(self, db_session):
        repo = WorkspaceRepository(db_session)
        ws = repo.create(path="/tmp/ws_get", name="Get WS")
        db_session.commit()
        fetched = repo.get_by_id(ws.id)
        assert fetched is not None
        assert fetched.name == "Get WS"

    def test_list_all(self, db_session):
        repo = WorkspaceRepository(db_session)
        repo.create(path="/tmp/ws_a", name="WS A")
        repo.create(path="/tmp/ws_b", name="WS B")
        db_session.commit()
        all_ws = repo.list_all()
        assert len(all_ws) == 2

    def test_delete(self, db_session):
        repo = WorkspaceRepository(db_session)
        ws = repo.create(path="/tmp/ws_del", name="Del WS")
        db_session.commit()
        repo.delete(ws.id)
        db_session.commit()
        assert repo.get_by_id(ws.id) is None

    def test_delete_not_found(self, db_session):
        repo = WorkspaceRepository(db_session)
        with pytest.raises(RecordNotFoundError):
            repo.delete("no-such-id")


class TestProjectRepository:
    """Tests for ProjectRepository."""

    def _make_workspace(self, db_session, path="/tmp/ws_proj", name="ProjWS"):
        ws_repo = WorkspaceRepository(db_session)
        ws = ws_repo.create(path=path, name=name)
        db_session.flush()
        return ws

    def test_create_project(self, db_session):
        ws = self._make_workspace(db_session)
        repo = ProjectRepository(db_session)
        proj = repo.create(name="my-project", workspace_id=ws.id)
        db_session.commit()
        assert proj.id is not None
        assert proj.name == "my-project"
        assert proj.workspace_id == ws.id

    def test_list_by_workspace(self, db_session):
        ws = self._make_workspace(db_session)
        ws2 = self._make_workspace(db_session, path="/tmp/ws2", name="WS2")
        repo = ProjectRepository(db_session)
        repo.create(name="proj-a", workspace_id=ws.id)
        repo.create(name="proj-b", workspace_id=ws.id)
        repo.create(name="proj-c", workspace_id=ws2.id)
        db_session.commit()
        ws1_projects = repo.list_all(workspace_id=ws.id)
        assert len(ws1_projects) == 2

    def test_delete_cascades(self, db_session):
        """Deleting a project should cascade to prompts."""
        ws = self._make_workspace(db_session)
        repo = ProjectRepository(db_session)
        proj = repo.create(name="cascade-proj", workspace_id=ws.id)
        db_session.flush()

        pr_repo = PromptRepository(db_session)
        pr_repo.create(
            filename="p.txt",
            filepath="/tmp/p.txt",
            project_id=proj.id,
        )
        db_session.commit()

        repo.delete(proj.id)
        db_session.commit()

        # Prompt should be gone too
        prompts = pr_repo.list_all(project_id=proj.id)
        assert len(prompts) == 0
