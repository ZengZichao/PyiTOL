# Taxonomy Analysis Tutorial

PyiTOL provides a complete taxonomy analysis toolchain: rank identification, information extraction, monophyly detection, and automated styling.

## 1. Taxonomic Rank Identification

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

Automatically identifies standard taxonomic ranks (domain, phylum, class, order, family, genus, species) as well as custom columns.

## 2. Taxonomic Information Extraction

### Basic Extraction

```bash
pyitol taxonomy extract \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_tips.txt
```

Output format: one terminal node per line, including ID and taxonomic name.

### Statistical Extraction (with LCA and member count)

```bash
pyitol taxonomy extract-stats \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output phylum_stats.csv
```

Output columns: rank, group, member_count, lca_node, members

### Extract from Tree Tip Names

Extract taxonomic information automatically directly from tree tip (leaf node) names, without preparing a taxonomy table in advance:

```bash
pyitol taxonomy extract-from-names \
  --tree tree.nwk --format auto \
  --output taxonomy_from_names.csv
```

Supports six naming formats (specified via `--format`):

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
| `strict` | Strict mode (default), decides according to standard binary tree classification rules |
| `relaxed` | Relaxed mode; if members occupy only some of the child branches of the polytomy, the group is judged paraphyletic rather than polyphyletic |
| `data-insufficient` | Data-insufficient mode; the above case is judged as `data_insufficient`, indicating the topology is unresolved and no conclusion can be reached |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --polytomy-mode relaxed \
  --output monophyly.csv
```

### Multiple Tree Handling

When the tree file contains multiple trees, specify the processing strategy via `--multi-tree-mode`:

| Strategy | Description |
|------|------|
| `ask` | Default; prompts the user to choose (automatically falls back to `first` in non-interactive environments) |
| `first` | Use only the first tree |
| `last` | Use only the last tree |
| `random` | Randomly select one tree |
| `split` | Process all trees separately; result files get a numeric suffix |
| `all` | Same as `split`; returns results for all trees processed separately |

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree trees.nexus \
  --rank Phylum --multi-tree-mode split \
  --output monophyly.csv
```

## 4. Monophyly Decision Principle

PyiTOL performs the following algorithm for each group of terminal nodes:

1. **Find LCA**: Compute the most recent common ancestor of all members of the taxon
2. **Compute differences**:
   - `E = LCA descendants \ taxon members` (intruding nodes)
   - `M = taxon members \ LCA descendants` (missing nodes)
3. **Decision**:
   - `E=∅` and `M=∅` → **monophyletic**
   - `M=∅` and `E≠∅` → **paraphyletic**
   - `M≠∅` → **polyphyletic**
   - `--polytomy-mode=data-insufficient`, the LCA is a polytomy, members occupy only some child branches, and intruding nodes are present → **data_insufficient**

The fourth state, `data_insufficient`, occurs only under `--polytomy-mode data-insufficient`: when the LCA is a polytomy (an unresolved multifurcation) and the taxon members are spread across some but not all child branches, accompanied by intruding nodes, the topology is insufficiently resolved to make a reliable monophyletic/paraphyletic/polyphyletic decision. In this case the `data_insufficient` status is emitted to remind the user to supplement data or switch to the `relaxed`/`strict` mode.

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

### Add Symbol Markers for High-Rank Taxa

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
| `width` | TREE_COLORS (width) | Branch width |
| `highlight` | DATASET_STYLE | Label background highlight |
| `symbol` | DATASET_SYMBOLS | Symbol markers |
| `range` | DATASET_RANGE | Colored range |
| `gradient` | DATASET_GRADIENT | Gradient strip |

### Check and Style (One Step)

The `check-and-style` command merges monophyly checking and styling template generation into a single step: it first checks whether the specified taxon is monophyletic; if so, it generates a styling template, otherwise it emits a warning and skips.

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

`--taxon` supports four special identifiers for locating key ancestor nodes at the root of the tree of life (`--taxonomy` and `--domain-column` are required):

| Identifier | Meaning |
|--------|------|
| `LUCA` | Most recent common ancestor of all archaea and bacteria |
| `LACA` | Most recent common ancestor of all archaea |
| `LBCA` | Most recent common ancestor of all bacteria |
| `ROOT` | Root of the whole tree; returns all terminal nodes in the tree without specifying a domain |

```bash
pyitol taxonomy check-and-style \
  --tree tree.nwk --taxonomy taxonomy.csv \
  --taxon "LBCA" --action highlight \
  --domain-column Domain --output lbca.txt
```

## 6. Binary Data Conversion

Convert categorical data into a 0/1 matrix:

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
