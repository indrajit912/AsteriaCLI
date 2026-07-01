"""
Editor launch utilities for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional

from asteria.constants import SUPPORTED_EDITORS, DEFAULT_EDITOR
from asteria.exceptions import EditorError, EditorNotFoundError

logger = logging.getLogger("asteria.utils.editor")


def get_editor_command(editor_name: str) -> Optional[str]:
    """Resolve an editor name to an executable command.

    Args:
        editor_name: Short editor name (e.g., 'vim', 'vscode').

    Returns:
        Executable command string, or None if not found.
    """
    # Direct mapping from constants
    cmd = SUPPORTED_EDITORS.get(editor_name.lower())
    if cmd and shutil.which(cmd):
        return cmd

    # Fallback: try the name directly
    if shutil.which(editor_name):
        return editor_name

    # Windows-specific: check common install paths
    if sys.platform == "win32":
        win_paths = {
            "notepad++": [
                r"C:\Program Files\Notepad++\notepad++.exe",
                r"C:\Program Files (x86)\Notepad++\notepad++.exe",
            ],
            "vscode": [
                r"C:\Users\{}\AppData\Local\Programs\Microsoft VS Code\Code.exe".format(
                    os.environ.get("USERNAME", "")
                ),
                r"C:\Program Files\Microsoft VS Code\Code.exe",
            ],
        }
        for path_list in win_paths.get(editor_name.lower(), []):
            if Path(path_list).exists():
                return path_list

    return None


def open_editor(filepath: Path, editor: Optional[str] = None) -> None:
    """Open a file in the configured editor.

    If the editor is not specified, falls back to the EDITOR environment
    variable, then to the platform default (notepad on Windows, vim elsewhere).

    Args:
        filepath: Path to the file to open.
        editor: Optional editor name or command.

    Raises:
        EditorNotFoundError: If the editor cannot be found.
        EditorError: If the editor process fails.
    """
    # Resolve editor
    editor_name = (
        editor
        or os.environ.get("EDITOR")
        or os.environ.get("VISUAL")
        or DEFAULT_EDITOR
    )

    cmd = get_editor_command(editor_name)
    if not cmd:
        # On Windows fall back to notepad
        if sys.platform == "win32":
            cmd = "notepad"
        else:
            raise EditorNotFoundError(
                f"Editor '{editor_name}' not found. "
                "Set a valid editor in your config or EDITOR environment variable."
            )

    try:
        logger.debug("Opening editor: %s %s", cmd, filepath)
        subprocess.run([cmd, str(filepath)], check=True)
    except FileNotFoundError as exc:
        raise EditorNotFoundError(
            f"Editor command '{cmd}' not found on PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise EditorError(
            f"Editor exited with non-zero status: {exc.returncode}"
        ) from exc


def edit_content_in_editor(
    content: str = "",
    suffix: str = ".txt",
    editor: Optional[str] = None,
) -> str:
    """Open editor with temporary content and return modified text.

    Creates a temporary file, opens it in the editor, and returns
    the content after the editor is closed.

    Args:
        content: Initial file content.
        suffix: File extension for the temp file.
        editor: Optional editor name override.

    Returns:
        The edited file content as a string.

    Raises:
        EditorError: If editing fails.
    """
    # Create temp file
    with tempfile.NamedTemporaryFile(
        mode="w",
        suffix=suffix,
        encoding="utf-8",
        delete=False,
    ) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        open_editor(tmp_path, editor=editor)
        return tmp_path.read_text(encoding="utf-8")
    finally:
        tmp_path.unlink(missing_ok=True)
