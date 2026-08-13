"""Task Cmd commands."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, cast

import typer
from rich.progress import track

from pyitol.api.client import ITOLAPIClient
from pyitol.cli.apps import task_app
from pyitol.cli.common import (
    _apply_config_overrides,
    _assign_colors,
    _load_config_file,
    get_console,
)
from pyitol.core.connect_convert import matrix_to_connect
from pyitol.core.parser import detect_tree_schema
from pyitol.core.taxonomy import (
    check_monophyly,
    check_monophyly_with_taxa_list,
    extract_taxonomy,
)
from pyitol.templates.generator import TemplateGenerator
from pyitol.templates.schemas.base import SEPARATOR_MAP, create_schema
from pyitol.utils.session import SessionContext

# Keyword arguments explicitly accepted by client.export() beyond format/output_dir.
# Any other parameter will be passed through extra_params.
_EXPORT_PARAM_KEYS = frozenset({"datasets_visible", "dpi", "width", "height"})


def _split_export_params(param_dict: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """Split param_dict into known client.export() kwargs and extra iTOL params."""
    known: dict[str, str] = {k: v for k, v in param_dict.items() if k in _EXPORT_PARAM_KEYS}
    extra: dict[str, str] = {k: v for k, v in param_dict.items() if k not in _EXPORT_PARAM_KEYS}
    return known, extra


@task_app.command("upload")
def task_upload(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    config_files: list[str] = typer.Option(None, "--config", "-c", help="配置文件路径(可多次指定)"),
    api_key: str = typer.Option(None, "--api-key", help="iTOL API密钥"),
    api_key_file: str = typer.Option(None, "--api-key-file", help="API密钥文件路径"),
    dataset_name: str = typer.Option(None, "--dataset-name", help="数据集名称"),
    tree_description: str = typer.Option(None, "--tree-description", help="树描述信息"),
    verbose: bool = typer.Option(False, "--verbose", help="显示详细响应"),
    # NOTE: verbose parameter reserved for future use
    retry: int = typer.Option(3, "--retry", help="重试次数"),
    wait: int = typer.Option(60, "--wait", help="等待下载时间(秒)"),
    download_path: str = typer.Option(None, "--download", "-d", help="下载输出路径"),
    parameters_file: str = typer.Option(None, "--parameters-file", help="下载参数文件"),
    parameters: list[str] = typer.Option(None, "--parameter", help="下载参数(格式: key=value)"),
):
    """上传树和模板到 iTOL。"""
    console = get_console(ctx)
    # Resolve optional params from config file
    overrides = _apply_config_overrides(
        ctx,
        api_key=(api_key, None),
        api_key_file=(api_key_file, None),
        dataset_name=(dataset_name, None),
        retry=(retry, 3),
        wait=(wait, 60),
        download_path=(download_path, None),
    )
    api_key = overrides["api_key"]
    api_key_file = overrides["api_key_file"]
    dataset_name = overrides["dataset_name"]
    retry = overrides["retry"]
    wait = overrides["wait"]
    download_path = overrides["download_path"]

    try:
        with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=retry) as client:
            template_files = list(config_files) if config_files else []

            tree_name = dataset_name or Path(tree_path).stem
            tree_id = client.upload(
                tree_path,
                template_files,
                project_name=tree_name,
                tree_description=tree_description,
            )
            console.print(f"[bold green]✓ 上传成功: {tree_id}[/]")
            SessionContext().save_snapshot()
            console.print(f"  树名: {tree_name}")

            if download_path:
                console.print(f"  等待 {wait} 秒渲染...")
                import time

                time.sleep(wait)

                param_dict = {}
                if parameters_file:
                    with open(parameters_file, encoding="utf-8") as f:
                        for line in f:
                            if "=" in line:
                                k, v = line.strip().split("=", 1)
                                param_dict[k.strip()] = v.strip()
                if parameters:
                    for p in parameters:
                        if "=" in p:
                            k, v = p.split("=", 1)
                            param_dict[k.strip()] = v.strip()

                fmt = param_dict.pop("format", "pdf")
                known, extra = _split_export_params(param_dict)
                export_kwargs = {"extra_params": extra} if extra else {}
                results = client.export(
                    [tree_id],
                    fmt=fmt,
                    output_dir=download_path,
                    **export_kwargs,  # type: ignore[arg-type]
                    **known,  # type: ignore[arg-type]
                )
                exported = []
                for _tid, path in results.items():
                    console.print(f"[bold green]✓ 已导出到: {path}[/]")
                    exported.append(path)
                SessionContext().save_snapshot(generated_files=cast(list[str | Path], exported))
    except Exception as e:
        console.print(f"[bold red]✗ 上传失败: {e}[/]")
        raise typer.Exit(1)


@task_app.command("export")
def task_export(
    ctx: typer.Context,
    upload_id: str = typer.Option(..., "--upload-id", "-u", help="上传ID"),
    download_path: str = typer.Option(..., "--download", "-d", help="下载输出路径"),
    api_key: str = typer.Option(None, "--api-key", help="iTOL API密钥"),
    api_key_file: str = typer.Option(None, "--api-key-file", help="API密钥文件路径"),
    parameters_file: str = typer.Option(None, "--parameters-file", help="下载参数文件"),
    parameters: list[str] = typer.Option(None, "--parameter", help="下载参数(格式: key=value)"),
    wait: int = typer.Option(60, "--wait", help="等待下载时间(秒)"),
    retry: int = typer.Option(3, "--retry", help="重试次数"),
):
    """导出 iTOL 可视化图片。"""
    console = get_console(ctx)
    overrides = _apply_config_overrides(
        ctx,
        api_key=(api_key, None),
        api_key_file=(api_key_file, None),
        retry=(retry, 3),
        wait=(wait, 60),
    )
    api_key = overrides["api_key"]
    api_key_file = overrides["api_key_file"]
    retry = overrides["retry"]
    wait = overrides["wait"]

    try:
        with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=retry) as client:
            param_dict = {}
            if parameters_file:
                with open(parameters_file, encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            param_dict[k.strip()] = v.strip()
            if parameters:
                for p in parameters:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        param_dict[k.strip()] = v.strip()

            fmt = param_dict.pop("format", "pdf")
            known, extra = _split_export_params(param_dict)
            export_kwargs = {"extra_params": extra} if extra else {}
            results = client.export(
                [upload_id],
                fmt=fmt,
                output_dir=download_path,
                **export_kwargs,  # type: ignore[arg-type]
                **known,  # type: ignore[arg-type]
            )
            exported = []
            for _tid, path in results.items():
                console.print(f"[bold green]✓ 已导出到: {path}[/]")
                exported.append(path)
            SessionContext().save_snapshot(generated_files=cast(list[str | Path], exported))
    except Exception as e:
        console.print(f"[bold red]✗ 导出失败: {e}[/]")
        raise typer.Exit(1)


@task_app.command("upload-and-export")
def task_upload_and_export(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    output: str = typer.Option(..., "--output", "-o", help="输出图片路径"),
    config_files: list[str] = typer.Option(None, "--config", "-c", help="配置文件路径(可多次指定)"),
    api_key: str = typer.Option(None, "--api-key", help="iTOL API密钥"),
    api_key_file: str = typer.Option(None, "--api-key-file", help="API密钥文件路径"),
    dataset_name: str = typer.Option(None, "--dataset-name", help="数据集名称"),
    tree_description: str = typer.Option(None, "--tree-description", help="树描述信息"),
    verbose: bool = typer.Option(False, "--verbose", help="显示详细响应"),
    wait: int = typer.Option(60, "--wait", help="等待下载时间(秒)"),
    retry: int = typer.Option(3, "--retry", help="重试次数"),
    format: str = typer.Option("svg", "--format", "-f", help="导出格式: svg/png/pdf"),
    dpi: int | None = typer.Option(None, "--dpi", help="导出图片DPI (仅PNG/PDF)"),
    width: int | None = typer.Option(None, "--width", help="导出图片宽度 (像素)"),
    height: int | None = typer.Option(None, "--height", help="导出图片高度 (像素)"),
    parameters_file: str = typer.Option(None, "--parameters-file", help="导出参数文件(每行key=value)"),
    parameters: list[str] = typer.Option(None, "--parameter", help="导出参数(格式: key=value, 可多次指定)"),
):
    """上传并导出图片(一步完成)。"""
    console = get_console(ctx)
    overrides = _apply_config_overrides(
        ctx,
        api_key=(api_key, None),
        api_key_file=(api_key_file, None),
        dataset_name=(dataset_name, None),
        tree_description=(tree_description, None),
        retry=(retry, 3),
        wait=(wait, 60),
        format=(format, "svg"),
        dpi=(dpi, None),
        width=(width, None),
        height=(height, None),
    )
    api_key = overrides["api_key"]
    api_key_file = overrides["api_key_file"]
    dataset_name = overrides["dataset_name"]
    tree_description = overrides["tree_description"]
    retry = overrides["retry"]
    wait = overrides["wait"]
    format = overrides["format"]
    dpi = overrides.get("dpi") or dpi
    width = overrides.get("width") or width
    height = overrides.get("height") or height
    # Config overrides applied above

    try:
        with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=retry) as client:
            template_files = list(config_files) if config_files else []

            tree_name = dataset_name or Path(tree_path).stem
            tree_id = client.upload(
                tree_path,
                template_files,
                project_name=tree_name,
                tree_description=tree_description,
            )
            console.print(f"[bold green]✓ 上传成功: {tree_id}[/]")
            SessionContext().save_snapshot()
            console.print(f"  等待 {wait} 秒渲染...")
            import time

            time.sleep(wait)

            # Parse export parameters from --parameter and --parameters-file;
            # supports iTOL parameters such as datasets_visible, background, display_mode
            param_dict = {}
            if parameters_file:
                with open(parameters_file, encoding="utf-8") as f:
                    for line in f:
                        if "=" in line:
                            k, v = line.strip().split("=", 1)
                            param_dict[k.strip()] = v.strip()
            if parameters:
                for p in parameters:
                    if "=" in p:
                        k, v = p.split("=", 1)
                        param_dict[k.strip()] = v.strip()

            # The --format option takes precedence over a same-named --parameter value
            param_dict.pop("format", None)

            # Split known parameters (datasets_visible/dpi/width/height) from extra ones
            known_str, extra = _split_export_params(param_dict)
            known: dict[str, object] = dict(known_str)
            export_kwargs = {"extra_params": extra} if extra else {}

            # --dpi / --width / --height options take precedence over same-named
            # --parameter values; keep their native (int) type instead of going
            # through param_dict's str conversion
            if dpi:
                known["dpi"] = dpi
            if width:
                known["width"] = width
            if height:
                known["height"] = height

            output_dir = str(Path(output).parent) if output else "."
            results = client.export(
                [tree_id],
                fmt=format,
                output_dir=output_dir,
                **export_kwargs,  # type: ignore[arg-type]
                **known,  # type: ignore[arg-type]
            )
            exported = []
            for _tid, path in results.items():
                console.print(f"[bold green]✓ 已导出到: {path}[/]")
                exported.append(path)
            SessionContext().save_snapshot(generated_files=cast(list[str | Path], exported))
    except Exception as e:
        console.print(f"[bold red]✗ 操作失败: {e}[/]")
        raise typer.Exit(1)


@task_app.command("delete")
def task_delete(
    ctx: typer.Context,
    upload_ids: list[str] = typer.Option(None, "--upload-id", "-u", help="上传ID(可多次指定)"),
    project_names: list[str] = typer.Option(None, "--project", "-p", help="项目名称(可多次指定，将删除整个项目)"),
    api_key: str = typer.Option(None, "--api-key", help="iTOL API密钥"),
    api_key_file: str = typer.Option(None, "--api-key-file", help="API密钥文件路径"),
    retry: int = typer.Option(3, "--retry", help="重试次数"),
    confirm: bool = typer.Option(False, "--confirm", help="确认删除（不提示交互确认）"),
):
    """删除已上传的树或项目。"""
    console = get_console(ctx)
    overrides = _apply_config_overrides(
        ctx,
        api_key=(api_key, None),
        api_key_file=(api_key_file, None),
        retry=(retry, 3),
    )
    api_key = overrides["api_key"]
    api_key_file = overrides["api_key_file"]
    retry = overrides["retry"]

    if not upload_ids and not project_names:
        console.print("[bold red]✗ 必须指定至少一个 --upload-id 或 --project[/]")
        raise typer.Exit(1)

    targets = []
    if upload_ids:
        targets.extend([f"树:{uid}" for uid in upload_ids])
    if project_names:
        targets.extend([f"项目:{p}" for p in project_names])

    if not confirm:
        console.print(f"[bold yellow]⚠ 即将删除 {len(targets)} 个目标: {', '.join(targets)}[/]")
        # In non-interactive environments (CI/scripts), require explicit --confirm
        if not sys.stdin.isatty():
            console.print("[bold red]✗ 非交互式环境请使用 --confirm 参数确认删除[/]")
            raise typer.Exit(1)
        user_input = typer.prompt("确认删除? 输入 y/Y 继续", default="n")
        if user_input.lower() not in ("y", "yes"):
            console.print("[bold yellow]已取消删除[/]")
            raise typer.Exit(0)

    try:
        with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=retry) as client:
            if upload_ids:
                results = client.batch_delete(upload_ids)
                for uid, status in track(results.items(), description="[red]Deleting trees..."):
                    if status:
                        console.print(f"[bold green]✓ 已删除树: {uid}[/]")
                        SessionContext().save_snapshot()
                    else:
                        console.print(f"[bold red]✗ 删除失败（树）: {uid}[/]")
            if project_names:
                results = client.batch_delete_projects(project_names)
                for name, status in track(results.items(), description="[red]Deleting projects..."):
                    if status:
                        console.print(f"[bold green]✓ 已删除项目: {name}[/]")
                        SessionContext().save_snapshot()
                    else:
                        console.print(f"[bold red]✗ 删除失败（项目）: {name}[/]")
    except Exception as e:
        console.print(f"[bold red]✗ 删除失败: {e}[/]")
        raise typer.Exit(1)


@task_app.command("status")
def task_status(
    ctx: typer.Context,
    tree_name: str = typer.Option(..., "--tree-name", "-n", help="已上传的树名称"),
    api_key: str = typer.Option(None, "--api-key", help="iTOL API密钥"),
    api_key_file: str = typer.Option(None, "--api-key-file", help="API密钥文件路径"),
):
    """查询已上传树的状态。"""
    console = get_console(ctx)
    overrides = _apply_config_overrides(
        ctx,
        api_key=(api_key, None),
        api_key_file=(api_key_file, None),
    )
    api_key = overrides["api_key"]
    api_key_file = overrides["api_key_file"]

    try:
        with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=1) as client:
            result = client.query_status(tree_name)
            status = result.get("status", "unknown")
            if status == "ready":
                console.print(f'[bold green]✓ 树 "{tree_name}" 状态: 就绪[/]')
            else:
                console.print(f'[bold yellow]⚠ 树 "{tree_name}" 状态: {status}[/]')
                if "response" in result:
                    console.print(f"  HTTP 响应码: {result['response']}")
                raise typer.Exit(1)
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[bold red]✗ 查询失败: {e}[/]")
        raise typer.Exit(1)


@task_app.command("run")
def task_run(
    ctx: typer.Context,
    config: str = typer.Option(None, "--config", "-c", help="单配置文件路径(YAML/JSON)"),
    config_list: str = typer.Option(None, "--config-list", "-l", help="批量配置文件路径(YAML/JSON列表)"),
):
    """运行配置文件(单配置或批量列表)。"""
    console = get_console(ctx)

    if not config and not config_list:
        console.print("[bold red]✗ 必须指定 --config 或 --config-list[/]")
        raise typer.Exit(1)
    if config and config_list:
        console.print("[bold red]✗ --config 和 --config-list 不能同时使用[/]")
        raise typer.Exit(1)

    target_path = Path(config) if config else Path(config_list)
    if not target_path.exists():
        console.print(f"[bold red]✗ 配置文件不存在: {target_path}[/]")
        raise typer.Exit(1)

    try:
        configs = _load_config_file(str(target_path))
        if config:
            # Single config mode
            if isinstance(configs, list):
                console.print("[bold yellow]⚠ 单配置文件不应为列表，将只处理第一个配置[/]")
                configs = [configs[0]]
            else:
                configs = [configs]

        if config_list and not isinstance(configs, list):
            configs = [configs]

        for cfg in configs:
            cmd = cfg.get("command")
            if cmd == "upload":
                tree = cfg.get("tree")
                cfgs = cfg.get("configs", [])
                api_key = cfg.get("api_key")
                api_key_file = cfg.get("api_key_file")
                name = cfg.get("name")
                with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=3) as client:
                    tree_id = client.upload(tree, cfgs, project_name=name)
                    console.print(f"[bold green]✓ 上传成功: {tree_id} ({name})[/]")
            elif cmd == "export":
                upload_id = cfg.get("upload_id")
                download = cfg.get("download")
                api_key = cfg.get("api_key")
                api_key_file = cfg.get("api_key_file")
                params = cfg.get("parameters", {})
                with ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=3) as client:
                    fmt = params.pop("format", "pdf")
                    known, extra = _split_export_params(params)
                    export_kwargs = {"extra_params": extra} if extra else {}
                    export_results = client.export(
                        [upload_id],
                        fmt=fmt,
                        output_dir=download,
                        **export_kwargs,  # type: ignore[arg-type]
                        **known,  # type: ignore[arg-type]
                    )
                    for _tid, path in export_results.items():
                        console.print(f"[bold green]✓ 导出成功: {path}[/]")
            elif cmd == "extract":
                import pandas as pd

                tree = cfg.get("tree")
                taxonomy = cfg.get("taxonomy")
                rank = cfg.get("rank")
                output = cfg.get("output", "taxonomy_extract.txt")
                id_column = cfg.get("id_column", "id")
                if not all([tree, taxonomy, rank]):
                    console.print("[bold red]✗ extract 命令需要 tree, taxonomy, rank 参数[/]")
                    continue
                extract_results: list[dict[str, Any]] = extract_taxonomy(taxonomy, tree, rank, id_column)
                with open(output, "w", encoding="utf-8") as f:
                    for r in extract_results:
                        f.write(f"{r['id']}\t{r['name']}\n")
                console.print(f"[bold green]✓ 已提取 {len(extract_results)} 条记录: {output}[/]")
            elif cmd == "monophyly":
                import pandas as pd

                tree = cfg.get("tree")
                taxonomy = cfg.get("taxonomy")
                rank = cfg.get("rank")
                taxa = cfg.get("taxa")
                taxa_file = cfg.get("taxa_file")
                output = cfg.get("output", "monophyly.csv")
                id_column = cfg.get("id_column", "id")
                if not tree or not taxonomy:
                    console.print("[bold red]✗ monophyly 命令需要 tree 和 taxonomy 参数[/]")
                    continue
                taxa_list = taxa.split(",") if isinstance(taxa, str) else (taxa if taxa else None)
                if taxa_file and not taxa_list:
                    taxa_list = Path(taxa_file).read_text(encoding="utf-8").strip().splitlines()
                if taxa_list:
                    mono_results: list[dict[str, Any]] = check_monophyly_with_taxa_list(
                        taxonomy, tree, rank, taxa_list, None, id_column
                    )
                elif rank:
                    mono_results = check_monophyly(taxonomy, tree, rank, id_column)
                else:
                    console.print("[bold red]✗ monophyly 命令必须指定 rank 或 taxa[/]")
                    continue
                df = pd.DataFrame(mono_results)
                df.to_csv(output, index=False)
                console.print(f"[bold green]✓ 已检查 {len(mono_results)} 个分类群: {output}[/]")
                mono_count = sum(1 for r in mono_results if r["status"] == "monophyletic")
                para_count = sum(1 for r in mono_results if r["status"] == "paraphyletic")
                poly_count = sum(1 for r in mono_results if r["status"] == "polyphyletic")
                console.print(f"  单系: {mono_count}, 并系: {para_count}, 复系: {poly_count}")
            elif cmd == "convert-binary":
                import pandas as pd

                input_file = cfg.get("input")
                output = cfg.get("output", "binary_matrix.csv")
                raw_cols = cfg.get("columns", "")
                columns = raw_cols.split(",") if isinstance(raw_cols, str) else (raw_cols if raw_cols else [])
                id_column = cfg.get("id_column", "id")
                if not input_file:
                    console.print("[bold red]✗ convert-binary 命令需要 input 参数[/]")
                    continue
                df = pd.read_csv(input_file, sep=None, engine="python", dtype=str)
                if id_column in df.columns:
                    df = df.rename(columns={id_column: "id"})
                for col in columns:
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: 1 if pd.notna(x) and str(x).strip() not in ("", "0") else 0)
                out_df = df[["id"] + [c for c in columns if c in df.columns]]
                out_df.to_csv(output, index=False)
                console.print(f"[bold green]✓ 二元矩阵已生成: {output}[/]")
            elif cmd == "convert-connect":
                import pandas as pd

                input_file = cfg.get("input")
                output = cfg.get("output", "connections.csv")
                raw_cols = cfg.get("columns", "")
                columns = raw_cols.split(",") if isinstance(raw_cols, str) else (raw_cols if raw_cols else [])
                weight_mode = cfg.get("weight_mode", "co-occurrence")
                min_weight = cfg.get("min_weight", 0.5)
                max_connections = cfg.get("max_connections", 500)
                id_column = cfg.get("id_column", "id")
                if not input_file:
                    console.print("[bold red]✗ convert-connect 命令需要 input 参数[/]")
                    continue
                df = pd.read_csv(input_file, sep=None, engine="python", dtype=str)
                if id_column in df.columns:
                    df = df.rename(columns={id_column: "id"})
                for c in columns:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)
                conn_data = matrix_to_connect(
                    df, columns, weight_mode=weight_mode, min_weight=min_weight, max_connections=max_connections
                )
                conn_df = pd.DataFrame(conn_data)
                conn_df.to_csv(output, index=False)
                console.print(f"[bold green]✓ 连接对已生成: {output} ({len(conn_data)} 对连接)[/]")
            elif cmd == "template":
                # Template generation via bundle config
                import dendropy
                import pandas as pd

                tree = cfg.get("tree")
                taxonomy = cfg.get("taxonomy")
                output_dir = cfg.get("output_dir", ".")
                prefix = cfg.get("prefix", "")
                separator = cfg.get("separator", "TAB")
                bundle_cfg = cfg.get("bundle", [])
                if not bundle_cfg:
                    console.print("[bold yellow]⚠ template 命令需要 bundle 配置列表[/]")
                    continue
                if not tree or not taxonomy:
                    console.print("[bold red]✗ template 命令需要 tree 和 taxonomy 参数[/]")
                    continue
                tree_schema = detect_tree_schema(tree)
                tree_obj = dendropy.Tree.get_from_path(str(tree), schema=tree_schema, preserve_underscores=True)
                tip_set = {t.taxon.label for t in tree_obj.leaf_nodes() if t.taxon}
                df = pd.read_csv(taxonomy, sep=None, engine="python", dtype=str)
                id_column = cfg.get("id_column", "id")
                if id_column in df.columns:
                    df = df.rename(columns={id_column: "id"})
                df = df[df["id"].isin(tip_set)]
                gen = TemplateGenerator()
                for item in bundle_cfg:
                    btype = item.get("type", "")
                    column = item.get("column", "")
                    blabel = item.get("label", f"{btype}_{column}")
                    if btype in ("color-strip", "colorstrip"):
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
                    elif btype in ("highlight",):
                        schema = create_schema("style", label=blabel, color="#ff0000", separator=separator)
                        if column in df.columns:
                            colors_dict = _assign_colors(df, column, item.get("colors"))
                            data = []
                            for _, row in df.iterrows():
                                val = row[column]
                                if pd.isna(val):
                                    continue
                                data.append(
                                    {
                                        "id": row["id"],
                                        "type": "label_background",
                                        "color": colors_dict.get(val, "#999999"),
                                    }
                                )
                            schema.columns = ["id", "type", "color"]
                            schema.data_rows = data
                        gen.add_schema(schema)
                    elif btype in ("simple-bar", "simplebar", "simple_bar"):
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
                    elif btype == "heatmap":
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
                    elif btype in ("tree-colors", "tree_colors", "branch"):
                        schema = create_schema("tree_colors", label=blabel, separator=separator)
                        if column in df.columns:
                            colors_dict = _assign_colors(df, column, item.get("colors"))
                            data = []
                            for _, row in df.iterrows():
                                val = row[column]
                                if pd.isna(val):
                                    continue
                                data.append(
                                    {
                                        "id": row["id"],
                                        "type": item.get("color_type", "clade"),
                                        "color": colors_dict.get(val, "#999999"),
                                    }
                                )
                            schema.columns = ["id", "type", "color"]
                            schema.data_rows = data
                        gen.add_schema(schema)
                    elif btype == "binary":
                        cols = item.get("columns", [column])
                        schema = create_schema("binary", label=blabel, separator=separator)
                        data = []
                        for _, row in df.iterrows():
                            row_data = {"id": row["id"]}
                            for col in cols:
                                row_data[col] = (
                                    "1" if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "" else "0"
                                )
                            data.append(row_data)
                        schema.columns = ["id", *cols]
                        schema.data_rows = data
                        field_colors = item.get("field_colors", ["#ff0000", "#00ff00", "#0000ff"])
                        field_shapes = item.get("field_shapes", ["1", "2", "3"])
                        schema.parameters["FIELD_COLORS"] = SEPARATOR_MAP.get(separator.upper(), "\t").join(
                            field_colors[: len(cols)]
                        )
                        schema.parameters["FIELD_SHAPES"] = SEPARATOR_MAP.get(separator.upper(), "\t").join(
                            field_shapes[: len(cols)]
                        )
                        schema.parameters["SHOW_INTERNAL"] = item.get("show_internal", "1")
                        gen.add_schema(schema)
                    else:
                        console.print(f"[bold yellow]⚠ task run template 中忽略未知类型: {btype}[/]")
                paths = gen.write_multiple(output_dir, prefix=prefix)
                for p in paths:
                    console.print(f"[bold green]✓ 模板已生成: {p}[/]")
            else:
                console.print(f"[bold yellow]⚠ 未知命令: {cmd}[/]")
    except Exception as e:
        console.print(f"[bold red]✗ 运行失败: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# TREE COMMANDS
# =============================================================================
