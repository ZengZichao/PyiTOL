# 分类分析教程

[English](taxonomy_en.md) | 中文

PyiTOL 提供完整的分类分析工具链：等级识别、信息提取、单系性检测和自动化美化。

## 1. 分类等级识别

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

`taxonomy ranks` 原样列出分类表格中除 ID 列（`--id-column`，默认 `id`）之外的所有列名：标准分类等级（domain、phylum、class、order、family、genus、species 等）与自定义列一视同仁，既不做识别判断，也不重新排序。

## 2. 分类信息提取

### 基础提取

```bash
pyitol taxonomy extract \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_tips.txt
```

输出格式：每行一个末端（叶），包含 ID 和分类名。

### 统计提取（含 LCA 和成员数）

```bash
pyitol taxonomy extract-stats \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_stats.csv
```

输出列：rank, group, member_count, lca_node, members

### 从树末端名称提取

无需预先准备分类表格，直接从树末端（叶）名称自动提取分类学信息：

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format auto \
  --output taxonomy_from_names.csv
```

`--format` 的帮助文本只列出 4 种取值（`auto`/`gtdb`/`embedded`/`ncbi`），实现另支持 `underscore` 与 `mixed`，共六种命名格式：

| 格式 | 说明 | 示例 |
|------|------|------|
| `auto` | 自动检测（默认） | — |
| `gtdb` | GTDB 格式（`X__` 前缀，分号分隔） | `d__Bacteria;p__Proteobacteria;...;s__Species` |
| `embedded` | 嵌入式格式（`_X_` 标记） | `accession_d_Bacteria_p_Proteo_c_..._g_Genus` |
| `ncbi` | NCBI 格式（属种下划线分隔） | `Escherichia_coli` |
| `underscore` | 下划线分隔多等级 | `Family_Genus_species` |
| `mixed` | 混合格式（GTDB + 嵌入式） | 混合上述两种 |

可通过 `--taxonomy-levels` 自定义分类级别前缀映射（如 `d:Domain,p:Phylum,...`），通过 `--delimiter` 指定名称分隔符（默认下划线）。

通过 `--taxonomy-delimiter-mode` 控制嵌入式格式（`embedded`）下分类标记的解析方式，用于解决分类名本身含下划线时的解析歧义：

| 模式 | 说明 |
|------|------|
| `segment` | 正向匹配（默认），按标记逐段解析 |
| `reverse` | 严格逆序，从右向左验证 g→f→o→c→p→d；不匹配时发出 WARNING 并回退到 `greedy` |
| `greedy` | 从首个 `d_` 标记开始截取整段作为分类信息 |

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format embedded \
  --taxonomy-delimiter-mode reverse \
  --output taxonomy_from_names.csv
```

## 3. 单系性检测

### 按分类等级批量检测

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv
```

### 按指定类群检测

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "Proteobacteria,Firmicutes,Actinobacteria" \
  --output monophyly.csv
```

### 从文件读取类群列表

```bash
echo -e "Proteobacteria\nFirmicutes" > taxa_list.txt
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa-file taxa_list.txt --output monophyly.csv
```

### 多歧节点处理

通过 `--polytomy-mode` 控制当 LCA 为多歧节点（multifurcation）时的判定行为：

| 模式 | 说明 |
|------|------|
| `strict` | 严格模式（默认），按标准二叉树分类规则判定；但当 LCA 为多歧节点、成员仅占据部分子分支且存在混入节点时，同样判为 `data_insufficient` |
| `relaxed` | 宽松模式，若成员仅占据多歧节点的部分子分支，判为并系而非复系 |
| `data-insufficient` | 数据不足模式，上述情况判为 `data_insufficient`，表示拓扑未解析、无法定论 |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --polytomy-mode relaxed \
  --output monophyly.csv
```

### 多棵树处理

`--multi-tree-mode`（帮助文本列出 `ask`/`first`/`last`/`split`，默认 `ask`）在 `taxonomy monophyly` 与 `taxonomy check-and-style` 上只是被接收：`monophyly` 会解析该取值（并允许被配置文件覆盖），`check-and-style` 甚至不读取它；两者都不会把它传给单系性检测的读树代码（源码注释标注该参数 reserved for future use）。这两个命令直接用 `dendropy.Tree.get_from_path` 载入树，因此既不提示选择、也不拆分输出，任何取值当前都没有效果。

各策略本身的语义如下（由 `pyitol/core/parser.py::load_tree` 实现）：

| 策略 | 说明 |
|------|------|
| `ask` | 默认，提示用户选择（非交互环境自动回退到 `first`） |
| `first` | 仅使用第一棵树 |
| `last` | 仅使用最后一棵树 |
| `split` | 返回全部树的列表，由调用方逐棵处理 |
| `all` | 代码内部别名，与 `split` 等价：返回全部树并分别处理（帮助文本未列出） |

只有经 `pyitol/core/parser.py::load_tree` 加载树的代码路径才会真正执行上述策略；这些路径目前由内部以固定值调用（`validate` 内部使用 `first` 与 `all`），命令行尚未把本选项的取值传进去。因此下面的命令无论是否加上 `--multi-tree-mode`，行为都完全相同：

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree trees.nexus \
  --rank Phylum \
  --output monophyly.csv
```

## 4. 单系性判定原理

PyiTOL 对每组末端（叶）执行以下算法：

1. **找 LCA**：计算类群所有成员的最近共同祖先
2. **算差集**：
   - `E = LCA后代 \ 类群成员`（混入节点）
   - `M = 类群成员 \ LCA后代`（缺失节点）
