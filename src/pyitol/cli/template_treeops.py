"""Template tree operations commands - tree colors, collapse, prune, etc."""

import logging
from pathlib import Path
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
    _parse_colors,
    get_console,
    load_filtered_taxonomy,
    resolve_output_path,
    validate_input_paths,
)
from pyitol.templates.generator import (
    TemplateGenerator,
    generate_arrow_template,
    generate_collapse_template,
    generate_prune_template,
    generate_ranges_template,
    generate_spacing_template,
)
from pyitol.templates.schemas.base import create_schema
from pyitol.utils.color_tools import assign_colors_to_categories
from pyitol.utils.session import SessionContext

logger = logging.getLogger(__name__)


@template_app.command("create-tree-colors")
def template_tree_colors(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于着色的列名"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("tree_colors"),
    color_type: str = typer.Option("clade", "--color-type", help="着色类型: clade/label/branch/width/range/gradient"),
    width_value: str = typer.Option("3", "--width-value", help="分支线宽度(仅width类型)"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成树着色模板 - 支持分支、标签、分支线、宽度、范围和渐等着色。"""
    validate_input_paths(tree_path, taxonomy_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors_dict: dict[str, str] = {}
    if colors:
        colors_dict = _parse_colors(colors) or {}
    else:
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)

    # For range type: group by category, use tree-ordered first|last as endpoints
    if color_type == "range":
        from pyitol.utils.tree_info import get_tip_order

        tip_list = get_tip_order(tree_path)
        tip_order = {t: i for i, t in enumerate(tip_list)}
        cat_groups: dict[str, list[str]] = {}
        cat_colors: dict[str, str] = {}
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            color = colors_dict.get(val, "#999999")
            cat_groups.setdefault(val, []).append(row["id"])
            cat_colors[val] = color
        data = []
        for val, members in cat_groups.items():
            ordered = sorted(members, key=lambda x: tip_order.get(x, len(tip_order)))
            range_id = f"{ordered[0]}|{ordered[-1]}" if len(ordered) >= 2 else ordered[0]
            data.append({"id": range_id, "type": "range", "color": cat_colors[val]})
            if len(ordered) < 2:
                logger.warning(f"Category '{val}' has only 1 member; range type requires 2+ tips")
    else:
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            color = colors_dict.get(val, "#999999")
            if color_type == "clade":
                data.append({"id": row["id"], "type": "clade", "color": color})
            elif color_type == "label":
                data.append({"id": row["id"], "type": "label", "color": color})
            elif color_type == "branch":
                data.append({"id": row["id"], "type": "branch", "color": color})
            elif color_type == "width":
                data.append({"id": row["id"], "type": "width", "width": width_value, "color": color})
            elif color_type == "gradient":
                try:
                    float(val)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping non-numeric value '{val}' for gradient type")
                    continue
                data.append({"id": row["id"], "value": str(float(val)), "color": "#999999"})

    tmpl_schema = create_schema("tree_colors", label=label, separator=separator)
    if color_type == "gradient":
        tmpl_schema.columns = ["id", "value", "color"]
    elif color_type == "width":
        tmpl_schema.columns = ["id", "type", "width", "color"]
    else:
        tmpl_schema.columns = ["id", "type", "color"]
    tmpl_schema.data_rows = data

    gen = TemplateGenerator()
    gen.add_schema(tmpl_schema)
    gen.write(output)
    get_console(ctx).print(f"[bold green]✓ 树着色配置模板已生成: {output} (类型: {color_type})[/]")
    SessionContext().save_snapshot(generated_files=[output])


@template_app.command("create-branch-gradient")
def template_branch_gradient(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于渐变的数值列名"),
    color_min: str = typer.Option("#ff0000", "--color-min", help="最小值颜色"),
    color_max: str = typer.Option("#0000ff", "--color-max", help="最大值颜色"),
    use_mid_color: bool = typer.Option(False, "--use-mid-color", help="使用中间颜色"),
    color_mid: str = typer.Option("#ffff00", "--color-mid", help="中间颜色"),
    label: str = _common_label_option("branch_gradient"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成分支渐变模板 - 根据数值数据为分支添加颜色渐变效果。"""
    validate_input_paths(tree_path, taxonomy_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    from pyitol.templates.generator import generate_gradient_template

    path = generate_gradient_template(
        output,
        taxonomy_path,
        tree_path,
        column,
        label=label,
        id_column=id_column,
        separator=separator,
        color_min=color_min,
        color_max=color_max,
        use_mid_color=use_mid_color,
        color_mid=color_mid,
    )
    get_console(ctx).print(f"[bold green]✓ 分支渐变配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


def _do_collapse(
    ctx: typer.Context,
    output: str,
    node_ids: Optional[str],
    label: str,
    separator: str,
    taxon: Optional[str] = None,
    rank: Optional[str] = None,
    taxonomy_path: Optional[str] = None,
    tree_path: Optional[str] = None,
    id_column: str = "id",
    strict: bool = False,
    force: bool = False,
    no_clobber: bool = False,
) -> Path | None:
    """Core collapse logic (no Typer decorator)."""
    console = get_console(ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return None
    output = str(checked)

    if taxon:
        if not taxonomy_path or not tree_path or not rank:
            console.print("[bold red]✗ 使用 --taxon 时必须同时指定 --taxonomy, --tree 和 --rank[/]")
            raise typer.Exit(1)

        from pyitol.core.monophyly import check_monophyly_with_taxa_list

        console.print(f"[dim]检查类群 {taxon} 的单系性...[/]")
        results = check_monophyly_with_taxa_list(
            taxonomy_path=taxonomy_path,
            tree_path=tree_path,
            rank=rank,
            taxa_list=[taxon],
            id_column=id_column,
        )

        if not results:
            console.print(f"[bold red]✗ 未找到类群 {taxon}[/]")
            raise typer.Exit(1)

        result = results[0]
        status = result["status"]

        if status == "monophyletic":
            console.print(f"  OK {taxon} 是单系群 (monophyletic)")
            console.print(f"  成员数: {result['member_count']}, LCA: {result['lca_node']}")
            members = result.get("members", "").split("|") if result.get("members") else []
            if not members:
                console.print("[bold red]✗ 无法获取类群成员列表[/]")
                raise typer.Exit(1)
            path = generate_collapse_template(output, members, label or taxon, separator)
            console.print(f"  OK 折叠分支模板已生成: {path} ({len(members)} 个节点)")
            SessionContext().save_snapshot(generated_files=[path])
            return path
        else:
            console.print(f"  WARN {taxon} 不是单系群 (当前状态: {status})")
            console.print(f"  成员数: {result['member_count']}")
            if status == "paraphyletic":
                console.print("  该类群是并系群,包含不属于该类群的额外节点")
                if result.get("extra_nodes"):
                    console.print(f"  额外节点: {result['extra_nodes'][:200]}")
            elif status == "polyphyletic":
                console.print("  该类群是复系群,成员分布在多个独立进化支中")
                if result.get("subgroups"):
                    console.print(f"  子群分解: {result['subgroups'][:200]}")
            console.print("  无法折叠非单系群,因为折叠操作需要所有成员构成一个完整的进化支")

            if strict:
                console.print("  [bold red]--strict 模式: 终止操作[/]")
                raise typer.Exit(1)
            else:
                console.print("  [dim]跳过此类群,继续处理...[/]")
                return None
    elif node_ids:
        path = generate_collapse_template(output, node_ids.split(","), label, separator)
        console.print(f"  OK 折叠分支配置模板已生成: {path}")
        SessionContext().save_snapshot(generated_files=[path])
        return path
    else:
        console.print("[bold red]✗ collapse 需要 --node-ids 或 --taxon[/]")
        raise typer.Exit(1)


@template_app.command("create-collapse")
def template_collapse(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    node_ids: Optional[str] = typer.Option(None, "--node-ids", "-n", help="要折叠的节点ID,逗号分隔"),
    label: str = _common_label_option("collapse"),
    separator: str = _common_separator_option(),
    taxon: Optional[str] = typer.Option(None, "--taxon", help="要折叠的类群名称(需配合 --taxonomy 和 --tree)"),
    rank: Optional[str] = typer.Option(None, "--rank", help="分类等级(如 Phylum, Class)"),
    taxonomy_path: Optional[str] = typer.Option(None, "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: Optional[str] = typer.Option(None, "--tree", "-r", help="树文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    strict: bool = typer.Option(False, "--strict", help="严格模式: 非单系群时终止(默认跳过)"),
):
    """生成折叠分支模板。

    可通过两种方式指定要折叠的节点:
    1. --node-ids: 直接指定节点ID
    2. --taxon + --rank + --taxonomy + --tree: 通过类群名称查找，会先检查单系性

    非单系群时默认跳过并继续，使用 --strict 可改为终止。
    """
    return _do_collapse(
        ctx,
        output,
        node_ids,
        label,
        separator,
        taxon=taxon,
        rank=rank,
        taxonomy_path=taxonomy_path,
        tree_path=tree_path,
        id_column=id_column,
        strict=strict,
        force=force,
        no_clobber=no_clobber,
    )


@template_app.command("create-prune")
def template_prune(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    node_ids: str = typer.Option(..., "--node-ids", "-n", help="要修剪的节点ID,逗号分隔"),
    label: str = _common_label_option("prune"),
    separator: str = _common_separator_option(),
):
    """生成修剪分支模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    path = generate_prune_template(output, node_ids.split(","), label, separator)
    get_console(ctx).print(f"[bold green]✓ 修剪分支配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-spacing")
def template_spacing(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data", "-d", help="节点间距数据文件路径"),
    label: str = _common_label_option("spacing"),
    separator: str = _common_separator_option(),
):
    """生成节点间距调整模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    data_path = Path(data_file)
    import pandas as pd

    df = pd.read_csv(data_path, sep=None, engine="python", dtype=str)
    data = [{"id": row.get("id", ""), "factor": row.get("factor", "1.0")} for _, row in df.iterrows()]
    path = generate_spacing_template(output, data, label, separator)
    get_console(ctx).print(f"[bold green]✓ 节点间距配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-ranges")
def template_ranges(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于分组的列名"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("ranges"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成彩色范围标注模板。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    _, df, _, tip_order = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors_dict: dict[str, str] = {}
    if colors:
        colors_dict = _parse_colors(colors) or {}
    else:
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)

    data = []
    for group_name, group_df in df.groupby(column):
        members = [m for m in group_df["id"].tolist() if m in tip_order]
        members = sorted(members, key=lambda x: tip_order.get(x, 0))
        if len(members) >= 2:
            tip1 = members[0]
            tip2 = members[-1]
            data.append({"id": f"{tip1}|{tip2}", "label": group_name, "color": colors_dict.get(group_name, "#999999")})
        elif len(members) == 1:
            data.append({"id": members[0], "label": group_name, "color": colors_dict.get(group_name, "#999999")})

    path = generate_ranges_template(output, data, label, separator=separator)
    get_console(ctx).print(f"[bold green]✓ 彩色范围标注配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-highlight")
def template_highlight(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于分组的列名"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    label: str = _common_label_option("highlight"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成标签背景高亮模板。"""
    validate_input_paths(tree_path, taxonomy_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors_dict: dict[str, str] = {}
    if colors:
        colors_dict = _parse_colors(colors) or {}
    else:
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)

    data = []
    for _, row in df.iterrows():
        val = row[column]
        if pd.isna(val):
            continue
        data.append({"id": row["id"], "type": "label_background", "color": colors_dict.get(val, "#999999")})

    from pyitol.templates.generator import generate_style_template

    path = generate_style_template(output, data, label=label, separator=separator)
    get_console(ctx).print(f"[bold green]✓ 标签背景高亮配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-style")
def template_style(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    taxonomy_path: str = _common_taxonomy_option(),
    tree_path: str = _common_tree_option(),
    column: str = typer.Option(..., "--column", "-c", help="用于样式分类的列名"),
    style_type: str = typer.Option("branch", "--style-type", help="样式类型: branch/label/label_background"),
    colors: Optional[str] = typer.Option(None, "--colors", help="自定义颜色映射JSON"),
    line_style: str = typer.Option("normal", "--line-style", help="线型: normal/dashed/dotted"),
    font: str = typer.Option("Arial", "--font", help="字体名称"),
    size: str = typer.Option("1", "--size", help="大小因子"),
    label: str = _common_label_option("style"),
    id_column: str = _common_id_column_option(),
    separator: str = _common_separator_option(),
):
    """生成分支/标签样式模板 - 设置分支线型、标签字体和背景样式。"""
    validate_input_paths(tree_path, taxonomy_path, ctx=ctx)
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    _, df, _, _ = load_filtered_taxonomy(tree_path, taxonomy_path, id_column)

    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors_dict: dict[str, str] = {}
    if colors:
        colors_dict = _parse_colors(colors) or {}
    else:
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)

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
            data.append({"id": row["id"], "type": "label_background", "color": color, "size": size})

    from pyitol.templates.generator import generate_style_template

    path = generate_style_template(output, data, label=label, separator=separator)
    get_console(ctx).print(f"[bold green]✓ 分支/标签样式配置模板已生成: {path} (类型: {style_type})[/]")
    SessionContext().save_snapshot(generated_files=[path])


@template_app.command("create-arrow")
def template_arrow(
    ctx: typer.Context,
    output: str = _common_output_option(),
    force: bool = typer.Option(False, "--force", "-f", help="覆盖已存在的输出文件"),
    no_clobber: bool = typer.Option(False, "--no-clobber", help="跳过已存在的输出文件"),
    data_file: str = typer.Option(..., "--data-file", "-d", help="箭头数据CSV文件(列: id,position,direction,color)"),
    label: str = _common_label_option("arrows"),
    color: str = typer.Option("#ff0000", "--color", help="默认颜色"),
    arrow_size: str = typer.Option("30", "--arrow-size", help="箭头大小"),
    separator: str = _common_separator_option(),
):
    """生成箭头注释模板 - 在指定节点位置添加箭头标记。"""
    checked = resolve_output_path(ctx, output, force, no_clobber)
    if checked is None:
        return
    output = str(checked)
    import pandas as pd

    df = pd.read_csv(data_file, sep=None, engine="python", dtype=str)
    data = [dict(row) for _, row in df.iterrows()]
    path = generate_arrow_template(output, data, label, color, arrow_size, separator)
    get_console(ctx).print(f"[bold green]✓ 箭头注释配置模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])
