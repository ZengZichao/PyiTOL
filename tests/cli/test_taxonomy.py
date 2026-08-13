"""Tests for PyiTOL CLI taxonomy commands (beyond style)."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\tFirmicutes\nC\tArchaea\tEuryarchaeota\nD\tArchaea\tCrenarchaeota\n"  # noqa: E501


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


class TestTaxonomyRanks:
    def test_ranks_command(self, taxonomy_file):
        result = runner.invoke(app, ["taxonomy", "ranks", "--taxonomy", taxonomy_file])
        assert result.exit_code == 0, result.output
        assert "Kingdom" in result.output or "Phylum" in result.output


class TestTaxonomyExtract:
    def test_extract(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "extract.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "extract",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "Bacteria" in content
        assert "Archaea" in content


class TestTaxonomyExtractStats:
    def test_extract_stats(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "stats.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "extract-stats",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestTaxonomyMonophyly:
    def test_monophyly_rank(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "mono.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "monophyly",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--rank",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_monophyly_taxa(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "mono.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "monophyly",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--taxa",
                "Bacteria,Archaea",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_monophyly_taxa_file(self, tmp_path, tree_file, taxonomy_file):
        taxa_file = tmp_path / "taxa.txt"
        taxa_file.write_text("Bacteria\nArchaea\n")
        out = tmp_path / "mono.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "monophyly",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--taxa-file",
                str(taxa_file),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_monophyly_no_rank_or_taxa(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "mono.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "monophyly",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1


class TestTaxonomyConvertBinary:
    def test_convert_binary(self, tmp_path):
        data = tmp_path / "tax.tsv"
        data.write_text("id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\t\n")
        out = tmp_path / "binary.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-binary",
                "--input",
                str(data),
                "--columns",
                "Kingdom,Phylum",
                "--output",
                str(out),
                "--id-column",
                "id",
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_binary_missing_columns(self, tmp_path):
        data = tmp_path / "tax.tsv"
        data.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "binary.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-binary",
                "--input",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1

    def test_convert_binary_missing_column_warning(self, tmp_path):
        data = tmp_path / "tax.tsv"
        data.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "binary.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-binary",
                "--input",
                str(data),
                "--columns",
                "MissingCol",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_binary_compat_mode(self, tmp_path, tree_file):
        data = tmp_path / "tax.tsv"
        data.write_text(
            "id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\t\nC\tArchaea\tEuryarchaeota\nD\tArchaea\tCrenarchaeota\n"
        )
        out = tmp_path / "binary.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-binary",
                "--taxonomy",
                str(data),
                "--tree",
                tree_file,
                "--columns",
                "Kingdom,Phylum",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_binary_compat_missing_params(self, tmp_path, tree_file):
        out = tmp_path / "binary.txt"
        # Missing --taxonomy
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-binary",
                "--tree",
                tree_file,
                "--columns",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1


class TestTaxonomyConvertConnect:
    def test_convert_connect(self, tmp_path, taxonomy_file):
        out = tmp_path / "connect.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-connect",
                "--taxonomy",
                taxonomy_file,
                "--columns",
                "Kingdom,Phylum",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_connect_input_auto_detect(self, tmp_path):
        data = tmp_path / "matrix.csv"
        data.write_text("id,A,B\nX,1,1\nY,1,0\n")
        out = tmp_path / "connect.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-connect",
                "--input",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_connect_auto_detect_no_binary(self, tmp_path):
        data = tmp_path / "matrix.csv"
        data.write_text("id,A,B\nX,foo,bar\nY,baz,qux\n")
        out = tmp_path / "connect.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-connect",
                "--input",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_convert_connect_compat_missing_params(self, tmp_path):
        out = tmp_path / "connect.csv"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "convert-connect",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