3. **判定**：
   - `E=∅` 且 `M=∅` → **单系群 (monophyletic)**
   - `M≠∅`（部分成员不在树中） → **取样不全 (incomplete_sampling)**
   - `M=∅` 且 `E≠∅` → 依拓扑判为 **并系群 (paraphyletic)** 或 **复系群 (polyphyletic)**；若混入节点全部映射到同一类群则仍判单系，若全部无法映射则判 `data_insufficient`
   - LCA 为多歧节点、成员仅占据部分子分支且 `E≠∅` → 默认 `strict` 与 `data-insufficient` 模式判为 **数据不足 (data_insufficient)**，`relaxed` 模式判为并系群

`data_insufficient` 有两种来源：一是上述多歧节点情形（默认 `strict` 与 `data-insufficient` 模式都会返回它，只有 `relaxed` 不会）；二是非多歧情形下混入节点全部不在分类映射中、无法判断其归属。此时输出 `data_insufficient` 以提示用户补齐分类表，或在多歧节点情形下改用 `relaxed` 模式。

复系群会进一步分解为亚组，输出每个亚组的 LCA 和成员。

## 5. 美化配置生成

根据单系性检测结果，自动生成 iTOL 模板：

### 为不同门类生成色带

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output phylum_colors.txt
```

### 为特定类群着色分支

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxon "Proteobacteria" --action color-branch \
  --color "#e64b35" --output highlight.txt
```

### 为属级类群添加符号标记

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Genus --action symbol --output genus_symbols.txt
```

### 支持的美化动作

| 动作 | 生成模板 | 效果 |
|------|---------|------|
| `color-branch` | TREE_COLORS (clade) | 分支着色 |
| `color-label` | TREE_COLORS (label) | 标签着色 |
| `color-range` | TREE_COLORS (range) | 范围着色 |
| `color-strip` | DATASET_COLORSTRIP | 色带 |
| `style-branch` | DATASET_STYLE | 分支线型 |
| `style-label` | DATASET_STYLE | 标签样式 |
| `width` | DATASET_STYLE | 分支宽度 |
| `highlight` | DATASET_STYLE | 标签背景高亮 |
| `symbol` | DATASET_SYMBOL | 符号标记 |
| `range` | DATASET_RANGE | 彩色范围 |
| `gradient` | DATASET_GRADIENT | 渐变色带 |

### 检查并美化（一步到位）

`check-and-style` 命令将单系性检查与美化模板生成合并为一步：先检查指定类群是否为单系群，若是则生成美化模板；否则输出警告或错误并以状态码 1 退出，不写出任何模板文件。

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "Escherichia" --rank Genus \
  --action color-branch --output escherichia.txt
```

支持的美化类型（`--action`）：

| 动作 | 效果 |
|------|------|
| `color-branch` | 分支着色（默认） |
| `highlight` | 标签背景高亮 |
| `color-strip` | 色带 |

通过 `--taxonomy-source-priority` 控制同时提供外部分类表格和树名嵌入分类信息时的合并优先级：

| 取值 | 说明 |
|------|------|
| `table` | 表格优先（默认），以 `--taxonomy` 指定的分类表格为准 |
| `embedded` | 树名嵌入信息优先；树名提取的分类信息会填充表格中的缺失字段，冲突时以树名为准并输出 WARNING 日志 |

不提供 `--taxonomy` 时，可自动从树末端名称提取分类信息（需配合 `--name-format` 指定格式）。

#### 特殊标识符

`--taxon` 支持四个特殊标识符，用于定位生命树根部的关键祖先节点。使用任一标识符都必须提供 `--taxonomy`；`--domain-column` 是可选的，默认取列名 `Domain`（表格中列名大小写不一致时会自动匹配），但 `LUCA`/`LACA`/`LBCA` 要求分类表格确实含有域列，否则抛出 `MetadataParseError`：

| 标识符 | 含义 |
|--------|------|
| `LUCA` | 所有古菌和细菌的最近共同祖先 |
| `LACA` | 所有古菌的最近共同祖先 |
| `LBCA` | 所有细菌的最近共同祖先 |
| `ROOT` | 全树根，返回分类表格中与树末端（叶）标签相交的那部分 ID，不使用域列 |

`taxonomy monophyly` 的 `--taxa`/`--taxa-file` 接受同一组标识符（`LUCA`/`LACA`/`LBCA`/`ROOT`，其帮助文本只列出前三个），但该命令没有 `--domain-column` 选项，域列名固定按 `Domain` 查找。

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "LBCA" --action highlight \
  --domain-column Domain --output lbca.txt
```

## 6. 二元数据转换

将 `--columns` 指定各列的存在/缺失数据（如基因有无）转换为 0/1 矩阵：

```bash
pyitol taxonomy convert-binary \
  --input data.csv --columns "GeneA,GeneB,GeneC" \
  --output binary_matrix.csv
```

## 7. 连接对转换

将 0/1 矩阵转换为连接对（用于 Connections 模板）：

```bash
pyitol taxonomy convert-connect \
  --input binary_matrix.csv --output connections.csv \
  --min-weight 0.5
```

## 8. 完整工作流示例

```bash
# 1. 检测单系性
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv

# 2. 生成美化模板
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output colors.txt

pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action highlight --output highlights.txt

# 3. 上传并导出
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt --config highlights.txt \
  --output result.svg --format svg
```
