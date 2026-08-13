"""Tests for PyiTOL template generator module."""

import pytest

from pyitol.exceptions import InvalidColumnError, TemplateError
from pyitol.templates.generator import (
    TemplateGenerator,
    generate_alignment_template,
    generate_arrow_template,
    generate_binary_template,
    generate_boxplot_template,
    generate_branch_template,
    generate_collapse_template,
    generate_color_strip_template,
    generate_connection_template,
    generate_domain_template,
    generate_external_shape_template,
    generate_gradient_template,
    generate_heatmap_template,
    generate_image_template,
    generate_labels_template,
    generate_linechart_template,
    generate_manual_template,
    generate_meme_template,
    generate_multibar_template,
    generate_pie_template,
    generate_placement_template,
    generate_popup_info_template,
    generate_prune_template,
    generate_ranges_template,
    generate_simple_bar_template,
    generate_spacing_template,
    generate_style_template,
    generate_symbols_template,
    generate_tanglegram_template,
    generate_template,
    generate_text_template,
    generate_timescale_template,
    generate_tree_colors_template,
)
from pyitol.templates.schemas.base import REQUIRED_COLUMNS, SCHEMA_MAP, LegendConfig, create_schema

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tPhylum\tcount\tvalue\nA\tBacteria\tProteobacteria\t10\t0.5\nB\tBacteria\tProteobacteria\t20\t0.8\nC\tArchaea\tEuryarchaeota\t15\t0.3\nD\tArchaea\tEuryarchaeota\t25\t0.6\n"  # noqa: E501


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


class TestSchemaCreation:
    def test_all_schemas_exist(self):
        for name in SCHEMA_MAP:
            schema = create_schema(name)
            assert schema is not None

    def test_required_columns_present(self):
        for _type_name, req_cols in REQUIRED_COLUMNS.items():
            assert len(req_cols) > 0


class TestTemplateGenerator:
    def test_write_basic(self, tmp_path):
        gen = TemplateGenerator()
        schema = create_schema("simple_bar", label="test")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        gen.add_schema(schema)
        path = gen.write(tmp_path / "test.txt")
        assert path.exists()
        content = path.read_text()
        assert "DATASET_SIMPLEBAR" in content
        assert "SEPARATOR TAB" in content


