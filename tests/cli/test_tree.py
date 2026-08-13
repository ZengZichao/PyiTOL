"""Tests for PyiTOL CLI tree commands."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
IQ_TREE_NEWICK = "((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def iqtree_file(tmp_path):
    p = tmp_path / "iq.treefile"
    p.write_text(IQ_TREE_NEWICK)
    return str(p)


class TestTreeInfo:
    def test_info_command(self, tree_file):
        result = runner.invoke(app, ["tree", "info", "--tree", tree_file])
        assert result.exit_code == 0, result.output
        assert "tip_count" in result.output or "4" in result.output

    def test_info_verbose(self, tree_file):
        result = runner.invoke(app, ["tree", "info", "--tree", tree_file, "--verbose"])
        assert result.exit_code == 0


class TestFormatSupportValues:
    def test_format_iqtree(self, iqtree_file, tmp_path):
        output = tmp_path / "formatted.nwk"
        result = runner.invoke(
            app,
            [
                "tree",
                "format-support-values",
                "--tree",
                iqtree_file,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert ")90" in content
