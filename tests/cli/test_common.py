"""Unit tests for cli/common.py helper functions."""

from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

from pyitol.cli.common import (
    _apply_config_overrides,
    _load_config_file,
    _parse_colors,
    _parse_log_detail,
    _resolve_param,
    get_console,
)

runner = CliRunner()


class TestLoadConfigFile:
    def test_yaml_file(self, tmp_path):
        p = tmp_path / "config.yaml"
        p.write_text("key: value\n", encoding="utf-8")
        result = _load_config_file(str(p))
        assert result == {"key": "value"}

    def test_yml_file(self, tmp_path):
        p = tmp_path / "config.yml"
        p.write_text("foo: bar\n", encoding="utf-8")
        result = _load_config_file(str(p))
        assert result == {"foo": "bar"}

    def test_json_file(self, tmp_path):
        p = tmp_path / "config.json"
        p.write_text('{"a": 1}', encoding="utf-8")
        result = _load_config_file(str(p))
        assert result == {"a": 1}

    def test_unknown_suffix_yaml_content(self, tmp_path):
        p = tmp_path / "config.txt"
        p.write_text("key: value\n", encoding="utf-8")
        result = _load_config_file(str(p))
        assert result == {"key": "value"}

    def test_unknown_suffix_json_content(self, tmp_path):
        p = tmp_path / "config.txt"
        p.write_text('{"key": "value"}', encoding="utf-8")
        result = _load_config_file(str(p))
        assert result == {"key": "value"}

    def test_unknown_suffix_yaml_falls_back_to_json(self, tmp_path, monkeypatch):
        p = tmp_path / "config.txt"
        p.write_text('{"key": "value"}', encoding="utf-8")
        import pyitol.cli.common as common_mod

        def fake_safe_load(content):
            raise ValueError("forced yaml failure")

        monkeypatch.setattr(common_mod.yaml, "safe_load", fake_safe_load)
        result = _load_config_file(str(p))
        assert result == {"key": "value"}

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            _load_config_file("/nonexistent/config.yaml")


class TestResolveParam:
    @pytest.fixture
    def mock_ctx(self):
        ctx = MagicMock()
        ctx.obj = {"config_data": {}}
        return ctx

    def test_cli_value_set(self, mock_ctx):
        assert _resolve_param(mock_ctx, "key", "cli") == "cli"

    def test_cli_value_empty_string(self, mock_ctx):
        assert _resolve_param(mock_ctx, "key", "", default="def") == "def"

    def test_cli_value_empty_list(self, mock_ctx):
        assert _resolve_param(mock_ctx, "key", [], default="def") == "def"

    def test_from_config_section(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"task": {"key": "sec"}}
        assert _resolve_param(mock_ctx, "key", None, section="task") == "sec"

    def test_from_config_top_level(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"key": "top"}
        assert _resolve_param(mock_ctx, "key", None) == "top"

    def test_from_nested_config(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"taxonomy": {"key": "nested"}}
        assert _resolve_param(mock_ctx, "key", None) == "nested"

    def test_default(self, mock_ctx):
        assert _resolve_param(mock_ctx, "key", None, default="def") == "def"

    def test_cli_value_equal_default_falls_back_to_config(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"key": "cfg"}
        assert _resolve_param(mock_ctx, "key", "def", default="def") == "cfg"

    def test_cli_value_different_from_default_wins(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"key": "cfg"}
        assert _resolve_param(mock_ctx, "key", "explicit", default="def") == "explicit"

    def test_tree_path_alias(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"tree": "tree.nwk"}
        assert _resolve_param(mock_ctx, "tree_path", None) == "tree.nwk"

    def test_taxonomy_path_alias(self, mock_ctx):
        mock_ctx.obj["config_data"] = {"taxonomy": "tax.csv"}
        assert _resolve_param(mock_ctx, "taxonomy_path", None) == "tax.csv"

    def test_no_ctx_obj(self):
        ctx = MagicMock()
        ctx.obj = None
        assert _resolve_param(ctx, "key", None, default="def") == "def"


class TestApplyConfigOverrides:
    def test_basic(self):
        ctx = MagicMock()
        ctx.obj = {"config_data": {"a": 1}}
        result = _apply_config_overrides(ctx, a=(None, 0), b=(None, 2))
        assert result == {"a": 1, "b": 2}


class TestParseLogDetail:
    def test_empty(self):
        assert _parse_log_detail("") == {}

    def test_none(self):
        assert _parse_log_detail(None) == {}

    def test_single_pair(self):
        assert _parse_log_detail("rank=phylum") == {"rank": "phylum"}

    def test_multiple_pairs(self):
        assert _parse_log_detail("rank=phylum, groups=5") == {"rank": "phylum", "groups": "5"}

    def test_no_equals(self):
        assert _parse_log_detail("foobar") == {}


class TestParseColors:
    def test_json_format(self):
        assert _parse_colors('{"A": "#ff0000"}') == {"A": "#ff0000"}

    def test_simplified_format(self):
        assert _parse_colors("A:#ff0000,B:#00ff00") == {"A": "#ff0000", "B": "#00ff00"}

    def test_simplified_format_empty_result(self):
        assert _parse_colors("foobar") is None

    def test_none(self):
        assert _parse_colors(None) is None


class TestGetConsole:
    def test_without_ctx_obj(self):
        ctx = MagicMock()
        ctx.obj = None
        console = get_console(ctx)
        assert console is not None
