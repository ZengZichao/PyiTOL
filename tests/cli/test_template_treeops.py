"""Tests for template_treeops CLI commands - tree colors, collapse, prune, etc."""

from pathlib import Path

from typer.testing import CliRunner

from pyitol.cli.apps import template_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Importability tests
# ---------------------------------------------------------------------------


class TestTemplateTreeopsImportability:
    """Verify all tree operation command functions are importable."""

    def test_import_template_tree_colors(self):
        from pyitol.cli.template_treeops import template_tree_colors

        assert callable(template_tree_colors)

    def test_import_template_branch_gradient(self):
        from pyitol.cli.template_treeops import template_branch_gradient

        assert callable(template_branch_gradient)

    def test_import_template_collapse(self):
        from pyitol.cli.template_treeops import template_collapse

        assert callable(template_collapse)

    def test_import_template_prune(self):
        from pyitol.cli.template_treeops import template_prune

        assert callable(template_prune)

    def test_import_template_spacing(self):
        from pyitol.cli.template_treeops import template_spacing

        assert callable(template_spacing)

    def test_import_template_ranges(self):
        from pyitol.cli.template_treeops import template_ranges

        assert callable(template_ranges)

    def test_import_template_highlight(self):
        from pyitol.cli.template_treeops import template_highlight

        assert callable(template_highlight)

    def test_import_template_style(self):
        from pyitol.cli.template_treeops import template_style

        assert callable(template_style)

    def test_import_template_arrow(self):
        from pyitol.cli.template_treeops import template_arrow

        assert callable(template_arrow)


# ---------------------------------------------------------------------------
# CliRunner tests for collapse and prune (no tree/taxonomy required)
# ---------------------------------------------------------------------------


class TestCollapseCommand:
    """Test 'create-collapse' via CliRunner."""

    def test_collapse_produces_output(self, tmp_path):
        output = str(tmp_path / "collapse.txt")
        result = runner.invoke(
            template_app,
            [
                "create-collapse",
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

    def test_collapse_with_multiple_ids(self, tmp_path):
        output = str(tmp_path / "collapse_multi.txt")
        result = runner.invoke(
            template_app,
            [
                "create-collapse",
                "-n",
                "node1,node2,node3",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()

    def test_collapse_with_custom_label(self, tmp_path):
        output = str(tmp_path / "collapse_label.txt")
        result = runner.invoke(
            template_app,
            [
                "create-collapse",
                "--node-ids",
                "X,Y",
                "--label",
                "my_collapses",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()


class TestPruneCommand:
    """Test 'create-prune' via CliRunner."""

    def test_prune_produces_output(self, tmp_path):
        output = str(tmp_path / "prune.txt")
        result = runner.invoke(
            template_app,
            [
                "create-prune",
                "--node-ids",
                "A,B",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_PRUNE" in content or "PRUNE" in content.upper()

    def test_prune_with_multiple_ids(self, tmp_path):
        output = str(tmp_path / "prune_multi.txt")
        result = runner.invoke(
            template_app,
            [
                "create-prune",
                "-n",
                "taxon1,taxon2",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
