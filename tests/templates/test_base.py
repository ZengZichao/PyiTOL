"""Tests for PyiTOL template base schemas."""

import pytest

from pyitol.exceptions import TemplateTypeError
from pyitol.templates.schemas.base import (
    LegendConfig,
    TemplateSchema,
    create_schema,
)


class TestLegendConfig:
    def test_get_lines_all_fields(self):
        legend = LegendConfig(
            title="My Legend",
            position_x="100",
            position_y="200",
            horizontal="1",
            shapes=["1", "2"],
            colors=["#ff0000", "#00ff00"],
            labels=["A", "B"],
            shape_scales=["0.5", "1.0"],
        )
        lines = legend.get_lines(sep="\t")
        assert "LEGEND_TITLE\tMy Legend" in lines
        assert "LEGEND_POSITION_X\t100" in lines
        assert "LEGEND_POSITION_Y\t200" in lines
        assert "LEGEND_HORIZONTAL\t1" in lines
        assert "LEGEND_SHAPES\t1\t2" in lines
        assert "LEGEND_COLORS\t#ff0000\t#00ff00" in lines
        assert "LEGEND_LABELS\tA\tB" in lines
        assert "LEGEND_SHAPE_SCALES\t0.5\t1.0" in lines

    def test_get_lines_empty(self):
        legend = LegendConfig()
        assert legend.get_lines() == []


class TestTemplateSchema:
    def test_invalid_separator_defaults_to_tab(self):
        schema = TemplateSchema(separator="INVALID")
        assert schema.separator == "TAB"
        assert schema.get_separator_char() == "\t"

    def test_validate_missing_required_column(self):
        schema = create_schema("simple_bar")
        schema.columns = ["id"]  # missing 'bar_height'
        schema.data_rows = [{"id": "A", "bar_height": "10"}]
        errors = schema.validate()
        assert any("Missing required column: bar_height" in e for e in errors)

    def test_validate_missing_required_field_in_row(self):
        schema = create_schema("simple_bar")
        schema.columns = ["id", "bar_height"]
        schema.data_rows = [{"id": "A"}, {"id": "B", "bar_height": ""}]
        errors = schema.validate()
        assert any("missing required field 'bar_height'" in e for e in errors)

    def test_get_parameter_lines_skips_reserved_keys(self):
        schema = create_schema("simple_bar", label="test", color="#00ff00")
        schema.parameters["DATASET_LABEL"] = "ignored"
        schema.parameters["COLOR"] = "ignored"
        schema.parameters["SEPARATOR"] = "SPACE"
        schema.parameters["CUSTOM"] = "kept"
        lines = schema.get_parameter_lines()
        # Reserved parameter keys should be skipped (label/color come from attrs)
        assert not any(line.endswith("ignored") for line in lines)
        assert any("CUSTOM" in line for line in lines)


class TestCreateSchema:
    def test_unknown_type_raises(self):
        with pytest.raises(TemplateTypeError, match="Unknown template type"):
            create_schema("nonexistent_type")
