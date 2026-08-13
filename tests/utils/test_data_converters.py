"""Tests for PyiTOL data converters module."""

from pathlib import Path

import pytest

from pyitol.utils.data_converters import (
    category_to_binary,
    category_to_connect,
    count_to_tree,
    df_tree,
    group_columns,
    long_to_wide,
    wide_to_long,
)

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = (
    "id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\t\nC\tArchaea\tEuryarchaeota\nD\t\tCrenarchaeota\n"
)


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "test.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


class TestCategoryToBinary:
    def test_non_empty_to_one(self, tree_file, taxonomy_file, tmp_path):
        output = tmp_path / "binary.csv"
        result = category_to_binary(taxonomy_file, str(output), ["Kingdom", "Phylum"])
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert list(df.columns) == ["id", "Kingdom", "Phylum"]
        assert str(df[df["id"] == "A"]["Kingdom"].values[0]) == "1"
        assert str(df[df["id"] == "A"]["Phylum"].values[0]) == "1"
        assert str(df[df["id"] == "B"]["Kingdom"].values[0]) == "1"
        assert str(df[df["id"] == "B"]["Phylum"].values[0]) == "0"
        assert str(df[df["id"] == "C"]["Kingdom"].values[0]) == "1"
        assert str(df[df["id"] == "C"]["Phylum"].values[0]) == "1"
        assert str(df[df["id"] == "D"]["Kingdom"].values[0]) == "0"
        assert str(df[df["id"] == "D"]["Phylum"].values[0]) == "1"


class TestCategoryToConnect:
    def test_same_category_pairs(self, tree_file, taxonomy_file):
        result = category_to_connect(taxonomy_file, tree_file, "Kingdom")
        assert len(result["connections"]) > 0
        assert result["column"] == "Kingdom"


class TestWideToLong:
    def test_conversion(self, tmp_path):
        data = "id\tcol1\tcol2\nA\t1\t2\nB\t3\t4\n"
        p = tmp_path / "wide.tsv"
        p.write_text(data)
        output = tmp_path / "long.csv"
        result = wide_to_long(str(p), str(output))
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert list(df.columns) == ["id", "variable", "value"]
        assert len(df) == 4


class TestLongToWide:
    def test_conversion(self, tmp_path):
        data = "id\tvariable\tvalue\nA\tcol1\t1\nA\tcol2\t2\nB\tcol1\t3\nB\tcol2\t4\n"
        p = tmp_path / "long.tsv"
        p.write_text(data)
        output = tmp_path / "wide.csv"
        result = long_to_wide(str(p), str(output))
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert "col1" in df.columns
        assert "col2" in df.columns
        assert len(df) == 2


class TestCountToTree:
    def test_conversion(self, tmp_path, tree_file):
        data = "id\tcount\nA\t10\nB\t20\nC\t30\nD\t40\n"
        p = tmp_path / "counts.tsv"
        p.write_text(data)
        result = count_to_tree(str(p), tree_file, "count")
        assert len(result["data"]) == 4


class TestGroupColumns:
    def test_grouping(self, tmp_path):
        data = "id\tA\tB\nX\t1\t2\nY\t3\t4\n"
        p = tmp_path / "grouped.tsv"
        p.write_text(data)
        output = tmp_path / "output.csv"
        result = group_columns(str(p), str(output))
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert "group" in df.columns
        assert "value" in df.columns

    def test_group_by_column(self, tmp_path):
        data = "id\tgroup\tA\tB\nX\tG1\t1\t2\nY\tG1\t3\t4\nZ\tG2\t5\t6\n"
        p = tmp_path / "grouped.tsv"
        p.write_text(data)
        output = tmp_path / "output.csv"
        result = group_columns(str(p), str(output), columns=["A", "B"], group_by="group", agg_func="sum")
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert len(df) == 2

    def test_group_regex(self, tmp_path):
        data = "id\tATP1\tATP2\tCOX1\tOther\nX\t1\t2\t3\t4\nY\t5\t6\t7\t8\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        output = tmp_path / "output.csv"
        result = group_columns(str(p), str(output), group_regex=r"^(ATP|COX)", agg_func="sum")
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert "^(ATP|COX)" in df.columns
        assert "Other" in df.columns

    def test_group_map(self, tmp_path):
        data = "id\tATP1\tATP2\tPSI\tPSII\nX\t1\t2\t3\t4\nY\t5\t6\t7\t8\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        output = tmp_path / "output.csv"
        gmap = {"energy": ["ATP1", "ATP2"], "photo": ["PSI", "PSII"]}
        result = group_columns(str(p), str(output), group_map=gmap, agg_func="sum")
        assert Path(result).exists()
        df = __import__("pandas").read_csv(result)
        assert "energy" in df.columns
        assert "photo" in df.columns
        assert df["energy"].iloc[0] == 3.0
        assert df["photo"].iloc[0] == 7.0

    def test_anno_col_group_alias(self, tmp_path):
        from pyitol.utils.data_converters import anno_col_group

        data = "id\tA\tB\nX\t1\t2\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        output = tmp_path / "output.csv"
        result = anno_col_group(str(p), str(output))
        assert Path(result).exists()


