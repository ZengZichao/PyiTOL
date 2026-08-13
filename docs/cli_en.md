# PyiTOL CLI Complete Reference

## Global Parameters

All subcommands share the following global parameters:

| Parameter | Shortcut | Default | Description |
|------|------|--------|------|
| `--version` | | | Show version number, Git hash, dependency library versions, and license |
| `--verbose` | | `False` | Show verbose logs (DEBUG level) |
| `--quiet` | `-q` | `False` | Show only key information (WARNING level) |
| `--config` | `-c` | | YAML/JSON configuration file path |
| `--log-file` | | | Log file path (also output to file) |
| `--low-memory` | | `False` | Low memory mode (suitable for large datasets) |

## Command Overview

```
pyitol [global parameters] <main command> <subcommand> [parameters]
```

---

## self-test - Self-Test Mode

### `pyitol self-test`

Runs a self-test: verifies dependency libraries, example parsing, and monophyly determination logic.

```bash
pyitol self-test
```

Outputs a `[PASS]/[FAIL]` table that verifies:
- Third-party dependency libraries can be imported and their versions
- Internal modules can be imported
- Newick tree parsing
- Embedded taxonomy extraction
- Monophyletic group determination logic
- Malicious character detection

Exit code: 0=all passed, 1=some failed

---

## validate - Input Validation

### `pyitol validate`

Validates input file format, color codes, and node ID consistency. Supports deep validation and adversarial protection.

```bash
# Basic validation
pyitol validate --tree tree.nwk --taxonomy taxonomy.csv

# Deep validation (with sequence file)
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta --alphabet DNA
```

| Parameter | Shortcut | Description |
|------|------|------|
| `--tree` | `-t` | Tree file path |
| `--taxonomy` | | Taxonomy table file path |
| `--sequence` | `-s` | Sequence file path |
| `--alphabet` | | Expected alphabet: `auto`/`DNA`/`RNA`/`protein`/`any` |
| `--template` | | Template file path (can be specified multiple times) |
| `--color` | | Color code (can be specified multiple times) |

**Deep validation contents**:
- Tree file: bracket balance, negative branch lengths (CRITICAL), empty node names (ERROR), duplicate tip names (ERROR), multiple root nodes (CRITICAL)
- Sequence file: alphabet detection (DNA/RNA/protein), ID uniqueness, length consistency
- Adversarial protection: malicious characters (control characters/bidirectional text), circular dependencies, empty files

---

## config - Configuration File Management

### `pyitol config init`

Generates a default configuration file template.

```bash
pyitol config init --output pyitol_config.yaml
```

| Parameter | Default | Description |
|------|--------|------|
| `--output` / `-o` | `pyitol_config.yaml` | Output configuration file path |
| `--api-key-file` | `.itolapi.key` | API key file path |
| `--default-format` | `svg` | Default export format |

---

## template - Template Management

### `pyitol template create <type>` ⭐ Unified Entry

Creates an iTOL v7 template file based on the type. This is the **recommended unified entry** for template generation.

```bash
# Example: generate a taxonomy color strip
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt

# Example: generate a heatmap
pyitol template create heatmap \
  --taxonomy expr.csv --tree tree.nwk \
  --columns Sample1,Sample2,Sample3 --output heatmap.txt

# Example: conditional collapse of a monophyletic group
pyitol template create collapse \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon Cyanobacteriota --rank Phylum \
  --strict -o collapse.txt
```

**Supported template types**:

