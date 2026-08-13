"""Annotation schema definitions for labels, popup info, tree colors, ranges, and style."""

from dataclasses import dataclass

from .base import TemplateSchema, register_template


@register_template(
    type_name="dataset_labels",
    header="LABELS",
    required_columns=["id", "label"],
    aliases=["labels"],
)
@dataclass
class LabelsSchema(TemplateSchema):
    dataset_type: str = "dataset_labels"
    label: str = "labels"


@register_template(
    type_name="dataset_popup_info",
    header="POPUP_INFO",
    required_columns=["id", "title", "content"],
    no_label_color=True,
    aliases=["popup_info"],
)
@dataclass
class PopupInfoSchema(TemplateSchema):
    dataset_type: str = "dataset_popup_info"
    label: str = "popup_info"


@register_template(
    type_name="dataset_tree_colors",
    header="TREE_COLORS",
    required_columns=["id", "type", "color"],
    no_label_color=True,
    aliases=["tree_colors", "branch", "dataset_branches"],
)
@dataclass
class BranchSchema(TemplateSchema):
    dataset_type: str = "dataset_tree_colors"
    label: str = "branch"


@dataclass
class TreeColorsSchema(TemplateSchema):
    """Alias for BranchSchema - kept for backward compatibility."""

    dataset_type: str = "dataset_tree_colors"
    label: str = "tree_colors"


@register_template(
    type_name="dataset_range",
    header="DATASET_RANGE",
    required_columns=["id", "label", "color"],
    aliases=["range"],
)
@dataclass
class RangeSchema(TemplateSchema):
    dataset_type: str = "dataset_range"
    label: str = "range"


@register_template(
    type_name="dataset_style",
    header="DATASET_STYLE",
    required_columns=["id", "type", "color"],
    aliases=["style"],
)
@dataclass
class StyleSchema(TemplateSchema):
    dataset_type: str = "dataset_style"
    label: str = "style"
