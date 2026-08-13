# Quick Start: From Installation to Figure

This tutorial walks you through your first use of PyiTOL in 10 minutes, producing a publication-grade phylogenetic tree figure.

## Prerequisites

- Python 3.9+
- iTOL API Key (obtained after registering at https://itol.embl.de/)

## Step 1: Installation

```bash
cd /path/to/PyiTOL
pip install -e .
```

Verify the installation:

```bash
pyitol --help
```

## Step 2: Prepare Data

Prepare two files:

**tree.nwk** — Phylogenetic tree (Newick format)
```
(A:0.1,B:0.2,(C:0.15,D:0.1):0.05);
```

**taxonomy.csv** — Taxonomic information for terminal nodes
```csv
id,Phylum,Genus,GC_content
A,Proteobacteria,Escherichia,52
B,Firmicutes,Bacillus,35
C,Proteobacteria,Pseudomonas,58
D,Actinobacteria,Streptomyces,72
```

## Step 3: View Taxonomic Ranks

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

Output:
```
可用分类等级:
  1. Phylum
  2. Genus
  3. GC_content
```

## Step 4: Monophyly Detection

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv
```

View the results:
```bash
cat monophyly.csv
```

## Step 5: Generate Templates

### Generate a Color Strip

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt
```

### Generate a GC Content Bar Chart

```bash
pyitol template create simple-bar \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column GC_content --output bars.txt
```

## Step 6: Upload to iTOL

```bash
# Save the API Key first
echo "YOUR_API_KEY" > .itolapi.key

# Upload
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --dataset-name MyFirstTree
```

## Step 7: Export the Figure

```bash
pyitol task export \
  --upload-id YOUR_TREE_ID \
  --download ./output --format svg
```

Or perform upload and export in a single step:

```bash
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --output result.svg --format svg --wait 60
```

## Step 8: Simplify Operations with a Configuration File

> **Tip**: The project root provides a `config.example.yaml` template containing all configurable options with comments. You can directly run `cp config.example.yaml my_config.yaml` and modify it for use.

`pyitol task run` executes batch tasks via a configuration file, where each configuration item specifies the operation type through the `command` field. Supported `command` values include: `upload`, `export`, `extract`, `monophyly`, `convert-binary`.

Create a single configuration file `workflow.yaml`:

```yaml
command: upload
tree: tree.nwk
configs: [colors.txt, bars.txt]
api_key: YOUR_API_KEY
name: MyFirstTree
```

```bash
pyitol task run --config workflow.yaml
```

To perform upload and export in a single step, you can create a batch list file `batch.yaml`:

```yaml
- command: upload
  tree: tree.nwk
  configs: [colors.txt, bars.txt]
  api_key: YOUR_API_KEY
  name: MyFirstTree
- command: export
  upload_id: TREE_ID_FROM_UPLOAD
  download: ./output
  parameters:
    format: svg
    dpi: 300
```

```bash
pyitol task run --config-list batch.yaml
```

For more configuration file examples, see the [API Usage Guide](../api.md#批量操作).

## Next Steps

- [Taxonomy Analysis Tutorial](taxonomy.md) — Dive deeper into monophyly detection and styling configuration
- [Template Generation Tutorial](templates.md) — Explore 31 iTOL v7 template types (plus `external-shape-bubble` variant)
