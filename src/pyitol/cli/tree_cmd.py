"""Tree Cmd commands."""

from pathlib import Path

import typer
from rich.table import Table

from pyitol.cli.apps import tree_app
from pyitol.cli.common import get_console
from pyitol.core.parser import format_support_values
from pyitol.utils.session import SessionContext
from pyitol.utils.tree_info import get_tree_info


@tree_app.command("info")
def tree_info_cmd(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
):
    """显示树文件的基本信息。"""
    info = get_tree_info(tree_path)
    console = get_console(ctx)
    table = Table(title=f"树信息: {Path(tree_path).name}")
    table.add_column("属性")
    table.add_column("值")
    for k, v in info.items():
        table.add_row(str(k), str(v))
    console.print(table)


@tree_app.command("format-support-values")
def tree_format_support(
    ctx: typer.Context,
    tree_path: str = typer.Option(..., "--tree", "-r", help="树文件路径"),
    output: str = typer.Option("formatted_tree.nwk", "--output", "-o", help="输出文件路径"),
):
    """格式化支持值显示(支持 IQ-TREE, RAxML, ALRT 等格式)。"""
    with open(tree_path, encoding="utf-8") as f:
        content = f.read()
    newick = format_support_values(content=content)
    Path(output).write_text(str(newick), encoding="utf-8")
    get_console(ctx).print(f"[bold green]✓ 支持值已格式化: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


# =============================================================================
# UTILS COMMANDS
# =============================================================================
