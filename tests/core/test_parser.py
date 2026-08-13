"""Tests for PyiTOL core parser module."""

import dendropy
import pytest

from pyitol.core.parser import (
    MetadataParser,
    TreeParser,
    _get_node_label,
    _get_tip_label,
    count_trees_in_file,
    detect_tree_schema,
    format_support_values,
    load_tree,
)
from pyitol.exceptions import MetadataParseError, TreeParseError

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
IQ_TREE_NEWICK = "((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);"
NEXUS_TREE = """#NEXUS
begin trees;
    tree tree1 = ((A,B),(C,D));
end;
"""
SIMPLE_TSV = "id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\tFirmicutes\nC\tArchaea\tEuryarchaeota\nD\tArchaea\tCrenarchaeota\n"  # noqa: E501


@pytest.fixture
def newick_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def iqtree_file(tmp_path):
    p = tmp_path / "test.treefile"
    p.write_text(IQ_TREE_NEWICK)
    return str(p)


@pytest.fixture
def nexus_file(tmp_path):
    p = tmp_path / "test.nex"
    p.write_text(NEXUS_TREE)
    return str(p)


@pytest.fixture
def tsv_file(tmp_path):
    p = tmp_path / "test.tsv"
    p.write_text(SIMPLE_TSV)
    return str(p)


class TestGetNodeLabel:
    def test_with_taxon(self):
        tree = dendropy.Tree.get(data="(A,B);", schema="newick")
        tip = tree.leaf_nodes()[0]
        assert _get_node_label(tip) == "A"

    def test_without_taxon(self):
        tree = dendropy.Tree.get(data="(A,B);", schema="newick")
        internal = tree.internal_nodes()[0]
        internal.taxon = None
        assert _get_node_label(internal) == ""


class TestGetTipLabel:
    def test_with_taxon(self):
        tree = dendropy.Tree.get(data="(A,B);", schema="newick")
        tip = tree.leaf_nodes()[0]
        assert _get_tip_label(tip) == "A"

    def test_without_taxon(self):
        tree = dendropy.Tree.get(data="(A,B);", schema="newick")
        tip = tree.leaf_nodes()[0]
        tip.taxon = None
        assert _get_tip_label(tip) == ""


class TestTreeParser:
    def test_parse_newick(self, newick_file):
        parser = TreeParser(newick_file)
        assert parser.get_tip_count() == 4
        assert len(parser.tip_labels) == 4
        assert set(parser.tip_labels) == {"A", "B", "C", "D"}

    def test_parse_nexus(self, nexus_file):
        parser = TreeParser(nexus_file)
        assert parser.get_tip_count() == 4

    def test_auto_detect_schema(self, newick_file):
        parser = TreeParser()
        parser.parse(newick_file)
        assert parser.tree is not None
        assert parser.get_tip_count() == 4
        assert set(parser.get_all_ids()) == {"A", "B", "C", "D"}

    def test_get_all_ids(self, newick_file):
        parser = TreeParser(newick_file)
        ids = parser.get_all_ids()
        assert "A" in ids
        assert "B" in ids

    def test_detect_support_value_format_iqtree(self, iqtree_file):
        parser = TreeParser(iqtree_file)
        fmt = parser.detect_support_value_format()
        assert "iqtree" in fmt

    def test_file_not_found(self):
        parser = TreeParser("nonexistent.nwk")
        assert parser.tree is None
        assert parser.tip_labels == []

    def test_parse_file_not_found(self):
        parser = TreeParser()
        with pytest.raises(TreeParseError):
            parser.parse("nonexistent.nwk")

    def test_parse_newick_with_bom(self, tmp_path):
        p = tmp_path / "bom.nwk"
        p.write_bytes(b"\xef\xbb\xbf(A:0.1,B:0.2);")
        parser = TreeParser(str(p))
        assert parser.get_tip_count() == 2
        assert "A" in parser.tip_labels


