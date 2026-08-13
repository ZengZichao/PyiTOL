# PyiTOL Examples Documentation

This directory contains the official example code for the **PyiTOL** project, organized into two main categories:
- **`api_demos/`** — Demonstrates the full functionality of the iTOL API (upload, export, delete, status query)
- **`template_demos/`** — Demonstrates iTOL template file generation, batch processing, and publication-grade plotting workflows

All examples follow these design principles:
- **No duplication, no redundancy**: Each example demonstrates a unique combination of features or workflow patterns
- **Academic journal publication grade**: Uses 300 DPI export, English project names, and colorblind-friendly color presets
- **Complete coverage**: The examples collectively cover all 31 iTOL template types (plus the `external-shape-bubble` variant) and all core methods of the API

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
└── README.md
```

---

## API Demos (`api_demos/`)

### 01_basic_upload.py
**Nature**: Minimal Working Example
**Purpose**: Demonstrates the most basic iTOL workflow — uploading a phylogenetic tree and exporting it as a PDF.
**Key features**:
- `ITOLAPIClient` initialization (auto-reads `.itolapi.key`)
- `upload_and_export()` convenience method
- Built-in render polling (`query_status`) to wait for readiness
- Suitable for first-time users of the PyiTOL API

### 02_multi_dataset_publication.py
**Nature**: Comprehensive academic publication-grade example
**Purpose**: Demonstrates how to upload a **multi-dataset combination** (color strip + heatmap + bar) and export journal-grade images.
**Key features**:
- Uses `TemplateGenerator` to dynamically generate templates
- Applies the `colorblind` preset palette (Tol Bright)
- **300 DPI PDF** export (meets print requirements for journals such as Nature / Cell / ISME J)
- Simultaneously exports SVG vector graphics for post-editing
- English project names and professional dataset labels

### 03_advanced_api_operations.py
**Nature**: Full API lifecycle management example
**Purpose**: Demonstrates complete management operations after tree upload, suitable for automated pipelines.
**Key features**:
- `force=True` to overwrite an existing upload with the same name
- `query_status()` render status query
- PNG (300 DPI) and TIFF dual-format export
- `batch_delete()` for batch cleanup of temporary uploads

### 04_batch_format_export.py
**Nature**: Multi-format batch export example
**Purpose**: Exports all four supported formats after a single upload, avoiding wasted time from repeated uploads.
**Key features**:
- Full coverage of PDF / SVG / PNG / TIFF
- Parameters optimized for different use cases (PDF→print, SVG→vector editing, PNG→presentations, TIFF→journal submission)
- Unified `batch_export` logic

---

## Template Demos (`template_demos/`)

### 01_generate_all_template_types.py
**Nature**: Template type compatibility full-spectrum test
**Purpose**: Programmatically generates **all 31 iTOL v7 template types** (plus the `external-shape-bubble` variant), serving as a syntax reference and engine compatibility verification.
**Key features**:
- Calls all `generate_*_template()` functions
- Covers `DATASET_SIMPLEBAR`, `DATASET_HEATMAP`, `DATASET_COLORSTRIP`, `TREE_COLORS`, `COLLAPSE`, `PRUNE`, `SPACING`, `DATASET_BINARY`, `DATASET_CONNECTION`, `DATASET_DOMAINS`, `DATASET_ALIGNMENT`, `DATASET_ARROWS`, `DATASET_TANGLEGRAM`, `DATASET_TIMESCALE`, `DATASET_MEME`, `DATASET_MANUAL`, and all other types
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
| **Project name** | Use professional English names; avoid Chinese or "temporary" wording | All new examples |
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
- All example output directories use the relative path `outputs/`, which is not tracked by version control.
