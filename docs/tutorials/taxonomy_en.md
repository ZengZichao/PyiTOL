# Taxonomy Analysis Tutorial

[中文](taxonomy.md) | English

PyiTOL provides a complete taxonomy analysis toolchain: rank identification, information extraction, monophyly detection, and automated styling.

## 1. Taxonomic Rank Identification

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

`taxonomy ranks` lists every column of the taxonomy table except the ID column (`--id-column`, default `id`): standard ranks (domain, phylum, class, order, family, genus, species, etc.) and custom columns are reported the same way, with no recognition step and no reordering.

## 2. Taxonomic Information Extraction

### Basic Extraction

```bash
pyitol taxonomy extract \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_tips.txt
```

Output format: one tip (leaf) per line, including ID and taxonomic name.

### Statistical Extraction (with LCA and member count)

```bash
pyitol taxonomy extract-stats \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_stats.csv
```

Output columns: rank, group, member_count, lca_node, members

### Extract from Tree Tip Names

Extract taxonomic information automatically directly from tree tip (leaf) names, without preparing a taxonomy table in advance:

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format auto \
  --output taxonomy_from_names.csv
```

The `--format` help text lists only 4 values (`auto`/`gtdb`/`embedded`/`ncbi`), while the implementation additionally supports `underscore` and `mixed`, giving six naming formats in total:

| Format | Description | Example |
|------|------|------|
| `auto` | Auto-detect (default) | — |
| `gtdb` | GTDB format (`X__` prefix, semicolon-separated) | `d__Bacteria;p__Proteobacteria;...;s__Species` |
| `embedded` | Embedded format (`_X_` markers) | `accession_d_Bacteria_p_Proteo_c_..._g_Genus` |
| `ncbi` | NCBI format (genus and species separated by underscore) | `Escherichia_coli` |
| `underscore` | Underscore-separated multiple ranks | `Family_Genus_species` |
| `mixed` | Mixed format (GTDB + embedded) | A mix of the two above |

You can customize the taxonomic level prefix mapping via `--taxonomy-levels` (e.g., `d:Domain,p:Phylum,...`) and specify the name delimiter via `--delimiter` (default is underscore).

Use `--taxonomy-delimiter-mode` to control how taxonomic markers are parsed in the embedded format (`embedded`), resolving parsing ambiguity when taxon names themselves contain underscores:

| Mode | Description |
|------|------|
| `segment` | Forward matching (default), parsing segment by segment according to markers |
| `reverse` | Strict reverse order, verifying g→f→o→c→p→d from right to left; emits a WARNING and falls back to `greedy` on mismatch |
| `greedy` | Captures the entire segment starting from the first `d_` marker as taxonomic information |

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format embedded \
  --taxonomy-delimiter-mode reverse \
  --output taxonomy_from_names.csv
```

## 3. Monophyly Detection

### Batch Detection by Taxonomic Rank

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv
```

### Detection by Specified Taxa

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa "Proteobacteria,Firmicutes,Actinobacteria" \
  --output monophyly.csv
```

### Read Taxa List from a File

```bash
echo -e "Proteobacteria\nFirmicutes" > taxa_list.txt
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxa-file taxa_list.txt --output monophyly.csv
```

### Polytomy Handling

Use `--polytomy-mode` to control the decision behavior when the LCA is a polytomy (multifurcation):

| Mode | Description |
|------|------|
| `strict` | Strict mode (default), deciding by the standard binary-tree classification rules; but when the LCA is a polytomy, members occupy only some child branches and intruding nodes exist, it likewise returns `data_insufficient` |
| `relaxed` | Relaxed mode; if members occupy only some of the child branches of the polytomy, the group is judged paraphyletic rather than polyphyletic |
| `data-insufficient` | Data-insufficient mode; the above case is judged as `data_insufficient`, indicating the topology is unresolved and no conclusion can be reached |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --polytomy-mode relaxed \
  --output monophyly.csv
```

### Multiple Tree Handling

`--multi-tree-mode` (the help text lists `ask`/`first`/`last`/`split`, default `ask`) is only accepted on `taxonomy monophyly` and `taxonomy check-and-style`: `monophyly` parses the value (and lets a configuration file override it), while `check-and-style` does not even read it; neither passes it on to the tree-loading code of monophyly detection (the source comment marks the parameter as reserved for future use). Those two commands load the tree with a plain `dendropy.Tree.get_from_path` call, so nothing is prompted and nothing is split — any value currently has no effect.

The semantics of the strategies themselves are as follows (implemented by `pyitol/core/parser.py::load_tree`):

| Strategy | Description |
|------|------|
| `ask` | Default; prompts the user to choose (automatically falls back to `first` in non-interactive environments) |
| `first` | Use only the first tree |
| `last` | Use only the last tree |
| `split` | Return all trees as a list so the caller can process them one by one |
| `all` | Internal alias equivalent to `split`: returns all trees for separate processing (not listed in the help text) |

Only code paths that load trees through `pyitol/core/parser.py::load_tree` actually apply the strategies above; those paths are currently invoked internally with hard-coded values (`validate` uses `first` and `all`), and the command line does not forward this option yet. The command below therefore behaves identically whether or not `--multi-tree-mode` is passed:

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree trees.nexus \
  --rank Phylum \
  --output monophyly.csv
```

## 4. Monophyly Decision Principle

PyiTOL performs the following algorithm for each group of tips (leaves):

