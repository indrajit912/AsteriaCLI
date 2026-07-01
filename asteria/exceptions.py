"""
Custom exceptions for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""


class AsteriaError(Exception):
    """Base exception for all AsteriaCLI errors."""

    pass


# ─── Configuration Errors ────────────────────────────────────────────────────


class ConfigError(AsteriaError):
    """Raised when there is a configuration-related error."""

    pass


class ConfigNotFoundError(ConfigError):
    """Raised when configuration file is not found."""

    pass


class ConfigInvalidError(ConfigError):
    """Raised when configuration file has invalid content."""

    pass


# ─── Database Errors ─────────────────────────────────────────────────────────


class DatabaseError(AsteriaError):
    """Raised when there is a database-related error."""

    pass


class DatabaseNotInitializedError(DatabaseError):
    """Raised when the database has not been initialized."""

    pass


class RecordNotFoundError(DatabaseError):
    """Raised when a record is not found in the database."""

    def __init__(self, record_type: str, identifier: str) -> None:
        self.record_type = record_type
        self.identifier = identifier
        super().__init__(f"{record_type} not found: '{identifier}'")


class DuplicateRecordError(DatabaseError):
    """Raised when attempting to create a duplicate record."""

    def __init__(self, record_type: str, identifier: str) -> None:
        self.record_type = record_type
        self.identifier = identifier
        super().__init__(
            f"{record_type} already exists: '{identifier}'"
        )


# ─── Module Errors ───────────────────────────────────────────────────────────


class ModuleError(AsteriaError):
    """Raised when there is a module-related error."""

    pass


class AgyError(ModuleError):
    """Raised for Agy module errors."""

    pass


class GeminiError(ModuleError):
    """Raised for Gemini module errors."""

    pass


class GeminiAPIError(GeminiError):
    """Raised when the Gemini API returns an error."""

    pass


class GeminiRunnerError(GeminiError):
    """Raised when there is an error running a Gemini prompt."""

    pass


# ─── File Errors ─────────────────────────────────────────────────────────────


class FileError(AsteriaError):
    """Raised when there is a file-related error."""

    pass


class FileNotFoundError(FileError):
    """Raised when a required file is not found."""

    pass


class FilePermissionError(FileError):
    """Raised when there is insufficient file permissions."""

    pass


# ─── Editor Errors ───────────────────────────────────────────────────────────


class EditorError(AsteriaError):
    """Raised when there is an error launching the editor."""

    pass


class EditorNotFoundError(EditorError):
    """Raised when the configured editor is not found."""

    pass


# ─── Export/Import Errors ────────────────────────────────────────────────────


class ExportError(AsteriaError):
    """Raised when there is an export error."""

    pass


class ImportError(AsteriaError):
    """Raised when there is an import error."""

    pass


# ─── Search Errors ───────────────────────────────────────────────────────────


class SearchError(AsteriaError):
    """Raised when there is a search-related error."""

    pass


class NoResultsFoundError(SearchError):
    """Raised when a search returns no results."""

    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(f"No results found for query: '{query}'")
