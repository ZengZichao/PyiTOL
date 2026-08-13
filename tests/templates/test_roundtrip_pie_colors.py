"""Independent QA final verification — Phase-3 item 2.

Item 2 added templates test coverage and fixed a pie color-alignment bug in
``generator.generate_pie_template``: ``value_columns`` are now filtered
(position/radius removed) *before* ``FIELD_COLORS`` are derived, so
``FIELD_COLORS`` aligns 1:1 with the filtered ``FIELD_LABELS``.

Independently verifies (own generators + own scenarios, no reliance on the
engineer's test files):
  * generate -> learn round-trip restores type/columns for color_strip/collapse/prune
  * pie FIELD_COLORS is 1:1 with the filtered value columns (bug fix effective)
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from pyitol.templates.generator import (
    generate_collapse_template,
    generate_color_strip_template,
    generate_pie_template,
    generate_prune_template,
)
from pyitol.templates.learner import learn_template

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tGroup\tValue\nA\tG1\t10\nB\tG1\t20\nC\tG2\t30\nD\tG2\t40\n"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "t.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "tax.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


class TestRoundTrip:
    def test_color_strip(self, tmp_path, tree_file, taxonomy_file):
        out = generate_color_strip_template(tmp_path / "cs.txt", taxonomy_file, tree_file, column="Group")
        ds = learn_template(str(out))["datasets"][0]
        assert ds["type"] == "dataset_colorstrip"
        # Learner restores columns as (id, value, color) for color_strip.
        assert ds["columns"] == ["id", "value", "color"]
        assert {r["id"] for r in ds["data"]} == {"A", "B", "C", "D"}

    def test_collapse(self, tmp_path):
        out = generate_collapse_template(tmp_path / "c.txt", ["X", "Y", "Z"])
        ds = learn_template(str(out))["datasets"][0]
        assert ds["type"] == "dataset_collapse"
        assert ds["columns"] == ["id"]
        assert [r["id"] for r in ds["data"]] == ["X", "Y", "Z"]

    def test_prune(self, tmp_path):
        out = generate_prune_template(tmp_path / "p.txt", ["P1", "P2"])
        ds = learn_template(str(out))["datasets"][0]
        assert ds["type"] == "dataset_prune"
        assert ds["columns"] == ["id"]
        assert [r["id"] for r in ds["data"]] == ["P1", "P2"]


class TestPieColorAlignment:
    HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

    def _parse(self, content: str):
        labels = colors = None
        for line in content.splitlines():
            if line.startswith("FIELD_LABELS"):
                labels = line.split("\t", 1)[1].split("\t")
            elif line.startswith("FIELD_COLORS"):
                colors = line.split("\t", 1)[1].split("\t")
        return labels, colors

    def test_position_radius_filtered_alignment(self, tmp_path, tree_file):
        tsv = "id\tposition\tradius\tcount\tvalue\nA\t0.5\t10\t5\t3\nB\t-1\t20\t8\t2\n"
        tax = tmp_path / "pie.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(
            tmp_path / "pie.txt",
            str(tax),
            tree_file,
            ["position", "radius", "count", "value"],
        )
        labels, colors = self._parse(Path(path).read_text())
        # position/radius must be filtered out -> only count/value remain.
        assert labels == ["count", "value"], labels
        # Critical alignment invariant: FIELD_COLORS 1:1 with FIELD_LABELS.
        assert len(colors) == len(labels) == 2, (colors, labels)
        assert all(self.HEX_RE.match(c) for c in colors), colors

    def test_normal_value_columns_alignment(self, tmp_path, tree_file):
        tsv = "id\tcount\tvalue\nA\t5\t3\nB\t8\t2\n"
        tax = tmp_path / "pie2.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(tmp_path / "pie2.txt", str(tax), tree_file, ["count", "value"])
        labels, colors = self._parse(Path(path).read_text())
        assert labels == ["count", "value"]
        assert len(colors) == len(labels)
        assert all(self.HEX_RE.match(c) for c in colors)