class TestConvertToBinaryMatrix:
    def test_pure_binary_data(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0\nB\t1\nC\t0\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(str(p), id_column="id")
        assert result["id"].tolist() == ["A", "B", "C"]
        assert result["col1"].tolist() == [-1, 1, -1]

    def test_ternary_data(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t-1\nB\t0\nC\t1\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(str(p), id_column="id")
        assert result["col1"].tolist() == [-1, 0, 1]

    def test_continuous_0_1_auto_range(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0.1\nB\t0.5\nC\t0.9\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(str(p), id_column="id")
        assert result["col1"].tolist() == [-1, 0, 1]

    def test_positive_only_auto_range(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0.5\nB\t1.0\nC\t5.0\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(str(p), id_column="id")
        # Fixed logic - values <= 1.0 are neutral (zero), > 1.0 are positive
        # zero_r=(0.5, 1.0), pos_range=(1.0, 5.0)
        # A(0.5): zero (0), B(1.0): zero (0), C(5.0): pos (1)
        assert result["col1"].tolist() == [0, 0, 1]

    def test_negative_values_explicit_range(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t-2\nB\t0\nC\t2\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(
            str(p), id_column="id", negative_range=(-3, -1), zero_range=(-1, 1), positive_range=(1, 3)
        )
        assert result["col1"].tolist() == [-1, 0, 1]

    def test_negative_values_without_range_raises(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t-2\nB\t0\nC\t1\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        with pytest.raises(ValueError, match="negative values"):
            convert_to_binary_matrix(str(p), id_column="id")

    def test_explicit_range_not_lower_inclusive(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0.0\nB\t0.3\nC\t0.5\nD\t0.7\nE\t1.0\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(
            str(p),
            id_column="id",
            negative_range=(0.0, 0.5),
            zero_range=(0.5, 0.5),
            positive_range=(0.5, 1.0),
            lower_inclusive=False,
            upper_inclusive=True,
        )
        # lower_inclusive=False: neg lower bound uses > (strict), pos lower bound uses >=
        # A(0.0): not > 0.0 → not in neg; 0.0 >= 0.5? No → not in pos → NA
        # B(0.3): 0.3 > 0.0 and <= 0.5 → in neg → -1
        # C(0.5): 0.5 > 0.0 and <= 0.5 → in neg, but also 0.5 >= 0.5 and <= 1.0 → in pos (overwrites) → 1
        # D(0.7): not <= 0.5 → not in neg; 0.7 >= 0.5 and <= 1.0 → in pos → 1
        # E(1.0): 1.0 >= 0.5 and <= 1.0 → in pos → 1
        vals = result["col1"].tolist()
        assert vals[1] == -1
        assert vals[2] == 1
        assert vals[3] == 1
        assert vals[4] == 1

    def test_explicit_range_not_upper_inclusive(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0.0\nB\t0.3\nC\t0.5\nD\t0.8\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(
            str(p),
            id_column="id",
            negative_range=(0.0, 0.4),
            zero_range=(0.4, 0.6),
            positive_range=(0.6, 1.0),
            lower_inclusive=True,
            upper_inclusive=False,
        )
        # lower_inclusive=True: neg lower bound >=, pos lower bound >
        # upper_inclusive=False: neg upper bound <, pos upper bound <
        # A(0.0): 0.0 >= 0.0 and < 0.4 → in neg → -1
        # B(0.3): 0.3 >= 0.0 and < 0.4 → in neg → -1
        # C(0.5): not < 0.4 → not in neg; 0.5 >= 0.4 and 0.5 < 0.6 → in zero → 0
        # D(0.8): not in neg; not in zero; 0.8 > 0.6 and 0.8 < 1.0 → in pos → 1
        vals = result["col1"].tolist()
        assert vals[0] == -1
        assert vals[1] == -1
        assert vals[2] == 0
        assert vals[3] == 1

    def test_explicit_range_both_inclusive_false(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "id\tcol1\nA\t0.0\nB\t0.5\nC\t1.0\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(
            str(p),
            id_column="id",
            negative_range=(0.0, 0.5),
            zero_range=(0.5, 0.5),
            positive_range=(0.5, 1.0),
            lower_inclusive=False,
            upper_inclusive=False,
        )
        # lower_inclusive=False: lower bound > (strict), upper_inclusive=False: upper bound < (strict)
        # A(0.0): not > 0.0 → not in neg → NA
        # B(0.5): 0.5 > 0.0 and 0.5 < 0.5 → False → not in neg; 0.5 > 0.5 → not in zero; 0.5 >= 0.5 and 0.5 < 1.0 → in pos → 1  # noqa: E501
        # C(1.0): not < 0.5 → not in neg; not < 0.5 → not in zero; 1.0 >= 0.5 and 1.0 < 1.0 → False → not in pos → NA
        vals = result["col1"].tolist()
        assert vals[1] == 1

    def test_no_id_column_uses_first_column(self, tmp_path):
        from pyitol.utils.data_converters import convert_to_binary_matrix

        data = "name\tcol1\nA\t0\nB\t1\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        result = convert_to_binary_matrix(str(p), id_column="id")
        # When id_column is not found, first column is used but renamed to id_column
        assert "id" in result.columns
        assert result["id"].tolist() == ["A", "B"]


class TestCategoryToConnectEdgeCases:
    def test_empty_group_skipped(self, tree_file, taxonomy_file):
        result = category_to_connect(taxonomy_file, tree_file, "Phylum")
        # B has empty Phylum, D also has empty-like values; still should return connections or empty
        assert "connections" in result

    def test_na_group_skipped(self, tree_file, tmp_path):
        data = "id\tKingdom\nA\tK1\nB\t\nC\tK1\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(data)
        result = category_to_connect(str(tax), tree_file, "Kingdom")
        # B has empty Kingdom -> skipped by groupby(dropna=True), A and C in K1 -> one connection
        assert result["connections"] == [("A", "C")]

    def test_whitespace_group_skipped(self, tree_file, tmp_path):
        data = "id\tKingdom\nA\tK1\nB\t   \nC\tK1\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(data)
        result = category_to_connect(str(tax), tree_file, "Kingdom")
        # B has whitespace-only Kingdom -> skipped by continue, A and C in K1 -> one connection
        assert result["connections"] == [("A", "C")]


class TestWideToLongEdgeCases:
    def test_no_id_column(self, tmp_path):
        data = "name\tcol1\tcol2\nA\t1\t2\nB\t3\t4\n"
        p = tmp_path / "wide.tsv"
        p.write_text(data)
        output = tmp_path / "long.csv"
        result = wide_to_long(str(p), str(output), id_column="missing")
        df = __import__("pandas").read_csv(result)
        assert len(df) == 4


class TestDfTree:
    def test_col_mode(self, tmp_path):
        data = "id\tA\tB\tC\nX\t1\t2\t3\nY\t4\t5\t6\nZ\t7\t8\t9\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        tree = df_tree(str(p), main="col", id_column="id")
        assert tree.endswith(";")
        assert "X" in tree or "Y" in tree or "Z" in tree

    def test_row_mode(self, tmp_path):
        data = "id\tA\tB\tC\nX\t1\t2\t3\nY\t4\t5\t6\nZ\t7\t8\t9\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        tree = df_tree(str(p), main="row", id_column="id")
        assert tree.endswith(";")
        # In row mode, columns become leaf nodes
        assert "A" in tree or "B" in tree or "C" in tree

    def test_hclust_order(self, tmp_path):
        data = "id\tA\tB\tC\nX\t1\t2\t3\nY\t4\t5\t6\nZ\t7\t8\t9\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        tree = df_tree(str(p), main="col", order="hclust", id_column="id")
        assert tree.endswith(";")

    def test_with_dataframe(self):
        import pandas as pd

        df = pd.DataFrame(
            {
                "id": ["X", "Y", "Z"],
                "A": [1.0, 4.0, 7.0],
                "B": [2.0, 5.0, 8.0],
                "C": [3.0, 6.0, 9.0],
            }
        )
        tree = df_tree(df, main="col")
        assert tree.endswith(";")
        assert "X" in tree or "Y" in tree or "Z" in tree

    def test_invalid_main(self, tmp_path):
        data = "id\tA\tB\nX\t1\t2\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        with pytest.raises(ValueError):
            df_tree(str(p), main="invalid")

    def test_invalid_order(self, tmp_path):
        data = "id\tA\tB\nX\t1\t2\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        with pytest.raises(ValueError):
            df_tree(str(p), order="invalid")

    def test_specified_columns(self, tmp_path):
        data = "id\tA\tB\tC\nX\t1\t2\t3\nY\t4\t5\t6\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        tree = df_tree(str(p), columns=["A", "B"], main="col", id_column="id")
        assert tree.endswith(";")

    def test_no_numeric_columns_raises(self, tmp_path):
        data = "id\tA\tB\nX\tfoo\tbar\nY\tbaz\tqux\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        with pytest.raises(ValueError):
            df_tree(str(p), main="col", id_column="id")

    def test_no_id_column_file(self, tmp_path):
        data = "A\tB\n1\t2\n3\t4\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        tree = df_tree(str(p), main="col")
        assert tree.endswith(";")

    def test_no_id_column_dataframe(self):
        import pandas as pd

        df = pd.DataFrame({"A": [1.0, 3.0], "B": [2.0, 4.0]})
        tree = df_tree(df, main="col")
        assert tree.endswith(";")

    def test_specified_columns_not_found(self, tmp_path):
        data = "id\tA\tB\nX\t1\t2\n"
        p = tmp_path / "data.tsv"
        p.write_text(data)
        with pytest.raises(ValueError, match="None of the specified columns"):
            df_tree(str(p), columns=["Z"], main="col", id_column="id")
