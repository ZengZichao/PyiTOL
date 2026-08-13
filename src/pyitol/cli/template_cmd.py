"""Template commands (split into submodules for maintainability).

This module is a thin aggregator that re-exports every ``template_*`` command
function defined in the sibling submodules.  Commands are registered on the
shared ``template_app`` Typer instance at import time via their decorators, so
importing this module (for its side effects) makes the full ``template``
command group available to the top-level CLI.

Explicit imports (instead of ``from module import *``) keep the public API
discoverable, satisfy static analysis (no F403 star-import), and let the
``__all__`` declaration mark these names as intentional re-exports (no F401).
"""

from pyitol.cli.template_advanced import (
    template_alignment,
    template_external_shape_bubble,
    template_image,
    template_linechart,
    template_manual,
    template_meme,
    template_placement,
    template_tanglegram,
    template_timescale,
)
from pyitol.cli.template_datasets import (
    template_binary,
    template_boxplot,
    template_branch,
    template_color_strip,
    template_connections,
    template_domains,
    template_external_shape,
    template_gradient,
    template_heatmap,
    template_labels,
    template_multi_bar,
    template_pie,
    template_popup_info,
    template_simple_bar,
    template_symbols,
    template_text,
)
from pyitol.cli.template_tools import (
    template_bundle,
    template_create,
    template_validate,
)
from pyitol.cli.template_treeops import (
    template_arrow,
    template_branch_gradient,
    template_collapse,
    template_highlight,
    template_prune,
    template_ranges,
    template_spacing,
    template_style,
    template_tree_colors,
)

__all__ = [
    "template_alignment",
    "template_arrow",
    "template_binary",
    "template_boxplot",
    "template_branch",
    "template_branch_gradient",
    "template_bundle",
    "template_collapse",
    # template_datasets
    "template_color_strip",
    "template_connections",
    # template_tools
    "template_create",
    "template_domains",
    "template_external_shape",
    "template_external_shape_bubble",
    "template_gradient",
    "template_heatmap",
    "template_highlight",
    "template_image",
    "template_labels",
    # template_advanced
    "template_linechart",
    "template_manual",
    "template_meme",
    "template_multi_bar",
    "template_pie",
    "template_placement",
    "template_popup_info",
    "template_prune",
    "template_ranges",
    "template_simple_bar",
    "template_spacing",
    "template_style",
    "template_symbols",
    "template_tanglegram",
    "template_text",
    "template_timescale",
    # template_treeops
    "template_tree_colors",
    "template_validate",
]
