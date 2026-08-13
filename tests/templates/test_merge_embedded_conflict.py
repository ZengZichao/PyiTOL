"""Regression test for ``merge_embedded_taxonomy`` conflict branch.

Reproduces the source bug routed by QA (Phase-3 item 1 final): when the same
id carries *different* values in the embedded source vs the table, the conflict
branch must (a) not raise ``KeyError`` and (b) keep the embedded value
(embedded wins). The previous implementation indexed a positional
``RangeIndex`` Series by a string id label (``aligned.loc[tip_id]``), which
crashed on ids such as 'A'.

These tests exercise the unit directly so the regression is locked regardless
of CLI plumbing.
"""

from __future__ import annotations

import pandas as pd
from rich.console import Console

from pyitol.cli.taxonomy_cmd import merge_embedded_taxonomy


def test_conflict_path_keeps_embedded_value_and_does_not_crash():
    """Conflicting id 'A' (table=Proteo, embedded=Firmicutes) must keep the
    embedded value, emit a warning, and never raise."""
    console = Console(record=True)
    tax_df = pd.DataFrame(
        {
            "id": ["A", "B", "C"],
            "Phylum": ["Proteo", "Actino", "Eury"],
        }
    )
    embedded_df = pd.DataFrame(
        {
            "id": ["A", "B", "C"],
            "Phylum": ["Firmicutes", "Actino", "Eury"],  # A conflicts with table
        }
    )

    result = merge_embedded_taxonomy(embedded_df, tax_df, console)

    # 1) Embedded wins on the conflicting id.
    assert result.loc[result["id"] == "A", "Phylum"].iloc[0] == "Firmicutes"
    # 2) Non-conflicting values are preserved verbatim.
    assert result.loc[result["id"] == "B", "Phylum"].iloc[0] == "Actino"
    assert result.loc[result["id"] == "C", "Phylum"].iloc[0] == "Eury"
    # 3) Conflict warning emitted (names the id/column).
    text = console.export_text()
    assert "冲突" in text and "A" in text


def test_gap_fill_and_embedded_only_column():
    """Embedded fills a table gap and adds an embedded-only column without
    disturbing tax-only columns."""
    console = Console(record=True)
    tax_df = pd.DataFrame(
        {
            "id": ["A", "B"],
            "Genus": ["Escherichia", "Salmonella"],
        }
    )
    embedded_df = pd.DataFrame(
        {
            "id": ["A", "B"],
            "Species": ["coli", None],  # partial embedded-only column
        }
    )

    result = merge_embedded_taxonomy(embedded_df, tax_df, console)

    # Tax-only column untouched.
    assert list(result["Genus"]) == ["Escherichia", "Salmonella"]
    # Embedded-only column added; embedded value kept, missing gap stays NaN.
    assert "Species" in result.columns
    assert result.loc[result["id"] == "A", "Species"].iloc[0] == "coli"
    assert pd.isna(result.loc[result["id"] == "B", "Species"].iloc[0])
