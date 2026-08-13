# 模板生成专用子命令参考（template create-*）

本页逐个记录 `pyitol template` 下的 **34 个专用子命令**（`pyitol template create-*`）。这些命令与统一入口 `pyitol template create <类型>` 功能等价，但每个命令只接受其类型专属的参数，适合在脚本中精确调用，且无需记忆 `template_type` 字符串。

> 统一入口 `pyitol template create` 已支持 31 种类型，外加 `external-shape-bubble` 仅能通过本页专用子命令生成。若你只需要偶尔生成模板，使用统一入口即可；若你在流水线中按固定类型批量调用，专用子命令更直观。

## 公共选项

除专门说明外，以下选项适用于本页所有命令（默认值以源码为准）：

| 选项 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--output` | `-o` | `config_template.txt` | 输出模板文件路径 |
| `--taxonomy` | `-t` | （多数命令必填） | 分类信息表格文件路径 |
| `--tree` | `-r` | （多数命令必填） | Newick 树文件路径 |
| `--label` | `-l` | 随类型变化 | 数据集标签 |
| `--id-column` | | `id` | ID 列名 |
| `--separator` | `-s` | `TAB` | 数据分隔符：`TAB`/`SPACE`/`COMMA` |
| `--colors` | | | 自定义颜色映射，支持 JSON（`{"A":"#ff0000"}`）或简写（`A:#ff0000,B:#00ff00`） |

> 与统一入口不同，专用子命令**不支持** `--force` / `--no-clobber`：若输出文件已存在会直接报错退出。请改用不同的 `--output` 或先删除旧文件。

根据输入依赖，本页命令分为三类：
- **数据集注释类**：基于“树 + 分类表”的列生成数据集；多数需要 `--tree` 与 `--taxonomy`。
- **树结构操作类**：折叠、修剪、间距、着色、样式等。
- **高级注释类**：需要外部数据文件（`--data` / `--connections`），不依赖树与分类表。

---

## 一、数据集注释类（Datasets）

### `pyitol template create-color-strip`

为末端分支添加分类色带（color strip）。

**专属选项**：`--column`/`-c`（必填，分类列名）、`--colors`、`--strip-width`（默认 `50`）、`--palette`（配色预设子集名）。

```bash
pyitol template create-color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --strip-width 60 --output color_strip.txt
```

### `pyitol template create-branch`

根据分类信息为分支着色（branch coloring）。

**专属选项**：`--column`/`-c`（必填）、`--colors`。

```bash
pyitol template create-branch \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Class --colors '{"A":"#ff0000","B":"#00ff00"}' --output branch.txt
```

### `pyitol template create-simple-bar`

单值柱状图（simple bar chart）。

**专属选项**：`--column`/`-c`（必填，数值列名）、`--bar-color`（默认 `#3c5484`）、`--bar-width`（默认 `50`）。

```bash
pyitol template create-simple-bar \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Abundance --bar-color "#1f77b4" --output simple_bar.txt
```

### `pyitol template create-multi-bar`

多值柱状图（multi bar chart）。

**专属选项**：`--columns`/`-c`（必填，逗号分隔多列）、`--colors`、`--field-labels`（字段标签，逗号分隔）、`--width`（默认 `1000`）、`--alignment`（默认 `center`）。

```bash
pyitol template create-multi-bar \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Sample1,Sample2,Sample3 \
  --field-labels S1,S2,S3 --width 1200 --output multi_bar.txt
```

### `pyitol template create-heatmap`

热图（heatmap）。

**专属选项**：`--columns`/`-c`（必填，逗号分隔多列）、`--gradient`（颜色渐变，逗号分隔色值，如 `#ff0000,#ffffff,#0000ff`）。

```bash
pyitol template create-heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Gene1,Gene2,Gene3 \
  --gradient "#d73027,#ffffbf,#1a9850" --output heatmap.txt
```

### `pyitol template create-symbols`

符号标记（symbols）。

**专属选项**：`--column`/`-c`（必填）、`--symbol-type`（默认 `diamond`；可选 `diamond`/`circle`/`square`/`triangle`/`star`）、`--colors`、`--size`（默认 `30`）。

```bash
pyitol template create-symbols \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Status --symbol-type circle --size 40 --output symbols.txt
```

### `pyitol template create-pie`

饼图（pie chart）。

**专属选项**：`--columns`/`-c`（必填，逗号分隔多列）、`--colors`、`--pie-size`（默认 `50`）。

