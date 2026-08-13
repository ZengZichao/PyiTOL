"""Utils Cmd commands.

NOTE: 'tree-info' is duplicated by 'tree info' (canonical).
NOTE: 'learn-template' is duplicated by 'learn template' (canonical).
These utils versions are kept for backward compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.table import Table

from pyitol.cli.apps import utils_app
from pyitol.cli.common import get_console
from pyitol.core.binary_convert import category_to_binary
from pyitol.core.column_group import group_columns
from pyitol.core.connect_convert import matrix_to_connect
from pyitol.core.count_tree import build_tree_from_counts
from pyitol.core.parser import detect_tree_schema
from pyitol.templates.learner import learn_template
from pyitol.utils.data_converters import df_tree, long_to_wide, wide_to_long
from pyitol.utils.io import find_first_tree_file, search_tree_file
from pyitol.utils.session import SessionContext
from pyitol.utils.tree_info import get_tree_info


@utils_app.command("tree-info")
def utils_tree_info(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
):
    """显示树文件的基本信息。

    P2-29: 此命令与 'tree info' 重复。建议使用 'pyitol tree info'。
    """
    import warnings

    warnings.warn("'utils tree-info' is deprecated; use 'tree info' instead", DeprecationWarning, stacklevel=2)
    info = get_tree_info(tree_path)
    console = get_console(ctx)
    table = Table(title=f"树信息: {Path(tree_path).name}")
    table.add_column("属性")
    table.add_column("值")
    for k, v in info.items():
        table.add_row(str(k), str(v))
    console.print(table)


@utils_app.command("search-tree-file")
def utils_search_tree_file(
    ctx: typer.Context,
    directory: str = typer.Option(".", "--dir", "-d", help="搜索目录"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive", help="是否递归搜索子目录"),
    first_only: bool = typer.Option(False, "--first-only", help="只返回第一个匹配的文件"),
):
    """在目录中自动搜索系统发育树文件。"""
    console = get_console(ctx)
    if first_only:
        result = find_first_tree_file(directory, recursive)
        if result:
            console.print(f"[bold green]✓ 找到树文件: {result}[/]")
        else:
            console.print("[bold yellow]⚠ 未找到树文件[/]")
    else:
        files = search_tree_file(directory, recursive)
        if files:
            console.print(f"[bold green]✓ 找到 {len(files)} 个树文件:[/]")
            for f in files:
                console.print(f"  {f}")
        else:
            console.print("[bold yellow]⚠ 未找到树文件[/]")


@utils_app.command("taxonomy-parse")
def utils_taxonomy_parse(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    max_rows: int = typer.Option(10, "--max-rows", help="显示的最大行数"),
):
    """解析并预览分类表格的结构和内容。"""
    import pandas as pd

    console = get_console(ctx)
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    console.print("[bold]分类表格概览:[/]")
    console.print(f"  行数: {len(df)}, 列数: {len(df.columns)}")
    console.print(f"  列名: {', '.join(df.columns)}")
    if id_column in df.columns:
        console.print(f"  ID列唯一值: {df[id_column].nunique()}")
    table = Table(title=f"前 {min(len(df), max_rows)} 行预览")
    for col in df.columns:
        table.add_column(col)
    for _, row in df.head(max_rows).iterrows():
        table.add_row(*[str(v) for v in row.values])
    console.print(table)


@utils_app.command("learn-template")
def utils_learn_template(
    ctx: typer.Context,
    template_files: list[str] = typer.Option(..., "--template", "-t", help="模板文件路径(可多次指定)"),
    output: str = typer.Option("learned_config.json", "--output", "-o", help="输出文件路径"),
):
    """从已有 iTOL 模板文件反向学习配置。

    P2-29: 此命令与 'learn template' 重复。建议使用 'pyitol learn template'。
    """
    import warnings

    warnings.warn(
        "'utils learn-template' is deprecated; use 'learn template' instead", DeprecationWarning, stacklevel=2
    )
    console = get_console(ctx)
    all_data = []
    for tf in template_files:
        data = learn_template(tf)
        all_data.append(data)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    console.print(f"[bold green]✓ 已从 {len(template_files)} 个模板中学习: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("wide-to-long")
def utils_wide_to_long(
    ctx: typer.Context,
    data_path: str = typer.Option(..., "--data", "-d", help="数据文件路径"),
    output: str = typer.Option("long_format.csv", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    value_name: str = typer.Option("value", "--value-name", help="值列名"),
    variable_name: str = typer.Option("variable", "--variable-name", help="变量列名"),
):
    """宽格式转长格式。"""
    wide_to_long(data_path, output, id_column, value_name, variable_name)
    get_console(ctx).print(f"[bold green]✓ 已转换为长格式: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("long-to-wide")
def utils_long_to_wide(
    ctx: typer.Context,
    data_path: str = typer.Option(..., "--data", "-d", help="数据文件路径"),
    output: str = typer.Option("wide_format.csv", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    variable_column: str = typer.Option("variable", "--variable-column", help="变量列名"),
    value_column: str = typer.Option("value", "--value-column", help="值列名"),
):
    """长格式转宽格式。"""
    long_to_wide(data_path, output, id_column, variable_column, value_column)
    get_console(ctx).print(f"[bold green]✓ 已转换为宽格式: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("count-to-tree")
def utils_count_to_tree(
    ctx: typer.Context,
    data_path: str = typer.Option(..., "--data", "-d", help="计数值数据文件路径"),
    output: str = typer.Option("tree_from_counts.nwk", "--output", "-o", help="输出树文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    method: str = typer.Option("upgma", "--method", help="建树方法: upgma/nj"),
):
    """基于计数值距离构建系统发育树。"""
    tree_str = build_tree_from_counts(data_path, id_column, method=method)
    Path(output).write_text(tree_str, encoding="utf-8")
    get_console(ctx).print(f"[bold green]✓ 已从计数值构建树: {output} ({method})[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("group-columns")
def utils_group_columns(
    ctx: typer.Context,
    data_path: str = typer.Option(..., "--data", "-d", help="数据文件路径"),
    output: str = typer.Option("grouped.csv", "--output", "-o", help="输出文件路径"),
    columns: str = typer.Option(None, "--columns", "-c", help="要聚合的列名,逗号分隔"),
    group_by: str = typer.Option(None, "--group-by", "-g", help="按行分组列名"),
    group_regex: str = typer.Option(None, "--group-regex", help='按列名正则匹配分组,如 "^(ATP|COX)"'),
    group_map: str = typer.Option(None, "--group-map", help='列分组映射(JSON),如 {"energy": ["ATP", "COX"]}'),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    agg_func: str = typer.Option("sum", "--agg", help="聚合函数: sum/mean/max/min"),
):
    """按指定列聚合数据。支持正则匹配列名分组和多属性映射分组。"""
    import json

    col_list = columns.split(",") if columns else None
    gmap = json.loads(group_map) if group_map else None
    group_columns(data_path, output, col_list, group_by, group_regex, gmap, id_column, agg_func)
    get_console(ctx).print(f"[bold green]✓ 列已聚合: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("binary")
def utils_binary(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    columns: str = typer.Option(..., "--columns", "-c", help="要转换的列名,逗号分隔"),
    output: str = typer.Option("binary.csv", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """分类数据转换为二元矩阵。"""
    category_to_binary(taxonomy_path, output, columns.split(","), id_column)
    get_console(ctx).print(f"[bold green]✓ 二元矩阵已生成: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("connections")
def utils_connections(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    columns: str = typer.Option(..., "--columns", "-c", help="要转换的列名,逗号分隔"),
    output: str = typer.Option("connections.csv", "--output", "-o", help="输出文件路径"),
    weight_mode: str = typer.Option("co-occurrence", "--weight-mode", help="权重模式: co-occurrence/count"),
    min_weight: float = typer.Option(0.5, "--min-weight", help="最小权重阈值"),
    max_connections: int = typer.Option(500, "--max-connections", help="最大连接数"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """生成连接对(基于共现权重)。"""
    import pandas as pd

    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    col_list = columns.split(",")
    for c in col_list:
        if c in df.columns:
            df[c] = df[c].notna().astype(int)
    conn_data = matrix_to_connect(
        df, col_list, weight_mode=weight_mode, min_weight=min_weight, max_connections=max_connections
    )
    conn_df = pd.DataFrame(conn_data, columns=["id1", "id2", "weight", "color"])
    conn_df.to_csv(output, index=False)
    get_console(ctx).print(f"[bold green]✓ 连接对已生成: {output} ({len(conn_data)} 对)[/]")
    SessionContext().save_snapshot(generated_files=[output])


@utils_app.command("preview")
def utils_preview(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    column: str = typer.Option(..., "--column", "-c", help="要预览的列名"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    max_rows: int = typer.Option(20, "--max-rows", help="显示的最大行数"),
):
    """预览分类表格中特定列的数据分布。"""
    import dendropy
    import pandas as pd

    console = get_console(ctx)
    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)]

    if column not in df.columns:
        console.print(f"[bold red]✗ 列不存在: {column}[/]")
        raise typer.Exit(1)

    value_counts = df[column].value_counts()
    table = Table(title=f"列 '{column}' 的值分布 (前 {min(len(value_counts), max_rows)})")
    table.add_column("值")
    table.add_column("计数")
    for val, count in value_counts.head(max_rows).items():
        table.add_row(str(val), str(count))
    console.print(table)


@utils_app.command("df-tree")
def utils_df_tree(
    ctx: typer.Context,
    data_path: str = typer.Option(..., "--data", "-d", help="数据文件路径(CSV/TSV)"),
    output: str = typer.Option("df_tree.nwk", "--output", "-o", help="输出树文件路径"),
    columns: str = typer.Option(None, "--columns", "-c", help="用于建树的列名,逗号分隔"),
    main: str = typer.Option(
        "col", "--main", help="建树方向: col(基于列相似性,行为末端节点) / row(基于行相似性,列为末端节点)"
    ),
    order: str = typer.Option("none", "--order", help="排序方式: none / hclust"),
    metric: str = typer.Option("euclidean", "--metric", help="距离度量: euclidean/cityblock/correlation等"),
    linkage_method: str = typer.Option("average", "--linkage", help="连接方法: average/complete/single/ward"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """从数据框直接构建 Newick 格式的系统发育树。"""
    col_list = columns.split(",") if columns else None
    tree_str = df_tree(
        data_path,
        columns=col_list,
        main=main,
        order=order,
        metric=metric,
        linkage_method=linkage_method,
        id_column=id_column,
    )
    Path(output).write_text(tree_str, encoding="utf-8")
    get_console(ctx).print(f"[bold green]✓ 已从数据框构建树: {output} (main={main}, order={order})[/]")
    SessionContext().save_snapshot(generated_files=[output])


# =============================================================================
# LEARN COMMANDS
# =============================================================================
