"""
Main CLI entry point for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.panel import Panel

from asteria.config.manager import get_config
from asteria.constants import APP_DIR, BACKUP_DIR, DB_PATH, CONFIG_PATH
from asteria.database.connection import get_engine, init_db, reset_engine
from asteria.logging_config import setup_logging
from asteria.modules.agy.commands import app as agy_app
from asteria.modules.gemini.commands import app as gemini_app
from asteria.utils.console import (
    confirm_action,
    console,
    make_table,
    print_banner,
    print_error,
    print_info,
    print_key_value,
    print_section,
    print_success,
    print_warning,
    prompt_input,
)
from asteria.version import (
    __author__,
    __copyright__,
    __description__,
    __url__,
    __version__,
)

# ─── Root App ────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="asteria",
    help="[bold cyan]AsteriaCLI[/bold cyan] — Your unified interface for AI workflows.",
    rich_markup_mode="rich",
    no_args_is_help=False,
    add_completion=True,
    pretty_exceptions_enable=True,
    pretty_exceptions_show_locals=False,
)

# Register module sub-apps
app.add_typer(agy_app, name="agy")
app.add_typer(gemini_app, name="gemini")

# ─── Config Commands ──────────────────────────────────────────────────────────

config_app = typer.Typer(
    name="config",
    help="Manage [cyan]configuration[/cyan] settings.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
app.add_typer(config_app, name="config")


@config_app.command("show")
def config_show() -> None:
    """[cyan]Show[/cyan] the current configuration."""
    config = get_config()
    all_cfg = config.all()
    print_section("AsteriaCLI Configuration")

    for section, values in all_cfg.items():
        if isinstance(values, dict):
            data: dict = {}
            for key, val in values.items():
                display_key = f"{section}.{key}"
                display_val = (
                    "***" if "key" in key.lower() and val else str(val) or "—"
                )
                data[display_key] = display_val
            from asteria.utils.console import print_key_value
            print_key_value(data)
        else:
            console.print(f"  [dim]{section}:[/dim] {values}")

    console.print(f"\n  [dim]Config file: {config.config_path}[/dim]")


@config_app.command("set")
def config_set(
    key: str = typer.Argument(..., help="Config key (dot notation, e.g. general.default_editor)"),
    value: Optional[str] = typer.Argument(None, help="Value to set"),
) -> None:
    """[yellow]Set[/yellow] a configuration value."""
    config = get_config()

    if key == "gemini.api_key":
        if not value:
            # hidden input for secret
            value = prompt_input("Enter Gemini API Key", password=True)
            confirm = prompt_input("Confirm Gemini API Key", password=True)
            if value != confirm:
                print_error("API keys do not match.")
                raise typer.Exit(1)
    elif not value:
        value = prompt_input(f"Enter value for {key}")

    config.set(key, value)
    config.save()
    print_success(f"Config updated: [bold white]{key}[/bold white]")


@config_app.command("path")
def config_path() -> None:
    """Show the [cyan]path[/cyan] to the config file."""
    config = get_config()
    console.print(f"  [path]{config.config_path}[/path]")


# ─── Database Commands ────────────────────────────────────────────────────────

db_app = typer.Typer(
    name="db",
    help="Database [cyan]management[/cyan] commands.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
app.add_typer(db_app, name="db")


@db_app.command("stats")
def db_stats() -> None:
    """Show [cyan]database statistics[/cyan]."""
    from asteria.modules.agy.service import AgyService
    from asteria.modules.gemini.service import OutputService

    agy_stats = AgyService.statistics()
    gemini_stats = OutputService.statistics()

    data = {
        "Database path": str(DB_PATH),
        "DB size": _format_size(DB_PATH),
        "─── Agy ───────────────────": "",
        "  Total conversations": str(agy_stats["total"]),
        "  Categories": str(agy_stats["categories"]),
        "─── Gemini ─────────────────": "",
        "  Workspaces": str(gemini_stats["workspaces"]),
        "  Projects": str(gemini_stats["projects"]),
        "  Prompts": str(gemini_stats["prompts"]),
        "  Outputs": str(gemini_stats["outputs"]),
    }
    print_key_value(data, title="Database Statistics")


@db_app.command("backup")
def db_backup(
    output_dir: Optional[Path] = typer.Option(
        None, "--output", "-o", help="Backup directory"
    ),
) -> None:
    """[cyan]Backup[/cyan] the database to a file."""
    import shutil
    from datetime import datetime

    backup_dir = output_dir or BACKUP_DIR
    backup_dir.mkdir(parents=True, exist_ok=True)

    if not DB_PATH.exists():
        print_error("Database not found. Run: asteria init")
        raise typer.Exit(1)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"asteria_{timestamp}.db"

    try:
        shutil.copy2(DB_PATH, backup_path)
        print_success(f"Backup created: [path]{backup_path}[/path]")
    except OSError as exc:
        print_error(f"Backup failed: {exc}")
        raise typer.Exit(1)


@db_app.command("restore")
def db_restore(
    backup_file: Path = typer.Argument(..., help="Path to backup .db file"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """[red]Restore[/red] the database from a backup file (DESTRUCTIVE)."""
    import shutil

    if not backup_file.exists():
        print_error(f"Backup file not found: {backup_file}")
        raise typer.Exit(1)

    if not yes:
        if not confirm_action(
            "Restore will OVERWRITE your current database. Continue?",
            dangerous=True,
        ):
            print_info("Aborted.")
            raise typer.Exit(0)

    try:
        # Close engine connections
        reset_engine()
        shutil.copy2(backup_file, DB_PATH)
        print_success(f"Database restored from: [path]{backup_file}[/path]")
    except OSError as exc:
        print_error(f"Restore failed: {exc}")
        raise typer.Exit(1)


def _format_size(path: Path) -> str:
    """Format a file size in human-readable form."""
    try:
        size = path.stat().st_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
    except OSError:
        return "—"


# ─── Global Commands ──────────────────────────────────────────────────────────


@app.command("version")
def version_cmd() -> None:
    """Show [cyan]version[/cyan] and developer information."""
    data = {
        "Version": __version__,
        "Description": __description__,
        "Author": __author__,
        "Affiliation": "IIT Kanpur",
        "URL": __url__,
        "Copyright": __copyright__,
    }
    print_key_value(data, title="AsteriaCLI")


@app.command("init")
def init_cmd(
    force: bool = typer.Option(
        False, "--force", "-f", help="Re-initialise even if already set up"
    ),
) -> None:
    """[green]Initialise[/green] the database and configuration."""
    print_banner()
    print_section("Initialising AsteriaCLI")

    # Setup config
    config = get_config()
    if not CONFIG_PATH.exists() or force:
        config.initialize()
        print_success(f"Config created: [path]{CONFIG_PATH}[/path]")
    else:
        print_info(f"Config already exists: [path]{CONFIG_PATH}[/path]")

    # Setup logging
    setup_logging(level=config.log_level)

    # Init database
    try:
        init_db()
        print_success(f"Database ready: [path]{DB_PATH}[/path]")
        # Ensure internal workspace and README
        from asteria.modules.gemini.service import WorkspaceService
        ws = WorkspaceService.get_or_create_default_workspace()
        print_success(f"Workspace ready: [path]{ws.path}[/path]")
    except Exception as exc:
        print_error(f"Database init failed: {exc}")
        raise typer.Exit(1)

    print_success("AsteriaCLI is ready! Run [bold white]asteria --help[/bold white] to get started.")


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        None, "--version", "-V", is_eager=True, help="Show version and exit"
    ),
) -> None:
    """[bold cyan]AsteriaCLI[/bold cyan] — Your unified command-line interface for AI workflows.

    \b
    [dim]Developer:[/dim]  Indrajit Ghosh, Postdoctoral Researcher, IIT Kanpur
    [dim]Version:[/dim]    {version_str}

    \b
    Run [bold]asteria init[/bold] to get started.
    Run [bold]asteria --help[/bold] to see all commands.
    """.format(version_str=__version__)

    if version:
        console.print(
            f"[bold cyan]AsteriaCLI[/bold cyan] v[bold white]{__version__}[/bold white]"
        )
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        print_banner()
        console.print(
            "\n  Run [bold cyan]asteria --help[/bold cyan] to see available commands.\n"
            "  Run [bold cyan]asteria init[/bold cyan] to get started.\n"
        )


if __name__ == "__main__":
    app()
