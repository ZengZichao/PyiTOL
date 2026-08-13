# Template Generation Subcommand Reference (`template create-*`)

This page documents all **34 dedicated subcommands** under `pyitol template` (`pyitol template create-*`). They are functionally equivalent to the unified entry point `pyitol template create <type>`, but each command accepts only its type-specific parameters — ideal for precise scripting and pipelines, with no need to remember the `template_type` string.

> The unified entry `pyitol template create` supports 31 types; `external-shape-bubble` is only available through the dedicated subcommand on this page. Use the unified entry for occasional template generation; use dedicated subcommands for fixed-type batch calls in pipelines.

## Common options

Unless noted otherwise, the following options apply to every command on this page (defaults taken from source):

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--output` | `-o` | `config_template.txt` | Output template file path |
| `--taxonomy` | `-t` | (required by most) | Taxonomy table file path |
| `--tree` | `-r` | (required by most) | Newick tree file path |
| `--label` | `-l` | varies by type | Dataset label |
| `--id-column` | | `id` | ID column name |
| `--separator` | `-s` | `TAB` | Data separator: `TAB`/`SPACE`/`COMMA` |
| `--colors` | | | Custom color map; JSON (`{"A":"#ff0000"}`) or shorthand (`A:#ff0000,B:#00ff00`) |

> Unlike the unified entry, dedicated subcommands do **not** support `--force` / `--no-clobber`: if the output file exists, the command errors out. Use a different `--output` or delete the old file first.

By input dependency, the commands are grouped into three classes:
- **Datasets**: generated from "tree + taxonomy" columns; most require `--tree` and `--taxonomy`.
- **Tree structure**: collapse, prune, spacing, coloring, styling, etc.
- **Advanced**: require an external data file (`--data` / `--connections`); do not depend on tree or taxonomy.

---

## 1. Datasets

### `pyitol template create-color-strip`

Add a classification color strip to terminal branches.

**Specific options**: `--column`/`-c` (required, category column), `--colors`, `--strip-width` (default `50`), `--palette` (palette subset name).

```bash
pyitol template create-color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --strip-width 60 --output color_strip.txt
```

### `pyitol template create-branch`

Color branches by taxonomy (branch coloring).

**Specific options**: `--column`/`-c` (required), `--colors`.

```bash
pyitol template create-branch \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Class --colors '{"A":"#ff0000","B":"#00ff00"}' --output branch.txt
```

### `pyitol template create-simple-bar`

Single-value bar chart.

**Specific options**: `--column`/`-c` (required, numeric column), `--bar-color` (default `#3c5484`), `--bar-width` (default `50`).

```bash
pyitol template create-simple-bar \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Abundance --bar-color "#1f77b4" --output simple_bar.txt
```

### `pyitol template create-multi-bar`

Multi-value bar chart.

**Specific options**: `--columns`/`-c` (required, comma-separated columns), `--colors`, `--field-labels` (comma-separated field labels), `--width` (default `1000`), `--alignment` (default `center`).

```bash
pyitol template create-multi-bar \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Sample1,Sample2,Sample3 \
  --field-labels S1,S2,S3 --width 1200 --output multi_bar.txt
```

### `pyitol template create-heatmap`

Heatmap.

**Specific options**: `--columns`/`-c` (required, comma-separated columns), `--gradient` (color gradient, comma-separated values, e.g. `#ff0000,#ffffff,#0000ff`).

```bash
pyitol template create-heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Gene1,Gene2,Gene3 \
  --gradient "#d73027,#ffffbf,#1a9850" --output heatmap.txt
```

### `pyitol template create-symbols`

Symbol markers.

**Specific options**: `--column`/`-c` (required), `--symbol-type` (default `diamond`; `diamond`/`circle`/`square`/`triangle`/`star`), `--colors`, `--size` (default `30`).

```bash
pyitol template create-symbols \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Status --symbol-type circle --size 40 --output symbols.txt
```

### `pyitol template create-pie`

Pie chart.

**Specific options**: `--columns`/`-c` (required, comma-separated columns), `--colors`, `--pie-size` (default `50`).