| Type | Description | Required Parameters |
|------|------|---------|
| `color-strip` | Color strip | `--taxonomy`, `--tree`, `--column` |
| `branch` | Branch coloring | `--taxonomy`, `--tree`, `--column` |
| `simple-bar` | Single-value bar chart | `--taxonomy`, `--tree`, `--column` |
| `multi-bar` | Multi-value bar chart | `--taxonomy`, `--tree`, `--columns` |
| `heatmap` | Heatmap | `--taxonomy`, `--tree`, `--columns` |
| `symbols` | Symbol markers | `--taxonomy`, `--tree`, `--column` |
| `pie` | Pie chart | `--taxonomy`, `--tree`, `--columns` |
| `boxplot` | Boxplot | `--taxonomy`, `--tree` |
| `gradient` | Color gradient | `--taxonomy`, `--tree`, `--column` |
| `connections` | Connection lines | `--connections` |
| `labels` | Label renaming | `--taxonomy`, `--tree`, `--column` |
| `popup-info` | Hover information | `--taxonomy`, `--tree` |
| `domains` | Protein domains | `--data-file` |
| `binary` | Binary data | `--taxonomy`, `--tree`, `--columns` |
| `text` | Text labels | `--taxonomy`, `--tree`, `--column` |
| `external-shape` | External shapes | `--taxonomy`, `--tree`, `--column` |
| `tree-colors` | Tree coloring | `--taxonomy`, `--tree`, `--column` |
| `branch-gradient` | Branch gradient | `--taxonomy`, `--tree`, `--column` |
| `collapse` | Collapse clades | `--node-ids` or `--taxon` |
| `prune` | Prune branches | `--node-ids` |
| `spacing` | Node spacing | `--data-file` |
| `ranges` | Colored ranges | `--taxonomy`, `--tree`, `--column` |
| `highlight` | Label highlighting | `--taxonomy`, `--tree`, `--column` |
| `style` | Branch/label style | `--taxonomy`, `--tree`, `--column` |
| `arrow` | Arrow annotations | `--data-file` |
| `linechart` | Line chart | `--taxonomy`, `--tree`, `--column` |
| `image` | Image embedding | `--taxonomy`, `--tree` |
| `alignment` | Sequence alignment | `--taxonomy`, `--tree` |
| `tanglegram` | Tanglegram | `--connections` |
| `placement` | Phylogenetic placement | `--data-file` |
| `timescale` | Timescale | `--data-file` |
| `meme` | MEME motifs | `--data-file` |
| `manual` | Manual annotations | `--data-file` |

> **Note**: The unified entry `template create` supports 31 types. Additionally, `external-shape-bubble` (bubble external shape, a variant of `external-shape`) must be created via the dedicated subcommand `pyitol template create-external-shape-bubble` and is not covered by the unified entry. There are also 31 dedicated `create-*` subcommands available (`pyitol template create-color-strip`, etc.), which are functionally equivalent to the unified entry.

**Common parameters**:

| Parameter | Shortcut | Default | Description |
|------|------|--------|------|
| `--output` / `-o` | | `config_template.txt` | Output template file path |
| `--taxonomy` / `-t` | | | Taxonomy table file path |
| `--tree` / `-r` | | | Tree file path |
| `--column` / `-c` | | | Data column name |
| `--columns` | | | Multiple data column names, comma-separated |
| `--colors` | | | Custom color mapping JSON |
| `--label` / `-l` | | `dataset` | Dataset label |
| `--id-column` | | `id` | ID column name |
| `--separator` / `-s` | | `TAB` | Data separator |
| `--palette` | | | Color palette preset |
| `--data-file` / `-d` | | | Data file path |
| `--force` / `-f` | | `False` | Overwrite existing output file |
| `--no-clobber` | | `False` | Skip existing output file |

**collapse-specific parameters**:

| Parameter | Description |
|------|------|
| `--node-ids` / `-n` | Node IDs to collapse, comma-separated |
| `--taxon` | Taxon name to collapse (requires `--taxonomy` and `--tree`) |
| `--rank` | Taxonomic rank (e.g., Phylum, Class) |
| `--strict` | Strict mode: abort if not monophyletic (skips by default) |

### `pyitol template bundle`

One-click bundled generation of multiple visualization template files.

```bash
pyitol template bundle \
  --output-dir ./templates \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --config '[{"type":"color-strip","column":"Phylum"},{"type":"heatmap","columns":["A","B","C"]}]'
```

