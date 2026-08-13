"""QA independent regression tests for Item 4: NHX comment handling + determinism.

Verifies:
- _count_newick_trees / _load_all_trees correctly ignore ';' and '()' that
  appear *inside* NHX comments ([&&NHX...]) when counting / splitting trees.
- load_tree(multi_tree='split') returns the correct number of trees for NHX
  content.
- The removed non-deterministic 'random' multi-tree strategy now raises.
- No `import random` / `randint` / `random.` remains in the source.
"""

from pathlib import Path

import pytest

from pyitol.core.parser import (
    _count_newick_trees,
    _load_all_trees,
    load_tree,
)

# NHX annotations may contain ';' and '()' that must NOT be treated as tree
# separators or depth changes.
NHX_MULTI = "(A,(B,(C,D)[&&NHX:s=foo;x=(p)q]):0.1);(E,F)[&&NHX:note=a(b)c;];"
NHX_SINGLE = "(A,B)[&&NHX:foo=bar;baz];"
PLAIN_MULTI = "(A,B);(C,D);(E,F);"


def _tips(tree):
    return {n.taxon.label for n in tree.leaf_nodes() if n.taxon}


class TestNHXCommentDepth:
    def test_count_trees_nhx_multi(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(NHX_MULTI)
        assert _count_newick_trees(Path(p)) == 2

    def test_count_trees_nhx_single(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(NHX_SINGLE)
        assert _count_newick_trees(Path(p)) == 1

    def test_count_trees_plain_multi(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(PLAIN_MULTI)
        assert _count_newick_trees(Path(p)) == 3

    def test_load_all_trees_nhx_multi(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(NHX_MULTI)
        trees = _load_all_trees(Path(p), "newick")
        assert len(trees) == 2
        assert _tips(trees[0]) == {"A", "B", "C", "D"}
        assert _tips(trees[1]) == {"E", "F"}

    def test_load_all_trees_nhx_single(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(NHX_SINGLE)
        trees = _load_all_trees(Path(p), "newick")
        assert len(trees) == 1

    def test_load_tree_split_nhx(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(NHX_MULTI)
        trees = load_tree(Path(p), multi_tree="split")
        assert isinstance(trees, list)
        assert len(trees) == 2


class TestDeterminism:
    def test_no_random_strategy(self, tmp_path):
        p = tmp_path / "t.nwk"
        p.write_text(PLAIN_MULTI)
        with pytest.raises(Exception):  # noqa: B017
            load_tree(Path(p), multi_tree="random")

    def test_no_random_in_source(self):
        bad = []
        src = Path(__file__).resolve().parents[2] / "src" / "pyitol"
        for py in src.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for token in ("import random", "from random", "randint", "random."):
                if token in text:
                    bad.append((str(py), token))
        assert not bad, f"Non-deterministic random usage found: {bad}"