class TestLoadTreeBom:
    def test_load_tree_strips_bom(self, tmp_path):
        p = tmp_path / "bom.nwk"
        p.write_bytes(b"\xef\xbb\xbf(A:0.1,B:0.2);")
        tree = load_tree(str(p))
        assert len(tree.leaf_nodes()) == 2

    def test_detect_schema_with_bom(self, tmp_path):
        p = tmp_path / "bom.nwk"
        p.write_bytes(b"\xef\xbb\xbf(A:0.1,B:0.2);")
        assert detect_tree_schema(str(p)) == "newick"

    def test_count_trees_with_bom(self, tmp_path):
        p = tmp_path / "bom.nwk"
        p.write_bytes(b"\xef\xbb\xbf(A:0.1,B:0.2);")
        assert count_trees_in_file(str(p)) == 1

    def test_detect_schema_by_nexus_extension(self, tmp_path):
        p = tmp_path / "tree.nex"
        p.write_text("random content that is not newick")
        parser = TreeParser()
        parser.tree_path = p
        schema = parser._detect_schema("not newick")
        assert schema == "nexus"

    def test_detect_schema_by_treex_extension(self, tmp_path):
        p = tmp_path / "tree.treex"
        p.write_text("random content")
        parser = TreeParser()
        parser.tree_path = p
        schema = parser._detect_schema("not newick")
        assert schema == "nexus"

    def test_detect_schema_fallback_newick(self, tmp_path):
        p = tmp_path / "tree.txt"
        p.write_text("not nexus or newick")
        parser = TreeParser()
        parser.tree_path = p
        schema = parser._detect_schema("not nexus or newick")
        assert schema == "newick"

    def test_extract_support_values_with_comments(self):
        tree = dendropy.Tree.get(data="(A,B,(C,D));", schema="newick")
        for node in tree.internal_nodes():
            node.comments = ["90"]
        parser = TreeParser()
        parser.tree = tree
        parser._extract_support_values()
        assert len(parser.support_values) > 0

    def test_extract_support_values_non_numeric_comment(self):
        tree = dendropy.Tree.get(data="(A,B,(C,D));", schema="newick")
        for node in tree.internal_nodes():
            node.comments = ["abc"]
        parser = TreeParser()
        parser.tree = tree
        parser._extract_support_values()
        # non-numeric comments should be silently skipped
        assert parser.support_values == {}

    def test_extract_support_values_malformed_numeric(self):
        tree = dendropy.Tree.get(data="(A,B,(C,D));", schema="newick")
        for node in tree.internal_nodes():
            node.comments = ["1.2.3"]
        parser = TreeParser()
        parser.tree = tree
        parser._extract_support_values()
        # regex matches but float conversion fails
        assert parser.support_values == {}

    def test_detect_support_format_raxml(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("((A:0.1,B:0.2)){90}:0.3,(C:0.4,D:0.5){85}:0.6);")
        parser = TreeParser()
        parser.tree_path = p
        fmt = parser.detect_support_value_format()
        assert fmt == "raxml"

    def test_detect_support_format_posterior(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("((A:0.1,B:0.2)[&prob=0.95]:0.3,(C:0.4,D:0.5)[&prob=0.85]:0.6);")
        parser = TreeParser()
        parser.tree_path = p
        fmt = parser.detect_support_value_format()
        assert fmt == "posterior"

    def test_detect_support_format_general(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);")
        parser = TreeParser(str(p))
        fmt = parser.detect_support_value_format()
        assert fmt == "general"

    def test_detect_support_format_iqtree_both(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("((A:0.1,B:0.2)[&support=90]:0.3,(C:0.4,D:0.5)85:0.6);")
        parser = TreeParser(str(p))
        fmt = parser.detect_support_value_format()
        assert fmt == "iqtree_both"

    def test_get_tree_object(self, newick_file):
        parser = TreeParser(newick_file)
        tree = parser.get_tree_object()
        assert isinstance(tree, dendropy.Tree)


class TestMetadataParser:
    def test_parse_tsv(self, tsv_file):
        parser = MetadataParser(tsv_file)
        assert parser.dataframe is not None
        assert len(parser.dataframe) == 4
        assert "id" in parser.dataframe.columns

    def test_detect_column_types(self, tsv_file):
        parser = MetadataParser(tsv_file)
        assert "Kingdom" in parser.column_types
        assert parser.column_types["Kingdom"] == "categorical"

    def test_validate_against_tree(self, tsv_file, newick_file):
        meta = MetadataParser(tsv_file)
        tree = TreeParser(newick_file)
        orphans = meta.validate_against_tree(tree.tip_labels)
        assert len(orphans) == 0

    def test_file_not_found(self):
        with pytest.raises(MetadataParseError):
            MetadataParser("nonexistent.tsv")

    def test_parse_csv(self, tmp_path):
        p = tmp_path / "test.csv"
        p.write_text("id,Value\nA,1\nB,2\n")
        parser = MetadataParser(str(p))
        assert len(parser.dataframe) == 2
        assert "id" in parser.dataframe.columns
        assert "Value" in parser.dataframe.columns

    def test_parse_unsupported_format(self, tmp_path):
        p = tmp_path / "test.doc"
        p.write_text("id\tValue\nA\t1\n")
        with pytest.raises(MetadataParseError, match="Unsupported"):
            MetadataParser(str(p))

    def test_detect_id_column_fallback(self, tmp_path):
        p = tmp_path / "test.tsv"
        p.write_text("foo\tValue\nA\t1\nB\t2\n")
        parser = MetadataParser(str(p))
        assert len(parser.dataframe) == 2
        assert "id" in parser.dataframe.columns

    def test_detect_column_types_empty(self, tmp_path):
        p = tmp_path / "test.tsv"
        p.write_text("id\tValue\nA\t\nB\t\n")
        parser = MetadataParser(str(p))
        assert parser.column_types["Value"] == "unknown"

    def test_detect_column_types_color(self, tmp_path):
        p = tmp_path / "test.tsv"
        p.write_text("id\tColor\nA\t#FF0000\nB\t#00FF00\n")
        parser = MetadataParser(str(p))
        assert parser.column_types["Color"] == "color"

    def test_detect_column_types_numeric(self, tmp_path):
        p = tmp_path / "test.tsv"
        p.write_text("id\tValue\nA\t1.5\nB\t2.3\n")
        parser = MetadataParser(str(p))
        assert parser.column_types["Value"] == "numeric"

    def test_validate_against_tree_no_id_column(self, tmp_path):
        p = tmp_path / "test.tsv"
        p.write_text("foo\tValue\nA\t1\nB\t2\n")
        parser = MetadataParser()
        parser.parse(str(p), id_column="nonexistent")
        orphans = parser.validate_against_tree(["A", "B"])
        assert orphans == []

    def test_parse_excel(self, tmp_path):
        # openpyxl 是 Excel 解析的可选依赖（pyproject.toml [excel] extra）
        pytest.importorskip("openpyxl")
        import pandas as pd

        p = tmp_path / "test.xlsx"
        df = pd.DataFrame({"id": ["A", "B"], "Value": ["1", "2"]})
        df.to_excel(p, index=False)
        parser = MetadataParser(str(p))
        assert len(parser.dataframe) == 2
        assert "id" in parser.dataframe.columns


class TestFormatSupportValues:
    def test_format_iqtree(self, iqtree_file, tmp_path):
        output = tmp_path / "formatted.nwk"
        format_support_values(iqtree_file, output, fmt="iqtree", support_type="bootstrap")
        assert output.exists()
        content = output.read_text()
        assert ")90" in content

    def test_format_raxml(self, tmp_path):
        raxml_tree = tmp_path / "raxml.nwk"
        raxml_tree.write_text("((A:0.1,B:0.2){90}:0.3,(C:0.4,D:0.5){85}:0.6);")
        output = tmp_path / "formatted.nwk"
        format_support_values(str(raxml_tree), output, fmt="raxml")
        assert output.exists()
        content = output.read_text()
        assert ")90" in content

    def test_format_general(self, tmp_path):
        tree = tmp_path / "tree.nwk"
        tree.write_text("((A:0.1,B:0.2)90/95:0.3,(C:0.4,D:0.5)80:0.6);")
        output = tmp_path / "formatted.nwk"
        format_support_values(str(tree), output, fmt="general")
        assert output.exists()

    def test_format_content_only(self, tmp_path):
        tree = tmp_path / "tree.nwk"
        tree.write_text("((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);")
        output = tmp_path / "formatted.nwk"
        format_support_values(content="((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);", output_path=output)
        assert output.exists()

    def test_write_newick(self, newick_file, tmp_path):
        parser = TreeParser(newick_file)
        output = tmp_path / "out.nwk"
        parser.write_newick(output)
        assert output.exists()
        content = output.read_text()
        assert content.strip().endswith(";")

    def test_get_node_count(self, newick_file):
        parser = TreeParser(newick_file)
        # dendropy internal_nodes() includes root node
        assert parser.get_node_count() == 3

    def test_get_depth(self, newick_file):
        parser = TreeParser(newick_file)
        assert parser.get_depth() > 0

    def test_format_support_values_value_error(self):
        with pytest.raises(TreeParseError, match="Either tree_path or content"):
            format_support_values()

    def test_format_iqtree_alrt(self, tmp_path):
        tree = tmp_path / "tree.nwk"
        tree.write_text("((A:0.1,B:0.2)90/95:0.3,(C:0.4,D:0.5)80/85:0.6);")
        output = tmp_path / "formatted.nwk"
        format_support_values(str(tree), output, fmt="iqtree", support_type="aLRT")
        assert output.exists()
        content = output.read_text()
        assert ")95" in content

    def test_format_support_values_return_string(self, tmp_path):
        """Cover line 277: return raw when output_path is None."""
        tree = tmp_path / "tree.nwk"
        tree.write_text("((A:0.1,B:0.2)90:0.3,(C:0.4,D:0.5)85:0.6);")
        result = format_support_values(str(tree), fmt="general")
        assert isinstance(result, str)
        assert ")90" in result