### `pyitol template validate`

Validates iTOL template file format.

```bash
pyitol template validate --template colors.txt
```

PyiTOL also provides 34 dedicated subcommands `pyitol template create-*` (e.g. `create-color-strip`, `create-symbols`, `create-pie`), each accepting only its type-specific parameters — better suited for precise scripting and pipelines. Full options and examples are in [Template Subcommand Reference](templates-reference_en.md).

---

## taxonomy - Taxonomy Analysis

### `pyitol taxonomy ranks`

Displays the list of taxonomic ranks.

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

### `pyitol taxonomy extract`

Extracts information for a specified taxonomic rank.

```bash
pyitol taxonomy extract --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output extract.txt
```

### `pyitol taxonomy extract-stats`

Extracts taxonomy statistics (member count, LCA node, etc.).

```bash
pyitol taxonomy extract-stats --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output stats.csv
```

### `pyitol taxonomy extract-from-names`

Automatically extracts taxonomic information from tree tip names.

```bash
# GTDB format
pyitol taxonomy extract-from-names --tree tree.nwk --format gtdb -o taxonomy.csv

# Embedded format
pyitol taxonomy extract-from-names --tree tree.nwk --format embedded -o taxonomy.csv

# Auto-detection
pyitol taxonomy extract-from-names --tree tree.nwk --format auto -o taxonomy.csv

# Custom taxonomy levels
pyitol taxonomy extract-from-names --tree tree.nwk \
  --taxonomy-levels "d:Domain,p:Phylum,c:Class,o:Order,f:Family,g:Genus,s:Species" \
  -o taxonomy.csv
```

| Parameter | Default | Description |
|------|--------|------|
| `--tree` / `-r` | | Tree file path |
| `--output` / `-o` | `taxonomy_from_names.csv` | Output taxonomy table path |
| `--format` / `-f` | `auto` | Naming format: `auto`/`gtdb`/`embedded`/`ncbi` |
| `--delimiter` / `-d` | `_` | Name delimiter |
| `--taxonomy-levels` | | Custom taxonomy level prefixes |
| `--taxonomy-delimiter-mode` | Embedded format parsing strategy | `segment` (default) / `reverse` / `greedy` |

**Supported formats**:
- **GTDB (Format B)**: `d__Bacteria;p__Proteobacteria;c__Gammaproteobacteria;...`
- **Embedded (Format A)**: `GB_GCA_0001_d_Bacteria_p_Proteo_c_Gamma_o_Enter_f_Enter_g_Escherichia`
- **NCBI**: `Genus_species`

### `pyitol taxonomy monophyly`

Checks the monophyly (monophyletic/paraphyletic/polyphyletic) of a specified taxonomic group.

```bash
# Detect by taxonomic rank
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk --rank Phylum --output mono.csv

# Detect by specified taxa
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "Proteobacteria,Firmicutes" --output mono.csv

# Use special identifiers
pyitol taxonomy monophyly --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "LUCA,LACA,LBCA,ROOT" --output mono.csv
```

| Parameter | Description |
|------|------|
| `--taxonomy` / `-t` | Taxonomy table file path |
| `--tree` / `-r` | Tree file path |
| `--rank` | Taxonomic rank name |
| `--taxa` | Specified taxon names, comma-separated (supports LUCA/LACA/LBCA/ROOT) |
| `--taxa-file` | File containing taxon names (one per line) |
| `--output` / `-o` | Output file path |
| `--id-column` | ID column name |
| `--multi-tree-mode` / `-m` | Multi-tree processing strategy: `ask`/`first`/`last`/`random`/`split` |

**Special identifiers**:
- `LUCA`: MRCA of all bacteria and archaea
- `LACA`: MRCA of all archaea
- `LBCA`: MRCA of all bacteria
- `ROOT`: Root of the entire tree (all tip nodes)

### `pyitol taxonomy check-and-style`

