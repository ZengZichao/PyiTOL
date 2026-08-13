"""Tests for template_tools CLI commands - create, bundle, validate."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyitol.cli.apps import template_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Importability tests
# ---------------------------------------------------------------------------


class TestTemplateToolsImportability:
    """Verify the three top-level tool command functions are importable."""

    def test_import_template_create(self):
        from pyitol.cli.template_tools import template_create

        assert callable(template_create)

    def test_import_template_bundle(self):
        from pyitol.cli.template_tools import template_bundle

        assert callable(template_bundle)

    def test_import_template_validate(self):
        from pyitol.cli.template_tools import template_validate

        assert callable(template_validate)


# ---------------------------------------------------------------------------
# CliRunner tests for 'create' (unified) with collapse type
# ---------------------------------------------------------------------------


class TestCreateCollapseCommand:
    """Test the unified 'create collapse' command via CliRunner."""

    def test_create_collapse_produces_output(self, tmp_path):
        output = str(tmp_path / "collapse.txt")
        result = runner.invoke(
            template_app,
            [
                "create",
                "collapse",
                "--node-ids",
                "A,B",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_COLLAPSE" in content or "COLLAPSE" in content.upper()

    def test_create_collapse_with_short_flags(self, tmp_path):
        output = str(tmp_path / "collapse_short.txt")
        result = runner.invoke(
            template_app,
            [
                "create",
                "collapse",
                "-n",
                "X,Y,Z",
                "-o",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()

    def test_create_collapse_with_label_and_separator(self, tmp_path):
        output = str(tmp_path / "collapse_opts.txt")
        result = runner.invoke(
            template_app,
            [
                "create",
                "collapse",
                "--node-ids",
                "node1,node2",
                "--label",
                "collapsed_clades",
                "--separator",
                "TAB",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()


# ---------------------------------------------------------------------------
# CliRunner tests for 'validate'
# ---------------------------------------------------------------------------


class TestValidateCommand:
    """Test the 'validate' command via CliRunner."""

    @pytest.fixture
    def valid_template(self, tmp_path):
        """Create a minimal valid iTOL color strip template."""
        p = tmp_path / "valid_template.txt"
        p.write_text(
            "DATASET_COLORSTRIP\n"
            "SEPARATOR TAB\n"
            "DATASET_LABEL\ttest\n"
            "COLOR\t#ff0000\n"
            "STRIP_WIDTH\t50\n"
            "\n"
            "DATA\n"
            "A\tGroup1\t#ff0000\n"
            "B\tGroup1\t#00ff00\n"
        )
        return str(p)

    @pytest.fixture
    def invalid_template(self, tmp_path):
        """Create an invalid template (unknown type)."""
        p = tmp_path / "invalid_template.txt"
        p.write_text("UNKNOWN_TYPE\nSEPARATOR TAB\n\nDATA\n")
        return str(p)

    def test_validate_valid_template(self, valid_template):
        result = runner.invoke(
            template_app,
            [
                "validate",
                "--template",
                valid_template,
            ],
        )
        assert result.exit_code == 0, result.output
        assert "格式正确" in result.output or "全部通过" in result.output

    def test_validate_invalid_template(self, invalid_template):
        result = runner.invoke(
            template_app,
            [
                "validate",
                "--template",
                invalid_template,
            ],
        )
        # Should exit with non-zero or report errors/warnings
        assert result.exit_code != 0 or "未检测到" in result.output or "格式异常" in result.output


class TestUnifiedVsSubcommandLabel:
    """TC-9.6: unified and sub-command entry should produce identical output."""

    def test_unified_and_subcommand_label_match(self, tmp_path, tree_file, taxonomy_file):
        unified_out = str(tmp_path / "unified.txt")
        subcmd_out = str(tmp_path / "subcmd.txt")

        result_unified = runner.invoke(
            template_app,
            [
                "create",
                "color-strip",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "Phylum",
                "--output",
                unified_out,
            ],
        )
        result_subcmd = runner.invoke(
            template_app,
            [
                "create-color-strip",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "Phylum",
                "--output",
                subcmd_out,
            ],
        )

        assert result_unified.exit_code == 0, result_unified.output
        assert result_subcmd.exit_code == 0, result_subcmd.output

        unified_label = next(
            (line for line in Path(unified_out).read_text().splitlines() if line.startswith("DATASET_LABEL")),
            "",
        )
        subcmd_label = next(
            (line for line in Path(subcmd_out).read_text().splitlines() if line.startswith("DATASET_LABEL")),
            "",
        )
        assert unified_label == subcmd_label
        assert "color_strip" in subcmd_label
