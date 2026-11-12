# Quick Start: From Installation to Figure

[中文](quickstart.md) | English

This tutorial walks you through your first use of PyiTOL in 10 minutes, producing a publication-grade phylogenetic tree figure.

## Prerequisites

- Python 3.10+
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

**taxonomy.csv** — Taxonomic information for the tips (leaves)
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

Output (PyiTOL's runtime console messages are Chinese by default, so the header line below is quoted verbatim; it reads "Available taxonomic ranks:"):
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
  --download ./output --parameter format=svg
```

> **Tip**: `pyitol task export` has no `--format` option; the export format must be passed via `--parameter format=svg`. To use `--format`/`--dpi`/`--width`/`--height` directly, use `task upload-and-export` below instead.

Or perform upload and export in a single step:

```bash
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --output result.png --format png --dpi 300 --wait 60
```

## Step 8: Simplify Operations with a Configuration File

> **Tip**: The project root provides a `config.example.yaml` template containing all configurable options with comments. You can directly run `cp config.example.yaml my_config.yaml` and modify it for use.

`pyitol task run` executes batch tasks via a configuration file, where each configuration item specifies the operation type through the `command` field. Supported `command` values include: `upload`, `export`, `extract`, `monophyly`, `convert-binary`, `convert-connect`, `template`.

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

To chain upload and export as two entries executed in order within one batch manifest (for a true single step, use the `task upload-and-export` command shown above), create a batch list file `batch.yaml`:

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

For more configuration file examples, see the [API Usage Guide](../api_en.md#batch-operations).

## Next Steps

- [Taxonomy Analysis Tutorial](taxonomy_en.md) — Dive deeper into monophyly detection and styling configuration
- [Template Generation Tutorial](templates_en.md) — Explore the 33 template types supported by the unified entry point (plus the `external-shape-bubble` variant)
