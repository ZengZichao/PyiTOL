"""Tests for pyitol.templates.schemas.datasets_simple module."""

from pyitol.templates.schemas.base import (
    NO_LABEL_COLOR_TYPES,
    REQUIRED_COLUMNS,
    SCHEMA_MAP,
    TEMPLATE_TYPE_HEADER,
    TemplateSchema,
)
from pyitol.templates.schemas.datasets_simple import (
    BinarySchema,
    BoxplotSchema,
    ColorStripSchema,
    ExternalshapeSchema,
    GradientSchema,
    HeatmapSchema,
    MultiBarSchema,
    PiechartSchema,
    SimpleBarSchema,
    SymbolsSchema,
    TextSchema,
)

# ---------------------------------------------------------------------------
# Instantiation tests
# ---------------------------------------------------------------------------


class TestSimpleDatasetsInstantiation:
    """Verify every simple-dataset schema can be instantiated with defaults."""

    def test_simple_bar_schema(self):
        s = SimpleBarSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_simple_bar"

    def test_multi_bar_schema(self):
        s = MultiBarSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_multibar"

    def test_color_strip_schema(self):
        s = ColorStripSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_colorstrip"

    def test_heatmap_schema(self):
        s = HeatmapSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_heatmap"

    def test_symbols_schema(self):
        s = SymbolsSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_symbols"

    def test_piechart_schema(self):
        s = PiechartSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_piechart"

    def test_binary_schema(self):
        s = BinarySchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_binary"

    def test_gradient_schema(self):
        s = GradientSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_gradient"

    def test_externalshape_schema(self):
        s = ExternalshapeSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_externalshape"

    def test_text_schema(self):
        s = TextSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_text"

    def test_boxplot_schema(self):
        s = BoxplotSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_boxplot"


# ---------------------------------------------------------------------------
# SCHEMA_MAP registration tests
# ---------------------------------------------------------------------------


class TestSimpleDatasetsSchemaMap:
    """Verify schemas are registered in SCHEMA_MAP with correct type_name and aliases."""

    def test_simple_bar_schema_map(self):
        assert SCHEMA_MAP["dataset_simple_bar"] is SimpleBarSchema
        assert SCHEMA_MAP["simple_bar"] is SimpleBarSchema

    def test_multi_bar_schema_map(self):
        assert SCHEMA_MAP["dataset_multibar"] is MultiBarSchema
        assert SCHEMA_MAP["multi_bar"] is MultiBarSchema

    def test_color_strip_schema_map(self):
        assert SCHEMA_MAP["dataset_colorstrip"] is ColorStripSchema
        assert SCHEMA_MAP["color_strip"] is ColorStripSchema
        assert SCHEMA_MAP["colorstrip"] is ColorStripSchema

    def test_heatmap_schema_map(self):
        assert SCHEMA_MAP["dataset_heatmap"] is HeatmapSchema
        assert SCHEMA_MAP["heatmap"] is HeatmapSchema

    def test_symbols_schema_map(self):
        assert SCHEMA_MAP["dataset_symbols"] is SymbolsSchema
        assert SCHEMA_MAP["symbols"] is SymbolsSchema
        assert SCHEMA_MAP["symbol"] is SymbolsSchema

    def test_piechart_schema_map(self):
        assert SCHEMA_MAP["dataset_piechart"] is PiechartSchema
        assert SCHEMA_MAP["pie"] is PiechartSchema
        assert SCHEMA_MAP["piechart"] is PiechartSchema

    def test_binary_schema_map(self):
        assert SCHEMA_MAP["dataset_binary"] is BinarySchema
        assert SCHEMA_MAP["binary"] is BinarySchema

    def test_gradient_schema_map(self):
        assert SCHEMA_MAP["dataset_gradient"] is GradientSchema
        assert SCHEMA_MAP["gradient"] is GradientSchema

    def test_externalshape_schema_map(self):
        assert SCHEMA_MAP["dataset_externalshape"] is ExternalshapeSchema
        assert SCHEMA_MAP["externalshape"] is ExternalshapeSchema

    def test_text_schema_map(self):
        assert SCHEMA_MAP["dataset_text"] is TextSchema
        assert SCHEMA_MAP["text"] is TextSchema

    def test_boxplot_schema_map(self):
        assert SCHEMA_MAP["dataset_boxplot"] is BoxplotSchema
        assert SCHEMA_MAP["boxplot"] is BoxplotSchema


# ---------------------------------------------------------------------------
# TEMPLATE_TYPE_HEADER tests
# ---------------------------------------------------------------------------


