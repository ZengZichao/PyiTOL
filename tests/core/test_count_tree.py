"""Tests for PyiTOL core count_tree module."""

import pytest

from pyitol.core.count_tree import build_tree_from_counts, count_to_tree
from pyitol.exceptions import TreeParseError

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


class TestCountToTree:
    def test_basic(self, tree_file, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\tcount\nA\t10\nB\t20\nC\t30\nD\t40\n")
        result = count_to_tree(str(p), tree_file, value_column="count", id_column="id")
        assert result["columns"] == ["id", "count"]
        assert len(result["data"]) == 4

    def test_na_value(self, tree_file, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\tcount\nA\t10\nB\t\nC\t30\nD\t40\n")
        result = count_to_tree(str(p), tree_file, value_column="count", id_column="id")
        # B has empty value -> NaN -> skipped
        assert len(result["data"]) == 3

    def test_single_member_in_tree(self, tree_file, tmp_path):
        # 仅 A 在树中且 count 非空：data 应包含 1 行，列为 id+count
        p = tmp_path / "counts.tsv"
        p.write_text("id\tcount\nA\t10\n")
        result = count_to_tree(str(p), tree_file, value_column="count", id_column="id")
        assert result["columns"] == ["id", "count"]
        assert len(result["data"]) == 1
        assert result["data"][0] == ["A", "10"]

    def test_id_not_in_tree_filtered(self, tree_file, tmp_path):
        # X 不在树中，应被过滤；A 在树中保留
        p = tmp_path / "counts.tsv"
        p.write_text("id\tcount\nA\t10\nX\t99\n")
        result = count_to_tree(str(p), tree_file, value_column="count", id_column="id")
        assert len(result["data"]) == 1
        assert result["data"][0][0] == "A"


class TestBuildTreeFromCounts:
    def test_basic(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\nC\t5\t6\n")
        newick = build_tree_from_counts(str(p), id_column="id")
        assert newick.endswith(";")

    def test_no_id_column(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("a\tb\n1\t2\n3\t4\n5\t6\n")
        newick = build_tree_from_counts(str(p), id_column="id")
        assert newick.endswith(";")

    def test_nj_method(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\nC\t5\t6\n")
        newick = build_tree_from_counts(str(p), id_column="id", method="nj")
        assert newick.endswith(";")

    def test_unsupported_method(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\nC\t5\t6\n")
        with pytest.raises(TreeParseError, match="Unsupported method"):
            build_tree_from_counts(str(p), id_column="id", method="foo")
