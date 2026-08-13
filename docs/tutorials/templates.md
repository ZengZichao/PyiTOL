# 模板生成教程

PyiTOL 支持 iTOL v7 规范下的 31 种模板类型（通过统一入口 `template create <类型>` 创建）。另有 `external-shape-bubble`（气泡外部形状，`external-shape` 的变体）需通过专用子命令 `create-external-shape-bubble` 创建，不在统一入口支持范围内。除统一入口外，还提供 31 个功能等价的专用 `create-*` 子命令：例如 `pyitol template create arrow` 与 `pyitol template create-arrow` 等价，可按习惯选用。

## 统一入口

```bash
pyitol template create <类型> \
  --taxonomy data.csv --tree tree.nwk \
  --column <列名> --output output.txt
```

查看所有支持类型：

```bash
pyitol template create --help
```

## 分类数据类模板

### Color Strip（颜色条带）

为每个末端节点添加颜色条带，用于展示分类信息。

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --strip-width 50 --palette nature
```

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

### External Shape（外部形状）

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

### Gradient（颜色渐变）

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

为分组类群标注彩色范围带，突出 clade 分布。

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
  --connections "[[A,B],[C,D]]" --output connections.txt
```

### Tanglegram（纠缠图）

```bash
pyitol template create tanglegram \
  --connections "A,X;B,Y;C,Z" --output tanglegram.txt
```

### Domains（蛋白结构域）

```bash
pyitol template create domains \
  --data-file domains.csv --output domains.txt
```

domains.csv 格式：id, from, to, type, color

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

```bash
pyitol utils learn-template --template colors.txt --output learned.json
```

## 批量学习主题

从模板目录学习推荐默认参数：

```bash
pyitol learn train-theme --dir ./templates --output theme.json
```

## 分隔符选择

所有模板命令支持 `--separator` 参数：

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

## 配色预设

使用 `--palette` 指定预设配色：

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --palette nature --output colors.txt
```

可用预设：`nature`, `cell`, `colorblind`

查看预设颜色：

```bash
pyitol learn palette --preset-name nature
```
