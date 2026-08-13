# PyiTOL 示例说明文档

本目录包含 **PyiTOL** 项目的官方示例代码，分为两大类别：
- **`api_demos/`** — 演示 iTOL API 的完整功能（上传、导出、删除、状态查询）
- **`template_demos/`** — 演示 iTOL 模板文件的生成、批量处理与学术级绘图工作流

所有示例均遵循以下设计原则：
- **不重复、不冗余**：每个示例展示独特的功能组合或工作流模式
- **学术期刊发表级别**：使用 300 DPI 导出、英文项目名、色盲友好（colorblind-friendly）配色预设
- **完整覆盖**：示例 collectively 覆盖全部 31 种 iTOL 模板类型（含 `external-shape-bubble` 变体）以及 API 的所有核心方法

---

## 目录结构

```
examples/
├── api_demos/
│   ├── 01_basic_upload.py
│   ├── 02_multi_dataset_publication.py
│   ├── 03_advanced_api_operations.py
│   └── 04_batch_format_export.py
│
├── template_demos/
│   ├── 01_generate_all_template_types.py
│   ├── 02_batch_upload_existing_templates.py
│   ├── 03_publication_quality_figure.py
│   ├── 04_cli_workflow.py
│   └── 05_reverse_learn_template.py
│
└── README.md
```

---

## API Demos (`api_demos/`)

### 01_basic_upload.py
**性质**：最小可用示例（Minimal Working Example）
**用途**：演示最基础的 iTOL 工作流 —— 上传一棵系统发育树并导出为 PDF。
**关键特性**：
- `ITOLAPIClient` 初始化（自动读取 `.itolapi.key`）
- `upload_and_export()` 便捷方法
- 内置渲染轮询（`query_status`）等待就绪
- 适用于首次体验 PyiTOL API 的用户

### 02_multi_dataset_publication.py
**性质**：学术发表级综合示例
**用途**：演示如何上传 **多数据集组合**（color strip + heatmap + bar）并导出期刊级图片。
**关键特性**：
- 使用 `TemplateGenerator` 动态生成模板
- 应用 `colorblind` 预设调色板（Tol Bright）
- **300 DPI PDF** 导出（满足 Nature / Cell / ISME J 等期刊印刷要求）
- 同时导出 SVG 矢量图供后期编辑
- 英文项目名与专业数据集标签

### 03_advanced_api_operations.py
**性质**：API 全生命周期管理示例
**用途**：演示树上传后的完整管理操作，适合自动化流水线。
**关键特性**：
- `force=True` 覆盖已上传的同名将
- `query_status()` 渲染状态查询
- PNG（300 DPI）与 TIFF 双格式导出
- `batch_delete()` 批量清理临时上传

### 04_batch_format_export.py
**性质**：多格式批量导出示例
**用途**：单次上传后导出全部四种支持格式，避免重复上传浪费时间。
**关键特性**：
- PDF / SVG / PNG / TIFF 全覆盖
- 针对不同用途优化参数（PDF→印刷、SVG→矢量编辑、PNG→演示文稿、TIFF→期刊投稿）
- 统一的 `batch_export` 逻辑

---

## Template Demos (`template_demos/`)

### 01_generate_all_template_types.py
**性质**：模板类型兼容性全景测试
**用途**：程序化生成 **全部 31 种 iTOL v7 模板类型**（含 `external-shape-bubble` 变体），作为语法参考与引擎兼容性验证。
**关键特性**：
- 调用所有 `generate_*_template()` 函数
- 覆盖 `DATASET_SIMPLEBAR`、`DATASET_HEATMAP`、`DATASET_COLORSTRIP`、`TREE_COLORS`、`COLLAPSE`、`PRUNE`、`SPACING`、`DATASET_BINARY`、`DATASET_CONNECTION`、`DATASET_DOMAINS`、`DATASET_ALIGNMENT`、`DATASET_ARROWS`、`DATASET_TANGLEGRAM`、`DATASET_TIMESCALE`、`DATASET_MEME`、`DATASET_MANUAL` 等全部类型
- 输出至 `outputs/all_types/`，便于批量检查

### 02_batch_upload_existing_templates.py
**性质**：现有模板文件批量集成测试
**用途**：遍历项目 `tests/data/` 目录中的所有 `template_*.txt` 模板文件，逐一上传至 iTOL 并导出 PDF 验证。
**关键特性**：
- 自动发现模板文件
- 每个文件独立上传并记录 tree ID
- 生成 `batch_upload_log.txt` 汇总报告
- 适合验证 legacy 模板在新版本 iTOL 上的兼容性

### 03_publication_quality_figure.py
**性质**：高影响力期刊级多图层示例
**用途**：从 taxonomy 元数据表构建一个 **三层叠加** 的发表级系统发育图。
**关键特性**：
- 图层 1：Color Strip（Phylum，NATURE primary 调色板）
- 图层 2：Simple Bar（Genome Size）
- 图层 3：Heatmap（Genomic Features）
- 使用 `generate_*_template()` 函数精细控制参数
- 300 DPI PDF + PNG 双格式导出
- 可直接用于论文投稿的配图