class TestSimpleDatasetsHeaders:
    """Verify the correct iTOL header is registered for each simple-dataset type."""

    def test_simple_bar_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_simple_bar"] == "DATASET_SIMPLEBAR"
        assert TEMPLATE_TYPE_HEADER["simple_bar"] == "DATASET_SIMPLEBAR"

    def test_multi_bar_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_multibar"] == "DATASET_MULTIBAR"
        assert TEMPLATE_TYPE_HEADER["multi_bar"] == "DATASET_MULTIBAR"

    def test_color_strip_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_colorstrip"] == "DATASET_COLORSTRIP"
        assert TEMPLATE_TYPE_HEADER["color_strip"] == "DATASET_COLORSTRIP"
        assert TEMPLATE_TYPE_HEADER["colorstrip"] == "DATASET_COLORSTRIP"

    def test_heatmap_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_heatmap"] == "DATASET_HEATMAP"
        assert TEMPLATE_TYPE_HEADER["heatmap"] == "DATASET_HEATMAP"

    def test_symbols_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_symbols"] == "DATASET_SYMBOL"
        assert TEMPLATE_TYPE_HEADER["symbols"] == "DATASET_SYMBOL"

    def test_piechart_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_piechart"] == "DATASET_PIECHART"
        assert TEMPLATE_TYPE_HEADER["pie"] == "DATASET_PIECHART"
        assert TEMPLATE_TYPE_HEADER["piechart"] == "DATASET_PIECHART"

    def test_binary_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_binary"] == "DATASET_BINARY"
        assert TEMPLATE_TYPE_HEADER["binary"] == "DATASET_BINARY"

    def test_gradient_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_gradient"] == "DATASET_GRADIENT"
        assert TEMPLATE_TYPE_HEADER["gradient"] == "DATASET_GRADIENT"

    def test_externalshape_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_externalshape"] == "DATASET_EXTERNALSHAPE"
        assert TEMPLATE_TYPE_HEADER["externalshape"] == "DATASET_EXTERNALSHAPE"

    def test_text_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_text"] == "DATASET_TEXT"
        assert TEMPLATE_TYPE_HEADER["text"] == "DATASET_TEXT"

    def test_boxplot_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_boxplot"] == "DATASET_BOXPLOT"
        assert TEMPLATE_TYPE_HEADER["boxplot"] == "DATASET_BOXPLOT"


# ---------------------------------------------------------------------------
# REQUIRED_COLUMNS tests
# ---------------------------------------------------------------------------


class TestSimpleDatasetsRequiredColumns:
    """Verify required columns are correctly registered for each simple-dataset type."""

    def test_simple_bar_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_simple_bar"] == ["id", "bar_height"]
        assert REQUIRED_COLUMNS["simple_bar"] == ["id", "bar_height"]

    def test_multi_bar_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_multibar"] == ["id"]
        assert REQUIRED_COLUMNS["multi_bar"] == ["id"]

    def test_color_strip_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_colorstrip"] == ["id", "value", "color"]
        assert REQUIRED_COLUMNS["color_strip"] == ["id", "value", "color"]
        assert REQUIRED_COLUMNS["colorstrip"] == ["id", "value", "color"]

    def test_heatmap_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_heatmap"] == ["id"]
        assert REQUIRED_COLUMNS["heatmap"] == ["id"]

    def test_symbols_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_symbols"] == ["id", "type", "value", "color"]
        assert REQUIRED_COLUMNS["symbols"] == ["id", "type", "value", "color"]
        assert REQUIRED_COLUMNS["symbol"] == ["id", "type", "value", "color"]

    def test_piechart_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_piechart"] == ["id"]
        assert REQUIRED_COLUMNS["pie"] == ["id"]
        assert REQUIRED_COLUMNS["piechart"] == ["id"]

    def test_binary_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_binary"] == ["id"]
        assert REQUIRED_COLUMNS["binary"] == ["id"]

    def test_gradient_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_gradient"] == ["id", "value"]
        assert REQUIRED_COLUMNS["gradient"] == ["id", "value"]

    def test_externalshape_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_externalshape"] == ["id"]
        assert REQUIRED_COLUMNS["externalshape"] == ["id"]

    def test_text_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_text"] == ["id", "text"]
        assert REQUIRED_COLUMNS["text"] == ["id", "text"]

    def test_boxplot_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_boxplot"] == [
            "id",
            "minimum",
            "q1",
            "median",
            "q3",
            "maximum",
        ]
        assert REQUIRED_COLUMNS["boxplot"] == [
            "id",
            "minimum",
            "q1",
            "median",
            "q3",
            "maximum",
        ]


# ---------------------------------------------------------------------------
# NO_LABEL_COLOR_TYPES tests
# ---------------------------------------------------------------------------


class TestSimpleDatasetsLabelColor:
    """Verify that none of the simple-dataset schemas are no_label_color types."""

    def test_no_simple_datasets_in_no_label_color(self):
        no_label_keys = [
            "dataset_simple_bar",
            "simple_bar",
            "dataset_multibar",
            "multi_bar",
            "dataset_colorstrip",
            "color_strip",
            "colorstrip",
            "dataset_heatmap",
            "heatmap",
            "dataset_symbols",
            "symbols",
            "symbol",
            "dataset_piechart",
            "pie",
            "piechart",
            "dataset_binary",
            "binary",
            "dataset_gradient",
            "gradient",
            "dataset_externalshape",
            "externalshape",
            "dataset_text",
            "text",
            "dataset_boxplot",
            "boxplot",
        ]
        for key in no_label_keys:
            assert key not in NO_LABEL_COLOR_TYPES, f"{key} should not be in NO_LABEL_COLOR_TYPES"
