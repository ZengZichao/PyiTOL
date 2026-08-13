# Template Generation Tutorial

PyiTOL supports 31 template types under the iTOL v7 specification (created via the unified entry `template create <type>`). Additionally, `external-shape-bubble` (bubble external shape, a variant of `external-shape`) can be created through the dedicated subcommand `pyitol template create-external-shape-bubble` and is not covered by the unified entry. There are also 31 dedicated `create-*` subcommands available (`pyitol template create-color-strip`, etc.), which are functionally equivalent to the unified entry.

## Unified Entry

```bash
pyitol template create <type> \
  --taxonomy data.csv --tree tree.nwk \
  --column <column_name> --output output.txt
```

View all supported types:

```bash
pyitol template create --help
```

## Categorical Data Templates

### Color Strip

Adds a color strip to each terminal node to display categorical information.

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --strip-width 50 --palette nature
```

### Tree Colors

Colors branches, labels, ranges, or widths.

```bash
# Branch coloring (clade)
pyitol template create tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --color-type clade --output tree_colors.txt

# Label coloring
pyitol template create tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Genus --color-type label --output labels.txt
```

### Symbols

Adds symbols on branches.

```bash
pyitol template create symbols \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Type --symbol-type diamond --output symbols.txt
```

Symbol types: `diamond`, `circle`, `square`, `triangle`, `star`

### External Shape

Adds shape markers outside nodes.

```bash
pyitol template create external-shape \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Group --shape-type circle --output shapes.txt
```

### Branch

Colors branches according to categorical information.

```bash
pyitol template create branch \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output branch.txt
```

### Binary

Displays multiple binary (presence/absence) fields for each node, useful for scenarios such as gene presence/absence or phenotype markers.

```bash
pyitol template create binary \
  --taxonomy metadata.csv --tree tree.nwk \
  --columns "GeneA,GeneB,GeneC" --output binary.txt
```

### External Shape Bubble

Displays numeric data outside nodes as multiple columns of bubbles. This type is not part of the unified `template create` entry and must be created using the dedicated subcommand.

```bash
pyitol template create-external-shape-bubble \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "Sample1,Sample2,Sample3" --output bubble.txt
```

## Numeric Data Templates

### Simple Bar

```bash
pyitol template create simple-bar \
  --taxonomy metadata.csv --tree tree.nwk \
  --column GC_content --bar-color "#3c5484" --output bars.txt
```

### Multi-Bar

```bash
pyitol template create multi-bar \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "Sample1,Sample2,Sample3" \
  --field-labels "T1,T2,T3" --output multibar.txt
```

### Heatmap

```bash
pyitol template create heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns "A,B,C,D" \
  --gradient "#ff0000,#ffff00,#0000ff" --output heatmap.txt
```

### Pie Chart

```bash
pyitol template create pie \
  --taxonomy comp.csv --tree tree.nwk \
  --columns "CompA,CompB,CompC" --output pie.txt
```

### Boxplot

```bash
pyitol template create boxplot \
  --taxonomy stats.csv --tree tree.nwk \
  --output boxplot.txt
```

The data file must contain: minimum, q1, median, q3, maximum columns.

### Gradient

```bash
pyitol template create gradient \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Abundance --color-min "#ff0000" --color-max "#0000ff" \
  --output gradient.txt
```

### Linechart

Plots a line chart beside the tree to show how numeric values change along positions.

```bash
pyitol template create linechart \
  --taxonomy expr.csv --tree tree.nwk \
  --column Value --position-column Position \
  --color "#3c5484" --output linechart.txt
```

### Branch Gradient

Adds a color gradient to branches based on numeric data.

```bash
pyitol template create branch-gradient \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Abundance --color-min "#ff0000" --color-max "#0000ff" \
  --output branch_gradient.txt
```

## Tree Structure Templates

### Collapse

```bash
pyitol template create collapse \
  --node-ids "NodeA,NodeB" --output collapse.txt
```

### Prune

```bash
pyitol template create prune \
  --node-ids "NodeA,NodeB" --output prune.txt
```

### Spacing

```bash
pyitol template create spacing \
  --data-file spacing.csv --output spacing.txt
```

spacing.csv format: id, factor

### Ranges

Annotates grouped taxa with colored range bands to highlight clade distribution.

```bash
pyitol template create ranges \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output ranges.txt
```

### Style

Sets branch line styles, label fonts, and background styles.

```bash
pyitol template create style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --style-type branch \
  --line-style dashed --output style.txt
```

Style types: `branch`, `label`, `label_background`

## Annotation Templates

### Labels

```bash
pyitol template create labels \
  --taxonomy names.csv --tree tree.nwk \
  --column NewName --output labels.txt
```

### Popup Info

```bash
pyitol template create popup-info \
  --taxonomy info.csv --tree tree.nwk \
  --output popup.txt
```

info.csv must contain: id, title, content columns.

### Text

Adds custom text labels next to nodes.

```bash
pyitol template create text \
  --taxonomy metadata.csv --tree tree.nwk \
  --column Description --font-size 12 --output text.txt
```

### Image

Embeds images (local files or URLs) next to nodes.

```bash
pyitol template create image \
  --taxonomy images.csv --tree tree.nwk \
  --image-column ImageFile --image-width 50 --output images.txt
```

### Highlight

Adds background highlights to labels, colored by group.

```bash
pyitol template create highlight \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output highlight.txt
```

## Advanced Templates

### Connections

```bash
pyitol template create connections \
  --connections "[[A,B],[C,D]]" --output connections.txt
```

### Tanglegram

```bash
pyitol template create tanglegram \
  --connections "A,X;B,Y;C,Z" --output tanglegram.txt
```

### Domains

```bash
pyitol template create domains \
  --data-file domains.csv --output domains.txt
```

domains.csv format: id, from, to, type, color

### Arrows v7+

```bash
pyitol template create arrow \
  --data-file arrows.csv --output arrows.txt
```

### Placement v7+

```bash
pyitol template create placement \
  --data-file placement.csv --output placement.txt
```

### Timescale v7+

```bash
pyitol template create timescale \
  --data-file times.csv --output timescale.txt
```

times.csv format: time_point, label, color

### MEME Motifs v7+

```bash
pyitol template create meme \
  --data-file meme.csv --output meme.txt
```

### Manual v7+

```bash
pyitol template create manual \
  --data-file custom.csv --output manual.txt
```

## Bundling Multiple Templates in One Step

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

## Template Validation

```bash
pyitol template validate --template colors.txt
```

## Learn from Existing Templates

```bash
pyitol utils learn-template --template colors.txt --output learned.json
```

## Learning Themes in Batch

Learn recommended default parameters from a template directory:

```bash
pyitol learn train-theme --dir ./templates --output theme.json
```

## Delimiter Selection

All template commands support the `--separator` parameter:

| Value | Description |
|----|------|
| `TAB` | Tab character (default) |
| `SPACE` | Space |
| `COMMA` | Comma |

```bash
pyitol template create color-strip \
  --taxonomy data.csv --tree tree.nwk \
  --column Phylum --separator COMMA --output colors.txt
```

## Color Palettes

Use `--palette` to specify a preset color palette:

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --palette nature --output colors.txt
```

Available presets: `nature`, `cell`, `colorblind`

View the preset colors:

```bash
pyitol learn palette --preset-name nature
```
