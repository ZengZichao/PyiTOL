"""Tests for pyitol.core.binary_convert module."""

from __future__ import annotations

import pandas as pd

from pyitol.core.binary_convert import category_to_binary

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _write_csv(path, content: str) -> str:
    """Write raw CSV text to *path* and return the path as a string."""
    path.write_text(content, encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


class TestCategoryToBinary:
    """Tests for the category_to_binary function."""

    def test_basic_conversion(self, tmp_path):
        """Non-empty values become '1', empty/NaN values become '0'."""
        csv_content = "id,genus,species\nseq1,Bacteroides,fragilis\nseq2,,vulgatus\nseq3,Clostridium,\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        result = category_to_binary(taxonomy_path, output_path, columns=["genus", "species"])

        assert result == output_path
        df = pd.read_csv(output_path, dtype=str)

        assert list(df["id"]) == ["seq1", "seq2", "seq3"]
        assert list(df["genus"]) == ["1", "0", "1"]
        assert list(df["species"]) == ["1", "1", "0"]

    def test_custom_id_column(self, tmp_path):
        """The id_column parameter renames the chosen column to 'id'."""
        csv_content = "name,phylum,class\nsampleA,Firmicutes,Clostridia\nsampleB,Bacteroidota,\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(taxonomy_path, output_path, columns=["phylum", "class"], id_column="name")

        df = pd.read_csv(output_path, dtype=str)
        assert "id" in df.columns
        assert list(df["id"]) == ["sampleA", "sampleB"]
        assert list(df["phylum"]) == ["1", "1"]
        assert list(df["class"]) == ["1", "0"]

    def test_multiple_columns(self, tmp_path):
        """All specified columns are converted to binary."""
        csv_content = "id,a,b,c,d\nr1,x,,y,\nr2,,,z,w\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(
            taxonomy_path,
            output_path,
            columns=["a", "b", "c", "d"],
        )

        df = pd.read_csv(output_path, dtype=str)
        assert list(df["a"]) == ["1", "0"]
        assert list(df["b"]) == ["0", "0"]
        assert list(df["c"]) == ["1", "1"]
        assert list(df["d"]) == ["0", "1"]

    def test_output_file_is_valid_csv(self, tmp_path):
        """Output file exists, has correct header and comma-separated format."""
        csv_content = "id,genus\nseq1,Bacteroides\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "result.csv")

        category_to_binary(taxonomy_path, output_path, columns=["genus"])

        # Re-read with pandas to confirm valid CSV structure
        df = pd.read_csv(output_path, dtype=str)
        assert list(df.columns) == ["id", "genus"]
        assert len(df) == 1
        assert df.iloc[0]["id"] == "seq1"
        assert df.iloc[0]["genus"] == "1"

    def test_empty_string_and_whitespace_treated_as_zero(self, tmp_path):
        """Empty strings and whitespace-only cells are treated as '0'."""
        csv_content = "id,status\nseq1,present\nseq2, \nseq3,\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(taxonomy_path, output_path, columns=["status"])

        df = pd.read_csv(output_path, dtype=str)
        assert list(df["status"]) == ["1", "0", "0"]

    def test_all_rows_empty(self, tmp_path):
        """When every value in a column is empty, all become '0'."""
        csv_content = "id,col1\nseq1,\nseq2,\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(taxonomy_path, output_path, columns=["col1"])

        df = pd.read_csv(output_path, dtype=str)
        assert list(df["col1"]) == ["0", "0"]

    def test_tab_separated_input(self, tmp_path):
        """The function accepts tab-separated input (sep=None + engine='python')."""
        csv_content = "id\tgenus\nseq1\tBacteroides\nseq2\t\n"
        taxonomy_path = _write_csv(tmp_path / "tax.tsv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(taxonomy_path, output_path, columns=["genus"])

        df = pd.read_csv(output_path, dtype=str)
        assert list(df["genus"]) == ["1", "0"]

    def test_only_id_and_target_columns_in_output(self, tmp_path):
        """Columns not listed in `columns` are excluded from the output."""
        csv_content = "id,genus,species,extra\nseq1,Bac,frag,info\n"
        taxonomy_path = _write_csv(tmp_path / "tax.csv", csv_content)
        output_path = str(tmp_path / "out.csv")

        category_to_binary(taxonomy_path, output_path, columns=["genus"])

        df = pd.read_csv(output_path, dtype=str)
        assert list(df.columns) == ["id", "genus"]
        assert "species" not in df.columns
        assert "extra" not in df.columns
