# PyiTOL

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/pyitol.svg)](https://pypi.org/project/pyitol)
[![CI](https://github.com/ZengZichao/PyiTOL/actions/workflows/ci.yml/badge.svg)](https://github.com/ZengZichao/PyiTOL/actions/workflows/ci.yml)
[![Docs](https://github.com/ZengZichao/PyiTOL/actions/workflows/docs.yml/badge.svg)](https://zengzichao.github.io/PyiTOL/)
[![ORCID](https://img.shields.io/badge/ORCID-0000--0001--6553--970X-a6ce39?logo=orcid&logoColor=white)](https://orcid.org/0000-0001-6553-970X)

English | [中文](README_CN.md)

**PyiTOL** is a Python CLI tool for automating phylogenetic tree visualization on the **iTOL (Interactive Tree Of Life)** platform.

## Features

### Core Features

- **33 iTOL template types** via the unified entry `pyitol template create <type>` (plus `external-shape-bubble`, a variant of `external-shape`, for 34 dedicated subcommands in total): color strips, heatmaps, bar charts, pie charts, symbols, binary matrices, gradients, protein domains, connections, and more
- **Full API client**: upload, export PDF/SVG/PNG/TIFF/EPS/Newick/Nexus/PhyloXML, delete, and batch operations via iTOL batch endpoints
- **Taxonomy & monophyly analysis**: built-in dendropy integration for monophyletic/paraphyletic/polyphyletic group classification
- **Extract taxonomy from tip names**: supports GTDB (`d__Bacteria;p__Proteobacteria;...`), embedded (`_d_Bacteria_p_...`), NCBI (`Genus_species`), auto-detection, underscore, and mixed formats
- **Monophyly check → conditional styling**: check if a taxon is monophyletic, then automatically decide whether to generate beautification templates
- **Color-blind friendly palettes**: `tol_bright`, `tol_vibrant`, `wong`, `okabeito`, and more
- **Auto legend positioning**: legends placed in bottom-right corner to avoid tree overlap
- **Session snapshots & replay**: YAML-based operation recording for reproducible workflows
- **Newick/Nexus dual format**: automatic tree file format detection

### Taxonomy Parsing

- **Format A (embedded)**: `GB_GCA_0001_d_Bacteria_p_Proteo_c_..._g_Genus`
- **Format B (semicolon)**: `d__Archaea;p__Thermoproteota;c__Korarchaeia;...`
- **Mixed mode**: auto-detect and unify both formats
- **Extensible levels**: custom taxonomy level prefixes via `--taxonomy-levels`
- **Special identifiers**: `LUCA` (MRCA of all Bacteria and Archaea), `LACA` (MRCA of Archaea), `LBCA` (MRCA of Bacteria), `ROOT` (all tips in the tree)

### Monophyly-Based Clade Collapsing

```bash
# Collapse by taxon name (with monophyly check)
pyitol template create-collapse --taxon Cyanobacteriota --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk -o collapse.txt

# Strict mode: terminate on non-monophyletic groups
pyitol template create-collapse --taxon Proteobacteria --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk --strict -o collapse.txt

# Default mode: skip non-monophyletic groups and continue
pyitol template create-collapse --taxon Proteobacteria --rank Phylum \
  --taxonomy tax.csv --tree tree.nwk -o collapse.txt
```

### Real-time Logging

- Stream output, no buffering, direct `sys.stdout` write with `flush`
- ISO8601 timestamps: `2025-03-21T10:15:30.123 | INFO     | message`
- Plain text format, no color output
- `--log-file` for simultaneous file output
- Log levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

### Multi-tree Handling

Multi-tree strategy selection is a **library capability**, implemented by `pyitol.core.parser.load_tree()`:

```python
# load one tree out of a multi-tree file, or all of them
from pyitol.core.parser import load_tree

tree = load_tree("trees.nwk", multi_tree="first")
trees = load_tree("trees.nwk", multi_tree="split")
```

Strategies: `ask` (default, prompts on an interactive terminal and falls back to `first` otherwise), `first` (first tree), `last` (last tree), `split` (return every tree for separate processing). `all` is an internal alias equivalent to `split`. The tool is deliberately deterministic, so there is no `random` strategy. On the CLI, only `taxonomy monophyly` and `taxonomy check-and-style` declare `--multi-tree-mode` / `-m`, and both currently ignore the value (the source marks the parameter as reserved for future use); no `template create <type>` or `template create-*` command accepts it, and all other commands call the library with a hard-coded strategy.

### Input File Validation

```bash
# Validate tree, sequence, and taxonomy files
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta

# Deep validation: bracket balance, branch lengths, duplicate names, alphabet
pyitol validate --tree tree.nwk --alphabet DNA
```

Validation includes:
- Trees: bracket balance, negative branch lengths (CRITICAL), empty names (ERROR), duplicate tips (ERROR), multi-root (ERROR)
- Sequences: alphabet detection (DNA/RNA/protein), ID uniqueness, length consistency
- Adversarial protection: malicious characters (control/bidi), circular dependencies, empty files

### Self-test Mode

```bash
# Run self-test: verify dependencies, sample parsing, monophyly logic
pyitol self-test
```

Outputs `[PASS]/[FAIL]` table verifying:
- Third-party dependency imports and versions
- Internal module imports
- Newick tree parsing
- Embedded taxonomy extraction
- Monophyly detection logic
- Malicious character detection

## Installation

```bash
pip install pyitol
```

With conda (recommended for bioinformatics users):

```bash
conda create -n pyitol python=3.12
conda activate pyitol
pip install pyitol
```

From source:

```bash
git clone https://github.com/ZengZichao/PyiTOL.git
cd PyiTOL
pip install -e ".[dev]"
```

Install optional dependencies (memory monitoring):

```bash
pip install pyitol[memory]
```

### Docker Deployment

PyiTOL provides a Docker image for isolated environments:

```bash
# Build from the included Dockerfile
docker build -t pyitol:latest .

# Run with mounted data directory
docker run -v $(pwd)/data:/data pyitol:latest \
  template create color-strip --tree /data/tree.nwk \
  --taxonomy /data/tax.csv --column Phylum -o /data/output.txt
```

The Docker image includes all runtime dependencies and is suitable for HPC clusters or cloud platforms.

### Verify Installation

After installation, run the following commands to verify:

```bash
# Check version
pyitol --version

# Run self-test (verifies dependencies, sample parsing, core logic)
pyitol self-test
```

Expected output:
```
pyitol 1.0.3
license: MIT
...
```

```
  PyiTOL Self-Test Results
  =======================================================
  [PASS] Import typer (v0.25.1)
  [PASS] Import pandas (v2.3.3)
  [PASS] Parse sample Newick (4 tips)
  [PASS] Monophyly detection (G1=mono, G2=mono)
  ...
  All checks passed.
```

## Example Data

The project ships example data under `examples/data/`:

| File | Description |
|------|-------------|
| `synthetic_130tips.nwk` | Synthetic phylogenetic tree with 130 tips |
| `synthetic_130tips_taxonomy.csv` | Corresponding taxonomy table (Phylum → Genus) |
| `synthetic_130tips_amr.csv` | Synthetic antimicrobial resistance gene data |
| `synthetic_130tips_auto_taxonomy.csv` | Auto-extracted taxonomy table |
| `synthetic_130tips_enriched.csv` | Enriched analysis data |
| `synthetic_32tips.nwk` | Synthetic 32-tip tree for monophyly tests |
| `synthetic_32tips_taxonomy.csv` | Corresponding taxonomy table |
| `synthetic_32tips_auto_taxonomy.csv` | Auto-extracted taxonomy table |
| `synthetic_32tips_enriched.csv` | Enriched analysis data |
| `synthetic_4096tips.nwk` | Large synthetic tree with 4096 tips (stress testing) |
| `synthetic_4096tips_taxonomy.csv` | Corresponding taxonomy table |
| `synthetic_4096tips_traits.csv` | Trait data |
| `synthetic_5000tips.nwk` | Large synthetic tree with 5000 tips (stress testing) |
| `synthetic_5000tips_taxonomy.csv` | Corresponding taxonomy table |
| `synthetic_5000tips_traits.csv` | Trait data |

Quick trial with the example data:

```bash
# Show tree info
pyitol tree info --tree examples/data/synthetic_130tips.nwk

# Validate input files
pyitol validate --tree examples/data/synthetic_130tips.nwk \
  --taxonomy examples/data/synthetic_130tips_taxonomy.csv

# Generate a color-strip template
pyitol template create color-strip \
  --tree examples/data/synthetic_130tips.nwk \
  --taxonomy examples/data/synthetic_130tips_taxonomy.csv \
  --column Phylum -o phylum_strip.txt

# Check monophyly
pyitol taxonomy monophyly \
  --tree examples/data/synthetic_32tips.nwk \
  --taxonomy examples/data/synthetic_32tips_taxonomy.csv \
  --rank Genus -o monophyly.csv

# Extract taxonomy from tip names
pyitol taxonomy extract-from-names \
  --tree examples/data/synthetic_130tips.nwk \
  --format auto -o extracted_taxonomy.csv
```

## Quick Start

### Local Template Generation (No API Key Required)

The fastest way to get started is to generate iTOL template files locally from your tree and taxonomy data — no API key or internet connection required:

```bash
# Generate a color-strip template from a Newick tree and taxonomy table
pyitol template create color-strip --tree tree.nwk --taxonomy tax.csv --column Phylum -o colorstrip.txt
```

This produces a plain-text iTOL template file (`colorstrip.txt`) that you can upload manually to [iTOL](https://itol.embl.de/) via drag-and-drop.

### Validate Input Files

Before generating templates, validate your input files for common issues:

```bash
pyitol validate --tree tree.nwk --taxonomy tax.csv
```

This checks tree format, bracket balance, duplicate tip names, and taxonomy consistency. For deeper validation including sequence alphabet detection:

```bash
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta --alphabet DNA
```

### Version Info

```bash
# Display version, Git hash, dependency versions and licenses
pyitol --version
```

Output example:
```
pyitol 1.0.3
license: MIT
date: 2026-08-26
git: abc1234
dependencies:
  typer: 0.25.1 (MIT)
  pandas: 2.3.3 (BSD-3-Clause)
  dendropy: 4.6.4 (BSD-3-Clause)
  numpy: 2.4.4 (BSD-3-Clause)
  ...
```

### Optional: Upload to iTOL

> The following steps require a free [iTOL API key](https://itol.embl.de/help.cgi#batch). If you only need local template generation, you can skip this section.

#### API Key Configuration

Three methods supported (highest to lowest priority):

```bash
# Method 1: Command-line (temporary)
pyitol task upload --tree tree.nwk --api-key YOUR_KEY

# Method 2: Environment variable
export ITOL_API_KEY=YOUR_KEY

# Method 3: Key file
pyitol task upload --tree tree.nwk --api-key-file /path/to/key.txt
```

> **Credential security**
>
> - **Never commit key files to version control.** Patterns `*.key`, `itolapi.key`, and `.itolapi.key` are already listed in `.gitignore`, but a key file can still leak through other channels — do not place it in cloud-synced folders (e.g. cloud-drive sync directories) or shared directories.
> - **Prefer `~/.config/pyitol/` (mode 600)** for storing key files, rather than the project root.
> - Session snapshots and logs automatically redact key material (`***REDACTED***`), so snapshots are safe to share.
> - If a key may have been exposed (committed, synced, or shared), **rotate it immediately** in your iTOL account settings.

#### Upload and Export PDF

```bash
# One-step: upload → render → export PDF locally
pyitol task upload-and-export \
  --tree tree.nwk \
  --config template1.txt \
  --config template2.txt \
  --api-key YOUR_KEY \
  --dataset-name "MyTree" \
  --format pdf \
  --dpi 300 \
  --output ./result.pdf \
  --wait 30
```

Supported formats: `pdf`, `svg`, `png`, `tiff`, `eps`, `newick`, `nexus`, `phyloxml`. Options: `--dpi`, `--width`, `--height`.

The `upload-and-export` command also supports `--parameter` for passing iTOL export parameters (e.g., `datasets_visible`, `display_mode`, `background`), consistent with the `task export` command:

```bash
# Control dataset visibility and rendering via --parameter
pyitol task upload-and-export \
  --tree tree.nwk \
  --config template1.txt --config template2.txt \
  --api-key YOUR_KEY --dataset-name "MyTree" \
  --format png --dpi 300 --output ./result.png --wait 30 \
  --parameter datasets_visible=0,1 \
  --parameter display_mode=2 \
  --parameter background=ffffff
```

## Taxonomy & Monophyly Analysis

### Extract Taxonomy from Tip Names

```bash
# GTDB format: d__Bacteria;p__Proteobacteria;...;s__Escherichia_coli
pyitol taxonomy extract-from-names --tree tree.nwk --format gtdb -o taxonomy.csv

# Embedded format: GB_GCA_0001_d_Bacteria_p_Proteo_c_..._g_Genus
pyitol taxonomy extract-from-names --tree tree.nwk --format embedded -o taxonomy.csv

# NCBI format: Genus_species
pyitol taxonomy extract-from-names --tree tree.nwk --format ncbi -o taxonomy.csv

# Auto-detect format
pyitol taxonomy extract-from-names --tree tree.nwk --format auto -o taxonomy.csv

# Custom taxonomy levels
pyitol taxonomy extract-from-names --tree tree.nwk \
  --taxonomy-levels "d:Domain,p:Phylum,c:Class,o:Order,f:Family,g:Genus,s:Species" \
  -o taxonomy.csv
```

### Monophyly Check → Conditional Styling

```bash
# Check if Escherichia is monophyletic
# If yes → generate branch coloring template
# If no → warn and exit
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxonomy tax.csv \
  --taxon Escherichia \
  --rank Genus \
  --action color-branch \
  --color "#e41a1c" \
  --output clade.txt

# Using special identifiers
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxonomy tax.csv \
  --taxon LUCA \
  --rank Domain \
  --action color-branch \
  --output luca.txt

# Without taxonomy file → auto-extract from tip names
pyitol taxonomy check-and-style \
  --tree tree.nwk \
  --taxon Salmonella \
  --rank Genus \
  --action highlight \
  --output highlight.txt
```

Supported styling types:
- `color-branch`: branch coloring
- `highlight`: label background highlighting
- `color-strip`: outer color strip

### Monophyly Check

```bash
# Check monophyly of all genera
pyitol taxonomy monophyly --tree tree.nwk --taxonomy tax.csv \
  --rank Genus --output monophyly_results.csv

# Check special identifiers
pyitol taxonomy monophyly --tree tree.nwk --taxonomy tax.csv \
  --taxa LUCA,LACA,LBCA,ROOT --output special_monophyly.csv

# Extract taxonomy summary
pyitol taxonomy extract --tree tree.nwk --taxonomy tax.csv \
  --rank Genus --output taxonomy_summary.csv

# List available taxonomy ranks
pyitol taxonomy ranks --taxonomy tax.csv
```

## Template Examples

```bash
# Color strip - categorical coloring by taxonomic rank (legend auto-positioned)
pyitol template create color-strip --tree tree.nwk --taxonomy tax.csv \
  --column Phylum -o strip.txt

# Heatmap - numeric data visualization
pyitol template create heatmap --tree tree.nwk --taxonomy tax.csv \
  --columns "gc_content,genome_size" --gradient "#ffffcc,#800026" -o heatmap.txt

# Bar chart - quantitative comparison
pyitol template create simple-bar --tree tree.nwk --taxonomy tax.csv \
  --column genome_size --bar-color "#3c5484" -o bar.txt

# Binary matrix - presence/absence
pyitol template create binary --tree tree.nwk --taxonomy tax.csv \
  --columns "amr_genes,virulence_factors" -o binary.txt

# Connection lines between nodes (JSON format)
pyitol template create connections --connections connections.json -o connections.txt

# Branch gradient - continuous coloring
pyitol template create branch-gradient --tree tree.nwk --taxonomy tax.csv \
  --column gc_content --color-min "#313695" --color-max "#a50026" -o gradient.txt

# Domain architecture
pyitol template create domains --data-file domains.json -o domain.txt

# Multi-column bubble external shape (dedicated subcommand only, not a unified-entry type)
pyitol template create-external-shape-bubble --tree tree.nwk --taxonomy tax.csv \
  --columns "gc_content,genome_size,gene_count" -o bubble.txt

# Bundle multiple templates at once
pyitol template bundle --tree tree.nwk --taxonomy tax.csv \
  --config '[{"type":"color-strip","column":"Phylum"},{"type":"heatmap","columns":["gc","genome_size"]}]' \
  --output-dir ./templates/
```

### Output File Structure

PyiTOL generates plain text template files that can be directly uploaded to iTOL:

| Output Type | Format | Description |
|-------------|--------|-------------|
| Template files (`.txt`) | iTOL standard | Contains dataset header and data rows, ready for iTOL |
| Taxonomy table (`.csv`) | CSV/TSV | ID column + taxonomy rank columns |
| Monophyly results (`.csv`) | CSV | Contains group/status/lca_node/member_count columns |
| Session snapshots (`.yaml`) | YAML | Operation history, supports `replay` |

Template file structure:
```
DATASET_COLORSTRIP
SEPARATOR TAB
DATASET_LABEL Phylum
COLOR #ff0000
...
DATA
TaxonA	#4477AA	Proteobacteria
TaxonB	#EE6677	Firmicutes
```

## Tree File Operations

```bash
# Show basic tree info (number of tips, internal nodes, whether branch lengths are present, etc.)
pyitol tree info --tree examples/data/synthetic_130tips.nwk

# Format support values (IQ-TREE bootstrap/aLRT style; RAxML etc. need the library API)
pyitol tree format-support-values --tree input.nwk -o output.nwk
```

## Utility Tools

```bash
# Search tree files in a directory
pyitol utils search-tree-file --dir ./data/

# Parse taxonomy info
pyitol utils taxonomy-parse --taxonomy tax.csv

# Data format conversion: wide table -> long table
pyitol utils wide-to-long --data wide.csv --id-column id -o long.csv

# Data format conversion: long table -> wide table
pyitol utils long-to-wide --data long.csv --id-column id -o wide.csv

# Counts data to tree
pyitol utils count-to-tree --data counts.csv -o tree.nwk

# Group columns
pyitol utils group-columns --data data.csv --group-regex '^col' -o grouped.csv

# Preview data files
pyitol utils preview --taxonomy tax.csv --tree tree.nwk --column Phylum

# DataFrame to tree
pyitol utils df-tree --data data.csv --columns col1,col2 -o tree.nwk
```

> **Note**: `utils tree-info` is deprecated, use `tree info` instead; `utils learn-template` is deprecated, use `learn template` instead.

## Learning from Existing Templates

```bash
# Learn parameters from an existing iTOL template file
pyitol learn template --template existing_template.txt

# Inspect a color palette preset
pyitol learn palette --preset-name nature

# Train a theme
pyitol learn train-theme --dir templates_dir/ --output theme.json
```

## Configuration File Management

```bash
# Initialize a configuration file
pyitol config init

# Or copy the bundled example template
cp config.example.yaml pyitol_config.yaml

# Use a configuration file
pyitol --config pyitol.yaml template create color-strip \
  --tree tree.nwk --taxonomy tax.csv --column Phylum
```

Example configuration file (`pyitol.yaml`):
```yaml
tree: examples/data/synthetic_130tips.nwk
taxonomy: examples/data/synthetic_130tips_taxonomy.csv
id_column: id
separator: TAB
palette: tol_bright
```

The project root provides a `config.example.yaml` template documenting all configurable options with comments (API key, export formats, tree parsing parameters, taxonomy parsing parameters, etc.); copy and edit it as needed. Its `multi_tree_mode` key is only read by `taxonomy monophyly`, which currently ignores it (see Multi-tree Handling). The `palette` key feeds the `--palette` option, which is likewise accepted but not used when writing templates: strip/branch colors come from the built-in `DEFAULT_PALETTE` (cycled per category) unless `--colors` supplies a JSON mapping.

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ Input Files │     │  Taxonomy   │     │  Templates  │
│             │     │   Parsing   │     │ Generation  │
│  tree.nwk   │────>│ From names  │────>│ color-strip │
│   tax.csv   │     │  or table   │     │   heatmap   │
│ seqs.fasta  │     │             │     │  bar / pie  │
└─────────────┘     └──────┬──────┘     └──────┬──────┘
                    ┌──────┴──────┐     ┌──────┴──────┐
                    │  Monophyly  │     │  Upload to  │
                    │    Check    │     │    iTOL     │
                    │  taxonomy   │     │   upload    │
                    │  monophyly  │     │ export PDF  │
                    └─────────────┘     └─────────────┘
```

Typical workflow:
1. **Prepare input**: Phylogenetic tree (Newick/Nexus) + taxonomy table (CSV/TSV)
2. **Parse taxonomy**: Auto-extract from tip names or use external table
3. **Monophyly check**: Verify if taxa are monophyletic
4. **Generate templates**: Create iTOL visualization templates based on taxonomy
5. **Upload & export**: Upload to iTOL platform and export PDF/SVG/PNG

## Color-Blind Friendly Palettes

| Palette | Colors | Source |
|---------|--------|--------|
| `tol_bright` | #4477AA #EE6677 #228833 #CCBB44 #66CCEE #AA3377 #BBBBBB | Paul Tol |
| `tol_vibrant` | #EE7733 #0077BB #33BBEE #EE3377 #CC3311 #009988 #BBBBBB | Paul Tol |
| `wong` | #000000 #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 | Wong (2011) |
| `okabeito` | #E69F00 #56B4E9 #009E73 #F0E442 #0072B2 #D55E00 #CC79A7 #000000 | Okabe & Ito (2008) |
| `ibm` | #648FFF #785EF0 #DC267F #FE6100 #FFB000 | IBM Design |

These names are read through the presets API (`get_palette("colorblind", "wong")`) or listed by `pyitol learn palette --preset-name colorblind`. The `--palette` option of `template create` and `create-color-strip` is accepted but currently unused, so passing a name there changes nothing; use `--colors colors.json` to control the colors that are actually written.

## Session Snapshots & Reproducibility

```bash
# After a workflow, session snapshot is saved automatically
pyitol task upload --tree tree.nwk --config template.txt
# Snapshot directory: $XDG_DATA_HOME/pyitol/session_logs when XDG_DATA_HOME is set,
# otherwise ~/.pyitol/session_logs

# Replay a previous session
pyitol replay --session session.yaml

# Show suggested commands without executing
pyitol replay --session session.yaml --dry-run
```

## Large-scale Data Handling

```bash
# Low memory mode (for large datasets)
pyitol --low-memory template create color-strip --tree large_tree.nwk ...

# Verbose logging (shows memory usage etc.)
pyitol --verbose template create color-strip --tree large_tree.nwk ...

# Log to file
pyitol --log-file pyitol.log template create color-strip --tree tree.nwk ...
```

- Trees with >10,000 tips trigger INFO log about resource requirements
- Use `--verbose` for DEBUG-level memory usage (requires `psutil`)

## Output File Management

```bash
# Default: error if output file exists (all subcommands are now protected)
pyitol template create color-strip --tree tree.nwk -o output.txt

# Force overwrite (every dedicated create-* subcommand takes it too)
pyitol template create color-strip --tree tree.nwk -o output.txt --force

# Skip existing files (same option set on the create-* subcommands)
pyitol template create color-strip --tree tree.nwk -o output.txt --no-clobber
```

> Every template command — the unified entry `template create` and all 34 dedicated `create-*` subcommands — refuses to overwrite an existing output file. Pass `--force`/`-f` to overwrite it, or `--no-clobber` to leave it untouched.

## Graceful Interrupt

Press `Ctrl+C` to gracefully terminate:
- Outputs current processing progress
- Closes all open file handles
- Deletes incomplete temporary files
- Exit code 130

## Error Codes

| Exit Code | Meaning | Description |
|-----------|---------|-------------|
| 0 | Success | Operation completed successfully |
| 1 | Runtime Error | Internal error, dependency issue, API failure |
| 2 | Parameter Error | Invalid CLI arguments, validation failure |
| 3 | Data Error | Input file format/content error |
| 130 | User Interrupt | SIGINT (Ctrl+C) received |

See [Error Codes Documentation](docs/error_codes_en.md) for details.

## CLI Overview

```
pyitol
├── --version             Display version, Git hash and dependency versions
├── --verbose             Enable verbose logging
├── --quiet               Show only critical info
├── --config              Load YAML/JSON config file (can be specified multiple times)
├── --log-file            Log file path
├── --low-memory          Low memory mode
├── self-test             Run self-test
├── validate              Validate input files
├── config                Configuration file management
├── template              Create and manage iTOL template files
│   ├── create-*          34 dedicated subcommands (33 types + external-shape-bubble)
│   ├── create-collapse   Collapse branches (with --taxon monophyly check)
│   ├── bundle            Batch-generate multiple templates
│   └── validate          Validate template format
├── taxonomy              Taxonomy analysis & monophyly detection
│   ├── ranks             List taxonomy ranks
│   ├── extract           Extract taxonomy info
│   ├── extract-stats     Extract taxonomy statistics
│   ├── extract-from-names  Auto-extract taxonomy from tip names
│   ├── monophyly         Monophyly check (supports LUCA/LACA/LBCA/ROOT)
│   ├── check-and-style   Monophyly check → conditional styling
│   ├── style             Taxonomy style templates
│   ├── convert-binary    Convert to binary matrix
│   └── convert-connect   Convert to connection pairs
├── task                  iTOL API task management
│   ├── upload            Upload to iTOL
│   ├── export            Export from iTOL
│   ├── upload-and-export Upload + export in one step
│   ├── delete            Delete iTOL trees
│   ├── status            Query tree status
│   └── run               Batch task execution
├── tree                  Tree file operations
├── utils                 Utility tools
├── learn                 Reverse-learn from existing templates
└── replay                Replay operation records
```

## Project Structure

```
PyiTOL/
├── src/pyitol/                 Source code
│   ├── api/                    iTOL API client
│   ├── cli/                    CLI command definitions
│   ├── core/                   Core algorithms (parser, monophyly, taxonomy)
│   ├── templates/              Template generators and schema definitions
│   └── utils/                  Utility functions (color, I/O, session, logging, shutdown)
├── tests/                      Test suite (1500+ tests)
│   ├── data/                   Test data files
│   ├── core/                   Core algorithm tests
│   ├── cli/                    CLI command tests
│   ├── templates/              Template system tests
│   ├── utils/                  Utility function tests
│   └── api/                    API client tests
├── examples/
│   └── data/                   Demo data files
├── docs/                       Documentation
│   ├── cli_en.md               CLI reference
│   ├── api_en.md               API guide
│   ├── error_codes_en.md       Error codes reference
│   └── tutorials/              Tutorials
│       ├── quickstart_en.md    Quick start guide
│       ├── templates_en.md     Template type overview
│       └── taxonomy_en.md      Taxonomy analysis tutorial
├── benchmarks/                 Performance benchmarks
└── pyproject.toml              Project configuration
```

## Documentation

- [Quick Start Guide](docs/tutorials/quickstart_en.md)
- [Template Type Overview](docs/tutorials/templates_en.md)
- [Taxonomy Analysis Tutorial](docs/tutorials/taxonomy_en.md)
- [CLI Reference](docs/cli_en.md)
- [API Guide](docs/api_en.md)
- [Error Codes Reference](docs/error_codes_en.md)
- [Contributing](CONTRIBUTING.md)

## Dependency Licenses

| Library | Version | License |
|---------|---------|---------|
| typer | >=0.15.0,<1.0 | MIT |
| rich | ~=13.0 | MIT |
| pandas | ~=2.0 | BSD-3-Clause |
| dendropy | >=4.6,<6.0 | BSD-3-Clause |
| numpy | >=1.24,<3.0 | BSD-3-Clause |
| requests | ~=2.32 | Apache-2.0 |
| PyYAML | ~=6.0 | MIT |
| pydantic | ~=2.5 | MIT |
| scipy | ~=1.11 | BSD-3-Clause |

## Citation

If you use PyiTOL in your research, please cite:

- **PyiTOL**: Zeng, Z. (2026). PyiTOL: reproducible Python workflows for iTOL annotation and taxonomic monophyly assessment. *bioRxiv*. doi:10.64898/2026.08.27.747471
- **iTOL**: Letunic, I., & Bork, P. (2021). Interactive Tree Of Life (iTOL) v5. *Nucleic Acids Research*, 49(W1), W293-W296. doi:10.1093/nar/gkab301
- **DendroPy**: Sukumaran, J., & Holder, M. T. (2010). DendroPy. *Bioinformatics*, 26(12), 1569-1571. doi:10.1093/bioinformatics/btq228
- **DendroPy 5**: Moreno, M. A., Holder, M. T., & Sukumaran, J. (2024). DendroPy 5: a mature Python library for phylogenetic computing. *Journal of Open Source Software*, 9(101), 6943. doi:10.21105/joss.06943
- **itol.toolkit**: Zhou, T., Xu, K., Zhao, F., Liu, W., Li, L., Hua, Z., & Zhou, X. (2023). itol.toolkit accelerates working with iTOL by an automated generation of annotation files. *Bioinformatics*, 39(6), btad339. doi:10.1093/bioinformatics/btad339

If you use the benchmark comparison features (ete3/ete4, optional dependencies):

- **ETE 3**: Huerta-Cepas, J., Serra, F., & Bork, P. (2016). ETE 3: Reconstruction, analysis, and visualization of phylogenomic data. *Molecular Biology and Evolution*, 33(6), 1635-1638. doi:10.1093/molbev/msw046

See [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/ZengZichao/PyiTOL/issues)
- **GitHub Discussions**: [Community discussions](https://github.com/ZengZichao/PyiTOL/discussions)
- **Email**: zengzichao@sjtu.edu.cn
- **Maintainer**: Zichao Zeng

Feel free to reach out through the above channels for questions, suggestions, or contributions.

## License

This project is licensed under the [MIT License](LICENSE). See [NOTICE](NOTICE) for third-party copyright and license information.
