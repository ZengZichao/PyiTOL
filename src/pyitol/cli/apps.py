"""Typer app definitions for all CLI command groups."""

import typer

config_app = typer.Typer(help="配置文件管理")
template_app = typer.Typer(help="创建和管理 iTOL 模板文件")
taxonomy_app = typer.Typer(help="分类分析与单系性检测")
task_app = typer.Typer(help="iTOL API 任务管理（上传/导出/删除）")
tree_app = typer.Typer(help="树文件操作")
utils_app = typer.Typer(help="实用工具")
learn_app = typer.Typer(help="从已有模板反向学习")
