"""Tests for template create unified entry covering all template types."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tValue\ttitle\tcontent\nA\tBacteria\t10\tA_title\tA_content\nB\tBacteria\t20\tB_title\tB_content\nC\tArchaea\t30\tC_title\tC_content\nD\tArchaea\t40\tD_title\tD_content\n"  # noqa: E501


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


class TestTemplateCreateUnifiedAllTypes:
    """Cover template_create() every elif branch via the unified 'template create' command."""

    def test_color_strip(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_COLORSTRIP" in out.read_text()

    def test_branch(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "TREE_COLORS" in out.read_text()

    def test_simple_bar(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_SIMPLEBAR" in out.read_text()

    def test_multi_bar(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_MULTIBAR" in out.read_text()

    def test_heatmap(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_HEATMAP" in out.read_text()

    def test_symbols(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_SYMBOL" in out.read_text()

    def test_pie(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_PIECHART" in out.read_text()

    def test_boxplot(self, tmp_path):
        tsv = "id\tminimum\tq1\tmedian\tq3\tmaximum\nA\t1\t2\t3\t4\t5\nB\t2\t3\t4\t5\t6\n"
        tax = tmp_path / "bp.tsv"
        tax.write_text(tsv)
        tree = tmp_path / "bp.nwk"
        tree.write_text(SIMPLE_NEWICK)
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_BOXPLOT" in out.read_text()

    def test_gradient(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_connections(self, tmp_path):
        conn = tmp_path / "conn.json"
        conn.write_text('[["A", "B"], ["C", "D"]]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "connections",
                "--connections",
                str(conn),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_CONNECTION" in out.read_text()

    def test_labels(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "LABELS" in out.read_text() or "DATASET_LABEL" in out.read_text()

    def test_popup_info(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "POPUP_INFO" in out.read_text()

    def test_domains(self, tmp_path):
        data = tmp_path / "dom.json"
        data.write_text('[{"id": "A", "from": "10", "to": "50", "type": "domain", "color": "#ff0000"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "domains",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_DOMAINS" in out.read_text()

    def test_binary(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_BINARY" in out.read_text()

    def test_text(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_TEXT" in out.read_text()

    def test_external_shape(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_EXTERNALSHAPE" in out.read_text() or "EXTERNALSHAPE" in out.read_text()

    def test_tree_colors(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "TREE_COLORS" in out.read_text()

    def test_tree_colors_with_color_type(self, tmp_path, tree_file, taxonomy_file):
        """Cover non-clade color_type branches in template_tree_colors."""
        out = tmp_path / "out.txt"
        for ctype in ("label", "branch", "width", "range", "gradient"):
            out = tmp_path / f"out_{ctype}.txt"
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
                    str(out),
                    "--color-type",
                    ctype,
                ],
            )
            assert result.exit_code == 0, result.output
            assert "TREE_COLORS" in out.read_text()

    def test_branch_gradient(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_branch_gradient_mid_color(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
                "--use-mid-color",
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_collapse(self, tmp_path):
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "collapse",
                "--node-ids",
                "A,B",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "COLLAPSE" in out.read_text()

    def test_prune(self, tmp_path):
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "prune",
                "--node-ids",
                "A,B",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "PRUNE" in out.read_text()

    def test_spacing(self, tmp_path):
        data = tmp_path / "sp.json"
        data.write_text('[{"id": "A", "spacing": "10"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "spacing",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_ranges(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_RANGE" in out.read_text()

    def test_highlight(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_STYLE" in out.read_text()

    def test_style(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_STYLE" in out.read_text()

    def test_style_branch(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
                "--style-type",
                "branch",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_STYLE" in out.read_text()

    def test_style_label(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
                "--style-type",
                "label",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_STYLE" in out.read_text()

    def test_style_label_background(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
                "--style-type",
                "label_background",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_STYLE" in out.read_text()

    def test_arrow(self, tmp_path):
        data = tmp_path / "arr.json"
        data.write_text('[{"id": "A", "to": "B", "color": "#ff0000"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "arrow",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_linechart(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
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
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_image(self, tmp_path, tree_file, taxonomy_file):
        tsv = "id\tKingdom\timg\turl\nA\tBacteria\ticon.png\thttp://a\nB\tBacteria\ticon.png\thttp://b\n"
        tax = tmp_path / "img.tsv"
        tax.write_text(tsv)
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
                "--column",
                "img",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_IMAGE" in out.read_text()

    def test_alignment(self, tmp_path, tree_file, taxonomy_file):
        tsv = "id\tKingdom\tseq\nA\tBacteria\tATGC\nB\tBacteria\tCGTA\n"
        tax = tmp_path / "aln.tsv"
        tax.write_text(tsv)
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
                "--column",
                "seq",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_ALIGNMENT" in out.read_text()

    def test_tanglegram(self, tmp_path):
        conn = tmp_path / "conn.json"
        conn.write_text('[["A", "B"], ["C", "D"]]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "tanglegram",
                "--connections",
                str(conn),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "DATASET_TANGLEGRAM" in out.read_text() or "TANGLEGRAM" in out.read_text()

    def test_placement(self, tmp_path):
        data = tmp_path / "pl.json"
        data.write_text('[{"id": "A", "x": "10", "y": "20"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "placement",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_timescale(self, tmp_path):
        data = tmp_path / "ts.json"
        data.write_text('[{"id": "A", "time": "10"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "timescale",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_meme(self, tmp_path):
        data = tmp_path / "meme.json"
        data.write_text('[{"id": "A", "motif": "ACGT"}]')
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "meme",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_manual(self, tmp_path):
        data = tmp_path / "man.txt"
        data.write_text("MANUAL\nA\t1\n")
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "manual",
                "--data-file",
                str(data),
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.read_text()

    def test_unknown_type(self, tmp_path):
        out = tmp_path / "out.txt"
        result = runner.invoke(
            app,
            [
                "template",
                "create",
                "unknown-type",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 1
        assert "未知模板类型" in result.output