```bash
pyitol template create-pie \
  --taxonomy counts.csv --tree tree.nwk \
  --columns CatA,CatB,CatC --pie-size 70 --output pie.txt
```

### `pyitol template create-boxplot`

Boxplot; columns point to precomputed min/quartiles/median/max.

**Specific options**: `--min` (default column `minimum`), `--q1` (default `q1`), `--median` (default `median`), `--q3` (default `q3`), `--max` (default `maximum`), `--extremes` (extreme-value columns, comma-separated, optional), `--color` (default `#00ff00`), `--width` (default `1500`).

```bash
pyitol template create-boxplot \
  --taxonomy stats.csv --tree tree.nwk \
  --min minimum --q1 q1 --median median --q3 q3 --max maximum \
  --color "#4c78a8" --output boxplot.txt
```

### `pyitol template create-gradient`

Numeric gradient color strip.

**Specific options**: `--column`/`-c` (required), `--color-min` (default `#ff0000`), `--color-max` (default `#0000ff`), `--strip-width` (default `25`), `--use-mid-color` (flag, enable mid color), `--color-mid` (default `#ffff00`).

```bash
pyitol template create-gradient \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Value --color-min "#ff0000" --color-max "#0000ff" \
  --use-mid-color --color-mid "#ffff00" --output gradient.txt
```

### `pyitol template create-labels`

Rename / customize terminal labels.

**Specific options**: `--column`/`-c` (required, label column).

```bash
pyitol template create-labels \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column DisplayName --output labels.txt
```

### `pyitol template create-popup-info`

Popup info shown on hover (title + content).

**Specific options**: `--title-column` (default `title`), `--content-column` (default `content`).

```bash
pyitol template create-popup-info \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --title-column Species --content-column Description --output popup.txt
```

### `pyitol template create-binary`

Binary dataset; converts category columns to 0/1 fields.

**Specific options**: `--columns`/`-c` (required, comma-separated category columns), `--field-colors` (default `#ff0000,#00ff00,#0000ff`), `--field-shapes` (default `1,2,3`, values 1–6), `--color` (default `#ff0000`), `--show-internal` (default `1`).

```bash
pyitol template create-binary \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --columns Trait1,Trait2,Trait3 \
  --field-colors "#e41a1c,#377eb8,#4daf4a" --output binary.txt
```

### `pyitol template create-text`

Text labels next to each node.

**Specific options**: `--column`/`-c` (required), `--font-size` (default `12`), `--font-style` (default `normal`).

```bash
pyitol template create-text \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Note --font-size 14 --output text.txt
```

### `pyitol template create-external-shape`

External shape markers drawn outside the tree.

**Specific options**: `--column`/`-c` (required), `--shape-type` (default `circle`; `circle`/`square`/`star`/`triangle_right`/`triangle_left`/`checkmark`), `--colors`, `--size` (default `20`).

```bash
pyitol template create-external-shape \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Group --shape-type star --size 25 --output ext_shape.txt
```

### `pyitol template create-connections`

Connection lines. **Does not depend on tree or taxonomy**; reads a connections JSON file.

**Specific options**: `--connections`/`-c` (required, JSON file path, format `[[id1,id2],...]`), `--color` (default `#e64b35`), `--line-width` (default `2`), `--line-type` (default `solid`; `solid`/`dotted`/`dashed`), `--arrow-head-size` (default `1`).

```bash
# pairs.json: [["TaxonA","TaxonB"], ["TaxonC","TaxonD"]]
pyitol template create-connections \
  --connections pairs.json --color "#e64b35" --line-type dashed --output connections.txt
```

### `pyitol template create-domains`

Protein domains. **Does not depend on tree or taxonomy**; reads a JSON data file.

**Specific options**: `--data`/`-d` (required, JSON file path), `--color` (default `#ff00aa`), `--scale` (optional).

```bash
# domains.json: [{"id":"TaxonA","domains":[{"start":1,"end":50,"name":"PF001","color":"#ff0000"}]}]
pyitol template create-domains \
  --data domains.json --color "#ff00aa" --output domains.txt
```

---

