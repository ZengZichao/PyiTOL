"""Learn Cmd commands."""

from __future__ import annotations

import json

import typer

from pyitol.cli.apps import learn_app
from pyitol.cli.common import get_console
from pyitol.templates.learner import learn_template, train_theme
from pyitol.templates.presets import get_palette, list_all_palettes
from pyitol.utils.session import SessionContext


@learn_app.command("template")
def learn_template_cmd(
    ctx: typer.Context,
    template_files: list[str] = typer.Option(..., "--template", "-t", help="模板文件路径(可多次指定)"),
    output: str = typer.Option("learned_config.json", "--output", "-o", help="输出文件路径"),
):
    """从已有 iTOL 模板文件反向学习配置。"""
    console = get_console(ctx)
    all_data = []
    for tf in template_files:
        data = learn_template(tf)
        all_data.append(data)

    with open(output, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=2, ensure_ascii=False)
    console.print(f"[bold green]✓ 已从 {len(template_files)} 个模板中学习: {output}[/]")
    SessionContext().save_snapshot(generated_files=[output])


@learn_app.command("palette")
def learn_palette_cmd(
    ctx: typer.Context,
    preset_name: str = typer.Option(..., "--preset-name", "-n", help="预设名称: nature/cell/colorblind"),
):
    """查看可用的配色预设。"""
    console = get_console(ctx)
    palettes = list_all_palettes()
    if preset_name in palettes:
        colors = get_palette(preset_name)
        console.print(f"[bold]{preset_name}[/] 预设包含 {len(colors)} 种颜色:")
        for i, c in enumerate(colors):
            console.print(f"  {i + 1}. [bold {c} on default]■[/] {c}")
    else:
        console.print(f"[bold red]✗ 未知预设: {preset_name}[/]")
        console.print(f"可用预设: {', '.join(palettes)}")


@learn_app.command("train-theme")
def learn_train_theme_cmd(
    ctx: typer.Context,
    template_dir: str = typer.Option(..., "--dir", "-d", help="模板文件目录路径"),
    output: str = typer.Option("trained_theme.json", "--output", "-o", help="输出主题配置文件路径"),
    min_freq: float = typer.Option(0.5, "--min-freq", help="推荐默认参数的最小频率阈值(0-1)"),
):
    """批量学习模板目录中的主题，生成各数据集类型的推荐默认参数。"""
    console = get_console(ctx)
    theme = train_theme(template_dir, min_freq=min_freq)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2, ensure_ascii=False)
    summary = theme.get("summary", {})
    console.print(
        f"[bold green]✓ 主题学习完成: {output} "
        f"({summary.get('total_files', 0)} 个文件, "
        f"{summary.get('total_datasets', 0)} 个数据集)[/]"
    )
    SessionContext().save_snapshot(generated_files=[output])