Checks whether a specified taxon is monophyletic; if so, generates a styling template, otherwise issues a warning.

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon Escherichia --rank Genus \
  --action color-branch --color "#e41a1c" \
  --output clade.txt

# Use special identifiers
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy tax.csv \
  --taxon LUCA --rank Domain \
  --action color-branch --output luca.txt
```

| Parameter | Description |
|------|------|
| `--tree` / `-r` | Tree file path |
| `--taxonomy` / `-t` | Taxonomy table file path (optional) |
| `--taxon` | Taxon name to check (supports LUCA/LACA/LBCA/ROOT) |
| `--rank` | Taxonomic rank (default Genus) |
| `--action` / `-a` | Style action: `color-branch`/`highlight`/`color-strip` |
| `--color` | Specified color (HEX) |
| `--output` / `-o` | Output template file path |
| `--name-format` | Naming format: `auto`/`gtdb`/`embedded`/`ncbi` |
| `--palette` | Color palette preset |
| `--domain-column` | Domain column name (used for LUCA/LACA/LBCA resolution) |
| `--multi-tree-mode` / `-m` | Multi-tree processing strategy |
| `--taxonomy-source-priority` | Mixed-source priority | `table` (default) / `embedded` |

### `pyitol taxonomy style`

Generates an iTOL template configuration file based on taxonomy information and a specified style action.

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output style.txt
```

**Supported style actions** (`--action`):
- `color-branch` / `color-label` / `color-range` / `color-strip`
- `style-branch` / `style-label`
- `width` / `highlight` / `symbol` / `range` / `gradient`

### `pyitol taxonomy convert-binary`

Converts taxonomy data into a 0/1 binary matrix.

```bash
pyitol taxonomy convert-binary --input data.csv --columns col1,col2 --output binary.csv
```

### `pyitol taxonomy convert-connect`

Converts a 0/1 matrix into a long-format table of connection pairs.

```bash
pyitol taxonomy convert-connect --input binary.csv --output connections.csv
```

---

## task - API Task Management

### `pyitol task upload`

Uploads trees and templates to iTOL.

```bash
pyitol task upload --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --api-key YOUR_KEY --dataset-name MyTree
```

### `pyitol task export`

Exports iTOL visualization images.

```bash
pyitol task export --upload-id TREE_ID --download ./output --format svg
```

### `pyitol task upload-and-export`

Uploads and exports an image (in one step).

```bash
pyitol task upload-and-export \
  --tree tree.nwk --config colors.txt \
  --output output.svg --format svg --wait 60
```

Supports `--parameter` for passing iTOL export parameters (e.g., `datasets_visible`, `display_mode`, `background`), consistent with `task export`:

```bash
pyitol task upload-and-export \
  --tree tree.nwk --config colors.txt \
  --output output.png --format png --dpi 300 --wait 60 \
  --parameter datasets_visible=0,1 \
  --parameter display_mode=2 \
  --parameter background=ffffff
```

Common `--parameter` values: `datasets_visible`, `display_mode` (0=rectangular/1=circular/2=unrooted circular/3=unrooted rectangular), `background`, `ignore_branch_length`, `line_width`, `current_font_size`, `margin`, `arc`.

### `pyitol task delete`

Deletes uploaded trees.

```bash
pyitol task delete --upload-id ID1 --upload-id ID2 --api-key YOUR_KEY
```

### `pyitol task status`

Queries the status of an uploaded tree.

```bash
pyitol task status --upload-id TREE_ID --api-key YOUR_KEY
```

### `pyitol task run`

Runs a configuration file (single config or batch list).

```bash
pyitol task run --config workflow.yaml
pyitol task run --config-list batch.yaml
```

---

## tree - Tree File Operations

### `pyitol tree info`

Displays basic tree file information.

```bash
pyitol tree info --tree tree.nwk
```

### `pyitol tree format-support-values`

Formats support value display (supports IQ-TREE, RAxML, ALRT and other formats).

