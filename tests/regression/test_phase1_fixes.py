"""Targeted regression tests for the 6 Phase-1 correctness fixes.

Each test reproduces the *original failure scenario* of a specific bug and
asserts the corrected behaviour. They are intentionally independent of the
engineer's self-test scripts and verify the source directly.

Run:
    PYTHONPATH=src python -m pytest tests/regression/test_phase1_fixes.py -v
"""

import dendropy
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import linkage, to_tree
from scipy.spatial.distance import pdist

from pyitol.core.count_tree import build_tree_from_counts
from pyitol.core.monophyly import check_monophyly_with_taxa_list
from pyitol.core.taxonomy import extract_taxonomy_from_tip_names
from pyitol.templates.learner import learn_template
from pyitol.utils.data_converters import df_tree


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _clade_label_sets_from_newick(newick: str) -> set[frozenset]:
    """Return the set of leaf-label frozensets for every internal clade.

    Two labeled trees with identical topology but mis-attached leaf names
    produce *different* clade label-sets, so this is a robust oracle for
    detecting leaf/name misalignment.
    """
    tree = dendropy.Tree.get(data=newick, schema="newick", preserve_underscores=True)
    sets: set[frozenset] = set()
    for node in tree.internal_nodes():
        leaves = frozenset(leaf.taxon.label for leaf in node.leaf_nodes())
        sets.add(leaves)
    return sets


def _oracle_clade_label_sets(matrix, labels, metric="euclidean", method="average") -> set[frozenset]:
    """Compute the *correct* clade label-sets directly from the matrix via scipy.

    ``Z`` is built on the original row order, so ``to_tree(Z)`` assigns each
    leaf ``node.id`` equal to the original matrix row index. The correct label
    for that leaf is therefore ``labels[node.id]`` (the true name of the row it
    represents). The fixed ``df_tree`` reorders matrix and labels *together*
    before re-deriving the tree, which yields exactly this correct labeling.
    """
    Z = linkage(pdist(np.asarray(matrix, dtype=float), metric=metric), method=method)
    root = to_tree(Z)

    sets: set[frozenset] = set()

    def walk(node):
        if node.is_leaf():
            return {labels[node.id]}
        left = walk(node.left)
        right = walk(node.right)
        s = left | right
        sets.add(frozenset(s))
        return s

    walk(root)
    return sets


# ---------------------------------------------------------------------------
# Item 1: df_tree(order='hclust') leaf/matrix alignment + non-negative root
# ---------------------------------------------------------------------------
class TestDfTreeHclustLeafAlignment:
    def test_leaf_names_aligned_with_matrix_rows(self):
        """Original bug: only leaf_labels were reordered, not the matrix, so
        to_tree(Z) node.id (original row index) got the WRONG label -> a clade
        that genuinely groups rows {A1,A2} was mis-labeled {A1,B1}.

        Construct a 4-taxon matrix where leaves_list forces a non-trivial
        reorder: rows [A1, B1, A2, B2] with A1-A2 close and B1-B2 close but all
        cross-distances large. Correct clustering = {A1,A2}, {B1,B2}.
        """
        labels = ["A1", "B1", "A2", "B2"]
        # features: A1=(0,0), B1=(100,0), A2=(0,1), B2=(100,1)
        matrix = [
            [0.0, 0.0],  # A1
            [100.0, 0.0],  # B1
            [0.0, 1.0],  # A2
            [100.0, 1.0],  # B2
        ]
        df = pd.DataFrame({"id": labels, "f1": [r[0] for r in matrix], "f2": [r[1] for r in matrix]})

        out = df_tree(df, main="col", order="hclust", id_column="id")

        # Parseable newick, all labels present
        assert out.endswith(";")
        for lab in labels:
            assert lab in out, f"leaf {lab} missing from tree: {out}"

        got = _clade_label_sets_from_newick(out)
        expected = _oracle_clade_label_sets(matrix, labels)
        # The only valid (correct) partition is {A1,A2} & {B1,B2}.
        assert got == expected, f"clade label-sets mismatch:\n got={got}\n exp={expected}"
        assert frozenset({"A1", "A2"}) in got
        assert frozenset({"B1", "B2"}) in got

    def test_root_branch_length_non_negative(self):
        """P1 fix: root branch length must be >= 0 (was negative before)."""
        df = pd.DataFrame(
            {
                "id": ["A", "B", "C", "D"],
                "x": [0.0, 1.0, 5.0, 6.0],
                "y": [0.0, 0.0, 0.0, 0.0],
            }
        )
        out = df_tree(df, main="col", order="hclust", id_column="id")
        tree = dendropy.Tree.get(data=out, schema="newick", preserve_underscores=True)
        root_len = tree.seed_node.edge_length
        assert root_len is not None
        assert root_len >= 0, f"root branch length is negative: {root_len}"


# ---------------------------------------------------------------------------
# Item 2: count_tree Newick has non-negative & parseable root branch length
# ---------------------------------------------------------------------------
class TestCountTreeNewickRoot:
    def _assert_valid_newick_root(self, newick: str, expected_leaves):
        assert newick.endswith(";")
        tree = dendropy.Tree.get(data=newick, schema="newick", preserve_underscores=True)
        assert tree.seed_node.edge_length is not None
        assert tree.seed_node.edge_length >= 0, f"negative root branch: {newick}"
        leaf_labels = {leaf.taxon.label for leaf in tree.leaf_nodes() if leaf.taxon}
        assert leaf_labels == set(expected_leaves)

    def test_hclust_root_non_negative(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\nC\t5\t6\n")
        newick = build_tree_from_counts(str(p), id_column="id")
        self._assert_valid_newick_root(newick, {"A", "B", "C"})

    def test_single_linkage_root_non_negative(self, tmp_path):
        p = tmp_path / "counts.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\nC\t5\t6\n")
        newick = build_tree_from_counts(str(p), id_column="id", method="nj")
        self._assert_valid_newick_root(newick, {"A", "B", "C"})