class TestGenerateFunctions:
    def test_color_strip(self, tmp_path, tree_file, taxonomy_file):
        path = generate_color_strip_template(tmp_path / "cs.txt", taxonomy_file, tree_file, "Kingdom")
        assert path.exists()
        assert "DATASET_COLORSTRIP" in path.read_text()

    def test_simple_bar(self, tmp_path, tree_file, taxonomy_file):
        path = generate_simple_bar_template(tmp_path / "sb.txt", taxonomy_file, tree_file, "count")
        assert path.exists()
        assert "DATASET_SIMPLEBAR" in path.read_text()

    def test_heatmap(self, tmp_path, tree_file, taxonomy_file):
        path = generate_heatmap_template(tmp_path / "hm.txt", taxonomy_file, tree_file, ["count", "value"])
        assert path.exists()
        assert "DATASET_HEATMAP" in path.read_text()

    def test_symbols(self, tmp_path, tree_file, taxonomy_file):
        path = generate_symbols_template(tmp_path / "sy.txt", taxonomy_file, tree_file, "Kingdom")
        assert path.exists()
        assert "DATASET_SYMBOL" in path.read_text()

    def test_pie(self, tmp_path, tree_file, taxonomy_file):
        path = generate_pie_template(tmp_path / "pie.txt", taxonomy_file, tree_file, ["count", "value"])
        assert path.exists()
        assert "DATASET_PIECHART" in path.read_text()

    def test_multibar(self, tmp_path, tree_file, taxonomy_file):
        path = generate_multibar_template(tmp_path / "mb.txt", taxonomy_file, tree_file, ["count", "value"])
        assert path.exists()
        assert "DATASET_MULTIBAR" in path.read_text()

    def test_boxplot(self, tmp_path):
        # Use a simple taxonomy with boxplot columns
        tsv = "id\tminimum\tq1\tmedian\tq3\tmaximum\nA\t1\t2\t3\t4\t5\nB\t2\t3\t4\t5\t6\nC\t1\t2\t3\t4\t5\nD\t2\t3\t4\t5\t6\n"  # noqa: E501
        tax_path = tmp_path / "bp.tsv"
        tax_path.write_text(tsv)
        tree_path = tmp_path / "bp.nwk"
        tree_path.write_text(SIMPLE_NEWICK)
        path = generate_boxplot_template(tmp_path / "bp.txt", str(tax_path), str(tree_path))
        assert path.exists()

    def test_gradient(self, tmp_path, tree_file, taxonomy_file):
        path = generate_gradient_template(tmp_path / "gr.txt", taxonomy_file, tree_file, "value")
        assert path.exists()

    def test_connections(self, tmp_path):
        path = generate_connection_template(tmp_path / "conn.txt", [("A", "B"), ("C", "D")])
        assert path.exists()
        assert "DATASET_CONNECTION" in path.read_text()

    def test_collapse(self, tmp_path):
        path = generate_collapse_template(tmp_path / "col.txt", ["A", "B"])
        assert path.exists()
        assert "COLLAPSE" in path.read_text()

    def test_prune(self, tmp_path):
        path = generate_prune_template(tmp_path / "pr.txt", ["A"])
        assert path.exists()
        assert "PRUNE" in path.read_text()

    def test_spacing(self, tmp_path):
        path = generate_spacing_template(tmp_path / "sp.txt", [{"id": "A", "factor": "2"}])
        assert path.exists()

    def test_labels(self, tmp_path):
        path = generate_labels_template(tmp_path / "lb.txt", [{"id": "A", "label": "Species_A"}])
        assert path.exists()

    def test_popup_info(self, tmp_path):
        path = generate_popup_info_template(tmp_path / "pi.txt", [{"id": "A", "title": "Info", "content": "Details"}])
        assert path.exists()

    def test_tree_colors(self, tmp_path):
        path = generate_tree_colors_template(
            tmp_path / "tc.txt", [{"id": "A", "type": "clade", "color": "#ff0000", "what": "all"}]
        )
        assert path.exists()

    def test_binary(self, tmp_path):
        path = generate_binary_template(tmp_path / "bi.txt", [{"id": "A", "col1": "1"}], ["col1"], ["#ff0000"], ["1"])
        assert path.exists()

    def test_domain(self, tmp_path):
        path = generate_domain_template(
            tmp_path / "dom.txt", [{"id": "A", "from": "10", "to": "50", "type": "domain", "color": "#ff00aa"}]
        )
        assert path.exists()

    def test_text(self, tmp_path):
        tsv = "id\tlabel\nA\tHello\nB\tWorld\nC\tTest\nD\tData\n"
        tax_path = tmp_path / "tx.tsv"
        tax_path.write_text(tsv)
        tree_path = tmp_path / "tx.nwk"
        tree_path.write_text(SIMPLE_NEWICK)
        path = generate_text_template(tmp_path / "tx.txt", str(tax_path), str(tree_path), "label")
        assert path.exists()

    def test_external_shape(self, tmp_path, tree_file, taxonomy_file):
        path = generate_external_shape_template(tmp_path / "es.txt", taxonomy_file, tree_file, "Kingdom")
        assert path.exists()

    def test_ranges(self, tmp_path):
        path = generate_ranges_template(tmp_path / "rg.txt", [{"id": "A", "label": "Group1", "color": "#ff0000"}])
        assert path.exists()

    def test_tanglegram(self, tmp_path):
        path = generate_tanglegram_template(tmp_path / "tg.txt", [("A", "C"), ("B", "D")])
        assert path.exists()

    def test_placement(self, tmp_path):
        path = generate_placement_template(
            tmp_path / "pl.txt", [{"id": "A", "position": "100", "count": "5", "color": "#ff0000"}]
        )
        assert path.exists()

    def test_timescale(self, tmp_path):
        path = generate_timescale_template(
            tmp_path / "ts.txt", [{"time_point": "0", "label": "Present", "color": "#000000"}]
        )
        assert path.exists()

    def test_meme(self, tmp_path):
        path = generate_meme_template(
            tmp_path / "mm.txt", [{"id": "A", "start": "10", "end": "20", "name": "motif1", "color": "#ff0000"}]
        )
        assert path.exists()

    def test_arrow(self, tmp_path):
        path = generate_arrow_template(
            tmp_path / "ar.txt", [{"id": "A", "position": "100", "direction": "right", "color": "#ff0000"}]
        )
        assert path.exists()

    def test_linechart(self, tmp_path):
        path = generate_linechart_template(tmp_path / "lc.txt", [{"id": "A", "position": "100", "value": "0.5"}])
        assert path.exists()

    def test_image(self, tmp_path):
        path = generate_image_template(
            tmp_path / "img.txt", [{"id": "A", "image_file": "img.png", "image_url": "http://example.com/img.png"}]
        )
        assert path.exists()

    def test_alignment(self, tmp_path):
        path = generate_alignment_template(tmp_path / "al.txt", [{"id": "A", "alignment": "ATCG"}])
        assert path.exists()

    def test_style_template(self, tmp_path):
        path = generate_style_template(
            tmp_path / "st.txt",
            [{"id": "A", "type": "label_background", "color": "#ff0000"}],
            label="highlight",
        )
        assert path.exists()
        content = path.read_text()
        assert "DATASET_STYLE" in content
        assert "label_background" in content

    def test_style_branch(self, tmp_path):
        path = generate_style_template(
            tmp_path / "st2.txt",
            [{"id": "A", "type": "branch", "color": "#00ff00", "style": "normal"}],
        )
        assert path.exists()
        content = path.read_text()
        assert "DATASET_STYLE" in content
        assert "branch" in content

    def test_branch_template(self, tmp_path, tree_file, taxonomy_file):
        path = generate_branch_template(
            tmp_path / "br.txt",
            taxonomy_file,
            tree_file,
            "Kingdom",
        )
        assert path.exists()
        content = path.read_text()
        assert "TREE_COLORS" in content or "branch" in content

    def test_manual_template(self, tmp_path):
        path = generate_manual_template(
            tmp_path / "mn.txt",
            [{"id": "A", "label": "manual data"}],
        )
        assert path.exists()
        content = path.read_text()
        assert "DATASET_MANUAL" in content

    def test_write_multiple(self, tmp_path):
        gen = TemplateGenerator()
        s1 = create_schema("simple_bar", label="bar1")
        s1.columns = ["id", "bar_height"]
        s1.data_rows = [{"id": "A", "bar_height": "10"}]
        s2 = create_schema("color_strip", label="strip1")
        s2.columns = ["id", "value", "color"]
        s2.data_rows = [{"id": "A", "value": "X", "color": "#ff0000"}]
        gen.add_schema(s1)
        gen.add_schema(s2)
        paths = gen.write_multiple(tmp_path, prefix="test_")
        assert len(paths) == 2
        for p in paths:
            assert p.exists()


