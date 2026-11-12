# 模板生成教程

[English](templates_en.md) | 中文

PyiTOL 支持 iTOL v7 规范下的 33 种模板类型（通过统一入口 `template create <类型>` 创建）。另有 `external-shape-bubble`（气泡外部形状，`external-shape` 的变体）不在统一入口支持范围内，只能通过专用子命令 `create-external-shape-bubble` 创建。统一入口的 33 种类型加上 `external-shape-bubble` 变体，共对应 34 个专用 `create-*` 子命令，其中 33 个与统一入口功能等价：例如 `pyitol template create arrow` 与 `pyitol template create-arrow` 等价，可按习惯选用。

## 统一入口

除 `--output` 之外，统一入口的必选参数**按类型而变**：多数类型要 `--taxonomy` + `--tree` 再加一个分类列（`--column` 或 `--columns`），数据文件类只给 `--data-file`，连接类只给 `--connections`，结构类给 `--node-ids`。下面的骨架演示最常见的一类，注释里给出各类型的必选参数：

```bash
# 必选参数按类型分组：
#   --taxonomy + --tree + --column：color-strip、branch、simple-bar、symbols、gradient、text、
#     external-shape、tree-colors、branch-gradient、ranges、highlight、style、linechart
#   --taxonomy + --tree + --columns：multi-bar、heatmap、pie、binary
#   --taxonomy + --tree + --column（也可用替代名 --label-column/--image-column/--alignment-column）：
#     labels、image、alignment；boxplot、popup-info 只需 --taxonomy + --tree（统计列名有默认值）
#   --data-file：domains、spacing、arrow、placement、timescale、meme、manual
#   --connections：connections（JSON 文件路径）、tanglegram（内联 id1,id2;id3,id4）
#   --node-ids：prune；collapse 用 --node-ids，或 --taxon + --rank + --taxonomy + --tree
#   external-shape-bubble 不在统一入口内，只能用专用子命令 create-external-shape-bubble
pyitol template create <类型> \
  --taxonomy data.csv --tree tree.nwk \
  --column <列名> --output output.txt
```

查看所有支持类型：

```bash
pyitol template create --help
```

> 注意：两种调用方式的**数据文件参数名不同**。统一入口 `template create` 一律使用 `--data-file`；专用子命令中 `create-domains`、`create-spacing` 使用 `--data`，而 `create-arrow`、`create-placement`、`create-timescale`、`create-meme`、`create-manual` 仍使用 `--data-file`。在两种写法之间复制示例时请先核对参数名。

## 分类数据类模板

### Color Strip（色带）

为每个末端（叶）添加色带（color strip），用于展示分类信息。

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --strip-width 50
```

`--palette` 虽是此类型的合法选项，但目前是保留选项、对输出无影响，故示例里不再使用（原因见“配色预设（`--palette` 暂不生效）”一节）。

### Tree Colors（树着色）

对分支、标签、范围或宽度进行着色。

```bash
# 分支着色（clade）
pyitol template create tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --color-type clade --output tree_colors.txt

# 标签着色
pyitol template create tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Genus --color-type label --output labels.txt
```

### Symbols（符号标记）

在分支上添加符号。

```bash
pyitol template create symbols \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Type --symbol-type diamond --output symbols.txt
```

符号类型：`diamond`, `circle`, `square`, `triangle`, `star`

### External Shapes（外部形状）

在节点外部添加形状标记。

```bash
pyitol template create external-shape \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Group --shape-type circle --output shapes.txt
```

### Branch（分支着色）

根据分类信息为分支着色。

```bash
pyitol template create branch \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output branch.txt
```

### Binary（二元数据）

为每个节点展示多个二元（存在/缺失）字段，可用于基因有无、表型标记等场景。

```bash
pyitol template create binary \
  --taxonomy metadata.csv --tree tree.nwk \
  --columns "GeneA,GeneB,GeneC" --output binary.txt
```

### External Shape Bubble（气泡外部形状）

以多列气泡形式在节点外部展示数值数据。该类型不在统一入口 `template create` 中，需使用专用子命令创建。

```bash
pyitol template create-external-shape-bubble \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "Sample1,Sample2,Sample3" --output bubble.txt
```

## 数值数据类模板

### Simple Bar（单值柱状图）

```bash
pyitol template create simple-bar \
  --taxonomy metadata.csv --tree tree.nwk \
  --column GC_content --bar-color "#3c5484" --output bars.txt
