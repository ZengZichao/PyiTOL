"""Tests for PyiTOL CLI utils commands."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


class TestUtilsTreeInfo:
    def test_tree_info(self, tree_file):
        result = runner.invoke(app, ["tree", "info", "--tree", tree_file])
        assert result.exit_code == 0, result.output


class TestSearchTreeFile:
    def test_search_recursive(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "tree.nwk").write_text(SIMPLE_NEWICK)
        result = runner.invoke(app, ["utils", "search-tree-file", "--dir", str(tmp_path)])
        assert result.exit_code == 0, result.output
        assert "tree.nwk" in result.output

    def test_search_no_files(self, tmp_path):
        result = runner.invoke(app, ["utils", "search-tree-file", "--dir", str(tmp_path)])
        assert result.exit_code == 0
        assert "未找到" in result.output

    def test_first_only(self, tmp_path):
        (tmp_path / "tree.nwk").write_text(SIMPLE_NEWICK)
        result = runner.invoke(app, ["utils", "search-tree-file", "--dir", str(tmp_path), "--first-only"])
        assert result.exit_code == 0
        assert "tree.nwk" in result.output

    def test_first_only_no_files(self, tmp_path):
        result = runner.invoke(app, ["utils", "search-tree-file", "--dir", str(tmp_path), "--first-only"])
        assert result.exit_code == 0
        assert "未找到" in result.output


class TestTaxonomyParse:
    def test_parse(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\n")
        result = runner.invoke(app, ["utils", "taxonomy-parse", "--taxonomy", str(p)])
        assert result.exit_code == 0, result.output
        assert "Bacteria" in result.output


class TestWideToLong:
    def test_conversion(self, tmp_path):
        p = tmp_path / "wide.tsv"
        p.write_text("id\tcol1\tcol2\nA\t1\t2\n")
        out = tmp_path / "long.csv"
        result = runner.invoke(app, ["utils", "wide-to-long", "--data", str(p), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestLongToWide:
    def test_conversion(self, tmp_path):
        p = tmp_path / "long.tsv"
        p.write_text("id\tvariable\tvalue\nA\tcol1\t1\n")
        out = tmp_path / "wide.csv"
        result = runner.invoke(app, ["utils", "long-to-wide", "--data", str(p), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestCountToTree:
    def test_basic(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\tcount\nA\t10\nB\t20\n")
        out = tmp_path / "tree.nwk"
        result = runner.invoke(app, ["utils", "count-to-tree", "--data", str(p), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestGroupColumns:
    def test_basic(self, tmp_path):
        p = tmp_path / "data.tsv"
        p.write_text("id\tA\tB\nX\t1\t2\n")
        out = tmp_path / "grouped.csv"
        result = runner.invoke(app, ["utils", "group-columns", "--data", str(p), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_group_regex(self, tmp_path):
        p = tmp_path / "data.tsv"
        p.write_text("id\tATP1\tATP2\tCOX1\nX\t1\t2\t3\n")
        out = tmp_path / "grouped.csv"
        result = runner.invoke(
            app, ["utils", "group-columns", "--data", str(p), "--output", str(out), "--group-regex", "^(ATP|COX)"]
        )
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestBinary:
    def test_basic(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tA\tB\nX\t1\t\nY\t\t2\n")
        out = tmp_path / "binary.csv"
        result = runner.invoke(app, ["utils", "binary", "--taxonomy", str(p), "--columns", "A,B", "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestConnections:
    def test_basic(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tA\tB\nX\t1\t1\nY\t1\t0\n")
        out = tmp_path / "conn.csv"
        result = runner.invoke(
            app, ["utils", "connections", "--taxonomy", str(p), "--columns", "A,B", "--output", str(out)]
        )
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestPreview:
    def test_basic(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        result = runner.invoke(
            app, ["utils", "preview", "--taxonomy", str(p), "--tree", tree_file, "--column", "Kingdom"]
        )
        assert result.exit_code == 0, result.output
        assert "Bacteria" in result.output

    def test_missing_column(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\n")
        result = runner.invoke(
            app, ["utils", "preview", "--taxonomy", str(p), "--tree", tree_file, "--column", "Missing"]
        )
        assert result.exit_code == 1


class TestDfTree:
    def test_basic(self, tmp_path):
        p = tmp_path / "data.tsv"
        p.write_text("id\tA\tB\nX\t1\t2\nY\t3\t4\n")
        out = tmp_path / "tree.nwk"
        result = runner.invoke(app, ["utils", "df-tree", "--data", str(p), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()


class TestLearnTemplate:
    def test_basic(self, tmp_path):
        tpl = tmp_path / "template.txt"
        tpl.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nDATASET_LABEL test\nCOLOR #ff0000\nDATA\nA\t10\n")
        out = tmp_path / "learned.json"
        result = runner.invoke(app, ["learn", "template", "--template", str(tpl), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()
