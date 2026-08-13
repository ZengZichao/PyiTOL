"""Data conversion utilities for iTOL template preparation."""

from __future__ import annotations

from typing import Any

import dendropy
import pandas as pd

from pyitol.core.binary_convert import category_to_binary  # noqa: F401

# Backward-compatible re-exports
from pyitol.core.column_group import group_columns
from pyitol.core.count_tree import count_to_tree  # noqa: F401
from pyitol.core.parser import detect_tree_schema


def _in_range(
    values: pd.Series,
    rng: tuple[float | None, float | None],
    lower_inclusive: bool = True,
    upper_inclusive: bool = True,
) -> pd.Series:
    """Return a boolean mask for *values* that fall within *rng*.

    Consolidates the previously duplicated boundary logic for the negative /
    zero / positive bands of :func:`convert_to_binary_matrix`. A bound equal to
    ``None`` is treated as unbounded (always ``True``), matching the original
    implementation. ``NaN`` values are excluded from the resulting mask.
    """
    lo, hi = rng
    if lower_inclusive:
        lb = values >= lo if lo is not None else pd.Series(True, index=values.index)
    else:
        lb = values > lo if lo is not None else pd.Series(True, index=values.index)
    if upper_inclusive:
        ub = values <= hi if hi is not None else pd.Series(True, index=values.index)
    else:
        ub = values < hi if hi is not None else pd.Series(True, index=values.index)
    return lb.fillna(False) & ub.fillna(False)


def convert_to_binary_matrix(
    input_file: str,
    negative_range: tuple[float, float] | None = None,
    zero_range: tuple[float, float] | None = None,
    positive_range: tuple[float, float] | None = None,
    lower_inclusive: bool = True,
    upper_inclusive: bool = True,
    id_column: str = "id",
) -> pd.DataFrame:
    """Convert numeric data to binary matrix (-1, 0, 1) with flexible range control.

    Provides equivalent functionality to itol.toolkit's convert_to_binary
    (independent reimplementation in Python; itol.toolkit is an R package).

    Fixed range detection logic for consistent boundary handling.
    """
    df = pd.read_csv(input_file, sep=None, engine="python")
    if id_column in df.columns:
        id_col = df[id_column]
        data_cols = [c for c in df.columns if c != id_column]
    else:
        id_col = df.iloc[:, 0]
        data_cols = list(df.columns[1:])

    result = pd.DataFrame({id_column: id_col})

    for col in data_cols:
        col_data = pd.to_numeric(df[col], errors="coerce")
        converted = pd.Series(index=df.index, dtype="Int64")

        min_val = col_data.min()
        max_val = col_data.max()

        # Auto-detect ranges if not provided
        if negative_range is None and zero_range is None and positive_range is None:
            unique_vals = set(col_data.dropna().unique())
            if unique_vals.issubset({0, 1}):
                # Pure binary data: map 0 -> -1, 1 -> 1 (same convention as itol.toolkit)
                result[col] = col_data.map({0: -1, 1: 1}).astype("Int64")
                continue
            if unique_vals.issubset({-1, 0, 1}):
                # Already ternary: keep as-is
                result[col] = col_data.astype("Int64")
                continue
            if min_val >= 0 and max_val <= 1:
                # Continuous [0,1]: split into three equal ranges
                # Convention: negative=[0,1/3), zero=[1/3,2/3], positive=(2/3,1]
                neg_range = (0.0, 1.0 / 3.0)
                zero_range = (1.0 / 3.0, 2.0 / 3.0)
                pos_range = (2.0 / 3.0, 1.0)
            elif min_val >= 0:
                # Non-negative data with values > 1:
                # Convention: values < 1.0 are neutral (zero), 1.0 is neutral, > 1.0 is positive
                # This avoids boundary overlap at exactly 1.0
                neg_range = None  # No negative range for non-negative data
                zero_range = (min_val, 1.0)  # inclusive on both ends
                pos_range = (1.0 + 1e-10, max_val)  # strictly > 1.0 (avoids overlap with zero)
            else:
                # Data has negative values
                raise ValueError(
                    f"Column '{col}' contains negative values not in binary format. Please provide explicit ranges."
                )
        else:
            neg_range = negative_range or (0.0, 0.5)
            zero_range = zero_range or (0.5, 0.5)
            pos_range = positive_range or (0.5, 1.0)

        # Apply ranges with consistent boundary control via the shared
        # ``_in_range`` helper. Bounds and precedence (pos > zero > neg) are
        # preserved exactly to keep numeric results unchanged. The positive
        # band intentionally passes ``not lower_inclusive`` to reproduce the
        # original (asymmetric) lower-bound behaviour where values equal to the
        # boundary are excluded from the positive band.
        if neg_range is not None:
            neg_mask = _in_range(col_data, neg_range, lower_inclusive, upper_inclusive)
            converted[neg_mask] = -1

        zero_mask = _in_range(col_data, zero_range, lower_inclusive, upper_inclusive)
        converted[zero_mask] = 0

        pos_mask = _in_range(col_data, pos_range, not lower_inclusive, upper_inclusive)
        converted[pos_mask] = 1

        result[col] = converted

    return result


