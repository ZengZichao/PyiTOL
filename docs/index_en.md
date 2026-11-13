# PyiTOL Documentation

[中文](index.md) | English

PyiTOL is a Python-based, full-pipeline automation command-line tool for iTOL (Interactive Tree Of Life) visualization.

## Documentation Navigation

| Document | Description |
|------|------|
| [Complete CLI Reference](cli_en.md) | Detailed description of all commands and parameters |
| [Template Subcommand Reference](templates-reference_en.md) | Full options and examples for the 34 dedicated `template create-*` subcommands |
| [API Usage Guide](api_en.md) | iTOL API interaction and automated upload/export |
| [Error Codes Reference](error_codes_en.md) | Tables of exit codes, E-series error codes and V-series validation codes |
| [Troubleshooting Guide](troubleshooting_en.md) | Common problems and their solutions |
| [Quick Start Tutorial](tutorials/quickstart_en.md) | A 10-minute tutorial from installation to figure output |
| [Taxonomy Analysis Tutorial](tutorials/taxonomy_en.md) | Monophyly detection and taxonomy information extraction |
| [Template Generation Tutorial](tutorials/templates_en.md) | Generation guide for the 33 iTOL v7 template types (plus the `external-shape-bubble` variant, 34 dedicated subcommands in total) |
| [Contributing Guide](contributing_en.md) | Project structure, coding conventions and development workflow |

## Core Features

```
PyiTOL Feature System:
├── Tree Structure
│   ├── Collapse Clades
│   ├── Prune Branches
│   ├── Node Spacing
│   └── Node Labels
├── Annotation
│   ├── Labels & Popup Info
│   ├── Tree Colors
│   ├── Branch Gradients
│   └── Colored Ranges
├── Datasets
│   ├── Binary Data
│   ├── Simple Bar / Multibar
│   ├── Pie Chart
│   ├── Color Strip
│   ├── Heatmap
│   ├── Boxplot
│   ├── Symbols
│   ├── Protein Domains
│   ├── Color Gradients
│   ├── External Shapes
│   ├── Text Labels
│   ├── Arrows
│   ├── Connections
│   ├── Tanglegrams
│   ├── Line Charts
│   ├── Images
│   ├── Alignments
│   ├── Phylogenetic Placements
│   ├── Timescales
│   └── Manual Annotations
├── Taxonomy Analysis
│   ├── Auto Ranks
│   ├── Taxonomy Extract
│   ├── Monophyly Check
│   ├── Style Config
│   ├── Binary Conversion
│   └── Connect Pairs
├── API Operations
│   ├── Upload
│   ├── Delete
│   ├── Export
│   └── Status
└── Utilities
    ├── Learning from Existing Templates
    ├── Tree Info
    ├── Color Tools
    ├── Count to Tree
    └── Column Grouping
```

## Installation

```bash
pip install -e .
```

Dependencies: Python 3.10+, typer, pandas, dendropy, numpy, requests, pydantic, PyYAML, rich, scipy

## Quick Verification

```bash
pyitol --help
pyitol template create --help
pyitol taxonomy monophyly --help
```
