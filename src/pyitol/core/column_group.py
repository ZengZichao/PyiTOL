"""Column grouping module - group data columns by specified rules."""

from __future__ import annotations

import re

import pandas as pd


def group_columns(
    input_file: str,
    output_file: str,
    columns: list[str] | None = None,
    group_by: str | None = None,
    group_regex: str | None = None,
    group_map: dict[str, list[str]] | None = None,
    id_column: str = "id",
    agg_func: str = "sum",
) -> str:
    """Group data columns by specified rules and output to file.

    Enhanced reimplementation of itol.toolkit's anno_col_group() with regex
    and multiple attribute name support (independent Python implementation;
    itol.toolkit is an R package).

    Args:
        input_file: Input CSV/Excel file path.
        output_file: Output CSV file path.
        columns: Specific columns to include. If None, uses all non-id columns.
        group_by: Column name to group by (for row-wise grouping).
        group_regex: Regex pattern to match column names for grouping.
            e.g. r'^(ATP|COX|NADH)' will group columns starting with those prefixes.
        group_map: Dict mapping group names to lists of column names.
            e.g. {'energy': ['ATP', 'COX'], 'photosynthesis': ['PSI', 'PSII']}
        id_column: Name of the ID column.
        agg_func: Aggregation function for grouped columns ('sum', 'mean', 'max', 'min').

    Returns:
        Output file path.
    """
    df = pd.read_csv(input_file, sep=None, engine="python")
    if columns is None:
        columns = [c for c in df.columns if c != id_column]

    # Apply regex-based column grouping if provided
    if group_regex and not group_map:
        matched = [c for c in columns if re.search(group_regex, c)]
        group_map = {group_regex: matched} if matched else None

    # Apply explicit group_map grouping
    if group_map:
        result = pd.DataFrame({id_column: df[id_column]})
        used_cols = set()
        for group_name, member_cols in group_map.items():
            valid_cols = [c for c in member_cols if c in df.columns and c in columns]
            if not valid_cols:
                continue
            used_cols.update(valid_cols)
            numeric_df = df[valid_cols].apply(pd.to_numeric, errors="coerce")
            if agg_func == "sum":
                result[group_name] = numeric_df.sum(axis=1, skipna=True)
            elif agg_func == "mean":
                result[group_name] = numeric_df.mean(axis=1, skipna=True)
            elif agg_func == "max":
                result[group_name] = numeric_df.max(axis=1, skipna=True)
            elif agg_func == "min":
                result[group_name] = numeric_df.min(axis=1, skipna=True)
            else:
                result[group_name] = numeric_df.sum(axis=1, skipna=True)
        # Add remaining ungrouped columns
        remaining = [c for c in columns if c not in used_cols]
        for c in remaining:
            result[c] = df[c]
        grouped = result
    elif group_by and group_by in df.columns:
        agg_methods = {c: agg_func for c in columns if c in df.columns and c != group_by}
        grouped = df.groupby(group_by).agg(agg_methods).reset_index()
    else:
        df_melted = df.melt(id_vars=[id_column], value_vars=columns, var_name="group", value_name="value")
        grouped = df_melted

    grouped.to_csv(output_file, index=False)
    return output_file
