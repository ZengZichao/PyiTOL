"""Independent QA regression tests for Item 4: NHX comments + determinism.

Verifies, independently of the other QA engineers' suites:
- ``_count_newick_trees`` ignores ``;`` / ``()`` characters that live inside
  NHX-style ``[...]`` comments, so it does not over/under-count trees.
- ``_load_all_trees`` splits a multi-tree Newick file correctly even when
  comments contain ``;`` / ``()``.
- Determinism: there is no ``random`` multi-tree strategy; requesting
  ``multi_tree='random'`` is rejected (``TreeParseError``).
"""

import pytest

from pyitol.core.parser import _count_newick_trees, _load_all_trees, load_tree
from pyitol.exceptions import TreeParseError


@pytest.fixture
def tree_file(tmp_path, content):
    p = tmp_path / "t.nwk"
    p.write_text(content)
    return p


# ---------------------------------------------------------------------------
# _count_newick_trees with NHX comments containing ; and ()
# ---------------------------------------------------------------------------
class TestCountNewickWithNHX:
    def test_single_tree_with_semicolon_in_comment(self, tmp_path):
        # The comment contains a ';' and a pair of '()' that must be ignored.
        content = "((A:0.1,B:0.2)[&&NHX:foo=bar;baz=(x)y],C:0.3);"
        p = tmp_path / "t.nwk"
        p.write_text(content)
        assert _count_newick_trees(p) == 1

    def test_multi_tree_with_comment_semicolons(self, tmp_path):
        # Two trees; the first carries a comment with a ';' and '()'.
        content = "(A,B)[&&NHX:support=90;(note)];(C,D);"
        p = tmp_path / "t.nwk"
        p.write_text(content)
        assert _count_newick_trees(p) == 2

    def test_only_comment_semicolons_do_not_count(self, tmp_path):
        # Comments with many ';' but a single real terminating ';'.
        content = "((A:0.1,B:0.2)[&&NHX:a=1;b=2;c=3],(C,D)[&&NHX:x=(y)z]);"
        p = tmp_path / "t.nwk"
        p.write_text(content)
        assert _count_newick_trees(p) == 1


# ---------------------------------------------------------------------------
# _load_all_trees with NHX comments
# ---------------------------------------------------------------------------
class TestLoadAllTreesWithNHX:
    def test_splits_multi_tree_with_comments(self, tmp_path):
        content = "(A,B)[&&NHX:support=90;(note)];\n(C,D);"
        p = tmp_path / "t.nwk"
        p.write_text(content)
        trees = _load_all_trees(p, "newick")
        assert len(trees) == 2
        tips0 = {n.taxon.label for n in trees[0].leaf_nodes() if n.taxon}
        tips1 = {n.taxon.label for n in trees[1].leaf_nodes() if n.taxon}
        assert tips0 == {"A", "B"}
        assert tips1 == {"C", "D"}

    def test_single_tree_comment_not_misparsed(self, tmp_path):
        content = "((A:0.1,B:0.2)[&&NHX:foo=bar;baz=(x)y],C:0.3);"
        p = tmp_path / "t.nwk"
        p.write_text(content)
        trees = _load_all_trees(p, "newick")
        assert len(trees) == 1
        tips = {n.taxon.label for n in trees[0].leaf_nodes() if n.taxon}
        assert tips == {"A", "B", "C"}


# ---------------------------------------------------------------------------
# Determinism: no 'random' multi-tree strategy
# ---------------------------------------------------------------------------
class TestDeterminismNoRandom:
    def test_random_strategy_rejected(self, tmp_path):
        content = "((A,B),(C,D));\n(E,F);"
        p = tmp_path / "multi.nwk"
        p.write_text(content)
        with pytest.raises(TreeParseError):
            load_tree(str(p), multi_tree="random")

    def test_deterministic_first_strategy_works(self, tmp_path):
        content = "((A,B),(C,D));\n(E,F);"
        p = tmp_path / "multi.nwk"
        p.write_text(content)
        tree = load_tree(str(p), multi_tree="first")
        tips = {n.taxon.label for n in tree.leaf_nodes() if n.taxon}
        assert tips == {"A", "B", "C", "D"}
