# Template Generation Tutorial

[中文](templates.md) | English

PyiTOL supports 33 template types under the iTOL v7 specification (created via the unified entry `template create <type>`). In addition, `external-shape-bubble` (bubble external shape, a variant of `external-shape`) is not covered by the unified entry and can only be created through the dedicated subcommand `pyitol template create-external-shape-bubble`. The 33 unified-entry types plus the `external-shape-bubble` variant correspond to 34 dedicated `create-*` subcommands, 33 of which map one-to-one onto the unified entry: for example, `pyitol template create arrow` and `pyitol template create-arrow` are interchangeable, so you may use whichever style you prefer. The defaults applied when an option is omitted, however, are not the same: the unified entry shares one generic set of defaults across all types, while each dedicated subcommand carries defaults tuned for its own type (for gradient, `--strip-width` defaults to 50 through the unified entry but 25 through `create-gradient`; for boxplot, `--width` defaults to 1000 versus 1500; for connections, `--color` defaults to `#ff0000` versus `#e64b35`). Pass those options explicitly when you need identical output.

## Unified Entry

Apart from `--output` (optional; it defaults to `config_template.txt`), the required arguments of the unified entry **vary by type**: most types take `--taxonomy` + `--tree` plus one category column (`--column` or `--columns`), the data-file types take only `--data-file`, the connection types take only `--connections`, and the structural types take `--node-ids`. The skeleton in this section covers the most common family, and the comments inside the fence give the required arguments for every type:

```bash
# Required arguments grouped by type:
#   --taxonomy + --tree + --column: color-strip, branch, simple-bar, symbols, gradient, text,
#     external-shape, tree-colors, branch-gradient, ranges, highlight, style, linechart
#   --taxonomy + --tree + --columns: multi-bar, heatmap, pie, binary
#   --taxonomy + --tree + --column (the alternate names --label-column/--image-column/--alignment-column
#     are also accepted): labels, image, alignment; boxplot and popup-info need only --taxonomy + --tree (their column-name options default)
#   --data-file: domains, spacing, arrow, placement, timescale, meme, manual
#   --connections: connections (JSON file path), tanglegram (inline id1,id2;id3,id4)
#   --node-ids: prune; collapse takes --node-ids or --taxon + --rank + --taxonomy + --tree
#   external-shape-bubble is outside the unified entry, only create-external-shape-bubble handles it
pyitol template create <type> \
  --taxonomy data.csv --tree tree.nwk \
  --column <column_name> --output output.txt
```

View all supported types:

```bash
pyitol template create --help
```

> Note: the two invocation styles use **different names for the data file option**. The unified entry `template create` always uses `--data-file`; among the dedicated subcommands, `create-domains` and `create-spacing` use `--data`, while `create-arrow`, `create-placement`, `create-timescale`, `create-meme`, and `create-manual` still use `--data-file`. Check the option name before copying an example from one style to the other.

## Categorical Data Templates

### Color Strip

Adds a color strip to each leaf to display categorical information.

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --strip-width 50
```

`--palette` is a legal option of this type yet a reserved one with zero effect on the output, so the Color Strip example omits it (the reason is in the "Color Palettes (`--palette` currently inert)" section).

### Tree Colors

Colors clades, branches, labels, ranges, widths, or gradients according to `--color-type` (`clade`/`branch`/`label`/`width`/`range`/`gradient`, default `clade`); the `gradient` value requires a numeric column.

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

Symbol types: `circle`, `square`, `triangle`, `star`, `left-triangle`, `right-triangle`; `diamond` (used in the example above, and the default of `--symbol-type` in both invocation styles) is kept only for backward compatibility — iTOL's DATASET_SYMBOL has no diamond, so it falls back to `square` and a warning is logged.

### External Shapes

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

Adds a gradient color strip (gradient strip) to each leaf based on a numeric column.

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
  --connections pairs.json --output connections.txt
```

`--connections` takes a JSON **file path** (not an inline string); file format: `[["TaxonA","TaxonB"],["TaxonC","TaxonD"]]`

### Alignment

Displays sequence alignment results next to nodes, colored with a nucleotide or amino acid scheme.

```bash
pyitol template create alignment \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --alignment-column AlignedSeq --color-scheme amino_acid --output alignment.txt
```

Color schemes: `nucleotide`, `amino_acid`

### Tanglegram

```bash
pyitol template create tanglegram \
  --connections "A,X;B,Y;C,Z" --output tanglegram.txt
```

### Domains

```bash
pyitol template create domains \
  --data-file domains.json --output domains.txt
```

domains.json is JSON content (not CSV), one record per domain, in the format `[{"id":"TaxonA","from":"10","to":"50","type":"PF001","color":"#ff0000"}]`.

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

The canonical command is `learn template` (`--template`/`-t` repeatable for several template files, `--output`/`-o` for the result file):

```bash
pyitol learn template --template colors.txt --output learned.json
```

> `utils learn-template` is a duplicate of `learn template`; its source docstring records the duplication and points to `learn template`, and calling it emits a DeprecationWarning. The supported form is `learn template`.

## Learning Themes in Batch

Learn recommended default parameters from a template directory:

```bash
pyitol learn train-theme --dir ./templates --output theme.json
```

## Data Field Separator Selection

The unified entry `template create`, all 34 dedicated `create-*` subcommands, and `template bundle` accept `--separator` (the data field separator, which sets the character between fields of a template data row):

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

> `--separator` and the `--delimiter` of `taxonomy extract-from-names` (the name-segment delimiter) are two different things: the latter splits rank segments inside a leaf name (e.g. `Bacteria_Firmicutes_...`), the former splits the fields of a template data row.

## Color Palettes (`--palette` currently inert)

`--palette` is a legal option of both the unified entry `template create` and the dedicated subcommand `create-color-strip`, yet neither hands its value to any generator function: `create-color-strip` calls `generate_color_strip_template()` with no `palette` argument, and that function has no `palette` parameter either (the source marks it as reserved). Hence `--palette nature` yields exactly the same template as omitting the option, and the other 32 types ignore it outright.

A preset's colors are readable through `learn palette`, and the actual hand-off to the template happens via `--colors` (valid on the 10 commands `color-strip`, `branch`, `tree-colors`, `ranges`, `highlight`, `style`, `symbols`, `pie`, `multi-bar`, `external-shape`):

```bash
pyitol learn palette --preset-name nature
```

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt \
  --colors '{"Firmicutes":"#1f77b4","Proteobacteria":"#ff7f0e"}'
```

Queryable preset names: `nature`, `cell`, `colorblind`

## Related documents

- [Template Subcommand Reference](../templates-reference_en.md): full options and examples for all 34 dedicated `create-*` subcommands.
- [CLI Reference](../cli_en.md): command overview, the unified `template create` entry, global options, and exit codes.
- [API Guide](../api_en.md): iTOL batch API and Python API usage.
