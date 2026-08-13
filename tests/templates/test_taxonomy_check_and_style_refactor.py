"""Independent regression tests for the taxonomy_check_and_style refactor.

The god-function ``taxonomy_check_and_style`` (cli/taxonomy_cmd.py) was refactored
into three helpers:
  * ``resolve_special_identifier_members``  (special-identifier resolution + tree-tip filter)
  * ``merge_embedded_taxonomy``            (vectorized embedded-taxonomy merge)
  * ``generate_style_template_for_action`` (single-action style template writer)

These tests verify that:
  * the helpers exist and behave per their documented contract,
  * ``merge_embedded_taxonomy`` follows "embedded fills gaps, conflicts -> embedded wins",
  * the caller ``taxonomy_check_and_style`` actually invokes the extracted helpers,
  * a CLI smoke of ``taxonomy check-and-style`` exits 0 and produces a file.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd
import pytest
import typer
from rich.console import Console
from typer.testing import CliRunner

from pyitol.cli import taxonomy_cmd
from pyitol.cli.main import app
from pyitol.cli.taxonomy_cmd import (
    generate_style_template_for_action,
    merge_embedded_taxonomy,
    resolve_special_identifier_members,
)

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"


# --------------------------------------------------------------------------- #
# merge_embedded_taxonomy: vectorized merge semantics
# --------------------------------------------------------------------------- #
class TestMergeEmbeddedTaxonomy:
    def test_fill_gaps_conflict_and_columns(self):
        console = Console(record=True)
        tax_df = pd.DataFrame(
            {
                "id": ["A", "B", "C"],
                "Kingdom": ["Bacteria", "Bacteria", "Archaea"],
                "Phylum": ["Proteo", None, "Eury"],  # B has a gap
            }
        )
        embedded_df = pd.DataFrame(
            {
                "id": ["A", "B", "C"],
                # A: conflict (Proteo vs Firmicutes); B: fills gap; C: identical
                "Phylum": ["Firmicutes", "Actino", "Eury"],
                "Class": ["Alpha", "Beta", "Gamma"],  # embedded-only column
            }
        )

        result = merge_embedded_taxonomy(embedded_df, tax_df, console)

        # 1) Gap fill: B.Phylum NaN -> embedded value 'Actino'
        assert result.loc[result["id"] == "B", "Phylum"].iloc[0] == "Actino"
        # 2) Conflict: A.Phylum 'Proteo' vs embedded 'Firmicutes' -> embedded wins
        assert result.loc[result["id"] == "A", "Phylum"].iloc[0] == "Firmicutes"
        # 3) Identical value unchanged
        assert result.loc[result["id"] == "C", "Phylum"].iloc[0] == "Eury"
        # 4) Tax-only column preserved untouched
        assert list(result["Kingdom"]) == ["Bacteria", "Bacteria", "Archaea"]
        # 5) Embedded-only column added for all rows
        assert "Class" in result.columns
        assert list(result["Class"]) == ["Alpha", "Beta", "Gamma"]
        # 6) Conflict warning emitted
        assert "冲突" in console.export_text()

    def test_embedded_leaves_tax_only_values_intact(self):
        console = Console()
        tax_df = pd.DataFrame(
            {
                "id": ["A", "B"],
                "Genus": ["Escherichia", "Salmonella"],
            }
        )
        embedded_df = pd.DataFrame(
            {
                "id": ["A", "B"],
                "Species": ["coli", "enterica"],  # embedded-only column, no overlap
            }
        )
        result = merge_embedded_taxonomy(embedded_df, tax_df, console)
        assert list(result["Genus"]) == ["Escherichia", "Salmonella"]
        assert list(result["Species"]) == ["coli", "enterica"]


# --------------------------------------------------------------------------- #
# resolve_special_identifier_members
# --------------------------------------------------------------------------- #
class TestResolveSpecialIdentifierMembers:
    def _tree_tax(self, tmp_path):
        tree = tmp_path / "t.nwk"
        tree.write_text(SIMPLE_NEWICK)
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tDomain\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        return str(tree), str(tax)

    def test_normal_returns_tree_filtered_members(self, tmp_path):
        console = Console(record=True)
        tree, tax = self._tree_tax(tmp_path)
        members = resolve_special_identifier_members("LUCA", tax, tree, "id", "Domain", console)
        # All four tips belong to Bacteria/Archaea and are in the tree.
        assert set(members) == {"A", "B", "C", "D"}

    def test_empty_members_raises_typer_exit(self, tmp_path, monkeypatch):
        console = Console()
        tree, tax = self._tree_tax(tmp_path)
        # Simulate the resolver returning an empty list (defensive branch).
        monkeypatch.setattr(taxonomy_cmd, "resolve_special_identifier", lambda *a, **k: [])
        with pytest.raises(typer.Exit) as exc:
            resolve_special_identifier_members("LUCA", tax, tree, "id", "Domain", console)
        assert exc.value.exit_code == 1


# --------------------------------------------------------------------------- #
# generate_style_template_for_action
# --------------------------------------------------------------------------- #
class TestGenerateStyleTemplateForAction:
    def test_three_actions_write_correct_dataset(self, tmp_path):
        ctx = MagicMock()
        members = ["A", "B"]

        p1 = generate_style_template_for_action(
            ctx, "color-branch", members, "grp", "#ff0000", "TAB", str(tmp_path / "b.txt")
        )
        c1 = Path(p1).read_text()
        assert "TREE_COLORS" in c1  # legacy iTOL header for tree_colors
        assert "A\tclade\t#ff0000" in c1

        p2 = generate_style_template_for_action(
            ctx, "highlight", members, "grp", "#00ff00", "TAB", str(tmp_path / "h.txt")
        )
        c2 = Path(p2).read_text()
        assert "DATASET_STYLE" in c2
        assert "A\tlabel_background\t#00ff00" in c2

        p3 = generate_style_template_for_action(
            ctx, "color-strip", members, "grp", "#0000ff", "TAB", str(tmp_path / "s.txt")
        )
        c3 = Path(p3).read_text()
        assert "DATASET_COLORSTRIP" in c3
        assert "STRIP_WIDTH" in c3

    def test_unknown_action_raises_exit(self, tmp_path):
        ctx = MagicMock()
        with pytest.raises(typer.Exit) as exc:
            generate_style_template_for_action(ctx, "bogus", ["A"], "grp", "#ff0000", "TAB", str(tmp_path / "x.txt"))
        assert exc.value.exit_code == 1


# --------------------------------------------------------------------------- #
# Caller wiring + CLI smoke
# --------------------------------------------------------------------------- #
class TestCallerWiringAndSmoke:
    def test_check_and_style_invokes_style_helper(self, tmp_path, monkeypatch):
        calls = []
        orig = taxonomy_cmd.generate_style_template_for_action

        def spy(ctx, action, members, label, color, separator, output):
            calls.append((action, label, list(members)))
            return orig(ctx, action, members, label, color, separator, output)

        monkeypatch.setattr(taxonomy_cmd, "generate_style_template_for_action", spy)

        # All tips share one group -> the group is the tree root -> monophyletic.
        tree = tmp_path / "t.nwk"
        tree.write_text(SIMPLE_NEWICK)
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tGroup\nA\tX\nB\tX\nC\tX\nD\tX\n")
        out = tmp_path / "styled.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "check-and-style",
                "--tree",
                str(tree),
                "--taxonomy",
                str(tax),
                "--taxon",
                "X",
                "--rank",
                "Group",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        # Helper must be called exactly once for the monophyletic group.
        assert len(calls) == 1
        assert calls[0][0] == "color-branch"  # default action
        assert set(calls[0][2]) == {"A", "B", "C", "D"}
        # Output file produced.
        assert out.exists()
        assert "TREE_COLORS" in out.read_text()

    def test_check_and_style_paraphyletic_exits_1(self, tmp_path):
        # Group Proteobacteria = {A,B}; C,D are Euryarchaeota -> paraphyletic
        # per the monophyly engine (extra nodes C|D) -> no template, exit 1.
        tree = tmp_path / "t.nwk"
        tree.write_text(SIMPLE_NEWICK)
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tPhylum\nA\tProteobacteria\nB\tProteobacteria\nC\tEuryarchaeota\nD\tEuryarchaeota\n")
        out = tmp_path / "styled.txt"
        result = runner.invoke(
            app,
            [
                "taxonomy",
                "check-and-style",
                "--tree",
                str(tree),
                "--taxonomy",
                str(tax),
                "--taxon",
                "Proteobacteria",
                "--rank",
                "Phylum",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert not out.exists()