def category_to_connect(
    taxonomy_path: str,
    tree_path: str,
    column: str,
    id_column: str = "id",
) -> dict:
    """Convert same-category nodes to connection pairs."""
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}

    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)].copy()

    groups = df.groupby(column)["id"].apply(list)
    connections = []
    for group_name, ids in groups.items():
        if pd.isna(group_name) or str(group_name).strip() == "":
            continue
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                connections.append((ids[i], ids[j]))

    return {"column": column, "connections": connections}


def wide_to_long(
    input_file: str,
    output_file: str,
    id_column: str = "id",
    value_name: str = "value",
    var_name: str = "variable",
) -> str:
    """Convert wide format to long format."""
    df = pd.read_csv(input_file, sep=None, engine="python")
    if id_column in df.columns:
        long_df = df.melt(id_vars=[id_column], var_name=var_name, value_name=value_name)
    else:
        long_df = df.melt(id_vars=[df.columns[0]], var_name=var_name, value_name=value_name)
    long_df.to_csv(output_file, index=False)
    return output_file


def long_to_wide(
    input_file: str,
    output_file: str,
    id_column: str = "id",
    variable_column: str = "variable",
    value_column: str = "value",
) -> str:
    """Convert long format to wide format."""
    df = pd.read_csv(input_file, sep=None, engine="python")
    wide_df = df.pivot(index=id_column, columns=variable_column, values=value_column).reset_index()
    wide_df.to_csv(output_file, index=False)
    return output_file


