"""
Gemini CLI commands for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from asteria.config.manager import get_config
from asteria.exceptions import (
    DuplicateRecordError,
    GeminiAPIError,
    GeminiError,
    RecordNotFoundError,
)
from asteria.modules.gemini.service import (
    OutputService,
    ProjectService,
    PromptService,
    WorkspaceService,
)
from asteria.utils.console import (
    confirm_action,
    console,
    make_table,
    print_error,
    print_info,
    print_key_value,
    print_no_results,
    print_section,
    print_success,
    print_warning,
    make_spinner,
    prompt_input,
)
from asteria.utils.editor import open_editor
from asteria.utils.formatting import format_datetime, format_tags, short_id, truncate
from asteria.database.connection import get_session
from asteria.modules.gemini.repository import WorkspaceRepository, ProjectRepository, PromptRepository, OutputRepository
from asteria.database.models.gemini import GeminiPrompt, GeminiOutput

# ─── Typer App ────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="gemini",
    help="[cyan]Manage Gemini API projects, prompts and outputs.[/cyan]",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Sub-apps

project_app = typer.Typer(
    name="project",
    help="Manage [cyan]projects[/cyan].",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
prompt_app = typer.Typer(
    name="prompt",
    help="Manage [cyan]prompts[/cyan].",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
output_app = typer.Typer(
    name="output",
    help="Manage [cyan]outputs[/cyan].",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


app.add_typer(project_app, name="project")
app.add_typer(prompt_app, name="prompt")
app.add_typer(output_app, name="output")


# ─── Workspace Commands ───────────────────────────────────────────────────────





# ─── Project Commands ─────────────────────────────────────────────────────────


@project_app.command("create")
def project_create(
    name: str = typer.Argument(..., help="Project name"),
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Workspace UUID, name, or path"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description"
    ),
) -> None:
    """[green]Create[/green] a new Gemini project."""
    print_section("Create Gemini Project")
    try:
        # Resolve workspace (use internal managed workspace if not provided)
        if not workspace:
            ws = WorkspaceService.get_or_create_default_workspace()
        else:
            ws = WorkspaceService.resolve_workspace(workspace)

        project = ProjectService.create_project(
            name=name,
            workspace_id=ws.id,
            description=description,
        )
        print_success(
            f"Project created: [bold white]{project.name}[/bold white] "
            f"[dim]in {ws.name}[/dim]"
        )
        print_info(
            f"Directory: {ws.path}/{name}/prompts/  and  {ws.path}/{name}/outputs/"
        )
    except DuplicateRecordError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Failed: {exc}")
        raise typer.Exit(1)


@project_app.command("list")
def project_list(
    workspace: Optional[str] = typer.Option(
        None, "--workspace", "-w", help="Filter by workspace"
    ),
) -> None:
    """[cyan]List[/cyan] all Gemini projects."""
    try:
        workspace_id = None
        if workspace:
            ws = WorkspaceService.resolve_workspace(workspace)
            workspace_id = ws.id

        projects = ProjectService.list_projects(workspace_id=workspace_id)
        if not projects:
            print_no_results("projects")
            return

        table = make_table(title="Gemini Projects", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Short ID", style="id", width=10)
        table.add_column("Name", style="title", min_width=15)
        table.add_column("Workspace", style="dim cyan", min_width=15)
        table.add_column("Description", style="dim", min_width=20, overflow="fold")
        table.add_column("Prompts", style="dim", width=8)
        table.add_column("Created", style="timestamp", width=12)
        for idx, proj in enumerate(projects, 1):
            prompts = PromptService.list_prompts(project_id=proj.id)
            table.add_row(
                str(idx),
                short_id(proj.id),
                proj.name,
                proj.workspace.name if proj.workspace else "—",
                proj.description or "—",
                str(len(prompts)),
                format_datetime(proj.created_at, "%Y-%m-%d"),
            )
        console.print(table)
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@project_app.command("delete")
def project_delete(
    identifier: str = typer.Argument(..., help="Project UUID or name"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """[red]Delete[/red] a Gemini project."""
    try:
        project = ProjectService.resolve_project(identifier)
        if not yes:
            if not confirm_action(
                f"Delete project '{project.name}'? (Prompts and outputs will be deleted too)",
                dangerous=True,
            ):
                print_info("Aborted.")
                raise typer.Exit(0)
        ProjectService.delete_project(project.id)
        print_success(f"Project deleted: {project.name}")
    except (RecordNotFoundError, GeminiError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


# ─── Prompt Commands ──────────────────────────────────────────────────────────


@prompt_app.command("new")
def prompt_new(
    filename: str = typer.Argument(..., help="Prompt filename (e.g., input1.txt)"),
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Project UUID or name"
    ),
    tags: Optional[str] = typer.Option(None, "--tags", help="Comma-separated tags"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes"),
    edit: bool = typer.Option(True, "--edit/--no-edit", help="Open editor immediately"),
) -> None:
    """[green]Create[/green] a new prompt file."""
    print_section("New Gemini Prompt")
    config = get_config()
    try:
        if not project:
            projects = ProjectService.list_projects()
            if not projects:
                print_error("No projects found. Run: asteria gemini project create")
                raise typer.Exit(1)
            if len(projects) == 1:
                proj = projects[0]
                print_info(f"Using project: {proj.name}")
            else:
                for i, p in enumerate(projects, 1):
                    console.print(f"  [dim]{i}.[/dim] {p.name}")
                project = prompt_input("Project name or ID")
                proj = ProjectService.resolve_project(project)
        else:
            proj = ProjectService.resolve_project(project)

        from asteria.utils.formatting import parse_tags
        tag_list = parse_tags(tags or "")

        prompt_obj = PromptService.create_prompt(
            filename=filename,
            project_id=proj.id,
            content="",
            tags=tag_list,
            notes=notes,
        )

        if edit:
            print_info(f"Opening editor: {prompt_obj.filepath}")
            open_editor(Path(prompt_obj.filepath), editor=config.default_editor)

        print_success(
            f"Prompt created: [bold white]{prompt_obj.filename}[/bold white] "
            f"[dim]in {proj.name}[/dim]"
        )
    except (RecordNotFoundError, GeminiError, DuplicateRecordError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Failed: {exc}")
        raise typer.Exit(1)


@prompt_app.command("list")
def prompt_list(
    project: Optional[str] = typer.Option(
        None, "--project", "-p", help="Filter by project"
    ),
) -> None:
    """[cyan]List[/cyan] all prompts."""
    try:
        project_id = None
        if project:
            proj = ProjectService.resolve_project(project)
            project_id = proj.id

        prompts = PromptService.list_prompts(project_id=project_id)
        if not prompts:
            print_no_results("prompts")
            return

        table = make_table(title="Gemini Prompts", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Short ID", style="id", width=10)
        table.add_column("Name", style="title", min_width=20, overflow="fold")
        table.add_column("Project", style="dim cyan", min_width=15, overflow="fold")
        table.add_column("Tags", style="tag", min_width=15, overflow="fold")
        table.add_column("Output", style="dim", width=8)
        table.add_column("Created", style="timestamp", width=12)
        table.add_column("Updated", style="timestamp", width=12)
        for idx, p in enumerate(prompts, 1):
            outputs = OutputService.list_outputs(prompt_id=p.id)
            table.add_row(
                str(idx),
                short_id(p.id),
                p.filename,
                p.project.name if p.project else "—",
                p.tags_display,
                "True" if outputs else "False",
                format_datetime(p.created_at, "%Y-%m-%d"),
                format_datetime(p.updated_at, "%Y-%m-%d"),
            )
        console.print(table)
    except (RecordNotFoundError, GeminiError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@prompt_app.command("edit")
def prompt_edit(
    identifier: str = typer.Argument(..., help="Prompt UUID or filename"),
    editor: Optional[str] = typer.Option(
        None, "--editor", "-e", help="Editor override"
    ),
) -> None:
    """[yellow]Edit[/yellow] a prompt file in your configured editor."""
    config = get_config()
    try:
        prompt_obj = PromptService.resolve_prompt(identifier)
        editor_name = editor or config.default_editor
        open_editor(Path(prompt_obj.filepath), editor=editor_name)
        print_success(f"Prompt saved: {prompt_obj.filename}")
    except (RecordNotFoundError, GeminiError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Editor error: {exc}")
        raise typer.Exit(1)


@prompt_app.command("delete")
def prompt_delete(
    identifier: str = typer.Argument(..., help="Prompt UUID or filename"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    remove_file: bool = typer.Option(
        False, "--remove-file", help="Also delete the file from disk"
    ),
) -> None:
    """[red]Delete[/red] a prompt."""
    try:
        prompt_obj = PromptService.resolve_prompt(identifier)
        if not yes:
            msg = f"Delete prompt '{prompt_obj.filename}'"
            if remove_file:
                msg += " AND its file from disk"
            msg += "?"
            if not confirm_action(msg, dangerous=True):
                print_info("Aborted.")
                raise typer.Exit(0)
        PromptService.delete_prompt(prompt_obj.id, delete_file=remove_file)
        print_success(f"Prompt deleted: {prompt_obj.filename}")
    except (RecordNotFoundError, GeminiError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@prompt_app.command("run")
def prompt_run(
    identifier: str = typer.Argument(..., help="Prompt UUID or filename"),
    api_key: Optional[str] = typer.Option(
        None, "--api-key", help="Gemini API key override"
    ),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model override"),
) -> None:
    """[green]Run[/green] a prompt through the Gemini API and save the output."""
    try:
        prompt_obj = PromptService.resolve_prompt(identifier)
        # Check for existing output(s)
        existing_outputs = OutputService.list_outputs(prompt_id=prompt_obj.id)
        if existing_outputs:
            msg = f"An output already exists for prompt '{prompt_obj.filename}'. Replace it?"
            if not confirm_action(msg, dangerous=True):
                print_info("Aborted.")
                raise typer.Exit(0)
            # Delete existing outputs and their files
            for out in existing_outputs:
                OutputService.delete_output(out.id, delete_file=True)
        print_info(
            f"Running prompt: [bold white]{prompt_obj.filename}[/bold white] ..."
        )
        with make_spinner(f"Calling Gemini API for {prompt_obj.filename}"):
            output = PromptService.run_prompt(
                prompt_id=prompt_obj.id,
                api_key=api_key,
                model=model,
            )
        print_success(
            f"Output saved: [bold white]{output.filename}[/bold white]\n"
            f"  [path]{output.filepath}[/path]"
        )
    except (RecordNotFoundError, GeminiError, GeminiAPIError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Unexpected error: {exc}")
        raise typer.Exit(1)


# ─── Output Commands ──────────────────────────────────────────────────────────





@output_app.command("list")
def output_list(
    prompt: Optional[str] = typer.Option(
        None, "--prompt", "-p", help="Filter by prompt UUID or filename"
    ),
) -> None:
    """[cyan]List[/cyan] all outputs."""
    try:
        prompt_id = None
        if prompt:
            prompt_obj = PromptService.resolve_prompt(prompt)
            prompt_id = prompt_obj.id

        outputs = OutputService.list_outputs(prompt_id=prompt_id)
        if not outputs:
            print_no_results("outputs")
            return

        table = make_table(title="Gemini Outputs", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Short ID", style="id", width=10)
        table.add_column("Project", style="dim cyan", min_width=15, overflow="fold")
        table.add_column("Prompt", style="title", min_width=20, overflow="fold")
        table.add_column("Created", style="timestamp", width=12)

        for idx, out in enumerate(outputs, 1):
            prompt_name = out.prompt.filename if out.prompt else "—"
            project_name = out.prompt.project.name if (out.prompt and out.prompt.project) else "—"
            table.add_row(
                str(idx),
                short_id(out.id),
                project_name,
                prompt_name,
                format_datetime(out.created_at, "%Y-%m-%d"),
            )
        console.print(table)
    except (RecordNotFoundError, GeminiError) as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@output_app.command("edit")
def output_edit(
    identifier: str = typer.Argument(..., help="Output UUID or filename"),
    editor: Optional[str] = typer.Option(None, "--editor", "-e", help="Editor override"),
) -> None:
    """[yellow]Edit[/yellow] an output file."""
    config = get_config()
    try:
        output = OutputService.get_output(identifier)
        open_editor(Path(output.filepath), editor=editor or config.default_editor)
        print_success(f"Output saved: {output.filename}")
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Editor error: {exc}")
        raise typer.Exit(1)


@output_app.command("delete")
def output_delete(
    identifier: str = typer.Argument(..., help="Output UUID"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
    remove_file: bool = typer.Option(
        False, "--remove-file", help="Also delete file from disk"
    ),
) -> None:
    """[red]Delete[/red] a Gemini output."""
    try:
        output = OutputService.get_output(identifier)
        if not yes:
            msg = f"Delete output '{output.filename}'"
            if remove_file:
                msg += " AND its file from disk"
            msg += "?"
            if not confirm_action(msg, dangerous=True):
                print_info("Aborted.")
                raise typer.Exit(0)
        OutputService.delete_output(output.id, delete_file=remove_file)
        print_success(f"Output deleted: {output.filename}")
    except RecordNotFoundError as exc:
        print_error(str(exc))
# ─── Import / Export Commands ─────────────────────────────────────────────────────

import json
from pathlib import Path
from asteria.version import __version__

@app.command("export")
def gemini_export(
    output_path: Path = typer.Option(
        None, "--output", "-o", help="Destination JSON file or directory (default: gemini_export.json)"
    ),
) -> None:
    """Export all Gemini data (workspaces, projects, prompts) to JSON including app version.
    If a directory is supplied, the export will be saved as 'gemini_export.json' inside it.
    """
    if output_path:
        if output_path.is_dir():
            dest = output_path / "gemini_export.json"
        else:
            dest = output_path
    else:
        dest = Path.cwd() / "gemini_export.json"
    # Ensure the target directory exists
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Notify user about export limitations
    print_warning("Export will NOT include outputs. Prompt text will be included in the JSON but will NOT be imported back.")
    try:
        with get_session() as session:
            ws_repo = WorkspaceRepository(session)
            proj_repo = ProjectRepository(session)
            prompt_repo = PromptRepository(session)
            data = {
                "__version__": __version__,
                "workspaces": [ws.to_dict() for ws in ws_repo.list_all()],
                "projects": [proj.to_dict() for proj in proj_repo.list_all()],
                "prompts": [
                    {
                        **prompt.to_dict(),
                        "tags": prompt.tags,
                        "text": Path(prompt.filepath).read_text(encoding="utf-8")
                        if Path(prompt.filepath).exists() else "",
                    }
                    for prompt in session.query(GeminiPrompt).all()
                ],
                # Outputs are intentionally excluded from export
            }
        # Write JSON, handling permission errors
        try:
            dest.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except PermissionError as perm_err:
            print_error(f"Permission denied when writing to {dest}: {perm_err}")
            raise typer.Exit(1)
        print_success(f"Gemini data exported to [path]{dest}[/path]")
    except Exception as exc:
        print_error(f"Export failed: {exc}")
        raise typer.Exit(1)

@app.command("import")
def gemini_import(
    import_path: Path = typer.Option(
        None, "--input", "-i", help="Source JSON file (default: gemini_export.json)"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation prompts"),
) -> None:
    """Import Gemini data from a JSON dump. Existing records will be updated or created."""
    src = import_path or Path.cwd() / "gemini_export.json"
    if not src.exists():
        print_error(f"Import file not found: {src}")
        raise typer.Exit(1)
    try:
        data = json.loads(src.read_text(encoding="utf-8"))
        file_version = data.get("__version__")
        if file_version and file_version != __version__:
            print_warning(f"Import file version {file_version} differs from current {__version__}.")
            if not yes and not confirm_action("Proceed with import despite version mismatch?", dangerous=True):
                print_info("Aborted.")
                raise typer.Exit(0)
        with get_session() as session:
            ws_map = {}
            # Workspaces
            for ws_dict in data.get("workspaces", []):
                repo = WorkspaceRepository(session)
                existing = repo.get_by_path(ws_dict["path"])
                if existing:
                    ws_map[ws_dict["id"]] = existing.id
                    existing.name = ws_dict["name"]
                    existing.description = ws_dict.get("description")
                else:
                    new_ws = repo.create(
                        path=ws_dict["path"],
                        name=ws_dict["name"],
                        description=ws_dict.get("description"),
                    )
                    ws_map[ws_dict["id"]] = new_ws.id
            session.commit()
            # Projects
            for proj_dict in data.get("projects", []):
                repo = ProjectRepository(session)
                mapped_ws_id = ws_map.get(proj_dict["workspace_id"], proj_dict["workspace_id"])
                existing = repo.get_by_name_and_workspace(proj_dict["name"], mapped_ws_id)
                if existing:
                    existing.description = proj_dict.get("description")
                else:
                    repo.create(
                        name=proj_dict["name"],
                        workspace_id=mapped_ws_id,
                        description=proj_dict.get("description"),
                    )
            session.commit()
            # Prompts and Outputs are intentionally NOT imported.
            print_warning("Outputs are not imported; only workspaces and projects are restored.")
            # No further action.
        print_success(f"Gemini data imported from [path]{src}[/path]")
    except Exception as exc:
        print_error(f"Import failed: {exc}")
        raise typer.Exit(1)
