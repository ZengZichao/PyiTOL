# PyiTOL

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI](https://img.shields.io/pypi/v/pyitol.svg)](https://pypi.org/project/pyitol)
[![CI](https://github.com/ZengZichao/PyiTOL/actions/workflows/ci.yml/badge.svg)](https://github.com/ZengZichao/PyiTOL/actions/workflows/ci.yml)

English | [中文](README_CN.md)

**PyiTOL** is a Python CLI tool for automating phylogenetic tree visualization on the **iTOL (Interactive Tree Of Life)** platform.

## Features

### Core Features

- **31 iTOL template types** (plus `external-shape-bubble`, a variant of `external-shape`): color strips, heatmaps, bar charts, pie charts, symbols, binary matrices, gradients, protein domains, connections, and more
- **Full API client**: upload, export PDF/SVG/PNG/TIFF/EPS/Newick/Nexus/PhyloXML, delete, and batch operations via iTOL batch endpoints
- **Taxonomy & monophyly analysis**: built-in dendropy integration for monophyletic/paraphyletic/polyphyletic group classification
- **Extract taxonomy from tip names**: supports GTDB (`d__Bacteria;p__Proteobacteria;...`), embedded (`_d_Bacteria_p_...`), NCBI (`Genus_species`), auto-detection, underscore, and mixed formats
- **Monophyly check → conditional styling**: check if a taxon is monophyletic, then automatically generate beautification templates
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

```bash
# Default: prompt user when multiple trees detected
pyitol template create color-strip --tree multi.nwk ...

# Specify processing strategy
pyitol template create color-strip --tree multi.nwk --multi-tree-mode first ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode last ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode random ...
pyitol template create color-strip --tree multi.nwk --multi-tree-mode split ...
```

### Input File Validation

```bash
# Validate tree, sequence, and taxonomy files
pyitol validate --tree tree.nwk --taxonomy tax.csv --sequence seqs.fasta

# Deep validation: bracket balance, branch lengths, duplicate names, alphabet
pyitol validate --tree tree.nwk --alphabet DNA
```

Validation includes:
- Trees: bracket balance, negative branch lengths (CRITICAL), empty names (ERROR), duplicate tips (ERROR), multi-root (CRITICAL)
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
cd pyitol
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
  pyitol template create color-strip --tree /data/tree.nwk \
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
pyitol 1.0.0
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
pyitol 1.0.0
license: MIT
date: 2026-08-13
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

> **Credential security / 凭据安全**
>
> - **Never commit key files to version control.** Patterns `*.key`, `itolapi.key`, and `.itolapi.key` are already listed in `.gitignore`, but a key file can still leak through other channels — do not place it in cloud-synced folders (e.g. cloud-drive sync directories) or shared directories.
> - **Prefer `~/.config/pyitol/` (mode 600) or your system keychain** for storing key files, rather than the project root.
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
  --column Phylum --palette tol_bright -o strip.txt

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
  --column gc_content --gradient "#313695,#a50026" -o gradient.txt

# Domain architecture
pyitol template create domains --data-file domains.json -o domain.txt

# Multi-column bubble external shape (numeric column visualization)
pyitol template create external-shape-bubble --tree tree.nwk --taxonomy tax.csv \
  --columns "gc_content,genome_size,gene_count" -o bubble.txt

# Bundle multiple templates at once
pyitol template bundle --tree tree.nwk --taxonomy tax.csv \
  --config '[{"type":"color-strip","column":"Phylum"},{"type":"heatmap","columns":"gc,genome_size"}]' \
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

## Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Input Files │     │   Taxonomy  │     │  Templates  │
│             │     │   Parsing   │     │  Generation │
│ tree.nwk    │────>│ From names  │────>│ color-strip │
│ tax.csv     │     │ or table    │     │ heatmap     │
│ seqs.fasta  │     │             │     │ bar/pie/... │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                   │
                           v                   v
                    ┌─────────────┐     ┌─────────────┐
                    │  Monophyly  │     │  Upload to  │
                    │   Check     │     │    iTOL     │
                    │             │     │             │
                    │ monophyly   │     │ upload      │
                    │ check       │     │ export PDF  │
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

Usage: `--palette wong`

## Session Snapshots & Reproducibility

```bash
# After a workflow, session snapshot is saved automatically
pyitol task upload --tree tree.nwk --config template.txt
# Snapshot saved to ~/.pyitol/session_logs/

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

# Force overwrite (unified entry 'template create' only)
pyitol template create color-strip --tree tree.nwk -o output.txt --force

# Skip existing files (unified entry 'template create' only)
pyitol template create color-strip --tree tree.nwk -o output.txt --no-clobber
```

> All standalone subcommands (e.g., `create-color-strip`, `create-heatmap`, etc.) now check if the output file already exists to prevent accidental overwrites. To overwrite, use the unified entry `template create` with `--force`.

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

See [Error Codes Documentation](docs/error_codes.md) for details.

## CLI Overview

```
pyitol
├── --version             Display version, Git hash and dependency versions
├── --verbose             Enable verbose logging
├── --quiet               Show only critical info
├── --log-file            Log file path
├── --low-memory          Low memory mode
├── self-test             Run self-test
├── validate              Validate input files
├── config                Configuration file management
├── template              Create and manage iTOL template files
│   ├── create-*          31 template creation subcommands
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
├── tests/                      Test suite (1702 tests)
│   ├── data/                   Test data files
│   ├── core/                   Core algorithm tests
│   ├── cli/                    CLI command tests
│   ├── templates/              Template system tests
│   ├── utils/                  Utility function tests
│   └── api/                    API client tests
├── examples/
│   └── data/                   Demo data files
├── docs/                       Documentation
│   └── error_codes.md          Error codes reference
├── benchmarks/                 Performance benchmarks
└── pyproject.toml              Project configuration
```

## Documentation

- [Quick Start Guide](docs/tutorials/quickstart.md)
- [Template Type Overview](docs/tutorials/templates.md)
- [Taxonomy Analysis Tutorial](docs/tutorials/taxonomy.md)
- [CLI Reference](docs/cli.md)
- [API Guide](docs/api.md)
- [Error Codes Reference](docs/error_codes.md)
- [Contributing](CONTRIBUTING.md)

## Dependency Licenses

| Library | Version | License |
|---------|---------|---------|
| typer | >=0.15.0 | MIT |
| rich | ~=13.0 | MIT |
| pandas | ~=2.0 | BSD-3-Clause |
| dendropy | ~=4.6 | BSD-3-Clause |
| numpy | >=1.24 | BSD-3-Clause |
| requests | ~=2.32 | Apache-2.0 |
| PyYAML | ~=6.0 | MIT |
| pydantic | ~=2.5 | MIT |

## Citation

If you use PyiTOL in your research, please cite:

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
