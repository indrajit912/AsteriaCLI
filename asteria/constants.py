"""
Global constants for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import os
from pathlib import Path

# ─── Application Directories ────────────────────────────────────────────────

APP_NAME = "AsteriaCLI"
APP_DIR = Path.home() / ".asteria"
DB_PATH = APP_DIR / "asteria.db"
CONFIG_PATH = APP_DIR / "config.toml"
LOG_PATH = APP_DIR / "asteria.log"
BACKUP_DIR = APP_DIR / "backups"

# ─── Database ────────────────────────────────────────────────────────────────

DATABASE_URL = f"sqlite:///{DB_PATH}"

# ─── Agy Constants ───────────────────────────────────────────────────────────

AGY_DEFAULT_CATEGORY = "General"
AGY_CATEGORIES = [
    "General",
    "Coding",
    "Research",
    "Writing",
    "Analysis",
    "Creative",
    "Math",
    "Science",
    "Other",
]

# ─── Gemini Constants ─────────────────────────────────────────────────────────

GEMINI_DEFAULT_MODEL = "gemini-2.5-flash"
GEMINI_PROMPTS_DIR = "prompts"
GEMINI_OUTPUTS_DIR = "outputs"

# ─── Internal Workspace ─────────────────────────────────────────────────────
# Dedicated workspace managed exclusively by AsteriaCLI to store Gemini data.
# Location: ~/.asteria/.asteria_workspace (or %USERPROFILE%\\.asteria\\.asteria_workspace on Windows)
# This directory is created automatically and should not be modified manually.
INTERNAL_WORKSPACE_DIR = APP_DIR / ".asteria_workspace"

# ─── Editor Constants ────────────────────────────────────────────────────────

SUPPORTED_EDITORS = {
    "vim": "vim",
    "nano": "nano",
    "vscode": "code",
    "notepad++": "notepad++",
    "notepad": "notepad",
    "emacs": "emacs",
    "gedit": "gedit",
}

DEFAULT_EDITOR = "vim"

# ─── UI Constants ────────────────────────────────────────────────────────────

DEFAULT_PAGE_SIZE = 20
MAX_DESCRIPTION_DISPLAY = 80
MAX_TITLE_DISPLAY = 50

# ─── Export Formats ──────────────────────────────────────────────────────────

EXPORT_FORMAT_JSON = "json"
EXPORT_FORMAT_CSV = "csv"
SUPPORTED_EXPORT_FORMATS = [EXPORT_FORMAT_JSON, EXPORT_FORMAT_CSV]

# ─── Fuzzy Search ────────────────────────────────────────────────────────────

FUZZY_SEARCH_THRESHOLD = 60  # Minimum similarity score (0-100)

# ─── Colors & Styling ────────────────────────────────────────────────────────

STYLE_PRIMARY = "bold cyan"
STYLE_SUCCESS = "bold green"
STYLE_ERROR = "bold red"
STYLE_WARNING = "bold yellow"
STYLE_INFO = "blue"
STYLE_DIM = "dim"
STYLE_HEADER = "bold white on dark_blue"
STYLE_TABLE_HEADER = "bold magenta"
