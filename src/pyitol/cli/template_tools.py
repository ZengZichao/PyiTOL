"""Template tools - unified create, bundle, and validate commands."""

import json
from pathlib import Path
from typing import Annotated, Any, Callable, Optional, cast

import pandas as pd
import typer

from pyitol.cli.apps import template_app
from pyitol.cli.common import (
    _apply_config_overrides,
    _assign_colors,
    _common_id_column_option,
    _common_separator_option,
    _common_taxonomy_option,
    _common_tree_option,
    check_output_path,
    get_console,
    load_filtered_taxonomy,
)
from pyitol.cli.template_advanced import (
    template_alignment,
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
from pyitol.cli.template_treeops import (
    _do_collapse,
    template_arrow,
    template_branch_gradient,
    template_highlight,
    template_prune,
    template_ranges,
    template_spacing,
    template_style,
    template_tree_colors,
)
from pyitol.templates.generator import TemplateGenerator
from pyitol.templates.schemas.base import SEPARATOR_MAP, create_schema
from pyitol.utils.color_tools import assign_colors_to_categories
from pyitol.utils.session import SessionContext

_TEMPLATE_TYPE_HELP = """模板类型，可选值:
color-strip, branch, simple-bar, multi-bar, heatmap, symbols, pie, boxplot,
gradient, connections, labels, popup-info, domains, binary, text,
external-shape, tree-colors, branch-gradient, collapse, prune, spacing,
ranges, highlight, style, arrow, linechart, image, alignment, tanglegram,
placement, timescale, meme, manual"""

# Default dataset labels used by the dedicated sub-commands. The unified
# ``template create`` entry point aligns its default label with these values
# so that the two invocation styles produce identical output.
_DEFAULT_LABELS: dict[str, str] = {
    "color-strip": "color_strip",
    "branch": "branch",
    "simple-bar": "simple_bar",
    "multi-bar": "multi_bar",
    "heatmap": "heatmap",
    "symbols": "symbols",
    "pie": "pie",
    "boxplot": "boxplot",
    "gradient": "gradient",
    "connections": "connections",
    "labels": "labels",
    "popup-info": "popup_info",
    "domains": "domains",
    "binary": "binary",
    "text": "text",
    "external-shape": "external_shape",
    "tree-colors": "tree_colors",
    "branch-gradient": "branch_gradient",
    "collapse": "collapse",
    "prune": "prune",
    "spacing": "spacing",
    "ranges": "ranges",
    "highlight": "highlight",
    "style": "style",
    "arrow": "arrows",
    "linechart": "linechart",
    "image": "images",
    "alignment": "alignment",
    "tanglegram": "tanglegram",
    "placement": "placement",
    "timescale": "timescale",
    "meme": "meme",
    "manual": "manual",
}

# =============================================================================
# ``template create`` dispatch table
#
# Previously the unified ``template create`` command contained a 30+ branch
# ``if/elif`` chain that re-checked required arguments and forwarded the
# resolved options to the matching dedicated sub-command.  Every accepted type
# alias (e.g. ``color-strip`` / ``colorstrip``) is now registered, together
# with a small handler, in a single table.  Adding a new template type is a
# one-line registration instead of another branch, and the per-type logic is
# isolated and trivially testable.
# =============================================================================

_CREATE_HANDLERS: dict[str, Callable[["typer.Context", str, str, dict], Any]] = {}


def _register_create(*aliases: str):
    """Register a ``template create`` handler under one or more aliases."""

    def _wrap(fn: Callable[["typer.Context", str, str, dict], Any]):
        for _alias in aliases:
            _CREATE_HANDLERS[_alias] = fn
        return fn

    return _wrap


def _require_args(ctx: typer.Context, type_label: str, needed: str) -> "typer.Exit":
    """Print a missing-argument error and abort the command."""
    console = get_console(ctx)
    console.print(f"[bold red]✗ 类型 '{type_label}' 需要 {needed}[/]")
    raise typer.Exit(1)


@_register_create("color-strip", "colorstrip")
def _h_create_color_strip(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "color-strip", "--taxonomy, --tree 和 --column")
    return template_color_strip(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        colors=kw["colors"],
        label=label,
        strip_width=kw["strip_width"],
        id_column=kw["id_column"],
        separator=kw["separator"],
        palette=kw["palette"],
    )


@_register_create("branch")
def _h_create_branch(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "branch", "--taxonomy, --tree 和 --column")
    return template_branch(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        colors=kw["colors"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("simple-bar", "simplebar", "simple_bar")
def _h_create_simple_bar(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "simple-bar", "--taxonomy, --tree 和 --column")
    return template_simple_bar(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        label=label,
        bar_color=kw["bar_color"],
        bar_width=kw["bar_width"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("multi-bar", "multibar", "multi_bar", "multi-bar-chart", "multibarchart")
def _h_create_multi_bar(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["columns"]):
        _require_args(ctx, "multi-bar", "--taxonomy, --tree 和 --columns")
    return template_multi_bar(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        columns=kw["columns"],
        colors=kw["colors"],
        field_labels=kw["field_labels"],
        label=label,
        width=kw["width"],
        alignment=kw["alignment"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("heatmap")
def _h_create_heatmap(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["columns"]):
        _require_args(ctx, "heatmap", "--taxonomy, --tree 和 --columns")
    return template_heatmap(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        columns=kw["columns"],
        gradient=kw["gradient"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("symbols", "symbol")
def _h_create_symbols(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "symbols", "--taxonomy, --tree 和 --column")
    return template_symbols(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        symbol_type=kw["symbol_type"],
        colors=kw["colors"],
        label=label,
        size=kw["size"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("pie", "piechart")
def _h_create_pie(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["columns"]):
        _require_args(ctx, "pie", "--taxonomy, --tree 和 --columns")
    return template_pie(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        columns=kw["columns"],
        colors=kw["colors"],
        label=label,
        pie_size=kw["pie_size"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("boxplot", "box-plot", "box_plot")
def _h_create_boxplot(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"]):
        _require_args(ctx, "boxplot", "--taxonomy 和 --tree")
    return template_boxplot(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        min_column=kw["min_column"],
        q1_column=kw["q1_column"],
        median_column=kw["median_column"],
        q3_column=kw["q3_column"],
        max_column=kw["max_column"],
        extremes_columns=kw["extremes"],
        label=label,
        color=kw["color"],
        width=kw["width"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("gradient", "color-gradient")
def _h_create_gradient(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "gradient", "--taxonomy, --tree 和 --column")
    return template_gradient(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        color_min=kw["color_min"],
        color_max=kw["color_max"],
        strip_width=kw["strip_width"],
        use_mid_color=kw["use_mid_color"],
        color_mid=kw["color_mid"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("connections", "connection")
def _h_create_connections(ctx, output, label, kw):
    if not kw["connections"]:
        _require_args(ctx, "connections", "--connections")
    return template_connections(
        ctx,
        output=output,
        connections=kw["connections"],
        color=kw["color"],
        line_width=kw["line_width"],
        line_type=kw["line_type"],
        label=label,
        arrow_head_size=kw["arrow_head_size"],
        separator=kw["separator"],
    )


@_register_create("labels", "label")
def _h_create_labels(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"]):
        _require_args(ctx, "labels", "--taxonomy 和 --tree")
    col = kw["label_column"] or kw["column"]
    if not col:
        _require_args(ctx, "labels", "--column 或 --label-column")
    return template_labels(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        label_column=col,
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("popup-info", "popup_info", "popupinfo")
def _h_create_popup_info(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"]):
        _require_args(ctx, "popup-info", "--taxonomy 和 --tree")
    return template_popup_info(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        title_column=kw["title_column"],
        content_column=kw["content_column"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("domains")
def _h_create_domains(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "domains", "--data-file")
    return template_domains(
        ctx,
        output=output,
        data_file=kw["data_file"],
        color=kw["color"],
        scale=kw["scale"],
        label=label,
        separator=kw["separator"],
    )


@_register_create("binary")
def _h_create_binary(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["columns"]):
        _require_args(ctx, "binary", "--taxonomy, --tree 和 --columns")
    return template_binary(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        columns=kw["columns"],
        field_colors=kw["field_colors"],
        field_shapes=kw["field_shapes"],
        label=label,
        color=kw["color"],
        show_internal=kw["show_internal"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("text", "text-label")
def _h_create_text(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "text", "--taxonomy, --tree 和 --column")
    return template_text(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        label=label,
        font_size=kw["font_size"],
        font_style=kw["font_style"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("external-shape", "externalshape", "external_shape")
def _h_create_external_shape(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "external-shape", "--taxonomy, --tree 和 --column")
    return template_external_shape(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        shape_type=kw["shape_type"],
        colors=kw["colors"],
        label=label,
        size=kw["size"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("tree-colors", "tree_colors", "treecolors")
def _h_create_tree_colors(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "tree-colors", "--taxonomy, --tree 和 --column")
    return template_tree_colors(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        colors=kw["colors"],
        label=label,
        color_type=kw["color_type"],
        width_value=kw["width_value"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("branch-gradient", "branch_gradient", "branchgradient")
def _h_create_branch_gradient(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "branch-gradient", "--taxonomy, --tree 和 --column")
    return template_branch_gradient(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        color_min=kw["color_min"],
        color_max=kw["color_max"],
        use_mid_color=kw["use_mid_color"],
        color_mid=kw["color_mid"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("collapse")
def _h_create_collapse(ctx, output, label, kw):
    return _do_collapse(
        ctx,
        output=output,
        node_ids=kw["node_ids"],
        label=label,
        separator=kw["separator"],
        taxon=kw["taxon"],
        rank=kw["rank"],
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        id_column=kw["id_column"],
    )


@_register_create("prune")
def _h_create_prune(ctx, output, label, kw):
    if not kw["node_ids"]:
        _require_args(ctx, "prune", "--node-ids")
    return template_prune(
        ctx,
        output=output,
        node_ids=kw["node_ids"],
        label=label,
        separator=kw["separator"],
    )


@_register_create("spacing")
def _h_create_spacing(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "spacing", "--data-file")
    return template_spacing(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        separator=kw["separator"],
    )


@_register_create("ranges", "range")
def _h_create_ranges(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "ranges", "--taxonomy, --tree 和 --column")
    return template_ranges(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        colors=kw["colors"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("highlight")
def _h_create_highlight(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "highlight", "--taxonomy, --tree 和 --column")
    return template_highlight(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        colors=kw["colors"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("style")
def _h_create_style(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "style", "--taxonomy, --tree 和 --column")
    return template_style(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        style_type=kw["style_type"],
        colors=kw["colors"],
        line_style=kw["line_style"],
        font=kw["font"],
        size=kw["size"],
        label=label,
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("arrow", "arrows")
def _h_create_arrow(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "arrow", "--data-file")
    return template_arrow(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        color=kw["color"],
        arrow_size=kw["arrow_size"],
        separator=kw["separator"],
    )


@_register_create("linechart", "line-chart")
def _h_create_linechart(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"] and kw["column"]):
        _require_args(ctx, "linechart", "--taxonomy, --tree 和 --column")
    return template_linechart(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        column=kw["column"],
        position_column=kw["position_column"],
        label=label,
        color=kw["color"],
        line_width=kw["line_width"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("image", "images")
def _h_create_image(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"]):
        _require_args(ctx, "image", "--taxonomy 和 --tree")
    img_col = kw["image_column"] or kw["column"]
    if not img_col:
        _require_args(ctx, "image", "--column 或 --image-column")
    return template_image(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        image_column=img_col,
        url_column=cast(str, kw["url_column"]),
        label=label,
        image_width=kw["image_width"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("alignment")
def _h_create_alignment(ctx, output, label, kw):
    if not (kw["taxonomy"] and kw["tree"]):
        _require_args(ctx, "alignment", "--taxonomy 和 --tree")
    align_col = kw["alignment_column"] or kw["column"]
    if not align_col:
        _require_args(ctx, "alignment", "--column 或 --alignment-column")
    return template_alignment(
        ctx,
        output=output,
        taxonomy_path=kw["taxonomy"],
        tree_path=kw["tree"],
        alignment_column=align_col,
        label=label,
        color_scheme=kw["color_scheme"],
        id_column=kw["id_column"],
        separator=kw["separator"],
    )


@_register_create("tanglegram")
def _h_create_tanglegram(ctx, output, label, kw):
    if not kw["connections"]:
        _require_args(ctx, "tanglegram", "--connections")
    return template_tanglegram(
        ctx,
        output=output,
        connections=kw["connections"],
        label=label,
        color=kw["color"],
        line_width=kw["line_width"],
        separator=kw["separator"],
    )


@_register_create("placement")
def _h_create_placement(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "placement", "--data-file")
    return template_placement(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        color=kw["color"],
        spacing=kw["spacing"],
        separator=kw["separator"],
    )


@_register_create("timescale")
def _h_create_timescale(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "timescale", "--data-file")
    return template_timescale(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        color=kw["color"],
        scale_position=kw["scale_position"],
        separator=kw["separator"],
    )


@_register_create("meme")
def _h_create_meme(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "meme", "--data-file")
    return template_meme(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        color=kw["color"],
        show_labels=kw["show_labels"],
        separator=kw["separator"],
    )


@_register_create("manual")
def _h_create_manual(ctx, output, label, kw):
    if not kw["data_file"]:
        _require_args(ctx, "manual", "--data-file")
    return template_manual(
        ctx,
        output=output,
        data_file=kw["data_file"],
        label=label,
        color=kw["color"],
        custom_header=kw["custom_header"],
        separator=kw["separator"],
    )


@template_app.command("create")
def template_create(
    ctx: typer.Context,
    template_type: Annotated[str, typer.Argument(help=_TEMPLATE_TYPE_HELP)],
    output: Annotated[str, typer.Option("--output", "-o", help="输出模板文件路径")] = "config_template.txt",
    taxonomy: Annotated[Optional[str], typer.Option("--taxonomy", "-t", help="分类信息表格文件路径")] = None,
    tree: Annotated[Optional[str], typer.Option("--tree", "-r", help="Newick格式系统发育树文件路径")] = None,
    column: Annotated[Optional[str], typer.Option("--column", "-c", help="数据列名")] = None,
    columns: Annotated[Optional[str], typer.Option("--columns", help="多个数据列名,逗号分隔")] = None,
    colors: Annotated[Optional[str], typer.Option("--colors", help="自定义颜色映射JSON或列表")] = None,
    label: Annotated[str, typer.Option("--label", "-l", help="数据集标签")] = "dataset",
    id_column: Annotated[str, typer.Option("--id-column", help="ID列名")] = "id",
    separator: Annotated[str, typer.Option("--separator", "-s", help="数据分隔符: TAB/SPACE/COMMA")] = "TAB",
    palette: Annotated[Optional[str], typer.Option("--palette", help="配色预设")] = None,
    # Type-specific options
    strip_width: Annotated[str, typer.Option("--strip-width", help="色带宽度")] = "50",
    bar_color: Annotated[str, typer.Option("--bar-color", help="柱状图颜色")] = "#3c5484",
    bar_width: Annotated[str, typer.Option("--bar-width", help="柱状图宽度")] = "50",
    field_labels: Annotated[Optional[str], typer.Option("--field-labels", help="字段标签,逗号分隔")] = None,
    width: Annotated[str, typer.Option("--width", help="图表宽度")] = "1000",
    alignment: Annotated[str, typer.Option("--alignment", help="对齐方式")] = "center",
    gradient: Annotated[Optional[str], typer.Option("--gradient", help="颜色渐变,逗号分隔的色值")] = None,
    symbol_type: Annotated[str, typer.Option("--symbol-type", help="符号类型")] = "diamond",
    size: Annotated[str, typer.Option("--size", help="符号/形状大小")] = "30",
    pie_size: Annotated[str, typer.Option("--pie-size", help="饼图大小")] = "50",
    min_column: Annotated[str, typer.Option("--min", help="最小值列名")] = "minimum",
    q1_column: Annotated[str, typer.Option("--q1", help="第一四分位数列名")] = "q1",
    median_column: Annotated[str, typer.Option("--median", help="中位数列名")] = "median",
    q3_column: Annotated[str, typer.Option("--q3", help="第三四分位数列名")] = "q3",
    max_column: Annotated[str, typer.Option("--max", help="最大值列名")] = "maximum",
    extremes: Annotated[Optional[str], typer.Option("--extremes", help="极端值列名,逗号分隔")] = None,
    color_min: Annotated[str, typer.Option("--color-min", help="最小值颜色")] = "#ff0000",
    color_max: Annotated[str, typer.Option("--color-max", help="最大值颜色")] = "#0000ff",
    use_mid_color: Annotated[bool, typer.Option("--use-mid-color", help="使用中间颜色")] = False,
    color_mid: Annotated[str, typer.Option("--color-mid", help="中间颜色")] = "#ffff00",
    connections: Annotated[Optional[str], typer.Option("--connections", help="连接数据(文件路径或逗号分隔对)")] = None,
    color: Annotated[str, typer.Option("--color", help="默认颜色")] = "#ff0000",
    line_width: Annotated[str, typer.Option("--line-width", help="连线/线条宽度")] = "2",
    line_type: Annotated[str, typer.Option("--line-type", help="连线类型: solid/dotted/dashed")] = "solid",
    arrow_head_size: Annotated[str, typer.Option("--arrow-head-size", help="箭头大小")] = "1",
    label_column: Annotated[Optional[str], typer.Option("--label-column", help="标签列名")] = None,
    title_column: Annotated[str, typer.Option("--title-column", help="标题列名")] = "title",
    content_column: Annotated[str, typer.Option("--content-column", help="内容列名")] = "content",
    data_file: Annotated[Optional[str], typer.Option("--data-file", "-d", help="数据文件路径")] = None,
    scale: Annotated[Optional[str], typer.Option("--scale", help="尺度")] = None,
    field_colors: Annotated[str, typer.Option("--field-colors", help="字段颜色,逗号分隔")] = "#ff0000,#00ff00,#0000ff",
    field_shapes: Annotated[str, typer.Option("--field-shapes", help="字段形状,逗号分隔(1-6)")] = "1,2,3",
    show_internal: Annotated[str, typer.Option("--show-internal", help="是否显示内部节点: 0/1")] = "1",
    font_size: Annotated[str, typer.Option("--font-size", help="字体大小")] = "12",
    font_style: Annotated[str, typer.Option("--font-style", help="字体样式")] = "normal",
    shape_type: Annotated[str, typer.Option("--shape-type", help="形状类型")] = "circle",
    color_type: Annotated[
        str, typer.Option("--color-type", help="着色类型: clade/label/branch/width/range/gradient")
    ] = "clade",
    width_value: Annotated[str, typer.Option("--width-value", help="分支线宽度(仅width类型)")] = "3",
    node_ids: Annotated[Optional[str], typer.Option("--node-ids", "-n", help="节点ID,逗号分隔")] = None,
    style_type: Annotated[str, typer.Option("--style-type", help="样式类型: branch/label/label_background")] = "branch",
    line_style: Annotated[str, typer.Option("--line-style", help="线型: normal/dashed/dotted")] = "normal",
    font: Annotated[str, typer.Option("--font", help="字体名称")] = "Arial",
    arrow_size: Annotated[str, typer.Option("--arrow-size", help="箭头大小")] = "30",
    image_column: Annotated[Optional[str], typer.Option("--image-column", help="图像文件名列名")] = None,
    url_column: Annotated[Optional[str], typer.Option("--url-column", help="图像URL列名")] = None,
    image_width: Annotated[str, typer.Option("--image-width", help="图像宽度")] = "50",
    alignment_column: Annotated[Optional[str], typer.Option("--alignment-column", help="序列比对列名")] = None,
    position_column: Annotated[
        Optional[str], typer.Option("--position-column", "-p", help="折线图位置列名(默认行号)")
    ] = None,
    color_scheme: Annotated[str, typer.Option("--color-scheme", help="颜色方案: nucleotide/amino_acid")] = "nucleotide",
    spacing: Annotated[str, typer.Option("--spacing", help="放置点间距/节点间距因子")] = "5",
    scale_position: Annotated[str, typer.Option("--scale-position", help="刻度位置: top/bottom/both")] = "bottom",
    show_labels: Annotated[str, typer.Option("--show-labels", help="是否显示标签: 0/1")] = "1",
    custom_header: Annotated[Optional[str], typer.Option("--custom-header", help="自定义头部JSON")] = None,
    taxon: Annotated[Optional[str], typer.Option("--taxon", help="类群名称(用于collapse)")] = None,
    rank: Annotated[Optional[str], typer.Option("--rank", help="分类等级(用于collapse)")] = None,
    force: Annotated[bool, typer.Option("--force", "-f", help="覆盖已存在的输出文件")] = False,
    no_clobber: Annotated[bool, typer.Option("--no-clobber", help="跳过已存在的输出文件")] = False,
):
    """统一入口：根据类型创建 iTOL 模板文件。"""
    # Apply config file overrides (CLI > config > default)
    overrides = _apply_config_overrides(
        ctx,
        output=(output, "config_template.txt"),
        tree=(tree, None),
        taxonomy=(taxonomy, None),
        column=(column, None),
        columns=(columns, None),
        label=(label, "dataset"),
        id_column=(id_column, "id"),
        separator=(separator, "TAB"),
        palette=(palette, None),
        colors=(colors, None),
        strip_width=(strip_width, "50"),
        bar_color=(bar_color, "#3c5484"),
        bar_width=(bar_width, "50"),
        width=(width, "1000"),
        alignment=(alignment, "center"),
        gradient=(gradient, None),
        symbol_type=(symbol_type, "diamond"),
        size=(size, "30"),
        pie_size=(pie_size, "50"),
        color=(color, "#ff0000"),
        line_width=(line_width, "2"),
        line_type=(line_type, "solid"),
        show_internal=(show_internal, "1"),
        font_size=(font_size, "12"),
        font_style=(font_style, "normal"),
        shape_type=(shape_type, "circle"),
        color_type=(color_type, "clade"),
        width_value=(width_value, "3"),
        style_type=(style_type, "branch"),
        line_style=(line_style, "normal"),
        font=(font, "Arial"),
        arrow_size=(arrow_size, "30"),
        color_scheme=(color_scheme, "nucleotide"),
        spacing=(spacing, "5"),
        scale_position=(scale_position, "bottom"),
        show_labels=(show_labels, "1"),
        node_ids=(node_ids, None),
        taxon=(taxon, None),
        rank=(rank, None),
        data_file=(data_file, None),
        position_column=(position_column, None),
    )
    output = overrides["output"]
    tree = overrides["tree"]
    taxonomy = overrides["taxonomy"]
    column = overrides["column"]
    columns = overrides["columns"]
    label = overrides["label"]
    id_column = overrides["id_column"]
    separator = overrides["separator"]
    palette = overrides["palette"]
    colors = overrides["colors"]
    strip_width = overrides["strip_width"]
    bar_color = overrides["bar_color"]
    bar_width = overrides["bar_width"]
    width = overrides["width"]
    alignment = overrides["alignment"]
    gradient = overrides["gradient"]
    symbol_type = overrides["symbol_type"]
    size = overrides["size"]
    pie_size = overrides["pie_size"]
    color = overrides["color"]
    line_width = overrides["line_width"]
    line_type = overrides["line_type"]
    show_internal = overrides["show_internal"]
    font_size = overrides["font_size"]
    font_style = overrides["font_style"]
    shape_type = overrides["shape_type"]
    color_type = overrides["color_type"]
    width_value = overrides["width_value"]
    style_type = overrides["style_type"]
    line_style = overrides["line_style"]
    font = overrides["font"]
    arrow_size = overrides["arrow_size"]
    color_scheme = overrides["color_scheme"]
    spacing = overrides["spacing"]
    scale_position = overrides["scale_position"]
    show_labels = overrides["show_labels"]
    node_ids = overrides["node_ids"]
    taxon = overrides["taxon"]
    rank = overrides["rank"]
    data_file = overrides["data_file"]
    position_column = overrides["position_column"]

    t = template_type.lower().replace("_", "-")

    # Align default label with the dedicated sub-command defaults so that
    # ``template create <type>`` and ``template create-<type>`` produce the
    # same output when the user does not explicitly set --label.
    if label == "dataset":
        label = _DEFAULT_LABELS.get(t, label)

    console = get_console(ctx)

    # Check output file protection
    output_path = check_output_path(output, force=force, no_clobber=no_clobber)
    if output_path is None:
        return  # Skip if --no-clobber and file exists

    # Thread --force / --no-clobber down to the dispatched sub-command, which
    # re-checks the (same) output path. Without this, `template create --force`
    # would still fail because the sub-command re-checked without force.
    if ctx.obj:
        ctx.obj["_cli_force"] = force
        ctx.obj["_cli_no_clobber"] = no_clobber

    # Bundle every resolved option into a single dictionary so that the
    # registered handlers can pull exactly what they need without a long
    # positional argument list.
    kw: dict[str, Any] = {
        "taxonomy": taxonomy,
        "tree": tree,
        "column": column,
        "columns": columns,
        "label": label,
        "id_column": id_column,
        "separator": separator,
        "palette": palette,
        "colors": colors,
        "strip_width": strip_width,
        "bar_color": bar_color,
        "bar_width": bar_width,
        "width": width,
        "alignment": alignment,
        "gradient": gradient,
        "symbol_type": symbol_type,
        "size": size,
        "pie_size": pie_size,
        "color": color,
        "line_width": line_width,
        "line_type": line_type,
        "arrow_head_size": arrow_head_size,
        "label_column": label_column,
        "title_column": title_column,
        "content_column": content_column,
        "connections": connections,
        "data_file": data_file,
        "scale": scale,
        "field_colors": field_colors,
        "field_shapes": field_shapes,
        "show_internal": show_internal,
        "font_size": font_size,
        "font_style": font_style,
        "shape_type": shape_type,
        "color_type": color_type,
        "width_value": width_value,
        "node_ids": node_ids,
        "style_type": style_type,
        "line_style": line_style,
        "font": font,
        "arrow_size": arrow_size,
        "image_column": image_column,
        "url_column": url_column,
        "image_width": image_width,
        "alignment_column": alignment_column,
        "position_column": position_column,
        "color_scheme": color_scheme,
        "spacing": spacing,
        "scale_position": scale_position,
        "show_labels": show_labels,
        "custom_header": custom_header,
        "taxon": taxon,
        "rank": rank,
        "use_mid_color": use_mid_color,
        "color_min": color_min,
        "color_max": color_max,
        "color_mid": color_mid,
        "extremes": extremes,
        "min_column": min_column,
        "q1_column": q1_column,
        "median_column": median_column,
        "q3_column": q3_column,
        "max_column": max_column,
        "field_labels": field_labels,
    }

    handler = _CREATE_HANDLERS.get(t)
    if handler is None:
        console.print(f"[bold red]✗ 未知模板类型: {template_type}[/]")
        raise typer.Exit(1)
    return handler(ctx, output, label, kw)


@template_app.command("bundle")
def template_bundle(
    ctx: typer.Context,
    output_dir: str = typer.Option(..., "--output-dir", "-o", help="输出目录"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    config: str = typer.Option(
        ..., "--config", "-c", help='打包配置JSON: [{"type":"color-strip","column":"Phylum"}, ...]'
    ),
    prefix: str = typer.Option("", "--prefix", help="文件名前缀"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """一键打包生成多个可视化模板文件。支持全部标准数据集类型。"""
    console = get_console(ctx)
    try:
        bundle_cfg = json.loads(config)
    except json.JSONDecodeError as e:
        console.print(f"[bold red]✗ 配置JSON格式错误: {e}[/]")
        raise typer.Exit(1)

    _, df, _, tip_order_map = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)

    gen = TemplateGenerator()
    for item in bundle_cfg:
        btype = item.get("type", "")
        column = item.get("column", "")
        blabel = item.get("label", f"{btype}_{column}")
        helper = _BUNDLE_HANDLERS.get(btype)
        if helper is None:
            console.print(f"[bold yellow]⚠ 忽略未知类型: {btype}[/]")
            continue
        helper(gen, df, item, column, blabel, separator, tip_order_map, console)

    paths = gen.write_multiple(output_dir, prefix=prefix)
    for p in paths:
        console.print(f"[bold green]✓ 模板已生成: {p}[/]")
    SessionContext().save_snapshot(generated_files=cast(list, paths))


# =============================================================================
# ``template bundle`` per-type generators
#
# The former monolithic ``if/elif`` chain (one branch per dataset type) is split
# into one small helper per type.  Each helper builds a single schema from one
# bundle spec item and appends it to the shared ``TemplateGenerator``.  The
# logic is preserved verbatim so the generated templates are byte-for-byte
# identical to the previous implementation; only the structure is de-duplicated.
# =============================================================================

_BUNDLE_HANDLERS: dict[str, Callable] = {}


def _register_bundle(*aliases: str):
    """Register a ``template bundle`` generator under one or more aliases."""

    def _wrap(fn: Callable):
        for _alias in aliases:
            _BUNDLE_HANDLERS[_alias] = fn
        return fn

    return _wrap


def _bundle_load_data_file(data_file, console, btype):
    """Read an external CSV into a list of row dicts, or warn and return None."""
    if data_file and Path(data_file).exists():
        ddf = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
        return [dict(row) for _, row in ddf.iterrows()]
    console.print(f"[bold yellow]⚠ {btype} 需要提供 data_file 参数且文件存在，已跳过[/]")
    return None


@_register_bundle("color-strip", "colorstrip")
def _bundle_color_strip(gen, df, item, column, blabel, separator, tip_order_map, console):
    colors = item.get("colors")
    schema = create_schema("color_strip", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, colors)
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "value": val, "color": colors_dict.get(val, "#999999")})
        schema.columns = ["id", "value", "color"]
        schema.data_rows = data
        schema.parameters["STRIP_WIDTH"] = item.get("strip_width", "50")
    gen.add_schema(schema)


@_register_bundle("tree-colors", "tree_colors", "branch")
def _bundle_tree_colors(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("tree_colors", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append(
                {"id": row["id"], "type": item.get("color_type", "clade"), "color": colors_dict.get(val, "#999999")}
            )
        schema.columns = ["id", "type", "color"]
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("branch-gradient", "branch_gradient")
def _bundle_branch_gradient(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("gradient", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            try:
                float(val)
            except ValueError:
                continue
            data.append({"id": row["id"], "value": val, "color": "#999999"})
        schema.columns = ["id", "value", "color"]
        schema.data_rows = data
        schema.parameters["COLOR_MIN"] = item.get("color_min", "#ff0000")
        schema.parameters["COLOR_MAX"] = item.get("color_max", "#0000ff")
        if item.get("use_mid_color"):
            schema.parameters["USE_MID_COLOR"] = "1"
            schema.parameters["COLOR_MID"] = item.get("color_mid", "#ffff00")
    gen.add_schema(schema)


@_register_bundle("symbols", "symbol")
def _bundle_symbols(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("symbols", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        symbol_type = item.get("symbol_type", "diamond")
        size = item.get("size", "30")
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append(
                {
                    "id": row["id"],
                    "type": symbol_type,
                    "value": size,
                    "color": colors_dict.get(val, "#999999"),
                    "label": val,
                }
            )
        schema.columns = ["id", "type", "value", "color", "label"]
        schema.data_rows = data
        schema.parameters["MAXIMUM_SIZE"] = size
    gen.add_schema(schema)


@_register_bundle("external-shape", "externalshape")
def _bundle_external_shape(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("externalshape", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        shape_type = item.get("shape_type", "circle")
        size = item.get("size", "20")
        shape_map = {
            "circle": "1",
            "square": "2",
            "star": "3",
            "triangle_right": "4",
            "triangle_left": "5",
            "checkmark": "6",
        }
        shape_code = shape_map.get(shape_type, "1")
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append(
                {
                    "id": row["id"],
                    "type": shape_code,
                    "value": size,
                    "color": colors_dict.get(val, "#999999"),
                    "label": val,
                }
            )
        schema.columns = ["id", "type", "value", "color", "label"]
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("highlight")
def _bundle_highlight(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("style", label=blabel, color="#ff0000", separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "type": "label_background", "color": colors_dict.get(val, "#999999")})
        schema.columns = ["id", "type", "color"]
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("ranges", "range")
def _bundle_ranges(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("range", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        data = []
        for group_name, group_df in df.groupby(column):
            members = [m for m in group_df["id"].tolist() if m in tip_order_map]
            members = sorted(members, key=lambda x: tip_order_map.get(x, 0))
            if len(members) >= 2:
                data.append(
                    {
                        "id": f"{members[0]}|{members[-1]}",
                        "label": group_name,
                        "color": colors_dict.get(group_name, "#999999"),
                    }
                )
            elif len(members) == 1:
                data.append({"id": members[0], "label": group_name, "color": colors_dict.get(group_name, "#999999")})
        schema.columns = ["id", "label", "color"]
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("labels", "label")
def _bundle_labels(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("labels", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "label": str(val)})
        schema.columns = ["id", "label"]
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("popup-info", "popup_info")
def _bundle_popup_info(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("popup_info", label=blabel, separator=separator)
    title_col = item.get("title_column", "title")
    content_col = item.get("content_column", "content")
    data = []
    for _, row in df.iterrows():
        title_val = row.get(title_col, "")
        content_val = row.get(content_col, "")
        data.append(
            {
                "id": row["id"],
                "title": "" if pd.isna(title_val) else str(title_val),
                "content": "" if pd.isna(content_val) else str(content_val),
            }
        )
    schema.columns = ["id", "title", "content"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("simple-bar", "simplebar", "simple_bar")
def _bundle_simple_bar(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("simple_bar", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            try:
                float(val)
            except ValueError:
                continue
            data.append({"id": row["id"], "bar_height": val})
        schema.columns = ["id", "bar_height"]
        schema.data_rows = data
        schema.parameters["WIDTH"] = item.get("width", "50")
        schema.parameters["COLOR"] = item.get("color", "#3c5484")
    gen.add_schema(schema)


@_register_bundle("multi-bar", "multibar", "multi_bar")
def _bundle_multi_bar(gen, df, item, column, blabel, separator, tip_order_map, console):
    cols = item.get("columns", [column])
    schema = create_schema("multi_bar", label=blabel, separator=separator)
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for vc in cols:
            row_data[vc] = "" if pd.isna(row.get(vc, "")) else str(row.get(vc, ""))
        data.append(row_data)
    schema.columns = ["id", *cols]
    schema.data_rows = data
    schema.parameters["WIDTH"] = item.get("width", "1000")
    field_labels = item.get("field_labels", cols)
    field_colors = item.get("field_colors", ["#e64b35", "#4dbbd5", "#00a087", "#3c5484", "#f39b7f"])
    sep_char = SEPARATOR_MAP.get(separator.upper(), "\t")
    schema.parameters["FIELD_LABELS"] = sep_char.join(field_labels)
    schema.parameters["FIELD_COLORS"] = sep_char.join(field_colors[: len(cols)])
    gen.add_schema(schema)


@_register_bundle("heatmap")
def _bundle_heatmap(gen, df, item, column, blabel, separator, tip_order_map, console):
    cols = item.get("columns", [column])
    schema = create_schema("heatmap", label=blabel, separator=separator)
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for vc in cols:
            row_data[vc] = "" if pd.isna(row.get(vc, "")) else str(row.get(vc, ""))
        data.append(row_data)
    schema.columns = ["id", *cols]
    schema.data_rows = data
    color_gradient = item.get("color_gradient", ["#ff0000", "#ffffff", "#0000ff"])
    schema.parameters["COLOR_MIN"] = color_gradient[0]
    if len(color_gradient) > 2:
        schema.parameters["COLOR_MID"] = color_gradient[1]
        schema.parameters["COLOR_MAX"] = color_gradient[-1]
        schema.parameters["USE_MID_COLOR"] = "1"
    else:
        schema.parameters["COLOR_MAX"] = color_gradient[-1]
    gen.add_schema(schema)


@_register_bundle("pie", "piechart")
def _bundle_pie(gen, df, item, column, blabel, separator, tip_order_map, console):
    cols = item.get("columns", [column])
    schema = create_schema("pie", label=blabel, separator=separator)
    colors = item.get("colors", list(assign_colors_to_categories([str(i) for i in range(len(cols))]).values()))
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for i, vc in enumerate(cols):
            val = row.get(vc, "")
            row_data[f"pie_{i + 1}"] = "0" if pd.isna(val) else val
            if i < len(colors):
                row_data[f"color_{i + 1}"] = colors[i]
        data.append(row_data)
    pie_cols = [f"pie_{i + 1}" for i in range(len(cols))]
    color_cols = [f"color_{i + 1}" for i in range(len(cols))]
    schema.columns = ["id", *pie_cols, *color_cols]
    schema.data_rows = data
    schema.parameters["MAXIMUM_SIZE"] = item.get("pie_size", "50")
    sep_char = SEPARATOR_MAP.get(separator.upper(), "\t")
    schema.parameters["FIELD_LABELS"] = sep_char.join(cols)
    schema.parameters["FIELD_COLORS"] = sep_char.join(colors[: len(cols)])
    gen.add_schema(schema)


@_register_bundle("gradient", "color-gradient")
def _bundle_gradient(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("gradient", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            try:
                float(val)
            except ValueError:
                continue
            data.append({"id": row["id"], "value": val})
        schema.columns = ["id", "value"]
        schema.data_rows = data
        schema.parameters["STRIP_WIDTH"] = item.get("strip_width", "25")
        schema.parameters["COLOR_MIN"] = item.get("color_min", "#ff0000")
        schema.parameters["COLOR_MAX"] = item.get("color_max", "#0000ff")
        if item.get("use_mid_color"):
            schema.parameters["USE_MID_COLOR"] = "1"
            schema.parameters["COLOR_MID"] = item.get("color_mid", "#ffff00")
    gen.add_schema(schema)


@_register_bundle("text", "text-label")
def _bundle_text(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("text", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val) or str(val).strip() == "":
                continue
            data.append({"id": row["id"], "text": str(val)})
        schema.columns = ["id", "text"]
        schema.data_rows = data
        schema.parameters["LABEL_SIZE_FACTOR"] = item.get("font_size", "12")
    gen.add_schema(schema)


@_register_bundle("boxplot")
def _bundle_boxplot(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("boxplot", label=blabel, separator=separator)
    min_c = item.get("min_column", "minimum")
    q1_c = item.get("q1_column", "q1")
    median_c = item.get("median_column", "median")
    q3_c = item.get("q3_column", "q3")
    max_c = item.get("max_column", "maximum")
    cols = ["id", min_c, q1_c, median_c, q3_c, max_c]
    data = []
    for _, row in df.iterrows():
        data.append({c: row.get(c, "") for c in cols})
    schema.columns = cols
    schema.data_rows = data
    schema.parameters["WIDTH"] = item.get("width", "1500")
    schema.parameters["COLOR"] = item.get("color", "#00ff00")
    gen.add_schema(schema)


@_register_bundle("linechart")
def _bundle_linechart(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("linechart", label=blabel, separator=separator)
    pos_col = item.get("position_column")
    has_pos = pos_col is not None and pos_col in df.columns
    if column in df.columns:
        data = []
        for i, (_, row) in enumerate(df.iterrows()):
            val = row[column]
            if pd.isna(val):
                continue
            pos_val = str(row[pos_col]) if has_pos and not pd.isna(row[pos_col]) else str(i)
            data.append({"id": row["id"], "position": pos_val, "value": str(val)})
        schema.columns = ["id", "position", "value"]
        schema.data_rows = data
        schema.parameters["LINE_WIDTH"] = item.get("line_width", "2")
        schema.parameters["COLOR"] = item.get("color", "#3c5484")
    gen.add_schema(schema)


@_register_bundle("image")
def _bundle_image(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("image", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append(
                {"id": row["id"], "image_file": str(val), "image_url": str(row.get(item.get("url_column"), ""))}
            )
        schema.columns = ["id", "image_file", "image_url"]
        schema.data_rows = data
        schema.parameters["MAXIMUM_SIZE"] = item.get("image_width", "50")
    gen.add_schema(schema)


@_register_bundle("alignment")
def _bundle_alignment(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("alignment", label=blabel, separator=separator)
    if column in df.columns:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "alignment": str(val)})
        schema.columns = ["id", "alignment"]
        schema.data_rows = data
        schema.parameters["COLOR_SCHEME"] = item.get("color_scheme", "nucleotide")
    gen.add_schema(schema)


@_register_bundle("binary")
def _bundle_binary(gen, df, item, column, blabel, separator, tip_order_map, console):
    cols = item.get("columns", [column])
    schema = create_schema("binary", label=blabel, separator=separator)
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for col in cols:
            row_data[col] = "1" if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "" else "0"
        data.append(row_data)
    schema.columns = ["id", *cols]
    schema.data_rows = data
    field_colors = item.get("field_colors", ["#ff0000", "#00ff00", "#0000ff"])
    field_shapes = item.get("field_shapes", ["1", "2", "3"])
    schema.parameters["FIELD_COLORS"] = SEPARATOR_MAP.get(separator.upper(), "\t").join(field_colors[: len(cols)])
    schema.parameters["FIELD_SHAPES"] = SEPARATOR_MAP.get(separator.upper(), "\t").join(field_shapes[: len(cols)])
    schema.parameters["SHOW_INTERNAL"] = item.get("show_internal", "1")
    gen.add_schema(schema)


@_register_bundle("collapse")
def _bundle_collapse(gen, df, item, column, blabel, separator, tip_order_map, console):
    node_ids = item.get("node_ids", [])
    schema = create_schema("collapse", label=blabel, separator=separator)
    data = [{"id": nid} for nid in node_ids]
    schema.columns = ["id"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("prune")
def _bundle_prune(gen, df, item, column, blabel, separator, tip_order_map, console):
    node_ids = item.get("node_ids", [])
    schema = create_schema("prune", label=blabel, separator=separator)
    data = [{"id": nid} for nid in node_ids]
    schema.columns = ["id"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("spacing")
def _bundle_spacing(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("spacing", label=blabel, separator=separator)
    node_ids = item.get("node_ids", [])
    factors = item.get("factors", ["1.0"] * len(node_ids))
    data = [{"id": nid, "factor": f} for nid, f in zip(node_ids, factors)]
    schema.columns = ["id", "factor"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("style")
def _bundle_style(gen, df, item, column, blabel, separator, tip_order_map, console):
    schema = create_schema("style", label=blabel, separator=separator)
    if column in df.columns:
        colors_dict = _assign_colors(df, column, item.get("colors"))
        style_type = item.get("style_type", "branch")
        line_style = item.get("line_style", "normal")
        font = item.get("font", "Arial")
        size = item.get("size", "1")
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            color = colors_dict.get(val, "#999999")
            if style_type == "branch":
                data.append({"id": row["id"], "type": "branch", "color": color, "style": line_style, "size": size})
            elif style_type == "label":
                data.append({"id": row["id"], "type": "label", "color": color, "font": font, "size": size})
            elif style_type == "label_background":
                data.append({"id": row["id"], "type": "label_background", "color": color})
        schema.columns = (
            ["id", "type", "color", "style", "size"]
            if style_type == "branch"
            else ["id", "type", "color", "font", "size"]
            if style_type == "label"
            else ["id", "type", "color"]
        )
        schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("connections", "connection")
def _bundle_connections(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "connections")
    if data is None:
        return
    schema = create_schema("connection", label=blabel, separator=separator)
    schema.columns = ["id1", "id2", "color", "width", "type"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("tanglegram")
def _bundle_tanglegram(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "tanglegram")
    if data is None:
        return
    schema = create_schema("tanglegram", label=blabel, separator=separator)
    schema.columns = ["id1", "id2", "color", "width"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("domains")
def _bundle_domains(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "domains")
    if data is None:
        return
    schema = create_schema("domains", label=blabel, separator=separator)
    schema.columns = ["id", "from", "to", "type", "color"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("arrows", "arrow")
def _bundle_arrows(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "arrows")
    if data is None:
        return
    schema = create_schema("arrows", label=blabel, separator=separator)
    schema.columns = ["id", "position", "direction", "color"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("placement")
def _bundle_placement(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "placement")
    if data is None:
        return
    schema = create_schema("placement", label=blabel, separator=separator)
    schema.columns = ["id", "position", "count", "color"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("timescale")
def _bundle_timescale(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "timescale")
    if data is None:
        return
    schema = create_schema("timescale", label=blabel, separator=separator)
    schema.columns = ["time_point", "label", "color"]
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("manual")
def _bundle_manual(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "manual")
    if data is None:
        return
    schema = create_schema("manual", label=blabel, separator=separator)
    if data:
        schema.columns = list(data[0].keys())
    schema.data_rows = data
    gen.add_schema(schema)


@_register_bundle("meme")
def _bundle_meme(gen, df, item, column, blabel, separator, tip_order_map, console):
    data = _bundle_load_data_file(item.get("data_file"), console, "meme")
    if data is None:
        return
    schema = create_schema("meme", label=blabel, separator=separator)
    schema.columns = ["id", "start", "end", "name", "color"]
    schema.data_rows = data
    gen.add_schema(schema)


@template_app.command("validate")
def template_validate(
    ctx: typer.Context,
    template_file: str = typer.Option(..., "--template", "-t", help="模板文件路径"),
):
    """验证 iTOL 模板文件格式是否正确。"""
    console = get_console(ctx)
    from pyitol.templates.learner import learn_template

    try:
        result = learn_template(template_file)
        datasets = result.get("datasets", [])
        if not datasets:
            console.print("[bold yellow]⚠ 未检测到数据集，模板可能为空或格式异常[/]")
            raise typer.Exit(1)

        all_ok = True
        for i, ds in enumerate(datasets):
            ds_type = ds.get("type", "unknown")
            errors = ds.get("validation_errors", [])
            params = ds.get("parameters", {})
            data = ds.get("data", [])

            if errors:
                console.print(f"[bold red]✗ 数据集 {i + 1} ({ds_type}): {len(errors)} 个错误[/]")
                for e in errors:
                    console.print(f"    {e}")
                all_ok = False
            else:
                console.print(f"[bold green]✓ 数据集 {i + 1} ({ds_type}): 格式正确[/]")
            console.print(f"  参数: {len(params)} 个, 数据行: {len(data)} 行")

        if all_ok:
            console.print("[bold green]✓ 模板验证全部通过[/]")
        else:
            console.print("[bold red]✗ 模板验证失败，请修正上述错误[/]")
            raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]✗ 验证失败: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# TAXONOMY COMMANDS
# =============================================================================
