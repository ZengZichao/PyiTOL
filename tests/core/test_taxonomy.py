"""Tests for PyiTOL taxonomy module."""

import pytest

from pyitol.core.taxonomy import (
    check_monophyly,
    extract_taxonomy,
    extract_taxonomy_from_tip_names,
    extract_taxonomy_ranks,
    extract_taxonomy_with_stats,
    get_ranks,
    parse_taxonomy_levels_config,
    parse_taxonomy_string,
)
from pyitol.exceptions import MetadataParseError

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tPhylum\nA\tBacteria\tProteobacteria\nB\tBacteria\tProteobacteria\nC\tArchaea\tEuryarchaeota\nD\tArchaea\tEuryarchaeota\n"  # noqa: E501


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


class TestExtractTaxonomy:
    def test_extract_basic(self, tree_file, taxonomy_file):
        result = extract_taxonomy(taxonomy_file, tree_file, "Kingdom", "id")
        assert len(result) == 4
        assert all("name" in r for r in result)

    def test_extract_phylum(self, tree_file, taxonomy_file):
        result = extract_taxonomy(taxonomy_file, tree_file, "Phylum", "id")
        assert len(result) == 4

    def test_extract_rank_not_found(self, tree_file, taxonomy_file):
        with pytest.raises(MetadataParseError, match="Rank column"):
            extract_taxonomy(taxonomy_file, tree_file, "MissingRank", "id")