class TestTemplateGeneratorExtended:
    def test_add_schema_from_data(self, tmp_path):
        gen = TemplateGenerator()
        gen.add_schema_from_data("simple_bar", "bar", [{"id": "A", "bar_height": "10"}], parameters={"WIDTH": "50"})
        path = gen.write(tmp_path / "test.txt")
        content = path.read_text()
        assert "DATASET_SIMPLEBAR" in content
        assert "WIDTH\t50" in content

    def test_set_style_and_name(self, tmp_path):
        gen = TemplateGenerator()
        schema = create_schema("simple_bar", label="bar")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        gen.add_schema(schema)
        gen.set_style({"treeType": "normal"})
        gen.set_name("my_template")
        path = gen.write(tmp_path / "test.txt")
        content = path.read_text()
        assert "DATASET_TREESTYLE" in content
        assert "treeType\tnormal" in content

    def test_legend_output(self, tmp_path):
        gen = TemplateGenerator()
        schema = create_schema("simple_bar", label="bar")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        schema.legend = LegendConfig(title="Legend", colors=["#ff0000"])
        gen.add_schema(schema)
        path = gen.write(tmp_path / "test.txt")
        content = path.read_text()
        assert "LEGEND_TITLE" in content
        assert "LEGEND_COLORS" in content

    def test_write_append_mode(self, tmp_path):
        gen = TemplateGenerator()
        schema = create_schema("simple_bar", label="bar")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        gen.add_schema(schema)
        path = gen.write(tmp_path / "test.txt")

        gen2 = TemplateGenerator()
        schema2 = create_schema("color_strip", label="strip")
        schema2.columns = ["id", "value", "color"]
        schema2.data_rows = [{"id": "B", "value": "X", "color": "#00ff00"}]
        gen2.add_schema(schema2)
        path2 = gen2.write(path, mode="append")
        content = path2.read_text()
        assert content.count("DATASET_SIMPLEBAR") == 1
        assert content.count("DATASET_COLORSTRIP") == 1

    def test_write_append_mode_file_not_exists(self, tmp_path):
        gen = TemplateGenerator()
        schema = create_schema("simple_bar", label="bar")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        gen.add_schema(schema)
        path = tmp_path / "nonexistent" / "test.txt"
        result = gen.write(path, mode="append")
        assert result.exists()


