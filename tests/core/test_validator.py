"""Tests for PyiTOL core validator module."""

import pandas as pd
import pytest

from pyitol.core.validator import (
    NAMED_COLORS,
    TemplateValidator,
    ValidationError,
    check_categorical_cardinality,
    check_delimiter_conflict,
    check_numeric_range,
    check_special_characters_in_ids,
    check_tree_ids_against_metadata,
    detect_file_type,
    detect_malicious_node_names,
    detect_taxonomy_circular_dependencies,
    validate_color_code,
    validate_file_not_empty,
    validate_inputs,
    validate_node_names,
)


class TestValidateColorCode:
    def test_valid_hex(self):
        valid, msg = validate_color_code("#FF0000")
        assert valid is True
        assert msg == ""

    def test_valid_hex_short(self):
        valid, _msg = validate_color_code("#F00")
        assert valid is True

    def test_valid_rgb(self):
        valid, _msg = validate_color_code("rgb(255, 0, 0)")
        assert valid is True

    def test_valid_rgba(self):
        valid, _msg = validate_color_code("rgba(255, 0, 0, 0.5)")
        assert valid is True

    def test_invalid_empty(self):
        valid, msg = validate_color_code("")
        assert valid is False
        assert "不能为空" in msg

    def test_missing_hash(self):
        valid, msg = validate_color_code("FF0000")
        assert valid is False
        assert "#" in msg

    def test_invalid_length(self):
        valid, msg = validate_color_code("#FF00")
        assert valid is False
        assert "RRGGBB" in msg

    def test_invalid_length_5(self):
        valid, msg = validate_color_code("#FF000")
        assert valid is False
        assert "RRGGBB" in msg

    def test_invalid_length_7(self):
        valid, msg = validate_color_code("#FF00000")
        assert valid is False
        assert "RRGGBB" in msg

    def test_no_rgb_when_disabled(self):
        valid, _msg = validate_color_code("rgb(255,0,0)", allow_rgb=False)
        assert valid is False

    def test_valid_hsl(self):
        valid, _msg = validate_color_code("hsl(120, 100%, 50%)")
        assert valid is True

    def test_valid_named_color(self):
        valid, _msg = validate_color_code("red")
        assert valid is True


class TestCheckDelimiterConflict:
    def test_tab_conflict(self):
        df = pd.DataFrame({"id": ["A", "B"], "val": ["x\ty", "z"]})
        errs = check_delimiter_conflict(df, "TAB")
        assert len(errs) == 1
        assert "分隔符冲突" in errs[0]

    def test_comma_conflict(self):
        df = pd.DataFrame({"id": ["A", "B"], "val": ["x,y", "z"]})
        errs = check_delimiter_conflict(df, "COMMA")
        assert len(errs) == 1

    def test_no_conflict(self):
        df = pd.DataFrame({"id": ["A", "B"], "val": ["x", "y"]})
        errs = check_delimiter_conflict(df, "TAB")
        assert len(errs) == 0


class TestCheckCategoricalCardinality:
    def test_too_many_categories(self):
        df = pd.DataFrame({"cat": [f"v{i}" for i in range(60)]})
        errs = check_categorical_cardinality(df, "cat", max_categories=50)
        assert len(errs) == 1
        assert "过多" in errs[0]

    def test_column_missing(self):
        df = pd.DataFrame({"cat": ["a", "b"]})
        errs = check_categorical_cardinality(df, "missing")
        assert len(errs) == 0


class TestCheckNumericRange:
    def test_below_min(self):
        df = pd.DataFrame({"val": [1, 2, 3]})
        errs = check_numeric_range(df, "val", min_val=2)
        assert len(errs) == 1
        assert "below" in errs[0] or "低于" in errs[0]

    def test_above_max(self):
        df = pd.DataFrame({"val": [10, 20, 30]})
        errs = check_numeric_range(df, "val", max_val=25)
        assert len(errs) == 1
        assert "exceeds" in errs[0] or "超过" in errs[0]

    def test_no_numeric(self):
        df = pd.DataFrame({"val": ["a", "b"]})
        errs = check_numeric_range(df, "val", min_val=0)
        assert len(errs) == 0

    def test_column_missing(self):
        df = pd.DataFrame({"val": [1, 2, 3]})
        errs = check_numeric_range(df, "missing", min_val=0)
        assert len(errs) == 0

    def test_biology_auto_range_gc_content(self):
        df = pd.DataFrame({"gc_content": [-5, 50, 105]})
        errs = check_numeric_range(df, "gc_content")
        assert len(errs) == 2
        assert "低于" in errs[0]
        assert "超过" in errs[1]


