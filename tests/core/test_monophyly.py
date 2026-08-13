"""Tests for PyiTOL core monophyly module."""

from unittest.mock import patch

import dendropy
import pytest

from pyitol.core.monophyly import (
    _check_monophyly_full,
    _find_lca,
    _find_subgroups,
    _find_tip_node,
    _get_lca_label,
    _safe_mrca,
    check_monophyly,
    check_monophyly_with_taxa_list,
    clear_tip_index_cache,
    get_special_identifier_description,
    is_special_identifier,
    resolve_special_identifier,
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


@pytest.fixture
def tree():
    return dendropy.Tree.get(data=SIMPLE_NEWICK, schema="newick", preserve_underscores=True)


class TestFindTipNode:
    def test_found(self, tree):
        node = _find_tip_node(tree, "A")
        assert node is not None
        assert node.taxon.label == "A"

    def test_not_found(self, tree):
        node = _find_tip_node(tree, "X")
        assert node is None


class TestGetLcaLabel:
    def test_empty_tip_nodes(self, tree):
        assert _get_lca_label(tree, []) == "N/A"

    def test_no_taxa(self, tree):
        tip = tree.leaf_nodes()[0]
        tip.taxon = None
        assert _get_lca_label(tree, [tip]) == "N/A"

    def test_lca_with_taxon_label(self, tree):
        tips = [n for n in tree.leaf_nodes() if n.taxon]
        lca = _safe_mrca(tree, taxa=[t.taxon for t in tips])
        taxon = dendropy.Taxon(label="ROOT")
        tree.taxon_namespace.add_taxon(taxon)
        lca.taxon = taxon
        assert _get_lca_label(tree, tips) == "ROOT"

    def test_lca_internal(self, tree):
        tips = [n for n in tree.leaf_nodes() if n.taxon]
        label = _get_lca_label(tree, tips)
        assert label.startswith("internal_")


class TestFindLca:
    def test_empty(self, tree):
        assert _find_lca(tree, []) is None

    def test_not_found(self, tree):
        assert _find_lca(tree, ["X", "Y"]) is None

    def test_valid(self, tree):
        lca = _find_lca(tree, ["A", "B"])
        assert lca is not None
        assert lca.is_internal()
        # LCA of A and B in (A,B,(C,D)) is the root node
        assert lca.parent_node is None


class TestCheckMonophyly:
    def test_rank_not_found(self, tree_file, taxonomy_file):
        with pytest.raises(MetadataParseError, match="Rank column"):
            check_monophyly(taxonomy_file, tree_file, "MissingRank", "id")


class TestCheckMonophylyWithTaxaList:
    def test_taxa_file(self, tree_file, taxonomy_file, tmp_path):
        taxa_file = tmp_path / "taxa.txt"
        taxa_file.write_text("Bacteria\nArchaea\n")
        results = check_monophyly_with_taxa_list(taxonomy_file, tree_file, rank="Kingdom", taxa_file=str(taxa_file))
        assert isinstance(results, list)
        assert len(results) == 2
        groups = {r["group"] for r in results}
        assert groups == {"Bacteria", "Archaea"}

    def test_rank_and_taxa_list(self, tree_file, taxonomy_file):
        results = check_monophyly_with_taxa_list(taxonomy_file, tree_file, rank="Kingdom", taxa_list=["Bacteria"])
        assert len(results) == 1
        assert results[0]["group"] == "Bacteria"

    def test_taxa_list_and_taxonomy_path(self, tree_file, taxonomy_file):
        results = check_monophyly_with_taxa_list(taxonomy_file, tree_file, taxa_list=["A", "B"])
        assert isinstance(results, list)
        assert len(results) == 2
        groups = {r["group"] for r in results}
        assert groups == {"A", "B"}

    def test_insufficient_args(self, tree_file):
        with pytest.raises(MetadataParseError, match="Either --rank with --taxonomy or --taxa"):
            check_monophyly_with_taxa_list(None, tree_file)


class TestCheckMonophylyFull:
    def setup_method(self):
        """Clear cache before each test to avoid stale data."""
        clear_tip_index_cache()

    def test_empty_tip_nodes(self, tree):
        result = _check_monophyly_full(tree, "test", [])
        assert result["status"] == "unknown"
        assert result["member_count"] == 0

    def test_polyphyletic_missing_nodes(self, tree):
        # C2: Include a member not in the tree. 缺采样节点(missing nodes)应与拓扑复系
        # (polyphyletic) 区分，返回独立的 'incomplete_sampling' 状态，而非错误地套用
        # 'polyphyletic'。
        result = _check_monophyly_full(tree, "test", ["A", "B", "X"])
        assert result["status"] == "incomplete_sampling"
        assert result["missing_nodes"] != ""

    def test_paraphyletic(self, tree):
        # Paraphyletic: real topology where extra descendants belong to mixed groups.
        # 使用外类群 E 强制定根（避免 dendropy 对未定根树的非确定性重定根），
        # 树 (((A,(C,D)),B),E) 中 LCA({A,B}) 为二叉节点，额外后代 {C,D} 构成
        # 已解析的姐妹群；C 属 G1、D 属 G2 -> paraphyletic。
        # 注意：(A,B,(C,D)) 这类根节点三歧（trifurcation）会被 C4 判定为
        # data_insufficient，故此处改用确定性定根的二叉树验证并系判定。
        fresh_tree = dendropy.Tree.get(
            data="(((A:0.1,(C:0.4,D:0.5):0.3):0.2,B:0.6):0.7,E:0.8);",
            schema="newick",
            preserve_underscores=True,
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G1", "D": "G2"}
        result = _check_monophyly_full(fresh_tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result["status"] == "paraphyletic"

    def test_c1_paraphyletic_not_polyphyletic(self):
        """C1 regression: a group equal to the LCA minus a single whole sister clade
        is paraphyletic, NOT polyphyletic.

        Tree: ((A,B),((C,D),(E,F)))  ->  root has two child clades:
          clade1 = (A,B), clade2 = ((C,D),(E,F)).
        Members {A,B,C,D}: S = LCA(root) \\ {E,F}.  Only one child clade (clade2)
        mixes S and non-S members, so by the strict definition this is paraphyletic.
        The old implementation wrongly flagged any group spanning >= 2 child clades
        as polyphyletic.
        """
        fresh_tree = dendropy.Tree.get(
            data="((A,B),((C,D),(E,F)));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(fresh_tree, "G", ["A", "B", "C", "D"], tip_to_group=None)
        assert result["status"] == "paraphyletic"

    def test_c1_true_polyphyletic(self):
        """C1: a group genuinely shredded across >= 2 mixing child clades is polyphyletic.

        Tree: ((A,B),(C,D),(E,F)) -> root has three child clades.
        Members {A,C,E}: every child clade contains exactly one S member plus a
        non-S member, so all three child clades are 'mixed' -> polyphyletic.
        """
        fresh_tree = dendropy.Tree.get(
            data="((A,B),(C,D),(E,F));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(fresh_tree, "G", ["A", "C", "E"], tip_to_group=None)
        assert result["status"] == "polyphyletic"

    def test_monophyletic(self, taxonomy_file, tmp_path):
        """Cover the normal path of check_monophyly (lines 80-91)."""
        # 使用外类群 E 强制定根，避免未定根三歧分支被 C4 判为 data_insufficient。
        # 树 (((A,(C,D)),B),E)：Proteobacteria={A,B} 为并系（缺采样的姐妹群
        # Euryarchaeota={C,D}），Euryarchaeota={C,D} 为单系。
        tree_path = tmp_path / "tree.nwk"
        tree_path.write_text("(((A:0.1,(C:0.4,D:0.5):0.3):0.2,B:0.6):0.7,E:0.8);")
        results = check_monophyly(taxonomy_file, str(tree_path), "Phylum", "id")
        assert isinstance(results, list)
        assert len(results) == 2
        # Proteobacteria is paraphyletic and Euryarchaeota is monophyletic;
        # verify the actual group names.
        groups = {r["group"] for r in results}
        assert groups == {"Proteobacteria", "Euryarchaeota"}
        statuses = {r["status"] for r in results}
        assert statuses == {"monophyletic", "paraphyletic"}

    def test_tip_to_group_none_vs_empty_dict(self, tree):
        """Verify that None and empty dict are handled differently.

        When tip_to_group is None, extra nodes should lead to paraphyletic status.
        When tip_to_group is an empty dict {}, the same behavior should occur
        (conservative default: paraphyletic when no mapping available).
        """
        # Test with None (no mapping provided)
        result_none = _check_monophyly_full(tree, "test", ["A"], tip_to_group=None)
        # Test with empty dict (mapping provided but empty)
        result_empty = _check_monophyly_full(tree, "test", ["A"], tip_to_group={})
        # Both should give the same result when there are extra nodes
        assert result_none["status"] == result_empty["status"]

    def test_tip_to_group_with_valid_mapping(self, tree):
        """Verify nested monophyly detection with valid tip_to_group mapping."""
        # 确定性定根二叉树 (((A,(C,D)),B),E)：LCA({A,B}) 为二叉节点，
        # 额外节点 {C,D} 全部映射到与 A、B 相同的组 -> 嵌套单系。
        fresh_tree = dendropy.Tree.get(
            data="(((A:0.1,(C:0.4,D:0.5):0.3):0.2,B:0.6):0.7,E:0.8);",
            schema="newick",
            preserve_underscores=True,
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G1", "D": "G1"}
        result = _check_monophyly_full(fresh_tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result["status"] == "monophyletic"

    def test_tip_to_group_with_different_groups(self, tree):
        """Verify paraphyletic detection when extra nodes belong to different groups."""
        # 确定性定根二叉树 (((A,(C,D)),B),E)：LCA({A,B}) 为二叉节点，
        # 额外节点 {C,D} 属于另一组 -> 并系（paraphyletic）。
        fresh_tree = dendropy.Tree.get(
            data="(((A:0.1,(C:0.4,D:0.5):0.3):0.2,B:0.6):0.7,E:0.8);",
            schema="newick",
            preserve_underscores=True,
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G2", "D": "G2"}
        result = _check_monophyly_full(fresh_tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result["status"] == "paraphyletic"

    def test_tip_to_group_partial_mapping(self, tree):
        """Verify behavior when tip_to_group has values but doesn't contain all extra nodes."""
        # In tree (A:0.1,B:0.2,(C:0.4,D:0.5):0.6), LCA({A,B}) = root
        # Extra nodes are {C, D}. If tip_to_group only maps some extras,
        # taxonomy data is insufficient to determine classification.
        # Create a completely independent tree to avoid namespace issues
        independent_tree = dendropy.Tree.get(
            data="(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);", schema="newick", preserve_underscores=True
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G1"}  # D not in mapping
        result = _check_monophyly_full(independent_tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result["status"] == "data_insufficient"


class TestPolytomyHandling:
    def setup_method(self):
        clear_tip_index_cache()

    def test_strict_mode_polytomy_treated_as_data_insufficient(self):
        """C4: In strict mode a group spanning 2 of 3 polytomy child clades cannot be
        definitively classified because the unresolved topology prevents any
        mono/para/poly call.  It must return 'data_insufficient', NOT a forced
        'polyphyletic' (the old behaviour over-reported polyphyly on polytomies).
        """
        tree = dendropy.Tree.get(
            data="(A,B,C);",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(tree, "G", ["A", "B"], polytomy_mode="strict")
        assert result["status"] == "data_insufficient"
        assert "polytomy" in result["polytomy_details"].lower()
        assert "2/3" in result["polytomy_details"]

    def test_relaxed_mode_polytomy_treated_as_paraphyletic(self):
        """In relaxed mode the same group is conservatively paraphyletic, not polyphyletic."""
        tree = dendropy.Tree.get(
            data="(A,B,C);",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(tree, "G", ["A", "B"], polytomy_mode="relaxed")
        assert result["status"] == "paraphyletic"
        assert "polytomy" in result["polytomy_details"].lower()
        assert "2/3" in result["polytomy_details"]

    def test_data_insufficient_mode_polytomy(self):
        """In data-insufficient mode, a group in a polytomy is marked data_insufficient."""
        tree = dendropy.Tree.get(
            data="(A,B,C);",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(tree, "G", ["A", "B"], polytomy_mode="data-insufficient")
        assert result["status"] == "data_insufficient"
        assert "polytomy" in result["polytomy_details"].lower()
        assert "2/3" in result["polytomy_details"]

    def test_all_child_clades_still_monophyletic(self):
        """Spanning every child clade of a polytomy remains monophyletic."""
        tree = dendropy.Tree.get(
            data="(A,B,C);",
            schema="newick",
            preserve_underscores=True,
        )
        for mode in ("strict", "relaxed"):
            result = _check_monophyly_full(tree, "G", ["A", "B", "C"], polytomy_mode=mode)
            assert result["status"] == "monophyletic"

    def test_single_child_clade_remains_monophyletic(self):
        """A group confined to one polytomy child clade is monophyletic."""
        tree = dendropy.Tree.get(
            data="(A,(B,C));",
            schema="newick",
            preserve_underscores=True,
        )
        for mode in ("strict", "relaxed"):
            result = _check_monophyly_full(tree, "G", ["B", "C"], polytomy_mode=mode)
            assert result["status"] == "monophyletic"


class TestFindSubgroups:
    def test_single_node(self, tree):
        result = _find_subgroups(tree, ["A"])
        assert len(result) == 1
        assert result[0]["lca"] == "A"

    def test_empty_list(self, tree):
        result = _find_subgroups(tree, [])
        assert len(result) == 1
        assert result[0]["lca"] == "N/A"

    def test_seed_node_none(self, tree):
        result = _find_subgroups(tree, ["X", "Y"])
        assert result == []

    def test_empty_group_taxa(self):
        """Test behavior when nodes lose their taxon after seed check."""
        # Use an independent tree to avoid corrupting the shared fixture
        independent_tree = dendropy.Tree.get(
            data="(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);",
            schema="newick",
            preserve_underscores=True,
        )
        original_find = _find_tip_node

        def fake_find(t, label):
            node = original_find(t, label)
            if node:
                node.taxon = None
            return node

        with patch("pyitol.core.monophyly._find_tip_node", side_effect=fake_find):
            result = _find_subgroups(independent_tree, ["A", "B"])
            # Groups will break early due to empty group_taxa
            assert isinstance(result, list)

    def test_empty_subgroup_tips(self, tree):
        """Test that subgroups are computed correctly even when some nodes are invalid."""
        # With the optimized _find_subgroups, we pre-compute tip_node_map
        # and filter out invalid nodes. Test that valid nodes still form subgroups.
        result = _find_subgroups(tree, ["A", "B"])
        # Both A and B are valid, so we should get subgroups
        assert len(result) >= 1
        # Check that all members are accounted for
        all_members = set()
        for sg in result:
            all_members.update(sg["members"])
        assert all_members == {"A", "B"}

    def test_sibling_clades_merge_into_subgroups(self):
        """回归测试:同一单系支内的兄弟成员必须合并进同一子群。

        历史缺陷:扩展快路径要求候选成员已位于当前子群 MRCA 之下,
        导致兄弟进化枝永远无法合并,子群退化为单成员。
        """
        tree = dendropy.Tree.get(
            data="((t0,t1),(t2,t3),(t4,t5));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _find_subgroups(tree, ["t0", "t1", "t4", "t5"])
        assert len(result) == 2
        member_sets = sorted([sorted(sg["members"]) for sg in result])
        assert member_sets == [["t0", "t1"], ["t4", "t5"]]

    def test_nested_clade_members_merge(self):
        """嵌套进化枝中同支成员应合并,非同支成员不得并入。"""
        tree = dendropy.Tree.get(
            data="(((a,b),c),(d,(e,f)));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _find_subgroups(tree, ["a", "b", "e", "f"])
        assert len(result) == 2
        member_sets = sorted([sorted(sg["members"]) for sg in result])
        assert member_sets == [["a", "b"], ["e", "f"]]

    def test_four_member_clade_not_fragmented(self):
        """回归测试:4 成员完整进化枝不得碎片化为多个 cherry 子群。

        历史缺陷:判据要求新 LCA 末端集为当前子群子集,
        导致尚未访问的同支成员被误判为外部节点。
        """
        tree = dendropy.Tree.get(
            data="((((t0,t1),(t2,t3)),(t4,t5)),(t6,t7));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _find_subgroups(tree, ["t0", "t1", "t2", "t3", "t6", "t7"])
        assert len(result) == 2
        member_sets = sorted([sorted(sg["members"]) for sg in result])
        assert member_sets == [
            ["t0", "t1", "t2", "t3"],
            ["t6", "t7"],
        ]


class TestMonophylyInvariants:
    """Property-based tests for monophyly classification invariants."""

    def setup_method(self):
        # 清除跨树缓存，避免不同测试间节点 id 复用导致的陈旧缓存（KeyError/误判）。
        clear_tip_index_cache()

    def test_monophyletic_subset_remains_monophyletic(self):
        """单系群的子集仍应为单系群。"""
        # 使用确定性定根二叉树 (((A,B),(C,D)),E)，检查 {A,B,C,D} 为单系群
        # 然后检查其任意子集（如 {A,B}）也应为单系群
        # 注意：tip_to_group 需要映射所有节点到同一组
        tree = dendropy.Tree.get(
            data="(((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6):0.7,E:0.8);",
            schema="newick",
            preserve_underscores=True,
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G1", "D": "G1"}
        # Full set is monophyletic
        result_full = _check_monophyly_full(tree, "G1", ["A", "B", "C", "D"], tip_to_group=tip_to_group)
        assert result_full["status"] == "monophyletic"
        # Subset is also monophyletic
        result_subset = _check_monophyly_full(tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result_subset["status"] == "monophyletic"

    def test_polyphyletic_groups_have_at_least_two_subgroups(self):
        """复系群应至少分解为 2 个子群。"""
        # 使用树 ((A,C),(B,D))，检查 G={A,B} 为复系群
        # 子群分解应返回至少 2 个子群
        tree = dendropy.Tree.get(
            data="((A,C),(B,D));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(tree, "G", ["A", "B"])
        assert result["status"] == "polyphyletic"
        subgroups = _find_subgroups(tree, ["A", "B"])
        assert len(subgroups) >= 2

    def test_paraphyletic_has_extra_nodes(self):
        """并系群结果应包含额外节点。"""
        # 构造一个并系群场景，验证 extra_nodes 非空。
        # 使用确定性定根二叉树 (((A,(C,D)),B),E)，{A,B} 为并系、额外节点 {C,D} 非空。
        tree = dendropy.Tree.get(
            data="(((A:0.1,(C:0.4,D:0.5):0.3):0.2,B:0.6):0.7,E:0.8);",
            schema="newick",
            preserve_underscores=True,
        )
        tip_to_group = {"A": "G1", "B": "G1", "C": "G1", "D": "G2"}
        result = _check_monophyly_full(tree, "G1", ["A", "B"], tip_to_group=tip_to_group)
        assert result["status"] == "paraphyletic"
        assert result["extra_nodes"] != ""

    def test_empty_members_returns_unknown(self):
        """空成员列表应返回 unknown。"""
        tree = dendropy.Tree.get(
            data="(A,B,(C,D));",
            schema="newick",
            preserve_underscores=True,
        )
        result = _check_monophyly_full(tree, "G", [])
        assert result["status"] == "unknown"

    def test_single_member_is_always_monophyletic(self):
        """单成员组应始终为单系群。"""
        # 在任何树拓扑中，单个叶节点都是单系群
        tree = dendropy.Tree.get(
            data="(A,B,(C,D));",
            schema="newick",
            preserve_underscores=True,
        )
        for tip in ["A", "B", "C", "D"]:
            result = _check_monophyly_full(tree, "G", [tip])
            assert result["status"] == "monophyletic"


# ---- 特殊标识符（LUCA/LACA/LBCA/ROOT）测试 ----
# 树拓扑：Bacteria 与 Archaea 各自单系，合起来（LUCA）也单系
DOMAIN_NEWICK = "((BAC1:0.1,BAC2:0.2):0.3,(ARC1:0.4,ARC2:0.5):0.6);"
DOMAIN_TAXONOMY = (
    "id\tDomain\tPhylum\n"
    "BAC1\tBacteria\tProteobacteria\n"
    "BAC2\tBacteria\tFirmicutes\n"
    "ARC1\tArchaea\tEuryarchaeota\n"
    "ARC2\tArchaea\tCrenarchaeota\n"
)


@pytest.fixture
def domain_tree_file(tmp_path):
    p = tmp_path / "domain.nwk"
    p.write_text(DOMAIN_NEWICK)
    return str(p)


@pytest.fixture
def domain_taxonomy_file(tmp_path):
    p = tmp_path / "domain.tsv"
    p.write_text(DOMAIN_TAXONOMY)
    return str(p)


class TestSpecialIdentifiers:
    """覆盖 LUCA/LACA/LBCA/ROOT 特殊标识符的检测、解析与单系性判定。"""

    def setup_method(self):
        clear_tip_index_cache()

    # --- is_special_identifier ---

    def test_is_special_identifier_recognizes_all(self):
        for name in ("LUCA", "LACA", "LBCA", "ROOT"):
            assert is_special_identifier(name)

    def test_is_special_identifier_case_insensitive(self):
        assert is_special_identifier("luca")
        assert is_special_identifier("LuCa")
        assert is_special_identifier("  LBCA  ")

    def test_is_special_identifier_rejects_normal_names(self):
        assert not is_special_identifier("Bacteria")
        assert not is_special_identifier("Escherichia")
        assert not is_special_identifier("")

    # --- get_special_identifier_description ---

    def test_description_luca_mentions_bacteria_and_archaea(self):
        desc = get_special_identifier_description("LUCA")
        assert "Bacteria" in desc
        assert "Archaea" in desc

    def test_description_laca_mentions_archaea(self):
        assert "Archaea" in get_special_identifier_description("LACA")

    def test_description_lbca_mentions_bacteria(self):
        assert "Bacteria" in get_special_identifier_description("LBCA")

    def test_description_root_mentions_tree(self):
        assert "root" in get_special_identifier_description("ROOT").lower()

    def test_description_unknown_returns_empty(self):
        assert get_special_identifier_description("UNKNOWN") == ""

    # --- resolve_special_identifier ---

    def test_resolve_luca_returns_all_members(self, domain_taxonomy_file):
        members = resolve_special_identifier("LUCA", domain_taxonomy_file)
        assert set(members) == {"BAC1", "BAC2", "ARC1", "ARC2"}

    def test_resolve_laca_returns_only_archaea(self, domain_taxonomy_file):
        members = resolve_special_identifier("LACA", domain_taxonomy_file)
        assert set(members) == {"ARC1", "ARC2"}
        assert "BAC1" not in members

    def test_resolve_lbca_returns_only_bacteria(self, domain_taxonomy_file):
        members = resolve_special_identifier("LBCA", domain_taxonomy_file)
        assert set(members) == {"BAC1", "BAC2"}
        assert "ARC1" not in members

    def test_resolve_root_returns_all_ids(self, domain_taxonomy_file):
        members = resolve_special_identifier("ROOT", domain_taxonomy_file)
        assert set(members) == {"BAC1", "BAC2", "ARC1", "ARC2"}

    def test_resolve_unknown_returns_none(self, domain_taxonomy_file):
        assert resolve_special_identifier("UNKNOWN", domain_taxonomy_file) is None

    def test_resolve_case_insensitive_identifier(self, domain_taxonomy_file):
        members = resolve_special_identifier("luca", domain_taxonomy_file)
        assert len(members) == 4

    def test_resolve_missing_domain_column_raises(self, tmp_path):
        bad = tmp_path / "bad.tsv"
        bad.write_text("id\tPhylum\nA\tProteo\n")
        with pytest.raises(MetadataParseError, match="Domain column"):
            resolve_special_identifier("LUCA", str(bad))

    def test_resolve_no_matching_members_raises(self, tmp_path):
        empty = tmp_path / "empty.tsv"
        empty.write_text("id\tDomain\nA\tEukarya\n")
        with pytest.raises(MetadataParseError, match="No tips found"):
            resolve_special_identifier("LUCA", str(empty))

    def test_resolve_case_insensitive_domain_column(self, tmp_path):
        tax = tmp_path / "t.tsv"
        tax.write_text("id\tdomain\nA\tBacteria\n")
        members = resolve_special_identifier("LBCA", str(tax), domain_column="Domain")
        assert members == ["A"]

    # --- check_monophyly_with_taxa_list with special identifiers ---

    def test_check_monophyly_luca_monophyletic(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["LUCA"])
        assert len(results) == 1
        assert results[0]["group"] == "LUCA"
        assert results[0]["status"] == "monophyletic"
        assert int(results[0]["member_count"]) == 4

    def test_check_monophyly_laca_monophyletic(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["LACA"])
        assert results[0]["status"] == "monophyletic"
        assert int(results[0]["member_count"]) == 2

    def test_check_monophyly_lbca_monophyletic(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["LBCA"])
        assert results[0]["status"] == "monophyletic"
        assert int(results[0]["member_count"]) == 2

    def test_check_monophyly_root_monophyletic(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["ROOT"])
        assert results[0]["status"] == "monophyletic"
        assert int(results[0]["member_count"]) == 4

    def test_check_monophyly_multiple_special(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["LACA", "LBCA"])
        assert len(results) == 2
        statuses = {r["status"] for r in results}
        assert statuses == {"monophyletic"}

    def test_lbca_polyphyletic_when_bacteria_scattered(self, tmp_path):
        # Bacteria 散落在树两端 -> 复系
        nwk = tmp_path / "scatter.nwk"
        nwk.write_text("((BAC1,ARC1),(BAC2,ARC2));")
        tax = tmp_path / "tax.tsv"
        tax.write_text(DOMAIN_TAXONOMY)
        results = check_monophyly_with_taxa_list(str(tax), str(nwk), taxa_list=["LBCA"])
        assert results[0]["status"] == "polyphyletic"
        assert int(results[0]["member_count"]) == 2

    def test_special_case_insensitive_in_check(self, domain_tree_file, domain_taxonomy_file):
        results = check_monophyly_with_taxa_list(domain_taxonomy_file, domain_tree_file, taxa_list=["luca"])
        assert results[0]["status"] == "monophyletic"
