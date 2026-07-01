"""
Formatting utilities for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from asteria.utils.dt import format_local, local_now


def format_datetime(
    dt: Optional[datetime],
    fmt: str = "%Y-%m-%d %H:%M",
    *,
    include_tz: bool = False,
) -> str:
    """Format a datetime object to a localised display string.

    Delegates to :func:`asteria.utils.dt.format_local`, the single
    authoritative formatter for all user-facing timestamps.

    Args:
        dt:         Datetime object (may be ``None``).
        fmt:        :meth:`~datetime.datetime.strftime` format string.
        include_tz: Append the local timezone abbreviation (e.g., ``IST``).

    Returns:
        Formatted string, or ``'\u2014'`` (em-dash) if *dt* is ``None``.
    """
    return format_local(dt, fmt, include_tz=include_tz)


def format_tags(tags: list[str]) -> str:
    """Format a list of tags as a comma-separated string.

    Args:
        tags: List of tag strings.

    Returns:
        Comma-separated tag string or '—' if empty.
    """
    if not tags:
        return "—"
    return ", ".join(f"#{t}" for t in tags)


def truncate(text: str, max_len: int = 60, suffix: str = "…") -> str:
    """Truncate a string to a maximum display length.

    Args:
        text: Input string.
        max_len: Maximum allowed length.
        suffix: Appended when truncated.

    Returns:
        Truncated string.
    """
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def short_id(uuid: str, length: int = 8) -> str:
    """Return a shortened UUID prefix for display.

    Args:
        uuid: Full UUID string.
        length: Number of characters to show.

    Returns:
        Shortened UUID string.
    """
    return uuid[:length] if uuid else "—"


def parse_tags(tags_str: str) -> list[str]:
    """Parse a comma-separated tag string into a list.

    Args:
        tags_str: Comma-separated tag string.

    Returns:
        List of cleaned tag strings.
    """
    if not tags_str:
        return []
    return [t.strip().lstrip("#").lower() for t in tags_str.split(",") if t.strip()]


def records_to_json(records: list[dict[str, Any]], indent: int = 2) -> str:
    """Serialize a list of record dictionaries to JSON.

    Args:
        records: List of dictionaries.
        indent: JSON indentation level.

    Returns:
        JSON string.
    """
    return json.dumps(records, indent=indent, ensure_ascii=False, default=str)


def records_to_csv(records: list[dict[str, Any]]) -> str:
    """Serialize a list of record dictionaries to CSV.

    Args:
        records: List of dictionaries with uniform keys.

    Returns:
        CSV string.
    """
    if not records:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(records[0].keys()))
    writer.writeheader()
    writer.writerows(records)
    return output.getvalue()


def write_export_file(
    content: str,
    path: Path,
    overwrite: bool = False,
) -> Path:
    """Write content to an export file.

    Args:
        content: Text content to write.
        path: Destination path.
        overwrite: Whether to overwrite an existing file.

    Returns:
        The resolved output path.

    Raises:
        FileExistsError: If path exists and overwrite is False.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"Export file already exists: {path}. "
            "Use --overwrite to replace it."
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def pluralise(count: int, singular: str, plural: Optional[str] = None) -> str:
    """Return a pluralised noun based on count.

    Args:
        count: Item count.
        singular: Singular form.
        plural: Optional plural form (defaults to singular + 's').

    Returns:
        Appropriate form of the noun.
    """
    if count == 1:
        return singular
    return plural or f"{singular}s"
