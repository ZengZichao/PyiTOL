"""QA3 item-3 boundary & exception tests for the templates module.

Covers (per code-review 2.5 / phase-3 item 13b):
  * single-column datasets (COLLAPSE/PRUNE) never silently drop data
    (regression lock for the Phase-1 fix);
  * under-filled data rows emit a warning instead of being dropped silently;
  * pie ``FIELD_COLORS`` aligns 1:1 with ``FIELD_LABELS`` even when
    ``position``/``radius`` are passed as value columns (the pie color bug);
  * illegal column combinations raise the domain ``InvalidColumnError``.
"""

import logging

import pytest

from pyitol.exceptions import InvalidColumnError
from pyitol.templates.generator import (
    generate_color_strip_template,
    generate_pie_template,
    generate_template,
)
from pyitol.templates.learner import learn_template
from pyitol.templates.schemas.base import create_schema

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


class TestSingleColumnNoDataLoss:
    """Regression lock for the Phase-1 single-column data-loss fix."""

    def test_collapse_preserves_all_node_ids(self, tmp_path):
        schema = create_schema("collapse", label="col", separator="TAB")
        schema.columns = ["id"]
        schema.data_rows = [{"id": n} for n in ["A", "B", "C", "D", "E"]]
        out = tmp_path / "c.txt"
        generate_template(out, [schema])
        ds = learn_template(str(out))["datasets"][0]
        assert ds["type"] == "dataset_collapse"
        assert [r["id"] for r in ds["data"]] == ["A", "B", "C", "D", "E"]

    def test_prune_preserves_all_node_ids(self, tmp_path):
        schema = create_schema("prune", label="pr", separator="TAB")
        schema.columns = ["id"]
        schema.data_rows = [{"id": "N1"}, {"id": "N2"}, {"id": "N3"}]
        out = tmp_path / "p.txt"
        generate_template(out, [schema])
        ds = learn_template(str(out))["datasets"][0]
        assert ds["type"] == "dataset_prune"
        assert [r["id"] for r in ds["data"]] == ["N1", "N2", "N3"]


class TestUnderfilledRowWarns:
    """Learner must warn (not silently drop) rows shorter than inferred cols."""

    def test_short_row_warns_and_is_skipped(self, tmp_path, caplog):
        p = tmp_path / "u.txt"
        # First row is full (3 fields) -> infers 3 columns; second row is short.
        p.write_text("DATASET_COLORSTRIP\nSEPARATOR TAB\nDATA\nA\tg1\t#ff0000\nB\n")
        with caplog.at_level(logging.WARNING):
            result = learn_template(str(p))
        ds = result["datasets"][0]
        # The under-filled row is skipped; the full row survives.
        assert [r["id"] for r in ds["data"]] == ["A"]
        assert any("字段不足" in rec.message for rec in caplog.records)

    def test_full_rows_are_kept_without_warning(self, tmp_path, caplog):
        p = tmp_path / "f.txt"
        p.write_text("DATASET_COLORSTRIP\nSEPARATOR TAB\nDATA\nA\tg1\t#ff0000\nB\tg2\t#00ff00\n")
        with caplog.at_level(logging.WARNING):
            result = learn_template(str(p))
        ds = result["datasets"][0]
        assert [r["id"] for r in ds["data"]] == ["A", "B"]
        assert not any("字段不足" in rec.message for rec in caplog.records)


class TestPieColorAlignment:
    """FIELD_COLORS must align 1:1 with FIELD_LABELS (pie color bug fix)."""

    def test_position_radius_in_value_columns_filtered(self, tmp_path, tree_file):
        tsv = "id\tposition\tradius\tcount\tvalue\nA\t0.5\t10\t5\t3\nB\t-1\t20\t8\t2\n"
        tax = tmp_path / "pie.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(
            tmp_path / "pie.txt",
            str(tax),
            tree_file,
            ["position", "radius", "count", "value"],
        )
        content = path.read_text()
        labels, colors = None, None
        for line in content.splitlines():
            if line.startswith("FIELD_LABELS"):
                labels = line.split("\t", 1)[1].split("\t")
            elif line.startswith("FIELD_COLORS"):
                colors = line.split("\t", 1)[1].split("\t")
        # position/radius must be filtered out -> only count/value remain.
        assert labels == ["count", "value"]
        # Critical: FIELD_COLORS must have exactly as many entries as labels.
        # (Before the fix, colors were derived from the *unfiltered* value_columns
        # and thus carried an extra entry for position/radius -> misaligned.)
        assert len(colors) == len(labels) == 2
        assert all(c.startswith("#") for c in colors)

    def test_normal_value_columns_unchanged(self, tmp_path, tree_file):
        tsv = "id\tcount\tvalue\nA\t5\t3\nB\t8\t2\n"
        tax = tmp_path / "pie2.tsv"
        tax.write_text(tsv)
        path = generate_pie_template(tmp_path / "pie2.txt", str(tax), tree_file, ["count", "value"])
        content = path.read_text()
        labels = colors = None
        for line in content.splitlines():
            if line.startswith("FIELD_LABELS"):
                labels = line.split("\t", 1)[1].split("\t")
            elif line.startswith("FIELD_COLORS"):
                colors = line.split("\t", 1)[1].split("\t")
        assert labels == ["count", "value"]
        assert len(colors) == len(labels)


class TestIllegalColumnRaisesDomainError:
    """Illegal column combinations raise the domain InvalidColumnError (Phase 2)."""

    def test_missing_column_raises_invalid_column_error(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        with pytest.raises(InvalidColumnError):
            generate_color_strip_template(str(out), taxonomy_file, tree_file, column="NO_SUCH_COLUMN")
