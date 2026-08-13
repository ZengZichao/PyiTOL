"""Tests for PyiTOL template learner module."""

import json

import pytest

from pyitol.templates.learner import (
    HEADER_REVERSE,
    learn_common_themes,
    learn_field,
    learn_separator,
    learn_template,
    learn_type,
    train_theme,
)


@pytest.fixture
def template_file(tmp_path):
    p = tmp_path / "test.txt"
    lines = [
        "TEMPLATE_NAME test_template",
        "",
        "DATASET_COLORSTRIP",
        "SEPARATOR TAB",
        "DATASET_LABEL\ttest_color_strip",
        "COLOR\t#ff0000",
        "STRIP_WIDTH\t50",
        "",
        "DATA",
        "A\tGroup1\t#ff0000",
        "B\tGroup1\t#ff0000",
        "C\tGroup2\t#00ff00",
        "D\tGroup2\t#00ff00",
    ]
    p.write_text("\n".join(lines) + "\n")
    return str(p)


class TestHeaderReverse:
    def test_all_headers_mapped(self):
        for _header, ds_type in HEADER_REVERSE.items():
            assert ds_type is not None
            assert len(ds_type) > 0

    def test_core_types_present(self):
        assert "DATASET_COLORSTRIP" in HEADER_REVERSE
        assert "DATASET_SIMPLEBAR" in HEADER_REVERSE
        assert "DATASET_HEATMAP" in HEADER_REVERSE
        assert "DATASET_SYMBOLS" in HEADER_REVERSE
        assert "TREE_COLORS" in HEADER_REVERSE
        assert "COLLAPSE" in HEADER_REVERSE


class TestLearnTemplate:
    def test_parse_basic(self, template_file):
        result = learn_template(template_file)
        assert result["template_name"] == "test_template"
        assert len(result["datasets"]) == 1

    def test_extract_parameters(self, template_file):
        result = learn_template(template_file)
        ds = result["datasets"][0]
        assert ds["parameters"]["STRIP_WIDTH"] == "50"
        assert ds["parameters"]["DATASET_LABEL"] == "test_color_strip"

    def test_extract_data(self, template_file):
        result = learn_template(template_file)
        ds = result["datasets"][0]
        assert len(ds["data"]) == 4
        assert ds["data"][0]["id"] == "A"
        assert ds["data"][0]["value"] == "Group1"

    def test_extract_columns(self, template_file):
        result = learn_template(template_file)
        ds = result["datasets"][0]
        assert ds["columns"] == ["id", "value", "color"]


