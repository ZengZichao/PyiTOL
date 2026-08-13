# PyiTOL CLI 完整参考

## 全局参数

所有子命令共享以下全局参数：

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--version` | | | 显示版本号、Git哈希、依赖库版本及许可证 |
| `--verbose` | | `False` | 显示详细日志（DEBUG级别） |
| `--quiet` | `-q` | `False` | 仅显示关键信息（WARNING级别） |
| `--config` | `-c` | | YAML/JSON 配置文件路径 |
| `--log-file` | | | 日志文件路径（同时输出到文件） |
| `--low-memory` | | `False` | 低内存模式（适用于大型数据集） |

## 命令总览

```
pyitol [全局参数] <主命令> <子命令> [参数]
```

---

## self-test - 自检模式

### `pyitol self-test`

执行自检：验证依赖库、示例解析、单系群判定逻辑。

```bash
pyitol self-test
```

输出 `[PASS]/[FAIL]` 表格，验证：
- 第三方依赖库可导入及版本
- 内部模块可导入
- Newick 树解析
- 嵌入式分类提取
- 单系群判定逻辑
- 恶意字符检测

退出码：0=全部通过，1=有失败

---

## validate - 输入验证

### `pyitol validate`

验证输入文件格式、颜色代码和节点ID一致性。支持深度验证和对抗性防护。

```bash
# 基本验证
pyitol validate --tree tree.nwk --taxonomy taxonomy.csv

# 深度验证（含序列文件）
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta --alphabet DNA
```

| 参数 | 简写 | 说明 |
|------|------|------|
| `--tree` | `-t` | 树文件路径 |
| `--taxonomy` | | 分类表格文件路径 |
| `--sequence` | `-s` | 序列文件路径 |
| `--alphabet` | | 预期字母表: `auto`/`DNA`/`RNA`/`protein`/`any` |
| `--template` | | 模板文件路径（可多次指定） |
| `--color` | | 颜色代码（可多次指定） |

**深度验证内容**：
- 树文件：括号平衡、负分支长度(CRITICAL)、空节点名(ERROR)、重复tip名(ERROR)、多根节点(CRITICAL)
- 序列文件：字母表检测(DNA/RNA/protein)、ID唯一性、长度一致性
- 对抗性防护：恶意字符(控制字符/双向文本)、循环依赖、空文件

---

## config - 配置文件管理

### `pyitol config init`

生成默认配置文件模板。

```bash
pyitol config init --output pyitol_config.yaml
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--output` / `-o` | `pyitol_config.yaml` | 输出配置文件路径 |
| `--api-key-file` | `.itolapi.key` | API密钥文件路径 |
| `--default-format` | `svg` | 默认导出格式 |

---

## template - 模板管理

### `pyitol template create <类型>` ⭐ 统一入口

根据类型创建 iTOL v7 模板文件。这是模板生成的**推荐统一入口**。

```bash
# 示例：生成分类色带
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt

# 示例：生成热图
pyitol template create heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Sample1,Sample2,Sample3 --output heatmap.txt

# 示例：单系群条件折叠
pyitol template create collapse \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon Cyanobacteriota --rank Phylum \
  --strict -o collapse.txt
