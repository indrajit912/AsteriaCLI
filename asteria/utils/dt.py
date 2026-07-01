"""
Centralised datetime utilities for AsteriaCLI.

All datetime values throughout AsteriaCLI — database records, log entries,
CLI output, and exported data — are produced by :func:`local_now`.  This
makes it trivial to change timezone behaviour application-wide by editing a
single function.

**Current behaviour:** every timestamp reflects the *local machine timezone*
so that dates displayed in the terminal, written to the database, and written
to log files are all consistent with the clock the developer sees on screen.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

from datetime import datetime


def local_now() -> datetime:
    """Return the current local time as a timezone-aware :class:`datetime`.

    ``datetime.now().astimezone()`` attaches the running machine's local
    timezone (e.g., ``+05:30`` for IST) to the naive local time, producing a
    fully timezone-aware value without hard-coding any particular zone.

    This is the **single authoritative source** for "now" across AsteriaCLI.
    All database defaults, log timestamps, CLI display values, and exported
    records call this function, so changing timezone behaviour only ever
    requires editing this one place.

    Returns:
        A timezone-aware :class:`datetime` representing the current local time.

    Example::

        >>> from asteria.utils.dt import local_now
        >>> ts = local_now()
        >>> print(ts)          # e.g. 2026-06-30 17:20:46.123456+05:30
        >>> print(ts.tzname()) # e.g. 'India Standard Time' or 'IST'
    """
    return datetime.now().astimezone()


def format_local(
    dt: datetime | None,
    fmt: str = "%Y-%m-%d %H:%M",
    *,
    include_tz: bool = False,
) -> str:
    """Format a :class:`datetime` for human-readable CLI display.

    If *dt* is timezone-aware it is displayed as-is (no conversion).
    If *dt* is naive (e.g., read from an older database row) it is treated as
    local time.

    Args:
        dt:         Datetime to format, or ``None``.
        fmt:        :meth:`~datetime.datetime.strftime` format string.
                    Defaults to ``"%Y-%m-%d %H:%M"``.
        include_tz: When *True*, ``" %Z"`` is appended so the timezone
                    abbreviation (e.g., ``IST``) appears in the output.

    Returns:
        Formatted string, or ``"—"`` when *dt* is ``None``.
    """
    if dt is None:
        return "\u2014"  # em-dash
    effective_fmt = fmt + " %Z" if include_tz else fmt
    return dt.strftime(effective_fmt)
