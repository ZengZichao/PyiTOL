# PyiTOL Examples Documentation

English | [中文](README.md)

This directory contains the official example code for the **PyiTOL** project, organized into two main categories:
- **`api_demos/`** — Demonstrates the full functionality of the iTOL API (upload, export, delete, status query)
- **`template_demos/`** — Demonstrates iTOL template file generation, batch processing, and publication-grade plotting workflows

All examples follow these design principles:
- **No duplication, no redundancy**: Each example demonstrates a unique combination of features or workflow patterns
- **Academic journal publication grade**: Uses 300 DPI export, English project names, and colorblind-friendly color presets
- **Complete coverage**: The examples call 31 of the type-specific template generator functions (`generator.py` defines 32 `generate_*_template()` functions; the only one never called is `generate_external_shape_bubble_template()`) and cover all core methods of the API

---

## Directory Structure

```
examples/
├── api_demos/
│   ├── 01_basic_upload.py
│   ├── 02_multi_dataset_publication.py
│   ├── 03_advanced_api_operations.py
│   └── 04_batch_format_export.py
│
├── template_demos/
│   ├── 01_generate_all_template_types.py
│   ├── 02_batch_upload_existing_templates.py
│   ├── 03_publication_quality_figure.py
│   ├── 04_cli_workflow.py
│   └── 05_reverse_learn_template.py
│
├── data/
│   ├── synthetic_32tips.nwk
│   ├── synthetic_32tips_taxonomy.csv
│   ├── synthetic_32tips_enriched.csv
│   ├── synthetic_32tips_auto_taxonomy.csv
│   ├── synthetic_130tips.nwk
│   ├── synthetic_130tips_taxonomy.csv
│   ├── synthetic_130tips_enriched.csv
│   ├── synthetic_130tips_auto_taxonomy.csv
│   ├── synthetic_130tips_amr.csv
│   ├── synthetic_4096tips.nwk
│   ├── synthetic_4096tips_taxonomy.csv
│   ├── synthetic_4096tips_traits.csv
│   ├── synthetic_5000tips.nwk
│   ├── synthetic_5000tips_taxonomy.csv
│   └── synthetic_5000tips_traits.csv
│
├── README.md
└── README_EN.md
```

---

## Example Data Files (`data/`)

The `data/` directory provides 15 synthetic data files grouped by size into 32 / 130 / 4096 / 5000 tips sets; only `synthetic_32tips.nwk` and `synthetic_32tips_enriched.csv` are actually read by the example scripts, while the remaining files serve larger-scale demos and external tests:

- `.nwk` — Newick phylogenetic tree
- `_taxonomy.csv` — taxonomic metadata (phylum/class/order/family/genus/species)
- `_enriched.csv` — enriched trait table (genome size, GC content, etc.)
- `_traits.csv` — trait table for the 4096/5000 tips scale
- `_auto_taxonomy.csv` — taxonomy table auto-parsed from tree tip names
- `_amr.csv` — antimicrobial resistance (AMR) data for the 130 tips set

All `api_demos/` scripts and the tree files of `template_demos/01`, `02`, `03` locate this directory via `Path(__file__).resolve().parents[1] / "data"`; in contrast, `template_demos/02_batch_upload_existing_templates.py:28`, `04_cli_workflow.py:23-25` and `05_reverse_learn_template.py:27` resolve `parents[2] / "tests" / "data"` and use the project-level `tests/data/` instead. Please do not move these files.

---

## API Demos (`api_demos/`)

### 01_basic_upload.py
**Nature**: Minimal Working Example
**Purpose**: Demonstrates the most basic iTOL workflow — uploading a phylogenetic tree and exporting it as a PDF.
**Key features**:
- `ITOLAPIClient` initialization (auto-reads `.itolapi.key`)
- `upload_and_export()` convenience method
- Built-in fixed wait before the export (`wait_time` / `poll_interval`); no `query_status` polling, because iTOL offers no official "tree ready" status API
- Suitable for first-time users of the PyiTOL API

### 02_multi_dataset_publication.py
**Nature**: Comprehensive academic publication-grade example
**Purpose**: Demonstrates how to upload a **multi-dataset combination** (color strip + heatmap + bar) and export journal-grade images.
**Key features**:
- Uses `generate_color_strip_template()` to dynamically generate templates
- Applies the `colorblind` preset palette (Tol Bright)
- **300 DPI PDF** export (meets print requirements for journals such as Nature / Cell / ISME J)
- Simultaneously exports SVG vector graphics for post-editing
- English project names and professional dataset labels