class TestGenerateTemplate:
    def test_convenience_function(self, tmp_path):
        s1 = create_schema("simple_bar", label="bar1")
        s1.columns = ["id", "bar_height"]
        s1.data_rows = [{"id": "A", "bar_height": "10"}]
        path = generate_template(
            tmp_path / "out.txt",
            [s1],
            style_params={"treeType": "normal"},
            template_name="test",
        )
        assert path.exists()
        content = path.read_text()
        assert "DATASET_SIMPLEBAR" in content
        assert "DATASET_TREESTYLE" in content


class TestGenerateFunctionsExtended:
    def test_color_strip_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_color_strip_template(tmp_path / "cs.txt", taxonomy_file, tree_file, "Missing")

    def test_color_strip_na_value(self, tmp_path, tree_file):
        tsv = "id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n"
        tax = tmp_path / "tax_na.tsv"
        tax.write_text(tsv)
        path = generate_color_strip_template(tmp_path / "cs.txt", str(tax), tree_file, "Kingdom")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]

    def test_manual_empty_data_with_custom_header(self, tmp_path):
        path = generate_manual_template(tmp_path / "mn.txt", [], custom_header={"CUSTOM": "val"})
        content = path.read_text()
        assert "DATASET_MANUAL" in content
        assert "CUSTOM\tval" in content

    def test_simple_bar_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_simple_bar_template(tmp_path / "sb.txt", taxonomy_file, tree_file, "Missing")

    def test_simple_bar_non_numeric_and_na(self, tmp_path, tree_file):
        tsv = "id\tcount\nA\t10\nB\tabc\nC\t\nD\t20\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_simple_bar_template(tmp_path / "sb.txt", str(tax), tree_file, "count")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]
        assert "C\t" not in [line[:2] for line in content.splitlines() if line.startswith("C\t")]

    def test_branch_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_branch_template(tmp_path / "br.txt", taxonomy_file, tree_file, "Missing")

    def test_branch_na_value(self, tmp_path, tree_file):
        tsv = "id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_branch_template(tmp_path / "br.txt", str(tax), tree_file, "Kingdom")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]

    def test_symbols_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_symbols_template(tmp_path / "sy.txt", taxonomy_file, tree_file, "Missing")

    def test_symbols_invalid_type(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(TemplateError, match="无效的符号类型"):
            generate_symbols_template(tmp_path / "sy.txt", taxonomy_file, tree_file, "Kingdom", symbol_type="invalid")

    def test_symbols_na_value(self, tmp_path, tree_file):
        tsv = "id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_symbols_template(tmp_path / "sy.txt", str(tax), tree_file, "Kingdom")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]

    def test_heatmap_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_heatmap_template(tmp_path / "hm.txt", taxonomy_file, tree_file, ["Missing"])

    def test_heatmap_short_gradient_and_column_labels(self, tmp_path, tree_file, taxonomy_file):
        path = generate_heatmap_template(
            tmp_path / "hm.txt",
            taxonomy_file,
            tree_file,
            ["count"],
            color_gradient=["#ff0000", "#0000ff"],
            column_labels={"count": "Count"},
        )
        content = path.read_text()
        assert "USE_MID_COLOR" not in content
        assert "COLOR_MAX\t#0000ff" in content
        assert "COLUMN_LABEL:count\tCount" in content

    def test_boxplot_missing_column(self, tmp_path, tree_file):
        tsv = "id\tminimum\tq1\tmedian\tq3\tmaximum\nA\t1\t2\t3\t4\t5\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_boxplot_template(tmp_path / "bp.txt", str(tax), tree_file, min_column="Missing")

    def test_boxplot_extremes(self, tmp_path, tree_file):
        tsv = "id\tminimum\tq1\tmedian\tq3\tmaximum\te1\te2\nA\t1\t2\t3\t4\t5\t0\t10\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_boxplot_template(tmp_path / "bp.txt", str(tax), tree_file, extremes_columns=["e1", "e2"])
        content = path.read_text()
        # The extreme values should appear in the data row, not the column names
        assert "0\t10" in content

    def test_domain_with_scale(self, tmp_path):
        path = generate_domain_template(
            tmp_path / "dom.txt",
            [{"id": "A", "from": "10", "to": "50", "type": "domain", "color": "#ff00aa"}],
            scale="1-100",
        )
        content = path.read_text()
        assert "DATASET_SCALE\t1-100" in content

    def test_gradient_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_gradient_template(tmp_path / "gr.txt", taxonomy_file, tree_file, "Missing")

    def test_gradient_na_value(self, tmp_path, tree_file):
        tsv = "id\tvalue\nA\t1.0\nB\t\nC\t2.0\nD\t3.0\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_gradient_template(tmp_path / "gr.txt", str(tax), tree_file, "value")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]

    def test_gradient_use_mid_color(self, tmp_path, tree_file, taxonomy_file):
        path = generate_gradient_template(
            tmp_path / "gr.txt",
            taxonomy_file,
            tree_file,
            "value",
            use_mid_color=True,
            color_mid="#ffff00",
        )
        content = path.read_text()
        assert "USE_MID_COLOR\t1" in content
        assert "COLOR_MID\t#ffff00" in content

    def test_external_shape_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_external_shape_template(tmp_path / "es.txt", taxonomy_file, tree_file, "Missing")

    def test_external_shape_na_value(self, tmp_path, tree_file):
        tsv = "id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_external_shape_template(tmp_path / "es.txt", str(tax), tree_file, "Kingdom")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]

    def test_text_missing_column(self, tmp_path, tree_file, taxonomy_file):
        with pytest.raises(InvalidColumnError, match="Column 'Missing' not found"):
            generate_text_template(tmp_path / "tx.txt", taxonomy_file, tree_file, "Missing")

    def test_text_na_and_empty(self, tmp_path, tree_file):
        tsv = "id\tlabel\nA\tHello\nB\t\nC\t  \nD\tData\n"
        tax = tmp_path / "tax.tsv"
        tax.write_text(tsv)
        path = generate_text_template(tmp_path / "tx.txt", str(tax), tree_file, "label")
        content = path.read_text()
        assert "B\t" not in [line[:2] for line in content.splitlines() if line.startswith("B\t")]
        assert "C\t" not in [line[:2] for line in content.splitlines() if line.startswith("C\t")]

    def test_style_empty_data(self, tmp_path):
        path = generate_style_template(tmp_path / "st.txt", [])
        content = path.read_text()
        assert "DATASET_STYLE" in content
        assert "DATA" in content

    def test_pie_official_format(self, tmp_path, tree_file):
        """Pie chart rows must follow id\tposition\tradius\tvalue1\tvalue2..."""
        tsv = "id\tposition\tradius\tcount\tvalue\nA\t0.5\t10\t5\t3\nB\t-1\t20\t8\t2\nC\t1\t15\t6\t4\nD\t0\t5\t7\t1\n"
        tax = tmp_path / "pie.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(tmp_path / "pie.txt", str(tax), tree_file, ["count", "value"])
        content = path.read_text()
        assert "DATASET_PIECHART" in content
        assert "FIELD_COLORS" in content
        data_lines = [line for line in content.splitlines() if line.startswith("A\t") or line.startswith("B\t")]
        assert any("A\t0.5\t10\t5\t3" in line for line in data_lines)
        assert any("B\t-1\t20\t8\t2" in line for line in data_lines)
        assert "color_1" not in content

    def test_pie_backward_compat_defaults(self, tmp_path, tree_file):
        """Old-style DataFrames without position/radius columns get sensible defaults."""
        tsv = "id\tcount\tvalue\nA\t5\t3\nB\t8\t2\nC\t6\t4\nD\t7\t1\n"
        tax = tmp_path / "pie_old.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(tmp_path / "pie_old.txt", str(tax), tree_file, ["count", "value"])
        content = path.read_text()
        data_lines = [line for line in content.splitlines() if line.startswith("A\t")]
        assert any("A\t0\t1\t5\t3" in line for line in data_lines)

    def test_common_visual_params(self, tmp_path, tree_file, taxonomy_file):
        path = generate_simple_bar_template(
            tmp_path / "sb.txt",
            taxonomy_file,
            tree_file,
            "count",
            margin="5",
            height_factor="2",
            show_internal="1",
            border_width="1",
            border_color="#00ff00",
            dataset_scale=["10", "20"],
        )
        content = path.read_text()
        assert "MARGIN\t5" in content
        assert "HEIGHT_FACTOR\t2" in content
        assert "SHOW_INTERNAL\t1" in content
        assert "BORDER_WIDTH\t1" in content
        assert "BORDER_COLOR\t#00ff00" in content
        assert "DATASET_SCALE\t10\t20" in content

    def test_heatmap_type_specific_params(self, tmp_path, tree_file, taxonomy_file):
        path = generate_heatmap_template(
            tmp_path / "hm.txt",
            taxonomy_file,
            tree_file,
            ["count", "value"],
            field_tree="(count,value);",
            show_tree="1",
            color_nan="#ffffff",
            normalization="rows",
            display_values="1",
            value_size="12",
        )
        content = path.read_text()
        assert "FIELD_TREE\t(count,value);" in content
        assert "SHOW_TREE\t1" in content
        assert "COLOR_NAN\t#ffffff" in content
        assert "NORMALIZATION\trows" in content
        assert "DISPLAY_VALUES\t1" in content
        assert "VALUE_SIZE\t12" in content

    def test_color_strip_type_specific_params(self, tmp_path, tree_file):
        tsv = "id\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n"
        tax = tmp_path / "cs.tsv"
        tax.write_text(tsv)
        path = generate_color_strip_template(
            tmp_path / "cs.txt",
            str(tax),
            tree_file,
            "Kingdom",
            color_branches="1",
            complete_border="1",
            show_strip_labels="1",
            strip_label_position="1",
            strip_label_color="#ffffff",
            strip_label_size="12",
        )
        content = path.read_text()
        assert "COLOR_BRANCHES\t1" in content
        assert "COMPLETE_BORDER\t1" in content
        assert "SHOW_STRIP_LABELS\t1" in content
        assert "STRIP_LABEL_POSITION\t1" in content
        assert "STRIP_LABEL_COLOR\t#ffffff" in content
        assert "STRIP_LABEL_SIZE\t12" in content

    def test_domain_official_format(self, tmp_path):
        path = generate_domain_template(
            tmp_path / "dom.txt",
            [{"id": "A", "domain": "RE|10|50|#ff0000|domain1"}],
            shape_scale="2",
        )
        content = path.read_text()
        assert "DATASET_DOMAINS" in content
        data_lines = [line for line in content.splitlines() if line.startswith("A\t")]
        assert any("RE|10|50|#ff0000|domain1" in line for line in data_lines)
        assert "SHAPE_SCALE\t2" in content

    def test_arrow_width_param(self, tmp_path):
        path = generate_arrow_template(
            tmp_path / "ar.txt",
            [{"id": "A", "position": "100", "direction": "right", "color": "#ff0000"}],
            arrow_width="3",
        )
        content = path.read_text()
        assert "ARROW_WIDTH\t3" in content

    def test_tanglegram_second_tree(self, tmp_path):
        path = generate_tanglegram_template(
            tmp_path / "tg.txt",
            [("A", "C"), ("B", "D")],
            second_tree="(A,B);",
        )
        content = path.read_text()
        assert "TANGLEGRAM_TREE" in content
        assert "(A,B);" in content
        assert "END_TANGLEGRAM_TREE" in content


class TestFormatContractFixes:
    """Lock the iTOL v7 format-contract fixes (H2 / H3 / M3 / M7)."""

    def test_color_strip_column_order(self, tmp_path, tree_file, taxonomy_file):
        # iTOL DATASET_COLORSTRIP data rows: `ID <sep> COLOR <sep> LABEL`
        path = generate_color_strip_template(
            tmp_path / "cs.txt",
            taxonomy_file,
            tree_file,
            "Kingdom",
        )
        content = path.read_text()
        data_lines = [ln for ln in content.splitlines() if ln.startswith("A\t")]
        assert data_lines, "缺少 A 的数据行"
        parts = data_lines[0].split("\t")
        assert parts[0] == "A"
        assert parts[1].startswith("#")  # 颜色 hex 在第二列
        assert parts[2] == "Bacteria"  # 分类名(label) 在最后一列

    def test_symbols_numeric_type(self, tmp_path, tree_file, taxonomy_file):
        # DATASET_SYMBOL 的 type 必须为数字编码（diamond -> 1）
        path = generate_symbols_template(
            tmp_path / "sy.txt",
            taxonomy_file,
            tree_file,
            "Kingdom",
            symbol_type="diamond",
        )
        content = path.read_text()
        data_lines = [ln for ln in content.splitlines() if ln.startswith("A\t")]
        assert data_lines
        parts = data_lines[0].split("\t")
        # 列序: id, type, value, color, label
        assert parts[0] == "A"
        assert parts[1] == "1"  # diamond -> square(1)
        assert parts[2] == "30"  # 默认 size
        assert parts[3].startswith("#")
        assert parts[4] == "Bacteria"

    def test_connection_numeric_type_straight(self, tmp_path):
        # DATASET_CONNECTION 第5列 type 必须为数字编码（straight -> 1）
        path = generate_connection_template(
            tmp_path / "conn.txt",
            [("A", "B"), ("C", "D")],
            line_type="straight",
        )
        content = path.read_text()
        data_lines = [ln for ln in content.splitlines() if ln.startswith("A\t")]
        assert data_lines
        parts = data_lines[0].split("\t")
        # 列序: id1, id2, color, width, type
        assert parts[4] == "1"

    def test_connection_numeric_type_solid(self, tmp_path):
        # 默认 solid -> 曲线(0)
        path = generate_connection_template(
            tmp_path / "conn.txt",
            [("A", "B")],
            line_type="solid",
        )
        content = path.read_text()
        data_lines = [ln for ln in content.splitlines() if ln.startswith("A\t")]
        assert data_lines[0].split("\t")[4] == "0"

    def test_external_shape_columns_and_numeric(self, tmp_path, tree_file, taxonomy_file):
        # 单形状 externalshape 列名应为 id,type,value,color,label 且 type 为数字
        from pyitol.templates.learner import learn_template

        path = generate_external_shape_template(
            tmp_path / "es.txt",
            taxonomy_file,
            tree_file,
            "Kingdom",
            shape_type="circle",
        )
        content = path.read_text()
        data_lines = [ln for ln in content.splitlines() if ln.startswith("A\t")]
        assert data_lines
        parts = data_lines[0].split("\t")
        # 列序: id, type, value, color, label
        assert parts[0] == "A"
        assert parts[1] == "2"  # circle -> 2
        assert parts[3].startswith("#")
        assert parts[4] == "Bacteria"
        # 反向解析：列名应推断为语义名（M7）
        ds = learn_template(str(path))["datasets"][0]
        assert ds["columns"] == ["id", "type", "value", "color", "label"]
