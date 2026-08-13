# 分类分析教程

PyiTOL 提供完整的分类分析工具链：等级识别、信息提取、单系性检测和自动化美化。

## 1. 分类等级识别

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

自动识别标准分类等级（domain, phylum, class, order, family, genus, species）以及自定义列。

## 2. 分类信息提取

### 基础提取

```bash
pyitol taxonomy extract \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_tips.txt
```

输出格式：每行一个末端节点，包含 ID 和分类名。

### 统计提取（含 LCA 和成员数）

```bash
pyitol taxonomy extract-stats \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_stats.csv
```

输出列：rank, group, member_count, lca_node, members

### 从树末端名称提取

无需预先准备分类表格，直接从树末端（叶节点）名称自动提取分类学信息：

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format auto \
  --output taxonomy_from_names.csv
```

支持六种命名格式（通过 `--format` 指定）：

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
| `strict` | 严格模式（默认），按标准二叉树分类规则判定 |
| `relaxed` | 宽松模式，若成员仅占据多歧节点的部分子分支，判为并系而非复系 |
| `data-insufficient` | 数据不足模式，上述情况判为 `data_insufficient`，表示拓扑未解析、无法定论 |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --polytomy-mode relaxed \
  --output monophyly.csv
```

### 多棵树处理

当树文件包含多棵树时，通过 `--multi-tree-mode` 指定处理策略：

| 策略 | 说明 |
|------|------|
| `ask` | 默认，提示用户选择（非交互环境自动回退到 `first`） |
| `first` | 仅使用第一棵树 |
| `last` | 仅使用最后一棵树 |
| `random` | 随机选择一棵树 |
| `split` | 分别处理所有树，结果文件添加数字后缀 |
| `all` | 同 `split`，返回所有树分别处理 |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree trees.nexus \
  --rank Phylum --multi-tree-mode split \
  --output monophyly.csv
```

## 4. 单系性判定原理

PyiTOL 对每组末端节点执行以下算法：

1. **找 LCA**：计算类群所有成员的最近共同祖先
2. **算差集**：
   - `E = LCA后代 \ 类群成员`（混入节点）
   - `M = 类群成员 \ LCA后代`（缺失节点）
3. **判定**：
   - `E=∅` 且 `M=∅` → **单系群 (monophyletic)**
   - `M=∅` 且 `E≠∅` → **并系群 (paraphyletic)**
   - `M≠∅` → **多系群 (polyphyletic)**
   - `--polytomy-mode=data-insufficient` 且 LCA 为多歧节点、成员仅占据部分子分支且存在混入节点 → **数据不足 (data_insufficient)**

第四种状态 `data_insufficient` 仅在 `--polytomy-mode data-insufficient` 下出现：当 LCA 是多歧节点（未解析的多分叉），且类群成员散布于其中部分但非全部子分支，并伴随混入节点时，拓扑关系未充分解析，无法做出可靠的单系/并系/复系判定。此时输出 `data_insufficient` 状态以提示用户需补充数据或改用 `relaxed`/`strict` 模式。

多系群会进一步分解为亚组，输出每个亚组的 LCA 和成员。

## 5. 美化配置生成

根据单系性检测结果，自动生成 iTOL 模板：

### 为不同门类生成颜色条带

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

### 为高门类群添加符号标记

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
| `color-strip` | DATASET_COLORSTRIP | 颜色条带 |
| `style-branch` | DATASET_STYLE | 分支线型 |
| `style-label` | DATASET_STYLE | 标签样式 |
| `width` | TREE_COLORS (width) | 分支宽度 |
| `highlight` | DATASET_STYLE | 标签背景高亮 |
| `symbol` | DATASET_SYMBOLS | 符号标记 |
| `range` | DATASET_RANGE | 彩色范围 |
| `gradient` | DATASET_GRADIENT | 渐变色带 |

### 检查并美化（一步到位）

`check-and-style` 命令将单系性检查与美化模板生成合并为一步：先检查指定类群是否为单系群，若是则生成美化模板，否则发出警告并跳过。

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
| `color-strip` | 颜色条带 |

通过 `--taxonomy-source-priority` 控制同时提供外部分类表格和树名嵌入分类信息时的合并优先级：

| 取值 | 说明 |
|------|------|
| `table` | 表格优先（默认），以 `--taxonomy` 指定的分类表格为准 |
| `embedded` | 树名嵌入信息优先；树名提取的分类信息会填充表格中的缺失字段，冲突时以树名为准并输出 WARNING 日志 |

不提供 `--taxonomy` 时，可自动从树末端名称提取分类信息（需配合 `--name-format` 指定格式）。

#### 特殊标识符

`--taxon` 支持四个特殊标识符，用于定位生命树根部的关键祖先节点（需提供 `--taxonomy` 与 `--domain-column`）：

| 标识符 | 含义 |
|--------|------|
| `LUCA` | 所有古菌和细菌的最近共同祖先 |
| `LACA` | 所有古菌的最近共同祖先 |
| `LBCA` | 所有细菌的最近共同祖先 |
| `ROOT` | 全树根，返回树中所有末端节点，无需指定域 |

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "LBCA" --action highlight \
  --domain-column Domain --output lbca.txt
```

## 6. 二元数据转换

将分类数据转换为 0/1 矩阵：

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
