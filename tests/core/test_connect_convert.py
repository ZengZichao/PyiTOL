"""Tests for PyiTOL core connect_convert module."""

import pandas as pd

from pyitol.core.connect_convert import matrix_to_connect


class TestMatrixToConnect:
    def test_basic_dataframe(self):
        df = pd.DataFrame(
            {
                "id": ["A", "B", "C"],
                "f1": [1, 1, 0],
                "f2": [1, 0, 1],
            }
        )
        result = matrix_to_connect(df)
        assert isinstance(result, list)
        assert len(result) > 0
        assert "id1" in result[0]
        assert "id2" in result[0]
        assert "weight" in result[0]
        assert "color" in result[0]

    def test_string_input(self, tmp_path):
        p = tmp_path / "matrix.tsv"
        p.write_text("id\tf1\tf2\nA\t1\t1\nB\t1\t0\nC\t0\t1\n")
        result = matrix_to_connect(str(p))
        assert isinstance(result, list)
        assert len(result) > 0

    def test_string_input_no_id_column(self, tmp_path):
        p = tmp_path / "matrix.tsv"
        p.write_text("f1\tf2\n1\t1\n1\t0\n0\t1\n")
        result = matrix_to_connect(str(p))
        assert isinstance(result, list)
        # When no id column, first column values become ids
        assert result[0]["id1"] == "1"

    def test_dataframe_no_id_no_columns(self):
        df = pd.DataFrame(
            {
                "f1": [1, 1, 0],
                "f2": [1, 0, 1],
            }
        )
        result = matrix_to_connect(df)
        assert isinstance(result, list)
        assert result[0]["id1"].startswith("node_")

    def test_weight_mode_count(self):
        df = pd.DataFrame(
            {
                "id": ["A", "B", "C"],
                "f1": [1, 1, 0],
                "f2": [1, 0, 1],
            }
        )
        result = matrix_to_connect(df, weight_mode="count")
        assert isinstance(result, list)
        # weight should be integer count, not ratio
        assert all(isinstance(r["weight"], float) for r in result)

    def test_max_connections(self):
        df = pd.DataFrame(
            {
                "id": [f"N{i}" for i in range(10)],
            }
        )
        # Add many columns so there are many pairwise connections
        for i in range(10):
            df[f"f{i}"] = [1] * 10
        result = matrix_to_connect(df, max_connections=5)
        assert len(result) == 5
