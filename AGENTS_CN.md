# PyiTOL Agent 指南

[English](AGENTS.md) | 中文

## 项目简介

PyiTOL 是一个用于自动化 iTOL（Interactive Tree Of Life）系统发育树可视化的 Python CLI 工具。主包位于 `src/pyitol/`，入口为 `pyitol` 命令或 `python -m pyitol`。

## 代码结构

- `src/pyitol/api/` — iTOL HTTP API 客户端
- `src/pyitol/cli/` — Typer 命令行接口
- `src/pyitol/core/` — 树解析、分类法、单系性、输入校验
- `src/pyitol/templates/` — iTOL v7 模板生成与反向解析
- `src/pyitol/utils/` — 日志、会话、颜色、I/O 等工具
- `tests/` — pytest 测试套件

## 常用命令

```bash
# 开发安装
pip install -e ".[dev]"

# 运行测试（跳过需真实 iTOL API 密钥的集成测试）
pytest tests/ -m "not integration"

# 运行自检
pyitol self-test

# 代码检查与格式化
ruff check src/ tests/
ruff format src/ tests/
```

## 代码规范

- 遵循 PEP 8，行宽 120 字符
- 所有公共函数需类型提示与文档字符串（docstring）
- 错误文案为双语：`src/pyitol/core/validator.py` 的 `_ERROR_MESSAGES` 中中英文各维护一份表。运行时语言是线程本地的，默认中文；语言未知或缺失时回退到中文，而非英文。`src/pyitol/utils/reporter.py` 中的 iTOL API 错误翻译表仅有中文
- 保持确定性行为，避免随机算法

## 版本说明

`pyproject.toml` 使用 `setuptools_scm` 动态生成版本；非 git 仓库时回退到版本 `1.0.3`。`src/pyitol/__init__.py` 优先从 `_version.py` 读取版本，读取失败时回退到 `1.0.3`。