# ---------------------------------------------------------------------------
# Item 3: NCBI tip-name parsing -> Species = epithet (not binomial)
# ---------------------------------------------------------------------------
class TestNcbiSpeciesEpithet:
    def test_species_is_epithet_not_binomial(self, tmp_path):
        tree = tmp_path / "t.nwk"
        tree.write_text("(Homo_sapiens,Salmonella_enterica);")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="ncbi")
        assert "Species" in df.columns
        assert "Genus" in df.columns
        assert df["Species"].tolist() == ["sapiens", "enterica"], df["Species"].tolist()
        assert df["Genus"].tolist() == ["Homo", "Salmonella"], df["Genus"].tolist()
        # Explicitly guard against the old buggy behaviour: full binomial.
        assert "Homo_sapiens" not in df["Species"].tolist()


# ---------------------------------------------------------------------------
# Item 4: check_monophyly_with_taxa_list keeps special identifiers when mixed
#          with normal names
# ---------------------------------------------------------------------------
DOMAIN_NEWICK = "((BAC1:0.1,BAC2:0.2):0.3,(ARC1:0.4,ARC2:0.5):0.6);"
DOMAIN_TAXONOMY = (
    "id\tDomain\tPhylum\n"
    "BAC1\tBacteria\tProteobacteria\n"
    "BAC2\tBacteria\tFirmicutes\n"
    "ARC1\tArchaea\tEuryarchaeota\n"
    "ARC2\tArchaea\tCrenarchaeota\n"
)


class TestMonophylySpecialIdentifierMixed:
    def test_special_group_not_dropped_when_mixed_with_normal(self, tmp_path):
        """Original bug: a special identifier (LUCA) mixed with a normal name
        (BAC1) was silently dropped from the results.

        With the fix, resolved_groups (LUCA=all 4) is initialized outside the
        conditional and union-merged back into the normal groups, so the LUCA
        group must appear in the results with all 4 members.
        """
        tree = tmp_path / "domain.nwk"
        tree.write_text(DOMAIN_NEWICK)
        tax = tmp_path / "domain.tsv"
        tax.write_text(DOMAIN_TAXONOMY)

        results = check_monophyly_with_taxa_list(str(tax), str(tree), taxa_list=["LUCA", "BAC1"])
        groups = {r["group"]: r for r in results}
        assert "LUCA" in groups, f"LUCA special group dropped! groups={list(groups)}"
        assert "BAC1" in groups
        assert int(groups["LUCA"]["member_count"]) == 4


# ---------------------------------------------------------------------------
# Item 5: learner keeps single-column COLLAPSE/PRUNE node IDs (no data loss)
# ---------------------------------------------------------------------------
class TestLearnerSingleColumnCollapsePrune:
    def _write_template(self, tmp_path, header, body_lines):
        p = tmp_path / "t.txt"
        lines = [header, "SEPARATOR TAB", "DATA", *body_lines]
        p.write_text("\n".join(lines) + "\n")
        return str(p)

    def test_collapse_single_column_ids_preserved(self, tmp_path):
        """Single-column node-ID dataset with a leading blank line after DATA.

        Catches BOTH pre-fix bugs:
          * column-inference guard failing to infer -> all data dropped
          * empty line at start of DATA -> junk empty-id row / lost rows
        """
        p = self._write_template(tmp_path, "COLLAPSE", ["", "node1", "node2", "node3"])
        result = learn_template(p)
        ds = result["datasets"][0]
        data = ds["data"]
        ids = [row.get("id") for row in data]
        assert ids == ["node1", "node2", "node3"], f"COLLAPSE data lost/junk: {data}"
        assert ds["columns"] == ["id"]

    def test_prune_single_column_ids_preserved(self, tmp_path):
        p = self._write_template(tmp_path, "PRUNE", ["", "leafA", "leafB"])
        result = learn_template(p)
        ds = result["datasets"][0]
        ids = [row.get("id") for row in ds["data"]]
        assert ids == ["leafA", "leafB"], f"PRUNE data lost/junk: {ds['data']}"
        assert ds["columns"] == ["id"]


# ---------------------------------------------------------------------------
# Item 6: SCHEMA_MAP populated even when base.py imported in isolation
# ---------------------------------------------------------------------------
class TestSchemaAutoRegistration:
    def test_schema_map_populated_on_isolated_import(self):
        """Original bug: registration depended on templates.presets being
        imported elsewhere, so importing schemas.base in isolation yielded an
        empty SCHEMA_MAP. The fix imports the submodules directly at the bottom
        of base.py.
        """
        from pyitol.templates.schemas.base import SCHEMA_MAP

        assert len(SCHEMA_MAP) > 0, "SCHEMA_MAP is empty after isolated import"
        # Common schemas that must be present.
        for expected in ("dataset_collapse", "dataset_prune", "dataset_colorstrip", "dataset_simple_bar"):
            assert expected in SCHEMA_MAP, f"{expected} missing from SCHEMA_MAP"
