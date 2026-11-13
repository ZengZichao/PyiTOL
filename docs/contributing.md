# 贡献指南

[English](contributing_en.md) | 中文

> 本页为文档站版本，内容与仓库根目录的 `CONTRIBUTING_CN.md` 保持一致；修改时请两处同步，避免文档漂移。

感谢您对 PyiTOL 的兴趣！以下是参与项目开发的指南。

## 开始之前

1. Fork 本仓库并克隆您的 fork
2. 以开发模式安装：
   ```bash
   pip install -e ".[dev]"
   ```
3. 运行测试套件以验证您的环境（跳过需要真实 iTOL API Key 的集成测试）：
   ```bash
   pytest tests/ -m "not integration"
   ```

## 开发环境配置

**前置条件：**
- Python 3.10 或更高版本
- Git

**配置步骤：**

```bash
# 克隆您的 fork
git clone https://github.com/ZengZichao/PyiTOL.git
cd PyiTOL

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 以可编辑模式安装，并一并安装开发依赖
pip install -e ".[dev]"

# 安装 pre-commit 钩子
pre-commit install
```

## 项目结构

```
src/pyitol/
├── __main__.py             # python -m pyitol 入口
├── exceptions.py           # 各包共享的异常层次结构
├── api/                    # iTOL REST 客户端
│   └── client.py           # 基于单个 requests.Session 实现上传 / 查询 / 导出 / 删除；HTTPS 适配器对 429/5xx 的 POST 与 GET 请求做封顶指数退避重试
├── cli/                    # CLI 入口（基于 Typer）
│   ├── apps.py             # 各命令组的 Typer app 定义
│   ├── main.py             # 主入口 + validate/replay/self-test
│   ├── common.py           # 共享 CLI 工具函数
│   ├── template_cmd.py     # 模板命令聚合器（重新导出各子模块）
│   ├── template_tools.py   # 统一的 create/bundle/validate 命令
│   ├── template_datasets.py # 数据集模板命令（create-xxx）
│   ├── template_treeops.py # 树结构命令（create-xxx）
│   ├── template_advanced.py # 高级模板命令（create-xxx，含 external-shape-bubble）
│   ├── task_cmd.py         # 任务命令（upload/export/delete）
│   ├── taxonomy_cmd.py     # 分类学命令
│   ├── tree_cmd.py         # 树信息命令
│   ├── config_cmd.py       # 配置文件管理命令
│   ├── utils_cmd.py        # 工具命令
│   └── learn_cmd.py        # 模板反向学习/逆向解析命令
├── core/                   # 核心逻辑
│   ├── parser.py           # 树/元数据解析
│   ├── taxonomy.py         # 分类信息提取
│   ├── monophyly.py        # 单系性检测
│   ├── validator.py        # 输入校验、错误码及其文案
│   ├── binary_convert.py   # 分类列 -> 二元矩阵
│   ├── connect_convert.py  # 0/1 矩阵 -> 连线配对
│   ├── column_group.py     # 数据列分组
│   └── count_tree.py       # 计数数据 -> 树格式
├── templates/              # 模板引擎
│   ├── generator.py        # 模板生成器（32 个类型专属 generate_* 写出函数 + generate_template）
│   ├── learner.py          # 反向解析器（模板文件 -> 结构化字典）
│   ├── schemas/            # Schema 类（base、annotations、datasets_simple、datasets_advanced、tree_structure）+ presets.py
│   └── presets/            # 调色板（nature、cell、colorblind）
└── utils/                  # 工具函数
    ├── session.py          # 会话快照
    ├── reporter.py         # iTOL API 错误翻译（仅中文）
    ├── color_tools.py      # 颜色工具
    ├── constants.py        # 共享常量
    ├── logger.py           # 日志
    ├── fasta.py            # FASTA 解析
    ├── io.py               # 文件发现、路径处理、文本编码的安全读取
    ├── tree_info.py        # 树拓扑 / 支持值统计
    ├── data_converters.py  # 数据集转换辅助函数
    └── shutdown.py         # 优雅退出
```

每个目录另有 `__init__.py`；`src/pyitol/` 还包含 `py.typed` 与由 setuptools_scm 生成的 `_version.py`。`templates/` 下**没有** `parser.py`——反向解析全部在 `templates/learner.py` 中实现。

## 代码规范