### 04_cli_workflow.py
**性质**：纯命令行工作流示例
**用途**：展示如何在不编写 Python 代码的情况下，通过 `pyitol` CLI 完成完整工作流。
**关键特性**：
- 调用 `pyitol validate` 预检输入
- 调用 `pyitol template create` 生成 color-strip / heatmap / simple-bar
- 使用 `subprocess` 在脚本内驱动 CLI
- 适合 Snakemake / Nextflow / Bash 流水线集成

### 05_reverse_learn_template.py
**性质**：模板逆向工程示例
**用途**：将现有的 iTOL 模板文件反向解析为结构化 JSON，并从模板库中训练推荐主题。
**关键特性**：
- `learn_template()` 单文件解析（类型识别、参数提取、数据提取）
- `train_theme()` 目录级主题学习（统计最常见参数组合）
- 输出 JSON 格式的结构化配置，便于迁移至程序化工作流

---

## 快速开始

### 前置条件

1. 安装 PyiTOL（开发模式）：
   ```bash
   pip install -e .
   ```
2. 获取 iTOL API Key（https://itol.embl.de/help.cgi#batch）
3. 在项目根目录创建 `.itolapi.key` 文件，写入你的 API Key

### 运行示例

```bash
# 基础上传
python examples/api_demos/01_basic_upload.py

# 生成全部模板类型
python examples/template_demos/01_generate_all_template_types.py

# 学术级多数据集上传
python examples/api_demos/02_multi_dataset_publication.py
```

---

## 学术发表最佳实践（源自示例）

| 要素 | 推荐做法 | 对应示例 |
|---|---|---|
| **分辨率** | 导出 300 DPI 的 PDF 或 PNG | `02_multi_dataset_publication.py`、`03_publication_quality_figure.py` |
| **配色** | 使用色盲友好预设（Tol Bright / Vibrant） | `02_multi_dataset_publication.py` |
| **项目名** | 使用英文专业名称，避免中文或"临时"字样 | 全部新示例 |
| **图层组合** | 将 color strip、heatmap、bar 等互补数据集叠加 | `03_publication_quality_figure.py` |
| **矢量编辑** | 同时导出 SVG 供 Illustrator / Inkscape 微调 | `02_multi_dataset_publication.py` |
| **格式多样性** | 根据投稿要求输出 PDF（印刷）、TIFF（部分期刊）、PNG（PPT） | `04_batch_format_export.py` |

---

## 模板类型覆盖矩阵

| iTOL 模板类型 | 示例覆盖方式 |
|---|---|
| `DATASET_SIMPLEBAR` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_MULTIBAR` | `01_generate_all_template_types.py` |
| `DATASET_COLORSTRIP` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_HEATMAP` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_SYMBOLS` | `01_generate_all_template_types.py` |
| `DATASET_PIECHART` | `01_generate_all_template_types.py` |
| `DATASET_BINARY` | `01_generate_all_template_types.py` |
| `DATASET_GRADIENT` | `01_generate_all_template_types.py` |
| `DATASET_BOXPLOT` | `01_generate_all_template_types.py` |
| `DATASET_CONNECTION` | `01_generate_all_template_types.py` |
| `DATASET_DOMAINS` | `01_generate_all_template_types.py` |
| `DATASET_TEXT` | `01_generate_all_template_types.py` |
| `DATASET_EXTERNALSHAPE` | `01_generate_all_template_types.py` |
| `DATASET_LINECHART` | `01_generate_all_template_types.py` |
| `DATASET_IMAGE` | `01_generate_all_template_types.py` |
| `DATASET_ALIGNMENT` | `01_generate_all_template_types.py` |
| `DATASET_ARROWS` | `01_generate_all_template_types.py` |
| `DATASET_TANGLEGRAM` | `01_generate_all_template_types.py` |
| `DATASET_PLACEMENT` | `01_generate_all_template_types.py` |
| `DATASET_TIMESCALE` | `01_generate_all_template_types.py` |
| `DATASET_MEME` | `01_generate_all_template_types.py` |
| `DATASET_MANUAL` | `01_generate_all_template_types.py` |
| `DATASET_RANGE` | `01_generate_all_template_types.py` |
| `DATASET_STYLE` | `01_generate_all_template_types.py` |
| `TREE_COLORS` | `01_generate_all_template_types.py` |
| `LABELS` | `01_generate_all_template_types.py` |
| `POPUP_INFO` | `01_generate_all_template_types.py` |
| `COLLAPSE` | `01_generate_all_template_types.py` |
| `PRUNE` | `01_generate_all_template_types.py` |
| `SPACING` | `01_generate_all_template_types.py` |

---

## 维护说明

- 新增模板类型时，请在 `01_generate_all_template_types.py` 中添加对应的 `generate_*_template()` 调用。
- 新增 API 方法时，请在 `api_demos/` 中创建新的独立示例，避免与现有示例功能重叠。
- 所有示例的输出目录均使用相对路径 `outputs/`，不会被版本控制跟踪。
