"""
Rich console utilities for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import io
import os
import sys
from typing import Any, Optional

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from asteria.version import __author__, __version__

# ─── Custom Theme ─────────────────────────────────────────────────────────────

ASTERIA_THEME = Theme(
    {
        "primary": "bold cyan",
        "success": "bold green",
        "error": "bold red",
        "warning": "bold yellow",
        "info": "blue",
        "dim": "dim white",
        "header": "bold white",
        "table.header": "bold magenta",
        "id": "dim cyan",
        "tag": "bold bright_cyan",
        "category": "bold yellow",
        "title": "bold white",
        "path": "dim green",
        "timestamp": "dim",
    }
)

# ─── Global Console ───────────────────────────────────────────────────────────
# Force UTF-8 output to avoid Windows cp1252 encoding errors.

def _make_console(stderr: bool = False) -> Console:
    """Create a Rich console with UTF-8 safe output."""
    # Wrap the standard stream in a UTF-8 writer when needed
    stream = sys.stderr if stderr else sys.stdout
    try:
        # Try to reconfigure to utf-8 (Python 3.7+)
        stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass
    return Console(
        theme=ASTERIA_THEME,
        stderr=stderr,
        highlight=True,
    )

console = _make_console(stderr=False)
err_console = _make_console(stderr=True)



# ─── Banner & Headings ────────────────────────────────────────────────────────


def print_banner() -> None:
    """Print the AsteriaCLI welcome banner."""
    panel = Panel(
        f"\n[bold bright_cyan]  *  AsteriaCLI[/bold bright_cyan]  [bold cyan]*[/bold cyan]\n\n"
        f"  [dim white]Your unified interface for AI workflows[/dim white]\n\n"
        f"  [dim cyan]v{__version__}[/dim cyan]  [dim]|[/dim]  [dim white]{__author__}[/dim white]  "
        f"[dim]|[/dim]  [dim white]IIT Kanpur[/dim white]\n",
        border_style="cyan",
        padding=(0, 2),
    )
    console.print(panel)


def print_section(title: str, style: str = "primary") -> None:
    """Print a section separator with a title.

    Args:
        title: Section title text.
        style: Rich style string for the rule.
    """
    console.print(Rule(f"[{style}]{title}[/{style}]", style=style))


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Message text.
    """
    console.print(f"[success][OK][/success] {message}")


def print_error(message: str) -> None:
    """Print an error message.

    Args:
        message: Message text.
    """
    err_console.print(f"[error][ERROR][/error] {message}")


def print_warning(message: str) -> None:
    """Print a warning message.

    Args:
        message: Message text.
    """
    console.print(f"[warning][WARN][/warning] {message}")


def print_info(message: str) -> None:
    """Print an informational message.

    Args:
        message: Message text.
    """
    console.print(f"[info][INFO][/info] {message}")


def print_panel(
    content: str,
    title: str = "",
    border_style: str = "cyan",
    padding: tuple[int, int] = (1, 2),
) -> None:
    """Print content inside a Rich panel.

    Args:
        content: Panel content (supports Rich markup).
        title: Optional panel title.
        border_style: Border color/style.
        padding: Padding as (vertical, horizontal).
    """
    panel = Panel(
        content,
        title=f"[bold]{title}[/bold]" if title else None,
        border_style=border_style,
        padding=padding,
    )
    console.print(panel)


# ─── Confirmation Dialogs ─────────────────────────────────────────────────────


def confirm_action(
    message: str,
    default: bool = False,
    dangerous: bool = False,
) -> bool:
    """Prompt the user for confirmation.

    Args:
        message: Confirmation question text.
        default: Default choice (True=yes, False=no).
        dangerous: If True, styles the prompt in red.

    Returns:
        True if user confirmed, False otherwise.
    """
    style = "error" if dangerous else "warning"
    styled_message = f"[{style}]{message}[/{style}]"
    return Confirm.ask(styled_message, default=default, console=console)


def prompt_input(
    message: str,
    default: Optional[str] = None,
    password: bool = False,
) -> str:
    """Prompt the user for text input.

    Args:
        message: Prompt text.
        default: Default value.
        password: Whether to hide input.

    Returns:
        User-provided string value.
    """
    return Prompt.ask(
        f"[primary]{message}[/primary]",
        default=default or "",
        password=password,
        console=console,
    )


# ─── Tables ───────────────────────────────────────────────────────────────────


def make_table(
    title: Optional[str] = None,
    box_style: box.Box = box.ROUNDED,
    show_header: bool = True,
    header_style: str = "table.header",
    border_style: str = "dim cyan",
    show_lines: bool = False,
) -> Table:
    """Create a styled Rich table.

    Args:
        title: Optional table title.
        box_style: Box drawing style.
        show_header: Whether to show column headers.
        header_style: Style for header row.
        border_style: Border style.
        show_lines: Whether to show row separators.

    Returns:
        Configured Rich Table.
    """
    return Table(
        title=f"[bold]{title}[/bold]" if title else None,
        box=box_style,
        show_header=show_header,
        header_style=header_style,
        border_style=border_style,
        show_lines=show_lines,
        padding=(0, 1),
    )


# ─── Progress Spinners ────────────────────────────────────────────────────────


def make_spinner(description: str = "Working...") -> Progress:
    """Create a Rich progress spinner.

    Args:
        description: Text shown beside the spinner.

    Returns:
        Rich Progress instance (use as context manager).
    """
    return Progress(
        SpinnerColumn(style="primary"),
        TextColumn("[primary]{task.description}"),
        TimeElapsedColumn(),
        console=console,
        transient=True,
    )


def make_progress_bar() -> Progress:
    """Create a Rich progress bar.

    Returns:
        Rich Progress instance (use as context manager).
    """
    return Progress(
        SpinnerColumn(style="primary"),
        TextColumn("[primary]{task.description}"),
        BarColumn(bar_width=40, style="cyan", complete_style="bright_cyan"),
        TextColumn("[dim]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    )


# ─── Syntax Highlighting ──────────────────────────────────────────────────────


def print_syntax(
    code: str,
    language: str = "python",
    theme: str = "monokai",
    line_numbers: bool = False,
) -> None:
    """Print syntax-highlighted code.

    Args:
        code: Source code string.
        language: Language identifier for highlighting.
        theme: Pygments colour theme.
        line_numbers: Whether to show line numbers.
    """
    syntax = Syntax(
        code,
        language,
        theme=theme,
        line_numbers=line_numbers,
        padding=(1, 2),
    )
    console.print(syntax)


# ─── Key-Value Display ────────────────────────────────────────────────────────


def print_key_value(
    data: dict[str, Any],
    title: Optional[str] = None,
) -> None:
    """Display a dictionary as a formatted key-value panel.

    Args:
        data: Dictionary of key-value pairs.
        title: Optional panel title.
    """
    lines = []
    for key, value in data.items():
        key_str = f"[dim white]{key:.<25}[/dim white]"
        val_str = f"[white]{value}[/white]"
        lines.append(f"  {key_str} {val_str}")
    content = "\n".join(lines)
    print_panel(content, title=title or "Details", border_style="cyan")


def print_no_results(entity: str = "records") -> None:
    """Print a styled 'no results' message.

    Args:
        entity: What kind of entity was searched.
    """
    console.print(
        f"\n  [dim]No {entity} found.[/dim]\n"
    )


def truncate(text: str, max_len: int = 60, suffix: str = "…") -> str:
    """Truncate a string to a maximum length.

    Args:
        text: Input string.
        max_len: Maximum allowed length.
        suffix: Suffix appended when truncated.

    Returns:
        Potentially truncated string.
    """
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix
