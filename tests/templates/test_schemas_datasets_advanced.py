"""Tests for pyitol.templates.schemas.datasets_advanced module."""

from pyitol.templates.schemas.base import (
    NO_LABEL_COLOR_TYPES,
    REQUIRED_COLUMNS,
    SCHEMA_MAP,
    TEMPLATE_TYPE_HEADER,
    TemplateSchema,
)
from pyitol.templates.schemas.datasets_advanced import (
    AlignmentSchema,
    ArrowsSchema,
    ConnectionSchema,
    DomainsSchema,
    ImageSchema,
    LinechartSchema,
    ManualSchema,
    MemeSchema,
    PlacementSchema,
    TanglegramSchema,
    TimescaleSchema,
)

# ---------------------------------------------------------------------------
# Instantiation tests
# ---------------------------------------------------------------------------


class TestAdvancedDatasetsInstantiation:
    """Verify every advanced-dataset schema can be instantiated with defaults."""

    def test_domains_schema(self):
        s = DomainsSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_domains"

    def test_arrows_schema(self):
        s = ArrowsSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_arrows"

    def test_connection_schema(self):
        s = ConnectionSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_connections"

    def test_tanglegram_schema(self):
        s = TanglegramSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_tanglegram"

    def test_linechart_schema(self):
        s = LinechartSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_linechart"

    def test_image_schema(self):
        s = ImageSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_image"

    def test_alignment_schema(self):
        s = AlignmentSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_alignment"

    def test_placement_schema(self):
        s = PlacementSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_placement"

    def test_timescale_schema(self):
        s = TimescaleSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_timescale"

    def test_meme_schema(self):
        s = MemeSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_meme"

    def test_manual_schema(self):
        s = ManualSchema()
        assert isinstance(s, TemplateSchema)
        assert s.dataset_type == "dataset_manual"


# ---------------------------------------------------------------------------
# SCHEMA_MAP registration tests
# ---------------------------------------------------------------------------


class TestAdvancedDatasetsSchemaMap:
    """Verify schemas are registered in SCHEMA_MAP with correct type_name and aliases."""

    def test_domains_schema_map(self):
        assert SCHEMA_MAP["dataset_domains"] is DomainsSchema
        assert SCHEMA_MAP["domains"] is DomainsSchema

    def test_arrows_schema_map(self):
        assert SCHEMA_MAP["dataset_arrows"] is ArrowsSchema
        assert SCHEMA_MAP["arrows"] is ArrowsSchema

    def test_connection_schema_map(self):
        assert SCHEMA_MAP["dataset_connections"] is ConnectionSchema
        assert SCHEMA_MAP["connection"] is ConnectionSchema

    def test_tanglegram_schema_map(self):
        assert SCHEMA_MAP["dataset_tanglegram"] is TanglegramSchema
        assert SCHEMA_MAP["tanglegram"] is TanglegramSchema

    def test_linechart_schema_map(self):
        assert SCHEMA_MAP["dataset_linechart"] is LinechartSchema
        assert SCHEMA_MAP["linechart"] is LinechartSchema

    def test_image_schema_map(self):
        assert SCHEMA_MAP["dataset_image"] is ImageSchema
        assert SCHEMA_MAP["image"] is ImageSchema

    def test_alignment_schema_map(self):
        assert SCHEMA_MAP["dataset_alignment"] is AlignmentSchema
        assert SCHEMA_MAP["alignment"] is AlignmentSchema

    def test_placement_schema_map(self):
        assert SCHEMA_MAP["dataset_placement"] is PlacementSchema
        assert SCHEMA_MAP["placement"] is PlacementSchema

    def test_timescale_schema_map(self):
        assert SCHEMA_MAP["dataset_timescale"] is TimescaleSchema
        assert SCHEMA_MAP["timescale"] is TimescaleSchema

    def test_meme_schema_map(self):
        assert SCHEMA_MAP["dataset_meme"] is MemeSchema
        assert SCHEMA_MAP["meme"] is MemeSchema

    def test_manual_schema_map(self):
        assert SCHEMA_MAP["dataset_manual"] is ManualSchema
        assert SCHEMA_MAP["manual"] is ManualSchema


# ---------------------------------------------------------------------------
# TEMPLATE_TYPE_HEADER tests
# ---------------------------------------------------------------------------


class TestAdvancedDatasetsHeaders:
    """Verify the correct iTOL header is registered for each advanced-dataset type."""

    def test_domains_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_domains"] == "DATASET_DOMAINS"
        assert TEMPLATE_TYPE_HEADER["domains"] == "DATASET_DOMAINS"

    def test_arrows_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_arrows"] == "DATASET_ARROWS"
        assert TEMPLATE_TYPE_HEADER["arrows"] == "DATASET_ARROWS"

    def test_connection_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_connections"] == "DATASET_CONNECTION"
        assert TEMPLATE_TYPE_HEADER["connection"] == "DATASET_CONNECTION"

    def test_tanglegram_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_tanglegram"] == "DATASET_TANGLEGRAM"
        assert TEMPLATE_TYPE_HEADER["tanglegram"] == "DATASET_TANGLEGRAM"

    def test_linechart_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_linechart"] == "DATASET_LINECHART"
        assert TEMPLATE_TYPE_HEADER["linechart"] == "DATASET_LINECHART"

    def test_image_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_image"] == "DATASET_IMAGE"
        assert TEMPLATE_TYPE_HEADER["image"] == "DATASET_IMAGE"

    def test_alignment_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_alignment"] == "DATASET_ALIGNMENT"
        assert TEMPLATE_TYPE_HEADER["alignment"] == "DATASET_ALIGNMENT"

    def test_placement_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_placement"] == "DATASET_PLACEMENT"
        assert TEMPLATE_TYPE_HEADER["placement"] == "DATASET_PLACEMENT"

    def test_timescale_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_timescale"] == "DATASET_TIMESCALE"
        assert TEMPLATE_TYPE_HEADER["timescale"] == "DATASET_TIMESCALE"

    def test_meme_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_meme"] == "DATASET_MEME"
        assert TEMPLATE_TYPE_HEADER["meme"] == "DATASET_MEME"

    def test_manual_header(self):
        assert TEMPLATE_TYPE_HEADER["dataset_manual"] == "DATASET_MANUAL"
        assert TEMPLATE_TYPE_HEADER["manual"] == "DATASET_MANUAL"


# ---------------------------------------------------------------------------
# REQUIRED_COLUMNS tests
# ---------------------------------------------------------------------------


class TestAdvancedDatasetsRequiredColumns:
    """Verify required columns are correctly registered for each advanced-dataset type."""

    def test_domains_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_domains"] == ["id", "from", "to", "type"]
        assert REQUIRED_COLUMNS["domains"] == ["id", "from", "to", "type"]

    def test_arrows_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_arrows"] == ["id", "position"]
        assert REQUIRED_COLUMNS["arrows"] == ["id", "position"]

    def test_connection_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_connections"] == ["id1", "id2"]
        assert REQUIRED_COLUMNS["connection"] == ["id1", "id2"]

    def test_tanglegram_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_tanglegram"] == ["id1", "id2"]
        assert REQUIRED_COLUMNS["tanglegram"] == ["id1", "id2"]

    def test_linechart_required_columns(self):
        # iTOL DATASET_LINECHART 数据行为 `ID <sep> position <sep> value`
        assert REQUIRED_COLUMNS["dataset_linechart"] == ["id", "position", "value"]
        assert REQUIRED_COLUMNS["linechart"] == ["id", "position", "value"]

    def test_image_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_image"] == ["id", "image_file"]
        assert REQUIRED_COLUMNS["image"] == ["id", "image_file"]

    def test_alignment_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_alignment"] == ["id", "alignment"]
        assert REQUIRED_COLUMNS["alignment"] == ["id", "alignment"]

    def test_placement_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_placement"] == ["id", "position", "count"]
        assert REQUIRED_COLUMNS["placement"] == ["id", "position", "count"]

    def test_timescale_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_timescale"] == ["time_point", "label"]
        assert REQUIRED_COLUMNS["timescale"] == ["time_point", "label"]

    def test_meme_required_columns(self):
        assert REQUIRED_COLUMNS["dataset_meme"] == ["id", "start", "end", "name"]
        assert REQUIRED_COLUMNS["meme"] == ["id", "start", "end", "name"]

    def test_manual_no_required_columns(self):
        """ManualSchema has no required_columns registered."""
        assert "dataset_manual" not in REQUIRED_COLUMNS
        assert "manual" not in REQUIRED_COLUMNS


# ---------------------------------------------------------------------------
# NO_LABEL_COLOR_TYPES tests
# ---------------------------------------------------------------------------


class TestAdvancedDatasetsLabelColor:
    """Verify that none of the advanced-dataset schemas are no_label_color types."""

    def test_no_advanced_datasets_in_no_label_color(self):
        no_label_keys = [
            "dataset_domains",
            "domains",
            "dataset_arrows",
            "arrows",
            "dataset_connections",
            "connection",
            "dataset_tanglegram",
            "tanglegram",
            "dataset_linechart",
            "linechart",
            "dataset_image",
            "image",
            "dataset_alignment",
            "alignment",
            "dataset_placement",
            "placement",
            "dataset_timescale",
            "timescale",
            "dataset_meme",
            "meme",
            "dataset_manual",
            "manual",
        ]
        for key in no_label_keys:
            assert key not in NO_LABEL_COLOR_TYPES, f"{key} should not be in NO_LABEL_COLOR_TYPES"
