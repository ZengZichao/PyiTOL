"""Count-to-tree module - convert count data to tree-compatible format and build trees."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from scipy.cluster.hierarchy import ClusterNode
import dendropy

from pyitol.core.parser import detect_tree_schema
from pyitol.exceptions import TreeParseError

logger = logging.getLogger(__name__)


def count_to_tree(
    input_file: str,
    tree_path: str,
    value_column: str = "count",
    id_column: str = "id",
) -> dict:
    """Convert count data to tree-compatible format."""
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}

    df = pd.read_csv(input_file, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)].copy()

    data = []
    for _, row in df.iterrows():
        val = row.get(value_column, "0")
        if pd.isna(val):
            continue
        data.append([row["id"], val])

    return {"columns": ["id", value_column], "data": data}


def build_tree_from_counts(
    input_file: str,
    id_column: str = "id",
    method: str = "hclust",
    metric: str = "euclidean",
    linkage: str = "average",
) -> str:
    """Build a phylogenetic tree from count data using hierarchical clustering.

    Args:
        input_file: Path to count data matrix (wide format)
        id_column: Column name for sample IDs
        method: Clustering method ('hclust' for hierarchical clustering, 'upgma', 'single_linkage')
        metric: Distance metric for hierarchical clustering
        linkage: Linkage method for hierarchical clustering

    Returns:
        Newick format tree string.

    Note:
        The 'single_linkage' method (formerly 'nj') uses scipy's single linkage
        clustering as a distance-based tree approximation. This is NOT a true
        Neighbor-Joining algorithm (Saitou & Nei, 1987). For accurate NJ trees,
        use specialized tools (e.g., rapidnj, FastME, or ete3).
    """
    from scipy.cluster.hierarchy import linkage as scipy_linkage
    from scipy.cluster.hierarchy import to_tree
    from scipy.spatial.distance import pdist

    df = pd.read_csv(input_file, sep=None, engine="python")
    if id_column in df.columns:
        labels = df[id_column].astype(str).tolist()
        matrix = df.drop(columns=[id_column]).values
    else:
        labels = [str(i) for i in range(len(df))]
        matrix = df.values

    if method in ("hclust", "upgma", "average"):
        dist = pdist(matrix, metric=metric)
        Z = scipy_linkage(dist, method=linkage)
        root = to_tree(Z, rd=False)

        def _to_newick(node: ClusterNode, labels: list[str], parent_dist: float = 0) -> str:
            if node.is_leaf():
                # Branch length = parent height - leaf height (leaf height = 0)
                branch_len = parent_dist
                return f"{labels[node.id]}:{branch_len:.6f}"
            left = _to_newick(node.left, labels, node.dist)
            right = _to_newick(node.right, labels, node.dist)
            # Branch length from parent to this node
            branch_len = parent_dist - node.dist
            return f"({left},{right}):{branch_len:.6f}"

        # P1-xx: Pass the root's own height as `parent_dist` so the root branch length
        # evaluates to 0 (parent_dist - root.dist == 0) instead of a negative value.
        # Internal nodes still receive their parent's distance, so child branch lengths
        # remain positive and the Newick output is valid.
        return _to_newick(root, labels, root.dist) + ";"
    elif method in ("nj", "single_linkage"):
        # Renamed from 'nj' to 'single_linkage' for clarity.
        # 'nj' is kept as alias for backward compatibility.
        # WARNING: This is NOT a true Neighbor-Joining algorithm (Saitou & Nei, 1987).
        # It uses scipy's single linkage as a distance-based tree approximation.
        # For accurate NJ trees, use specialized tools (e.g., rapidnj, FastME, or ete3).
        dist = pdist(matrix, metric=metric)
        Z = scipy_linkage(dist, method="single")
        root = to_tree(Z, rd=False)

        def _to_newick_sl(node: ClusterNode, labels: list[str], parent_dist: float = 0) -> str:
            if node.is_leaf():
                branch_len = parent_dist
                return f"{labels[node.id]}:{branch_len:.6f}"
            left = _to_newick_sl(node.left, labels, node.dist)
            right = _to_newick_sl(node.right, labels, node.dist)
            branch_len = parent_dist - node.dist
            return f"({left},{right}):{branch_len:.6f}"

        # P1-xx: Pass the root's own height as `parent_dist` so the root branch length
        # evaluates to 0 (parent_dist - root.dist == 0) instead of a negative value.
        return _to_newick_sl(root, labels, root.dist) + ";"
    else:
        raise TreeParseError(f"Unsupported method: {method}. Use 'hclust', 'upgma', 'single_linkage', or 'nj'.")
