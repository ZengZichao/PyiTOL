"""Taxonomy Cmd commands."""

from __future__ import annotations

from pathlib import Path

import dendropy
import pandas as pd
import typer
from rich.console import Console

from pyitol.cli.apps import taxonomy_app
from pyitol.cli.common import (
    _apply_config_overrides,
    get_console,
    validate_input_paths,
)
from pyitol.core.connect_convert import matrix_to_connect
from pyitol.core.monophyly import (
    get_special_identifier_description,
    is_special_identifier,
    resolve_special_identifier,
)
from pyitol.core.parser import detect_tree_schema
from pyitol.core.taxonomy import (
    check_monophyly,
    check_monophyly_with_taxa_list,
    extract_taxonomy,
    extract_taxonomy_with_stats,
    get_ranks,
)
from pyitol.templates.generator import TemplateGenerator, generate_binary_template, generate_connection_template
from pyitol.templates.presets import get_palette
from pyitol.templates.schemas.base import LegendConfig, create_schema
from pyitol.utils.constants import (
    DEFAULT_PRIMARY_COLOR,
    DEFAULT_SEPARATOR,
    PRIMARY_RGB_PALETTE,
)
from pyitol.utils.session import SessionContext


@taxonomy_app.command("ranks")
def taxonomy_ranks(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """显示分类等级列表。"""
    ranks = get_ranks(taxonomy_path, id_column)
    console = get_console(ctx)
    console.print("[bold]可用分类等级:[/]")
    for i, r in enumerate(ranks):
        console.print(f"  {i + 1}. {r}")


@taxonomy_app.command("extract")
def taxonomy_extract(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    rank: str = typer.Option(..., "--rank", help="分类等级名称"),
    output: str = typer.Option("taxonomy_extract.txt", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """提取指定分类等级的信息。"""
    results = extract_taxonomy(taxonomy_path, tree_path, rank, id_column)
    with open(output, "w", encoding="utf-8") as f:
        for r in results:
            f.write(f"{r['id']}\t{r['name']}\n")
    get_console(ctx).print(f"[bold green]✓ 已提取 {len(results)} 条记录: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@taxonomy_app.command("extract-stats")
def taxonomy_extract_stats(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    rank: str = typer.Option(..., "--rank", help="分类等级名称"),
    output: str = typer.Option("taxonomy_stats.csv", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
):
    """提取分类统计信息（成员数、LCA节点等）。"""
    df = extract_taxonomy_with_stats(taxonomy_path, tree_path, rank, output, id_column)
    get_console(ctx).print(f"[bold green]✓ 已提取 {len(df)} 个分类群的统计信息: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@taxonomy_app.command("monophyly")
def taxonomy_monophyly(
    ctx: typer.Context,
    taxonomy_path: str | None = typer.Option(None, "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: str | None = typer.Option(None, "--tree", "-r", help="树文件路径"),
    rank: str = typer.Option(None, "--rank", help="分类等级名称"),
    taxa: str = typer.Option(None, "--taxa", help="指定分类群名称,逗号分隔。支持特殊标识符: LUCA, LACA, LBCA"),
    taxa_file: str = typer.Option(None, "--taxa-file", help="包含分类群名称的文件(每行一个)"),
    output: str = typer.Option("monophyly.csv", "--output", "-o", help="输出文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    multi_tree_mode: str = typer.Option(
        "ask", "--multi-tree-mode", "-m", help="多棵树处理策略: ask/first/last/random/split"
    ),
    # NOTE: multi_tree_mode parameter reserved for future use
    polytomy_mode: str = typer.Option(
        "strict", "--polytomy-mode", help="多歧节点处理策略: strict/relaxed/data-insufficient"
    ),
):
    """检查指定分类群的单系性(单系/并系/复系)。

    支持特殊标识符: LUCA(所有古菌和细菌的MRCA)、LACA(所有古菌的MRCA)、LBCA(所有细菌的MRCA)。
    --polytomy-mode relaxed 时, 若成员分散在多歧节点的部分子分支中, 将判为并系而非复系。
    --polytomy-mode data-insufficient 时, 此类情况将判为数据不足(data_insufficient)。
    """
    overrides = _apply_config_overrides(
        ctx,
        taxonomy_path=(taxonomy_path, None),
        tree_path=(tree_path, None),
        rank=(rank, None),
        taxa=(taxa, None),
        taxa_file=(taxa_file, None),
        output=(output, "monophyly.csv"),
        id_column=(id_column, "id"),
        multi_tree_mode=(multi_tree_mode, "ask"),
        polytomy_mode=(polytomy_mode, "strict"),
    )
    taxonomy_path = overrides["taxonomy_path"]
    tree_path = overrides["tree_path"]
    rank = overrides["rank"]
    taxa = overrides["taxa"]
    taxa_file = overrides["taxa_file"]
    output = overrides["output"]
    id_column = overrides["id_column"]
    multi_tree_mode = overrides["multi_tree_mode"]
    polytomy_mode = overrides["polytomy_mode"]

    import pandas as pd

    console = get_console(ctx)
    if not taxonomy_path or not tree_path:
        console.print("[bold red]✗ 必须指定 --taxonomy 和 --tree（或通过配置文件提供）[/]")
        raise typer.Exit(1)
    taxa_list = taxa.split(",") if taxa else None
    if taxa_file:
        taxa_list = Path(taxa_file).read_text(encoding="utf-8").strip().splitlines()

    # Show info for special identifiers
    if taxa_list:
        for name in taxa_list:
            name_stripped = name.strip()
            if is_special_identifier(name_stripped):
                desc = get_special_identifier_description(name_stripped)
                console.print(f"[dim]特殊标识符 {name_stripped}: {desc}[/]")

    if taxa_list:
        results = check_monophyly_with_taxa_list(
            taxonomy_path, tree_path, rank, taxa_list, None, id_column, polytomy_mode=polytomy_mode
        )
    elif rank:
        results = check_monophyly(taxonomy_path, tree_path, rank, id_column, polytomy_mode=polytomy_mode)
    else:
        console.print("[bold red]✗ 必须指定 --rank 或 --taxa/--taxa-file[/]")
        raise typer.Exit(1)

    df = pd.DataFrame(results)
    df.to_csv(output, index=False)
    console.print(f"[bold green]✓ 已检查 {len(results)} 个分类群: {output}[/]")

    # Print summary
    mono_count = sum(1 for r in results if r["status"] == "monophyletic")
    para_count = sum(1 for r in results if r["status"] == "paraphyletic")
    poly_count = sum(1 for r in results if r["status"] == "polyphyletic")
    console.print(
        f"  单系(Monophyletic): {mono_count}, 并系(Paraphyletic): {para_count}, 复系(Polyphyletic): {poly_count}"
    )
    SessionContext().save_snapshot(generated_files=[output])


@taxonomy_app.command("style")
def taxonomy_style(
    ctx: typer.Context,
    taxonomy_path: str = typer.Option(..., "--taxonomy", "-t", help="分类表格文件路径"),
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    rank: str = typer.Option(None, "--rank", help="分类等级名称"),
    taxon: str = typer.Option(None, "--taxon", help="指定类群名称,逗号分隔"),
    action: str = typer.Option(
        ...,
        "--action",
        "-a",
        help="美化类型: color-branch/color-label/color-range/color-strip/style-branch/style-label/width/highlight/symbol/range/gradient",  # noqa: E501
    ),
    output: str = typer.Option("style_template.txt", "--output", "-o", help="输出模板文件路径"),
    color: str = typer.Option(None, "--color", help="指定颜色(HEX)"),
    label: str = typer.Option(None, "--label", "-l", help="自定义标签"),
    palette: str = typer.Option("nature", "--palette", help="配色预设: nature/cell/colorblind"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    separator: str = typer.Option(DEFAULT_SEPARATOR, "--separator", help="分隔符: TAB/SPACE/COMMA"),
):
    """根据分类信息和指定美化类型生成 iTOL 模板配置文件。"""
    validate_input_paths(tree_path, taxonomy_path, ctx=ctx)
    import pandas as pd

    console = get_console(ctx)

    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)]

    # Determine target column and values
    target_column = rank
    if not target_column and not taxon:
        console.print("[bold red]✗ 必须指定 --rank 或 --taxon[/]")
        raise typer.Exit(1)

    if taxon:
        taxa_list = [t.strip() for t in taxon.split(",")]
    else:
        taxa_list = sorted(df[target_column].dropna().unique()) if target_column in df.columns else []

    if not taxa_list:
        console.print("[bold red]✗ 未找到有效的类群信息[/]")
        raise typer.Exit(1)

    # Assign colors
    colors = get_palette(palette, n=len(taxa_list))
    color_map = {val: color if color else colors[i % len(colors)] for i, val in enumerate(taxa_list)}

    # Get tree tip order for range/gradient actions
    tip_order_map: dict[str, int] = {}
    if action in ("range", "gradient", "color-range"):
        from pyitol.utils.tree_info import get_tip_order

        tip_list = get_tip_order(tree_path)
        tip_order_map = {t: i for i, t in enumerate(tip_list)}

    gen = TemplateGenerator()

    for val in taxa_list:
        if target_column and target_column in df.columns:
            members = df[df[target_column] == val]["id"].tolist()
        else:
            # If --taxon is used without rank, try to find exact matches in id column
            members = [val] if val in tip_set else []

        if not members:
            continue

        # Sort members by tree order for range-type actions
        if tip_order_map:
            members = sorted(members, key=lambda x: tip_order_map.get(x, len(tip_order_map)))

        ds_label = label or f"{action}_{val}"

        if action == "color-branch":
            schema = create_schema("tree_colors", label=ds_label, separator=separator)
            data = [{"id": m, "type": "clade", "color": color_map[val]} for m in members]
            schema.columns = ["id", "type", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "color-label":
            schema = create_schema("tree_colors", label=ds_label, separator=separator)
            data = [{"id": m, "type": "label", "color": color_map[val]} for m in members]
            schema.columns = ["id", "type", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "color-range":
            schema = create_schema("tree_colors", label=ds_label, separator=separator)
            if len(members) >= 2:
                data = [{"id": f"{members[0]}|{members[-1]}", "type": "range", "color": color_map[val]}]
            else:
                data = [{"id": members[0], "type": "range", "color": color_map[val]}]
            schema.columns = ["id", "type", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "color-strip":
            schema = create_schema("color_strip", label=ds_label, separator=separator)
            data = [{"id": m, "value": val, "color": color_map[val]} for m in members]
            schema.columns = ["id", "value", "color"]
            schema.data_rows = data
            schema.parameters["STRIP_WIDTH"] = "50"
            gen.add_schema(schema)
        elif action == "style-branch":
            schema = create_schema("style", label=ds_label, color=color_map[val], separator=separator)
            data = [{"id": m, "type": "branch", "color": color_map[val], "style": "normal"} for m in members]
            schema.columns = ["id", "type", "color", "style"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "style-label":
            schema = create_schema("style", label=ds_label, color=color_map[val], separator=separator)
            data = [{"id": m, "type": "label", "color": color_map[val], "font": "Arial"} for m in members]
            schema.columns = ["id", "type", "color", "font"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "width":
            schema = create_schema("style", label=ds_label, separator=separator)
            data = [{"id": m, "type": "branch", "color": color_map[val], "size": "2"} for m in members]
            schema.columns = ["id", "type", "color", "size"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "highlight":
            schema = create_schema("style", label=ds_label, color=color_map[val], separator=separator)
            data = [{"id": m, "type": "label_background", "color": color_map[val]} for m in members]
            schema.columns = ["id", "type", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "symbol":
            schema = create_schema("symbols", label=ds_label, separator=separator)
            data = [{"id": m, "type": "circle", "value": "30", "color": color_map[val]} for m in members]
            schema.columns = ["id", "type", "value", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "range":
            schema = create_schema("range", label=ds_label, color=color_map[val], separator=separator)
            if len(members) >= 2:
                data = [{"id": f"{members[0]}|{members[-1]}", "label": val, "color": color_map[val]}]
            else:
                data = [{"id": members[0], "label": val, "color": color_map[val]}]
            schema.columns = ["id", "label", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        elif action == "gradient":
            schema = create_schema("gradient", label=ds_label, separator=separator)
            data = [{"id": m, "value": "1", "color": color_map[val]} for m in members]
            schema.columns = ["id", "value", "color"]
            schema.data_rows = data
            gen.add_schema(schema)
        else:
            console.print(f"[bold red]✗ 未知的美化类型: {action}[/]")
            raise typer.Exit(1)

    gen.write(output)
    console.print(f"[bold green]✓ 样式模板已生成: {output} (action={action}, {len(taxa_list)} 个类群)[/]")
    SessionContext().save_snapshot(generated_files=[output])


@taxonomy_app.command("convert-binary")
def taxonomy_convert_binary(
    ctx: typer.Context,
    input_file: str = typer.Option(None, "--input", "-i", help="输入表格文件路径(CSV/Excel)"),
    output: str = typer.Option("binary_matrix.csv", "--output", "-o", help="输出文件路径"),
    taxonomy_path: str = typer.Option(None, "--taxonomy", "-t", help="分类表格文件路径(兼容模式)"),
    tree_path: str = typer.Option(None, "--tree", "-r", help="树文件路径(兼容模式)"),
    columns: str = typer.Option(None, "--columns", "-c", help="要转换的列名,逗号分隔"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    label: str = typer.Option("binary", "--label", "-l", help="数据集标签(兼容模式)"),
    separator: str = typer.Option(DEFAULT_SEPARATOR, "--separator", help="分隔符: TAB/SPACE/COMMA"),
):
    """将分类数据转换为 0/1 二元矩阵(CSV)或二元数据模板。"""
    import pandas as pd

    console = get_console(ctx)

    if input_file and (not taxonomy_path and not tree_path):
        # Pure file-conversion mode: input CSV/Excel → output 0/1 matrix CSV
        df = pd.read_csv(input_file, sep=None, engine="python", dtype=str)
        if id_column in df.columns:
            df = df.rename(columns={id_column: "id"})

        if not columns:
            console.print("[bold red]✗ 纯文件转换模式下必须指定 --columns[/]")
            raise typer.Exit(1)

        col_list = columns.split(",")
        for col in col_list:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: 1 if pd.notna(x) and str(x).strip() not in ("", "0") else 0)
            else:
                console.print(f"[bold yellow]⚠ 列不存在,已跳过: {col}[/]")

        out_df = df[["id"] + [c for c in col_list if c in df.columns]]
        out_df.to_csv(output, index=False)
        console.print(f"[bold green]✓ 二元矩阵已生成: {output}[/]")
        SessionContext().save_snapshot(generated_files=[output])
        return

    # Compatibility mode: generate the iTOL template directly
    if not taxonomy_path or not tree_path or not columns:
        console.print("[bold red]✗ 兼容模式下必须指定 --taxonomy, --tree 和 --columns[/]")
        raise typer.Exit(1)

    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    df = df[df["id"].isin(tip_set)]

    col_list = columns.split(",")
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for col in col_list:
            row_data[col] = "1" if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "" else "0"
        data.append(row_data)

    path = generate_binary_template(
        output,
        data,
        col_list,
        PRIMARY_RGB_PALETTE,
        ["1", "2", "3"],
        label,
        DEFAULT_PRIMARY_COLOR,
        "1",
        separator=separator,
    )
    console.print(f"[bold green]✓ 二元数据模板已生成: {path}[/]")
    SessionContext().save_snapshot(generated_files=[path])


@taxonomy_app.command("convert-connect")
def taxonomy_convert_connect(
    ctx: typer.Context,
    input_file: str = typer.Option(None, "--input", "-i", help="输入 0/1 矩阵文件路径(CSV/Excel)"),
    output: str = typer.Option("connections.csv", "--output", "-o", help="输出文件路径"),
    taxonomy_path: str = typer.Option(None, "--taxonomy", "-t", help="分类表格文件路径(兼容模式)"),
    columns: str = typer.Option(None, "--columns", "-c", help="要转换的列名,逗号分隔"),
    weight_mode: str = typer.Option("co-occurrence", "--weight-mode", help="权重模式: co-occurrence/count"),
    min_weight: float = typer.Option(0.5, "--min-weight", help="最小权重阈值"),
    max_connections: int = typer.Option(500, "--max-connections", help="最大连接数"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    label: str = typer.Option("connections", "--label", "-l", help="数据集标签(兼容模式)"),
    separator: str = typer.Option(DEFAULT_SEPARATOR, "--separator", help="分隔符: TAB/SPACE/COMMA"),
):
    """将 0/1 矩阵转换为连接对长格式表格(CSV)或连接注释模板。"""
    import pandas as pd

    console = get_console(ctx)

    if input_file and not taxonomy_path:
        # Pure file-conversion mode
        df = pd.read_csv(input_file, sep=None, engine="python", dtype=str)
        if id_column in df.columns:
            df = df.rename(columns={id_column: "id"})

        if not columns:
            # Auto-detect numeric/binary columns
            numeric_cols = []
            for col in df.columns:
                if col == "id":
                    continue
                try:
                    df[col] = pd.to_numeric(df[col], errors="raise")
                    if set(df[col].dropna().unique()).issubset({0, 1}):
                        numeric_cols.append(col)
                except Exception:  # noqa: S110
                    pass
            columns = ",".join(numeric_cols)
            console.print(f"[bold]自动检测到 {len(numeric_cols)} 个二元列[/]")

        col_list = columns.split(",")
        for c in col_list:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

        conn_data = matrix_to_connect(
            df, col_list, weight_mode=weight_mode, min_weight=min_weight, max_connections=max_connections
        )
        conn_df = pd.DataFrame(conn_data)
        conn_df.to_csv(output, index=False)
        console.print(f"[bold green]✓ 连接对已生成: {output} ({len(conn_data)} 对连接)[/]")
        SessionContext().save_snapshot(generated_files=[output])
        return

    # Compatibility mode: generate the iTOL template directly
    if not taxonomy_path or not columns:
        console.print("[bold red]✗ 兼容模式下必须指定 --taxonomy 和 --columns[/]")
        raise typer.Exit(1)

    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    col_list = columns.split(",")
    df = df[["id"] + [c for c in col_list if c in df.columns]]

    for c in col_list:
        if c in df.columns:
            df[c] = df[c].apply(lambda x: 1 if pd.notna(x) and str(x).strip() not in ("", "0") else 0)

    conn_data = matrix_to_connect(
        df, col_list, weight_mode=weight_mode, min_weight=min_weight, max_connections=max_connections
    )
    # matrix_to_connect returns list[dict]; generate_connection_template expects list[tuple]
    conn_pairs = [(d["id1"], d["id2"]) for d in conn_data]
    path = generate_connection_template(output, conn_pairs, "#e64b35", "2", "solid", label, "1", separator)
    console.print(f"[bold green]✓ 连接注释模板已生成: {path} ({len(conn_data)} 对连接)[/]")
    SessionContext().save_snapshot(generated_files=[path])


@taxonomy_app.command("extract-from-names")
def taxonomy_extract_from_names(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    output: str = typer.Option("taxonomy_from_names.csv", "--output", "-o", help="输出分类表格路径"),
    name_format: str = typer.Option("auto", "--format", "-f", help="命名格式: auto/gtdb/embedded/ncbi"),
    delimiter: str = typer.Option("_", "--delimiter", "-d", help="名称分隔符(默认下划线)"),
    taxonomy_levels: str = typer.Option(
        None, "--taxonomy-levels", help='自定义分类级别前缀(如 "d:Domain,p:Phylum,...")'
    ),
    delimiter_mode: str = typer.Option(
        "segment",
        "--taxonomy-delimiter-mode",
        help="嵌入式格式解析策略: segment(正向匹配)/reverse(严格逆序)/greedy(从首个_d_截取)",
    ),
):
    """从树末端名称自动提取分类学信息。

    支持 GTDB 格式 (d__Bacteria;p__Proteobacteria;...;s__Species)、
    嵌入式格式 (accession_d_Bacteria_p_Proteo_c_..._g_Genus)
    和 NCBI 格式 (Genus_species)。

    可通过 --taxonomy-levels 自定义分类级别前缀映射。
    --taxonomy-delimiter-mode 控制嵌入式格式的解析策略，解决分类名含下划线时的歧义问题。
    """
    from pyitol.core.taxonomy import extract_taxonomy_from_tip_names

    console = get_console(ctx)

    df = extract_taxonomy_from_tip_names(
        tree_path,
        output_path=output,
        name_format=name_format,
        delimiter=delimiter,
        taxonomy_levels=taxonomy_levels,
        delimiter_mode=delimiter_mode,
    )
    console.print(f"[bold green]✓ 已从 {len(df)} 个末端名称提取分类信息: {output}[/]")

    # Show detected ranks
    ranks = [c for c in df.columns if c != "id"]
    console.print(f"  检测到的分类等级: {', '.join(ranks)}")

    # Show summary per rank
    for rank in ranks:
        n_unique = df[rank].dropna().nunique()
        console.print(f"  {rank}: {n_unique} 个唯一值")

    SessionContext().save_snapshot(generated_files=[output])


def resolve_special_identifier_members(
    taxon: str,
    taxonomy_path: str,
    tree_path: str,
    id_column: str,
    domain_column: str,
    console: Console,
) -> list[str]:
    """Resolve a special identifier (LUCA/LACA/LBCA) to its member tree tips.

    Reads the tree, filters the resolved members down to actual leaf tips, and
    logs the member count. Raises ``typer.Exit(1)`` when no members can be
    resolved (e.g. the identifier yields nothing in the taxonomy table).

    Args:
        taxon: Special identifier name (already confirmed via ``is_special_identifier``).
        taxonomy_path: Path to the taxonomy table (required for special identifiers).
        tree_path: Path to the tree file.
        id_column: ID column name in the taxonomy table.
        domain_column: Domain column name used for LUCA/LACA/LBCA resolution.
        console: Rich console used for logging.

    Returns:
        Member tip labels that are present in the tree.
    """
    members = resolve_special_identifier(taxon, taxonomy_path, id_column=id_column, domain_column=domain_column)
    if not members:
        console.print(f"[bold red]✗ 无法解析标识符 {taxon}，未找到任何成员[/]")
        raise typer.Exit(1)

    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    members = [m for m in members if m in tip_set]
    console.print(f"[bold]解析 {taxon}: {len(members)} 个成员[/]")
    return members


def merge_embedded_taxonomy(
    embedded_df: pd.DataFrame,
    tax_df: pd.DataFrame,
    console: Console,
) -> pd.DataFrame:
    """Merge taxonomy extracted from tree tip names into the table taxonomy.

    Embedded values fill gaps in the table; where both sources provide a value
    and they differ, the embedded value takes priority and a warning is logged.
    Uses a single ``set_index('id')`` + per-column alignment (vectorized)
    instead of the previous ``列 × iterrows × loc`` nested loop, avoiding the
    O(n·m) cost on large tables.

    Args:
        embedded_df: Taxonomy extracted from tip names (must contain an 'id' column).
        tax_df: Table taxonomy (already normalized, must contain an 'id' column).
        console: Rich console used for conflict warnings.

    Returns:
        The merged taxonomy DataFrame (the input may be modified in place).
    """
    for rank_col in embedded_df.columns:
        if rank_col == "id":
            continue
        if rank_col not in tax_df.columns:
            tax_df[rank_col] = None
        # Per-id embedded value (drop NaN; keep first on duplicate ids).
        emb = embedded_df[["id", rank_col]].dropna(subset=[rank_col])
        emb = emb.set_index("id")[rank_col]
        emb = emb[~emb.index.duplicated(keep="first")]

        table_series = tax_df.set_index("id")[rank_col]

        # Conflicts: both sources provide a non-null value and they differ.
        # Iterate only over ids present in *both* id-indexed Series, so lookup
        # is by the 'id' label (never a positional RangeIndex) -> no KeyError
        # on string ids such as 'A'.
        for tip_id in tax_df["id"]:
            if tip_id not in emb.index or tip_id not in table_series.index:
                continue
            tv = table_series[tip_id]
            ev = emb[tip_id]
            if pd.notna(tv) and pd.notna(ev) and str(tv) != str(ev):
                console.print(
                    f"  [yellow]WARNING: ID={tip_id} {rank_col} 冲突: table={tv} vs embedded={ev}, 使用 embedded[/]"
                )

        # Embedded takes priority: start from the embedded Series and let the
        # table fill only the gaps (NaN) it leaves behind. With ``embedded`` as
        # the *first* argument of ``combine_first``, embedded values win on
        # conflicts and tax-only values are preserved where embedded is absent.
        merged = emb.combine_first(table_series)
        tax_df[rank_col] = tax_df["id"].map(merged)

    return tax_df


def generate_style_template_for_action(
    ctx: typer.Context,
    action: str,
    members: list[str],
    label: str,
    color: str,
    separator: str,
    output: str,
) -> Path:
    """Build and write a single-schema iTOL styling template for one action.

    Supports the three actions accepted by ``taxonomy check-and-style``
    (``color-branch`` / ``highlight`` / ``color-strip``). Applies a
    bottom-right auto-positioned legend. Returns the written file path and
    raises ``typer.Exit(1)`` on an unknown action. ``label`` doubles as both the
    dataset label and the legend title (typically the taxon name).

    Args:
        ctx: Typer context (used for console access).
        action: Styling action name.
        members: Member tip ids to include in the template.
        label: Dataset label and legend title (usually the taxon name).
        color: Assigned color (HEX string).
        separator: Separator name (TAB/SPACE/COMMA).
        output: Output template file path.

    Returns:
        Path to the written template file.
    """
    console = get_console(ctx)
    gen = TemplateGenerator()

    if action == "color-branch":
        schema = create_schema("tree_colors", label=label, separator=separator)
        data = [{"id": m, "type": "clade", "color": color} for m in members]
        schema.columns = ["id", "type", "color"]
        schema.data_rows = data
    elif action == "highlight":
        schema = create_schema("style", label=label, color=color, separator=separator)
        data = [{"id": m, "type": "label_background", "color": color} for m in members]
        schema.columns = ["id", "type", "color"]
        schema.data_rows = data
    elif action == "color-strip":
        schema = create_schema("color_strip", label=label, separator=separator)
        data = [{"id": m, "color": color, "value": label} for m in members]
        schema.columns = ["id", "color", "value"]
        schema.data_rows = data
        schema.parameters["STRIP_WIDTH"] = "50"
    else:
        console.print(f"[bold red]✗ 未知的美化类型: {action}[/]")
        raise typer.Exit(1)

    legend_x, legend_y = LegendConfig.auto_position(n_items=1, position="bottom-right")
    schema.legend.title = label
    schema.legend.position_x = legend_x
    schema.legend.position_y = legend_y
    schema.legend.shapes = ["1"]
    schema.legend.colors = [color]
    schema.legend.labels = [label]
    gen.add_schema(schema)
    return gen.write(output)


@taxonomy_app.command("check-and-style")
def taxonomy_check_and_style(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    taxonomy_path: str = typer.Option(None, "--taxonomy", "-t", help="分类表格文件路径(可选,不提供则从树名提取)"),
    taxon: str = typer.Option(..., "--taxon", help="要检查的类群名称(如 Escherichia, LUCA, LACA, LBCA)"),
    rank: str = typer.Option("Genus", "--rank", help="分类等级(默认 Genus)"),
    action: str = typer.Option("color-branch", "--action", "-a", help="美化类型: color-branch/highlight/color-strip"),
    color: str = typer.Option(None, "--color", help="指定颜色(HEX),不指定则自动分配"),
    output: str = typer.Option("styled_template.txt", "--output", "-o", help="输出模板文件路径"),
    id_column: str = typer.Option("id", "--id-column", help="ID列名"),
    name_format: str = typer.Option(
        "auto", "--name-format", help="命名格式: auto/gtdb/embedded/ncbi(仅无--taxonomy时使用)"
    ),
    palette: str = typer.Option("nature", "--palette", help="配色预设"),
    separator: str = typer.Option(DEFAULT_SEPARATOR, "--separator", help="分隔符: TAB/SPACE/COMMA"),
    domain_column: str = typer.Option("Domain", "--domain-column", help="Domain列名(用于LUCA/LACA/LBCA解析)"),
    multi_tree_mode: str = typer.Option(
        "ask", "--multi-tree-mode", "-m", help="多棵树处理策略: ask/first/last/random/split"
    ),
    source_priority: str = typer.Option(
        "table", "--taxonomy-source-priority", help="混合来源优先级: embedded(树名优先)/table(表格优先),默认table"
    ),
    # NOTE: multi_tree_mode parameter reserved for future use
):
    """检查指定类群是否为单系群，如果是则生成美化模板，否则警告。

    支持特殊标识符: LUCA(所有古菌和细菌的MRCA)、LACA(所有古菌的MRCA)、LBCA(所有细菌的MRCA)。

    工作流程:
    1. 从分类表格或树末端名称提取分类信息
    2. 检查指定类群的单系性
    3. 如果是单系群 → 生成分支着色/高亮模板
    4. 如果不是 → 警告并跳过
    """
    from pyitol.core.taxonomy import extract_taxonomy_from_tip_names

    console = get_console(ctx)

    # Handle special identifiers (LUCA/LACA/LBCA)
    is_special = is_special_identifier(taxon)
    if is_special:
        desc = get_special_identifier_description(taxon)
        console.print(f"[bold]特殊标识符: {taxon} - {desc}[/]")

        if not taxonomy_path:
            console.print("[bold red]✗ 使用特殊标识符(LUCA/LACA/LBCA)时必须提供 --taxonomy 分类表格[/]")
            raise typer.Exit(1)

        # Resolve special identifier to member list (filtered to tree tips)
        members = resolve_special_identifier_members(taxon, taxonomy_path, tree_path, id_column, domain_column, console)

        # Check monophyly using check_monophyly_with_taxa_list
        results = check_monophyly_with_taxa_list(
            taxonomy_path=taxonomy_path,
            tree_path=tree_path,
            rank=None,
            taxa_list=[taxon],
            id_column=id_column,
        )

        if not results:
            console.print(f"[bold red]✗ 未找到 {taxon} 的单系性检查结果[/]")
            raise typer.Exit(1)

        result = results[0]
        status = result["status"]

        if status == "monophyletic":
            console.print(f"[bold green]✓ {taxon} 是单系群 (monophyletic)[/]")
            console.print(f"  成员数: {result['member_count']}, LCA: {result['lca_node']}")
        else:
            console.print(f"[bold yellow]⚠ {taxon} 是 {status}，不是单系群[/]")
            console.print(f"  成员数: {result['member_count']}")
            console.print("  [bold yellow]无法通过指定类群名称进行簇的操作[/]")
            raise typer.Exit(1)

        # Generate template for special identifier
        assigned_color = color or get_palette(palette, n=1)[0]
        path = generate_style_template_for_action(ctx, action, members, taxon, assigned_color, separator, output)

        console.print(f"[bold green]✓ 模板已生成: {path}[/]")
        SessionContext().save_snapshot(generated_files=[path])
        return

    # Step 1: Get taxonomy data
    if taxonomy_path:
        from pyitol.core.taxonomy import _normalize_taxonomy_df

        tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
        tax_df = _normalize_taxonomy_df(tax_df, id_column)

        # If source_priority is 'embedded', also extract from tip names and merge
        if source_priority == "embedded":
            embedded_df = extract_taxonomy_from_tip_names(tree_path, name_format=name_format)
            # Merge: embedded values fill gaps in table, conflicts logged.
            # Vectorized (set_index + per-column alignment) instead of the
            # previous column × iterrows × loc nested loop (avoids O(n·m) cost).
            tax_df = merge_embedded_taxonomy(embedded_df, tax_df, console)
    else:
        # Auto-extract from tip names
        console.print("[dim]未提供分类表格,从树末端名称自动提取...[/]")
        tax_df = extract_taxonomy_from_tip_names(tree_path, name_format=name_format)
        # Save intermediate file
        auto_tax_path = str(Path(output).parent / "taxonomy_auto.csv")
        tax_df.to_csv(auto_tax_path, index=False)
        console.print(f"  [dim]自动提取的分类表: {auto_tax_path}[/]")

    # Step 2: Check monophyly
    tree_schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=tree_schema, preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    tax_df["id"] = tax_df["id"].astype(str)
    tax_df = tax_df[tax_df["id"].isin(tip_set)]

    if rank not in tax_df.columns:
        console.print("[bold red]✗ 分类等级 '" + rank + "' 不在表格中。可用: " + str(list(tax_df.columns)) + "[/]")
        raise typer.Exit(1)

    # Find members of the specified taxon
    members = tax_df[tax_df[rank] == taxon]["id"].tolist()
    if not members:
        # Try partial match
        members = tax_df[tax_df[rank].str.contains(taxon, na=False, case=False)]["id"].tolist()
        if members:
            console.print(f"[bold yellow]⚠ 精确匹配未找到,使用模糊匹配: {taxon} → {len(members)} 个成员[/]")
        else:
            console.print("[bold red]✗ 类群 '" + taxon + "' 在等级 '" + rank + "' 中未找到任何成员[/]")
            console.print(f"  可用的 {rank} 值: {sorted(tax_df[rank].dropna().unique())[:20]}")
            raise typer.Exit(1)

    console.print(f"[bold]检查类群: {taxon} ({rank}), {len(members)} 个成员[/]")

    # Check monophyly using the core function
    tax_file = taxonomy_path if taxonomy_path else auto_tax_path
    results = check_monophyly_with_taxa_list(
        taxonomy_path=tax_file,
        tree_path=tree_path,
        rank=rank,
        taxa_list=[taxon],
        id_column="id",
    )

    if not results:
        console.print(f"[bold red]✗ 未找到类群 '{taxon}' 的单系性检查结果[/]")
        raise typer.Exit(1)

    result = results[0]
    status = result["status"]
    member_count = result["member_count"]
    extra_count = result["extra_count"]

    # Step 3: Apply styling based on monophyly status
    if status == "monophyletic":
        console.print(f"[bold green]✓ {taxon} 是单系群 (monophyletic)[/]")
        console.print(f"  成员数: {member_count}, LCA: {result['lca_node']}")

        # Generate the requested template
        assigned_color = color or get_palette(palette, n=1)[0]
        path = generate_style_template_for_action(ctx, action, members, taxon, assigned_color, separator, output)

        console.print(f"[bold green]✓ 模板已生成: {path}[/]")
        SessionContext().save_snapshot(generated_files=[path])

    elif status == "paraphyletic":
        console.print(f"[bold yellow]⚠ {taxon} 是并系群 (paraphyletic),不是单系群[/]")
        console.print(f"  成员数: {member_count}, 额外节点: {extra_count}")
        console.print(f"  LCA: {result['lca_node']}")
        console.print("  [bold yellow]无法通过指定类群名称进行簇的操作,因为该类群不构成一个完整的进化支[/]")
        if result["extra_nodes"]:
            console.print(f"  额外节点: {result['extra_nodes'][:200]}")
        raise typer.Exit(1)

    elif status == "polyphyletic":
        console.print(f"[bold red]✗ {taxon} 是复系群 (polyphyletic),不是单系群[/]")
        console.print(f"  成员数: {member_count}")
        console.print("  [bold red]该类群成员分布在多个独立的进化支中,无法作为单一簇操作[/]")
        if result["subgroups"]:
            console.print(f"  子群分解: {result['subgroups'][:300]}")
        raise typer.Exit(1)

    elif status == "data_insufficient":
        console.print(f"[bold yellow]⚠ {taxon} 分类数据不足 (data_insufficient)[/]")
        console.print(f"  成员数: {member_count}, 无法确定单系性状态")
        raise typer.Exit(1)

    else:
        console.print(f"[bold red]✗ 未知状态: {status}[/]")
        raise typer.Exit(1)