```

### Multi-Bar（多值柱状图）

```bash
pyitol template create multi-bar \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "Sample1,Sample2,Sample3" \
  --field-labels "T1,T2,T3" --output multibar.txt
```

### Heatmap（热图）

```bash
pyitol template create heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "A,B,C,D" \
  --gradient "#ff0000,#ffff00,#0000ff" --output heatmap.txt
```

### Pie Chart（饼图）

```bash
pyitol template create pie \
  --taxonomy comp.csv --tree tree.nwk \
  --columns "CompA,CompB,CompC" --output pie.txt
```

### Boxplot（箱线图）

```bash
pyitol template create boxplot \
  --taxonomy stats.csv --tree tree.nwk \
  --output boxplot.txt
```

数据文件需包含：minimum, q1, median, q3, maximum 列。

### Gradient（渐变色带）

按数值列为末端（叶）添加渐变色带（gradient strip）。

```bash
pyitol template create gradient \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Abundance --color-min "#ff0000" --color-max "#0000ff" \
  --output gradient.txt
```

### Linechart（折线图）

在树旁绘制折线图，展示数值随位置的变化趋势。

```bash
pyitol template create linechart \
  --taxonomy expr.csv --tree tree.nwk \
  --column Value --position-column Position \
  --color "#3c5484" --output linechart.txt
```

### Branch Gradient（分支渐变）

根据数值数据为分支添加颜色渐变效果。

```bash
pyitol template create branch-gradient \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Abundance --color-min "#ff0000" --color-max "#0000ff" \
  --output branch_gradient.txt
```

## 树结构类模板

### Collapse（折叠分支）

```bash
pyitol template create collapse \
  --node-ids "NodeA,NodeB" --output collapse.txt
```

### Prune（修剪分支）

```bash
pyitol template create prune \
  --node-ids "NodeA,NodeB" --output prune.txt
```

### Spacing（节点间距）

```bash
pyitol template create spacing \
  --data-file spacing.csv --output spacing.txt
```

spacing.csv 格式：id, factor

### Ranges（彩色范围）

为分组类群标注彩色范围带，突出单系群（clade）分布。

```bash
pyitol template create ranges \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output ranges.txt
```

### Style（样式）

设置分支线型、标签字体和背景样式。

```bash
pyitol template create style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --style-type branch \
  --line-style dashed --output style.txt
```

样式类型：`branch`, `label`, `label_background`

## 注释类模板

### Labels（标签重命名）

```bash
pyitol template create labels \
  --taxonomy names.csv --tree tree.nwk \
  --column NewName --output labels.txt
```

### Popup Info（悬停信息）

```bash
pyitol template create popup-info \
  --taxonomy info.csv --tree tree.nwk \
  --output popup.txt
```

info.csv 需包含：id, title, content 列。

### Text（文本标签）

在节点旁添加自定义文本标签。

```bash
pyitol template create text \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Description --font-size 12 --output text.txt
```

### Image（图像嵌入）

在节点旁嵌入图像（本地文件或 URL）。

```bash
pyitol template create image \
  --taxonomy images.csv --tree tree.nwk \
  --image-column ImageFile --image-width 50 --output images.txt
```

### Highlight（高亮）

为标签添加背景高亮，按分组着色。

```bash
pyitol template create highlight \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output highlight.txt
```

## 高级模板

### Connections（连接线）

```bash
pyitol template create connections \
  --connections pairs.json --output connections.txt
```

`--connections` 接收的是 JSON **文件路径**（不是内联字符串），文件格式：`[["TaxonA","TaxonB"],["TaxonC","TaxonD"]]`

### Alignment（序列比对）

在节点旁展示序列比对结果，按核苷酸或氨基酸方案着色。

```bash
pyitol template create alignment \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --alignment-column AlignedSeq --color-scheme amino_acid --output alignment.txt
```

颜色方案：`nucleotide`, `amino_acid`

### Tanglegram（纠缠图）

```bash
pyitol template create tanglegram \
  --connections "A,X;B,Y;C,Z" --output tanglegram.txt
