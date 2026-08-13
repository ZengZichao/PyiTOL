"""PyiTOL CLI - iTOL visualization toolkit for Python."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast

import pandas as pd
import typer
from rich.console import Console

from pyitol.api.client import ITOLAPIClient

# Import sub-modules to register their commands
from pyitol.cli import (
    config_cmd,  # noqa: F401
    learn_cmd,  # noqa: F401
    task_cmd,  # noqa: F401
    taxonomy_cmd,  # noqa: F401
    template_advanced,  # noqa: F401
    template_cmd,  # noqa: F401
    template_datasets,  # noqa: F401
    template_treeops,  # noqa: F401
    tree_cmd,  # noqa: F401
    utils_cmd,  # noqa: F401
)
from pyitol.cli.apps import (
    config_app,
    learn_app,
    task_app,
    taxonomy_app,
    template_app,
    tree_app,
    utils_app,
)
from pyitol.cli.common import (
    _load_config_file,
    _parse_log_detail,
    get_console,
)
from pyitol.core.monophyly import set_low_memory
from pyitol.core.taxonomy import (
    check_monophyly,
    extract_taxonomy_with_stats,
    get_ranks,
)
from pyitol.core.validator import (
    ValidationError,
    validate_inputs,
)
from pyitol.exceptions import (
    APIError,
    APIKeyError,
    ColorCodeError,
    ExportError,
    MetadataParseError,
    PyiTOLBaseError,
    SeparatorConflictError,
    SessionError,
    TemplateError,
    TreeParseError,
    UploadError,
)
from pyitol.templates.generator import (
    TemplateGenerator,
    generate_alignment_template,
    generate_arrow_template,
    generate_binary_template,
    generate_boxplot_template,
    generate_branch_template,
    generate_collapse_template,
    generate_color_strip_template,
    generate_external_shape_bubble_template,
    generate_external_shape_template,
    generate_gradient_template,
    generate_heatmap_template,
    generate_image_template,
    generate_labels_template,
    generate_linechart_template,
    generate_manual_template,
    generate_meme_template,
    generate_multibar_template,
    generate_pie_template,
    generate_placement_template,
    generate_popup_info_template,
    generate_prune_template,
    generate_ranges_template,
    generate_simple_bar_template,
    generate_style_template,
    generate_symbols_template,
    generate_tanglegram_template,
    generate_text_template,
    generate_timescale_template,
    generate_tree_colors_template,
)
from pyitol.templates.schemas.base import create_schema
from pyitol.utils.color_tools import assign_colors_to_categories
from pyitol.utils.session import SessionContext
from pyitol.utils.tree_info import get_tree_info


def _build_banner() -> str:
    """Build banner with version, license, date info, and dependency licenses."""
    from pyitol import _DEPENDENCY_LICENSES, __license__, __release_date__, __version__, get_git_hash

    git_hash = get_git_hash()
    hash_str = f"  commit: {git_hash}" if git_hash else ""
    # Build dependency license summary
    dep_lines = []
    for lib, lic in _DEPENDENCY_LICENSES.items():
        dep_lines.append(f"    {lib}: {lic}")
    deps_str = "\n".join(dep_lines)
    return rf"""
  ██████╗ ██╗   ██╗██╗████████╗ ██████╗ ██╗
  ██╔══██╗╚██╗ ██╔╝██║╚══██╔══╝██╔═══██╗██║
  ██████╔╝ ╚████╔╝ ██║   ██║   ██║   ██║██║
  ██╔═══╝   ╚██╔╝  ██║   ██║   ██║   ██║██║
  ██║        ██║   ██║   ██║   ╚██████╔╝███████╗
  ╚═╝        ╚═╝   ╚═╝   ╚═╝    ╚═════╝ ╚══════╝
  Phylogenetic Tree Visualization Automation
  version: {__version__}  license: {__license__}  date: {__release_date__}{hash_str}
  Dependencies:
{deps_str}
"""


_BANNER = _build_banner()


def _version_callback(value: bool):
    """Print version info and exit."""
    if value:
        from pyitol import __license__, __release_date__, __version__, get_dependency_versions, get_git_hash

        git_hash = get_git_hash()
        deps = get_dependency_versions()
        sys.stdout.write(f"pyitol {__version__}\n")
        sys.stdout.write(f"license: {__license__}\n")
        sys.stdout.write(f"date: {__release_date__}\n")
        if git_hash:
            sys.stdout.write(f"git: {git_hash}\n")
        sys.stdout.write("dependencies:\n")
        for name, ver in deps.items():
            sys.stdout.write(f"  {name}: {ver}\n")
        sys.stdout.flush()
        raise SystemExit(0)


app = typer.Typer(
    name="pyitol",
    help="PyiTOL - iTOL 可视化全流程自动化工具",
    add_completion=False,
    invoke_without_command=True,
)

app.add_typer(config_app, name="config")
app.add_typer(template_app, name="template")
app.add_typer(taxonomy_app, name="taxonomy")
app.add_typer(task_app, name="task")
app.add_typer(tree_app, name="tree")
app.add_typer(utils_app, name="utils")
app.add_typer(learn_app, name="learn")


class CLIState:
    """Global CLI state passed via Typer context."""

    verbose: bool = False
    quiet: bool = False
    low_memory: bool = False
    config_file: list[str] | None = None
    console: Console = Console()


@app.callback()
def main_callback(
    ctx: typer.Context,
    version: bool = typer.Option(False, "--version", help="显示版本号、Git哈希和依赖库版本"),
    verbose: bool = typer.Option(False, "--verbose", help="显示详细日志"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="仅显示关键信息"),
    config: list[str] | None = typer.Option(None, "--config", "-c", help="YAML/JSON 配置文件路径（可多次指定）"),
    log_file: str | None = typer.Option(None, "--log-file", help="日志文件路径(同时输出到文件)"),
    low_memory: bool = typer.Option(False, "--low-memory", help="低内存模式(适用于大型数据集)"),
):
    """PyiTOL - 基于 Python 的 iTOL 模板生成与分析工具"""
    _version_callback(version)

    import logging

    from pyitol.utils.logger import setup_logging

    if not quiet:
        sys.stdout.write(_BANNER + "\n")
        sys.stdout.flush()

    # Setup real-time logging (plain text, no color)
    if verbose:
        setup_logging(level=logging.DEBUG, show_time=True, log_file=log_file)
    elif quiet:
        setup_logging(level=logging.WARNING, show_time=False, log_file=log_file)
    else:
        setup_logging(level=logging.INFO, show_time=True, log_file=log_file)

    state = CLIState()
    state.verbose = verbose
    state.quiet = quiet
    state.low_memory = low_memory
    set_low_memory(low_memory)
    state.config_file = config
    if quiet:
        state.console = Console(quiet=True)
    else:
        state.console = Console()
    ctx.ensure_object(dict)
    ctx.obj["state"] = state
    if config:
        merged: dict = {}
        try:
            for cfg_path in config:
                data = _load_config_file(cfg_path)
                if isinstance(data, dict):
                    merged.update(data)
                elif isinstance(data, list):
                    # If config is a list of dicts, merge them sequentially
                    for item in data:
                        if isinstance(item, dict):
                            merged.update(item)
            ctx.obj["config_data"] = merged
        except Exception as e:
            sys.stdout.write(f"WARN 配置文件加载失败: {e}\n")
            sys.stdout.flush()
            ctx.obj["config_data"] = {}
    else:
        ctx.obj["config_data"] = {}


# =============================================================================
# VALIDATE COMMAND (top-level)
# =============================================================================


@app.command("validate")
def validate_command(
    ctx: typer.Context,
    tree: str | None = typer.Option(None, "--tree", "-t", help="树文件路径"),
    taxonomy: str | None = typer.Option(None, "--taxonomy", help="分类表格文件路径"),
    templates: list[str] | None = typer.Option(None, "--template", help="模板文件路径（可多次指定）"),
    colors: list[str] | None = typer.Option(None, "--color", help="颜色代码（可多次指定）"),
    sequence: str | None = typer.Option(None, "--sequence", "-s", help="序列文件路径"),
    alphabet: str = typer.Option("auto", "--alphabet", help="预期字母表: auto/DNA/RNA/protein/any"),
):
    """验证输入文件格式、颜色代码和节点ID一致性。

    支持的文件格式:
    - 树文件: Newick (.nwk/.newick/.tree), Nexus (.nexus/.nex)
    - 序列文件: FASTA (.fa/.fasta), FASTQ (.fq/.fastq)
    - 表格文件: CSV (.csv), TSV (.tsv), Excel (.xlsx/.xls)

    树文件深度验证: 括号平衡、分支长度非负、重复节点名、多根节点
    序列文件深度验证: 字母表检测、ID唯一性、长度一致性
    对抗性防护: 恶意字符检测、循环依赖检测、空文件检测
    """
    from pyitol.core.validator import (
        deep_validate_sequence,
        deep_validate_tree,
        detect_file_type,
        detect_taxonomy_circular_dependencies,
        validate_file_not_empty,
        validate_node_names,
    )

    session = SessionContext()
    console = get_console(ctx)
    has_error = False

    try:
        # Check for empty files first
        for path, _label in [(tree, "树文件"), (taxonomy, "分类表格"), (sequence, "序列文件")]:
            if path:
                empty_errors = validate_file_not_empty(path)
                for e in empty_errors:
                    console.print(f"  CRIT {e}")
                    has_error = True

        # Deep validate tree file
        if tree and not has_error:
            console.print(f"\n  检查树文件: {tree}")
            tree_result = deep_validate_tree(tree)

            # Format
            console.print(f"    格式: {tree_result['format']}")

            # Info
            info = tree_result.get("info", {})
            if "tree_count" in info:
                console.print(f"    树数量: {info['tree_count']}")
            if "tip_count" in info:
                console.print(f"    末端数: {info['tip_count']}")
            if "node_count" in info:
                console.print(f"    节点数: {info['node_count']}")
            if info.get("has_branch_lengths"):
                console.print("    分支长度: 有")

            # Multi-tree info
            for i, ti in enumerate(tree_result.get("trees", [])):
                if len(tree_result["trees"]) > 1:
                    console.print(
                        f"    Tree #{i + 1}: {ti.get('tip_count', '?')} tips, {ti.get('node_count', '?')} nodes"
                    )

            # Warnings
            for w in tree_result.get("warnings", []):
                console.print(f"    WARN {w}")

            # Errors
            for e in tree_result.get("errors", []):
                console.print(f"    ERR {e}")
                has_error = True

            if tree_result["valid"]:
                console.print("    OK 树文件验证通过")
            else:
                console.print("    FAIL 树文件验证失败")

        # Deep validate sequence file
        if sequence:
            console.print(f"\n  检查序列文件: {sequence}")
            seq_result = deep_validate_sequence(sequence, expected_alphabet=alphabet)

            console.print(f"    格式: {seq_result['format']}")
            console.print(f"    字母表: {seq_result.get('alphabet', 'unknown')}")

            info = seq_result.get("info", {})
            if "sequence_count" in info:
                console.print(f"    序列数: {info['sequence_count']}")
            if "min_length" in info:
                console.print(f"    长度范围: {info['min_length']} - {info['max_length']}")

            for w in seq_result.get("warnings", []):
                console.print(f"    WARN {w}")

            for e in seq_result.get("errors", []):
                console.print(f"    ERR {e}")
                has_error = True

            if seq_result["valid"]:
                console.print("    OK 序列文件验证通过")
            else:
                console.print("    FAIL 序列文件验证失败")

        # Original validation
        result = validate_inputs(
            tree_path=tree,
            metadata_path=taxonomy,
            template_paths=cast(list[str | Path] | None, templates),
            colors=colors,
        )

        if taxonomy:
            console.print(f"\n  检查分类表格: {taxonomy}")
            tax_info = detect_file_type(taxonomy)
            if tax_info["exists"]:
                console.print(f"    格式: {tax_info['format']}")
            for e in tax_info.get("errors", []):
                console.print(f"    ERR {e}")

            # Check for circular dependencies in taxonomy
            circ_errors = detect_taxonomy_circular_dependencies(taxonomy)
            for e in circ_errors:
                console.print(f"    ERR {e}")
                has_error = True

        # Check for malicious node names in tree
        if tree:
            try:
                from pyitol.core.parser import get_single_tree

                tree_obj = get_single_tree(tree)
                tip_names = [n.taxon.label for n in tree_obj.leaf_nodes() if n.taxon]
                malicious = validate_node_names(tip_names)
                if malicious:
                    console.print("\n  检查节点名称安全性:")
                    for e in malicious:
                        console.print(f"    ERR {e}")
                        has_error = True
            except Exception:  # noqa: S110
                pass  # Skip if tree parsing failed earlier

        for w in result.get("warnings", []):
            console.print(f"  WARN {w}")

        for e in result.get("errors", []):
            console.print(f"  ERR {e}")
            has_error = True

        if has_error:
            session.log_error("验证失败")
            # Validation failure uses the dedicated exit code 3, distinct from
            # generic errors (typer.Exit(1)), so callers (e.g. CI) can tell the
            # failure type apart; this is an intentionally kept CLI contract.
            raise typer.Exit(3)

        console.print("\n  OK 所有验证通过")
        session.log_validate(f"tree={tree}, taxonomy={taxonomy}", "validate")
        session.save_snapshot()
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"  FAIL 验证失败: {e}")
        raise typer.Exit(1)


# =============================================================================
# TEMPLATE CREATE COMMANDS
# =============================================================================

# =============================================================================
# REPLAY COMMAND
# =============================================================================


def _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column="id", multi_tree="error"):
    """Load tree and taxonomy, filter taxonomy to tree tips. Returns (tree, df, tip_set)."""
    from pyitol.core.parser import get_single_tree
    from pyitol.core.taxonomy import _normalize_taxonomy_df

    tree = get_single_tree(tree_path, multi_tree=multi_tree)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    df = _normalize_taxonomy_df(df, id_column)
    df = df[df["id"].isin(tip_set)]
    return tree, df, tip_set


# ---------------------------------------------------------------------------
# Generator function registry (replaces globals() lookups in replay dispatch)
# Uses sys.modules lookup so that test patches on pyitol.cli.main.<func> work.
# ---------------------------------------------------------------------------
def _resolve_generator(func_or_name):
    """Compatibility shim: generator is already a Callable."""
    return func_or_name if callable(func_or_name) else None


class ReplayTemplateDispatch(TypedDict):
    handler: Callable
    generator: Callable
    label: str


# ---------------------------------------------------------------------------
# Replay dispatch registry (10.1 plugin architecture)
# ---------------------------------------------------------------------------
# Replaces the 30+ elif chain in replay_command with a dynamic dispatch table.
# New template types can register their replay handler here or via
# REPLAY_SPECIAL_HANDLERS decorator.
# ---------------------------------------------------------------------------


def _replay_column_template(func_or_name, action, params, outputs, taxonomy_path, tree_path, id_column, console):
    """Generic replay for templates requiring a single 'column' parameter."""
    func = _resolve_generator(func_or_name) if isinstance(func_or_name, str) else func_or_name
    if func is None:
        console.print(f"    [bold red]↳ 未知的模板生成函数: {func_or_name}[/]")
        return "skipped"
    column = params.get("column")
    output = outputs.get(action, f"{action.replace('template_', '')}.txt")
    if column and taxonomy_path and tree_path:
        func(output, taxonomy_path, tree_path, column, id_column=id_column)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


def _replay_columns_template(func_or_name, action, params, outputs, taxonomy_path, tree_path, id_column, console):
    """Generic replay for templates requiring a 'columns' list parameter."""
    func = _resolve_generator(func_or_name) if isinstance(func_or_name, str) else func_or_name
    if func is None:
        console.print(f"    [bold red]↳ 未知的模板生成函数: {func_or_name}[/]")
        return "skipped"
    columns = params.get("columns", "").split(",") if params.get("columns") else []
    output = outputs.get(action, f"{action.replace('template_', '')}.txt")
    if columns and taxonomy_path and tree_path:
        func(output, taxonomy_path, tree_path, columns, id_column=id_column)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


def _replay_no_column_template(func_or_name, action, params, outputs, taxonomy_path, tree_path, id_column, console):
    """Generic replay for templates not requiring a column parameter."""
    func = _resolve_generator(func_or_name) if isinstance(func_or_name, str) else func_or_name
    if func is None:
        console.print(f"    [bold red]↳ 未知的模板生成函数: {func_or_name}[/]")
        return "skipped"
    output = outputs.get(action, f"{action.replace('template_', '')}.txt")
    if taxonomy_path and tree_path:
        func(output, taxonomy_path, tree_path, id_column=id_column)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"  # pragma: no cover


# Standard taxonomy/tree-based templates dispatched by parameter type
REPLAY_TEMPLATE_DISPATCH: dict[str, ReplayTemplateDispatch] = {
    "template_color_strip": {
        "handler": _replay_column_template,
        "generator": generate_color_strip_template,
        "label": "color_strip",
    },
    "template_branch": {
        "handler": _replay_column_template,
        "generator": generate_branch_template,
        "label": "branch",
    },
    "template_simple_bar": {
        "handler": _replay_column_template,
        "generator": generate_simple_bar_template,
        "label": "simple_bar",
    },
    "template_symbols": {
        "handler": _replay_column_template,
        "generator": generate_symbols_template,
        "label": "symbols",
    },
    "template_gradient": {
        "handler": _replay_column_template,
        "generator": generate_gradient_template,
        "label": "gradient",
    },
    "template_text": {
        "handler": _replay_column_template,
        "generator": generate_text_template,
        "label": "text",
    },
    "template_external_shape": {
        "handler": _replay_column_template,
        "generator": generate_external_shape_template,
        "label": "external_shape",
    },
    "template_multi_bar": {
        "handler": _replay_columns_template,
        "generator": generate_multibar_template,
        "label": "multi_bar",
    },
    "template_heatmap": {
        "handler": _replay_columns_template,
        "generator": generate_heatmap_template,
        "label": "heatmap",
    },
    "template_pie": {
        "handler": _replay_columns_template,
        "generator": generate_pie_template,
        "label": "pie",
    },
    "template_linechart": {
        "handler": _replay_columns_template,
        "generator": generate_linechart_template,
        "label": "linechart",
    },
    "template_boxplot": {
        "handler": _replay_no_column_template,
        "generator": generate_boxplot_template,
        "label": "boxplot",
    },
    "template_arrow": {
        "handler": _replay_no_column_template,
        "generator": generate_arrow_template,
        "label": "arrow",
    },
    "template_image": {
        "handler": _replay_no_column_template,
        "generator": generate_image_template,
        "label": "image",
    },
    "template_alignment": {
        "handler": _replay_no_column_template,
        "generator": generate_alignment_template,
        "label": "alignment",
    },
    "template_tanglegram": {
        "handler": _replay_no_column_template,
        "generator": generate_tanglegram_template,
        "label": "tanglegram",
    },
    "template_placement": {
        "handler": _replay_no_column_template,
        "generator": generate_placement_template,
        "label": "placement",
    },
    "template_timescale": {
        "handler": _replay_no_column_template,
        "generator": generate_timescale_template,
        "label": "timescale",
    },
    "template_meme": {
        "handler": _replay_no_column_template,
        "generator": generate_meme_template,
        "label": "meme",
    },
    "template_manual": {
        "handler": _replay_no_column_template,
        "generator": generate_manual_template,
        "label": "manual",
    },
    "template_external_shape_bubble": {
        "handler": _replay_columns_template,
        "generator": generate_external_shape_bubble_template,
        "label": "external_shape_bubble",
    },
}

# Special handlers for non-standard replay logic
REPLAY_SPECIAL_HANDLERS: dict[str, Callable] = {}


def _register_special_handler(action: str):
    """Decorator to register a custom replay handler for a template action."""

    def decorator(func):
        REPLAY_SPECIAL_HANDLERS[action] = func
        return func

    return decorator


@_register_special_handler("template_tree_colors")
def _replay_tree_colors(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    column = params.get("column")
    output = outputs.get(action, "tree_colors.txt")
    if column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "type": "clade", "color": colors_dict.get(val, "#999999")})
        generate_tree_colors_template(output, data)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_binary")
def _replay_binary(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    columns = params.get("columns", "").split(",") if params.get("columns") else []
    output = outputs.get(action, "binary.txt")
    if columns and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        data = []
        for _, row in df.iterrows():
            row_data = {"id": row["id"]}
            for col in columns:
                row_data[col] = "1" if col in row and not pd.isna(row[col]) and str(row[col]).strip() != "" else "0"
            data.append(row_data)
        field_colors = ["#ff0000", "#00ff00", "#0000ff"]
        field_shapes = ["1", "2", "3"]
        generate_binary_template(output, data, columns, field_colors, field_shapes, separator="TAB")
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_labels")
def _replay_labels(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    label_column = params.get("label_column") or params.get("column")
    output = outputs.get(action, "labels.txt")
    if label_column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        data = [
            {"id": row["id"], "label": str(row[label_column])}
            for _, row in df.iterrows()
            if not pd.isna(row[label_column])
        ]
        generate_labels_template(output, data)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_popup_info")
def _replay_popup_info(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    output = outputs.get(action, "popup_info.txt")
    if taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        data = [
            {"id": row["id"], "title": str(row.get("title", "")), "content": str(row.get("content", ""))}
            for _, row in df.iterrows()
        ]
        generate_popup_info_template(output, data)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_collapse")
def _replay_collapse(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    node_ids = params.get("node_ids", "").split(",") if params.get("node_ids") else []
    output = outputs.get(action, "collapse.txt")
    if node_ids:
        generate_collapse_template(output, node_ids)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_prune")
def _replay_prune(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    node_ids = params.get("node_ids", "").split(",") if params.get("node_ids") else []
    output = outputs.get(action, "prune.txt")
    if node_ids:
        generate_prune_template(output, node_ids)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_ranges")
def _replay_ranges(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    column = params.get("column")
    output = outputs.get(action, "ranges.txt")
    if column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)
        data = []
        for group_name, group_df in df.groupby(column):
            members = sorted(group_df["id"].tolist())
            if len(members) >= 2:
                tip1 = members[0]
                tip2 = members[-1]
                data.append(
                    {"id": f"{tip1}|{tip2}", "label": group_name, "color": colors_dict.get(group_name, "#999999")}
                )
            elif len(members) == 1:
                data.append({"id": members[0], "label": group_name, "color": colors_dict.get(group_name, "#999999")})
        generate_ranges_template(output, data)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_highlight")
def _replay_highlight(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    column = params.get("column")
    output = outputs.get(action, "highlight.txt")
    if column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            data.append({"id": row["id"], "type": "label_background", "color": colors_dict.get(val, "#999999")})
        schema = create_schema("style", label="highlight", color="#ff0000", separator="TAB")
        schema.columns = ["id", "type", "color"]
        schema.data_rows = data
        gen = TemplateGenerator()
        gen.add_schema(schema)
        gen.write(output)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_style")
def _replay_style(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    column = params.get("column")
    output = outputs.get(action, "style.txt")
    if column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
        unique_vals = sorted(df[column].dropna().unique())
        colors_dict = assign_colors_to_categories(unique_vals)
        style_type = params.get("style_type", "branch")
        data = []
        for _, row in df.iterrows():
            val = row[column]
            if pd.isna(val):
                continue
            color = colors_dict.get(val, "#999999")
            if style_type == "branch":
                data.append({"id": row["id"], "type": "branch", "color": color, "style": "normal", "size": "1"})
            elif style_type == "label":
                data.append({"id": row["id"], "type": "label", "color": color, "font": "Arial", "size": "1"})
            elif style_type == "label_background":
                data.append({"id": row["id"], "type": "label_background", "color": color, "size": "1"})
        generate_style_template(output, data)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_branch_gradient")
def _replay_branch_gradient(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    column = params.get("column")
    output = outputs.get(action, "branch_gradient.txt")
    if column and taxonomy_path and tree_path:
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_path, taxonomy_path, id_column)
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
        schema = create_schema("gradient", label="branch_gradient", separator="TAB")
        schema.columns = ["id", "value", "color"]
        schema.data_rows = data
        gen = TemplateGenerator()
        gen.add_schema(schema)
        gen.write(output)
        console.print(f"    [bold green]↳ 复现 {action}: {output}[/]")
        return "replayed"
    return "skipped"


@_register_special_handler("template_connections")
def _replay_connections(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    console.print(f"    [bold yellow]↳ {action} 需要连接对数据文件，请手动检查参数后执行[/]")
    return "skipped"


@_register_special_handler("template_domains")
def _replay_domains(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    console.print(f"    [bold yellow]↳ {action} 需要域数据JSON文件，请手动检查参数后执行[/]")
    return "skipped"


@_register_special_handler("template_spacing")
def _replay_spacing(action, params, outputs, taxonomy_path, tree_path, id_column, console):
    console.print(f"    [bold yellow]↳ {action} 需要间距数据文件，请手动检查参数后执行[/]")
    return "skipped"


@app.command("replay")
def replay_command(
    ctx: typer.Context,
    session_file: str = typer.Option(..., "--session", "-s", help="session.yaml 文件路径"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅显示建议命令，不实际执行"),
    use_command_line: bool = typer.Option(True, "--use-cli", help="优先使用记录的命令行参数直接复现"),
):
    """回放之前的操作记录。使用快照文件完全重现之前的操作，无需重新输入所有参数。"""
    console = get_console(ctx)
    session_data = SessionContext.load_from_file(session_file)
    console.print(f"[bold]回放操作记录: {session_file}[/]")

    # Compatibility: new format uses nested inputs/outputs; old format uses top-level keys
    inputs = session_data.get("inputs", {})
    outputs = session_data.get("outputs", {})
    tree_path = inputs.get("tree") or session_data.get("tree")
    taxonomy_path = inputs.get("taxonomy") or session_data.get("taxonomy")
    id_column = inputs.get("id_column") or session_data.get("id_column", "id")
    command_line = session_data.get("command_line", [])

    logs = session_data.get("logs", [])
    replayed = 0
    failed = 0
    skipped = 0

    # ------------------------------------------------------------------
    # Strategy 1: direct CLI replay when command_line is available
    # ------------------------------------------------------------------
    if use_command_line and command_line:
        console.print(f"[bold]检测到完整命令行记录，将直接复现: pyitol {' '.join(command_line)}[/]")
        if dry_run:
            console.print("  [dim]dry-run 模式，跳过实际执行[/]")
            skipped += 1
        else:
            from typer.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(app, command_line)
            if result.exit_code == 0:
                console.print("  [bold green]↳ 命令复现成功[/]")
                if result.output:
                    for line in result.output.strip().splitlines()[:10]:
                        console.print(f"    {line}")
                replayed += 1
            else:
                console.print(f"  [bold red]↳ 命令复现失败 (exit_code={result.exit_code})[/]")
                if result.output:
                    console.print(result.output)
                failed += 1
        # If CLI replay succeeded and there are no additional logs, summarize and exit
        if not logs or replayed > 0:
            console.print("\n[bold]回放完成。[/]")
            console.print(f"  成功复现: {replayed} | 跳过: {skipped} | 失败: {failed}")
            return

    # ------------------------------------------------------------------
    # Strategy 2: log-by-log replay (fallback for old snapshots or extra logs)
    # ------------------------------------------------------------------
    for log in logs:
        action = log.get("action", "unknown")
        detail = log.get("detail", "")
        ts = log.get("timestamp", "N/A")
        console.print(f"  [{ts}] {action}: {detail}")

        if dry_run:
            continue

        params = _parse_log_detail(detail)

        try:
            if action == "tree_info" and tree_path:
                info = get_tree_info(tree_path)
                console.print(f"    [dim]↳ 复现 tree-info: {info}[/]")
                replayed += 1
            elif action == "taxonomy_ranks" and taxonomy_path:
                ranks = get_ranks(taxonomy_path, id_column)
                console.print(f"    [dim]↳ 复现 taxonomy-ranks: {ranks}[/]")
                replayed += 1
            elif action == "taxonomy_extract" and taxonomy_path and tree_path:
                rank = params.get("rank", "phylum")
                output_path = outputs.get("taxonomy_extract", "taxonomy_extract.csv")
                result = extract_taxonomy_with_stats(taxonomy_path, tree_path, rank, output_path, id_column=id_column)
                console.print(f"    [dim]↳ 复现 taxonomy-extract: {len(result)} groups at {rank} → {output_path}[/]")
                replayed += 1
            elif action == "taxonomy_monophyly" and taxonomy_path and tree_path:
                rank = params.get("rank", "phylum")
                output_path = outputs.get("taxonomy_monophyly", "monophyly.csv")
                results = check_monophyly(taxonomy_path, tree_path, rank, id_column=id_column)
                pd.DataFrame(results).to_csv(output_path, index=False)
                console.print(f"    [dim]↳ 复现 taxonomy-monophyly: {len(results)} groups checked → {output_path}[/]")
                replayed += 1
            elif action == "validate" and tree_path:
                from pyitol.core.validator import validate_inputs

                validate_inputs(tree_path, taxonomy_path)
                console.print("    [dim]↳ 复现 validate: OK[/]")
                replayed += 1
            elif action == "task_upload" and tree_path:
                api_key = params.get("api_key")
                api_key_file = params.get("api_key_file")
                if api_key or api_key_file:
                    client = ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=3)
                    tree_id = client.upload(tree_path, [tree_path])
                    console.print(f"    [bold green]↳ 复现 upload: {tree_id}[/]")
                    replayed += 1
                else:
                    console.print(
                        f"    [bold yellow]↳ upload 操作缺少 API 密钥，请手动执行: pyitol task upload --tree {tree_path} ...[/]"  # noqa: E501
                    )
                    skipped += 1
            elif action == "task_export":
                upload_id = params.get("upload_id") or params.get("tree_id")
                api_key = params.get("api_key")
                api_key_file = params.get("api_key_file")
                if upload_id and (api_key or api_key_file):
                    client = ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=3)
                    fmt = params.get("format", "pdf")
                    export_results = client.export([upload_id], fmt=fmt)
                    console.print(f"    [bold green]↳ 复现 export: {export_results}[/]")
                    replayed += 1
                else:
                    console.print("    [bold yellow]↳ export 操作缺少 upload_id 或 API 密钥，请手动执行[/]")
                    skipped += 1
            elif action == "task_delete":
                upload_ids = params.get("upload_ids", [])
                api_key = params.get("api_key")
                api_key_file = params.get("api_key_file")
                if upload_ids and (api_key or api_key_file):
                    client = ITOLAPIClient(api_key=api_key, api_key_file=api_key_file, max_retries=3)
                    delete_results = client.batch_delete(upload_ids)
                    console.print(f"    [bold green]↳ 复现 delete: {delete_results}[/]")
                    replayed += 1
                else:
                    console.print("    [bold yellow]↳ delete 操作缺少 upload_id 或 API 密钥，请手动执行[/]")
                    skipped += 1
            # ------------------------------------------------------------------
            # Dynamic template replay dispatch (10.1 plugin architecture)
            # ------------------------------------------------------------------
            elif action in REPLAY_TEMPLATE_DISPATCH and taxonomy_path and tree_path:
                entry = REPLAY_TEMPLATE_DISPATCH[action]
                handler = entry["handler"]
                generator = entry["generator"]
                status = handler(generator, action, params, outputs, taxonomy_path, tree_path, id_column, console)
                if status == "replayed":
                    replayed += 1
                else:
                    skipped += 1
            elif action in REPLAY_SPECIAL_HANDLERS:
                status = REPLAY_SPECIAL_HANDLERS[action](
                    action, params, outputs, taxonomy_path, tree_path, id_column, console
                )
                if status == "replayed":
                    replayed += 1
                else:
                    skipped += 1
            elif action.startswith("template_"):
                template_type = action.replace("template_", "")
                out_files = list(outputs.values())
                console.print(f"    [dim]↳ 模板 [{template_type}] 历史输出: {out_files}[/]")
                replayed += 1
            elif action.startswith("taxonomy_"):
                out_files = list(outputs.values())
                console.print(f"    [dim]↳ 分类分析历史输出: {out_files}[/]")
                replayed += 1
            else:
                console.print("    [bold yellow]↳ 暂不支持自动复现，请手动执行[/]")
                skipped += 1
        except Exception as e:
            console.print(f"    [bold red]↳ 复现失败: {e}[/]")
            failed += 1

    console.print(f"\n[bold]回放完成。共 {len(logs)} 条操作记录。[/]")
    console.print(f"  成功复现: {replayed} | 跳过: {skipped} | 失败: {failed}")
    if tree_path:
        console.print(f"  树文件: {tree_path}")
    if taxonomy_path:
        console.print(f"  分类表格: {taxonomy_path}")
    if outputs:
        console.print(f"  生成文件: {list(outputs.values())}")
    if dry_run:
        console.print("[bold yellow]提示: 去掉 --dry-run 可尝试自动复现部分命令[/]")


# =============================================================================
# SELF-TEST COMMAND
# =============================================================================


@app.command("self-test")
def self_test_command(
    ctx: typer.Context,
):
    """执行自检：验证依赖库、示例解析、单系群判定逻辑。

    输出 [PASS]/[FAIL] 表格，退出码 0 表示全部通过。
    """
    console = get_console(ctx)
    results = []

    # 1. Check required dependencies
    deps = [
        ("typer", "typer", "0.15.0"),
        ("rich", "rich", "13.0"),
        ("pandas", "pandas", "2.0"),
        ("dendropy", "dendropy", "4.6"),
        ("pydantic", "pydantic", "2.5"),
        ("PyYAML", "yaml", "6.0"),
        ("requests", "requests", "2.31"),
        ("numpy", "numpy", "1.24"),
    ]

    for display_name, import_name, _min_version in deps:
        try:
            mod = __import__(import_name)
            ver = getattr(mod, "__version__", "unknown")
            results.append((f"Import {display_name}", "PASS", f"v{ver}"))
        except ImportError as e:
            results.append((f"Import {display_name}", "FAIL", str(e)))

    # 2. Check internal modules
    internal_modules = [
        "pyitol.core.parser",
        "pyitol.core.taxonomy",
        "pyitol.core.monophyly",
        "pyitol.core.validator",
        "pyitol.templates.generator",
        "pyitol.utils.io",
        "pyitol.utils.logger",
        "pyitol.utils.shutdown",
    ]
    for mod_name in internal_modules:
        try:
            __import__(mod_name)
            results.append((f"Import {mod_name.split('.')[-1]}", "PASS", ""))
        except ImportError as e:
            results.append((f"Import {mod_name.split('.')[-1]}", "FAIL", str(e)))

    # 3. Test sample tree parsing
    try:
        import tempfile

        sample_tree = "(A:0.1,B:0.2,(C:0.3,D:0.4):0.5);"
        with tempfile.NamedTemporaryFile(suffix=".nwk", mode="w", delete=False) as f:
            f.write(sample_tree)
            tmp_path = f.name
        os.chmod(tmp_path, 0o600)

        from pyitol.core.parser import get_single_tree

        tree = get_single_tree(tmp_path)
        tip_count = len(tree.leaf_nodes())
        Path(tmp_path).unlink()

        if tip_count == 4:
            results.append(("Parse sample Newick", "PASS", f"{tip_count} tips"))
        else:
            results.append(("Parse sample Newick", "FAIL", f"Expected 4 tips, got {tip_count}"))
    except Exception as e:
        results.append(("Parse sample Newick", "FAIL", str(e)))

    # 4. Test taxonomy extraction from embedded format
    try:
        sample_tree2 = "GB_GCA_0001_d_Bacteria_p_Proteo_c_Gamma_o_Enter_f_Enter_g_Escherichia;"
        with tempfile.NamedTemporaryFile(suffix=".nwk", mode="w", delete=False) as f:
            f.write(sample_tree2)
            tmp_path = f.name
        os.chmod(tmp_path, 0o600)

        from pyitol.core.taxonomy import extract_taxonomy_from_tip_names

        df = extract_taxonomy_from_tip_names(tmp_path, name_format="embedded")
        Path(tmp_path).unlink()

        if "Domain" in df.columns and df.iloc[0].get("Domain") == "Bacteria":
            results.append(("Extract embedded taxonomy", "PASS", "Domain=Bacteria"))
        else:
            results.append(("Extract embedded taxonomy", "FAIL", f"Columns: {list(df.columns)}"))
    except Exception as e:
        results.append(("Extract embedded taxonomy", "FAIL", str(e)))

    # 5. Test monophyly check with sample data
    try:
        # Create a simple tree and taxonomy for monophyly test
        tree_str = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
        with tempfile.NamedTemporaryFile(suffix=".nwk", mode="w", delete=False) as f:
            f.write(tree_str)
            tree_path = f.name
        os.chmod(tree_path, 0o600)

        tax_content = "id\tGroup\nA\tG1\nB\tG1\nC\tG2\nD\tG2\n"
        with tempfile.NamedTemporaryFile(suffix=".tsv", mode="w", delete=False) as f:
            f.write(tax_content)
            tax_path = f.name
        os.chmod(tax_path, 0o600)

        from pyitol.core.monophyly import check_monophyly

        mono_results = check_monophyly(tax_path, tree_path, "Group")
        Path(tree_path).unlink()
        Path(tax_path).unlink()

        statuses = {r["group"]: r["status"] for r in mono_results}
        if statuses.get("G1") == "monophyletic" and statuses.get("G2") == "monophyletic":
            results.append(("Monophyly detection", "PASS", "G1=mono, G2=mono"))
        else:
            results.append(("Monophyly detection", "FAIL", str(statuses)))
    except Exception as e:
        results.append(("Monophyly detection", "FAIL", str(e)))

    # 6. Test adversarial input detection
    try:
        from pyitol.core.validator import detect_malicious_node_names

        malicious = detect_malicious_node_names(["normal", "bad\x00name", "safe"])
        if len(malicious) == 1 and malicious[0] == "bad\x00name":
            results.append(("Malicious name detection", "PASS", "Caught 1"))
        else:
            results.append(("Malicious name detection", "FAIL", f"Got {malicious}"))
    except Exception as e:
        results.append(("Malicious name detection", "FAIL", str(e)))

    # Print results table
    console.print("\n  PyiTOL Self-Test Results")
    console.print("  " + "=" * 55)

    all_pass = True
    for name, status, detail in results:
        tag = "[PASS]" if status == "PASS" else "[FAIL]"
        detail_str = f" ({detail})" if detail else ""
        console.print(f"  {tag} {name}{detail_str}")
        if status != "PASS":
            all_pass = False

    console.print("  " + "=" * 55)
    if all_pass:
        console.print("  All checks passed.")
    else:
        console.print("  Some checks failed. See above for details.")

    raise SystemExit(0 if all_pass else 1)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    """Main entry point with differentiated exit codes.

    Exit codes:
    - 0: Success
    - 1: Runtime error (dependency, internal error)
    - 2: Parameter/CLI usage error
    - 3: Input data format/content error
    - 130: User interrupt (SIGINT/Ctrl+C)
    """
    # Register signal handlers for graceful shutdown
    from pyitol.utils.shutdown import register_signal_handlers

    register_signal_handlers()

    try:
        app()
    except KeyboardInterrupt:
        sys.stderr.write("\nInterrupted by user.\n")
        sys.stderr.flush()
        raise SystemExit(130)
    except (TreeParseError, MetadataParseError) as e:
        # Exit code 3: Input data format error
        console = Console()
        console.print(f"ERROR Data format error: {e}")
        raise SystemExit(3) from e
    except (APIKeyError, APIError, UploadError, ExportError) as e:
        # Exit code 1: Runtime/API error
        console = Console()
        console.print(f"ERROR API/Runtime error: {e}")
        raise SystemExit(1) from e
    except (ColorCodeError, SeparatorConflictError) as e:
        # Exit code 3: Input data content error
        console = Console()
        console.print(f"ERROR Data content error: {e}")
        raise SystemExit(3) from e
    except ValidationError as e:
        # Exit code 2: Validation/parameter error
        console = Console()
        console.print(f"ERROR Validation error: {e}")
        raise SystemExit(2) from e
    except TemplateError as e:
        # Exit code 3: Template error
        console = Console()
        console.print(f"ERROR Template error: {e}")
        raise SystemExit(3) from e
    except FileNotFoundError as e:
        # Exit code 3: Input file not found
        console = Console()
        console.print(f"ERROR File not found: {e}")
        raise SystemExit(3) from e
    except ValueError as e:
        # Exit code 2: Parameter error
        console = Console()
        console.print(f"ERROR Invalid value: {e}")
        raise SystemExit(2) from e
    except ConnectionError as e:
        console = Console()
        console.print(f"ERROR Connection error: {e}")
        raise SystemExit(1) from e
    except TimeoutError as e:
        console = Console()
        console.print(f"ERROR Timeout: {e}")
        raise SystemExit(1) from e
    except PermissionError as e:
        console = Console()
        console.print(f"ERROR Permission denied: {e}")
        raise SystemExit(1) from e
    except SessionError as e:
        console = Console()
        console.print(f"ERROR Session error: {e}")
        raise SystemExit(1) from e
    except PyiTOLBaseError as e:
        console = Console()
        console.print(f"ERROR PyiTOL error: {e}")
        raise SystemExit(1) from e
    except SystemExit:
        raise
    except Exception as e:
        console = Console()
        console.print(f"ERROR Unexpected error: {e}")
        console.print("  If this persists, please report with reproduction steps.")
        raise SystemExit(1) from e
