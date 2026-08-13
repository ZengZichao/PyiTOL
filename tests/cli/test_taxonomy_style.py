"""Tests for taxonomy style CLI command."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tPhylum\tcount\nA\tBacteria\tProteobacteria\t10\nB\tBacteria\tProteobacteria\t20\nC\tArchaea\tEuryarchaeota\t15\nD\tArchaea\tEuryarchaeota\t25\n"  # noqa: E501


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "test.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


class TestTaxonomyStyle:
    def test_color_branch(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "color-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "TREE_COLORS" in content
        assert "clade" in content

    def test_color_strip(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Phylum",
                "--action",
                "color-strip",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_COLORSTRIP" in content

    def test_symbol(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "symbol",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_SYMBOL" in content

    def test_range(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "range",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_RANGE" in content

    def test_style_branch(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "style-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content
        assert "branch" in content

    def test_highlight(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "highlight",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content
        assert "label_background" in content

    def test_color_label(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "color-label",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "label" in content

    def test_color_range(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "color-range",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_label(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "style-label",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content
        assert "label" in content

    def test_width(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "width",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_gradient(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "gradient",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_GRADIENT" in content

    def test_unknown_action(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "unknown-action",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1

    def test_taxon_mode(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--taxon",
                "A",
                "--action",
                "color-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_taxon_not_in_tree(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--taxon",
                "Z",
                "--action",
                "color-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_range_single_member(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--taxon",
                "A",
                "--action",
                "range",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_color_range_single_member(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--taxon",
                "A",
                "--action",
                "color-range",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_empty_taxa_list(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\t\nB\t\nC\t\nD\t\n")
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--action",
                "color-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1

    def test_missing_rank_and_taxon(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--action",
                "color-branch",
                "--palette",
                "nature",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1
