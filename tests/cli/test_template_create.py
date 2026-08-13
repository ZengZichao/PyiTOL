"""Tests for unified template create CLI command."""

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


class TestTemplateCreateUnified:
    def test_color_strip(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "color_strip.txt"
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
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_COLORSTRIP" in content

    def test_branch(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "branch.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "branch",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "TREE_COLORS" in content

    def test_simple_bar(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bar.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "simple-bar",
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
        content = output.read_text()
        assert "DATASET_SIMPLEBAR" in content

    def test_highlight(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "highlight.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "highlight",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_STYLE" in content
        assert "label_background" in content

    def test_heatmap(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "heatmap.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "heatmap",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--columns",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_HEATMAP" in content

    def test_labels(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "labels.txt"
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
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "LABELS" in content

    def test_collapse(self, tmp_path):
        output = tmp_path / "collapse.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "collapse",
                "--node-ids",
                "A,B",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "COLLAPSE" in content

    def test_unknown_type(self, tmp_path):
        output = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "unknown-type",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1
        assert "未知模板类型" in result.output

    def test_missing_required_params(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "out.txt"
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
                # missing --column
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 1
        assert "需要" in result.output

    def test_alias_colorstrip(self, tmp_path, tree_file, taxonomy_file):
        """Test that underscore alias works."""
        output = tmp_path / "alias.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "colorstrip",
                "--taxonomy",
                taxonomy_file,
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

    def test_multi_bar(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "multi.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "multi-bar",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--columns",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_MULTIBAR" in content

    def test_tree_colors(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "tree_colors.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tree-colors",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "TREE_COLORS" in content

    def test_style(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_STYLE" in content

    def test_symbols(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "symbols.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "symbols",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_SYMBOL" in content

    def test_gradient(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "gradient.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "gradient",
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
        content = output.read_text()
        assert "COLORSTRIP" in content or "GRADIENT" in content

    def test_ranges(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "ranges.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "ranges",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_RANGE" in content

    def test_text(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "text.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "text",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_TEXT" in content

    def test_external_shape(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "shape.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "external-shape",
                "--taxonomy",
                taxonomy_file,
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
        content = output.read_text()
        assert "DATASET_EXTERNALSHAPE" in content or "EXTERNALSHAPE" in content

    def test_pie(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "pie.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "pie",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--columns",
                "Value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_PIECHART" in content

    def test_boxplot(self, tmp_path):
        tsv = "id\tminimum\tq1\tmedian\tq3\tmaximum\nA\t1\t2\t3\t4\t5\nB\t2\t3\t4\t5\t6\n"
        tax = tmp_path / "bp.tsv"
        tax.write_text(tsv)
        tree = tmp_path / "bp.nwk"
        tree.write_text(SIMPLE_NEWICK)
        output = tmp_path / "boxplot.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "boxplot",
                "--taxonomy",
                str(tax),
                "--tree",
                str(tree),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_BOXPLOT" in content

    def test_connections(self, tmp_path):
        conn_file = tmp_path / "conn.json"
        conn_file.write_text('[["A", "B"], ["C", "D"]]')
        output = tmp_path / "conn.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "connections",
                "--connections",
                str(conn_file),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_CONNECTION" in content

    def test_domains(self, tmp_path):
        data = tmp_path / "dom.json"
        data.write_text('[{"id": "A", "from": "10", "to": "50", "type": "domain", "color": "#ff0000"}]')
        output = tmp_path / "dom.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "domains",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_DOMAINS" in content

    def test_binary(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "binary.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "binary",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--columns",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_BINARY" in content

    def test_linechart(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "linechart.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "linechart",
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
        content = output.read_text()
        assert "DATASET_LINECHART" in content

    def test_image(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "img.txt"
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
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_IMAGE" in content

    def test_alignment(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "al.txt"
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
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_ALIGNMENT" in content

    def test_tanglegram(self, tmp_path):
        output = tmp_path / "tg.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tanglegram",
                "--connections",
                "A-C,B-D",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_TANGLEGRAM" in content

    def test_placement(self, tmp_path):
        data = tmp_path / "pl.csv"
        data.write_text("id\tposition\tcount\tcolor\nA\t100\t5\t#ff0000\n")
        output = tmp_path / "pl.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "placement",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_PLACEMENT" in content

    def test_timescale(self, tmp_path):
        data = tmp_path / "ts.csv"
        data.write_text("time_point\tlabel\tcolor\n0\tPresent\t#000000\n")
        output = tmp_path / "ts.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "timescale",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_TIMESCALE" in content

    def test_meme(self, tmp_path):
        data = tmp_path / "meme.csv"
        data.write_text("id\tstart\tend\tname\tcolor\nA\t10\t20\tmotif1\t#ff0000\n")
        output = tmp_path / "meme.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "meme",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_MEME" in content

    def test_arrow(self, tmp_path):
        data = tmp_path / "arrow.csv"
        data.write_text("id\tposition\tdirection\tcolor\nA\t100\tright\t#ff0000\n")
        output = tmp_path / "arrow.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "arrow",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_ARROWS" in content

    def test_manual(self, tmp_path):
        data = tmp_path / "manual.csv"
        data.write_text("id\tlabel\nA\tmanual data\n")
        output = tmp_path / "manual.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "manual",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_MANUAL" in content

    def test_prune(self, tmp_path):
        output = tmp_path / "prune.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "prune",
                "--node-ids",
                "A,B",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "PRUNE" in content

    def test_spacing(self, tmp_path):
        data = tmp_path / "spacing.csv"
        data.write_text("id\tfactor\nA\t2\n")
        output = tmp_path / "spacing.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "spacing",
                "--data-file",
                str(data),
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "SPACING" in content


class TestTemplateCreateMissingParams:
    """Test all missing parameter branches in template_create unified entry."""

    @pytest.mark.parametrize(
        "template_type,args,expected_substring",
        [
            ("branch", ["--taxonomy", "{tax}", "--tree", "{tree}"], "branch' 需要 --taxonomy, --tree 和 --column"),
            (
                "simple-bar",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "simple-bar' 需要 --taxonomy, --tree 和 --column",
            ),
            (
                "multi-bar",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "multi-bar' 需要 --taxonomy, --tree 和 --columns",
            ),
            ("heatmap", ["--taxonomy", "{tax}", "--tree", "{tree}"], "heatmap' 需要 --taxonomy, --tree 和 --columns"),
            ("symbols", ["--taxonomy", "{tax}", "--tree", "{tree}"], "symbols' 需要 --taxonomy, --tree 和 --column"),
            ("pie", ["--taxonomy", "{tax}", "--tree", "{tree}"], "pie' 需要 --taxonomy, --tree 和 --columns"),
            ("boxplot", ["--taxonomy", "{tax}"], "boxplot' 需要 --taxonomy 和 --tree"),
            ("gradient", ["--taxonomy", "{tax}", "--tree", "{tree}"], "gradient' 需要 --taxonomy, --tree 和 --column"),
            ("connections", [], "connections' 需要 --connections"),
            ("labels", ["--taxonomy", "{tax}"], "labels' 需要 --taxonomy 和 --tree"),
            ("popup-info", ["--taxonomy", "{tax}"], "popup-info' 需要 --taxonomy 和 --tree"),
            ("domains", [], "domains' 需要 --data-file"),
            ("binary", ["--taxonomy", "{tax}", "--tree", "{tree}"], "binary' 需要 --taxonomy, --tree 和 --columns"),
            ("text", ["--taxonomy", "{tax}", "--tree", "{tree}"], "text' 需要 --taxonomy, --tree 和 --column"),
            (
                "external-shape",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "external-shape' 需要 --taxonomy, --tree 和 --column",
            ),
            (
                "tree-colors",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "tree-colors' 需要 --taxonomy, --tree 和 --column",
            ),
            (
                "branch-gradient",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "branch-gradient' 需要 --taxonomy, --tree 和 --column",
            ),
            ("collapse", [], "collapse 需要 --node-ids 或 --taxon"),
            ("prune", [], "prune' 需要 --node-ids"),
            ("spacing", [], "spacing' 需要 --data-file"),
            ("ranges", ["--taxonomy", "{tax}", "--tree", "{tree}"], "ranges' 需要 --taxonomy, --tree 和 --column"),
            (
                "highlight",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "highlight' 需要 --taxonomy, --tree 和 --column",
            ),
            ("style", ["--taxonomy", "{tax}", "--tree", "{tree}"], "style' 需要 --taxonomy, --tree 和 --column"),
            ("arrow", [], "arrow' 需要 --data-file"),
            (
                "linechart",
                ["--taxonomy", "{tax}", "--tree", "{tree}"],
                "linechart' 需要 --taxonomy, --tree 和 --column",
            ),
            ("image", ["--taxonomy", "{tax}"], "image' 需要 --taxonomy 和 --tree"),
            ("alignment", ["--taxonomy", "{tax}"], "alignment' 需要 --taxonomy 和 --tree"),
            ("tanglegram", [], "tanglegram' 需要 --connections"),
            ("placement", [], "placement' 需要 --data-file"),
            ("timescale", [], "timescale' 需要 --data-file"),
            ("meme", [], "meme' 需要 --data-file"),
            ("manual", [], "manual' 需要 --data-file"),
        ],
    )
    def test_missing_params(self, template_type, args, expected_substring, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "out.txt")
        formatted_args = [arg.format(tax=taxonomy_file, tree=tree_file) for arg in args] + ["--output", output]
        result = runner.invoke(app, ["template", "create", template_type, *formatted_args])
        assert result.exit_code == 1, result.output
        assert expected_substring in result.output

    def test_labels_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "out.txt")
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
                "--output",
                output,
            ],
        )
        assert result.exit_code == 1
        assert "labels' 需要 --column 或 --label-column" in result.output

    def test_image_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "out.txt")
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
                "--output",
                output,
            ],
        )
        assert result.exit_code == 1
        assert "image' 需要 --column 或 --image-column" in result.output

    def test_alignment_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "out.txt")
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
                "--output",
                output,
            ],
        )
        assert result.exit_code == 1
        assert "alignment' 需要 --column 或 --alignment-column" in result.output


class TestTemplateCreateBranches:
    """Test specific branches within template command bodies."""

    def test_popup_info(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "popup.txt"
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
        content = output.read_text()
        assert "POPUP_INFO" in content

    def test_branch_gradient(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg.txt"
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
        content = output.read_text()
        assert "DATASET_GRADIENT" in content

    def test_tree_colors_with_colors(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "tc.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tree-colors",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                '{"Bacteria": "#ff0000", "Archaea": "#0000ff"}',
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_tree_colors_with_nan(self, tmp_path, tree_file):
        tax = tmp_path / "tax_nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "tc.txt"
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
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    @pytest.mark.parametrize("ctype", ["label", "branch", "width", "range", "gradient"])
    def test_tree_colors_color_types(self, tmp_path, tree_file, taxonomy_file, ctype):
        output = tmp_path / f"tc_{ctype}.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tree-colors",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--color-type",
                ctype,
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "TREE_COLORS" in content

    def test_ranges_with_colors(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "ranges.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "ranges",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                '{"Bacteria": "#ff0000", "Archaea": "#0000ff"}',
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_ranges_single_member(self, tmp_path):
        tree = tmp_path / "sm.nwk"
        tree.write_text("(A:0.1,B:0.2,C:0.3);")
        tax = tmp_path / "sm.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\n")
        output = tmp_path / "ranges.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "ranges",
                "--taxonomy",
                str(tax),
                "--tree",
                str(tree),
                "--column",
                "Kingdom",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_RANGE" in content

    def test_highlight_with_colors(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "hl.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "highlight",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                '{"Bacteria": "#ff0000", "Archaea": "#0000ff"}',
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_highlight_with_nan(self, tmp_path, tree_file):
        tax = tmp_path / "tax_nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "hl.txt"
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
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_with_colors(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--colors",
                '{"Bacteria": "#ff0000", "Archaea": "#0000ff"}',
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_with_nan(self, tmp_path, tree_file):
        tax = tmp_path / "tax_nan.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        output = tmp_path / "style.txt"
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
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_style_label(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style_label.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--style-type",
                "label",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content

    def test_style_label_background(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style_lb.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "Kingdom",
                "--style-type",
                "label_background",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
        content = output.read_text()
        assert "DATASET_STYLE" in content

    def test_style_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "style_err.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "style",
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--column",
                "NonExistent",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code != 0

    def test_image_with_nan(self, tmp_path, tree_file):
        tax = tmp_path / "tax_img.tsv"
        tax.write_text("id\timage\nA\timg1.png\nB\t\nC\timg2.png\nD\timg3.png\n")
        output = tmp_path / "img.txt"
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
                "image",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_branch_gradient_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg_err.txt"
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
                "NonExistent",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code != 0

    def test_branch_gradient_with_nan(self, tmp_path, tree_file):
        tax = tmp_path / "tax_nan.tsv"
        tax.write_text("id\tvalue\nA\t0.5\nB\t\nC\t0.3\nD\t0.6\n")
        output = tmp_path / "bg.txt"
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
                "value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_branch_gradient_non_numeric(self, tmp_path, tree_file):
        tax = tmp_path / "tax_bad.tsv"
        tax.write_text("id\tvalue\nA\t0.5\nB\tbad\nC\t0.3\nD\t0.6\n")
        output = tmp_path / "bg.txt"
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
                "value",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()

    def test_branch_gradient_use_mid_color(self, tmp_path, tree_file, taxonomy_file):
        output = tmp_path / "bg_mid.txt"
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
                "--use-mid-color",
                "--output",
                str(output),
            ],
        )
        assert result.exit_code == 0, result.output
        assert output.exists()