## 2. Tree Structure

### `pyitol template create-tree-colors`

Tree colors; supports branch, label, branch-width, range, and gradient coloring.

**Specific options**: `--column`/`-c` (required), `--colors`, `--color-type` (default `clade`; `clade`/`label`/`branch`/`width`/`range`/`gradient`), `--width-value` (default `3`, only for `width` type).

```bash
# Color by branch
pyitol template create-tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --color-type branch --output tree_colors_branch.txt

# Color by numeric gradient
pyitol template create-tree-colors \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Score --color-type gradient --output tree_colors_grad.txt
```

### `pyitol template create-branch-gradient`

Branch gradient based on a numeric column.

**Specific options**: `--column`/`-c` (required), `--color-min` (default `#ff0000`), `--color-max` (default `#0000ff`), `--use-mid-color` (flag), `--color-mid` (default `#ffff00`).

```bash
pyitol template create-branch-gradient \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Distance --color-min "#fee090" --color-max "#4575b4" --output branch_grad.txt
```

### `pyitol template create-collapse`

Collapse clades. Two modes:
1. `--node-ids` directly specifies node IDs;
2. `--taxon` + `--rank` + `--taxonomy` + `--tree` finds a taxon by name (checks monophyly first).

Non-monophyletic groups are skipped by default; `--strict` aborts instead.

**Specific options**: `--node-ids`/`-n` (comma-separated), `--taxon`, `--rank`, `--taxonomy`/`-t`, `--tree`/`-r`, `--strict` (flag).

```bash
# Mode 1: by node IDs
pyitol template create-collapse \
  --node-ids "TaxonA,TaxonB" --output collapse_ids.txt

# Mode 2: by taxon name (checks monophyly first)
pyitol template create-collapse \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxon Cyanobacteriota --rank Phylum --strict --output collapse_taxon.txt
```

### `pyitol template create-prune`

Prune branches (remove specified nodes). **Does not depend on tree or taxonomy**.

**Specific options**: `--node-ids`/`-n` (required, comma-separated).

```bash
pyitol template create-prune \
  --node-ids "TaxonX,TaxonY,TaxonZ" --output prune.txt
```

### `pyitol template create-spacing`

Node spacing. **Does not depend on tree or taxonomy**; reads a CSV with `id` and `factor` columns.

**Specific options**: `--data`/`-d` (required, CSV file path).

```bash
# spacing.csv: id,factor
# TaxonA,2.0
# TaxonB,0.5
pyitol template create-spacing --data spacing.csv --output spacing.txt
```

### `pyitol template create-ranges`

Colored ranges; draws continuous background ranges grouped by a column.

**Specific options**: `--column`/`-c` (required), `--colors`.

```bash
pyitol template create-ranges \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Biome --colors '{"Marine":"#1f77b4","Soil":"#aec7e8"}' --output ranges.txt
```

### `pyitol template create-highlight`

Label background highlight.

**Specific options**: `--column`/`-c` (required), `--colors`.

```bash
pyitol template create-highlight \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Category --colors '{"Pathogenic":"#d62728"}' --output highlight.txt
```

### `pyitol template create-style`

Branch / label style (line style, font, background).

**Specific options**: `--column`/`-c` (required), `--style-type` (default `branch`; `branch`/`label`/`label_background`), `--colors`, `--line-style` (default `normal`; `normal`/`dashed`/`dotted`), `--font` (default `Arial`), `--size` (default `1`).

```bash
pyitol template create-style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Lineage --style-type branch --line-style dashed --output style.txt
```

### `pyitol template create-arrow`

Arrow annotations. **Does not depend on tree or taxonomy**; reads a CSV with `id`, `position`, `direction`, `color` columns.

**Specific options**: `--data-file`/`-d` (required, CSV file path), `--color` (default `#ff0000`), `--arrow-size` (default `30`).

```bash
# arrows.csv: id,position,direction,color
# TaxonA,0.5,right,#ff0000
pyitol template create-arrow --data-file arrows.csv --arrow-size 40 --output arrows.txt
```

---

## 3. Advanced

### `pyitol template create-linechart`

