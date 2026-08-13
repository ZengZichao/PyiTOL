"""Tree structure schema definitions for collapse, prune, spacing, and treestyle."""

from dataclasses import dataclass

from .base import TemplateSchema, register_template


@register_template(
    type_name="dataset_collapse",
    header="COLLAPSE",
    required_columns=["id"],
    no_label_color=True,
    aliases=["collapse"],
)
@dataclass
class CollapseSchema(TemplateSchema):
    dataset_type: str = "dataset_collapse"
    label: str = "collapse"


@register_template(
    type_name="dataset_prune",
    header="PRUNE",
    required_columns=["id"],
    no_label_color=True,
    aliases=["prune"],
)
@dataclass
class PruneSchema(TemplateSchema):
    dataset_type: str = "dataset_prune"
    label: str = "prune"


@register_template(
    type_name="dataset_spacing",
    header="SPACING",
    required_columns=["id", "factor"],
    no_label_color=True,
    aliases=["spacing"],
)
@dataclass
class SpacingSchema(TemplateSchema):
    dataset_type: str = "dataset_spacing"
    label: str = "spacing"


@register_template(
    type_name="dataset_treestyle",
    header="DATASET_TREESTYLE",
    no_label_color=True,
    aliases=["treestyle"],
)
@dataclass
class TreeStyleSchema(TemplateSchema):
    dataset_type: str = "dataset_treestyle"
    label: str = "treestyle"
