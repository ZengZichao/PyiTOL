"""Tests for PyiTOL tree info extraction module."""

import pytest

from pyitol.utils.tree_info import (
    extract_tree_info,
    get_node_count,
    get_tip_order,
    get_tree_info,
)

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


class TestExtractTreeInfo:
    def test_returns_dataframe(self, tree_file):
        df = extract_tree_info(tree_file)
        assert len(df) > 0
        assert "id" in df.columns
        assert "parent_id" in df.columns
        assert "branch_length" in df.columns
        assert "is_tip" in df.columns
        assert "descendant_count" in df.columns

    def test_tips_marked(self, tree_file):
        df = extract_tree_info(tree_file)
        tips = df[df["is_tip"]]
        assert set(tips["id"].tolist()) == {"A", "B", "C", "D"}

    def test_descendant_count(self, tree_file):
        df = extract_tree_info(tree_file)
        tips = df[df["is_tip"]]
        assert all(tips["descendant_count"] == 1)

    def test_output_file(self, tree_file, tmp_path):
        out = tmp_path / "info.csv"
        extract_tree_info(tree_file, output_path=out)
        assert out.exists()


class TestGetNodeCount:
    def test_counts(self, tree_file):
        counts = get_node_count(tree_file)
        assert counts["tip_count"] == 4
        # dendropy internal_nodes() includes the root node for this topology
        assert counts["internal_node_count"] == 3
        # total includes root plus tips and internal nodes (root counted once in preorder)
        assert counts["total_count"] == 7


class TestGetTipOrder:
    def test_order(self, tree_file):
        order = get_tip_order(tree_file)
        assert set(order) == {"A", "B", "C", "D"}


class TestGetTreeInfo:
    def test_summary(self, tree_file):
        info = get_tree_info(tree_file)
        assert info["tip_count"] == 4
        assert info["has_branch_lengths"] is True
        assert info["max_depth"] > 0
        assert "sample_tips" in info
