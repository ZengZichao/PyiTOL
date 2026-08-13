"""Connection conversion module - convert 0/1 matrix to connection pairs."""

from __future__ import annotations

import pandas as pd


def matrix_to_connect(
    df_or_input_file: pd.DataFrame | str,
    columns: list[str] | None = None,
    weight_mode: str = "co-occurrence",
    min_weight: float = 0.5,
    max_connections: int = 500,
    id_column: str = "id",
) -> list[dict]:
    """Convert a 0/1 matrix to connection pairs with co-occurrence weight.

    Args:
        df_or_input_file: DataFrame or path to CSV file
        columns: Column names to use (if DataFrame provided)
        weight_mode: 'co-occurrence' or 'count'
        min_weight: Minimum co-occurrence count or ratio threshold
        max_connections: Maximum number of connections to return
        id_column: ID column name (when input is file path)

    Returns:
        List of dicts with keys: id1, id2, weight, color
    """
    if isinstance(df_or_input_file, str):
        df = pd.read_csv(df_or_input_file, sep=None, engine="python")
        if id_column in df.columns:
            id_vals = df[id_column]
            matrix = df.drop(columns=[id_column])
        else:
            id_vals = df.iloc[:, 0]
            matrix = df.iloc[:, 1:]
    else:
        df = df_or_input_file.copy()
        id_vals = df["id"] if "id" in df.columns else None
        matrix = df.drop(columns=["id"]) if id_vals is not None else df[columns] if columns else df

    # Ensure binary numeric
    matrix = matrix.apply(pd.to_numeric, errors="coerce").fillna(0)

    # If columns are features (not node IDs), transpose so each row is a node
    # In the 0/1 matrix from category_to_binary, rows are nodes and columns are categories
    # We want connections between NODES (rows) based on shared categories
    node_ids = id_vals.astype(str).tolist() if id_vals is not None else [f"node_{i}" for i in range(len(matrix))]
    matrix_values = matrix.values
    n_nodes = len(node_ids)

    connections = []
    for i in range(n_nodes):
        for j in range(i + 1, n_nodes):
            # Count co-occurrence: both have 1 in same columns
            shared = ((matrix_values[i] == 1) & (matrix_values[j] == 1)).sum()
            total = len(matrix.columns)

            weight = (shared / total if total > 0 else 0) if weight_mode == "co-occurrence" else shared

            if weight >= min_weight:
                # Color intensity based on weight
                intensity = min(int(weight * 255), 255)
                color = f"#{intensity:02x}{intensity:02x}{intensity:02x}"
                connections.append(
                    {
                        "id1": node_ids[i],
                        "id2": node_ids[j],
                        "weight": float(weight),
                        "color": color,
                    }
                )

    # Sort by weight descending and limit
    connections.sort(key=lambda x: x["weight"], reverse=True)
    if len(connections) > max_connections:
        connections = connections[:max_connections]

    return connections