def df_tree(
    df_or_path: pd.DataFrame | str,
    columns: list[str] | None = None,
    main: str = "col",
    order: str = "none",
    metric: str = "euclidean",
    linkage_method: str = "average",
    id_column: str = "id",
) -> str:
    """Build a phylogenetic tree (Newick format) directly from a DataFrame.

    The tree is constructed using hierarchical clustering on either row or
    column similarities.

    Args:
        df_or_path: pandas DataFrame or path to a CSV/TSV file.
        columns: Column names to use for distance calculation.
            If None, all non-id numeric columns are used.
        main: Orientation of clustering:

            - ``'col'`` – columns are features; rows are leaf nodes.
            - ``'row'`` – rows are features; columns are leaf nodes.
        order: Leaf ordering strategy:

            - ``'none'`` – no reordering.
            - ``'hclust'`` – order leaves by hierarchical clustering.
        metric: Distance metric passed to :func:`scipy.spatial.distance.pdist`.
        linkage_method: Linkage method passed to
            :func:`scipy.cluster.hierarchy.linkage`.
        id_column: Name of the ID column when *df_or_path* is a file path.

    Returns:
        A Newick-formatted tree string.

    Raises:
        ValueError: If *main* or *order* is not one of the allowed values.
    """
    import numpy as np
    from scipy.cluster.hierarchy import leaves_list, to_tree
    from scipy.cluster.hierarchy import linkage as scipy_linkage
    from scipy.spatial.distance import pdist

    if main not in ("col", "row"):
        raise ValueError("main must be 'col' or 'row'")
    if order not in ("none", "hclust"):
        raise ValueError("order must be 'none' or 'hclust'")

    # Load data
    if isinstance(df_or_path, str):
        df = pd.read_csv(df_or_path, sep=None, engine="python")
        if id_column in df.columns:
            labels = df[id_column].astype(str).tolist()
            df = df.drop(columns=[id_column])
        else:
            labels = [str(i) for i in range(len(df))]
    else:
        df = df_or_path.copy()
        if id_column in df.columns:
            labels = df[id_column].astype(str).tolist()
            df = df.drop(columns=[id_column])
        else:
            labels = [str(i) for i in range(len(df))]

    # Determine columns to use
    if columns is not None:
        use_cols = [c for c in columns if c in df.columns]
        if not use_cols:
            raise ValueError(f"None of the specified columns found in DataFrame: {columns}")
        df = df[use_cols]

    # Convert to numeric, dropping non-numeric columns silently
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    numeric_df = numeric_df.dropna(axis=1, how="all")
    if numeric_df.empty:
        raise ValueError("No numeric columns available for distance calculation")

    # Build matrix based on main orientation
    if main == "col":
        matrix = numeric_df.values
        leaf_labels = labels
    else:  # main == 'row'
        matrix = numeric_df.values.T
        leaf_labels = list(numeric_df.columns)

    # Remove rows/cols with all NaN
    valid_mask = ~np.isnan(matrix).all(axis=1)
    matrix = matrix[valid_mask]
    leaf_labels = [leaf_labels[i] for i in range(len(leaf_labels)) if valid_mask[i]]

    # Hierarchical clustering
    dist = pdist(matrix, metric=metric)
    Z = scipy_linkage(dist, method=linkage_method)

    # Optional ordering.
    # IMPORTANT: `to_tree(Z)` assigns each leaf `node.id` according to the matrix
    # ROW ORDER the linkage was computed on. Reordering only `leaf_labels` (the old
    # behavior) silently detached names from their subtrees and produced a
    # taxonomically wrong tree. To keep labels strictly aligned with the matrix rows
    # we reorder BOTH the matrix and the labels by the dendrogram order, then rebuild
    # the tree on the reordered data. Recomputing the linkage uses identical pairwise
    # distances, so topology and branch lengths are unchanged.
    if order == "hclust":
        leaf_order = leaves_list(Z)
        matrix = matrix[leaf_order]
        leaf_labels = [leaf_labels[i] for i in leaf_order]
        dist = pdist(matrix, metric=metric)
        Z = scipy_linkage(dist, method=linkage_method)

    root = to_tree(Z, rd=False)

    def _to_newick(node: Any, leaf_labels: list[str], parent_dist: float = 0) -> str:
        if node.is_leaf():
            # Branch length = parent height - leaf height (leaf height = 0)
            branch_len = parent_dist
            return f"{leaf_labels[node.id]}:{branch_len:.6f}"
        left = _to_newick(node.left, leaf_labels, node.dist)
        right = _to_newick(node.right, leaf_labels, node.dist)
        # Branch length from parent to this node
        branch_len = parent_dist - node.dist
        return f"({left},{right}):{branch_len:.6f}"

    # P1-xx: Pass the root's own height as `parent_dist` so the root branch length
    # evaluates to 0 (parent_dist - root.dist == 0) instead of a negative value.
    # Internal nodes still receive their parent's distance, so child branch lengths
    # remain positive and the Newick output is valid.
    return _to_newick(root, leaf_labels, root.dist) + ";"


# Keep backward-compatible alias
anno_col_group = group_columns