### 03_advanced_api_operations.py
**Nature**: Full API lifecycle management example
**Purpose**: Demonstrates complete management operations after tree upload, suitable for automated pipelines.
**Key features**:
- `force=True` to overwrite an existing tree with the same name
- `query_status()` render status query
- PNG (300 DPI) and TIFF dual-format export
- `batch_delete()` for batch cleanup of temporary uploads

### 04_batch_format_export.py
**Nature**: Multi-format batch export example
**Purpose**: Exports all four supported formats after a single upload, avoiding wasted time from repeated uploads.
**Key features**:
- Full coverage of PDF / SVG / PNG / TIFF
- Parameters optimized for different use cases (PDF→print, SVG→vector editing, PNG→presentations, TIFF→journal submission)
- Unified loop-based export logic (produces `batch_export.<fmt>` files)

---

## Template Demos (`template_demos/`)

### 01_generate_all_template_types.py
**Nature**: Exhaustive compatibility test across all template types
**Purpose**: Programmatically calls **31 of the type-specific `generate_*_template()` generator functions** (`generator.py` defines 32; the only one not called is `generate_external_shape_bubble_template()`), serving as a syntax reference and engine compatibility verification.
**Key features**:
- Calls 31 of the 32 type-specific `generate_*_template()` functions (`generate_external_shape_bubble_template()` is not called, nor is the generic writer `generate_template()`)
- Covers `DATASET_SIMPLEBAR`, `DATASET_HEATMAP`, `DATASET_COLORSTRIP`, `TREE_COLORS`, `COLLAPSE`, `PRUNE`, `SPACING`, `DATASET_BINARY`, `DATASET_CONNECTION`, `DATASET_DOMAINS`, `DATASET_ALIGNMENT`, `DATASET_ARROWS`, `DATASET_TANGLEGRAM`, `DATASET_TIMESCALE`, `DATASET_MEME`, and `DATASET_MANUAL` (these 16 are the highlighted cases; see the 31-row coverage matrix below for the full list)
- Outputs to `outputs/all_types/` for convenient batch inspection

### 02_batch_upload_existing_templates.py
**Nature**: Batch integration test of existing template files
**Purpose**: Traverses all `template_*.txt` template files in the project's `tests/data/` directory, uploads each to iTOL and exports a PDF for verification.
**Key features**:
- Automatic template file discovery
- Independent upload for each file with tree ID recording
- Generates a `batch_upload_log.txt` summary report
- Suitable for verifying compatibility of legacy templates on newer versions of iTOL

### 03_publication_quality_figure.py
**Nature**: High-impact journal-grade multi-layer example
**Purpose**: Builds a publication-grade phylogenetic figure with **three stacked layers** from a taxonomy metadata table.
**Key features**:
- Layer 1: Color Strip (Phylum, NATURE primary palette)
- Layer 2: Simple Bar (Genome Size)
- Layer 3: Heatmap (Genomic Features)
- Uses `generate_*_template()` functions for fine-grained parameter control
- 300 DPI PDF + PNG dual-format export
- Ready-to-use figures for manuscript submission

### 04_cli_workflow.py
**Nature**: Pure command-line workflow example
**Purpose**: Demonstrates how to complete a full workflow via the `pyitol` CLI without writing any Python code.
**Key features**:
- Calls `pyitol validate` to pre-check input
- Calls `pyitol template create` to generate color-strip / heatmap / simple-bar
- Uses `subprocess` to drive the CLI from within the script
- Suitable for Snakemake / Nextflow / Bash pipeline integration

### 05_reverse_learn_template.py
**Nature**: Template reverse engineering example
**Purpose**: Reverse-parses existing iTOL template files into structured JSON and trains recommended themes from a template library.
**Key features**:
- `learn_template()` for single-file parsing (type identification, parameter extraction, data extraction)
- `train_theme()` for directory-level theme learning (statistical analysis of the most common parameter combinations)
- Outputs JSON-formatted structured configuration for easy migration to programmatic workflows

---

## Quick Start

### Prerequisites

1. Install PyiTOL (development mode):
   ```bash
   pip install -e .
   ```
