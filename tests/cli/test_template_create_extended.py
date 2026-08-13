"""Extended tests for CLI template create commands and template_create entry."""

import json

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tValue\nA\tBacteria\t10\nB\tBacteria\t20\nC\tArchaea\t30\nD\tArchaea\t40\n"


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


class TestDirectCommandsMissing:
    """Smoke tests for direct create-* commands not yet covered."""

    def test_popup_info(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "popup.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-popup-info",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        assert "POPUP_INFO" in output.read_text()

    def test_branch_gradient(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-branch-gradient",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        assert "DATASET_GRADIENT" in output.read_text()

    def test_branch_gradient_use_mid_color(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg_mid.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-branch-gradient",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Value",
                "--use-mid-color",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "USE_MID_COLOR" in content


class TestBranchCoverageDirect:
    """Cover branches inside individual create-* command implementations."""

    def test_tree_colors_with_colors_json(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "tc_colors.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create-tree-colors",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                colors_json,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    @pytest.mark.parametrize("color_type", ["label", "branch", "width", "range", "gradient"])
    def test_tree_colors_non_clade_types(self, tmp_path, tree_file, taxonomy_file, color_type):
        output = tmp_path / f"tc_{color_type}.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-tree-colors",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--color-type",
                color_type,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "TREE_COLORS" in content
        if color_type == "gradient":
            # gradient uses ['id', 'value', 'color']
            assert "TREE_COLORS" in content

    def test_tree_colors_skips_nan(self, tmp_path, tree_file):
        tax = tmp_path / "nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "tc_nan.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-tree-colors",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_ranges_with_colors_json(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "ranges_colors.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create-ranges",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                colors_json,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_ranges_single_member_group(self, tmp_path, tree_file):
        # Only A is Bacteria, B/C/D are Archaea -> Bacteria group has 1 member
        tax = tmp_path / "single.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "ranges_single.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-ranges",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_highlight_with_colors_json(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "hl_colors.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create-highlight",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                colors_json,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_highlight_skips_nan(self, tmp_path, tree_file):
        tax = tmp_path / "nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "hl_nan.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-highlight",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_missing_column_raises(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style_err.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "MissingCol",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1

    def test_style_with_colors_json(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style_colors.txt"
        colors_json = json.dumps({"Bacteria": "#ff0000", "Archaea": "#00ff00"})
        result = runner.invoke(
            app,
            [
                "template",
                "create-style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                colors_json,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    @pytest.mark.parametrize("style_type", ["label", "label_background"])
    def test_style_types(self, tmp_path, tree_file, taxonomy_file, style_type):
        output = tmp_path / f"style_{style_type}.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--style-type",
                style_type,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content

    def test_image_skips_nan(self, tmp_path, tree_file):
        tax = tmp_path / "img.tsv"
        tax.write_text("id\timage\nA\timg1.png\nB\t\nC\timg2.png\nD\timg3.png\n")
        output = tmp_path / "img_nan.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-image",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--image-column",
                "image",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()


class TestTemplateCreateErrorPaths:
    """Cover typer.Exit(1) branches in template_create unified entry."""

    def _assert_missing(self, type_arg, extra_args, expected_keyword):
        result = runner.invoke(app, ["template", "create", type_arg, "-o", "/dev/null", *extra_args])
        assert result.exit_code == 1, f"Expected exit 1 for {type_arg}, got {result.exit_code}\n{result.output}"
        assert expected_keyword in result.output

    def test_color_strip_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("color-strip", ["--taxonomy", taxonomy_file], "需要")

    def test_branch_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("branch", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_simple_bar_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("simple-bar", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_multi_bar_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("multi-bar", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_heatmap_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("heatmap", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_symbols_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("symbols", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_pie_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("pie", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_boxplot_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("boxplot", ["--taxonomy", taxonomy_file], "需要")

    def test_gradient_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("gradient", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_connections_missing(self):
        self._assert_missing("connections", [], "需要")

    def test_labels_missing_column(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("labels", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_popup_info_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("popup-info", ["--taxonomy", taxonomy_file], "需要")

    def test_domains_missing(self):
        self._assert_missing("domains", [], "需要")

    def test_binary_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("binary", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_text_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("text", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_external_shape_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("external-shape", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_tree_colors_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("tree-colors", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_branch_gradient_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("branch-gradient", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_collapse_missing(self):
        self._assert_missing("collapse", [], "需要")

    def test_prune_missing(self):
        self._assert_missing("prune", [], "需要")

    def test_spacing_missing(self):
        self._assert_missing("spacing", [], "需要")

    def test_ranges_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("ranges", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_highlight_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("highlight", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_style_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("style", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_arrow_missing(self):
        self._assert_missing("arrow", [], "需要")

    def test_linechart_missing(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("linechart", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_image_missing_column(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("image", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_alignment_missing_column(self, tmp_path, tree_file, taxonomy_file):
        self._assert_missing("alignment", ["--taxonomy", taxonomy_file, "--tree", tree_file], "需要")

    def test_tanglegram_missing(self):
        self._assert_missing("tanglegram", [], "需要")

    def test_placement_missing(self):
        self._assert_missing("placement", [], "需要")

    def test_timescale_missing(self):
        self._assert_missing("timescale", [], "需要")

    def test_meme_missing(self):
        self._assert_missing("meme", [], "需要")

    def test_manual_missing(self):
        self._assert_missing("manual", [], "需要")

    def test_unknown_type(self):
        result = runner.invoke(app, ["template", "create", "unknown-xyz", "-o", "/dev/null"])
        assert result.exit_code == 1
        assert "未知模板类型" in result.output


class TestTemplateCreateSuccessPaths:
    """Cover template_create unified entry success paths for previously missed types."""

    def test_popup_info_via_create(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "popup2.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "popup-info",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_branch_gradient_via_create(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg2.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "branch-gradient",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()


class TestMoreBranchCoverageDirect:
    """Additional branch coverage for direct commands."""

    def test_branch_gradient_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg_err.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-branch-gradient",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "NoSuchCol",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1

    def test_branch_gradient_skips_nan_and_nonnumeric(self, tmp_path, tree_file):
        tax = tmp_path / "mixed.tsv"
        tax.write_text("id\tValue\nA\t10\nB\t\nC\txyz\nD\t20\n")
        output = tmp_path / "bg_mixed.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-branch-gradient",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_skips_nan(self, tmp_path, tree_file):
        tax = tmp_path / "nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "style_nan.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create-style",
                "--taxonomy",
                str(tax),
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_template_create_labels_no_column(self, tmp_path, tree_file, taxonomy_file):
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "labels",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "-o",
                str(tmp_path / "out.txt"),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output

    def test_template_create_image_no_column(self, tmp_path, tree_file, taxonomy_file):
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "image",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "-o",
                str(tmp_path / "out.txt"),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output

    def test_template_create_alignment_no_column(self, tmp_path, tree_file, taxonomy_file):
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "alignment",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "-o",
                str(tmp_path / "out.txt"),
            ],
        )
        assert result.exit_code == 1


class TestTemplateCreateForceOverride:
    """Regression: `template create --force` must overwrite an existing output
    file (review item 7). The unified entry threads --force/--no-clobber down to
    the dedicated sub-command, which otherwise re-checks the path and would raise
    SystemExit(1) on an existing file."""

    def test_force_overwrites_existing_file(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        out.write_text("STALE_CONTENT_SHOULD_BE_REPLACED")
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
                "-c",
                "Kingdom",
                "-o",
                str(out),
                "--force",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "STALE_CONTENT_SHOULD_BE_REPLACED" not in out.read_text()
        assert "DATASET_COLORSTRIP" in out.read_text()

    def test_without_force_keeps_existing_file(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        out.write_text("PREEXISTING_CONTENT")
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
                "-c",
                "Kingdom",
                "-o",
                str(out),
            ],
        )
        # Existing file without --force must be refused (SystemExit 1).
        assert result.exit_code == 1
        assert "already exists" in result.output
        assert out.read_text() == "PREEXISTING_CONTENT"
