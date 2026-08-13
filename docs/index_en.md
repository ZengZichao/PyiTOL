# PyiTOL Documentation

PyiTOL is a Python-based, full-pipeline automation command-line tool for iTOL (Interactive Tree of Life) visualization.

## Documentation Navigation

| Document | Description |
|------|------|
| [Complete CLI Reference](cli.md) | Detailed description of all commands and parameters |
| [API Usage Guide](api.md) | iTOL API interaction and automated upload/export |
| [Quick Start Tutorial](tutorials/quickstart.md) | A 10-minute tutorial from installation to figure output |
| [Taxonomy Analysis Tutorial](tutorials/taxonomy.md) | Monophyly detection and taxonomy information extraction |
| [Template Generation Tutorial](tutorials/templates.md) | Generation guide for 31 iTOL v7 template types (plus the `external-shape-bubble` variant) |

## Core Features

```
PyiTOL Feature System:
├── Tree Structure
│   ├── Collapse Clades
│   ├── Prune Tree
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
│   ├── Shape Plots
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
    ├── Template Learning
    ├── Tree Info
    ├── Color Tools
    ├── Count to Tree
    └── Column Grouping
```

## Installation

```bash
pip install -e .
```

Dependencies: Python 3.9+, typer, pandas, dendropy, numpy, requests, pydantic, PyYAML, rich, scipy

## Quick Verification

```bash
pyitol --help
pyitol template create --help
pyitol taxonomy monophyly --help
```
