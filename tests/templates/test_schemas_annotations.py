"""Tests for pyitol.templates.schemas.annotations module."""

from pyitol.templates.schemas.annotations import (
    BranchSchema,
    LabelsSchema,
    PopupInfoSchema,
    RangeSchema,
    StyleSchema,
    TreeColorsSchema,
)
from pyitol.templates.schemas.base import (
    NO_LABEL_COLOR_TYPES,
    REQUIRED_COLUMNS,
    SCHEMA_MAP,
    TEMPLATE_TYPE_HEADER,
    TemplateSchema,
)

# ---------------------------------------------------------------------------
# Instantiation tests
# ---------------------------------------------------------------------------


class TestAnnotationsInstantiation:
    """Verify every annotation schema can be instantiated with defaults."""

    def test_labels_schema(self):
        s = LabelsSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_labels"

    def test_popup_info_schema(self):
        s = PopupInfoSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_popup_info"

    def test_branch_schema(self):
        s = BranchSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_tree_colors"

    def test_tree_colors_schema(self):
        s = TreeColorsSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_tree_colors"

    def test_range_schema(self):
        s = RangeSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_range"

    def test_style_schema(self):
        s = StyleSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_style"


# ---------------------------------------------------------------------------
# SCHEMA_MAP registration tests
# ---------------------------------------------------------------------------


class TestAnnotationsSchemaMap:
    """Verify schemas are registered in SCHEMA_MAP with correct type_name and aliases."""

    def test_labels_schema_map(self):
        assert SCHEMA_MAP["dataset_labels"] is LabelsSchema
        assert SCHEMA_MAP["labels"] is LabelsSchema

    def test_popup_info_schema_map(self):
        assert SCHEMA_MAP["dataset_popup_info"] is PopupInfoSchema
        assert SCHEMA_MAP["popup_info"] is PopupInfoSchema

    def test_branch_schema_map(self):
        assert SCHEMA_MAP["dataset_tree_colors"] is BranchSchema
        assert SCHEMA_MAP["tree_colors"] is BranchSchema
        assert SCHEMA_MAP["branch"] is BranchSchema
        assert SCHEMA_MAP["dataset_branches"] is BranchSchema

    def test_range_schema_map(self):
        assert SCHEMA_MAP["dataset_range"] is RangeSchema
        assert SCHEMA_MAP["range"] is RangeSchema

    def test_style_schema_map(self):
        assert SCHEMA_MAP["dataset_style"] is StyleSchema
        assert SCHEMA_MAP["style"] is StyleSchema


# ---------------------------------------------------------------------------
# TEMPLATE_TYPE_HEADER tests
# ---------------------------------------------------------------------------


class TestAnnotationsHeaders:
    """Verify the correct iTOL header is registered for each annotation type."""

    def test_labels_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_labels"] == "LABELS"
        assert TEMPLATE_TYPE_HEADER["labels"] == "LABELS"

    def test_popup_info_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_popup_info"] == "POPUP_INFO"
        assert TEMPLATE_TYPE_HEADER["popup_info"] == "POPUP_INFO"

    def test_branch_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_tree_colors"] == "TREE_COLORS"
        assert TEMPLATE_TYPE_HEADER["branch"] == "TREE_COLORS"

    def test_range_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_range"] == "DATASET_RANGE"
        assert TEMPLATE_TYPE_HEADER["range"] == "DATASET_RANGE"

    def test_style_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_style"] == "DATASET_STYLE"
        assert TEMPLATE_TYPE_HEADER["style"] == "DATASET_STYLE"


# ---------------------------------------------------------------------------
# REQUIRED_COLUMNS tests
# ---------------------------------------------------------------------------


class TestAnnotationsRequiredColumns:
    """Verify required columns are correctly registered for each annotation type."""

    def test_labels_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_labels"] == ["id", "label"]
        assert REQUIRED_COLUMNS["labels"] == ["id", "label"]

    def test_popup_info_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_popup_info"] == ["id", "title", "content"]
        assert REQUIRED_COLUMNS["popup_info"] == ["id", "title", "content"]

    def test_branch_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_tree_colors"] == ["id", "type", "color"]
        assert REQUIRED_COLUMNS["tree_colors"] == ["id", "type", "color"]
        assert REQUIRED_COLUMNS["branch"] == ["id", "type", "color"]
        assert REQUIRED_COLUMNS["dataset_branches"] == ["id", "type", "color"]

    def test_range_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_range"] == ["id", "label", "color"]
        assert REQUIRED_COLUMNS["range"] == ["id", "label", "color"]

    def test_style_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_style"] == ["id", "type", "color"]
        assert REQUIRED_COLUMNS["style"] == ["id", "type", "color"]


# ---------------------------------------------------------------------------
# NO_LABEL_COLOR_TYPES tests
# ---------------------------------------------------------------------------


class TestAnnotationsNoLabelColor:
    """Verify which annotation schemas opt out of label/color lines."""

    def test_popup_info_no_label_color(self):
        assert "dataset_popup_info" in NO_LABEL_COLOR_TYPES
        assert "popup_info" in NO_LABEL_COLOR_TYPES

    def test_branch_no_label_color(self):
        assert "dataset_tree_colors" in NO_LABEL_COLOR_TYPES
        assert "tree_colors" in NO_LABEL_COLOR_TYPES
        assert "branch" in NO_LABEL_COLOR_TYPES
        assert "dataset_branches" in NO_LABEL_COLOR_TYPES

    def test_labels_uses_label_color(self):
        assert "dataset_labels" not in NO_LABEL_COLOR_TYPES
        assert "labels" not in NO_LABEL_COLOR_TYPES

    def test_range_uses_label_color(self):
        assert "dataset_range" not in NO_LABEL_COLOR_TYPES

    def test_style_uses_label_color(self):
        assert "dataset_style" not in NO_LABEL_COLOR_TYPES


# ---------------------------------------------------------------------------
# TreeColorsSchema backward-compatibility note
# ---------------------------------------------------------------------------


class TestTreeColorsSchemaCompatibility:
    """TreeColorsSchema is not registered independently; it shares BranchSchema's type."""

    def test_tree_colors_not_separately_registered(self):
        # TreeColorsSchema is a plain dataclass (no @register_template),
        # so its type_name does not appear in SCHEMA_MAP as a distinct class.
        # The 'tree_colors' key points to BranchSchema, not TreeColorsSchema.
        assert SCHEMA_MAP.get("tree_colors") is BranchSchema

    def test_tree_colors_instance_fields(self):
        s = TreeColorsSchema()
        assert s.dataset_type == "dataset_tree_colors"
        assert s.label == "tree_colors"