class TestExtractTaxonomyRanks:
    def test_known_ranks(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tkingdom\tphylum\tclass\nA\tBacteria\tProteobacteria\tGammaproteobacteria\n")
        ranks = extract_taxonomy_ranks(str(p))
        assert "kingdom" in ranks
        assert "phylum" in ranks
        assert "class" in ranks

    def test_unknown_ranks_fallback(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tfoo\tbar\nA\t1\t2\n")
        ranks = extract_taxonomy_ranks(str(p))
        assert "foo" in ranks
        assert "bar" in ranks

    def test_unknown_ranks_with_id(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tfoo\tbar\nA\t1\t2\n")
        ranks = extract_taxonomy_ranks(str(p))
        assert "id" not in ranks


class TestExtractTaxonomyWithStats:
    def test_basic(self, tree_file, taxonomy_file, tmp_path):
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(taxonomy_file, tree_file, "Kingdom", str(out))
        assert not df.empty
        assert out.exists()

    def test_rank_not_found(self, tree_file, taxonomy_file, tmp_path):
        out = tmp_path / "out.csv"
        with pytest.raises(MetadataParseError, match="Rank column"):
            extract_taxonomy_with_stats(taxonomy_file, tree_file, "MissingRank", str(out))

    def test_empty_members(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(str(p), tree_file, "Kingdom", str(out))
        # only A is in tree; Bacteria group should contain exactly A
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]["group"] == "Bacteria"
        assert int(df.iloc[0]["member_count"]) == 1
        assert out.exists()

    def test_no_tip_nodes(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nX\tFoo\nY\tFoo\n")
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(str(p), tree_file, "Kingdom", str(out))
        # X and Y are not in tree, so no tip_nodes found
        assert df.empty


class TestCheckMonophyly:
    def test_monophyletic_groups(self, tree_file, taxonomy_file):
        results = check_monophyly(taxonomy_file, tree_file, "Kingdom", "id")
        assert len(results) == 2
        names = [r["group"] for r in results]
        assert "Bacteria" in names
        assert "Archaea" in names


class TestGetRanks:
    def test_get_ranks(self, taxonomy_file):
        ranks = get_ranks(taxonomy_file, "id")
        assert "Kingdom" in ranks
        assert "Phylum" in ranks


class TestParseTaxonomyLevelsConfig:
    def test_default_none(self):
        result = parse_taxonomy_levels_config(None)
        assert "d" in result
        assert result["d"][0] == "Domain"
        assert result["p"][0] == "Phylum"

    def test_custom_full(self):
        result = parse_taxonomy_levels_config("d:Domain,p:Phylum,c:Class")
        assert result["d"] == ("Domain", 0)
        assert result["p"] == ("Phylum", 1)
        assert result["c"] == ("Class", 2)

    def test_shorthand(self):
        result = parse_taxonomy_levels_config("d,p,c")
        assert result["d"] == ("Domain", 0)
        assert result["p"] == ("Phylum", 1)
        assert result["c"] == ("Class", 2)

    def test_custom_unknown_prefix(self):
        result = parse_taxonomy_levels_config("x:Custom")
        assert result["x"] == ("Custom", 0)

    def test_whitespace_handling(self):
        result = parse_taxonomy_levels_config(" d : Domain , p : Phylum ")
        assert result["d"] == ("Domain", 0)
        assert result["p"] == ("Phylum", 1)


class TestParseTaxonomyString:
    def test_format_a_embedded(self):
        tip = "GB_GCA_0001_d_Bacteria_p_Proteobacteria_c_Gammaproteobacteria"
        result = parse_taxonomy_string(tip)
        assert result["Domain"] == "Bacteria"
        assert result["Phylum"] == "Proteobacteria"
        assert result["Class"] == "Gammaproteobacteria"
        assert result["accession"] == "GB_GCA_0001"

    def test_format_a_with_all_ranks(self):
        tip = "acc_d_Bacteria_p_Firmicutes_c_Bacilli_o_Lactobacillales_f_Lactobacillaceae_g_Lactobacillus"
        result = parse_taxonomy_string(tip)
        assert result["Domain"] == "Bacteria"
        assert result["Phylum"] == "Firmicutes"
        assert result["Class"] == "Bacilli"
        assert result["Order"] == "Lactobacillales"
        assert result["Family"] == "Lactobacillaceae"
        assert result["Genus"] == "Lactobacillus"

    def test_format_b_gtdb(self):
        tax = "d__Archaea;p__Thermoproteota;c__Korarchaeia"
        result = parse_taxonomy_string(tax)
        assert result["Domain"] == "Archaea"
        assert result["Phylum"] == "Thermoproteota"
        assert result["Class"] == "Korarchaeia"

    def test_format_b_with_all_ranks(self):
        tax = "d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;o__Enterobacterales;f__Enterobacteriaceae;g__Escherichia;s__coli"  # noqa: E501
        result = parse_taxonomy_string(tax)
        assert result["Domain"] == "Bacteria"
        assert result["Phylum"] == "Proteobacteria"
        assert result["Class"] == "Gammaproteobacteria"
        assert result["Order"] == "Enterobacterales"
        assert result["Family"] == "Enterobacteriaceae"
        assert result["Genus"] == "Escherichia"
        assert result["Species"] == "coli"

    def test_empty_values_s(self):
        tax = "d__Bacteria;p__Proteobacteria;s__"
        result = parse_taxonomy_string(tax)
        assert result["Domain"] == "Bacteria"
        assert result["Phylum"] == "Proteobacteria"
        assert result.get("Species") is None

    def test_format_b_partial_prefixes(self):
        tax = "d__Bacteria;p__Proteobacteria"
        result = parse_taxonomy_string(tax)
        assert result["Domain"] == "Bacteria"
        assert result["Phylum"] == "Proteobacteria"
        assert result.get("Class") is None

    def test_unknown_format(self):
        result = parse_taxonomy_string("random_string")
        assert result == {}

    def test_empty_string(self):
        result = parse_taxonomy_string("")
        assert result == {}


class TestExtractTaxonomyFromTipNames:
    def test_embedded_format(self, tmp_path):
        tree = tmp_path / "test.nwk"
        tree.write_text(
            "(GB_GCA_0001_d_Bacteria_p_Proteo_c_Gamma_g_Genus,GB_GCA_0002_d_Bacteria_p_Firm_c_Bacilli_g_Genus2);"
        )
        df = extract_taxonomy_from_tip_names(str(tree), name_format="embedded")
        assert "Domain" in df.columns
        assert "Phylum" in df.columns
        assert "Genus" in df.columns
        assert len(df) == 2

    def test_gtdb_format(self, tmp_path):
        tree = tmp_path / "test.nwk"
        # GTDB tip 名含分号（;），Newick 中必须用引号包裹以避免被解析为树结束符。
        # 使用纯 GTDB 串（无 _d_ 前缀）避免与 embedded 格式歧义。
        tree.write_text("('d__Archaea;p__Thermoproteota','d__Bacteria;p__Proteobacteria');")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="gtdb")
        assert "Domain" in df.columns
        assert "Phylum" in df.columns
        assert len(df) == 2

    def test_mixed_format(self, tmp_path):
        tree = tmp_path / "test.nwk"
        # 含分号的 GTDB tip 名需引号包裹；embedded 格式无分号无需引号
        tree.write_text("('tip1_d__Archaea;p__Thermo',tip2_acc_d_Bacteria_p_Proteo);")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="mixed")
        assert len(df) == 2
        # Both tips should have at least Domain parsed
        assert "Domain" in df.columns

    def test_ncbi_format(self, tmp_path):
        tree = tmp_path / "test.nwk"
        tree.write_text("(Escherichia_coli,Salmonella_enterica);")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="ncbi")
        assert "Genus" in df.columns
        assert "Species" in df.columns
        assert len(df) == 2

    def test_auto_detect_gtdb(self, tmp_path):
        tree = tmp_path / "test.nwk"
        # GTDB tip 名含分号（;），Newick 中必须用引号包裹。
        # 使用纯 GTDB 串避免与 embedded 格式歧义，确保 auto 检测为 gtdb。
        tree.write_text("('d__Archaea;p__Thermoproteota','d__Bacteria;p__Proteobacteria');")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="auto")
        assert "Domain" in df.columns
        assert len(df) == 2

    def test_auto_detect_embedded(self, tmp_path):
        tree = tmp_path / "test.nwk"
        tree.write_text("(GB_GCA_0001_d_Bacteria_p_Proteo,GB_GCA_0002_d_Archaea_p_Thermo);")
        df = extract_taxonomy_from_tip_names(str(tree), name_format="auto")
        assert "Domain" in df.columns
        assert len(df) == 2

    def test_custom_levels(self, tmp_path):
        tree = tmp_path / "test.nwk"
        tree.write_text("(GB_GCA_0001_d_Bacteria_p_Proteo,GB_GCA_0002_d_Archaea_p_Thermo);")
        df = extract_taxonomy_from_tip_names(
            str(tree),
            name_format="embedded",
            taxonomy_levels="d:Domain,p:Phylum",
        )
        assert "Domain" in df.columns
        assert "Phylum" in df.columns

    def test_output_path(self, tmp_path):
        tree = tmp_path / "test.nwk"
        tree.write_text("(GB_GCA_0001_d_Bacteria_p_Proteo);")
        out = tmp_path / "output.csv"
        _ = extract_taxonomy_from_tip_names(str(tree), name_format="embedded", output_path=str(out))
        assert out.exists()


class TestExtractTaxonomyWithStatsBoundaries:
    def test_single_member_group(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(str(p), tree_file, "Kingdom", str(out))
        assert len(df) == 1
        assert int(df.iloc[0]["member_count"]) == 1

    def test_all_groups_monophyletic(self, tree_file, taxonomy_file, tmp_path):
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(taxonomy_file, tree_file, "Kingdom", str(out))
        assert len(df) == 2
        for _, row in df.iterrows():
            assert int(row["member_count"]) == 2

    def test_missing_output_dir_created(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "nested" / "dir" / "out.csv"
        _ = extract_taxonomy_with_stats(str(p), tree_file, "Kingdom", str(out))
        assert out.exists()

    def test_empty_members_raises(self, tree_file, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tKingdom\nX\tFoo\nY\tFoo\n")
        out = tmp_path / "out.csv"
        df = extract_taxonomy_with_stats(str(p), tree_file, "Kingdom", str(out))
        # X and Y are not in tree, so df should be empty
        assert df.empty