```bash
pyitol template create-pie \
  --taxonomy counts.csv --tree tree.nwk \
  --columns CatA,CatB,CatC --pie-size 70 --output pie.txt
```

### `pyitol template create-boxplot`

箱线图（boxplot），列名指向预计算的最小值/四分位数/中位数/最大值。

**专属选项**：`--min`（默认列名 `minimum`）、`--q1`（默认 `q1`）、`--median`（默认 `median`）、`--q3`（默认 `q3`）、`--max`（默认 `maximum`）、`--extremes`（极端值列名，逗号分隔，可选）、`--color`（默认 `#00ff00`）、`--width`（默认 `1500`）。

```bash
pyitol template create-boxplot \
  --taxonomy stats.csv --tree tree.nwk \
  --min minimum --q1 q1 --median median --q3 q3 --max maximum \
  --color "#4c78a8" --output boxplot.txt
```

### `pyitol template create-gradient`

基于数值列的颜色渐变色带（gradient strip）。

**专属选项**：`--column`/`-c`（必填）、`--color-min`（默认 `#ff0000`）、`--color-max`（默认 `#0000ff`）、`--strip-width`（默认 `25`）、`--use-mid-color`（开关，启用中间色）、`--color-mid`（默认 `#ffff00`）。

```bash
pyitol template create-gradient \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Value --color-min "#ff0000" --color-max "#0000ff" \
  --use-mid-color --color-mid "#ffff00" --output gradient.txt
```

### `pyitol template create-labels`

重命名/自定义末端标签（labels）。

**专属选项**：`--column`/`-c`（必填，标签列名）。

```bash
pyitol template create-labels \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column DisplayName --output labels.txt
```

### `pyitol template create-popup-info`

悬停信息（popup info），鼠标悬停节点时显示标题与内容。

**专属选项**：`--title-column`（默认 `title`）、`--content-column`（默认 `content`）。

```bash
pyitol template create-popup-info \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --title-column Species --content-column Description --output popup.txt
```

### `pyitol template create-binary`

二元数据（binary dataset），将分类列转为 0/1 字段。

**专属选项**：`--columns`/`-c`（必填，逗号分隔分类列）、`--field-colors`（默认 `#ff0000,#00ff00,#0000ff`）、`--field-shapes`（默认 `1,2,3`，取值 1–6）、`--color`（默认 `#ff0000`）、`--show-internal`（默认 `1`，是否显示内部节点）。

```bash
pyitol template create-binary \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --columns Trait1,Trait2,Trait3 \
  --field-colors "#e41a1c,#377eb8,#4daf4a" --output binary.txt
```

### `pyitol template create-text`

文本标签（text labels），在每个节点旁显示文本。

**专属选项**：`--column`/`-c`（必填）、`--font-size`（默认 `12`）、`--font-style`（默认 `normal`）。

```bash
pyitol template create-text \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Note --font-size 14 --output text.txt
```

### `pyitol template create-external-shape`

外部形状标记（external shape），在树外侧绘制形状。

**专属选项**：`--column`/`-c`（必填）、`--shape-type`（默认 `circle`；可选 `circle`/`square`/`star`/`triangle_right`/`triangle_left`/`checkmark`）、`--colors`、`--size`（默认 `20`）。

```bash
pyitol template create-external-shape \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Group --shape-type star --size 25 --output ext_shape.txt
```

### `pyitol template create-connections`

连接线（connections）。**不依赖树与分类表**，读取连接对 JSON 文件。

**专属选项**：`--connections`/`-c`（必填，JSON 文件路径，格式 `[[id1,id2],...]`）、`--color`（默认 `#e64b35`）、`--line-width`（默认 `2`）、`--line-type`（默认 `solid`；可选 `solid`/`dotted`/`dashed`）、`--arrow-head-size`（默认 `1`）。

```bash
# pairs.json: [["TaxonA","TaxonB"], ["TaxonC","TaxonD"]]
pyitol template create-connections \
  --connections pairs.json --color "#e64b35" --line-type dashed --output connections.txt
```

### `pyitol template create-domains`

蛋白质结构域（protein domains）。**不依赖树与分类表**，读取 JSON 数据文件。

**专属选项**：`--data`/`-d`（必填，JSON 文件路径）、`--color`（默认 `#ff00aa`）、`--scale`（尺度，可选）。

```bash
# domains.json: [{"id":"TaxonA","domains":[{"start":1,"end":50,"name":"PF001","color":"#ff0000"}]}]
pyitol template create-domains \
  --data domains.json --color "#ff00aa" --output domains.txt
```

