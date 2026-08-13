"""Tests for PyiTOL core column_group module."""

import pandas as pd

from pyitol.core.column_group import group_columns


class TestGroupColumns:
    def test_basic_sum(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\tATP\tCOX\tPSI\nA\t1\t2\t3\nB\t4\t5\t6\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"energy": ["ATP", "COX"], "photosynthesis": ["PSI"]},
        )
        df = pd.read_csv(out, sep=None, engine="python")
        assert "energy" in df.columns
        assert "photosynthesis" in df.columns

    def test_no_valid_cols(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\tATP\tCOX\nA\t1\t2\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"energy": ["NONEXISTENT"]},
        )
        df = pd.read_csv(out, sep=None, engine="python")
        # No valid columns in group_map, so ungrouped columns remain
        assert "ATP" in df.columns

    def test_group_by(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\tgroup\tval1\tval2\nA\tX\t1\t2\nB\tX\t3\t4\nC\tY\t5\t6\n")
        out = tmp_path / "output.tsv"
        group_columns(str(p), str(out), group_by="group")
        df = pd.read_csv(out, sep=None, engine="python")
        assert "group" in df.columns

    def test_melt_fallback(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\ta\tb\nA\t1\t2\nB\t3\t4\n")
        out = tmp_path / "output.tsv"
        group_columns(str(p), str(out))
        df = pd.read_csv(out, sep=None, engine="python")
        assert "group" in df.columns
        assert "value" in df.columns

    def test_agg_mean(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\ta\tb\nA\t1\t3\nB\t2\t4\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"combined": ["a", "b"]},
            agg_func="mean",
        )
        df = pd.read_csv(out, sep=None, engine="python")
        assert df["combined"].iloc[0] == 2.0

    def test_agg_max(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\ta\tb\nA\t1\t3\nB\t2\t4\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"combined": ["a", "b"]},
            agg_func="max",
        )
        df = pd.read_csv(out, sep=None, engine="python")
        assert df["combined"].iloc[0] == 3.0

    def test_agg_min(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\ta\tb\nA\t1\t3\nB\t2\t4\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"combined": ["a", "b"]},
            agg_func="min",
        )
        df = pd.read_csv(out, sep=None, engine="python")
        assert df["combined"].iloc[0] == 1.0

    def test_agg_else(self, tmp_path):
        p = tmp_path / "input.tsv"
        p.write_text("id\ta\tb\nA\t1\t3\nB\t2\t4\n")
        out = tmp_path / "output.tsv"
        group_columns(
            str(p),
            str(out),
            group_map={"combined": ["a", "b"]},
            agg_func="median",
        )
        df = pd.read_csv(out, sep=None, engine="python")
        # Falls back to sum
        assert df["combined"].iloc[0] == 4.0
