"""
Logging configuration for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.logging import RichHandler

from asteria.constants import LOG_PATH


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    rich_console: bool = True,
) -> logging.Logger:
    """Configure application-wide logging.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_file: Optional path to a log file. Defaults to APP_DIR/asteria.log.
        rich_console: Whether to use Rich for console log output.

    Returns:
        Configured root logger.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    log_file = log_file or LOG_PATH

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handlers: list[logging.Handler] = []

    # ─── Console Handler ──────────────────────────────────────────────────────
    if rich_console:
        console_handler = RichHandler(
            rich_tracebacks=True,
            show_path=False,
            markup=True,
        )
        console_handler.setLevel(logging.WARNING)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)

    handlers.append(console_handler)

    # ─── File Handler ─────────────────────────────────────────────────────────
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    handlers.append(file_handler)

    # ─── Root Logger ─────────────────────────────────────────────────────────
    logging.basicConfig(
        level=log_level,
        handlers=handlers,
        force=True,
    )

    logger = logging.getLogger("asteria")
    logger.setLevel(log_level)
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a named child logger under the 'asteria' namespace.

    Args:
        name: Logger name (will be prefixed with 'asteria.').

    Returns:
        Named logger instance.
    """
    return logging.getLogger(f"asteria.{name}")
