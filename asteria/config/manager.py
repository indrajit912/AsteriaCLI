"""
Configuration management for AsteriaCLI.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import logging
from pathlib import Path
from typing import Any, Optional

import toml
import tomli_w

from asteria.constants import (
    APP_DIR,
    CONFIG_PATH,
    DEFAULT_EDITOR,
    GEMINI_DEFAULT_MODEL,
    AGY_DEFAULT_CATEGORY,
    INTERNAL_WORKSPACE_DIR,
)
from asteria.exceptions import ConfigError, ConfigNotFoundError, ConfigInvalidError

logger = logging.getLogger("asteria.config")

# ─── Default Configuration ────────────────────────────────────────────────────

DEFAULT_CONFIG: dict[str, Any] = {
    "general": {
        "default_editor": DEFAULT_EDITOR,
        "log_level": "INFO",
        "page_size": 20,
        "date_format": "%Y-%m-%d %H:%M",
    },
    "gemini": {
        "api_key": "",
        "default_model": GEMINI_DEFAULT_MODEL,
        "output_suffix": "",
        "temperature": 0.7,
        "max_output_tokens": 8192,
    },
    "agy": {
        "default_category": AGY_DEFAULT_CATEGORY,
    },
    "ui": {
        "color_primary": "cyan",
        "color_success": "green",
        "color_error": "red",
        "color_warning": "yellow",
        "show_timestamps": True,
        "show_ids": False,
    },
    "database": {
        "backup_count": 5,
        "auto_backup": False,
    },
}


class ConfigManager:
    """Manages AsteriaCLI configuration stored as TOML.

    The configuration is stored in ~/.asteria/config.toml and provides
    typed access to all configuration values with sensible defaults.

    Attributes:
        config_path: Path to the configuration file.
        _data: The loaded configuration dictionary.
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        """Initialize ConfigManager.

        Args:
            config_path: Optional override for config file path.
        """
        self.config_path = config_path or CONFIG_PATH
        self._data: dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from file, creating defaults if not found."""
        if not self.config_path.exists():
            logger.debug("Config file not found; using defaults.")
            self._data = self._deep_copy(DEFAULT_CONFIG)
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded = toml.load(f)
            # Merge with defaults so new keys are always present
            self._data = self._deep_merge(
                self._deep_copy(DEFAULT_CONFIG), loaded
            )
            logger.debug("Configuration loaded from %s", self.config_path)
        except toml.TomlDecodeError as exc:
            raise ConfigInvalidError(
                f"Invalid TOML in config file: {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigError(
                f"Cannot read config file: {exc}"
            ) from exc

    def save(self) -> None:
        """Persist configuration to disk."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self.config_path, "wb") as f:
                tomli_w.dump(self._data, f)
            logger.debug("Configuration saved to %s", self.config_path)
        except OSError as exc:
            raise ConfigError(f"Cannot write config file: {exc}") from exc

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., 'general.default_editor').
            default: Default value if key is not found.

        Returns:
            The configuration value, or default.
        """
        parts = key.split(".")
        data = self._data
        for part in parts:
            if not isinstance(data, dict) or part not in data:
                return default
            data = data[part]
        return data

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value using dot notation.

        Args:
            key: Dot-separated key path (e.g., 'general.default_editor').
            value: Value to set.
        """
        parts = key.split(".")
        data = self._data
        for part in parts[:-1]:
            if part not in data or not isinstance(data[part], dict):
                data[part] = {}
            data = data[part]
        data[parts[-1]] = value
        logger.debug("Config key '%s' set to '%s'", key, value)

    def get_section(self, section: str) -> dict[str, Any]:
        """Get an entire configuration section.

        Args:
            section: Top-level section name.

        Returns:
            Dictionary of section values.
        """
        return self._data.get(section, {})

    def all(self) -> dict[str, Any]:
        """Return the full configuration dictionary.

        Returns:
            Complete configuration data.
        """
        return self._data

    def initialize(self) -> None:
        """Create the default config file if it does not exist."""
        if self.config_path.exists():
            logger.debug("Config already exists; skipping init.")
            return
        self._data = self._deep_copy(DEFAULT_CONFIG)
        self.save()
        logger.info("Default configuration created at %s", self.config_path)

    # ─── Convenience Properties ───────────────────────────────────────────────

    @property
    def default_editor(self) -> str:
        """Return the configured default editor."""
        return self.get("general.default_editor", DEFAULT_EDITOR)

    @property
    def log_level(self) -> str:
        """Return the configured log level."""
        return self.get("general.log_level", "INFO")

    @property
    def page_size(self) -> int:
        """Return the configured page size for listings."""
        return self.get("general.page_size", 20)

    @property
    def gemini_api_key(self) -> str:
        """Return the Gemini API key."""
        return self.get("gemini.api_key", "")

    @property
    def gemini_model(self) -> str:
        """Return the default Gemini model."""
        return self.get("gemini.default_model", GEMINI_DEFAULT_MODEL)

    @property
    def default_workspace(self) -> str:
        """Return the internal managed Gemini workspace path.

        This overrides any configuration value and always points to
        the dedicated workspace located at ``INTERNAL_WORKSPACE_DIR``.
        """
        from asteria.constants import INTERNAL_WORKSPACE_DIR
        return str(INTERNAL_WORKSPACE_DIR)

    # ─── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _deep_copy(data: dict[str, Any]) -> dict[str, Any]:
        """Return a deep copy of a dictionary."""
        import copy
        return copy.deepcopy(data)

    @staticmethod
    def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Recursively merge override into base.

        Args:
            base: The base dictionary (modified in-place).
            override: Values to overlay onto base.

        Returns:
            Merged dictionary.
        """
        for key, value in override.items():
            if (
                key in base
                and isinstance(base[key], dict)
                and isinstance(value, dict)
            ):
                ConfigManager._deep_merge(base[key], value)
            else:
                base[key] = value
        return base


# ─── Module-Level Singleton ───────────────────────────────────────────────────

_config: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Return the global ConfigManager singleton.

    Returns:
        Initialized ConfigManager instance.
    """
    global _config
    if _config is None:
        _config = ConfigManager()
    return _config


def reset_config() -> None:
    """Reset the global config singleton (used in testing)."""
    global _config
    _config = None
