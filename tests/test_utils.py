"""
Tests for utility modules.

Copyright (c) 2026-Present Indrajit Ghosh. All Rights Reserved.
"""

import pytest

from asteria.utils.formatting import (
    format_datetime,
    format_tags,
    parse_tags,
    pluralise,
    records_to_csv,
    records_to_json,
    short_id,
    truncate,
)
from asteria.utils.fuzzy import exact_or_fuzzy_match, fuzzy_score, fuzzy_filter
from asteria.config.manager import ConfigManager


class TestFormatting:
    """Tests for formatting utilities."""

    def test_truncate_short_string(self):
        assert truncate("hello", max_len=10) == "hello"

    def test_truncate_long_string(self):
        result = truncate("hello world", max_len=7, suffix="...")
        assert result == "hell..."
        assert len(result) == 7


    def test_truncate_empty(self):
        assert truncate("") == ""

    def test_short_id(self):
        uuid = "550e8400-e29b-41d4-a716-446655440000"
        assert short_id(uuid, 8) == "550e8400"

    def test_short_id_empty(self):
        assert short_id("") == "—"

    def test_parse_tags_comma_separated(self):
        tags = parse_tags("python, ai, llm")
        assert tags == ["python", "ai", "llm"]

    def test_parse_tags_with_hash(self):
        tags = parse_tags("#python, #ai")
        assert tags == ["python", "ai"]

    def test_parse_tags_empty(self):
        assert parse_tags("") == []

    def test_format_tags_empty(self):
        assert format_tags([]) == "—"

    def test_format_tags(self):
        result = format_tags(["python", "ai"])
        assert "#python" in result
        assert "#ai" in result

    def test_records_to_json(self):
        records = [{"name": "Alice", "age": 30}]
        json_str = records_to_json(records)
        assert '"name": "Alice"' in json_str

    def test_records_to_csv(self):
        records = [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]
        csv_str = records_to_csv(records)
        assert "Alice" in csv_str
        assert "Bob" in csv_str
        assert "name,age" in csv_str or "name" in csv_str

    def test_records_to_csv_empty(self):
        assert records_to_csv([]) == ""

    def test_pluralise_singular(self):
        assert pluralise(1, "item") == "item"

    def test_pluralise_plural(self):
        assert pluralise(2, "item") == "items"

    def test_pluralise_custom_plural(self):
        assert pluralise(2, "child", "children") == "children"


class TestFuzzySearch:
    """Tests for fuzzy search utilities."""

    def test_fuzzy_score_exact(self):
        score = fuzzy_score("python", "python")
        assert score == 100

    def test_fuzzy_score_partial(self):
        score = fuzzy_score("pythn", "python")
        assert score > 50

    def test_fuzzy_score_unrelated(self):
        score = fuzzy_score("xyz123", "python")
        assert score < 60

    def test_fuzzy_filter_finds_matches(self):
        items = ["python tutorial", "javascript basics", "python advanced"]
        results = fuzzy_filter("python", items, key=lambda x: x, threshold=60)
        assert len(results) == 2

    def test_fuzzy_filter_empty_query_returns_all(self):
        items = ["a", "b", "c"]
        results = fuzzy_filter("", items, key=lambda x: x)
        assert len(results) == 3

    def test_exact_or_fuzzy_prefers_exact(self):
        items = ["python guide", "pyth intro", "java"]
        results = exact_or_fuzzy_match("python", items, key=lambda x: x, threshold=60)
        assert results[0] == "python guide"


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_default_editor(self, tmp_path):
        config = ConfigManager(config_path=tmp_path / "config.toml")
        assert config.default_editor == "vim"

    def test_set_and_get(self, tmp_path):
        config = ConfigManager(config_path=tmp_path / "config.toml")
        config.set("general.default_editor", "nano")
        assert config.get("general.default_editor") == "nano"

    def test_save_and_reload(self, tmp_path):
        path = tmp_path / "config.toml"
        config = ConfigManager(config_path=path)
        config.set("gemini.api_key", "test-key-123")
        config.save()

        # Reload
        config2 = ConfigManager(config_path=path)
        assert config2.get("gemini.api_key") == "test-key-123"

    def test_get_missing_key_returns_default(self, tmp_path):
        config = ConfigManager(config_path=tmp_path / "config.toml")
        result = config.get("nonexistent.key", "my_default")
        assert result == "my_default"

    def test_initialize_creates_file(self, tmp_path):
        path = tmp_path / "new_config.toml"
        config = ConfigManager(config_path=path)
        config.initialize()
        assert path.exists()
