# PyiTOL 测试套件说明文档

本目录包含 **PyiTOL** 项目的完整自动化测试套件。测试遵循 **全面覆盖、不重复、不冗余** 的原则，使用 [pytest](https://docs.pytest.org/) 框架编写，覆盖项目所有核心模块、CLI 命令、API 客户端以及工具函数。

测试目录与源码包 `src/pyitol/` 一一对应，采用分层子目录结构组织。

---

## 目录结构

```
tests/
├── conftest.py                         # 全局共享 fixtures（树文件、分类表、API key 等）
├── test_concurrency.py                 # 并发与线程安全场景测试
├── test_exceptions.py                  # 异常类层次结构测试
├── test_main_entry.py                  # CLI 入口测试
├── test_realistic_data.py              # 真实数据场景测试
│
├── api/                                # API 客户端层测试
│   ├── test_client.py                  # ITOLAPIClient：上传/导出/删除/状态/响应解析
│   └── test_error_translation.py       # API 错误翻译与报告
│
├── cli/                                # CLI 命令层测试
│   ├── test_apps.py                    # 子应用注册
│   ├── test_common.py                  # CLI 公共工具（输出格式化、参数校验等）
│   ├── test_config.py                  # config 命令
│   ├── test_learn.py                   # learn 命令（template / palette / train-theme）
│   ├── test_main.py                    # 顶层命令（validate / replay 全量模板回放）
│   ├── test_task.py                    # task 命令（upload / export / delete / status）
│   ├── test_task_run.py                # task run 配置文件模式
│   ├── test_taxonomy.py                # taxonomy 子命令（ranks/extract/monophyly/convert）
│   ├── test_taxonomy_style.py          # taxonomy style 各 action
│   ├── test_template_advanced.py       # template 高级类型
│   ├── test_template_bundle.py         # template bundle 批量生成
│   ├── test_template_create.py         # template create 统一入口
│   ├── test_template_create_all.py     # template create 全类型遍历
│   ├── test_template_create_errors.py  # template create 错误容错
│   ├── test_template_create_extended.py# template create 扩展类型
│   ├── test_template_datasets.py       # template dataset 类模板
│   ├── test_template_edge_cases.py     # template 边界场景
│   ├── test_template_tools.py          # template 工具子命令
│   ├── test_template_treeops.py        # template 树操作类（collapse/prune/ranges 等）
│   ├── test_template_validate.py       # template validate
│   ├── test_tree.py                    # tree 子命令（info / format-support-values）
│   └── test_utils.py                   # utils 子命令
│
├── core/                               # 核心模块层测试
│   ├── test_binary_convert.py          # category_to_binary 二值化
│   ├── test_column_group.py            # group_columns 列分组
│   ├── test_connect_convert.py         # matrix_to_connect 连接转换
│   ├── test_count_tree.py              # count_to_tree
│   ├── test_monophyly.py               # 单系性检测
│   ├── test_parser.py                  # TreeParser / MetadataParser / format_support_values
│   ├── test_taxonomy.py                # 分类学提取与解析（GTDB/embedded/NCBI/mixed）
│   └── test_validator.py               # TemplateValidator / detect_file_type / validate_inputs
│
├── templates/                          # 模板模块层测试
│   ├── test_base.py                    # TemplateGenerator 基础引擎
│   ├── test_domain_exceptions_regression.py # 模板域异常回归（InvalidColumnError/TemplateError/TemplateTypeError）
│   ├── test_generator.py               # 全部 generate_*_template() 端到端生成
│   ├── test_learner.py                 # 模板反向学习 / train_theme
│   ├── test_presets.py                 # 预设与调色板（Nature/Cell/Colorblind）
│   ├── test_schemas_annotations.py     # 注释类 schema
│   ├── test_schemas_base.py            # 基础 schema 与 create_schema
│   ├── test_schemas_datasets_advanced.py # 高级 dataset schema
│   ├── test_schemas_datasets_simple.py # 简单 dataset schema
│   ├── test_schemas_presets.py         # 预设 schema
│   └── test_schemas_tree_structure.py  # 树结构类 schema
│
├── utils/                              # 工具模块层测试
│   ├── test_color_tools.py             # 颜色距离/梯度/分类着色
│   ├── test_data_converters.py         # 宽长转换/count_to_tree/group_columns/df_tree
│   ├── test_fasta.py                   # FASTA 读写迭代
│   ├── test_io.py                      # search_tree_file / find_first_tree_file
│   ├── test_reporter.py                # 错误翻译与报告
│   ├── test_session.py                 # SessionContext 生命周期与快照
│   ├── test_shutdown.py                # 信号处理与优雅关闭
│   └── test_tree_info.py               # extract_tree_info / get_tip_order 等
│
└── data/                               # 测试数据文件
    ├── 4taxa_monophyly.csv             # 单系性检验预期输出参考
    ├── 4taxa_tax_extract.csv           # 分类学提取预期输出参考
    ├── 4taxa_taxonomy.csv              # 示例分类学表格
    ├── 4taxa_tree.nwk                  # 4-tip 示例 Newick 树
    ├── template_bar.txt                # 模板参考文件
    ├── template_branch.txt
    ├── template_colorstrip.txt
    ├── template_heatmap.txt
    ├── template_style.txt
    └── template_symbols.txt
```

---

## 各层测试要点

### API 层（`api/`）

| 文件 | 测试对象 | 关键测试点 |
|---|---|---|
| `test_client.py` | `pyitol.api.client` | `ITOLAPIClient` 初始化（key / 文件 / 缺失）、上传成功/失败、导出（含 DPI）、批量/单条删除、`upload_and_export` 组合调用、状态查询、响应解析器 |
| `test_error_translation.py` | `pyitol.utils.reporter` | `translate_itol_api_error` 对关键字/常见/未知错误的翻译 |

### CLI 命令层（`cli/`）

| 文件 | 测试对象 | 关键测试点 |
|---|---|---|
| `test_main.py` | `pyitol.cli.main` | `validate` 命令、`replay` 命令对 **全部模板类型** 的回放（含成功/跳过/失败路径） |
| `test_task.py` / `test_task_run.py` | `pyitol.cli.task_cmd` | upload / export / upload-and-export / delete（交互/确认）/ status / task run 配置文件模式 |
| `test_taxonomy.py` / `test_taxonomy_style.py` | `pyitol.cli.taxonomy_cmd` | ranks / extract / extract-stats / monophyly / convert-binary / convert-connect / style 各 action |
| `test_template_*.py` | `pyitol.cli.template_cmd` / `template_advanced` / `template_datasets` / `template_tools` / `template_treeops` | 统一 `template create` 入口对 **30+ 模板类型** 的生成、别名、错误容错、bundle、validate、树操作类 |
| `test_tree.py` | `pyitol.cli.tree_cmd` | `tree info`、`tree format-support-values` |
| `test_utils.py` | `pyitol.cli.utils_cmd` | tree-info / search-tree-file / taxonomy-parse / wide-to-long / long-to-wide / count-to-tree / group-columns / binary / connections / preview / df-tree / learn-template |
| `test_learn.py` | `pyitol.cli.learn_cmd` | learn template（单/多文件）、learn palette、learn train-theme |
| `test_common.py` | `pyitol.cli.common` | 输出格式化、参数校验等公共工具 |
| `test_apps.py` | `pyitol.cli.apps` | 子应用注册 |
| `test_config.py` | `pyitol.cli.config_cmd` | config 命令 |

### 核心模块层（`core/`）

| 文件 | 测试对象 | 关键测试点 |
|---|---|---|
| `test_parser.py` | `pyitol.core.parser` | Newick / Nexus 解析、自动检测、tip/node 计数、深度、支持值格式检测（IQ-TREE/raxml/posterior）、`write_newick`、元数据 TSV/CSV/Excel 解析、列类型检测、树-元数据一致性、`format_support_values` |
| `test_taxonomy.py` | `pyitol.core.taxonomy` | `extract_taxonomy_from_tip_names`（GTDB/embedded/NCBI/mixed/auto）、`parse_taxonomy_string`、`check_monophyly`、`get_ranks` |
| `test_validator.py` | `pyitol.core.validator` | 颜色验证、分隔符冲突、`detect_file_type`（树/序列/表格/内容检测）、`TemplateValidator` 完整生命周期、`validate_inputs` |
| `test_monophyly.py` | `pyitol.core.monophyly` | 单系性检测各场景 |
| `test_binary_convert.py` / `test_connect_convert.py` / `test_column_group.py` / `test_count_tree.py` | 对应 core 转换模块 | 二值化 / 连接转换 / 列分组 / count-to-tree |

### 模板模块层（`templates/`）

| 文件 | 测试对象 | 关键测试点 |
|---|---|---|
| `test_generator.py` | `pyitol.templates.generator` | `TemplateGenerator` 引擎、**全部 30+ `generate_*_template()` 函数**端到端生成 |
| `test_learner.py` | `pyitol.templates.learner` | `HEADER_REVERSE` 完整性、单模板反向解析、`train_theme`（空/单/多文件聚合/JSON 序列化/容错） |
| `test_presets.py` | `pyitol.templates.presets` | 全部 schema preset、未知 preset 报错、Nature/Cell/Colorblind 调色板、色盲友好性 |
| `test_schemas_*.py` | `pyitol.templates.schemas.*` | base / annotations / datasets_simple / datasets_advanced / presets / tree_structure 各 schema 完整性 |
| `test_base.py` | `pyitol.templates.generator` | TemplateGenerator 基础引擎 |
| `test_domain_exceptions_regression.py` | `pyitol.templates.generator` / `presets` | 域异常回归：确认 InvalidColumnError/TemplateError/TemplateTypeError 而非裸 ValueError |

### 工具模块层（`utils/`）

| 文件 | 测试对象 | 关键测试点 |
|---|---|---|
| `test_color_tools.py` | `pyitol.utils.color_tools` | 颜色距离、相似度排序、梯度生成、分类着色、调色板循环 |
| `test_data_converters.py` | `pyitol.utils.data_converters` | 二值化、连接、宽长转换、count-to-tree、group_columns、df_tree |
| `test_fasta.py` | `pyitol.utils.fasta` | `fa_read` / `fa_write` / `fa_iter`、容错 |
| `test_io.py` | `pyitol.utils.io` | `search_tree_file` / `find_first_tree_file`、空目录容错 |
| `test_session.py` | `pyitol.utils.session` | `SessionContext` 生命周期、命令/输入输出记录、API 参数脱敏、快照保存/加载/重建 |
| `test_reporter.py` | `pyitol.utils.reporter` | 错误翻译与报告 |
| `test_shutdown.py` | `pyitol.utils.shutdown` | 信号处理与优雅关闭 |
| `test_tree_info.py` | `pyitol.utils.tree_info` | `extract_tree_info`、`get_node_count`、`get_tip_order`、`get_tree_info` |

### 顶层专题测试

| 文件 | 关键测试点 |
|---|---|
| `test_concurrency.py` | 并发与线程安全场景 |
| `test_exceptions.py` | 异常类层次结构与继承 |

---

## 运行测试

```bash
# 运行全部测试（跳过需真实 iTOL API 密钥的集成测试）
pytest tests/ -m "not integration"

# 运行特定层
pytest tests/core/ -v
pytest tests/cli/test_template_create.py -v

# 生成覆盖率报告（pyproject.toml 要求 ≥80%）
pytest tests/ -m "not integration" --cov=pyitol --cov-report=html
```

### 测试标记

`pyproject.toml` 中注册的 pytest marker：

- `integration` — 需要真实 iTOL API 凭据的集成测试（默认跳过）
- `slow` — 耗时较长的测试
- `stress` — 性能/压力测试
- `concurrency` — 并发/线程安全场景

### 可选依赖

部分测试需要可选依赖（在 `pyproject.toml` 的 `[project.optional-dependencies]` 中声明）：

- `excel` extra（`openpyxl`）：`test_parser.py::test_parse_excel` 测试 Excel 解析。未安装时该测试自动跳过（`pytest.importorskip`）。
- `memory` extra（`psutil`）：内存监控相关功能。

安装全部可选依赖：`pip install -e ".[dev,memory,excel]"`

---

## 设计原则

1. **单一职责**：每个测试文件对应一个源码模块或一个 CLI 命令组，避免跨模块耦合。
2. **分层对应**：`tests/` 子目录与 `src/pyitol/` 包结构一一对应（`api/` / `cli/` / `core/` / `templates/` / `utils/`）。
3. **共享 Fixtures**：`conftest.py` 集中管理常用测试数据（树文件、分类表、API key），消除跨文件重复 fixture。
4. **Mock 外部依赖**：所有 API 调用均使用 `unittest.mock.patch` 模拟 HTTP 请求，确保离线可运行。
5. **边界覆盖**：除正常路径外，每个模块均包含空输入、缺失文件、非法参数、越界数值等异常场景测试。
6. **无冗余**：已删除重复的 `test_cli_template_highlight.py`（并入 `test_template_create.py`）和 `test_dataset_style.py`（并入 `test_generator.py`）。
