"""Tests for template command edge cases: NaN, missing columns, colors param, validation errors."""

import json
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


class TestTemplateCreateEdgeCases:
    """Cover remaining branches in individual create-* commands."""

    def test_tree_colors_with_colors_param(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tree-colors",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
                "--colors",
                colors_json,
            ],
        )
        assert result.exit_code == 0, result.output

    def test_tree_colors_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tree-colors",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_branch_gradient_missing_column(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "branch-gradient",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "MissingCol",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1

    def test_branch_gradient_with_na_and_string(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\tValue\nA\tBacteria\t10\nB\tBacteria\t\nC\tArchaea\tfoo\nD\tArchaea\t20\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "branch-gradient",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Value",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_ranges_with_colors_param(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "ranges",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
                "--colors",
                colors_json,
            ],
        )
        assert result.exit_code == 0, result.output

    def test_ranges_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "ranges",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_highlight_with_colors_param(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "highlight",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
                "--colors",
                colors_json,
            ],
        )
        assert result.exit_code == 0, result.output

    def test_highlight_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "highlight",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_style_missing_column(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "MissingCol",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1

    def test_style_with_colors_param(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
                "--colors",
                colors_json,
            ],
        )
        assert result.exit_code == 0, result.output

    def test_style_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_image_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text(
            "id\tKingdom\timg\nA\tBacteria\ticon.png\nB\tBacteria\t\nC\tArchaea\ticon.png\nD\tArchaea\ticon.png\n"
        )
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "image",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--image-column",
                "img",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_template_create_labels_missing_column(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "labels",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output

    def test_template_create_image_missing_column(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "image",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output

    def test_template_create_alignment_missing_column(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "alignment",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output


class TestTemplateBundleEdgeCases:
    """Cover remaining branches in template_bundle."""

    def test_bundle_branch_gradient_mid_color(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tValue\nA\t10\nB\t20\nC\t30\nD\t40\n")
        bundle = [{"type": "branch-gradient", "column": "Value", "use_mid_color": True, "color_mid": "#00ff00"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_branch_gradient_with_string_value(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tValue\nA\t10\nB\tfoo\nC\t30\nD\t40\n")
        bundle = [{"type": "branch-gradient", "column": "Value"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_simple_bar_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tValue\nA\t10\nB\t\nC\tfoo\nD\t20\n")
        bundle = [{"type": "simple-bar", "column": "Value"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_multi_bar_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tV1\tV2\nA\t1\t2\nB\t\t3\nC\t4\t\nD\t5\t6\n")
        bundle = [{"type": "multi-bar", "columns": ["V1", "V2"]}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_heatmap_two_color_gradient(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tValue\nA\t1\nB\t2\nC\t3\nD\t4\n")
        bundle = [{"type": "heatmap", "columns": ["Value"], "color_gradient": ["#ff0000", "#0000ff"]}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_pie_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tV1\tV2\nA\t1\t2\nB\t\t3\nC\t4\t5\nD\t6\t7\n")
        bundle = [{"type": "pie", "columns": ["V1", "V2"], "colors": ["#ff0000", "#00ff00"]}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_gradient_column_not_found(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\n")
        bundle = [{"type": "gradient", "column": "Missing"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_gradient_with_string_value(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tValue\nA\t10\nB\tfoo\nC\t30\nD\t40\n")
        bundle = [{"type": "gradient", "column": "Value"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_style_label_and_label_background(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        bundle = [
            {"type": "style", "column": "Kingdom", "style_type": "label"},
            {"type": "style", "column": "Kingdom", "style_type": "label_background"},
        ]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_style_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        bundle = [{"type": "style", "column": "Kingdom", "style_type": "branch"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_tanglegram_from_connections(self, tmp_path, tree_file):
        conn = tmp_path / "conn.json"
        conn.write_text('[["A", "B"], ["C", "D"]]')
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        bundle = [{"type": "tanglegram", "data_file": str(conn)}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output

    def test_bundle_missing_data_file(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\n")
        bundle = [{"type": "connections", "data_file": "/nonexistent/file.csv"}]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--tree",
                tree_file,
                "--taxonomy",
                str(tax),
                "--output-dir",
                str(tmp_path),
                "--config",
                json.dumps(bundle),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "已跳过" in result.output


class TestTemplateValidateEdgeCases:
    """Cover template_validate error branches."""

    @patch("pyitol.templates.learner.learn_template")
    def test_validate_with_errors(self, mock_learn, tmp_path):
        mock_learn.return_value = {
            "datasets": [{"type": "color_strip", "validation_errors": ["bad header"], "parameters": {}, "data": []}]
        }
        tf = tmp_path / "fake.txt"
        tf.write_text("FAKE")
        result = runner.invoke(app, ["template", "validate", "--template", str(tf)])
        assert result.exit_code == 1
        assert "验证失败" in result.output

    @patch("pyitol.templates.learner.learn_template")
    def test_validate_empty_datasets(self, mock_learn, tmp_path):
        mock_learn.return_value = {"datasets": []}
        tf = tmp_path / "fake.txt"
        tf.write_text("FAKE")
        result = runner.invoke(app, ["template", "validate", "--template", str(tf)])
        assert result.exit_code == 1
        assert "未检测到数据集" in result.output