class TestCheckTreeIdsAgainstMetadata:
    def test_orphan_nodes(self):
        errs = check_tree_ids_against_metadata({"A", "B"}, {"A", "B", "C"})
        assert len(errs) == 1
        assert "孤立节点" in errs[0]

    def test_missing_nodes(self):
        errs = check_tree_ids_against_metadata({"A", "B", "C"}, {"A", "B"})
        assert len(errs) == 1
        assert "缺失注释" in errs[0]

    def test_perfect_match(self):
        errs = check_tree_ids_against_metadata({"A", "B"}, {"A", "B"})
        assert len(errs) == 0


class TestCheckSpecialCharactersInIds:
    def test_spaces(self):
        errs = check_special_characters_in_ids(["A B", "C"])
        assert len(errs) == 1
        assert "特殊符号" in errs[0]

    def test_tabs(self):
        errs = check_special_characters_in_ids(["A\tB"])
        assert len(errs) == 1

    def test_pipes(self):
        errs = check_special_characters_in_ids(["A|B"])
        assert len(errs) == 1

    def test_clean_ids(self):
        errs = check_special_characters_in_ids(["A", "B", "C_1"])
        assert len(errs) == 0


class TestTemplateValidator:
    def test_validate_tree_file_missing(self, tmp_path):
        v = TemplateValidator()
        assert v.validate_tree_file(str(tmp_path / "missing.nwk")) is False
        assert len(v.errors) == 1

    def test_validate_tree_file_empty(self, tmp_path):
        p = tmp_path / "empty.nwk"
        p.write_text("")
        v = TemplateValidator()
        assert v.validate_tree_file(str(p)) is False
        assert "为空" in v.errors[0]

    def test_validate_tree_file_valid(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("(A,B,(C,D));")
        v = TemplateValidator()
        assert v.validate_tree_file(str(p)) is True
        assert len(v.errors) == 0

    def test_validate_tree_file_format_warning(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("not a tree file")
        v = TemplateValidator()
        assert v.validate_tree_file(str(p)) is True
        assert len(v.warnings) == 1

    def test_validate_tree_file_dendropy_parse_error(self, tmp_path):
        p = tmp_path / "tree.nwk"
        # Invalid Newick: unmatched parenthesis
        p.write_text("(A,B,(C,D)")
        v = TemplateValidator()
        assert v.validate_tree_file(str(p)) is False
        assert len(v.errors) == 1
        assert "解析失败" in v.errors[0]

    def test_validate_metadata_file_missing(self, tmp_path):
        v = TemplateValidator()
        assert v.validate_metadata_file(str(tmp_path / "missing.csv")) is False

    def test_validate_metadata_file_unsupported(self, tmp_path):
        p = tmp_path / "data.doc"
        p.write_text("x")
        v = TemplateValidator()
        assert v.validate_metadata_file(str(p)) is True
        assert len(v.warnings) == 1

    def test_validate_template_file_missing(self, tmp_path):
        v = TemplateValidator()
        assert v.validate_template_file(str(tmp_path / "missing.txt")) is False

    def test_validate_template_file_no_header(self, tmp_path):
        p = tmp_path / "bad.txt"
        p.write_text("just some data")
        v = TemplateValidator()
        assert v.validate_template_file(str(p)) is False
        assert "缺少 iTOL 头部" in v.errors[0]

    def test_validate_template_file_valid(self, tmp_path):
        p = tmp_path / "good.txt"
        p.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\n")
        v = TemplateValidator()
        assert v.validate_template_file(str(p)) is True

    def test_validate_color_values(self):
        v = TemplateValidator()
        assert v.validate_color_values(["#FF0000", "#00FF00"]) is True
        assert len(v.errors) == 0

    def test_validate_color_values_invalid(self):
        v = TemplateValidator()
        assert v.validate_color_values(["bad_color"]) is False
        assert len(v.errors) == 1

    def test_validate_dataframe(self):
        df = pd.DataFrame({"id": ["A", "B"], "val": [1, 2]})
        v = TemplateValidator()
        result = v.validate_dataframe(df, separator="TAB")
        assert result is True

    def test_validate_dataframe_categorical_columns(self):
        df = pd.DataFrame({"id": ["A", "B"], "cat": ["x", "y"]})
        v = TemplateValidator()
        result = v.validate_dataframe(df, separator="TAB", categorical_columns=["cat"])
        assert result is True

    def test_validate_dataframe_numeric_columns(self):
        df = pd.DataFrame({"id": ["A", "B"], "num": [1, 100]})
        v = TemplateValidator()
        result = v.validate_dataframe(df, separator="TAB", numeric_columns=["num"])
        assert result is True

    def test_get_summary(self):
        v = TemplateValidator()
        v.errors = ["err1"]
        v.warnings = ["warn1"]
        summary = v.get_summary()
        assert summary["valid"] is False
        assert summary["errors"] == ["err1"]
        assert summary["warnings"] == ["warn1"]

    def test_raise_if_errors(self):
        v = TemplateValidator()
        v.errors = ["something wrong"]
        with pytest.raises(ValidationError, match="something wrong"):
            v.raise_if_errors()


class TestValidateInputs:
    def test_all_valid(self, tmp_path):
        tree = tmp_path / "tree.nwk"
        tree.write_text("(A,B);")
        meta = tmp_path / "meta.csv"
        meta.write_text("id\tval\nA\t1\n")
        tpl = tmp_path / "tpl.txt"
        tpl.write_text("DATASET_SIMPLEBAR")
        result = validate_inputs(
            tree_path=str(tree),
            metadata_path=str(meta),
            template_paths=[str(tpl)],
            colors=["#FF0000"],
        )
        assert result["valid"] is True

    def test_missing_tree(self, tmp_path):
        result = validate_inputs(tree_path=str(tmp_path / "missing.nwk"))
        assert result["valid"] is False
        assert "不存在" in result["errors"][0] or "not found" in result["errors"][0].lower()


class TestDetectMaliciousNodeNames:
    def test_control_char(self):
        malicious = detect_malicious_node_names(["node\x00name"])
        assert len(malicious) == 1

    def test_bidi_char(self):
        malicious = detect_malicious_node_names(["node\u202ename"])
        assert len(malicious) == 1

    def test_clean_name(self):
        malicious = detect_malicious_node_names(["normal_name", "node-1", "tip_A"])
        assert len(malicious) == 0

    def test_empty_name(self):
        malicious = detect_malicious_node_names([""])
        assert len(malicious) == 0


class TestValidateNodeNames:
    def test_malicious_names(self):
        errors = validate_node_names(["node\x00", "node\u202e"])
        assert len(errors) == 1
        assert "恶意字符" in errors[0] or "malicious" in errors[0].lower()

    def test_clean_names(self):
        errors = validate_node_names(["normal", "clean_123"])
        assert len(errors) == 0


class TestDetectTaxonomyCircularDependencies:
    def test_circular_detected(self, tmp_path):
        p = tmp_path / "circular.csv"
        p.write_text("id\tPhylum\tClass\nA\tProteo\tGammaproteo\nB\tGammaproteo\tProteo\n")
        errors = detect_taxonomy_circular_dependencies(str(p))
        assert len(errors) == 1
        assert "循环" in errors[0] or "circular" in errors[0].lower()

    def test_no_circular(self, tmp_path):
        p = tmp_path / "normal.csv"
        p.write_text("id\tPhylum\tClass\nA\tProteo\tGammaproteo\nB\tFirmicutes\tBacilli\n")
        errors = detect_taxonomy_circular_dependencies(str(p))
        assert len(errors) == 0

    def test_single_rank(self, tmp_path):
        p = tmp_path / "single.csv"
        p.write_text("id\tPhylum\nA\tProteo\n")
        errors = detect_taxonomy_circular_dependencies(str(p))
        assert len(errors) == 0


class TestValidateFileNotEmpty:
    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.txt"
        p.write_text("")
        errors = validate_file_not_empty(str(p))
        assert len(errors) == 1
        assert "为空" in errors[0] or "empty" in errors[0].lower()

    def test_non_empty_file(self, tmp_path):
        p = tmp_path / "data.txt"
        p.write_text("content")
        errors = validate_file_not_empty(str(p))
        assert len(errors) == 0

    def test_missing_file(self, tmp_path):
        errors = validate_file_not_empty(str(tmp_path / "missing.txt"))
        assert len(errors) == 0


class TestDetectFileType:
    def test_tree_newick(self, tmp_path):
        p = tmp_path / "tree.nwk"
        p.write_text("(A,B);")
        result = detect_file_type(str(p))
        assert result["exists"] is True
        assert result["category"] == "tree"
        assert result["format"] == "newick"

    def test_sequence_fasta(self, tmp_path):
        p = tmp_path / "seq.fa"
        p.write_text(">A\nATCG\n")
        result = detect_file_type(str(p))
        assert result["category"] == "sequence"
        assert result["format"] == "fasta"

    def test_table_csv(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("id,val\nA,1\n")
        result = detect_file_type(str(p))
        assert result["category"] == "table"
        assert result["format"] == "csv"

    def test_table_tsv(self, tmp_path):
        p = tmp_path / "data.tsv"
        p.write_text("id\tval\nA\t1\n")
        result = detect_file_type(str(p))
        assert result["category"] == "table"
        assert result["format"] == "tsv"

    def test_tree_nexus_by_content(self, tmp_path):
        p = tmp_path / "tree.txt"
        p.write_text("#NEXUS\nBEGIN TREES;\n")
        result = detect_file_type(str(p))
        assert result["category"] == "tree"
        assert result["format"] == "nexus"

    def test_missing_file(self, tmp_path):
        result = detect_file_type(str(tmp_path / "missing.nwk"))
        assert result["exists"] is False
        assert len(result["errors"]) == 1

    def test_empty_file(self, tmp_path):
        p = tmp_path / "empty.nwk"
        p.write_text("")
        result = detect_file_type(str(p))
        assert result["size"] == 0
        assert len(result["errors"]) == 1

    def test_unknown_extension_with_content(self, tmp_path):
        p = tmp_path / "data.xyz"
        p.write_text(">A\nATCG\n")
        result = detect_file_type(str(p))
        assert result["category"] == "sequence"
        assert result["format"] == "fasta"

    def test_unsupported_format_warning(self, tmp_path):
        p = tmp_path / "data.doc"
        p.write_text("some content")
        result = detect_file_type(str(p))
        assert "Unknown" in str(result.get("warnings", []))


class TestNamedColorValidation:
    def test_named_colors_extended(self):
        colors = [
            "black",
            "white",
            "red",
            "green",
            "blue",
            "yellow",
            "cyan",
            "orange",
            "purple",
            "pink",
            "brown",
            "gray",
            "grey",
            "darkred",
            "darkgreen",
            "darkblue",
            "lightblue",
            "lightgreen",
            "mediumseagreen",
            "midnightblue",
            "turquoise",
            "steelblue",
            "wheat",
            "crimson",
            "coral",
            "salmon",
            "gold",
            "khaki",
            "plum",
            "orchid",
            "tan",
            "beige",
            "ivory",
            "linen",
            "mistyrose",
            "seagreen",
            "skyblue",
            "snow",
            "springgreen",
            "thistle",
            "tomato",
            "whitesmoke",
            "yellowgreen",
        ]
        for color in colors:
            valid, msg = validate_color_code(color)
            assert valid is True, f"{color} should be valid: {msg}"

    def test_invalid_named_color(self):
        valid, _msg = validate_color_code("notacolor")
        assert valid is False

    @pytest.mark.parametrize("color_name", sorted(NAMED_COLORS))
    def test_all_named_colors_are_valid(self, color_name):
        """Ensure every named color in the built-in set passes validation."""
        valid, msg = validate_color_code(color_name)
        assert valid is True, f"{color_name} should be valid: {msg}"


class TestTemplateValidatorAdditional:
    def test_validate_metadata_file_valid_csv(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("id\tval\nA\t1\n")
        v = TemplateValidator()
        assert v.validate_metadata_file(str(p)) is True
        assert len(v.warnings) == 0

    def test_validate_metadata_file_unsupported_extension(self, tmp_path):
        p = tmp_path / "data.doc"
        p.write_text("x")
        v = TemplateValidator()
        assert v.validate_metadata_file(str(p)) is True
        assert len(v.warnings) == 1

    def test_validate_template_file_no_separator(self, tmp_path):
        p = tmp_path / "no_sep.txt"
        p.write_text("DATASET_COLORSTRIP\n")
        v = TemplateValidator()
        assert v.validate_template_file(str(p)) is True
        assert len(v.warnings) == 1
        # 错误信息为中文（含"分隔符"），英文 fallback 含 "SEPARATOR"
        assert "分隔符" in v.warnings[0] or "SEPARATOR" in v.warnings[0] or "separator" in v.warnings[0].lower()


class TestMaliciousNodeNames:
    """覆盖 detect_malicious_node_names / validate_node_names 安全检测。"""

    def test_clean_names_return_empty(self):
        assert detect_malicious_node_names(["A", "B", "Homo_sapiens"]) == []

    def test_control_char_nul_detected(self):
        assert detect_malicious_node_names(["A\x00B"]) == ["A\x00B"]

    def test_control_char_del_detected(self):
        assert detect_malicious_node_names(["bad\x7fname"]) == ["bad\x7fname"]

    def test_control_char_c1_range_detected(self):
        assert detect_malicious_node_names(["x\x9fy"]) == ["x\x9fy"]

    def test_bidi_override_detected(self):
        # U+202E RIGHT-TO-LEFT OVERRIDE，常用于伪装攻击
        malicious = "evil\u202etext"
        assert detect_malicious_node_names([malicious]) == [malicious]

    def test_bidi_isolate_detected(self):
        # U+2068 FIRST STRONG ISOLATE
        assert detect_malicious_node_names(["a\u2068b"]) == ["a\u2068b"]

    def test_empty_names_skipped(self):
        assert detect_malicious_node_names(["", None]) == []

    def test_mixed_clean_and_malicious(self):
        names = ["clean", "bad\x1ename", "also_clean"]
        result = detect_malicious_node_names(names)
        assert len(result) == 1
        assert "bad\x1ename" in result

    def test_tab_and_newline_not_flagged(self):
        # tab (\x09) 和换行 (\x0a) 不在控制字符检测范围内
        assert detect_malicious_node_names(["with\ttab", "with\nnewline"]) == []

    def test_validate_node_names_clean(self):
        assert validate_node_names(["A", "B"]) == []

    def test_validate_node_names_returns_error_message(self):
        errors = validate_node_names(["A\x00B", "C\x1eD"])
        assert len(errors) == 1
        assert "2" in errors[0]  # 2 个恶意名称

    def test_validate_node_names_sample_limit(self):
        # 超过 5 个恶意名称时，错误信息只显示前 5 个样本
        names = [f"name{i}\x00" for i in range(10)]
        errors = validate_node_names(names)
        assert len(errors) == 1
        assert "10" in errors[0]


class TestCircularDependencies:
    """覆盖 detect_taxonomy_circular_dependencies。"""

    def test_no_circular(self, tmp_path):
        p = tmp_path / "tax.tsv"
        p.write_text("id\tDomain\tPhylum\nA\tBacteria\tProteo\nB\tArchaea\tThermo\n")
        assert detect_taxonomy_circular_dependencies(str(p)) == []

    def test_circular_detected(self, tmp_path):
        # A 行: Domain=Bacteria, Phylum=Proteo
        # B 行: Domain=Proteo, Phylum=Bacteria  -> (Bacteria, Proteo) 和 (Proteo, Bacteria) 循环
        p = tmp_path / "tax.tsv"
        p.write_text("id\tDomain\tPhylum\nA\tBacteria\tProteo\nB\tProteo\tBacteria\n")
        errors = detect_taxonomy_circular_dependencies(str(p))
        assert len(errors) >= 1
        assert "circular" in errors[0].lower() or "循环" in errors[0]

    def test_single_rank_column_returns_empty(self, tmp_path):
        # 少于 2 个 rank 列时无法检测循环
        p = tmp_path / "tax.tsv"
        p.write_text("id\tDomain\nA\tBacteria\n")
        assert detect_taxonomy_circular_dependencies(str(p)) == []

    def test_same_value_no_circular(self, tmp_path):
        # 相同值不算循环 (va != vb 检查)
        p = tmp_path / "tax.tsv"
        p.write_text("id\tDomain\tPhylum\nA\tX\tX\n")
        assert detect_taxonomy_circular_dependencies(str(p)) == []

    def test_three_ranks_circular(self, tmp_path):
        # 三列中相邻列循环
        p = tmp_path / "tax.tsv"
        p.write_text("id\tA\tB\tC\n1\tX\tY\tZ\n2\tY\tX\tW\n")
        errors = detect_taxonomy_circular_dependencies(str(p))
        assert len(errors) >= 1