Line chart drawn beside the tree.

**Specific options**: `--column`/`-c` (required, numeric column), `--position-column`/`-p` (position column, defaults to row index), `--color` (default `#3c5484`), `--line-width` (default `2`).

```bash
pyitol template create-linechart \
  --taxonomy expr.csv --tree tree.nwk \
  --column Expression --position-column Time --output linechart.txt
```

### `pyitol template create-image`

Embed images beside nodes (file or URL).

**Specific options**: `--image-column`/`-i` (required, image filename column), `--url-column`/`-u` (image URL column, optional), `--image-width` (default `50`).

```bash
pyitol template create-image \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --image-column PhotoFile --url-column PhotoURL --image-width 60 --output images.txt
```

### `pyitol template create-alignment`

Sequence alignment display.

**Specific options**: `--alignment-column`/`-a` (required, alignment column), `--color-scheme` (default `nucleotide`; `nucleotide`/`amino_acid`).

```bash
pyitol template create-alignment \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --alignment-column AlignedSeq --color-scheme amino_acid --output alignment.txt
```

### `pyitol template create-tanglegram`

Tanglegram connecting corresponding nodes between two trees. **Does not depend on tree or taxonomy**.

**Specific options**: `--connections`/`-c` (required, format `id1,id2;id3,id4`), `--color` (default `#999999`), `--line-width` (default `1`).

```bash
pyitol template create-tanglegram \
  --connections "TaxonA,TaxonA2;TaxonB,TaxonB2" \
  --color "#999999" --output tanglegram.txt
```

### `pyitol template create-placement`

Phylogenetic placement. **Does not depend on tree or taxonomy**; reads a CSV with `id`, `position`, `count`, `color` columns.

**Specific options**: `--data-file`/`-d` (required, CSV file path), `--color` (default `#ff0000`), `--spacing` (default `5`).

```bash
# placement.csv: id,position,count,color
# Query1,0.8,12,#ff0000
pyitol template create-placement --data-file placement.csv --spacing 8 --output placement.txt
```

### `pyitol template create-timescale`

Timescale ticks on branches. **Does not depend on tree or taxonomy**; reads a CSV with `time_point`, `label`, `color` columns.

**Specific options**: `--data-file`/`-d` (required, CSV file path), `--color` (default `#000000`), `--scale-position` (default `bottom`; `top`/`bottom`/`both`).

```bash
# timescale.csv: time_point,label,color
# 0.5,Middle,#000000
pyitol template create-timescale --data-file timescale.csv --scale-position both --output timescale.txt
```

### `pyitol template create-meme`

MEME motifs. **Does not depend on tree or taxonomy**; reads a CSV with `id`, `start`, `end`, `name`, `color` columns.

**Specific options**: `--data-file`/`-d` (required, CSV file path), `--color` (default `#ff0000`), `--show-labels` (default `1`).

```bash
# meme.csv: id,start,end,name,color
# Seq1,10,30,Motif1,#ff0000
pyitol template create-meme --data-file meme.csv --show-labels 1 --output meme.txt
```

### `pyitol template create-manual`

Manual annotation with free-form custom data. **Does not depend on tree or taxonomy**; reads an arbitrary-column CSV.

**Specific options**: `--data-file`/`-d` (required, CSV file path), `--color` (default `#ff0000`), `--custom-header` (custom header JSON, e.g. `{"KEY":"VALUE"}`).

```bash
pyitol template create-manual \
  --data-file custom.csv --custom-header '{"FIELD_SHAPE":"1"}' --output manual.txt
```

### `pyitol template create-external-shape-bubble`

Multi-column bubble external shapes.

**Specific options**: `--columns`/`-c` (required, comma-separated numeric columns).

```bash
pyitol template create-external-shape-bubble \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Metric1,Metric2,Metric3 --output bubble.txt
```

---

## Related pages

- [CLI Reference](cli_en.md): command overview, the unified `template create` entry, global options, and exit codes.
- [Template Tutorial](tutorials/templates_en.md): selecting and combining 30+ template types.
- [API Guide](api_en.md): iTOL batch API and Python API usage.