```

**支持的模板类型**：

| 类型 | 说明 | 必需参数 |
|------|------|---------|
| `color-strip` | 颜色条带 | `--taxonomy`, `--tree`, `--column` |
| `branch` | 分支着色 | `--taxonomy`, `--tree`, `--column` |
| `simple-bar` | 单值柱状图 | `--taxonomy`, `--tree`, `--column` |
| `multi-bar` | 多值柱状图 | `--taxonomy`, `--tree`, `--columns` |
| `heatmap` | 热图 | `--taxonomy`, `--tree`, `--columns` |
| `symbols` | 符号标记 | `--taxonomy`, `--tree`, `--column` |
| `pie` | 饼图 | `--taxonomy`, `--tree`, `--columns` |
| `boxplot` | 箱线图 | `--taxonomy`, `--tree` |
| `gradient` | 颜色渐变 | `--taxonomy`, `--tree`, `--column` |
| `connections` | 连接线 | `--connections` |
| `labels` | 标签重命名 | `--taxonomy`, `--tree`, `--column` |
| `popup-info` | 悬停信息 | `--taxonomy`, `--tree` |
| `domains` | 蛋白结构域 | `--data-file` |
| `binary` | 二元数据 | `--taxonomy`, `--tree`, `--columns` |
| `text` | 文本标签 | `--taxonomy`, `--tree`, `--column` |
| `external-shape` | 外部形状 | `--taxonomy`, `--tree`, `--column` |
| `tree-colors` | 树着色 | `--taxonomy`, `--tree`, `--column` |
| `branch-gradient` | 分支渐变 | `--taxonomy`, `--tree`, `--column` |
| `collapse` | 折叠分支 | `--node-ids` 或 `--taxon` |
| `prune` | 修剪分支 | `--node-ids` |
| `spacing` | 节点间距 | `--data-file` |
| `ranges` | 彩色范围 | `--taxonomy`, `--tree`, `--column` |
| `highlight` | 标签高亮 | `--taxonomy`, `--tree`, `--column` |
| `style` | 分支/标签样式 | `--taxonomy`, `--tree`, `--column` |
| `arrow` | 箭头注释 | `--data-file` |
| `linechart` | 折线图 | `--taxonomy`, `--tree`, `--column` |
| `image` | 图像嵌入 | `--taxonomy`, `--tree` |
| `alignment` | 序列比对 | `--taxonomy`, `--tree` |
| `tanglegram` | 纠缠图 | `--connections` |
| `placement` | 系统发育放置 | `--data-file` |
| `timescale` | 时间尺度 | `--data-file` |
| `meme` | MEME基序 | `--data-file` |
| `manual` | 手动注释 | `--data-file` |

> **注意**：统一入口 `template create` 支持 31 种类型。另有 `external-shape-bubble`（气泡外部形状，`external-shape` 的变体）需通过专用子命令 `pyitol template create-external-shape-bubble` 创建，不在统一入口支持范围内。此外还有 31 个专用 `create-*` 子命令可用（`pyitol template create-color-strip` 等），与统一入口功能等价。

**公共参数**：

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--output` / `-o` | | `config_template.txt` | 输出模板文件路径 |
| `--taxonomy` / `-t` | | | 分类信息表格文件路径 |
| `--tree` / `-r` | | | 树文件路径 |
| `--column` / `-c` | | | 数据列名 |
| `--columns` | | | 多个数据列名,逗号分隔 |
| `--colors` | | | 自定义颜色映射JSON |
| `--label` / `-l` | | `dataset` | 数据集标签 |
| `--id-column` | | `id` | ID列名 |
| `--separator` / `-s` | | `TAB` | 数据分隔符 |
| `--palette` | | | 配色预设 |
| `--data-file` / `-d` | | | 数据文件路径 |
| `--force` / `-f` | | `False` | 覆盖已存在的输出文件 |
| `--no-clobber` | | `False` | 跳过已存在的输出文件 |

**collapse 特有参数**：

| 参数 | 说明 |
|------|------|
| `--node-ids` / `-n` | 要折叠的节点ID,逗号分隔 |
| `--taxon` | 要折叠的类群名称（需配合 `--taxonomy` 和 `--tree`） |
| `--rank` | 分类等级（如 Phylum, Class） |
| `--strict` | 严格模式: 非单系群时终止（默认跳过） |

### `pyitol template bundle`

一键打包生成多个可视化模板文件。

```bash
pyitol template bundle \
  --output-dir ./templates \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --config '[{"type":"color-strip","column":"Phylum"},{"type":"heatmap","columns":["A","B","C"]}]'
```

### `pyitol template validate`