```

### Domains（蛋白结构域）

```bash
pyitol template create domains \
  --data-file domains.json --output domains.txt
```

domains.json 为 JSON 内容（不是 CSV），格式为 `[{"id":"TaxonA","domains":[{"start":1,"end":50,"name":"PF001","color":"#ff0000"}]}]`。

### Arrows（箭头注释）v7+

```bash
pyitol template create arrow \
  --data-file arrows.csv --output arrows.txt
```

### Placement（系统发育放置）v7+

```bash
pyitol template create placement \
  --data-file placement.csv --output placement.txt
```

### Timescale（时间尺度）v7+

```bash
pyitol template create timescale \
  --data-file times.csv --output timescale.txt
```

times.csv 格式：time_point, label, color

### MEME Motifs（基序注释）v7+

```bash
pyitol template create meme \
  --data-file meme.csv --output meme.txt
```

### Manual（手动注释）v7+

```bash
pyitol template create manual \
  --data-file custom.csv --output manual.txt
```

## 一键打包多个模板

```bash
pyitol template bundle \
  --output-dir ./templates \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --config '[
    {"type":"color-strip","column":"Phylum"},
    {"type":"simple-bar","column":"GC_content"},
    {"type":"heatmap","columns":["A","B","C"]}
  ]' \
  --prefix "fig1_"
```

## 模板验证

```bash
pyitol template validate --template colors.txt
```

## 从已有模板学习

规范命令是 `learn template`（`--template`/`-t` 可重复指定多个模板文件，`--output`/`-o` 指定输出）：

```bash
pyitol learn template --template colors.txt --output learned.json
```

> `utils learn-template` 是与 `learn template` 功能重复的命令，源码 docstring 已标注该重复并建议改用 `learn template`，调用时还会发出 DeprecationWarning；受支持的写法是 `learn template`。

## 批量学习主题

从模板目录学习推荐默认参数：

```bash
pyitol learn train-theme --dir ./templates --output theme.json
```

## 数据字段分隔符选择

统一入口 `template create`、34 个专用 `create-*` 子命令以及 `template bundle` 都支持 `--separator`（数据字段分隔符，决定模板数据行各字段之间用什么字符分隔）：

| 值 | 说明 |
|----|------|
| `TAB` | 制表符（默认） |
| `SPACE` | 空格 |
| `COMMA` | 逗号 |

```bash
pyitol template create color-strip \
  --taxonomy data.csv --tree tree.nwk \
  --column Phylum --separator COMMA --output colors.txt
```

> `--separator` 与 `taxonomy extract-from-names` 的 `--delimiter`（名称分段符）是两回事：后者拆分末端（叶）名称内部的分类等级片段（如 `Bacteria_Firmicutes_...`），前者拆分模板数据行的字段。

## 配色预设（`--palette` 暂不生效）

`--palette` 是统一入口 `template create` 与专用子命令 `create-color-strip` 的合法选项，但两处都没有把它的值交给任何生成函数：`create-color-strip` 调用 `generate_color_strip_template()` 时不带 `palette` 实参，而该函数也没有 `palette` 形参（源码里注明它是保留参数）。因此 `--palette nature` 与省略该选项产出的模板内容相同，其余 32 种类型更是直接忽略它。

要用上预设配色，先用 `learn palette` 查出预设里的颜色，再经 `--colors` 显式传入（`--colors` 对 `color-strip`、`branch`、`tree-colors`、`ranges`、`highlight`、`style`、`symbols`、`pie`、`multi-bar`、`external-shape` 这 10 个命令有效）：

```bash
pyitol learn palette --preset-name nature
```

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --colors '{"Firmicutes":"#1f77b4","Proteobacteria":"#ff7f0e"}'
```

可查询的预设名：`nature`, `cell`, `colorblind`

## 相关文档

- [模板生成专用子命令参考](../templates-reference.md)：34 个专用 `create-*` 子命令的完整选项与示例。
- [CLI 完整参考](../cli.md)：命令总览、统一入口 `template create`、全局参数与退出码。
- [API 使用指南](../api.md)：iTOL 批量 API 与 Python API 用法。
