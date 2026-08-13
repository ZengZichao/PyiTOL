"""Tests using realistic biological data from tests/data/ fixtures.

These tests exercise PyiTOL with real-world-style data (8-tip tree with
biologically meaningful branch lengths, taxonomy with real phylum/genus/species
names and numeric columns like genome_size and gc_content) instead of the
simplified A/B/C/D test data used in unit tests.

This file also validates the expected-output reference files
(4taxa_monophyly.csv, 4taxa_tax_extract.csv) against actual computation results,
and exercises the iTOL template reference files in tests/data/.
"""

import csv

import pytest

from pyitol.core.monophyly import check_monophyly
from pyitol.core.parser import MetadataParser, TreeParser
from pyitol.core.taxonomy import extract_taxonomy_with_stats
from pyitol.core.validator import TemplateValidator
from pyitol.utils.tree_info import get_tree_info

# ---- Tree parsing with realistic data ----


class TestRealisticTreeParsing:
    """Parse the 8-tip tree with real branch lengths and verify structure."""

    def test_parse_eight_tip_tree(self, sample_tree_path):
        parser = TreeParser(sample_tree_path)
        assert parser.get_tip_count() == 8
        tips = set(parser.tip_labels)
        assert tips == {"A", "B", "C", "D", "E", "F", "G", "H"}

    def test_tree_has_two_root_children(self, sample_tree_path):
        """The tree ((B,(A,(C,(D,E)))),(F,(G,H))) has 2 direct children of root."""
        parser = TreeParser(sample_tree_path)
        tree = parser.get_tree_object()
        root = tree.seed_node
        # Root should have exactly 2 child nodes:
        # (B,(A,(C,(D,E)))) and (F,(G,H))
        child_nodes = root.child_nodes()
        assert len(child_nodes) == 2

    def test_tree_info_with_realistic_data(self, sample_tree_path):
        info = get_tree_info(sample_tree_path)
        assert info["tip_count"] == 8
        assert info["total_nodes"] >= 8

    def test_all_ids_match_taxonomy(self, sample_tree_path, sample_taxonomy_path):
        """Every tree tip should have a corresponding taxonomy entry."""
        tree_parser = TreeParser(sample_tree_path)
        meta_parser = MetadataParser(sample_taxonomy_path)
        orphans = meta_parser.validate_against_tree(tree_parser.tip_labels)
        assert len(orphans) == 0


# ---- Taxonomy parsing with realistic data ----


class TestRealisticTaxonomyParsing:
    """Parse taxonomy with real phylum/genus/species names and numeric columns."""

    def test_parse_realistic_taxonomy(self, sample_taxonomy_path):
        parser = MetadataParser(sample_taxonomy_path)
        assert parser.dataframe is not None
        assert len(parser.dataframe) == 8
        expected_columns = {"id", "phylum", "genus", "species", "genome_size", "gc_content"}
        assert expected_columns.issubset(set(parser.dataframe.columns))

    def test_phylum_column_types(self, sample_taxonomy_path):
        parser = MetadataParser(sample_taxonomy_path)
        assert parser.column_types["phylum"] == "categorical"
        assert parser.column_types["genus"] == "categorical"

    def test_numeric_column_detection(self, sample_taxonomy_path):
        """genome_size and gc_content should be detected as numeric."""
        parser = MetadataParser(sample_taxonomy_path)
        assert parser.column_types["genome_size"] == "numeric"
        assert parser.column_types["gc_content"] == "numeric"

    def test_real_phylum_names(self, sample_taxonomy_path):
        """Verify actual biological phylum names are present."""
        parser = MetadataParser(sample_taxonomy_path)
        phyla = set(parser.dataframe["phylum"].unique())
        assert phyla == {"Proteobacteria", "Firmicutes", "Actinobacteria"}

    def test_real_genus_names(self, sample_taxonomy_path):
        """Verify actual genus names are present."""
        parser = MetadataParser(sample_taxonomy_path)
        genera = set(parser.dataframe["genus"].unique())
        assert "Escherichia" in genera
        assert "Bacillus" in genera
        assert "Mycobacterium" in genera


# ---- Monophyly check with realistic data ----


