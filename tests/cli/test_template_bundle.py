"""Tests for template bundle CLI command."""

import json

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_FULL = "id\tKingdom\tPhylum\tcount\tvalue\ttext\timage\talignment\ttitle\tcontent\tbinary_col\nA\tBacteria\tProteobacteria\t10\t0.5\ttext1\timg1.png\tATCG\tt1\tc1\t1\nB\tBacteria\tProteobacteria\t20\t0.8\ttext2\timg2.png\tATCG\tt2\tc2\t\nC\tArchaea\tEuryarchaeota\t15\t0.3\ttext3\timg3.png\tCGTA\tt3\tc3\t1\nD\tArchaea\tEuryarchaeota\t25\t0.6\ttext4\timg4.png\tCGTA\tt4\tc4\t1\n"  # noqa: E501


@pytest.fixture
def bundle_tree_file(tmp_path):
    p = tmp_path / "bundle.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def bundle_taxonomy_file(tmp_path):
    p = tmp_path / "bundle.tsv"
    p.write_text(TAXONOMY_FULL)
    return str(p)


class TestTemplateBundle:
    def test_bundle_all_types(self, tmp_path, bundle_tree_file, bundle_taxonomy_file):
        conn_csv = tmp_path / "conn.csv"
        conn_csv.write_text("id1\tid2\tcolor\twidth\ttype\nA\tB\t#ff0000\t2\tsolid\n")
        tanglegram_csv = tmp_path / "tanglegram.csv"
        tanglegram_csv.write_text("id1\tid2\tcolor\twidth\nA\tC\t#999999\t1\n")
        domains_csv = tmp_path / "domains.csv"
        domains_csv.write_text("id\tfrom\tto\ttype\tcolor\nA\t10\t50\tdomain\t#ff0000\n")
        arrows_csv = tmp_path / "arrows.csv"
        arrows_csv.write_text("id\tposition\tdirection\tcolor\nA\t100\tright\t#ff0000\n")
        placement_csv = tmp_path / "placement.csv"
        placement_csv.write_text("id\tposition\tcount\tcolor\nA\t100\t5\t#ff0000\n")
        timescale_csv = tmp_path / "timescale.csv"
        timescale_csv.write_text("time_point\tlabel\tcolor\n0\tPresent\t#000000\n")
        meme_csv = tmp_path / "meme.csv"
        meme_csv.write_text("id\tstart\tend\tname\tcolor\nA\t10\t20\tmotif1\t#ff0000\n")
        manual_csv = tmp_path / "manual.csv"
        manual_csv.write_text("id\tlabel\tvalue\nA\tmanual\t1\n")

        config = [
            {"type": "color-strip", "column": "Kingdom", "label": "cs"},
            {"type": "tree-colors", "column": "Kingdom", "label": "tc"},
            {"type": "branch-gradient", "column": "value", "label": "bg"},
            {"type": "symbols", "column": "Kingdom", "label": "sym"},
            {"type": "external-shape", "column": "Kingdom", "label": "es"},
            {"type": "highlight", "column": "Kingdom", "label": "hl"},
            {"type": "ranges", "column": "Kingdom", "label": "rng"},
            {"type": "labels", "column": "Kingdom", "label": "lbl"},
            {"type": "popup-info", "column": "Kingdom", "label": "pop"},
            {"type": "simple-bar", "column": "value", "label": "sb"},
            {"type": "multi-bar", "columns": ["count", "value"], "label": "mb"},
            {"type": "heatmap", "columns": ["count", "value"], "label": "hm"},
            {"type": "pie", "columns": ["count", "value"], "label": "pie"},
            {"type": "gradient", "column": "value", "label": "grad"},
            {"type": "text", "column": "text", "label": "txt"},
            {"type": "boxplot", "label": "bp"},
            {"type": "linechart", "column": "value", "label": "lc"},
            {"type": "image", "column": "image", "label": "img"},
            {"type": "alignment", "column": "alignment", "label": "al"},
            {"type": "binary", "columns": ["binary_col"], "label": "bin"},
            {"type": "collapse", "node_ids": ["A", "B"], "label": "col"},
            {"type": "prune", "node_ids": ["C"], "label": "prn"},
            {"type": "spacing", "node_ids": ["A", "B"], "factors": ["2.0", "1.5"], "label": "spc"},
            {"type": "style", "column": "Kingdom", "label": "sty"},
            {"type": "connections", "data_file": str(conn_csv), "label": "conn"},
            {"type": "tanglegram", "data_file": str(tanglegram_csv), "label": "tgl"},
            {"type": "domains", "data_file": str(domains_csv), "label": "dom"},
            {"type": "arrows", "data_file": str(arrows_csv), "label": "arr"},
            {"type": "placement", "data_file": str(placement_csv), "label": "pl"},
            {"type": "timescale", "data_file": str(timescale_csv), "label": "ts"},
            {"type": "meme", "data_file": str(meme_csv), "label": "meme"},
            {"type": "manual", "data_file": str(manual_csv), "label": "man"},
        ]

        output_dir = tmp_path / "bundle_out"
        output_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--output-dir",
                str(output_dir),
                "--taxonomy",
                bundle_taxonomy_file,
                "--tree",
                bundle_tree_file,
                "--config",
                json.dumps(config),
            ],
        )
        assert result.exit_code == 0, result.output
        files = list(output_dir.glob("*.txt"))
        assert len(files) == len(config)

    def test_bundle_branches(self, tmp_path, bundle_tree_file, bundle_taxonomy_file):
        config = [
            {
                "type": "branch-gradient",
                "column": "value",
                "use_mid_color": True,
                "color_mid": "#00ff00",
                "label": "bg2",
            },
            {"type": "heatmap", "columns": ["count"], "color_gradient": ["#ff0000", "#0000ff"], "label": "hm2"},
            {"type": "gradient", "column": "value", "use_mid_color": True, "label": "grad2"},
            {"type": "style", "column": "Kingdom", "style_type": "label", "label": "sty_label"},
            {"type": "style", "column": "Kingdom", "style_type": "label_background", "label": "sty_lb"},
            {"type": "connections", "data_file": "nonexistent.csv", "label": "conn_skip"},
            {"type": "unknown-type", "column": "Kingdom", "label": "unk"},
        ]

        output_dir = tmp_path / "bundle_out2"
        output_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--output-dir",
                str(output_dir),
                "--taxonomy",
                bundle_taxonomy_file,
                "--tree",
                bundle_tree_file,
                "--config",
                json.dumps(config),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "忽略未知类型" in result.output
        assert "需要提供 data_file" in result.output
        files = list(output_dir.glob("*.txt"))
        assert len(files) == 5

    def test_bundle_single_member_ranges(self, tmp_path):
        tree = tmp_path / "sm.nwk"
        tree.write_text("(A:0.1,B:0.2,C:0.3);")
        tax = tmp_path / "sm.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\n")
        config = [{"type": "ranges", "column": "Kingdom"}]

        output_dir = tmp_path / "bundle_out3"
        output_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--output-dir",
                str(output_dir),
                "--taxonomy",
                str(tax),
                "--tree",
                str(tree),
                "--config",
                json.dumps(config),
            ],
        )
        assert result.exit_code == 0, result.output
        files = list(output_dir.glob("*.txt"))
        assert len(files) == 1

    def test_bundle_heatmap_two_color_gradient(self, tmp_path, tree_file, taxonomy_file):
        out_dir = tmp_path / "bundle_hm"
        out_dir.mkdir()
        config = [
            {"type": "heatmap", "columns": ["Value"], "color_gradient": ["#ff0000", "#0000ff"]},
        ]
        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--output-dir",
                str(out_dir),
                "--taxonomy",
                taxonomy_file,
                "--tree",
                tree_file,
                "--config",
                json.dumps(config),
            ],
        )
        assert result.exit_code == 0, result.output
        assert "模板已生成" in result.output

    def test_bundle_nan_and_invalid(self, tmp_path, bundle_tree_file):
        tax = tmp_path / "bundle_nan.tsv"
        tax.write_text("id\tKingdom\tvalue\nA\tBacteria\t0.5\nB\t\tbad\nC\tArchaea\t0.3\nD\tArchaea\t0.6\n")
        config = [
            {"type": "branch-gradient", "column": "value", "label": "bg_nan"},
            {"type": "simple-bar", "column": "value", "label": "sb_nan"},
            {"type": "gradient", "column": "value", "label": "grad_nan"},
            {"type": "style", "column": "Kingdom", "label": "sty_nan"},
        ]

        output_dir = tmp_path / "bundle_out4"
        output_dir.mkdir()

        result = runner.invoke(
            app,
            [
                "template",
                "bundle",
                "--output-dir",
                str(output_dir),
                "--taxonomy",
                str(tax),
                "--tree",
                bundle_tree_file,
                "--config",
                json.dumps(config),
            ],
        )
        assert result.exit_code == 0, result.output
        files = list(output_dir.glob("*.txt"))
        assert len(files) == len(config)