1. **Find LCA**: Compute the most recent common ancestor of all members of the taxon
2. **Compute differences**:
   - `E = LCA descendants \ taxon members` (intruding nodes)
   - `M = taxon members \ LCA descendants` (missing nodes)
3. **Decision**:
   - `E=∅` and `M=∅` → **monophyletic**
   - `M≠∅` (some members are absent from the tree) → **incomplete_sampling**
   - `M=∅` and `E≠∅` → **paraphyletic** or **polyphyletic** according to topology; if every intruding node maps to the same group the group is still judged monophyletic, and if none of them can be mapped it is judged `data_insufficient`
   - The LCA is a polytomy, members occupy only some child branches and `E≠∅` → the default `strict` mode and `data-insufficient` mode both return **data_insufficient**, while `relaxed` returns paraphyletic

`data_insufficient` has two origins: the polytomy case above (returned by both the default `strict` mode and `data-insufficient` mode; only `relaxed` does not return it), and the non-polytomy case where every intruding node is absent from the taxonomy mapping so its affiliation cannot be decided. In either case the `data_insufficient` status is emitted to prompt the user to complete the taxonomy table, or — in the polytomy case — to switch to `relaxed` mode.

Polyphyletic groups are further decomposed into subgroups, outputting the LCA and members of each subgroup.

## 5. Styling Configuration Generation

Automatically generates iTOL templates based on monophyly detection results:

### Generate Color Strips for Different Phyla

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output phylum_colors.txt
```

### Color Branches for a Specific Taxon

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --taxon "Proteobacteria" --action color-branch \
  --color "#e64b35" --output highlight.txt
```

### Add Symbol Markers for Genus-Level Taxa

```bash
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Genus --action symbol --output genus_symbols.txt
```

### Supported Styling Actions

| Action | Template Generated | Effect |
|------|---------|------|
| `color-branch` | TREE_COLORS (clade) | Branch coloring |
| `color-label` | TREE_COLORS (label) | Label coloring |
| `color-range` | TREE_COLORS (range) | Range coloring |
| `color-strip` | DATASET_COLORSTRIP | Color strip |
| `style-branch` | DATASET_STYLE | Branch line style |
| `style-label` | DATASET_STYLE | Label style |
| `width` | DATASET_STYLE | Branch width |
| `highlight` | DATASET_STYLE | Label background highlight |
| `symbol` | DATASET_SYMBOL | Symbol markers |
| `range` | DATASET_RANGE | Colored range |
| `gradient` | DATASET_GRADIENT | Gradient strip |

### Check and Style (One Step)

The `check-and-style` command merges monophyly checking and styling template generation into a single step: it first checks whether the specified taxon is monophyletic; if so, it generates a styling template, otherwise it emits a warning or error and exits with status 1, writing no template file.

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "Escherichia" --rank Genus \
  --action color-branch --output escherichia.txt
```

Supported styling types (`--action`):

| Action | Effect |
|------|------|
| `color-branch` | Branch coloring (default) |
| `highlight` | Label background highlight |
| `color-strip` | Color strip |

Use `--taxonomy-source-priority` to control the merge priority when both an external taxonomy table and tree-name-embedded taxonomic information are provided:

| Value | Description |
|------|------|
| `table` | Table takes priority (default); the taxonomy table specified by `--taxonomy` prevails |
| `embedded` | Tree-name-embedded information takes priority; taxonomic information extracted from tree names fills missing fields in the table, and on conflict the tree name prevails with a WARNING logged |

When `--taxonomy` is not provided, taxonomic information can be automatically extracted from tree tip names (use `--name-format` to specify the format).

#### Special Identifiers

`--taxon` supports four special identifiers for locating key ancestor nodes at the root of the tree of life. Any of them requires `--taxonomy`; `--domain-column` is optional and defaults to the column name `Domain` (a column whose name differs only in case is matched automatically), but `LUCA`/`LACA`/`LBCA` require the taxonomy table to actually contain a domain column, otherwise a `MetadataParseError` is raised:

| Identifier | Meaning |
|--------|------|
| `LUCA` | Most recent common ancestor of all archaea and bacteria |
| `LACA` | Most recent common ancestor of all archaea |
| `LBCA` | Most recent common ancestor of all bacteria |
| `ROOT` | Root of the whole tree; returns the IDs in the taxonomy table that intersect the tree tip (leaf) labels, without using a domain column |

The `--taxa`/`--taxa-file` options of `taxonomy monophyly` accept the same set of identifiers (`LUCA`/`LACA`/`LBCA`/`ROOT`, although its help text lists only the first three), but that command has no `--domain-column` option and looks the domain column up under the fixed name `Domain`.

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "LBCA" --action highlight \
  --domain-column Domain --output lbca.txt
```

## 6. Binary Data Conversion

Convert the presence/absence data of the columns given by `--columns` (e.g., gene presence/absence) into a 0/1 matrix:

```bash
pyitol taxonomy convert-binary \
  --input data.csv --columns "GeneA,GeneB,GeneC" \
  --output binary_matrix.csv
```

## 7. Connection Pair Conversion

Convert a 0/1 matrix into connection pairs (for the Connections template):

```bash
pyitol taxonomy convert-connect \
  --input binary_matrix.csv --output connections.csv \
  --min-weight 0.5
```

## 8. Complete Workflow Example

```bash
# 1. Detect monophyly
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv

# 2. Generate styling templates
pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action color-strip --output colors.txt

pyitol taxonomy style \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --action highlight --output highlights.txt

# 3. Upload and export
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt --config highlights.txt \
  --output result.svg --format svg
```
