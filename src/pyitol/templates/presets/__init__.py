"""Preset configurations for common iTOL visualization patterns and color palettes."""

from __future__ import annotations

from pyitol.exceptions import TemplateTypeError
from pyitol.templates.presets.cell import get_cell_palette, list_cell_palettes
from pyitol.templates.presets.colorblind import get_colorblind_palette, list_colorblind_palettes
from pyitol.templates.presets.nature import get_nature_palette, list_nature_palettes
from pyitol.templates.schemas.annotations import (
    BranchSchema,
    LabelsSchema,
    PopupInfoSchema,
    RangeSchema,
    TreeColorsSchema,
)
from pyitol.templates.schemas.base import TemplateSchema
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
from pyitol.templates.schemas.tree_structure import (
    CollapseSchema,
    PruneSchema,
    SpacingSchema,
)

SCHEMA_PRESETS = {
    "simple_bar": SimpleBarSchema,
    "multi_bar": MultiBarSchema,
    "color_strip": ColorStripSchema,
    "heatmap": HeatmapSchema,
    "symbols": SymbolsSchema,
    "pie": PiechartSchema,
    "binary": BinarySchema,
    "range": RangeSchema,
    "branch": BranchSchema,
    "externalshape": ExternalshapeSchema,
    "connection": ConnectionSchema,
    "domains": DomainsSchema,
    "alignment": AlignmentSchema,
    "image": ImageSchema,
    "text": TextSchema,
    "gradient": GradientSchema,
    "boxplot": BoxplotSchema,
    "linechart": LinechartSchema,
    "arrows": ArrowsSchema,
    "tanglegram": TanglegramSchema,
    "placement": PlacementSchema,
    "timescale": TimescaleSchema,
    "manual": ManualSchema,
    "meme": MemeSchema,
    "labels": LabelsSchema,
    "popup_info": PopupInfoSchema,
    "tree_colors": TreeColorsSchema,
    "collapse": CollapseSchema,
    "prune": PruneSchema,
    "spacing": SpacingSchema,
}


COLOR_PRESETS = {
    "nature": get_nature_palette,
    "cell": get_cell_palette,
    "colorblind": get_colorblind_palette,
}


def get_preset(name: str) -> TemplateSchema:
    """Get a schema preset by name."""
    if name not in SCHEMA_PRESETS:
        raise TemplateTypeError(f"Unknown preset: {name}. Available: {sorted(SCHEMA_PRESETS.keys())}")
    return SCHEMA_PRESETS[name]()


def list_presets() -> list[str]:
    """List all available preset names."""
    return sorted(SCHEMA_PRESETS.keys())


def get_palette(preset_name: str, palette_name: str = "primary", n: int | None = None) -> list[str]:
    """Get a color palette from a preset collection.

    Args:
        preset_name: 'nature', 'cell', or 'colorblind'
        palette_name: specific palette name within the collection
        n: number of colors needed
    """
    func = COLOR_PRESETS.get(preset_name)
    if func is None:
        raise TemplateTypeError(f"Unknown color preset: {preset_name}. Available: {list(COLOR_PRESETS.keys())}")
    return func(palette_name, n)


def list_all_palettes() -> dict:
    """List all available palette names grouped by preset."""
    return {
        "nature": list_nature_palettes(),
        "cell": list_cell_palettes(),
        "colorblind": list_colorblind_palettes(),
    }
