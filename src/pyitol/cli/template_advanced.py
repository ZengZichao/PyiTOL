"""Template advanced commands - linechart, image, alignment, tanglegram, etc."""

import json
from typing import Optional

import typer

from pyitol.cli.apps import template_app
from pyitol.cli.common import (
    _common_id_column_option,
    _common_label_option,
    _common_output_option,
    _common_separator_option,
    _common_taxonomy_option,
    _common_tree_option,
    get_console,
    load_filtered_taxonomy,
    resolve_output_path,
)
from pyitol.templates.generator import (
    generate_alignment_template,
    generate_external_shape_bubble_template,
    generate_image_template,
    generate_linechart_template,
    generate_manual_template,
    generate_meme_template,
    generate_placement_template,
    generate_tanglegram_template,
    generate_timescale_template,
)
from pyitol.utils.session import SessionContext


@template_app.command("create-linechart")
def template_linechart(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="数值列名"),
    position_column: str = typer.Option(None, "--position-column", "-p", help="位置列名(默认使用行号)"),
    label: str = _common_label_option("linechart"),
    color: str = typer.Option("#3c5484", "--color", help="默认颜色"),
    line_width: str = typer.Option("2", "--line-width", help="线条宽度"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成折线图模板 - 在树旁绘制折线图。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")
    has_pos = position_column is not None and position_column in df.columns
    data = []
    for i, (_, row) in enumerate(df.iterrows()):
        if pd.isna(row[column]):
            continue
        pos_val = str(row[position_column]) if has_pos and not pd.isna(row[position_column]) else str(i)
        data.append({"id": row["id"], "position": pos_val, "value": str(row[column])})
    path = generate_linechart_template(output, data, label, color, line_width, separator)
    get_console(ctx).print(f"[bold green]✓ 折线图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-image")
def template_image(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    image_column: str = typer.Option(..., "--image-column", "-i", help="图像文件名列名"),
    url_column: str = typer.Option(None, "--url-column", "-u", help="图像URL列名"),
    label: str = _common_label_option("images"),
    image_width: str = typer.Option("50", "--image-width", help="图像宽度"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成图像嵌入模板 - 在节点旁嵌入图像。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    if image_column not in df.columns:
        raise ValueError(f"Column '{image_column}' not found. Available: {list(df.columns)}")
    data = []
    for _, row in df.iterrows():
        if pd.isna(row[image_column]):
            continue
        item = {"id": row["id"], "image_file": str(row[image_column]), "image_url": str(row.get(url_column, ""))}
        data.append(item)
    path = generate_image_template(output, data, label, image_width, separator)
    get_console(ctx).print(f"[bold green]✓ 图像嵌入配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-alignment")
def template_alignment(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    alignment_column: str = typer.Option(..., "--alignment-column", "-a", help="序列比对列名"),
    label: str = _common_label_option("alignment"),
    color_scheme: str = typer.Option("nucleotide", "--color-scheme", help="颜色方案: nucleotide/amino_acid"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成序列比对模板 - 展示序列比对结果。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)
    if alignment_column not in df.columns:
        raise ValueError(f"Column '{alignment_column}' not found. Available: {list(df.columns)}")
    data = [
        {"id": row["id"], "alignment": str(row[alignment_column])}
        for _, row in df.iterrows()
        if not pd.isna(row[alignment_column])
    ]
    path = generate_alignment_template(output, data, label, color_scheme, separator)
    get_console(ctx).print(f"[bold green]✓ 序列比对配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-tanglegram")
def template_tanglegram(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    connections: str = typer.Option(..., "--connections", "-c", help="连接对,格式: id1,id2;id3,id4"),
    label: str = _common_label_option("tanglegram"),
    color: str = typer.Option("#999999", "--color", help="连线颜色"),
    line_width: str = typer.Option("1", "--line-width", help="连线宽度"),
    separator: str = _common_separator_option(),
):
    """生成纠缠图模板 - 连接两棵树之间的对应节点。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    pairs = []
    for pair_str in connections.split(";"):
        parts = pair_str.strip().split(",")
        if len(parts) >= 2:
            pairs.append((parts[0].strip(), parts[1].strip()))
    path = generate_tanglegram_template(output, pairs, label, color, line_width, separator)
    get_console(ctx).print(f"[bold green]✓ 纠缠图配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-placement")
def template_placement(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data-file", "-d", help="放置数据CSV文件(列: id,position,count,color)"),
    label: str = _common_label_option("placement"),
    color: str = typer.Option("#ff0000", "--color", help="默认颜色"),
    spacing: str = typer.Option("5", "--spacing", help="放置点间距"),
    separator: str = _common_separator_option(),
):
    """生成系统发育放置模板 - 展示短序列放置结果。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    df = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
    data = [dict(row) for _, row in df.iterrows()]
    path = generate_placement_template(output, data, label, color, spacing, separator)
    get_console(ctx).print(f"[bold green]✓ 系统发育放置配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-timescale")
def template_timescale(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data-file", "-d", help="时间数据CSV文件(列: time_point,label,color)"),
    label: str = _common_label_option("timescale"),
    color: str = typer.Option("#000000", "--color", help="默认颜色"),
    scale_position: str = typer.Option("bottom", "--scale-position", help="刻度位置: top/bottom/both"),
    separator: str = _common_separator_option(),
):
    """生成时间尺度模板 - 在分支上添加时间刻度标注。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    df = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
    data = [dict(row) for _, row in df.iterrows()]
    path = generate_timescale_template(output, data, label, color, scale_position, separator)
    get_console(ctx).print(f"[bold green]✓ 时间尺度配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-meme")
def template_meme(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data-file", "-d", help="MEME数据CSV文件(列: id,start,end,name,color)"),
    label: str = _common_label_option("meme"),
    color: str = typer.Option("#ff0000", "--color", help="默认颜色"),
    show_labels: str = typer.Option("1", "--show-labels", help="是否显示基序标签: 0/1"),
    separator: str = _common_separator_option(),
):
    """生成MEME基序模板 - 展示序列基序匹配位置。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    df = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
    data = [dict(row) for _, row in df.iterrows()]
    path = generate_meme_template(output, data, label, color, show_labels, separator)
    get_console(ctx).print(f"[bold green]✓ MEME基序配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-manual")
def template_manual(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data-file", "-d", help="自定义数据CSV文件"),
    label: str = _common_label_option("manual"),
    color: str = typer.Option("#ff0000", "--color", help="默认颜色"),
    custom_header: Optional[str] = typer.Option(None, "--custom-header", help='自定义头部JSON,如 {"KEY":"VALUE"}'),
    separator: str = _common_separator_option(),
):
    """生成手动注释模板 - 自定义数据格式的自由注释。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    df = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
    data = [dict(row) for _, row in df.iterrows()]
    header_dict = None
    if custom_header:
        try:
            header_dict = json.loads(custom_header)
        except json.JSONDecodeError as e:
            raise typer.BadParameter(f"自定义头部JSON格式错误: {e}", param_hint="--custom-header")
    path = generate_manual_template(output, data, header_dict, label, color, separator)
    get_console(ctx).print(f"[bold green]✓ 手动注释配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-external-shape-bubble")
def template_external_shape_bubble(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    columns: str = typer.Option(..., "--columns", "-c", help="数值列名,逗号分隔"),
    label: str = _common_label_option("external_shape_bubble"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成多列气泡外部形状模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    path = generate_external_shape_bubble_template(
        output,
        taxonomy_path,
        tree_path,
        columns.split(","),
        label=label,
        id_column=id_column,
        separator=separator,
    )
    get_console(ctx).print(f"[bold green]✓ 气泡外部形状配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])
