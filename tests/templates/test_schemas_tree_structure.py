"""Tests for pyitol.templates.schemas.tree_structure module."""

from pyitol.templates.schemas.base import (
    NO_LABEL_COLOR_TYPES,
    REQUIRED_COLUMNS,
    SCHEMA_MAP,
    TEMPLATE_TYPE_HEADER,
    TemplateSchema,
)
from pyitol.templates.schemas.tree_structure import (
    CollapseSchema,
    PruneSchema,
    SpacingSchema,
)

# ---------------------------------------------------------------------------
# Instantiation tests
# ---------------------------------------------------------------------------


class TestTreeStructureInstantiation:
    """Verify every tree-structure schema can be instantiated with defaults."""

    def test_collapse_schema(self):
        s = CollapseSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_collapse"
        assert s.label == "collapse"

    def test_prune_schema(self):
        s = PruneSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_prune"
        assert s.label == "prune"

    def test_spacing_schema(self):
        s = SpacingSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_spacing"
        assert s.label == "spacing"


# ---------------------------------------------------------------------------
# SCHEMA_MAP registration tests
# ---------------------------------------------------------------------------


class TestTreeStructureSchemaMap:
    """Verify schemas are registered in SCHEMA_MAP with correct type_name and aliases."""

    def test_collapse_schema_map(self):
        assert SCHEMA_MAP["dataset_collapse"] is CollapseSchema
        assert SCHEMA_MAP["collapse"] is CollapseSchema

    def test_prune_schema_map(self):
        assert SCHEMA_MAP["dataset_prune"] is PruneSchema
        assert SCHEMA_MAP["prune"] is PruneSchema

    def test_spacing_schema_map(self):
        assert SCHEMA_MAP["dataset_spacing"] is SpacingSchema
        assert SCHEMA_MAP["spacing"] is SpacingSchema


# ---------------------------------------------------------------------------
# TEMPLATE_TYPE_HEADER tests
# ---------------------------------------------------------------------------


class TestTreeStructureHeaders:
    """Verify the correct iTOL header is registered for each tree-structure type."""

    def test_collapse_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_collapse"] == "COLLAPSE"
        assert TEMPLATE_TYPE_HEADER["collapse"] == "COLLAPSE"

    def test_prune_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_prune"] == "PRUNE"
        assert TEMPLATE_TYPE_HEADER["prune"] == "PRUNE"

    def test_spacing_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_spacing"] == "SPACING"
        assert TEMPLATE_TYPE_HEADER["spacing"] == "SPACING"


# ---------------------------------------------------------------------------
# REQUIRED_COLUMNS tests
# ---------------------------------------------------------------------------


class TestTreeStructureRequiredColumns:
    """Verify required columns are correctly registered for each tree-structure type."""

    def test_collapse_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_collapse"] == ["id"]
        assert REQUIRED_COLUMNS["collapse"] == ["id"]

    def test_prune_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_prune"] == ["id"]
        assert REQUIRED_COLUMNS["prune"] == ["id"]

    def test_spacing_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_spacing"] == ["id", "factor"]
        assert REQUIRED_COLUMNS["spacing"] == ["id", "factor"]


# ---------------------------------------------------------------------------
# NO_LABEL_COLOR_TYPES tests
# ---------------------------------------------------------------------------


class TestTreeStructureNoLabelColor:
    """Verify that all tree-structure schemas are no_label_color types."""

    def test_collapse_no_label_color(self):
        assert "dataset_collapse" in NO_LABEL_COLOR_TYPES
        assert "collapse" in NO_LABEL_COLOR_TYPES

    def test_prune_no_label_color(self):
        assert "dataset_prune" in NO_LABEL_COLOR_TYPES
        assert "prune" in NO_LABEL_COLOR_TYPES

    def test_spacing_no_label_color(self):
        assert "dataset_spacing" in NO_LABEL_COLOR_TYPES
        assert "spacing" in NO_LABEL_COLOR_TYPES

    def test_uses_label_color_returns_false_for_collapse(self):
        s = CollapseSchema(dataset_type="dataset_collapse")
        assert s.uses_label_color() is False

    def test_uses_label_color_returns_false_for_prune(self):
        s = PruneSchema(dataset_type="dataset_prune")
        assert s.uses_label_color() is False

    def test_uses_label_color_returns_false_for_spacing(self):
        s = SpacingSchema(dataset_type="dataset_spacing")
        assert s.uses_label_color() is False
