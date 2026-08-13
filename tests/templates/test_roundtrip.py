"""Round-trip tests: generate_template -> learn_template preserves key fields.

These tests lock the generator <-> learner contract for representative schema
types. They catch regressions such as the Phase-1 single-column data-loss bug
(COLLAPSE/PRUNE node IDs dropped) and any format misalignment, by writing a
template with :func:`generate_template` and reverse-parsing it with
:func:`learn_template`, then asserting that ``type`` / ``columns`` /
``parameters`` (and the data values) are faithfully restored.
"""

from pathlib import Path

from pyitol.templates.generator import generate_template
from pyitol.templates.learner import learn_template
from pyitol.templates.schemas.base import create_schema


def _write(schemas: list, tmp_path: Path, name: str = "t.txt") -> str:
    """Write one or more schemas to a template file and return its path."""
    out = tmp_path / name
    generate_template(out, schemas)
    return str(out)


def test_roundtrip_color_strip(tmp_path):
    schema = create_schema("color_strip", label="cs", separator="TAB")
    schema.columns = ["id", "value", "color"]
    schema.data_rows = [
        {"id": "A", "value": "g1", "color": "#ff0000"},
        {"id": "B", "value": "g2", "color": "#00ff00"},
    ]
    schema.parameters["STRIP_WIDTH"] = "50"
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_colorstrip"
    assert ds["columns"] == ["id", "value", "color"]
    assert ds["parameters"]["STRIP_WIDTH"] == "50"
    assert [r["id"] for r in ds["data"]] == ["A", "B"]
    assert ds["data"][0]["value"] == "g1"


def test_roundtrip_labels(tmp_path):
    schema = create_schema("labels", label="lab", separator="TAB")
    schema.columns = ["id", "label"]
    schema.data_rows = [
        {"id": "A", "label": "NodeA"},
        {"id": "B", "label": "NodeB"},
    ]
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_labels"
    assert ds["columns"] == ["id", "label"]
    assert ds["data"][0] == {"id": "A", "label": "NodeA"}


def test_roundtrip_tree_colors(tmp_path):
    schema = create_schema("tree_colors", label="tc", separator="TAB")
    schema.columns = ["id", "type", "color"]
    schema.data_rows = [{"id": "A", "type": "clade", "color": "#ff0000"}]
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_tree_colors"
    assert ds["columns"] == ["id", "type", "color"]
    assert ds["data"][0] == {"id": "A", "type": "clade", "color": "#ff0000"}


def test_roundtrip_collapse(tmp_path):
    schema = create_schema("collapse", label="col", separator="TAB")
    schema.columns = ["id"]
    schema.data_rows = [{"id": "X"}, {"id": "Y"}]
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_collapse"
    assert ds["columns"] == ["id"]
    assert [r["id"] for r in ds["data"]] == ["X", "Y"]


def test_roundtrip_prune(tmp_path):
    schema = create_schema("prune", label="pr", separator="TAB")
    schema.columns = ["id"]
    schema.data_rows = [{"id": "P1"}, {"id": "P2"}]
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_prune"
    assert ds["columns"] == ["id"]
    assert [r["id"] for r in ds["data"]] == ["P1", "P2"]


def test_roundtrip_binary_preserves_field_labels(tmp_path):
    schema = create_schema("binary", label="bin", separator="TAB")
    field_labels = ["f1", "f2", "f3"]
    field_colors = ["#ff0000", "#00ff00", "#0000ff"]
    schema.columns = ["id", *field_labels]
    schema.data_rows = [
        {"id": "A", "f1": "1", "f2": "0", "f3": "1"},
        {"id": "B", "f1": "0", "f2": "1", "f3": "0"},
    ]
    schema.parameters["FIELD_LABELS"] = "\t".join(field_labels)
    schema.parameters["FIELD_COLORS"] = "\t".join(field_colors)
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["type"] == "dataset_binary"
    # The real field names live in FIELD_LABELS (learner uses generic field_N
    # column names), so they must survive in the parameter, not the columns.
    assert ds["parameters"]["FIELD_LABELS"] == "\t".join(field_labels)
    assert ds["parameters"]["FIELD_COLORS"] == "\t".join(field_colors)
    assert [r["id"] for r in ds["data"]] == ["A", "B"]
    assert ds["data"][0]["field_1"] == "1"


def test_roundtrip_multiple_datasets(tmp_path):
    s1 = create_schema("labels", label="a", separator="TAB")
    s1.columns = ["id", "label"]
    s1.data_rows = [{"id": "A", "label": "x"}]
    s2 = create_schema("collapse", label="b", separator="TAB")
    s2.columns = ["id"]
    s2.data_rows = [{"id": "B"}]
    dss = learn_template(_write([s1, s2], tmp_path))["datasets"]
    assert [d["type"] for d in dss] == ["dataset_labels", "dataset_collapse"]


def test_roundtrip_comma_separator(tmp_path):
    # 参数行与数据行均按分隔符切分；COMMA 下参数不得丢失
    # （修复前 learner 用硬编码 TAB 切分参数行，会把 KEY,VALUE 误判为
    # 单个无值参数）。
    schema = create_schema("color_strip", label="cs", separator="COMMA")
    schema.columns = ["id", "value", "color"]
    schema.data_rows = [
        {"id": "A", "value": "g1", "color": "#ff0000"},
        {"id": "B", "value": "g2", "color": "#00ff00"},
    ]
    schema.parameters["STRIP_WIDTH"] = "50"
    ds = learn_template(_write([schema], tmp_path))["datasets"][0]
    assert ds["separator"] == ","
    # 关键：COMMA 分隔下参数必须被正确解析（H4 修复前会全部丢失）
    assert ds["parameters"].get("STRIP_WIDTH") == "50"
    assert ds["parameters"].get("DATASET_LABEL") == "cs"
    assert ds["columns"] == ["id", "value", "color"]
    assert ds["data"][0]["value"] == "g1"
