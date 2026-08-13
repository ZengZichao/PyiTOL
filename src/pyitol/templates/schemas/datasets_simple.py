"""Simple dataset schema definitions for basic iTOL visualization types."""

from dataclasses import dataclass

from .base import TemplateSchema, register_template


@register_template(
    type_name="dataset_simple_bar",
    header="DATASET_SIMPLEBAR",
    required_columns=["id", "bar_height"],
    aliases=["simple_bar"],
)
@dataclass
class SimpleBarSchema(TemplateSchema):
    dataset_type: str = "dataset_simple_bar"
    label: str = "simple_bar"


@register_template(
    type_name="dataset_multibar",
    header="DATASET_MULTIBAR",
    required_columns=["id"],
    aliases=["multi_bar"],
)
@dataclass
class MultiBarSchema(TemplateSchema):
    dataset_type: str = "dataset_multibar"
    label: str = "multi_bar"


@register_template(
    type_name="dataset_colorstrip",
    header="DATASET_COLORSTRIP",
    required_columns=["id", "value", "color"],
    aliases=["color_strip", "colorstrip"],
)
@dataclass
class ColorStripSchema(TemplateSchema):
    dataset_type: str = "dataset_colorstrip"
    label: str = "color_strip"


@register_template(
    type_name="dataset_heatmap",
    header="DATASET_HEATMAP",
    required_columns=["id"],
    aliases=["heatmap"],
)
@dataclass
class HeatmapSchema(TemplateSchema):
    dataset_type: str = "dataset_heatmap"
    label: str = "heatmap"


@register_template(
    type_name="dataset_symbols",
    header="DATASET_SYMBOL",
    required_columns=["id", "type", "value", "color"],
    aliases=["symbols", "symbol"],
)
@dataclass
class SymbolsSchema(TemplateSchema):
    dataset_type: str = "dataset_symbols"
    label: str = "symbols"


@register_template(
    type_name="dataset_piechart",
    header="DATASET_PIECHART",
    required_columns=["id"],
    aliases=["pie", "piechart"],
)
@dataclass
class PiechartSchema(TemplateSchema):
    dataset_type: str = "dataset_piechart"
    label: str = "piechart"


@register_template(
    type_name="dataset_binary",
    header="DATASET_BINARY",
    required_columns=["id"],
    aliases=["binary"],
)
@dataclass
class BinarySchema(TemplateSchema):
    dataset_type: str = "dataset_binary"
    label: str = "binary"


@register_template(
    type_name="dataset_gradient",
    header="DATASET_GRADIENT",
    required_columns=["id", "value"],
    aliases=["gradient"],
)
@dataclass
class GradientSchema(TemplateSchema):
    dataset_type: str = "dataset_gradient"
    label: str = "gradient"


@register_template(
    type_name="dataset_externalshape",
    header="DATASET_EXTERNALSHAPE",
    required_columns=["id"],
    aliases=["externalshape"],
)
@dataclass
class ExternalshapeSchema(TemplateSchema):
    dataset_type: str = "dataset_externalshape"
    label: str = "externalshape"


@register_template(
    type_name="dataset_text",
    header="DATASET_TEXT",
    required_columns=["id", "text"],
    aliases=["text"],
)
@dataclass
class TextSchema(TemplateSchema):
    dataset_type: str = "dataset_text"
    label: str = "text"


@register_template(
    type_name="dataset_boxplot",
    header="DATASET_BOXPLOT",
    required_columns=["id", "minimum", "q1", "median", "q3", "maximum"],
    aliases=["boxplot"],
)
@dataclass
class BoxplotSchema(TemplateSchema):
    dataset_type: str = "dataset_boxplot"
    label: str = "boxplot"
