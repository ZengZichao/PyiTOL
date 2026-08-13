"""Config Cmd commands."""

from pathlib import Path

import typer
import yaml

from pyitol.cli.apps import config_app
from pyitol.cli.common import get_console
from pyitol.utils.session import SessionContext


@config_app.command("init")
def config_init(
    ctx: typer.Context,
    output: str = typer.Option("pyitol_config.yaml", "--output", "-o", help="输出配置文件路径"),
    api_key_file: str = typer.Option(".itolapi.key", "--api-key-file", help="API密钥文件路径"),
    default_format: str = typer.Option("svg", "--default-format", help="默认导出格式"),
):
    """生成默认配置文件模板。"""
    session = SessionContext()
    config = {
        "api_key_file": str(Path(api_key_file).resolve()),
        "default_format": default_format,
        "output_directory": str(Path(".").resolve()),
        "template_directory": "",
        "tree_directory": "",
    }
    path = Path(output)
    path.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    session.log_config(config)
    session.save_snapshot(generated_files=[output])
    get_console(ctx).print(f"[bold green]✓ 配置文件已生成: {path}[/]")


# =============================================================================
# VALIDATE COMMAND (top-level)
# =============================================================================