---

## 二、树结构操作类（Tree Structure）

### `pyitol template create-tree-colors`

树着色（tree colors），支持分支、标签、分支线宽、范围、渐变等多种着色类型。

**专属选项**：`--column`/`-c`（必填）、`--colors`、`--color-type`（默认 `clade`；可选 `clade`/`label`/`branch`/`width`/`range`/`gradient`）、`--width-value`（默认 `3`，仅 `width` 类型）。

```bash
# 按分支着色
pyitol template create-tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --color-type branch --output tree_colors_branch.txt

# 按数值渐变着色
pyitol template create-tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Score --color-type gradient --output tree_colors_grad.txt
```

### `pyitol template create-branch-gradient`

分支渐变（branch gradient），依据数值列为分支着色渐变。

**专属选项**：`--column`/`-c`（必填）、`--color-min`（默认 `#ff0000`）、`--color-max`（默认 `#0000ff`）、`--use-mid-color`（开关）、`--color-mid`（默认 `#ffff00`）。

```bash
pyitol template create-branch-gradient \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Distance --color-min "#fee090" --color-max "#4575b4" --output branch_grad.txt
```

### `pyitol template create-collapse`

折叠分支（collapse clades）。支持两种方式：
1. `--node-ids` 直接指定节点 ID；
2. `--taxon` + `--rank` + `--taxonomy` + `--tree` 按类群名称查找（会先检测单系性）。

非单系群默认跳过并继续，`--strict` 可改为终止。

**专属选项**：`--node-ids`/`-n`（逗号分隔）、`--taxon`、`--rank`、`--taxonomy`/`-t`、`--tree`/`-r`、`--strict`（开关）。

```bash
# 方式一：按节点 ID 折叠
pyitol template create-collapse \
  --node-ids "TaxonA,TaxonB" --output collapse_ids.txt

# 方式二：按类群名称折叠（先检测单系性）
pyitol template create-collapse \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxon Cyanobacteriota --rank Phylum --strict --output collapse_taxon.txt
```

### `pyitol template create-prune`

修剪分支（prune），移除指定节点。**不依赖树与分类表**。

**专属选项**：`--node-ids`/`-n`（必填，逗号分隔）。

```bash
pyitol template create-prune \
  --node-ids "TaxonX,TaxonY,TaxonZ" --output prune.txt
```

### `pyitol template create-spacing`

节点间距（node spacing）。**不依赖树与分类表**，读取含 `id` 与 `factor` 列的 CSV。

**专属选项**：`--data`/`-d`（必填，CSV 文件路径）。

```bash
# spacing.csv: id,factor
# TaxonA,2.0
# TaxonB,0.5
pyitol template create-spacing --data spacing.csv --output spacing.txt
```

### `pyitol template create-ranges`

彩色范围（colored ranges），按列分组后绘制连续范围背景。

**专属选项**：`--column`/`-c`（必填）、`--colors`。

```bash
pyitol template create-ranges \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Biome --colors '{"Marine":"#1f77b4","Soil":"#aec7e8"}' --output ranges.txt
```

### `pyitol template create-highlight`

标签背景高亮（label highlight）。

**专属选项**：`--column`/`-c`（必填）、`--colors`。

```bash
pyitol template create-highlight \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Category --colors '{"Pathogenic":"#d62728"}' --output highlight.txt
```

### `pyitol template create-style`

分支/标签样式（style），设置线型、字体、背景。

**专属选项**：`--column`/`-c`（必填）、`--style-type`（默认 `branch`；可选 `branch`/`label`/`label_background`）、`--colors`、`--line-style`（默认 `normal`；可选 `normal`/`dashed`/`dotted`）、`--font`（默认 `Arial`）、`--size`（默认 `1`）。

```bash
pyitol template create-style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Lineage --style-type branch --line-style dashed --output style.txt
```

### `pyitol template create-arrow`

箭头注释（arrows）。**不依赖树与分类表**，读取含 `id`、`position`、`direction`、`color` 列的 CSV。

**专属选项**：`--data-file`/`-d`（必填，CSV 文件路径）、`--color`（默认 `#ff0000`）、`--arrow-size`（默认 `30`）。

```bash
# arrows.csv: id,position,direction,color
# TaxonA,0.5,right,#ff0000
pyitol template create-arrow --data-file arrows.csv --arrow-size 40 --output arrows.txt
```

---

## 三、高级注释类（Advanced）

### `pyitol template create-linechart`