验证 iTOL 模板文件格式。

```bash
pyitol template validate --template colors.txt
```

此外，PyiTOL 还提供 34 个专用子命令 `pyitol template create-*`（如 `create-color-strip`、`create-symbols`、`create-pie`），各自只接受其类型专属参数，更适合在脚本/流水线中精确调用。其完整选项与示例见 [模板生成专用子命令参考](templates-reference.md)。

---

## taxonomy - 分类分析

### `pyitol taxonomy ranks`

显示分类等级列表。

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

### `pyitol taxonomy extract`

提取指定分类等级的信息。

```bash
pyitol taxonomy extract --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output extract.txt
```

### `pyitol taxonomy extract-stats`

提取分类统计信息（成员数、LCA节点等）。

```bash
pyitol taxonomy extract-stats --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output stats.csv
```

### `pyitol taxonomy extract-from-names`

从树末端名称自动提取分类学信息。

```bash
# GTDB 格式
pyitol taxonomy extract-from-names --tree tree.nwk --format gtdb -o taxonomy.csv

# 嵌入式格式
pyitol taxonomy extract-from-names --tree tree.nwk --format embedded -o taxonomy.csv

# 自动检测
pyitol taxonomy extract-from-names --tree tree.nwk --format auto -o taxonomy.csv

# 自定义分类级别
pyitol taxonomy extract-from-names --tree tree.nwk \
  --taxonomy-levels "d:Domain,p:Phylum,c:Class,o:Order,f:Family,g:Genus,s:Species" \
  -o taxonomy.csv
```

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--tree` / `-r` | | 树文件路径 |
| `--output` / `-o` | `taxonomy_from_names.csv` | 输出分类表格路径 |
| `--format` / `-f` | `auto` | 命名格式: `auto`/`gtdb`/`embedded`/`ncbi` |
| `--delimiter` / `-d` | `_` | 名称分隔符 |
| `--taxonomy-levels` | | 自定义分类级别前缀 |
| `--taxonomy-delimiter-mode` | 嵌入式格式解析策略 | `segment` (默认) / `reverse` / `greedy` |

**支持的格式**：
- **GTDB (Format B)**: `d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;...`
- **Embedded (Format A)**: `GB_GCA_0001_d_Bacteria_p_Proteo_c_Gamma_o_Enter_f_Enter_g_Escherichia`
- **NCBI**: `Genus_species`

### `pyitol taxonomy monophyly`

检查指定分类群的单系性（单系/并系/复系）。

```bash
# 按分类等级检测
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output mono.csv

# 按指定类群检测
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "Proteobacteria,Firmicutes" --output mono.csv

# 使用特殊标识符
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "LUCA,LACA,LBCA,ROOT" --output mono.csv
```

| 参数 | 说明 |
|------|------|
| `--taxonomy` / `-t` | 分类表格文件路径 |
| `--tree` / `-r` | 树文件路径 |
| `--rank` | 分类等级名称 |
| `--taxa` | 指定分类群名称,逗号分隔（支持 LUCA/LACA/LBCA/ROOT） |
| `--taxa-file` | 包含分类群名称的文件(每行一个) |
| `--output` / `-o` | 输出文件路径 |
| `--id-column` | ID列名 |
| `--multi-tree-mode` / `-m` | 多棵树处理策略: `ask`/`first`/`last`/`random`/`split` |

**特殊标识符**：
- `LUCA`：所有细菌和古菌的 MRCA
- `LACA`：所有古菌的 MRCA
- `LBCA`：所有细菌的 MRCA
- `ROOT`：全树根（所有末端节点）

### `pyitol taxonomy check-and-style`

检查指定类群是否为单系群，如果是则生成美化模板，否则警告。

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon Escherichia --rank Genus \
  --action color-branch --color "#e41a1c" \
  --output clade.txt

# 使用特殊标识符
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon LUCA --rank Domain \
  --action color-branch --output luca.txt
```