class TestRealisticMonophyly:
    """Run monophyly check on the 8-tip tree with 3 phyla.

    Expected results (from 4taxa_monophyly.csv):
      Actinobacteria (F,G,H): monophyletic
      Firmicutes (B,E):        paraphyletic
      Proteobacteria (A,C,D):  paraphyletic
    """

    def test_monophyly_actinobacteria_monophyletic(self, sample_tree_path, sample_taxonomy_path):
        results = check_monophyly(sample_taxonomy_path, sample_tree_path, "phylum", "id")
        actino = [r for r in results if r["group"] == "Actinobacteria"]
        assert len(actino) == 1
        assert actino[0]["status"] == "monophyletic"
        assert int(actino[0]["member_count"]) == 3

    def test_monophyly_firmicutes_paraphyletic(self, sample_tree_path, sample_taxonomy_path):
        results = check_monophyly(sample_taxonomy_path, sample_tree_path, "phylum", "id")
        firmi = [r for r in results if r["group"] == "Firmicutes"]
        assert len(firmi) == 1
        assert firmi[0]["status"] == "paraphyletic"
        assert int(firmi[0]["member_count"]) == 2

    def test_monophyly_proteobacteria_paraphyletic(self, sample_tree_path, sample_taxonomy_path):
        results = check_monophyly(sample_taxonomy_path, sample_tree_path, "phylum", "id")
        proto = [r for r in results if r["group"] == "Proteobacteria"]
        assert len(proto) == 1
        assert proto[0]["status"] == "paraphyletic"
        assert int(proto[0]["member_count"]) == 3

    def test_monophyly_results_match_reference(self, sample_tree_path, sample_taxonomy_path, data_dir):
        """Compare computed monophyly results against 4taxa_monophyly.csv reference."""
        results = check_monophyly(sample_taxonomy_path, sample_tree_path, "phylum", "id")
        # Read reference file
        ref_path = data_dir / "4taxa_monophyly.csv"
        with open(ref_path, newline="") as f:
            reader = csv.DictReader(f)
            ref_rows = {row["group"]: row for row in reader}
        # Verify each computed result matches reference
        for r in results:
            group = r["group"]
            assert group in ref_rows, f"Group {group} not in reference file"
            ref = ref_rows[group]
            assert r["status"] == ref["status"], f"Status mismatch for {group}"
            assert int(r["member_count"]) == int(ref["member_count"]), f"Member count mismatch for {group}"


# ---- Taxonomy extraction with realistic data ----


class TestRealisticTaxonomyExtraction:
    """Run taxonomy extraction and verify against 4taxa_tax_extract.csv reference."""

    def test_extract_phylum_groups(self, sample_tree_path, sample_taxonomy_path, tmp_path):
        out = tmp_path / "extract.csv"
        df = extract_taxonomy_with_stats(sample_taxonomy_path, sample_tree_path, "phylum", str(out))
        assert not df.empty
        assert len(df) == 3
        groups = set(df["group"].tolist())
        assert groups == {"Proteobacteria", "Firmicutes", "Actinobacteria"}
        assert out.exists()

    def test_extract_member_counts_match_reference(self, sample_tree_path, sample_taxonomy_path, tmp_path, data_dir):
        """Compare extraction member counts against 4taxa_tax_extract.csv reference."""
        out = tmp_path / "extract.csv"
        df = extract_taxonomy_with_stats(sample_taxonomy_path, sample_tree_path, "phylum", str(out))
        ref_path = data_dir / "4taxa_tax_extract.csv"
        with open(ref_path, newline="") as f:
            reader = csv.DictReader(f)
            ref_rows = {row["group"]: row for row in reader}
        for _, row in df.iterrows():
            group = row["group"]
            assert group in ref_rows, f"Group {group} not in reference file"
            ref = ref_rows[group]
            assert int(row["member_count"]) == int(ref["member_count"]), f"Member count mismatch for {group}"


# ---- Template file validation with realistic data ----


class TestRealisticTemplateFiles:
    """Validate the iTOL template reference files in tests/data/."""

    @pytest.mark.parametrize(
        "template_name",
        [
            "template_bar.txt",
            "template_branch.txt",
            "template_colorstrip.txt",
            "template_heatmap.txt",
            "template_style.txt",
            "template_symbols.txt",
        ],
    )
    def test_template_has_valid_header(self, template_name, data_dir):
        """Each template file should pass TemplateValidator header check."""
        tpl_path = data_dir / template_name
        validator = TemplateValidator()
        assert validator.validate_template_file(str(tpl_path)) is True
        assert len(validator.errors) == 0

    def test_bar_template_has_eight_data_rows(self, data_dir):
        """template_bar.txt should have 8 data rows matching the 8-tip tree."""
        tpl_path = data_dir / "template_bar.txt"
        content = tpl_path.read_text()
        # Count data lines (lines after 'columns' header that contain tab-separated data)
        lines = content.strip().split("\n")
        # Find the 'columns' line, then count subsequent data rows
        columns_idx = next(i for i, line in enumerate(lines) if line.startswith("columns"))
        data_lines = [line for line in lines[columns_idx + 2 :] if line.strip() and "\t" in line]
        assert len(data_lines) == 8

    def test_colorstrip_template_uses_real_phylum_colors(self, data_dir):
        """template_colorstrip.txt should use phylum names as values."""
        tpl_path = data_dir / "template_colorstrip.txt"
        content = tpl_path.read_text()
        assert "Proteobacteria" in content
        assert "Firmicutes" in content
        assert "Actinobacteria" in content

    def test_heatmap_template_uses_real_numeric_columns(self, data_dir):
        """template_heatmap.txt should reference genome_size and gc_content columns."""
        tpl_path = data_dir / "template_heatmap.txt"
        content = tpl_path.read_text()
        assert "genome_size" in content
        assert "gc_content" in content

    def test_symbols_template_has_correct_columns(self, data_dir):
        """template_symbols.txt should have 5 columns: id, type, value, color, label."""
        tpl_path = data_dir / "template_symbols.txt"
        content = tpl_path.read_text()
        assert "columns 5" in content
        assert "type" in content
        assert "value" in content
        assert "label" in content
