"""
Gemini service layer for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from pathlib import Path
from typing import Any, Optional

from asteria.constants import GEMINI_OUTPUTS_DIR, GEMINI_PROMPTS_DIR, INTERNAL_WORKSPACE_DIR
from asteria.database.connection import get_session
from asteria.database.models.gemini import (
    GeminiOutput,
    GeminiProject,
    GeminiPrompt,
    GeminiWorkspace,
)
from asteria.exceptions import GeminiError, GeminiRunnerError, RecordNotFoundError
from asteria.modules.gemini.repository import (
    OutputRepository,
    ProjectRepository,
    PromptRepository,
    WorkspaceRepository,
)
from asteria.utils.formatting import short_id
from asteria.modules.gemini.runner import GeminiRunner

logger = logging.getLogger("asteria.modules.gemini.service")


# ─── Workspace Service ────────────────────────────────────────────────────────


class WorkspaceService:
    """Business logic for Gemini workspaces."""

    @staticmethod
    def add_workspace(
        path: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> GeminiWorkspace:
        """Register a new workspace.

        Args:
            path: Absolute filesystem path.
            name: Human-readable name (defaults to directory name).
            description: Optional description.

        Returns:
            Created GeminiWorkspace.
        """
        resolved = Path(path).resolve()
        resolved.mkdir(parents=True, exist_ok=True)
        ws_name = name or resolved.name
        with get_session() as session:
            repo = WorkspaceRepository(session)
            ws = repo.create(
                path=str(resolved),
                name=ws_name,
                description=description,
            )
            session.commit()
            session.refresh(ws)
            return ws

    @staticmethod
    def list_workspaces() -> list[GeminiWorkspace]:
        with get_session() as session:
            return WorkspaceRepository(session).list_all()

    @staticmethod
    def get_workspace(workspace_id: str) -> GeminiWorkspace:
        with get_session() as session:
            return WorkspaceRepository(session).get_or_raise(workspace_id)

    @staticmethod
    def delete_workspace(workspace_id: str) -> None:
        with get_session() as session:
            WorkspaceRepository(session).delete(workspace_id)

    @staticmethod
    def resolve_workspace(identifier: str) -> GeminiWorkspace:
        """Find a workspace by ID, name, or path.

        Args:
            identifier: UUID, name, or path string.

        Returns:
            Matching GeminiWorkspace.

        Raises:
            RecordNotFoundError: If not found.
        """
        with get_session() as session:
            repo = WorkspaceRepository(session)
            # Try by ID
            ws = repo.get_by_id(identifier)
            if ws:
                return ws
            # Try by name
            ws = repo.get_by_name(identifier)
            if ws:
                return ws
            # Try by path
            ws = repo.get_by_path(identifier)
            if ws:
                return ws
            raise RecordNotFoundError("GeminiWorkspace", identifier)


    @staticmethod
    def get_or_create_default_workspace() -> GeminiWorkspace:
        """Return the internal managed workspace, creating it if necessary.

        This workspace is located at ``INTERNAL_WORKSPACE_DIR`` and is used for all Gemini data.
        """
        from asteria.constants import INTERNAL_WORKSPACE_DIR
        # Ensure the internal workspace directory exists on the filesystem
        workspace_path = Path(INTERNAL_WORKSPACE_DIR)
        workspace_path.mkdir(parents=True, exist_ok=True)
        # Check if workspace already exists in DB
        with get_session() as session:
            repo = WorkspaceRepository(session)
            ws = repo.get_by_path(str(workspace_path))
            if ws:
                return ws
            # Create the workspace record in DB
            ws = repo.create(
                path=str(workspace_path),
                name="default",
                description="Managed internal workspace for Gemini",
            )
            session.commit()
            session.refresh(ws)
        # Ensure README exists inside the workspace
        readme_path = workspace_path / "README.md"
        if not readme_path.exists():
            readme_path.write_text(
                "# AsteriaCLI Gemini Workspace\n\nThis directory is managed exclusively by AsteriaCLI. Do not modify files manually.",
                encoding="utf-8",
            )
        return ws

# ─── Project Service ──────────────────────────────────────────────────────────


class ProjectService:
    """Business logic for Gemini projects."""

    @staticmethod
    def create_project(
        name: str,
        workspace_id: str,
        description: Optional[str] = None,
    ) -> GeminiProject:
        """Create a project and its directory structure.

        Args:
            name: Project name.
            workspace_id: Parent workspace UUID.
            description: Optional description.

        Returns:
            Created GeminiProject.
        """
        with get_session() as session:
            ws_repo = WorkspaceRepository(session)
            workspace = ws_repo.get_or_raise(workspace_id)

            # Create directory structure
            project_dir = Path(workspace.path) / name
            (project_dir / GEMINI_PROMPTS_DIR).mkdir(parents=True, exist_ok=True)
            (project_dir / GEMINI_OUTPUTS_DIR).mkdir(parents=True, exist_ok=True)
            logger.info("Created project directories at %s", project_dir)

            proj_repo = ProjectRepository(session)
            project = proj_repo.create(
                name=name,
                workspace_id=workspace_id,
                description=description,
            )
            session.commit()
            session.refresh(project)
            return project

    @staticmethod
    def list_projects(workspace_id: Optional[str] = None) -> list[GeminiProject]:
        with get_session() as session:
            return ProjectRepository(session).list_all(workspace_id=workspace_id)

    @staticmethod
    def get_project(project_id: str) -> GeminiProject:
        with get_session() as session:
            return ProjectRepository(session).get_or_raise(project_id)

    @staticmethod
    def delete_project(project_id: str) -> None:
        with get_session() as session:
            project = ProjectRepository(session).get_or_raise(project_id)
            # Remove directory structure
            import shutil
            ws_repo = WorkspaceRepository(session)
            workspace = ws_repo.get_or_raise(project.workspace_id)
            project_dir = Path(workspace.path) / project.name
            if project_dir.exists():
                shutil.rmtree(project_dir)
            ProjectRepository(session).delete(project_id)


    @staticmethod
    def resolve_project(identifier: str) -> GeminiProject:
        """Find a project by UUID, short ID, or name (case‑insensitive)."""
        with get_session() as session:
            repo = ProjectRepository(session)
            # Direct UUID match
            project = repo.get_by_id(identifier)
            if project:
                return project
            # Short ID (prefix) match
            all_projects = repo.list_all()
            prefix_matches = [p for p in all_projects if p.id.startswith(identifier)]
            if len(prefix_matches) == 1:
                return prefix_matches[0]
            if len(prefix_matches) > 1:
                raise GeminiError(
                    f"Multiple projects match short ID '{identifier}'. Use full UUID."
                )
            # Name match (case‑insensitive)
            name_matches = [p for p in all_projects if p.name.lower() == identifier.lower()]
            if len(name_matches) == 1:
                return name_matches[0]
            if len(name_matches) > 1:
                raise GeminiError(
                    f"Multiple projects named '{identifier}'. Use UUID instead."
                )
            raise RecordNotFoundError("GeminiProject", identifier)

# ─── Prompt Service ───────────────────────────────────────────────────────────


class PromptService:
    """Business logic for Gemini prompts."""

    @staticmethod
    def create_prompt(
        filename: str,
        project_id: str,
        content: str = "",
        tags: Optional[list[str]] = None,
        notes: Optional[str] = None,
    ) -> GeminiPrompt:
        """Create a new prompt file and register it in the database.

        Args:
            filename: Prompt filename (e.g., 'input1.txt').
            project_id: Parent project UUID.
            content: Initial prompt content.
            tags: Optional tags.
            notes: Optional notes.

        Returns:
            Created GeminiPrompt.
        """
        with get_session() as session:
            proj_repo = ProjectRepository(session)
            project = proj_repo.get_or_raise(project_id)
            ws_repo = WorkspaceRepository(session)
            workspace = ws_repo.get_or_raise(project.workspace_id)

            # Resolve filepath
            prompts_dir = (
                Path(workspace.path) / project.name / GEMINI_PROMPTS_DIR
            )
            prompts_dir.mkdir(parents=True, exist_ok=True)

            if not filename.endswith(".txt"):
                filename = filename + ".txt"

            filepath = prompts_dir / filename
            filepath.write_text(content, encoding="utf-8")

            prompt_repo = PromptRepository(session)
            prompt = prompt_repo.create(
                filename=filename,
                filepath=str(filepath),
                project_id=project_id,
                tags=tags,
                notes=notes,
            )
            session.commit()
            session.refresh(prompt)
            return prompt

    @staticmethod
    def list_prompts(project_id: Optional[str] = None) -> list[GeminiPrompt]:
        with get_session() as session:
            return PromptRepository(session).list_all(project_id=project_id)

    @staticmethod
    def get_prompt(prompt_id: str) -> GeminiPrompt:
        with get_session() as session:
            return PromptRepository(session).get_or_raise(prompt_id)

    @staticmethod
    def delete_prompt(prompt_id: str, delete_file: bool = False) -> None:
        with get_session() as session:
            repo = PromptRepository(session)
            prompt = repo.get_or_raise(prompt_id)
            if delete_file:
                filepath = Path(prompt.filepath)
                if filepath.exists():
                    filepath.unlink()
            repo.delete(prompt_id)

    @staticmethod
    def resolve_prompt(identifier: str) -> GeminiPrompt:
        """Find a prompt by ID or filename."""
        with get_session() as session:
            repo = PromptRepository(session)
            prompt = repo.get_by_id(identifier)
            if prompt:
                return prompt
            prompts = repo.list_all()
            matches = [
                p
                for p in prompts
                if p.filename.lower() == identifier.lower()
                or p.filename.lower() == (identifier + ".txt").lower()
            ]
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise GeminiError(f"Multiple prompts named '{identifier}'.")
            # prefix match
            matches = [p for p in prompts if p.id.startswith(identifier)]
            if len(matches) == 1:
                return matches[0]
            raise RecordNotFoundError("GeminiPrompt", identifier)

    @staticmethod
    def run_prompt(
        prompt_id: str,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> GeminiOutput:
        """Execute a prompt and save the output.

        Args:
            prompt_id: UUID of the prompt to run.
            api_key: Optional API key override.
            model: Optional model override.

        Returns:
            Created GeminiOutput record.
        """
        with get_session() as session:
            prompt_repo = PromptRepository(session)
            prompt = prompt_repo.get_or_raise(prompt_id)

            proj_repo = ProjectRepository(session)
            project = proj_repo.get_or_raise(prompt.project_id)

            ws_repo = WorkspaceRepository(session)
            workspace = ws_repo.get_or_raise(project.workspace_id)

            # Build output path
            outputs_dir = (
                Path(workspace.path) / project.name / GEMINI_OUTPUTS_DIR
            )
            outputs_dir.mkdir(parents=True, exist_ok=True)
            # Use .md extension for Gemini output regardless of prompt file extension
            output_filename = Path(prompt.filename).stem + ".md"
            output_path = outputs_dir / output_filename

            # Run via Gemini API
            runner = GeminiRunner(api_key=api_key, model=model)
            runner.run_prompt_file(
                prompt_path=Path(prompt.filepath),
                output_path=output_path,
            )

            # Register output in database
            out_repo = OutputRepository(session)
            output = out_repo.create(
                filename=output_filename,
                filepath=str(output_path),
                prompt_id=prompt_id,
            )
            session.commit()
            session.refresh(output)
            return output


# ─── Output Service ───────────────────────────────────────────────────────────


class OutputService:
    """Business logic for Gemini outputs."""

    @staticmethod
    def list_outputs(prompt_id: Optional[str] = None) -> list[GeminiOutput]:
        with get_session() as session:
            return OutputRepository(session).list_all(prompt_id=prompt_id)

    @staticmethod
    def get_output(output_id: str) -> GeminiOutput:
        """Retrieve a GeminiOutput by full UUID or short ID.

        The CLI list command displays a shortened 8‑character ID. This method first
        attempts a direct lookup using the full UUID; if that fails it falls back to
        scanning the outputs and matching the short ID generated by ``short_id``.
        """
        with get_session() as session:
            repo = OutputRepository(session)
            # Direct lookup using the full identifier
            output = repo.get_by_id(output_id)
            if output:
                return output
            # Fallback: compare short IDs
            for out in repo.list_all():
                if short_id(out.id) == output_id:
                    return out
            # Not found – raise the standard error
            raise RecordNotFoundError("GeminiOutput", output_id)

    @staticmethod
    def delete_output(output_id: str, delete_file: bool = False) -> None:
        with get_session() as session:
            repo = OutputRepository(session)
            output = repo.get_or_raise(output_id)
            if delete_file:
                filepath = Path(output.filepath)
                if filepath.exists():
                    filepath.unlink()
            repo.delete(output_id)

    @staticmethod
    def statistics() -> dict[str, Any]:
        """Return statistics about the Gemini module.

        Returns:
            Dictionary of counts.
        """
        with get_session() as session:
            ws_count = WorkspaceRepository(session).count()
            proj_count = ProjectRepository(session).count()
            prompt_count = PromptRepository(session).count()
            output_count = OutputRepository(session).count()
        return {
            "workspaces": ws_count,
            "projects": proj_count,
            "prompts": prompt_count,
            "outputs": output_count,
        }