- **静态检查**：由 `ruff` 强制执行 PEP 8（`ruff check`）与 `ruff format` 格式化，行宽 120
- **类型注解**：所有函数签名与返回类型都必须标注。该要求实际由 `ruff` 的 `ANN` 规则系列强制（`pyproject.toml` 的 `[tool.ruff.lint] select`），其中 `src/pyitol/cli/*` 暂豁免 `ANN001`/`ANN201`/`ANN202` 等、`tests/**` 豁免整个 `ANN`；`mypy`（`[tool.mypy]`）只做类型一致性检查，并未开启 `disallow_untyped_defs`
- **文档字符串**：所有公共函数与类都必须编写 docstring
- **注释与文档字符串**：使用英文书写。中文/英文文案仅用于*面向用户*的文本（CLI 帮助、`core/validator.py` 产生的校验错误文案、`utils/reporter.py` 输出的 iTOL API 错误译文、日志），不用于面向开发者的代码文档。
- **CLI 参数**：每个选项都有长格式 `--flag`，不存在只有短选项的参数；常用选项另带短别名，但短别名的含义随命令而变——`-o` 几乎处处是 `--output`（仅 `template bundle` 为 `--output-dir`）；`-t` 在 `taxonomy monophyly` 上是 `--taxonomy`、在 `template validate` 上是 `--template`、在顶层 `validate` 命令上却是 `--tree`；`-c` 在全局层是 `--config`、在 `template create` 下是 `--column`、在 `template create-heatmap` 下是 `--columns`、在 `template create-connections` 下是 `--connections`
- **错误信息**：校验错误文案来自 `src/pyitol/core/validator.py` 中的 `_ERROR_MESSAGES`，每个错误码同时维护中文与英文两份文案。中文既是默认语言，也是回退语言：当前语言为线程本地状态（默认 `zh`），传入未知的语言取值时回退到中文文案表，且 `set_error_language()` 仅接受 `zh`/`en`。相比之下，iTOL API 返回的错误文本只会被翻译为中文（`src/pyitol/utils/reporter.py`）。此外，包内没有任何代码调用 `set_error_language()`，CLI 选项与配置文件也不提供语言开关，因此命令行用户实际看到的始终是中文，详见 `error_codes.md`。

### 修复标签说明

`src/pyitol` 的注释中保留有历史 QA 评审轮次的可追溯性标记。对当前代码做全量普查（`grep -rhoE "\b(C|M|H|L|P|R)[0-9]+\b" src/pyitol --include="*.py"`，另加小写的 `m[0-9]+`）后，实际存在的标签只有以下几族：

- **C1**-**C5**：`core/monophyly.py` 单系性判定的正确性修复（严格按定义区分并系/复系、清空过期 tip 索引缓存、多分叉处理、按树加锁与后代缓存）
- **H1**、**H3**：iTOL 协议与数值编码的一致性说明（iTOL 无官方"树就绪状态"查询接口；`SYMBOL_SHAPE_MAP` 与 `EXTERNAL_SHAPE_MAP` 两套编码不可混用）
- **M1** 以及小写的 **m2**-**m5**、**m9**：零散的小型评审修订（URL 解析、抽取共享的 schema 探测工具、线程本地语言状态、扩充 CSS 命名色表、移除不安全的 `http://` 挂载）
- **L9**、**L10**：`templates/generator.py` 的样板收敛（统一的 schema 写出）与共享映射表一致性
- **P1-x**、**P2-x**：按优先级编号的评审条目（P1 优先于 P2），实际编号为 `P1-7`…`P1-12`、`P1-17`、`P2-26`、`P2-29`，其中 `P1-xx` 指同批未单独编号的条目

代码中并不存在下列取值，请勿引用：`R*` 系列完全没有出现；`M2`-`M7`、`H2`/`H4`、`L3`-`L8`、`L11`-`L12`、`P3` 亦无对应标签。另有两类易被误认作修复标签的写法：`core/validator.py` 中 `ErrorCode` 的 `V001`-`V024` 是校验错误码（见 `error_codes.md`），`core/validator.py` 注释里的 "C0/C1 range" 指 Unicode 控制字符区段；而 `core/monophyly.py` 中孤立的 `V3` 只是旧编号残留。

新的贡献不应再添加此类标签；请直接在注释与 CHANGELOG 中描述改动本身。

提交前请运行 linter：

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### 工具链与质量闸门

PyiTOL 的本地闸门并不覆盖 CI 的全部检查：`pre-commit` 只镜像了 ruff 相关的两项检查，`mypy`、`pyitol self-test` 与测试套件仅在 CI 中运行：

- **pre-commit**（`.pre-commit-config.yaml`）：仅定义了两个钩子——`ruff`（带 `--fix`）与 `ruff-format`，每次提交时依次执行。
- **ruff / ruff-format**：静态检查与格式化，行宽 120；CI 中对应执行 `ruff check src/ tests/` 与 `ruff format --check src/ tests/`。
- **mypy**：对 `src/pyitol` 进行静态类型检查（配置位于 `pyproject.toml` 的 `[tool.mypy]`）。它**不是** pre-commit 钩子，只在 CI 的独立步骤里运行 `mypy src/pyitol`（见 `.github/workflows/ci.yml`），因此推送前请自行在本地执行一次。
- **pytest**：CI 实际执行的命令是 `pytest tests/ --cov=pyitol --cov-report=xml -m "not integration"`，在 **3.10、3.11、3.12、3.13** 的 Python 矩阵与 Ubuntu、macOS、Windows 三种运行环境中并行；覆盖率报告仅由 Python 3.12 + Ubuntu 的任务上传至 Codecov。此外 `pyproject.toml` 的 `[tool.pytest.ini_options] addopts` 已默认附带 `--cov=pyitol --cov-fail-under=80`，因此直接运行 `pytest` 同样会强制覆盖率闸门。

