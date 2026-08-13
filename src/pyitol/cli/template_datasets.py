"""Template dataset commands - color strip, bar, heatmap, symbols, pie, etc."""

import json
from pathlib import Path
from typing import Optional, cast

import typer

from pyitol.cli.apps import template_app
from pyitol.cli.common import (
    _common_id_column_option,
    _common_label_option,
    _common_output_option,
    _common_separator_option,
    _common_taxonomy_option,
    _common_tree_option,
    _parse_colors,
    get_console,
    load_filtered_taxonomy,
    resolve_output_path,
    validate_input_paths,
)
from pyitol.templates.generator import (
    generate_binary_template,
    generate_boxplot_template,
    generate_branch_template,
    generate_color_strip_template,
    generate_connection_template,
    generate_domain_template,
    generate_external_shape_template,
    generate_gradient_template,
    generate_heatmap_template,
    generate_labels_template,
    generate_multibar_template,
    generate_pie_template,
    generate_popup_info_template,
    generate_simple_bar_template,
    generate_symbols_template,
    generate_text_template,
)
from pyitol.utils.session import SessionContext


@template_app.command("create-color-strip")
def template_color_strip(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于分类的列名"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("color_strip"),
    strip_width: str = typer.Option("50", "--strip-width", help="色带宽度"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
    palette: str = typer.Option(None, "--palette", help="配色预设: nature/cell/colorblind 的子集名"),
    # NOTE: palette parameter reserved for future use
):
    """生成色带模板 - 根据分类信息为末端分支添加色带注释。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_dict = _parse_colors(colors)
    path = generate_color_strip_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        color_dict,
        label,
        id_column,
        strip_width,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 色带配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-branch")
def template_branch(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于分支着色的列名"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("branch"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成分支着色模板 - 根据分类信息为分支着色。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_dict = _parse_colors(colors)
    path = generate_branch_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        color_dict,
        label,
        id_column,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 分支着色配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-simple-bar")
def template_simple_bar(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="数值列名"),
    label: str = _common_label_option("simple_bar"),
    bar_color: str = typer.Option("#3c5484", "--bar-color", help="柱状图颜色"),
    bar_width: str = typer.Option("50", "--bar-width", help="柱状图宽度"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成单值柱状图模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    path = generate_simple_bar_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        label,
        id_column,
        bar_color,
        bar_width,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 单值柱状图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-multi-bar")
def template_multi_bar(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    columns: str = typer.Option(..., "--columns", "-c", help="数值列名,逗号分隔"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色列表JSON"),
    field_labels: Optional[str] = typer.Option(None, "--field-labels", help="字段标签,逗号分隔"),
    label: str = _common_label_option("multi_bar"),
    width: str = typer.Option("1000", "--width", help="图表宽度"),
    alignment: str = typer.Option("center", "--alignment", help="对齐方式"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成多值柱状图模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_list = cast(Optional[list[str]], _parse_colors(colors))
    field_label_list = [s.strip() for s in field_labels.split(",") if s.strip()] if field_labels else None
    path = generate_multibar_template(
        output,
        taxonomy_path,
        tree_path,
        columns.split(","),
        color_list,
        field_label_list,
        label,
        id_column,
        width,
        alignment,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 多值柱状图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-heatmap")
def template_heatmap(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    columns: str = typer.Option(..., "--columns", "-c", help="数值列名,逗号分隔"),
    gradient: Optional[str] = typer.Option(None, "--gradient", help="颜色渐变,逗号分隔的色值"),
    label: str = _common_label_option("heatmap"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成热图模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    gradient_list = gradient.split(",") if gradient else None
    path = generate_heatmap_template(
        output,
        taxonomy_path,
        tree_path,
        columns.split(","),
        gradient_list,
        label,
        id_column,
        None,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 热图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-symbols")
def template_symbols(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于符号分类的列名"),
    symbol_type: str = typer.Option("diamond", "--symbol-type", help="符号类型: diamond/circle/square/triangle/star"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("symbols"),
    size: str = typer.Option("30", "--size", help="符号大小"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成符号标记模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_dict = _parse_colors(colors)
    path = generate_symbols_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        symbol_type,
        color_dict,
        label,
        id_column,
        size,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 符号标记配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-pie")
def template_pie(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    columns: str = typer.Option(..., "--columns", "-c", help="数值列名,逗号分隔"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色列表JSON"),
    label: str = _common_label_option("pie"),
    pie_size: str = typer.Option("50", "--pie-size", help="饼图大小"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成饼图模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_list = cast(Optional[list[str]], _parse_colors(colors))
    path = generate_pie_template(
        output,
        taxonomy_path,
        tree_path,
        columns.split(","),
        color_list,
        label,
        id_column,
        pie_size,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 饼图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-boxplot")
def template_boxplot(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    min_column: str = typer.Option("minimum", "--min", help="最小值列名"),
    q1_column: str = typer.Option("q1", "--q1", help="第一四分位数列名"),
    median_column: str = typer.Option("median", "--median", help="中位数列名"),
    q3_column: str = typer.Option("q3", "--q3", help="第三四分位数列名"),
    max_column: str = typer.Option("maximum", "--max", help="最大值列名"),
    extremes_columns: Optional[str] = typer.Option(None, "--extremes", help="极端值列名,逗号分隔"),
    label: str = _common_label_option("boxplot"),
    color: str = typer.Option("#00ff00", "--color", help="箱线图颜色"),
    width: str = typer.Option("1500", "--width", help="图表宽度"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成箱线图模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    extremes = extremes_columns.split(",") if extremes_columns else None
    path = generate_boxplot_template(
        output,
        taxonomy_path,
        tree_path,
        id_column,
        min_column,
        q1_column,
        median_column,
        q3_column,
        max_column,
        extremes,
        label,
        color,
        width,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 箱线图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-gradient")
def template_gradient(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="数值列名"),
    color_min: str = typer.Option("#ff0000", "--color-min", help="最小值颜色"),
    color_max: str = typer.Option("#0000ff", "--color-max", help="最大值颜色"),
    strip_width: str = typer.Option("25", "--strip-width", help="色带宽度"),
    use_mid_color: bool = typer.Option(False, "--use-mid-color", help="使用中间颜色"),
    color_mid: str = typer.Option("#ffff00", "--color-mid", help="中间颜色"),
    label: str = _common_label_option("gradient"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成颜色渐变模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    path = generate_gradient_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        label,
        id_column,
        color_min,
        color_max,
        strip_width,
        use_mid_color,
        color_mid,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 颜色渐变配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-connections")
def template_connections(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    connections: str = typer.Option(..., "--connections", "-c", help="连接对文件路径(JSON格式[[id1,id2],...])"),
    color: str = typer.Option("#e64b35", "--color", help="连线颜色"),
    line_width: str = typer.Option("2", "--line-width", help="连线宽度"),
    line_type: str = typer.Option("solid", "--line-type", help="连线类型: solid/dotted/dashed"),
    label: str = _common_label_option("connections"),
    arrow_head_size: str = typer.Option("1", "--arrow-head-size", help="箭头大小"),
    separator: str = _common_separator_option(),
):
    """生成连接注释模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    conn_path = Path(connections)
    try:
        conn_data = json.loads(conn_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise typer.BadParameter(f"连接数据文件不存在: {connections}", param_hint="--connections")
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"连接数据文件JSON格式错误: {e}", param_hint="--connections")
    path = generate_connection_template(
        output,
        conn_data,
        color,
        line_width,
        line_type,
        label,
        arrow_head_size,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 连接注释配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-labels")
def template_labels(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    label_column: str = typer.Option(..., "--column", "-c", help="标签列名"),
    label: str = _common_label_option("labels"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成标签重命名模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    if label_column not in df.columns:
        raise ValueError(f"Column '{label_column}' not found. Available: {list(df.columns)}")
    data = [
        {"id": row["id"], "label": str(row[label_column])} for _, row in df.iterrows() if not pd.isna(row[label_column])
    ]
    path = generate_labels_template(output, data, label, separator)
    get_console(ctx).print(f"[bold green]✓ 标签重命名配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-popup-info")
def template_popup_info(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    title_column: str = typer.Option("title", "--title-column", help="标题列名"),
    content_column: str = typer.Option("content", "--content-column", help="内容列名"),
    label: str = _common_label_option("popup_info"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成悬停信息模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    data = []
    for _, row in df.iterrows():
        title_val = row.get(title_column, "")
        content_val = row.get(content_column, "")
        data.append(
            {
                "id": row["id"],
                "title": "" if pd.isna(title_val) else str(title_val),
                "content": "" if pd.isna(content_val) else str(content_val),
            }
        )
    path = generate_popup_info_template(output, data, label, separator)
    get_console(ctx).print(f"[bold green]✓ 悬停信息配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-domains")
def template_domains(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data", "-d", help="域数据文件路径(JSON格式)"),
    color: str = typer.Option("#ff00aa", "--color", help="默认颜色"),
    scale: Optional[str] = typer.Option(None, "--scale", help="尺度"),
    label: str = _common_label_option("domains"),
    separator: str = _common_separator_option(),
):
    """生成蛋白质域模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    data_path = Path(data_file)
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise typer.BadParameter(f"域数据文件不存在: {data_file}", param_hint="--data")
    except json.JSONDecodeError as e:
        raise typer.BadParameter(f"域数据文件JSON格式错误: {e}", param_hint="--data")
    path = generate_domain_template(output, data, label, color, scale, separator)
    get_console(ctx).print(f"[bold green]✓ 蛋白质域配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-binary")
def template_binary(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    columns: str = typer.Option(..., "--columns", "-c", help="分类列名,逗号分隔"),
    field_colors: str = typer.Option("#ff0000,#00ff00,#0000ff", "--field-colors", help="字段颜色,逗号分隔"),
    field_shapes: str = typer.Option("1,2,3", "--field-shapes", help="字段形状,逗号分隔(1-6)"),
    label: str = _common_label_option("binary"),
    color: str = typer.Option("#ff0000", "--color", help="默认颜色"),
    show_internal: str = typer.Option("1", "--show-internal", help="是否显示内部节点: 0/1"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成二元数据模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    col_list = columns.split(",")
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for col in col_list:
            row_data[col] = "1" if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "" else "0"
        data.append(row_data)
    colors = field_colors.split(",")
    shapes = field_shapes.split(",")
    path = generate_binary_template(
        output, data, col_list, colors, shapes, label, color, show_internal, separator=separator
    )
    get_console(ctx).print(f"[bold green]✓ 二元数据配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-text")
def template_text(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="文本列名"),
    label: str = _common_label_option("text"),
    font_size: str = typer.Option("12", "--font-size", help="字体大小"),
    font_style: str = typer.Option("normal", "--font-style", help="字体样式"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成文本标签模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    path = generate_text_template(
        output, taxonomy_path, tree_path, column, label, id_column, font_size, font_style, separator
    )
    get_console(ctx).print(f"[bold green]✓ 文本标签配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-external-shape")
def template_external_shape(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于形状分类的列名"),
    shape_type: str = typer.Option(
        "circle", "--shape-type", help="形状类型: circle/square/star/triangle_right/triangle_left/checkmark"
    ),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("external_shape"),
    size: str = typer.Option("20", "--size", help="形状大小"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成外部形状模板。"""
    validate_input_paths(taxonomy_path, tree_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    color_dict = _parse_colors(colors)
    path = generate_external_shape_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        shape_type,
        color_dict,
        label,
        id_column,
        size,
        separator,
    )
    get_console(ctx).print(f"[bold green]✓ 外部形状配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])
