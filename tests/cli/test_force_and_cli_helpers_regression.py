"""QA independent regression tests for Item 1: --force deep fix + CLI helpers.

Items verified:
- `pyitol template create <type> --force` overwrites a pre-existing,
  different-content output file (exit_code == 0, content replaced).
- `pyitol template create <type>` without --force refuses to overwrite
  (exit_code != 0) and keeps the original file.
- `--no-clobber` skips an existing file (exit 0, original preserved).
- Unit: resolve_output honors force / no_clobber correctly.
- Unit: load_filtered_taxonomy filters taxonomy rows down to tree tips and
  renames a custom id column.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from pyitol.cli.common import load_filtered_taxonomy, load_tree_tips, resolve_output
from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = (
    "id\tKingdom\tValue\n"
    "A\tBacteria\t10\n"
    "B\tBacteria\t20\n"
    "C\tArchaea\t30\n"
    "D\tArchaea\t40\n"
    "E\tBacteria\t99\n"  # not a tree tip -> should be dropped
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


class TestForceOverwriteCLI:
    def test_force_overwrites_existing(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "color_strip.txt"
        output.write_text("PRE-EXISTING CONTENT THAT MUST BE REPLACED")
        assert output.read_text() == "PRE-EXISTING CONTENT THAT MUST BE REPLACED"

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "color-strip",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
                "--force",
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        new_content = output.read_text()
        assert new_content != "PRE-EXISTING CONTENT THAT MUST BE REPLACED"
        assert "DATASET_COLORSTRIP" in new_content

    def test_no_force_keeps_original(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "color_strip.txt"
        original = "IMMUTABLE ORIGINAL"
        output.write_text(original)

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "color-strip",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code != 0, result.output
        assert output.read_text() == original

    def test_no_clobber_skips_existing(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "color_strip.txt"
        original = "SHOULD REMAIN"
        output.write_text(original)

        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "color-strip",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
                "--no-clobber",
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.read_text() == original


class TestResolveOutput:
    def test_existing_no_force_raises_systemexit(self, tmp_path):
        p = tmp_path / "x.txt"
        p.write_text("data")
        with pytest.raises(SystemExit):
            resolve_output(p, force=False, no_clobber=False)

    def test_existing_force_returns_path(self, tmp_path):
        p = tmp_path / "x.txt"
        p.write_text("data")
        out = resolve_output(p, force=True, no_clobber=False)
        assert out is not None
        assert Path(out) == p

    def test_existing_no_clobber_returns_none(self, tmp_path):
        p = tmp_path / "x.txt"
        p.write_text("data")
        assert resolve_output(p, force=False, no_clobber=True) is None

    def test_new_file_returns_path(self, tmp_path):
        p = tmp_path / "new.txt"
        out = resolve_output(p, force=False, no_clobber=False)
        assert out is not None


class TestLoadFilteredTaxonomy:
    def test_rows_filtered_to_tips(self, tree_file, taxonomy_file):
        _tree, df, tip_set, _tip_order = load_filtered_taxonomy(tree_file, taxonomy_file, id_column="id")
        assert tip_set == {"A", "B", "C", "D"}
        assert set(df["id"]) == {"A", "B", "C", "D"}
        assert len(df) == 4
        assert "E" not in set(df["id"])

    def test_custom_id_column_renamed(self, tmp_path):
        tree = tmp_path / "t.nwk"
        tree.write_text(SIMPLE_NEWICK)
        tax = tmp_path / "tax.tsv"
        tax.write_text("taxon\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\nE\tBacteria\n")
        _tree_obj, df, _tip_set, _ = load_filtered_taxonomy(str(tree), str(tax), id_column="taxon")
        assert set(df["id"]) == {"A", "B", "C", "D"}
        assert "E" not in set(df["id"])

    def test_load_tree_tips(self, tree_file):
        tips = load_tree_tips(tree_file)
        assert tips == {"A", "B", "C", "D"}