折线图（line chart），在树旁绘制数值折线。

**专属选项**：`--column`/`-c`（必填，数值列名）、`--position-column`/`-p`（位置列名，默认用行号）、`--color`（默认 `#3c5484`）、`--line-width`（默认 `2`）。

```bash
pyitol template create-linechart \
  --taxonomy expr.csv --tree tree.nwk \
  --column Expression --position-column Time --output linechart.txt
```

### `pyitol template create-image`

图像嵌入（images），在节点旁嵌入图片文件或 URL。

**专属选项**：`--image-column`/`-i`（必填，图像文件名列名）、`--url-column`/`-u`（图像 URL 列名，可选）、`--image-width`（默认 `50`）。

```bash
pyitol template create-image \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --image-column PhotoFile --url-column PhotoURL --image-width 60 --output images.txt
```

### `pyitol template create-alignment`

序列比对（alignment）展示。

**专属选项**：`--alignment-column`/`-a`（必填，序列比对列名）、`--color-scheme`（默认 `nucleotide`；可选 `nucleotide`/`amino_acid`）。

```bash
pyitol template create-alignment \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --alignment-column AlignedSeq --color-scheme amino_acid --output alignment.txt
```

### `pyitol template create-tanglegram`

纠缠图（tanglegram），连接两棵树之间的对应节点。**不依赖树与分类表**。

**专属选项**：`--connections`/`-c`（必填，格式 `id1,id2;id3,id4`）、`--color`（默认 `#999999`）、`--line-width`（默认 `1`）。

```bash
pyitol template create-tanglegram \
  --connections "TaxonA,TaxonA2;TaxonB,TaxonB2" \
  --color "#999999" --output tanglegram.txt
```

### `pyitol template create-placement`

系统发育放置（phylogenetic placement）。**不依赖树与分类表**，读取含 `id`、`position`、`count`、`color` 列的 CSV。

**专属选项**：`--data-file`/`-d`（必填，CSV 文件路径）、`--color`（默认 `#ff0000`）、`--spacing`（默认 `5`）。

```bash
# placement.csv: id,position,count,color
# Query1,0.8,12,#ff0000
pyitol template create-placement --data-file placement.csv --spacing 8 --output placement.txt
```

### `pyitol template create-timescale`

时间尺度（timescale），在分支上添加时间刻度。**不依赖树与分类表**，读取含 `time_point`、`label`、`color` 列的 CSV。

**专属选项**：`--data-file`/`-d`（必填，CSV 文件路径）、`--color`（默认 `#000000`）、`--scale-position`（默认 `bottom`；可选 `top`/`bottom`/`both`）。

```bash
# timescale.csv: time_point,label,color
# 0.5,Middle,#000000
pyitol template create-timescale --data-file timescale.csv --scale-position both --output timescale.txt
```

### `pyitol template create-meme`

MEME 基序（MEME motifs）。**不依赖树与分类表**，读取含 `id`、`start`、`end`、`name`、`color` 列的 CSV。

**专属选项**：`--data-file`/`-d`（必填，CSV 文件路径）、`--color`（默认 `#ff0000`）、`--show-labels`（默认 `1`）。

```bash
# meme.csv: id,start,end,name,color
# Seq1,10,30,Motif1,#ff0000
pyitol template create-meme --data-file meme.csv --show-labels 1 --output meme.txt
```

### `pyitol template create-manual`

手动注释（manual），自由格式自定义数据。**不依赖树与分类表**，读取任意列 CSV。

**专属选项**：`--data-file`/`-d`（必填，CSV 文件路径）、`--color`（默认 `#ff0000`）、`--custom-header`（自定义头部 JSON，如 `{"KEY":"VALUE"}`）。

```bash
pyitol template create-manual \
  --data-file custom.csv --custom-header '{"FIELD_SHAPE":"1"}' --output manual.txt
```

### `pyitol template create-external-shape-bubble`

多列气泡外部形状（external shape bubble），为多个数值列绘制气泡。

**专属选项**：`--columns`/`-c`（必填，逗号分隔数值列）。

```bash
pyitol template create-external-shape-bubble \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Metric1,Metric2,Metric3 --output bubble.txt
```

---

## 相关页面

- [CLI 完整参考](cli.md)：命令总览、统一入口 `template create`、全局参数与退出码。
- [模板生成教程](tutorials/templates.md)：30+ 种模板的选型与组合示例。
- [API 使用指南](api.md)：iTOL 批量 API 与 Python API 用法。
