"""Advanced dataset schema definitions for complex iTOL visualization types."""

from dataclasses import dataclass

from .base import TemplateSchema, register_template


@register_template(
    type_name="dataset_domains",
    header="DATASET_DOMAINS",
    required_columns=["id", "from", "to", "type"],
    aliases=["domains"],
)
@dataclass
class DomainsSchema(TemplateSchema):
    dataset_type: str = "dataset_domains"
    label: str = "domains"

    def validate(self) -> list[str]:
        """P1-11: Accept both [id,from,to,type] and [id,domain] formats."""
        errors = []
        if self.columns:
            has_domain_format = "domain" in self.columns and "id" in self.columns
            has_range_format = all(c in self.columns for c in ("id", "from", "to", "type"))
            if not has_domain_format and not has_range_format:
                errors.append(f"Domains columns must be [id,from,to,type] or [id,domain]; got {self.columns}")
        for i, row in enumerate(self.data_rows):
            if "id" not in row or row["id"] == "":
                errors.append(f"Row {i + 1}: missing required field 'id'")
        return errors


@register_template(
    type_name="dataset_arrows",
    header="DATASET_ARROWS",
    required_columns=["id", "position"],
    aliases=["arrows"],
)
@dataclass
class ArrowsSchema(TemplateSchema):
    dataset_type: str = "dataset_arrows"
    label: str = "arrows"


@register_template(
    type_name="dataset_connections",
    header="DATASET_CONNECTION",
    required_columns=["id1", "id2"],
    aliases=["connection"],
)
@dataclass
class ConnectionSchema(TemplateSchema):
    dataset_type: str = "dataset_connections"
    label: str = "connection"


@register_template(
    type_name="dataset_tanglegram",
    header="DATASET_TANGLEGRAM",
    required_columns=["id1", "id2"],
    aliases=["tanglegram"],
)
@dataclass
class TanglegramSchema(TemplateSchema):
    dataset_type: str = "dataset_tanglegram"
    label: str = "tanglegram"


@register_template(
    type_name="dataset_linechart",
    header="DATASET_LINECHART",
    # iTOL DATASET_LINECHART data rows are `ID <sep> position <sep> value`,
    # so the required columns are id, position, value.
    required_columns=["id", "position", "value"],
    aliases=["linechart"],
)
@dataclass
class LinechartSchema(TemplateSchema):
    dataset_type: str = "dataset_linechart"
    label: str = "linechart"


@register_template(
    type_name="dataset_image",
    header="DATASET_IMAGE",
    required_columns=["id", "image_file"],
    aliases=["image"],
)
@dataclass
class ImageSchema(TemplateSchema):
    dataset_type: str = "dataset_image"
    label: str = "image"


@register_template(
    type_name="dataset_alignment",
    header="DATASET_ALIGNMENT",
    required_columns=["id", "alignment"],
    aliases=["alignment"],
)
@dataclass
class AlignmentSchema(TemplateSchema):
    dataset_type: str = "dataset_alignment"
    label: str = "alignment"


@register_template(
    type_name="dataset_placement",
    header="DATASET_PLACEMENT",
    required_columns=["id", "position", "count"],
    aliases=["placement"],
)
@dataclass
class PlacementSchema(TemplateSchema):
    dataset_type: str = "dataset_placement"
    label: str = "placement"


@register_template(
    type_name="dataset_timescale",
    header="DATASET_TIMESCALE",
    required_columns=["time_point", "label"],
    aliases=["timescale"],
)
@dataclass
class TimescaleSchema(TemplateSchema):
    dataset_type: str = "dataset_timescale"
    label: str = "timescale"


@register_template(
    type_name="dataset_meme",
    header="DATASET_MEME",
    required_columns=["id", "start", "end", "name"],
    aliases=["meme"],
)
@dataclass
class MemeSchema(TemplateSchema):
    dataset_type: str = "dataset_meme"
    label: str = "meme"


@register_template(
    type_name="dataset_manual",
    header="DATASET_MANUAL",
    aliases=["manual"],
)
@dataclass
class ManualSchema(TemplateSchema):
    dataset_type: str = "dataset_manual"
    label: str = "manual"
