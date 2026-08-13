# PyiTOL

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/pyitol.svg)](https://pypi.org/project/pyitol)
[![CI](https://github.com/OWNER/pyitol/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/pyitol/actions/workflows/ci.yml)

[English](README.md) | 中文

**PyiTOL** 是一个面向 **iTOL (Interactive Tree Of Life)** 平台的 Python CLI 工具，用于系统发育树可视化的全流程自动化。

## 功能特性

### 核心功能

- **30+ 种 iTOL 模板类型**：色带、热图、柱状图、饼图、符号、二元矩阵、渐变、蛋白质域、连接线等（统一入口 31 种 + `external-shape-bubble` 变体）
- **完整 API 客户端**：通过 iTOL 批量接口执行上传、导出 PDF/SVG/PNG/TIFF/EPS/Newick/Nexus/PhyloXML、删除及批量操作
- **分类学与单系群分析**：内置 dendropy 集成，支持单系/并系/复系三分类检测
- **从树名提取分类学**：支持 GTDB (`d__Bacteria;p__Proteobacteria;...`)、嵌入式 (`_d_Bacteria_p_...`)、NCBI (`Genus_species`)、auto 自动检测、underscore、mixed 混合格式
- **单系群判定→条件美化**：检查类群单系性，自动决定是否生成美化模板
- **色盲友好配色方案**：`tol_bright`、`tol_vibrant`、`wong`、`okabeito` 等
- **图例自动定位**：生成模板时自动设置图例位置，避免与树图重叠
- **会话快照与回放**：基于 YAML 的操作记录，支持工作流可重复性
- **Newick/Nexus 双格式**：自动检测树文件格式

### 分类学解析

- **格式 A（嵌入式）**：`GB_GCA_0001_d_Bacteria_p_Proteo_c_..._g_Genus`
- **格式 B（表格分号式）**：`d__Archaea;p__Thermoproteota;c__Korarchaeia;...`
- **混合模式**：自动检测并统一两种格式
- **可扩展级别**：通过 `--taxonomy-levels` 自定义分类级别前缀
- **特殊标识符**：`LUCA`（所有细菌和古菌的MRCA）、`LACA`（古菌的MRCA）、`LBCA`（细菌的MRCA）、`ROOT`（全树根，所有末端）

### 单系群条件折叠

```bash
# 通过类群名称触发折叠（先检查单系性）
pyitol template create-collapse --taxon Cyanobacteriota --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk -o collapse.txt

# 严格模式：非单系群时终止
pyitol template create-collapse --taxon Proteobacteria --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk --strict -o collapse.txt

# 默认模式：非单系群时跳过并继续
pyitol template create-collapse --taxon Proteobacteria --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk -o collapse.txt
```

### 实时日志系统

- 流式输出，无缓冲，直接写入 `sys.stdout` 并 `flush`
- ISO8601 时间戳：`2025-03-21T10:15:30.123 | INFO     | message`
- 纯文本格式，无彩色输出
- 支持 `--log-file` 同时输出到文件
- 日志级别：`DEBUG`、`INFO`、`WARNING`、`ERROR`、`CRITICAL`

### 多棵树处理

```bash
# 默认模式（ask）：检测到多棵树时提示用户（非交互环境回退到 first）
pyitol template create color-strip --tree multi.nwk ...

# 指定处理策略
pyitol template create color-strip --tree multi.nwk --multi-tree-mode first ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode last ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode random ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode split ...  # 或 all
```

支持策略：`ask`（默认，交互提示）、`first`（第一棵）、`last`（最后一棵）、`random`（随机）、`split`/`all`（处理所有树）。

### 输入文件验证

```bash
# 验证树文件、序列文件、分类表格
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta

# 深度验证：括号平衡、分支长度、重复节点名、字母表检测
pyitol validate --tree tree.nwk --alphabet DNA
```

验证内容：
- 树文件：括号平衡、负分支长度(CRITICAL)、空节点名(ERROR)、重复tip名(ERROR)、多根节点(CRITICAL)
- 序列文件：字母表检测(DNA/RNA/protein)、ID唯一性、长度一致性
- 对抗性防护：恶意字符(控制字符/双向文本)、循环依赖、空文件

### 自检模式

```bash
# 执行自检：验证依赖库、示例解析、单系群判定逻辑
pyitol self-test
```

输出 `[PASS]/[FAIL]` 表格，验证：
- 第三方依赖库可导入及版本
- 内部模块可导入
- Newick 树解析
- 嵌入式分类提取
- 单系群判定逻辑
- 恶意字符检测

## 安装

```bash
pip install pyitol
```

使用 conda（推荐生物信息学用户）：

```bash
conda create -n pyitol python=3.12
conda activate pyitol
pip install pyitol
```

从源码安装：

```bash
git clone https://github.com/OWNER/pyitol.git
cd pyitol
pip install -e ".[dev]"
```

安装可选依赖（内存监控）：

```bash
pip install pyitol[memory]
```

### 验证安装

安装完成后，运行以下命令验证：

```bash
# 查看版本信息
pyitol --version

# 运行自检（验证依赖库、示例解析、核心逻辑）
pyitol self-test
```

预期输出：
```
pyitol 1.0.0
license: MIT
...
```

```
  PyiTOL Self-Test Results
  =======================================================
  [PASS] Import typer (v0.25.1)
  [PASS] Import pandas (v2.3.3)
  [PASS] Parse sample Newick (4 tips)
  [PASS] Monophyly detection (G1=mono, G2=mono)
  ...
  All checks passed.
```

## 示例数据

项目内置示例数据，位于 `examples/data/` 目录：

| 文件 | 说明 |
|------|------|
| `synthetic_130tips.nwk` | 130 个末端的合成系统发育树 |
| `synthetic_130tips_taxonomy.csv` | 对应分类学表格（Domain → Species） |
| `synthetic_130tips_amr.csv` | 合成抗生素耐药基因数据 |
| `synthetic_130tips_auto_taxonomy.csv` | 自动提取的分类学表格 |
| `synthetic_130tips_enriched.csv` | 富集分析数据 |
| `synthetic_32tips.nwk` | 32 个末端的合成单系群测试树 |
| `synthetic_32tips_taxonomy.csv` | 对应分类学表格 |
| `synthetic_32tips_auto_taxonomy.csv` | 自动提取的分类学表格 |
| `synthetic_32tips_enriched.csv` | 富集分析数据 |
| `synthetic_4096tips.nwk` | 4096 个末端的大型合成树（压测用） |
| `synthetic_4096tips_taxonomy.csv` | 对应分类学表格 |
| `synthetic_4096tips_monophyly.csv` | 单系性检测结果 |
| `synthetic_4096tips_phylum_strip.txt` | 门级色带模板 |
| `synthetic_4096tips_traits.csv` | 性状数据 |
| `synthetic_4096tips_trait_binary.txt` | 二元性状模板 |
| `synthetic_4096tips_trait_heatmap.txt` | 热图模板 |
| `synthetic_5000tips.nwk` | 5000 个末端的大型合成树（压测用） |
| `synthetic_5000tips_taxonomy.csv` | 对应分类学表格 |
| `synthetic_5000tips_monophyly.csv` | 单系性检测结果 |
| `synthetic_5000tips_traits.csv` | 性状数据 |

使用示例数据快速体验：

```bash
# 查看树信息
pyitol tree info --tree examples/data/synthetic_130tips.nwk

# 验证输入文件
pyitol validate --tree examples/data/synthetic_130tips.nwk \
  --taxonomy examples/data/synthetic_130tips_taxonomy.csv

# 生成色带模板
pyitol template create color-strip \
  --tree examples/data/synthetic_130tips.nwk \
  --taxonomy examples/data/synthetic_130tips_taxonomy.csv \
  --column Phylum --palette tol_bright -o phylum_strip.txt

# 检查单系性
pyitol taxonomy monophyly \
  --tree examples/data/synthetic_32tips.nwk \
  --taxonomy examples/data/synthetic_32tips_taxonomy.csv \
  --rank Genus -o monophyly.csv

# 从树名提取分类学
pyitol taxonomy extract-from-names \
  --tree examples/data/synthetic_130tips.nwk \
  --format auto -o extracted_taxonomy.csv
```

## 快速开始

### 版本信息

```bash
# 显示版本号、Git哈希、依赖库版本及许可证
pyitol --version
```

输出示例：
```
pyitol 1.0.0
license: MIT
date: 2026-08-13
dependencies:
  typer: 0.25.1 (MIT)
  pandas: 2.3.3 (BSD-3-Clause)
  dendropy: 4.6.4 (BSD-3-Clause)
  numpy: 2.4.4 (BSD-3-Clause)
  ...
```

### API 密钥配置

支持三种方式（优先级从高到低）：

```bash
# 方式 1：命令行临时指定
pyitol task upload --tree tree.nwk --api-key YOUR_KEY

# 方式 2：环境变量
export ITOL_API_KEY=YOUR_KEY

# 方式 3：密钥文件
pyitol task upload --tree tree.nwk --api-key-file /path/to/key.txt
```

> **凭据安全 / Credential security**
>
> - **切勿将密钥文件提交到版本控制。** `.gitignore` 已排除 `*.key`、`itolapi.key`、`.itolapi.key`，但密钥文件仍可能通过其他渠道泄露——请勿将其放在云盘同步目录或共享目录中。
> - **密钥文件建议存放于 `~/.config/pyitol/`（权限 600）或系统钥匙串**，不要放在项目根目录。
> - 会话快照与日志会自动脱敏密钥（`***REDACTED***`），快照可安全分享。
> - 若密钥可能已暴露（被提交、同步或分享），**请立即在 iTOL 账户设置中轮换**。

### 上传并导出 PDF

```bash
# 一步完成：上传 → 渲染 → 导出 PDF 到本地
pyitol task upload-and-export \
  --tree tree.nwk \
  --config template1.txt \
  --config template2.txt \
  --api-key YOUR_KEY \
  --dataset-name "MyTree" \
  --format pdf \
  --dpi 300 \
  --output ./result.pdf \
  --wait 30
```

支持导出格式：`pdf`、`svg`、`png`、`tiff`、`eps`、`newick`、`nexus`、`phyloxml`，可指定 `--dpi`、`--width`、`--height`。

`upload-and-export` 还支持 `--parameter` 参数传递 iTOL 导出参数（如 `datasets_visible`、`display_mode`、`background` 等），与 `task export` 命令一致：

```bash
# 通过 --parameter 控制数据集可见性和渲染参数
pyitol task upload-and-export \
  --tree tree.nwk \
  --config template1.txt --config template2.txt \
  --api-key YOUR_KEY --dataset-name "MyTree" \
  --format png --dpi 300 --output ./result.png --wait 30 \
  --parameter datasets_visible=0,1 \
  --parameter display_mode=2 \
  --parameter background=ffffff
```

## 工作流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  输入文件    │     │  分类学解析  │     │  模板生成    │
│             │     │             │     │             │
│ tree.nwk    │────>│ 从树名提取  │────>│ color-strip │
│ tax.csv     │     │ 或外部表格  │     │ heatmap     │
│ seqs.fasta  │     │             │     │ bar/pie/... │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           v                   v
                    ┌─────────────┐     ┌─────────────┐
                    │  单系群判定  │     │  上传 iTOL  │
                    │             │     │             │
                    │ monophyly   │     │ upload      │
                    │ check       │     │ export PDF  │
                    └─────────────┘     └─────────────┘
```

典型工作流程：
1. **准备输入**：系统发育树 (Newick/Nexus) + 分类学表格 (CSV/TSV)
2. **解析分类学**：从树名自动提取或使用外部表格
3. **单系群检查**：验证类群是否为单系群
4. **生成模板**：根据分类信息生成 iTOL 可视化模板
5. **上传导出**：上传至 iTOL 平台并导出 PDF/SVG/PNG

## 分类学与单系群分析

### 从树末端名称自动提取分类学

```bash
# GTDB 格式：d__Bacteria;p__Proteobacteria;...;s__Escherichia_coli
pyitol taxonomy extract-from-names --tree tree.nwk --format gtdb -o taxonomy.csv

# 嵌入式格式：GB_GCA_0001_d_Bacteria_p_Proteo_c_..._g_Genus
pyitol taxonomy extract-from-names --tree tree.nwk --format embedded -o taxonomy.csv

# NCBI 格式：Genus_species
pyitol taxonomy extract-from-names --tree tree.nwk --format ncbi -o taxonomy.csv

# 自动检测格式
pyitol taxonomy extract-from-names --tree tree.nwk --format auto -o taxonomy.csv

# 自定义分类级别
pyitol taxonomy extract-from-names --tree tree.nwk \
  --taxonomy-levels "d:Domain,p:Phylum,c:Class,o:Order,f:Family,g:Genus,s:Species" \
  -o taxonomy.csv
```

### 单系群判定→条件美化

```bash
# 检查 Escherichia 是否为单系群
# 如果是 → 生成分支着色模板
# 如果不是 → 警告并退出
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxonomy tax.csv \
  --taxon Escherichia \
  --rank Genus \
  --action color-branch \
  --color "#e41a1c" \
  --output clade.txt

# 使用特殊标识符
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxonomy tax.csv \
  --taxon LUCA \
  --rank Domain \
  --action color-branch \
  --output luca.txt

# 不提供分类表 → 自动从树名提取
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxon Salmonella \
  --rank Genus \
  --action highlight \
  --output highlight.txt
```

支持的美化类型：
- `color-branch`：分支着色
- `highlight`：标签背景高亮
- `color-strip`：外圈色带

### 单系性检查

```bash
# 检查所有属的单系性
pyitol taxonomy monophyly --tree tree.nwk --taxonomy tax.csv \
  --rank Genus --output monophyly_results.csv

# 检查特殊标识符
pyitol taxonomy monophyly --tree tree.nwk --taxonomy tax.csv \
  --taxa LUCA,LACA,LBCA --output special_monophyly.csv

# 提取分类学摘要
pyitol taxonomy extract --tree tree.nwk --taxonomy tax.csv \
  --rank Genus --output taxonomy_summary.csv

# 查看可用分类等级
pyitol taxonomy ranks --taxonomy tax.csv
```

## 模板示例

```bash
# 色带 - 按分类等级着色（图例自动定位到右下角）
pyitol template create color-strip --tree tree.nwk --taxonomy tax.csv \
  --column Phylum --palette tol_bright -o strip.txt

# 热图 - 数值数据可视化
pyitol template create heatmap --tree tree.nwk --taxonomy tax.csv \
  --columns "gc_content,genome_size" --gradient "#ffffcc,#800026" -o heatmap.txt

# 柱状图 - 定量比较
pyitol template create simple-bar --tree tree.nwk --taxonomy tax.csv \
  --column genome_size --bar-color "#3c5484" -o bar.txt

# 二元矩阵 - 存在/缺失
pyitol template create binary --tree tree.nwk --taxonomy tax.csv \
  --columns "amr_genes,virulence_factors" -o binary.txt

# 连接线 - 节点间关系（JSON 格式）
pyitol template create connections --connections connections.json -o connections.txt

# 分支渐变 - 连续着色
pyitol template create branch-gradient --tree tree.nwk --taxonomy tax.csv \
  --column gc_content --gradient "#313695,#a50026" -o gradient.txt

# 蛋白质域架构
pyitol template create domains --data-file domains.json -o domain.txt

# 多列气泡外部形状（数值列可视化）
pyitol template create external-shape-bubble --tree tree.nwk --taxonomy tax.csv \
  --columns "gc_content,genome_size,gene_count" -o bubble.txt

# 一键打包多个模板
pyitol template bundle --tree tree.nwk --taxonomy tax.csv \
  --config '[{"type":"color-strip","column":"Phylum"},{"type":"heatmap","columns":"gc,genome_size"}]' \
  --output-dir ./templates/
```

### 输出文件结构

PyiTOL 生成的模板文件均为纯文本格式，可直接上传至 iTOL 平台：

| 输出类型 | 文件格式 | 内容说明 |
|---------|---------|---------|
| 模板文件 (`.txt`) | iTOL 标准格式 | 包含数据集头部定义和数据行，可直接拖入 iTOL |
| 分类表格 (`.csv`) | CSV/TSV | 包含 ID 列和分类等级列 |
| 单系性结果 (`.csv`) | CSV | 包含 group/status/lca_node/member_count 等列 |
| 会话快照 (`.yaml`) | YAML | 记录操作历史，支持 `replay` 回放 |

模板文件示例结构：
```
DATASET_COLORSTRIP
SEPARATOR TAB
DATASET_LABEL Phylum
COLOR #ff0000
...
DATA
TaxonA	#4477AA	Proteobacteria
TaxonB	#EE6677	Firmicutes
```

## 树文件操作

```bash
# 查看树的基本信息（末端数、内部节点数、是否有分支长度等）
pyitol tree info --tree examples/data/synthetic_130tips.nwk

# 格式化支持值（IQ-TREE/RAxML 等）
pyitol tree format-support-values --tree input.nwk --format iqtree -o output.nwk
```

## 实用工具

```bash
# 搜索目录中的树文件
pyitol utils search-tree-file --dir ./data/

# 解析分类学信息
pyitol utils taxonomy-parse --taxonomy tax.csv

# 数据格式转换：宽表 → 长表
pyitol utils wide-to-long --data wide.csv --id-column id -o long.csv

# 数据格式转换：长表 → 宽表
pyitol utils long-to-wide --data long.csv --id-column id -o wide.csv

# 计数数据转树
pyitol utils count-to-tree --data counts.csv -o tree.nwk

# 列分组
pyitol utils group-columns --data data.csv --group-regex '^col' -o grouped.csv

# 预览数据文件
pyitol utils preview --taxonomy tax.csv --tree tree.nwk --column Phylum

# 数据框转树
pyitol utils df-tree --data data.csv --columns col1,col2 -o tree.nwk
```

> **注意**: `utils tree-info` 已废弃，请使用 `tree info`；`utils learn-template` 已废弃，请使用 `learn template`。

## 模板反向学习

```bash
# 从已有 iTOL 模板文件学习参数
pyitol learn template --input existing_template.txt

# 学习配色方案
pyitol learn palette --input templates_dir/

# 训练主题
pyitol learn train-theme --input templates_dir/ --output theme.yaml
```

## 配置文件管理

```bash
# 初始化配置文件
pyitol config init

# 或从项目自带的模板复制
cp config.example.yaml pyitol_config.yaml

# 使用配置文件
pyitol --config pyitol.yaml template create color-strip \
  --tree tree.nwk --taxonomy tax.csv --column Phylum
```

配置文件示例 (`pyitol.yaml`)：
```yaml
tree: examples/data/synthetic_130tips.nwk
taxonomy: examples/data/synthetic_130tips_taxonomy.csv
id_column: id
separator: TAB
palette: tol_bright
```

项目根目录提供 `config.example.yaml` 模板，包含所有可配置项及注释（API 密钥、导出格式、多棵树策略、分类学解析参数等），可直接复制后修改使用。

## 色盲友好配色方案

| 配色方案 | 颜色 | 来源 |
|---------|------|------|
| `tol_bright` | #4477AA #EE6677 #228833 #CCBB44 #66CCEE #AA3377 #BBBBBB | Paul Tol |
| `tol_vibrant` | #EE7733 #0077BB #33BBEE #EE3377 #CC3311 #009988 #BBBBBB | Paul Tol |
| `wong` | #000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 | Wong (2011) |
| `okabeito` | #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #000000 | Okabe & Ito (2008) |
| `ibm` | #648FFF #785EF0 #DC267F #FE6100 #FFB000 | IBM Design |

使用方式：`--palette wong`

## 会话快照与可重复性

```bash
# 工作流完成后，会话快照自动保存
pyitol task upload --tree tree.nwk --config template.txt
# 快照保存至 ~/.pyitol/session_logs/

# 回放之前的会话
pyitol replay --session session.yaml

# 仅显示建议命令，不实际执行
pyitol replay --session session.yaml --dry-run
```

## 大规模数据处理

```bash
# 低内存模式（适用于大型数据集）
pyitol --low-memory template create color-strip --tree large_tree.nwk ...

# 详细日志（显示内存使用等调试信息）
pyitol --verbose template create color-strip --tree large_tree.nwk ...

# 日志输出到文件
pyitol --log-file pyitol.log template create color-strip --tree tree.nwk ...
```

- 超过 10,000 末端的大型树会在 INFO 日志中提示资源需求
- 使用 `--verbose` 可在 DEBUG 级别查看内存使用（需安装 `psutil`）

## 输出文件管理

```bash
# 默认行为：输出文件已存在时报错（所有子命令均受保护）
pyitol template create color-strip --tree tree.nwk -o output.txt

# 强制覆盖（仅统一入口 template create 支持）
pyitol template create color-strip --tree tree.nwk -o output.txt --force

# 跳过已存在的文件（仅统一入口 template create 支持）
pyitol template create color-strip --tree tree.nwk -o output.txt --no-clobber
```

> 所有独立子命令（如 `create-color-strip`、`create-heatmap` 等）也会检查输出文件是否已存在，防止意外覆盖。如需覆盖，请使用统一入口 `template create` 的 `--force` 选项。

## 优雅中断

按 `Ctrl+C` 可优雅终止程序：
- 输出当前处理进度
- 关闭所有打开的文件句柄
- 删除未完成的临时文件
- 退出码 130

## 错误码

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 操作正常完成 |
| 1 | 运行错误 | 内部错误、依赖问题、API失败 |
| 2 | 参数错误 | 无效的CLI参数、验证失败 |
| 3 | 数据错误 | 输入文件格式/内容错误 |
| 130 | 用户中断 | 收到 SIGINT (Ctrl+C) |

详见 [错误码文档](docs/error_codes.md)。

## CLI 命令一览

```
pyitol
├── --version             显示版本号、Git哈希和依赖库版本
├── --verbose             显示详细日志
├── --quiet               仅显示关键信息
├── --log-file            日志文件路径
├── --low-memory          低内存模式
├── self-test             执行自检
├── validate              验证输入文件
├── config                配置文件管理
├── template              创建和管理 iTOL 模板文件
│   ├── create-*          31 种模板创建子命令
│   ├── create-collapse   折叠分支（支持 --taxon 单系群检查）
│   ├── bundle            一键打包多个模板
│   └── validate          验证模板格式
├── taxonomy              分类分析与单系性检测
│   ├── ranks             查看分类等级
│   ├── extract           提取分类信息
│   ├── extract-stats     提取分类统计
│   ├── extract-from-names  从树名自动提取分类学
│   ├── monophyly         单系性检查（支持 LUCA/LACA/LBCA/ROOT）
│   ├── check-and-style   单系群判定→条件美化
│   ├── style             分类样式模板
│   ├── convert-binary    转换为二元矩阵
│   └── convert-connect   转换为连接对
├── task                  iTOL API 任务管理
│   ├── upload            上传到 iTOL
│   ├── export            从 iTOL 导出
│   ├── upload-and-export 上传+导出一步完成
│   ├── delete            删除 iTOL 树
│   ├── status            查询树状态
│   └── run               批量任务执行
├── tree                  树文件操作
├── utils                 实用工具
├── learn                 从已有模板反向学习
└── replay                回放操作记录
```

## 项目结构

```
PyiTOL/
├── src/pyitol/                 源代码
│   ├── api/                    iTOL API 客户端
│   ├── cli/                    CLI 命令定义
│   ├── core/                   核心算法（解析器、单系群检测、分类学）
│   ├── templates/              模板生成器和 schema 定义
│   └── utils/                  工具函数（颜色、I/O、会话、日志、shutdown）
├── tests/                      测试套件（1702 个测试）
│   ├── data/                   测试数据文件
│   ├── core/                   核心算法测试
│   ├── cli/                    CLI 命令测试
│   ├── templates/              模板系统测试
│   ├── utils/                  工具函数测试
│   └── api/                    API 客户端测试
├── examples/
│   └── data/                   演示数据文件
├── docs/                       文档
│   └── error_codes.md          错误码参考
├── benchmarks/                 性能基准
└── pyproject.toml              项目配置
```

## 文档

- [快速开始指南](docs/tutorials/quickstart.md)
- [模板类型概览](docs/tutorials/templates.md)
- [分类学分析教程](docs/tutorials/taxonomy.md)
- [CLI 参考手册](docs/cli.md)
- [API 指南](docs/api.md)
- [错误码参考](docs/error_codes.md)
- [贡献指南](CONTRIBUTING.md)

## 依赖库许可证

| 库 | 版本 | 许可证 |
|----|------|--------|
| typer | >=0.15.0 | MIT |
| rich | ~=13.0 | MIT |
| pandas | ~=2.0 | BSD-3-Clause |
| dendropy | ~=4.6 | BSD-3-Clause |
| numpy | >=1.24 | BSD-3-Clause |
| requests | ~=2.32 | Apache-2.0 |
| PyYAML | ~=6.0 | MIT |
| pydantic | ~=2.5 | MIT |

## 引用

如果您在研究中使用了 PyiTOL，请引用：

- **iTOL**: Letunic, I., & Bork, P. (2021). Interactive Tree Of Life (iTOL) v5. *Nucleic Acids Research*, 49(W1), W293-W296. doi:10.1093/nar/gkab301
- **DendroPy**: Sukumaran, J., & Holder, M. T. (2010). DendroPy. *Bioinformatics*, 26(12), 1569-1571. doi:10.1093/bioinformatics/btq228
- **DendroPy 5**: Moreno, M. A., Holder, M. T., & Sukumaran, J. (2024). DendroPy 5: a mature Python library for phylogenetic computing. *Journal of Open Source Software*, 9(101), 6943. doi:10.21105/joss.06943
- **itol.toolkit**: Zhou, T., Xu, K., Zhao, F., Liu, W., Li, L., Hua, Z., & Zhou, X. (2023). itol.toolkit accelerates working with iTOL by an automated generation of annotation files. *Bioinformatics*, 39(6), btad339. doi:10.1093/bioinformatics/btad339

如果您使用了基准测试对比功能（ete3/ete4，可选依赖）：

- **ETE 3**: Huerta-Cepas, J., Serra, F., & Bork, P. (2016). ETE 3: Reconstruction, analysis, and visualization of phylogenomic data. *Molecular Biology and Evolution*, 33(6), 1635-1638. doi:10.1093/molbev/msw046

参见 [CITATION.cff](CITATION.cff) 获取机器可读的引用元数据。

## 联系与支持

- **GitHub Issues**: [报告问题或建议](https://github.com/OWNER/pyitol/issues)
- **GitHub Discussions**: [社区讨论](https://github.com/OWNER/pyitol/discussions)
- **邮箱**: zengzichao@sjtu.edu.cn
- **维护者**: Zichao Zeng

欢迎通过以上渠道提交问题、建议或贡献代码。

## 许可证

本项目基于 [MIT 许可证](LICENSE) 开源。第三方版权与许可证信息请参见 [NOTICE](NOTICE)。