class TestTrainTheme:
    def test_empty_dir(self, tmp_path):
        result = train_theme(str(tmp_path))
        assert result["summary"]["total_files"] == 0
        assert result["summary"]["total_datasets"] == 0
        assert result["themes"] == {}

    def test_single_template(self, tmp_path):
        p = tmp_path / "test.txt"
        lines = [
            "TEMPLATE_NAME test_template",
            "",
            "DATASET_COLORSTRIP",
            "SEPARATOR TAB",
            "DATASET_LABEL\ttest_color_strip",
            "COLOR\t#ff0000",
            "STRIP_WIDTH\t50",
            "",
            "DATA",
            "A\tGroup1\t#ff0000",
            "B\tGroup1\t#ff0000",
        ]
        p.write_text("\n".join(lines) + "\n")
        result = train_theme(str(tmp_path), min_freq=0.5)
        assert result["summary"]["total_files"] == 1
        assert result["summary"]["total_datasets"] == 1
        assert "dataset_colorstrip" in result["themes"]
        theme = result["themes"]["dataset_colorstrip"]
        assert theme["count"] == 1
        assert theme["recommended_defaults"]["COLOR"] == "#ff0000"
        assert theme["recommended_defaults"]["STRIP_WIDTH"] == "50"
        assert theme["color_distribution"][0]["color"] == "#ff0000"

    def test_multiple_templates_aggregation(self, tmp_path):
        # Template 1
        p1 = tmp_path / "t1.txt"
        p1.write_text(
            "DATASET_COLORSTRIP\nSEPARATOR TAB\nDATASET_LABEL\tl1\nCOLOR\t#ff0000\nSTRIP_WIDTH\t50\nDATA\nA\tv1\t#ff0000\n"  # noqa: E501
        )
        # Template 2
        p2 = tmp_path / "t2.txt"
        p2.write_text(
            "DATASET_COLORSTRIP\nSEPARATOR TAB\nDATASET_LABEL\tl2\nCOLOR\t#ff0000\nSTRIP_WIDTH\t60\nDATA\nB\tv2\t#00ff00\n"  # noqa: E501
        )
        result = train_theme(str(tmp_path), min_freq=0.5)
        assert result["summary"]["total_files"] == 2
        assert result["summary"]["total_datasets"] == 2
        theme = result["themes"]["dataset_colorstrip"]
        # COLOR appears in both -> recommended
        assert "COLOR" in theme["recommended_defaults"]
        # STRIP_WIDTH differs -> not recommended at min_freq=0.5 (each 50%)
        # Actually each value has freq 0.5, so with >=0.5 it should be included
        assert "STRIP_WIDTH" in theme["recommended_defaults"]
        assert theme["recommended_defaults"]["COLOR"] == "#ff0000"

    def test_json_serializable(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nDATASET_LABEL\tbar\nCOLOR\t#3c5484\nWIDTH\t50\nDATA\nA\t10\n")
        result = train_theme(str(tmp_path))
        # Should not raise
        json.dumps(result)

    def test_not_a_directory(self):
        with pytest.raises(NotADirectoryError):
            train_theme("/nonexistent/path/12345")


class TestLearnType:
    def test_empty_lines(self):
        assert learn_type(["", "   ", ""]) == ""

    def test_comment_only(self):
        assert learn_type(["# comment", "  # another"]) == ""

    def test_returns_first_valid_line(self):
        assert learn_type(["", "# comment", "DATASET_COLORSTRIP"]) == "DATASET_COLORSTRIP"


class TestLearnSeparator:
    def test_no_separator(self):
        assert learn_separator(["DATASET_COLORSTRIP", "DATA"]) == "\t"

    def test_invalid_separator(self):
        assert learn_separator(["SEPARATOR FOO"]) == "\t"


class TestLearnField:
    def test_all_fields(self):
        params = {
            "FIELD_LABELS": "a\tb",
            "FIELD_COLORS": "#ff0000\t#00ff00",
            "FIELD_SHAPES": "1\t2",
        }
        result = learn_field(params, "\t")
        assert result["labels"] == ["a", "b"]
        assert result["colors"] == ["#ff0000", "#00ff00"]
        assert result["shapes"] == ["1", "2"]


class TestLearnCommonThemes:
    def test_extracts_themes(self):
        params = {"MARGIN": "10", "SHOW_INTERNAL": "1", "UNKNOWN": "x"}
        result = learn_common_themes(params)
        assert "basic_theme" in result
        assert result["basic_theme"]["margin"] == "10"


class TestLearnTemplateExtended:
    def test_multiple_datasets(self, tmp_path):
        p = tmp_path / "multi.txt"
        p.write_text(
            "DATASET_COLORSTRIP\nSEPARATOR TAB\nDATA\nA\tv1\t#ff0000\n\nDATASET_SIMPLEBAR\nSEPARATOR TAB\nDATA\nA\t10\n"
        )
        result = learn_template(str(p))
        assert len(result["datasets"]) == 2
        assert result["datasets"][0]["type"] == "dataset_colorstrip"
        assert result["datasets"][1]["type"] == "dataset_simple_bar"

    def test_special_headers_column_inference(self, tmp_path):
        p = tmp_path / "special.txt"
        lines = [
            "TREE_COLORS",
            "SEPARATOR TAB",
            "DATA",
            "A\tclade\t#ff0000\tstyle1\tsize1",
            "",
            "COLLAPSE",
            "SEPARATOR TAB",
            "DATA",
            "A\textra",
            "",
            "PRUNE",
            "SEPARATOR TAB",
            "DATA",
            "B\textra",
            "",
            "SPACING",
            "SEPARATOR TAB",
            "DATA",
            "C\t2",
            "",
            "LABELS",
            "SEPARATOR TAB",
            "DATA",
            "D\tLabelD",
            "",
            "POPUP_INFO",
            "SEPARATOR TAB",
            "DATA",
            "E\tTitle\tContent",
            "",
            "DATASET_SYMBOLS",
            "SEPARATOR TAB",
            "DATA",
            "F\tcircle\t30\t#ff0000\tLabel",
            "",
            "DATASET_CONNECTION",
            "SEPARATOR TAB",
            "DATA",
            "G\tH\t#ff0000\t2\tsolid",
            "",
            "DATASET_BINARY",
            "SEPARATOR TAB",
            "DATA",
            "I\t1\t0",
        ]
        p.write_text("\n".join(lines) + "\n")
        result = learn_template(str(p))
        types = {ds["type"] for ds in result["datasets"]}
        assert "dataset_tree_colors" in types
        assert "dataset_collapse" in types
        assert "dataset_prune" in types
        assert "dataset_spacing" in types
        assert "dataset_labels" in types
        assert "dataset_popup_info" in types
        assert "dataset_symbols" in types
        assert "dataset_connections" in types
        assert "dataset_binary" in types
        for ds in result["datasets"]:
            if ds["type"] == "dataset_tree_colors":
                assert ds["columns"] == ["id", "type", "color", "style", "size"]
            elif ds["type"] == "dataset_collapse":
                assert ds["columns"] == ["id"]
            elif ds["type"] == "dataset_symbols":
                assert ds["columns"] == ["id", "type", "value", "color", "label"]

    def test_lines_before_dataset_ignored(self, tmp_path):
        """Cover line 276: lines before first DATASET header are skipped."""
        p = tmp_path / "pre.txt"
        p.write_text("RANDOM_PARAM\tvalue\nDATASET_SIMPLEBAR\nSEPARATOR TAB\nDATA\nA\t10\n")
        result = learn_template(str(p))
        assert len(result["datasets"]) == 1
        assert result["datasets"][0]["type"] == "dataset_simple_bar"

    def test_parameter_without_value(self, tmp_path):
        """Cover lines 334-335: parameter lines with no value."""
        p = tmp_path / "noval.txt"
        p.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nSHOW_INTERNAL\nDATA\nA\t10\n")
        result = learn_template(str(p))
        ds = result["datasets"][0]
        assert ds["parameters"]["SHOW_INTERNAL"] == ""


class TestTrainThemeExtended:
    def test_unreadable_file_skipped(self, tmp_path):
        bad = tmp_path / "bad.txt"
        bad.mkdir()
        good = tmp_path / "good.txt"
        good.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nDATA\nA\t10\n")
        result = train_theme(str(tmp_path))
        assert result["summary"]["total_files"] == 2
        assert result["summary"]["total_datasets"] == 1

    def test_field_metadata_and_common_themes(self, tmp_path):
        p = tmp_path / "t.txt"
        lines = [
            "DATASET_BINARY",
            "SEPARATOR TAB",
            "FIELD_LABELS\tf1\tf2",
            "FIELD_COLORS\t#ff0000\t#00ff00",
            "FIELD_SHAPES\t1\t2",
            "MARGIN\t10",
            "SHOW_INTERNAL\t1",
            "DATA",
            "A\t1\t0",
        ]
        p.write_text("\n".join(lines) + "\n")
        result = train_theme(str(tmp_path), min_freq=1.0)
        theme = result["themes"]["dataset_binary"]
        assert theme["count"] == 1
        assert "field_labels" in theme["field_distribution"]
        assert "field_colors" in theme["field_distribution"]
        assert "field_shapes" in theme["field_distribution"]
        colors = [c["color"] for c in theme["color_distribution"]]
        assert "#ff0000" in colors
