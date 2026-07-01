"""
Agy CLI commands for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.panel import Panel
from rich.text import Text

from asteria.constants import AGY_CATEGORIES, SUPPORTED_EXPORT_FORMATS
from asteria.exceptions import AgyError, RecordNotFoundError, DuplicateRecordError
from asteria.modules.agy.service import AgyService
from asteria.utils.console import (
    confirm_action,
    console,
    make_table,
    print_error,
    print_info,
    print_key_value,
    print_no_results,
    print_panel,
    print_section,
    print_success,
    print_warning,
    prompt_input,
)
from asteria.utils.formatting import format_datetime, format_tags, short_id, truncate

# ─── Typer App ────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="agy",
    help="[cyan]Manage Gemini Antigravity CLI conversations.[/cyan]",
    rich_markup_mode="rich",
    no_args_is_help=True,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _find_conversation_id(identifier: str) -> str:
    """Resolve a short ID or full UUID to a database record ID.

    Args:
        identifier: Full UUID, short ID prefix, or conversation_id.

    Returns:
        Full record UUID.

    Raises:
        typer.Exit: If not found.
    """
    # Try exact UUID match first
    try:
        conv = AgyService.get_conversation(identifier)
        return conv.id
    except RecordNotFoundError:
        pass

    # Try prefix search
    all_convs = AgyService.list_conversations()
    matches = [c for c in all_convs if c.id.startswith(identifier)]
    if len(matches) == 1:
        return matches[0].id
    if len(matches) > 1:
        print_error(f"Ambiguous short ID '{identifier}' matches multiple records.")
        raise typer.Exit(1)

    # Try conversation_id match
    matches = [c for c in all_convs if identifier in c.conversation_id]
    if len(matches) == 1:
        return matches[0].id
    if len(matches) > 1:
        print_error(f"Multiple conversations match '{identifier}'.")
        raise typer.Exit(1)

    print_error(f"No conversation found with ID: '{identifier}'")
    raise typer.Exit(1)


def _display_conversations_table(
    conversations: list,
    title: str = "Agy Conversations",
) -> None:
    """Render conversations as a Rich table.

    Args:
        conversations: List of AgyConversation instances.
        title: Table title.
    """
    if not conversations:
        print_no_results("conversations")
        return

    table = make_table(title=title, show_lines=True)
    table.add_column("#", style="dim", width=4, no_wrap=True)
    table.add_column("Short ID", style="id", width=10, no_wrap=True)
    table.add_column("Title", style="title", min_width=20, max_width=40, overflow="fold")
    table.add_column("Category", style="category", width=14, no_wrap=True)
    table.add_column("Tags", style="tag", min_width=15, max_width=25, overflow="fold")
    table.add_column("Conversation ID", style="dim cyan", min_width=20, max_width=35, overflow="fold")
    table.add_column("Updated", style="timestamp", width=17, no_wrap=True)

    for idx, conv in enumerate(conversations, start=1):
        table.add_row(
            str(idx),
            short_id(conv.id),
            conv.title,
            conv.category,
            conv.tags_display,
            conv.conversation_id,
            format_datetime(conv.updated_at, "%Y-%m-%d %H:%M"),
        )
    console.print(table)
    console.print(
        f"  [dim]Total: {len(conversations)} conversation(s)[/dim]\n"
    )


# ─── Commands ────────────────────────────────────────────────────────────────


@app.command("add")
def add_conversation(
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Conversation title"),
    conversation_id: Optional[str] = typer.Option(
        None, "--conv-id", "-c", help="Antigravity CLI conversation ID"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-k", help="Category label"
    ),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="Description"
    ),
    tags: Optional[str] = typer.Option(
        None, "--tags", help="Comma-separated tags (e.g. python,research)"
    ),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="Notes"),
) -> None:
    """[green]Add[/green] a new Agy conversation to the database."""
    print_section("Add Agy Conversation")

    # Interactive prompts for missing required fields
    if not title:
        title = prompt_input("Title")
    if not conversation_id:
        conversation_id = prompt_input("Conversation ID (from Antigravity CLI)")
    if not category:
        console.print(
            f"  [dim]Categories: {', '.join(AGY_CATEGORIES)}[/dim]"
        )
        category = prompt_input("Category", default="General")

    try:
        conv = AgyService.add_conversation(
            title=title,
            conversation_id=conversation_id,
            category=category,
            description=description,
            tags=tags,
            notes=notes,
        )
        print_success(
            f"Conversation added: [bold white]{conv.title}[/bold white] "
            f"[dim](ID: {short_id(conv.id)})[/dim]"
        )
    except DuplicateRecordError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Failed to add conversation: {exc}")
        raise typer.Exit(1)


@app.command("list")
def list_conversations(
    category: Optional[str] = typer.Option(
        None, "--category", "-k", help="Filter by category"
    ),
    sort_by: str = typer.Option(
        "created_at", "--sort-by", "-s", help="Sort field (created_at, updated_at, title)"
    ),
    asc: bool = typer.Option(False, "--asc", help="Sort ascending"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    page_size: int = typer.Option(20, "--page-size", help="Items per page"),
) -> None:
    """[cyan]List[/cyan] all Agy conversations."""
    try:
        convs = AgyService.list_conversations(
            category=category,
            order_by=sort_by,
            descending=not asc,
        )
        # Pagination
        total = len(convs)
        start = (page - 1) * page_size
        end = start + page_size
        page_convs = convs[start:end]

        title = "Agy Conversations"
        if category:
            title += f" — {category}"
        if total > page_size:
            title += f" (page {page}/{(total + page_size - 1) // page_size})"

        _display_conversations_table(page_convs, title=title)

        if total > end:
            print_info(
                f"Showing {start + 1}–{min(end, total)} of {total}. "
                f"Use --page {page + 1} for next page."
            )
    except Exception as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("show")
def show_conversation(
    identifier: str = typer.Argument(
        ..., help="Record UUID or short ID or conversation ID"
    ),
) -> None:
    """[cyan]Show[/cyan] full details of a conversation."""
    record_id = _find_conversation_id(identifier)
    try:
        conv = AgyService.get_conversation(record_id)
        data = {
            "Record ID": conv.id,
            "Title": conv.title,
            "Category": conv.category,
            "Conversation ID": conv.conversation_id,
            "Description": conv.description or "—",
            "Tags": conv.tags_display,
            "Notes": conv.notes or "—",
            "Created": format_datetime(conv.created_at),
            "Updated": format_datetime(conv.updated_at),
        }
        print_section("Conversation Details")
        print_key_value(data, title=conv.title)
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("edit")
def edit_conversation(
    identifier: str = typer.Argument(
        ..., help="Record UUID or short ID"
    ),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="New title"),
    description: Optional[str] = typer.Option(
        None, "--description", "-d", help="New description"
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-k", help="New category"
    ),
    conversation_id: Optional[str] = typer.Option(
        None, "--conv-id", "-c", help="New conversation ID"
    ),
    tags: Optional[str] = typer.Option(None, "--tags", help="New comma-separated tags"),
    notes: Optional[str] = typer.Option(None, "--notes", "-n", help="New notes"),
) -> None:
    """[yellow]Edit[/yellow] an existing Agy conversation."""
    record_id = _find_conversation_id(identifier)
    try:
        conv = AgyService.edit_conversation(
            record_id=record_id,
            title=title,
            description=description,
            category=category,
            conversation_id=conversation_id,
            tags=tags,
            notes=notes,
        )
        print_success(
            f"Conversation updated: [bold white]{conv.title}[/bold white]"
        )
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Edit failed: {exc}")
        raise typer.Exit(1)


@app.command("delete")
def delete_conversation(
    identifier: str = typer.Argument(
        ..., help="Record UUID or short ID"
    ),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """[red]Delete[/red] an Agy conversation."""
    record_id = _find_conversation_id(identifier)
    try:
        conv = AgyService.get_conversation(record_id)
        if not yes:
            confirmed = confirm_action(
                f"Delete conversation '{conv.title}'?",
                dangerous=True,
            )
            if not confirmed:
                print_info("Aborted.")
                raise typer.Exit(0)
        AgyService.delete_conversation(record_id)
        print_success(f"Deleted: [bold white]{conv.title}[/bold white]")
    except RecordNotFoundError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("search")
def search_conversations(
    query: str = typer.Argument(..., help="Search query"),
    fuzzy: bool = typer.Option(True, "--fuzzy/--no-fuzzy", help="Enable fuzzy search"),
    category: Optional[str] = typer.Option(
        None, "--category", "-k", help="Limit to category"
    ),
) -> None:
    """[cyan]Search[/cyan] conversations by title, description, tags, or conversation ID."""
    try:
        results = AgyService.search_conversations(query=query, fuzzy=fuzzy)
        if category:
            results = [r for r in results if r.category.lower() == category.lower()]
        _display_conversations_table(
            results,
            title=f'Search: "{query}"',
        )
    except Exception as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("export")
def export_conversations(
    output: Path = typer.Option(
        Path("agy_export.json"),
        "--output",
        "-o",
        help="Output file path",
    ),
    fmt: str = typer.Option(
        "json",
        "--format",
        "-f",
        help=f"Export format: {', '.join(SUPPORTED_EXPORT_FORMATS)}",
    ),
    category: Optional[str] = typer.Option(
        None, "--category", "-k", help="Filter by category"
    ),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing file"),
) -> None:
    """[cyan]Export[/cyan] conversations to JSON or CSV."""
    try:
        result_path = AgyService.export_conversations(
            output_path=output,
            fmt=fmt,
            category=category,
            overwrite=overwrite,
        )
        print_success(f"Exported to: [path]{result_path}[/path]")
    except FileExistsError as exc:
        print_error(str(exc))
        raise typer.Exit(1)
    except Exception as exc:
        print_error(f"Export failed: {exc}")
        raise typer.Exit(1)


@app.command("import")
def import_conversations(
    source: Path = typer.Argument(..., help="Path to JSON import file"),
) -> None:
    """[cyan]Import[/cyan] conversations from a JSON file."""
    if not source.exists():
        print_error(f"File not found: {source}")
        raise typer.Exit(1)
    try:
        imported, skipped = AgyService.import_conversations(source)
        print_success(
            f"Import complete: [bold green]{imported}[/bold green] added, "
            f"[dim]{skipped}[/dim] skipped."
        )
    except AgyError as exc:
        print_error(str(exc))
        raise typer.Exit(1)


@app.command("stats")
def show_stats() -> None:
    """Show [cyan]statistics[/cyan] about Agy conversations."""
    try:
        stats = AgyService.statistics()
        data = {
            "Total conversations": str(stats["total"]),
            "Total categories": str(stats["categories"]),
        }
        for cat, count in stats.get("by_category", {}).items():
            data[f"  {cat}"] = str(count)
        print_key_value(data, title="Agy Statistics")
    except Exception as exc:
        print_error(str(exc))
        raise typer.Exit(1)