安装并运行钩子：

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## 提交信息规范

本项目遵循 [Conventional Commits](https://www.conventionalcommits.org/)。请使用 `<type>(<scope>): <summary>` 格式，其中 `<type>` 取以下之一：

- `feat`：新功能
- `fix`：缺陷修复
- `docs`：仅文档改动
- `test`：新增或更新测试
- `refactor`：既非新增功能也非修复缺陷的代码改动
- `chore`：维护、工具链或发布改动

`<scope>` 可选，用于指明受影响的模块（例如 `api`、`core`、`templates`、`cli`）。以下示例中，首行 `feat` 为符合规范的示意写法（当前提交历史中尚无 `feat` 提交），其余三行均取自真实提交记录：

```
feat(cli): add create-external-shape-bubble subcommand
fix(core,api): reject duplicate tip labels; warn on retried POST uploads
docs: add PyiTOL bioRxiv preprint citation
chore(release): prepare v1.0.3 (version bump, changelogs, pending DOI)
```

## 测试要求

所有新代码都必须附带测试。项目使用 `pytest`。

```bash
# 运行全部测试
pytest tests/ -v

# 输出覆盖率报告
pytest tests/ --cov=pyitol --cov-report=term-missing

# 运行指定模块的测试
pytest tests/core/test_monophyly.py -v

# 跳过集成测试（需要真实 iTOL API Key）
pytest tests/ -m "not integration"
```

**覆盖率闸门**：代码覆盖率**必须达到至少 80%**。这是一个硬性闸门，由 CI 通过 `pyproject.toml` 中的 `--cov-fail-under=80` 强制；将覆盖率拉低至 80% 以下的 Pull Request 会直接失败。

**测试布局约定**：测试按领域归类于 `tests/<area>/test_<feature>.py`，例如 `tests/core/test_monophyly.py`。

## 添加新的 iTOL 模板类型

PyiTOL 提供统一入口 `pyitol template create <类型>`，支持 **33 种模板类型**；此外共有 **34 个专用 `pyitol template create-*` 子命令**（上述 33 种再加上 `external-shape-bubble` 变体）。要为新的类型添加支持：

1. **定义模板名称**于 `src/pyitol/templates/schemas/` 下对应的子模块（`datasets_simple.py`、`datasets_advanced.py`、`tree_structure.py`、`annotations.py`）：用 `@register_template` 装饰 schema 类，使其登记进 `schemas/base.py` 的 `SCHEMA_MAP`，从而让 `create_schema("<type>", ...)` 对该模板的参数执行校验。

2. **实现生成逻辑**于 `src/pyitol/templates/generator.py`。该模块的生成器是**模块级函数**而非类方法，请参照现有函数新增一个同风格的 `generate_<type>_template()`（例如 `generate_binary_template`、`generate_color_strip_template`），内部用 `create_schema()` 构造 schema、再交给 `_write_schema_file()` 写出。

3. **添加 CLI 命令**于 `src/pyitol/cli/` 下对应的 CLI 模块：
   - 数据集模板（color-strip、heatmap、bar、pie、symbols 等）放在 `template_datasets.py`
   - 树操作模板（tree-colors、collapse、prune、spacing、highlight、style 等）放在 `template_treeops.py`
   - 高级模板（linechart、image、alignment、tanglegram、placement、timescale、meme、manual、external-shape-bubble）放在 `template_advanced.py`

4. **注册别名**于 `template_tools.py` 的调度表：给处理器加上 `@_register_create("<type>", "<alias>", ...)` 装饰器，使 `pyitol template create <类型>` 也能路由到新生成器。

5. **添加测试**于 `tests/`，覆盖：
   - 使用合法输入的模板生成
   - 边界情况（空数据、字段缺失）
   - 输出格式校验

6. **更新文档**，并在适用时添加示例。

## 确定性行为

**本项目不包含任何随机算法或随机过程。** 所有输出（颜色分配、树解析、模板生成）都是确定性的，无需配置随机种子。

## 提交流程（Pull Request）

1. **从 `main` 创建特性分支**：
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **完成改动**并附带测试。保持提交聚焦，并遵循上文的提交信息规范。

3. **提交前自检**：
   ```bash
   # 全部测试通过
   pytest tests/ -v

   # 静态检查通过
   ruff check src/ tests/

   # 由 mypy 进行类型检查（配置位于 pyproject.toml 的 [tool.mypy]）
   mypy src/pyitol/
   ```

4. **提交 Pull Request**，并附上：
   - 对改动内容与原因的清晰描述
   - 相关 issue 的引用（如有）
   - 更新后的 CHANGELOG 条目（针对面向用户的改动）

5. **回应评审意见**。维护者（Maintainer）会在合理时间内评审您的 PR。

## 行为准则

本项目遵循 Contributor Covenant 行为准则（见仓库根目录的 `CODE_OF_CONDUCT_CN.md`，英文原版为 `CODE_OF_CONDUCT.md`）。