```bash
pyitol tree format-support-values --tree tree.nwk --output formatted.nwk
```

---

## utils - Utilities

### `pyitol utils tree-info`

Displays basic tree file information.

```bash
pyitol utils tree-info --tree tree.nwk
```

### `pyitol utils search-tree-file`

Automatically searches for a phylogenetic tree file in a directory.

```bash
pyitol utils search-tree-file --dir ./data/
```

### `pyitol utils taxonomy-parse`

Parses and previews the structure and content of a taxonomy table.

```bash
pyitol utils taxonomy-parse --taxonomy tax.csv
```

### `pyitol utils learn-template`

Reverse-learns configuration from an existing iTOL template file.

```bash
pyitol utils learn-template --template colors.txt --output learned.json
```

### `pyitol utils wide-to-long` / `long-to-wide`

Format conversion.

```bash
pyitol utils wide-to-long --data wide.csv --id-column id -o long.csv
pyitol utils long-to-wide --data long.csv --id-column id -o wide.csv
```

### `pyitol utils count-to-tree`

Builds a phylogenetic tree based on count-value distances.

```bash
pyitol utils count-to-tree --data counts.csv --output tree.nwk --method upgma
```

### `pyitol utils df-tree` ⭐

Builds a Newick-format phylogenetic tree directly from a data frame.

```bash
pyitol utils df-tree --data data.csv --columns A,B,C --output tree.nwk --main col
```

### `pyitol utils group-columns`

Aggregates data by specified columns. Supports regex matching for column-name grouping and multi-attribute mapping grouping.

```bash
pyitol utils group-columns --data data.csv --columns "col1,col2,col3" -o grouped.csv
```

### `pyitol utils binary`

Converts taxonomy data into a binary matrix.

```bash
pyitol utils binary --taxonomy data.csv --columns col1,col2 -o binary.csv
```

### `pyitol utils connections`

Generates connection pairs (based on co-occurrence weights).

```bash
pyitol utils connections --taxonomy binary.csv --columns col1,col2 -o connections.csv
```

### `pyitol utils preview`

Previews the data distribution of a specific column in the taxonomy table.

```bash
pyitol utils preview --taxonomy tax.csv --tree tree.nwk --column Phylum
```

---

## learn - Template Reverse Learning

### `pyitol learn template`

Reverse-learns configuration from template files.

```bash
pyitol learn template --template t1.txt --template t2.txt --output learned.json
```

### `pyitol learn palette`

Views available color palette presets.

```bash
pyitol learn palette --preset-name nature
```

### `pyitol learn train-theme` ⭐

Batch-learns themes from a template directory and generates recommended default parameters.

```bash
pyitol learn train-theme --dir ./templates --output theme.json --min-freq 0.5
```

---

## replay - Action Replay

### `pyitol replay`

Replays a previous operation record.

```bash
pyitol replay --session ~/.pyitol/session_logs/pyitol_20240115_120000.yaml
```

---

## Configuration File Format

PyiTOL supports passing a YAML/JSON configuration file via `--config` to override global parameters. Parameter priority: **command line > configuration file > default values**.

`--config` is used to override CLI default parameters (such as `tree`, `taxonomy`, `api_key`, etc.).

`pyitol task run` uses an independent task configuration file format, with each item specifying the operation via the `command` field, supporting `upload`/`export`/`extract`/`monophyly`/`convert-binary`, etc. See [API Usage Guide](api.md#batch-operations) for details.

Task configuration file example `batch.yaml` (list format):

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

## Exit Codes

| Exit Code | Meaning | Description |
|--------|------|------|
| 0 | Success | Operation completed normally |
| 1 | Runtime Error | Internal error, dependency issue, API failure |
| 2 | Parameter Error | Invalid CLI parameters, validation failure |
| 3 | Data Error | Input file format/content error |
| 130 | User Interrupt | Received SIGINT (Ctrl+C) |
