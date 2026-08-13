"""Tests for template schema base classes."""

import pytest

from pyitol.exceptions import TemplateTypeError
from pyitol.templates.schemas.base import (
    NO_LABEL_COLOR_TYPES,
    SCHEMA_MAP,
    LegendConfig,
    TemplateSchema,
    create_schema,
    get_registered_types,
)


class TestLegendConfig:
    def test_empty_by_default(self):
        legend = LegendConfig()
        assert legend.is_empty() is True

    def test_not_empty_with_title(self):
        legend = LegendConfig(title="My Legend")
        assert legend.is_empty() is False

    def test_get_lines_all_fields(self):
        legend = LegendConfig(
            title="Title",
            position_x="100",
            position_y="200",
            horizontal="1",
            shapes=["1", "2"],
            colors=["#ff0000", "#00ff00"],
            labels=["A", "B"],
            shape_scales=["1.0", "2.0"],
        )
        lines = legend.get_lines(sep="\t")
        assert len(lines) == 8
        assert "LEGEND_TITLE\tTitle" in lines
        assert "LEGEND_SHAPES\t1\t2" in lines
        assert "LEGEND_COLORS\t#ff0000\t#00ff00" in lines

    def test_get_lines_empty_list_not_included(self):
        legend = LegendConfig(title="T", shapes=[])
        lines = legend.get_lines(sep="\t")
        assert "LEGEND_TITLE\tT" in lines
        assert "LEGEND_SHAPES" not in "\n".join(lines)

    def test_get_lines_with_comma_sep(self):
        legend = LegendConfig(title="T")
        lines = legend.get_lines(sep=",")
        assert lines == ["LEGEND_TITLE,T"]


class TestTemplateSchema:
    def test_default_separator(self):
        schema = TemplateSchema()
        assert schema.separator == "TAB"

    def test_invalid_separator_fallback(self):
        schema = TemplateSchema(separator="INVALID")
        assert schema.separator == "TAB"

    def test_get_header_line(self):
        schema = TemplateSchema(dataset_type="dataset_simple_bar")
        assert schema.get_header_line() == "DATASET_SIMPLEBAR"

    def test_get_header_line_unknown(self):
        schema = TemplateSchema(dataset_type="unknown_type")
        assert schema.get_header_line() == "UNKNOWN_TYPE"

    def test_uses_label_color(self):
        for t in NO_LABEL_COLOR_TYPES:
            schema = TemplateSchema(dataset_type=t)
            assert schema.uses_label_color() is False
        schema = TemplateSchema(dataset_type="dataset_simple_bar")
        assert schema.uses_label_color() is True

    def test_validate_missing_required_column(self):
        schema = TemplateSchema(dataset_type="dataset_simple_bar", columns=["id"])
        errors = schema.validate()
        assert any("bar_height" in e for e in errors)

    def test_validate_missing_required_in_row(self):
        schema = TemplateSchema(
            dataset_type="dataset_simple_bar",
            columns=["id", "bar_height"],
            data_rows=[{"id": "A"}],
        )
        errors = schema.validate()
        assert any("missing required field 'bar_height'" in e for e in errors)

    def test_validate_empty_row_value(self):
        schema = TemplateSchema(
            dataset_type="dataset_simple_bar",
            columns=["id", "bar_height"],
            data_rows=[{"id": "A", "bar_height": ""}],
        )
        errors = schema.validate()
        assert any("missing required field 'bar_height'" in e for e in errors)

    def test_validate_none_row_value(self):
        # 必需字段取值为 None 也应判为缺失
        schema = TemplateSchema(
            dataset_type="dataset_simple_bar",
            columns=["id", "bar_height"],
            data_rows=[{"id": "A", "bar_height": None}],
        )
        errors = schema.validate()
        assert any("missing required field 'bar_height'" in e for e in errors)

    def test_get_parameter_lines_skips_reserved(self):
        schema = TemplateSchema(
            dataset_type="dataset_simple_bar",
            label="test",
            color="#ff0000",
            parameters={"DATASET_LABEL": "x", "COLOR": "#fff", "SEPARATOR": "TAB", "WIDTH": "50"},
        )
        lines = schema.get_parameter_lines()
        assert all("DATASET_LABEL" not in line or line.startswith("DATASET_LABEL\ttest") for line in lines)
        assert any("WIDTH\t50" in line for line in lines)
        assert not any(line.startswith("SEPARATOR") for line in lines)

    def test_get_parameter_lines_no_label_color_types(self):
        for t in NO_LABEL_COLOR_TYPES:
            schema = TemplateSchema(dataset_type=t, label="x", color="#fff")
            lines = schema.get_parameter_lines()
            assert "DATASET_LABEL" not in "\n".join(lines)
            assert "COLOR" not in "\n".join(lines)


class TestCreateSchema:
    def test_create_known_type(self):
        schema = create_schema("simple_bar", label="test")
        assert schema.dataset_type == "dataset_simple_bar"
        assert schema.label == "test"

    def test_create_unknown_type_raises(self):
        with pytest.raises(TemplateTypeError, match="Unknown template type"):
            create_schema("nonexistent_type")

    def test_all_types_creatable(self):
        for name in SCHEMA_MAP:
            schema = create_schema(name)
            assert schema is not None


class TestGetRegisteredTypes:
    def test_returns_dict(self):
        registry = get_registered_types()
        assert isinstance(registry, dict)
        assert len(registry) > 0