| 参数 | 说明 |
|------|------|
| `--tree` / `-r` | 树文件路径 |
| `--taxonomy` / `-t` | 分类表格文件路径(可选) |
| `--taxon` | 要检查的类群名称(支持 LUCA/LACA/LBCA/ROOT) |
| `--rank` | 分类等级(默认 Genus) |
| `--action` / `-a` | 美化类型: `color-branch`/`highlight`/`color-strip` |
| `--color` | 指定颜色(HEX) |
| `--output` / `-o` | 输出模板文件路径 |
| `--name-format` | 命名格式: `auto`/`gtdb`/`embedded`/`ncbi` |
| `--palette` | 配色预设 |
| `--domain-column` | Domain列名(用于LUCA/LACA/LBCA解析) |
| `--multi-tree-mode` / `-m` | 多棵树处理策略 |
| `--taxonomy-source-priority` | 混合来源优先级 | `table` (默认) / `embedded` |

### `pyitol taxonomy style`

根据分类信息和指定美化类型生成 iTOL 模板配置文件。

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output style.txt
```

**支持的美化动作** (`--action`)：
- `color-branch` / `color-label` / `color-range` / `color-strip`
- `style-branch` / `style-label`
- `width` / `highlight` / `symbol` / `range` / `gradient`

### `pyitol taxonomy convert-binary`

将分类数据转换为 0/1 二元矩阵。

```bash
pyitol taxonomy convert-binary --input data.csv --columns col1,col2 --output binary.csv
```

### `pyitol taxonomy convert-connect`

将 0/1 矩阵转换为连接对长格式表格。

```bash
pyitol taxonomy convert-connect --input binary.csv --output connections.csv
```

---

## task - API 任务管理

### `pyitol task upload`

上传树和模板到 iTOL。

```bash
pyitol task upload --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --api-key YOUR_KEY --dataset-name MyTree
```

### `pyitol task export`

导出 iTOL 可视化图片。

```bash
pyitol task export --upload-id TREE_ID --download ./output --format svg
```

### `pyitol task upload-and-export`

上传并导出图片（一步完成）。

```bash
pyitol task upload-and-export \
  --tree tree.nwk --config colors.txt \
  --output output.svg --format svg --wait 60
```

支持 `--parameter` 参数传递 iTOL 导出参数（如 `datasets_visible`、`display_mode`、`background` 等），与 `task export` 一致：

```bash
pyitol task upload-and-export \
  --tree tree.nwk --config colors.txt \
  --output output.png --format png --dpi 300 --wait 60 \
  --parameter datasets_visible=0,1 \
  --parameter display_mode=2 \
  --parameter background=ffffff
