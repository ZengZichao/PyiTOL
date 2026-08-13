"""Binary conversion module - convert taxonomy columns to binary matrix."""

from __future__ import annotations

import pandas as pd


def category_to_binary(
    taxonomy_path: str,
    output_path: str,
    columns: list[str],
    id_column: str = "id",
) -> str:
    """Convert taxonomy columns to binary matrix (non-empty=1, empty=0).

    Returns the output file path.
    """
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})

    result_data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for col in columns:
            val = row.get(col, "")
            row_data[col] = "1" if pd.notna(val) and str(val).strip() != "" else "0"
        result_data.append(row_data)

    result_df = pd.DataFrame(result_data)
    result_df.to_csv(output_path, index=False)
    return output_path