2. Obtain an iTOL API Key (https://itol.embl.de/help.cgi#batch)
3. Create a `.itolapi.key` file in the project root directory and write your API Key into it

### Running the Examples

```bash
# Basic upload
python examples/api_demos/01_basic_upload.py

# Generate all template types
python examples/template_demos/01_generate_all_template_types.py

# Academic-grade multi-dataset upload
python examples/api_demos/02_multi_dataset_publication.py
```

---

## Academic Publication Best Practices (Derived from Examples)

| Element | Recommended Practice | Corresponding Example |
|---|---|---|
| **Resolution** | Export PDF or PNG at 300 DPI | `02_multi_dataset_publication.py`, `03_publication_quality_figure.py` |
| **Color scheme** | Use colorblind-friendly presets (Tol Bright / Vibrant) | `02_multi_dataset_publication.py` |
| **Project name** | Use professional English names; avoid Chinese or "temporary" wording | All examples |
| **Layer composition** | Stack complementary datasets such as color strip, heatmap, and bar | `03_publication_quality_figure.py` |
| **Vector editing** | Simultaneously export SVG for Illustrator / Inkscape fine-tuning | `02_multi_dataset_publication.py` |
| **Format diversity** | Output PDF (print), TIFF (some journals), PNG (PPT) according to submission requirements | `04_batch_format_export.py` |

---

## Template Type Coverage Matrix

| iTOL Template Type | Example Coverage |
|---|---|
| `DATASET_SIMPLEBAR` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_MULTIBAR` | `01_generate_all_template_types.py` |
| `DATASET_COLORSTRIP` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_HEATMAP` | `01_generate_all_template_types.py` + `03_publication_quality_figure.py` |
| `DATASET_SYMBOLS` | `01_generate_all_template_types.py` |
| `DATASET_PIECHART` | `01_generate_all_template_types.py` |
| `DATASET_BINARY` | `01_generate_all_template_types.py` |
| `DATASET_GRADIENT` | `01_generate_all_template_types.py` |
| `DATASET_BOXPLOT` | `01_generate_all_template_types.py` |
| `DATASET_CONNECTION` | `01_generate_all_template_types.py` |
| `DATASET_DOMAINS` | `01_generate_all_template_types.py` |
| `DATASET_TEXT` | `01_generate_all_template_types.py` |
| `DATASET_EXTERNALSHAPE` | `01_generate_all_template_types.py` |
| `DATASET_LINECHART` | `01_generate_all_template_types.py` |
| `DATASET_IMAGE` | `01_generate_all_template_types.py` |
| `DATASET_ALIGNMENT` | `01_generate_all_template_types.py` |
| `DATASET_ARROWS` | `01_generate_all_template_types.py` |
| `DATASET_TANGLEGRAM` | `01_generate_all_template_types.py` |
| `DATASET_PLACEMENT` | `01_generate_all_template_types.py` |
| `DATASET_TIMESCALE` | `01_generate_all_template_types.py` |
| `DATASET_MEME` | `01_generate_all_template_types.py` |
| `DATASET_MANUAL` | `01_generate_all_template_types.py` |
| `DATASET_RANGE` | `01_generate_all_template_types.py` |
| `DATASET_STYLE` | `01_generate_all_template_types.py` |
| `BRANCH` | `01_generate_all_template_types.py` |
| `TREE_COLORS` | `01_generate_all_template_types.py` |
| `LABELS` | `01_generate_all_template_types.py` |
| `POPUP_INFO` | `01_generate_all_template_types.py` |
| `COLLAPSE` | `01_generate_all_template_types.py` |
| `PRUNE` | `01_generate_all_template_types.py` |
| `SPACING` | `01_generate_all_template_types.py` |

---

## Maintenance Notes

- When adding new template types, please add the corresponding `generate_*_template()` call in `01_generate_all_template_types.py`.
- When adding new API methods, please create a new standalone example in `api_demos/` to avoid feature overlap with existing examples.
- Every example writes its outputs into a per-subdirectory output folder `examples/<subdir>/outputs/` (resolved via `Path(__file__).parent / "outputs"`, e.g. `examples/template_demos/outputs/all_types/`). This path is **not** currently listed in `.gitignore`, so the generated artifacts may show up as untracked files; please clean them up yourself before committing if they are not needed.