```

`--parameter` 常用值：`datasets_visible`（数据集可见性）、`display_mode`（0=矩形/1=圆形/2=无根圆形/3=无根矩形）、`background`（背景色）、`ignore_branch_length`、`line_width`、`current_font_size`、`margin`、`arc`。

### `pyitol task delete`

删除已上传的树。

```bash
pyitol task delete --upload-id ID1 --upload-id ID2 --api-key YOUR_KEY
```

### `pyitol task status`

查询已上传树的状态。

```bash
pyitol task status --upload-id TREE_ID --api-key YOUR_KEY
```

### `pyitol task run`

运行配置文件（单配置或批量列表）。

```bash
pyitol task run --config workflow.yaml
pyitol task run --config-list batch.yaml
```

---

## tree - 树文件操作

### `pyitol tree info`

显示树文件基本信息。

```bash
pyitol tree info --tree tree.nwk
```

### `pyitol tree format-support-values`

格式化支持值显示（支持 IQ-TREE, RAxML, ALRT 等格式）。

```bash
pyitol tree format-support-values --tree tree.nwk --output formatted.nwk
```

---

## utils - 实用工具

### `pyitol utils tree-info`

显示树文件基本信息。

```bash
pyitol utils tree-info --tree tree.nwk
```

### `pyitol utils search-tree-file`

在目录中自动搜索系统发育树文件。

```bash
pyitol utils search-tree-file --dir ./data/
```

### `pyitol utils taxonomy-parse`

解析并预览分类表格的结构和内容。

```bash
pyitol utils taxonomy-parse --taxonomy tax.csv
```

### `pyitol utils learn-template`

从已有 iTOL 模板文件反向学习配置。

```bash
pyitol utils learn-template --template colors.txt --output learned.json
```

### `pyitol utils wide-to-long` / `long-to-wide`

格式转换。

```bash
pyitol utils wide-to-long --data wide.csv --id-column id -o long.csv
pyitol utils long-to-wide --data long.csv --id-column id -o wide.csv
```

### `pyitol utils count-to-tree`

基于计数值距离构建系统发育树。

```bash
pyitol utils count-to-tree --data counts.csv --output tree.nwk --method upgma
```

### `pyitol utils df-tree` ⭐

从数据框直接构建 Newick 格式的系统发育树。

```bash
pyitol utils df-tree --data data.csv --columns A,B,C --output tree.nwk --main col
```

### `pyitol utils group-columns`

按指定列聚合数据。支持正则匹配列名分组和多属性映射分组。

```bash
pyitol utils group-columns --data data.csv --columns "col1,col2,col3" -o grouped.csv
```

### `pyitol utils binary`

分类数据转换为二元矩阵。

```bash
pyitol utils binary --taxonomy data.csv --columns col1,col2 -o binary.csv
```

### `pyitol utils connections`

生成连接对（基于共现权重）。

```bash
pyitol utils connections --taxonomy binary.csv --columns col1,col2 -o connections.csv
```

### `pyitol utils preview`

预览分类表格中特定列的数据分布。

```bash
pyitol utils preview --taxonomy tax.csv --tree tree.nwk --column Phylum
```

---

## learn - 模板反向学习

### `pyitol learn template`

从模板文件反向学习配置。

```bash
pyitol learn template --template t1.txt --template t2.txt --output learned.json
```

### `pyitol learn palette`

查看可用的配色预设。

```bash
pyitol learn palette --preset-name nature
```

### `pyitol learn train-theme` ⭐

批量学习模板目录中的主题，生成推荐默认参数。

```bash
pyitol learn train-theme --dir ./templates --output theme.json --min-freq 0.5
```

---

## replay - 操作回放

### `pyitol replay`

回放之前的操作记录。

```bash
pyitol replay --session ~/.pyitol/session_logs/pyitol_20240115_120000.yaml
```

---

## 配置文件格式

PyiTOL 支持通过 `--config` 传入 YAML/JSON 配置文件作为全局参数覆盖，参数优先级：**命令行 > 配置文件 > 默认值**。

`--config` 用于覆盖 CLI 默认参数（如 `tree`、`taxonomy`、`api_key` 等）。

`pyitol task run` 则使用独立的任务配置文件格式，每项通过 `command` 字段指定操作，支持 `upload`/`export`/`extract`/`monophyly`/`convert-binary` 等。详见 [API 使用指南](api.md#批量操作)。

任务配置文件示例 `batch.yaml`（列表格式）：

```yaml
- command: upload
  tree: tree.nwk
  configs: [colors.txt, bars.txt]
  api_key: YOUR_API_KEY
  name: MyTree
- command: export
  upload_id: TREE_ID
  download: ./output
  parameters:
    format: svg
    dpi: 300
```

---

## 退出码

| 退出码 | 含义 | 说明 |
|--------|------|------|
| 0 | 成功 | 操作正常完成 |
| 1 | 运行错误 | 内部错误、依赖问题、API失败 |
| 2 | 参数错误 | 无效的CLI参数、验证失败 |
| 3 | 数据错误 | 输入文件格式/内容错误 |
| 130 | 用户中断 | 收到 SIGINT (Ctrl+C) |
