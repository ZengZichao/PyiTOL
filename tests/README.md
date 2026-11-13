# PyiTOL Test Suite Documentation

English | [中文](README_CN.md)

This directory contains the complete automated test suite of the **PyiTOL** project. The tests follow the principles of **comprehensive coverage, no duplication, and no redundancy**, are written with the [pytest](https://docs.pytest.org/) framework, and cover every core module, CLI command, API client and utility function of the project.

The test directory maps one-to-one onto the source package `src/pyitol/` and is organized as a hierarchy of subdirectories.

---

## Directory Structure

```
tests/
├── conftest.py                         # globally shared fixtures (tree files, taxonomy tables, API keys, etc.)
├── test_concurrency.py                 # concurrency and thread-safety scenario tests
├── test_exceptions.py                  # exception class hierarchy tests
├── test_main_entry.py                  # CLI entry point tests
├── test_realistic_data.py              # realistic data scenario tests
│
├── api/                                # API client layer tests
│   ├── __init__.py                     # package marker (empty file)
│   ├── test_client.py                  # ITOLAPIClient: upload/export/delete/status/response parsing
│   ├── test_client_robustness.py       # QA independent regression suite: network errors wrapped as UploadError/ExportError, temp zip cleanup
│   ├── test_client_robustness_regression.py # regression lock: same upload/export wrapping and temp-zip cleanup (sibling suite)
│   └── test_error_translation.py       # API error translation and reporting
│
├── cli/                                # CLI command layer tests
│   ├── __init__.py                     # package marker (empty file)
│   ├── test_apps.py                    # sub-application registration
│   ├── test_common.py                  # common CLI utilities (output formatting, argument validation, etc.)
│   ├── test_config.py                  # config command
│   ├── test_force_and_cli_helpers.py   # resolve_output force/no-clobber, load_filtered_taxonomy/load_tree_tips, template create --force
│   ├── test_force_and_cli_helpers_regression.py # regression lock: --force overwrite, --no-clobber skip and the CLI helper units
│   ├── test_learn.py                   # learn command (template / palette / train-theme)
│   ├── test_main.py                    # top-level commands (validate / replay across all template types)
│   ├── test_task.py                    # task command (upload / export / delete / status)
│   ├── test_task_run.py                # task run configuration-file mode
│   ├── test_taxonomy.py                # taxonomy subcommands (ranks/extract/monophyly/convert)
│   ├── test_taxonomy_style.py          # each taxonomy style action
│   ├── test_template_advanced.py       # template advanced types
│   ├── test_template_bundle.py         # template bundle batch generation
│   ├── test_template_create.py         # template create unified entry point
│   ├── test_template_create_all.py     # template create traversal over every type
│   ├── test_template_create_errors.py  # template create error tolerance
│   ├── test_template_create_extended.py# template create extended types
│   ├── test_template_datasets.py       # template dataset-type templates
│   ├── test_template_edge_cases.py     # template edge-case scenarios
│   ├── test_template_tools.py          # template tool subcommands
│   ├── test_template_treeops.py        # template tree-operations (collapse/prune/ranges, etc.)
│   ├── test_template_validate.py       # template validate
│   ├── test_tree.py                    # tree subcommands (info / format-support-values)
│   └── test_utils.py                   # utils subcommands
│
├── core/                               # core module layer tests
│   ├── __init__.py                     # package marker (empty file)
│   ├── test_binary_convert.py          # category_to_binary binarization
│   ├── test_column_group.py            # group_columns column grouping
│   ├── test_connect_convert.py         # matrix_to_connect connection conversion
│   ├── test_count_tree.py              # count_to_tree
│   ├── test_monophyly.py               # monophyly detection
│   ├── test_parser.py                  # TreeParser / MetadataParser / format_support_values
│   ├── test_parser_nhx_determinism.py  # _count_newick_trees/_load_all_trees ignore NHX comments; multi_tree='random' rejected
│   ├── test_parser_nhx_determinism_regression.py # regression lock: NHX-aware tree counting/splitting and the removed 'random' strategy
│   ├── test_taxonomy.py                # taxonomy extraction and parsing (GTDB/embedded/NCBI/mixed)
│   ├── test_validator.py               # TemplateValidator / detect_file_type / validate_inputs
│   ├── test_validator_nhx_extension.py # _detect_tree_format maps .nhx/.nhy to 'newick' (other mappings unchanged)
│   └── test_validator_nhx_extension_regression.py # regression lock: .nhx/.nhy extensions classified as 'newick'
│
├── templates/                          # template module layer tests
│   ├── __init__.py                     # package marker (empty file)
│   ├── test_base.py                    # base schema classes (TemplateSchema/LegendConfig/create_schema)
│   ├── test_boundary_exceptions.py     # single-column COLLAPSE/PRUNE keep all IDs, under-filled row warning, pie FIELD_COLORS, InvalidColumnError
│   ├── test_domain_exceptions.py       # generators/presets raise InvalidColumnError/TemplateError/TemplateTypeError, not bare ValueError
│   ├── test_domain_exceptions_regression.py # template domain exception regression (InvalidColumnError/TemplateError/TemplateTypeError)
│   ├── test_generator.py               # end-to-end generation of the 30+ generate_*_template() functions
│   ├── test_learner.py                 # template reverse learning / train_theme
│   ├── test_merge_embedded_conflict.py # merge_embedded_taxonomy conflict branch keeps the embedded value without KeyError
│   ├── test_presets.py                 # presets and palettes (Nature/Cell/Colorblind)
│   ├── test_roundtrip.py               # generate_template -> learn_template round-trip preserves type/columns/parameters
│   ├── test_roundtrip_pie_colors.py    # round-trip for color_strip/collapse/prune plus pie FIELD_COLORS 1:1 alignment
│   ├── test_schemas_annotations.py     # annotation-type schema
│   ├── test_schemas_base.py            # base schema and create_schema
│   ├── test_schemas_datasets_advanced.py # advanced dataset schema
│   ├── test_schemas_datasets_simple.py # simple dataset schema
│   ├── test_schemas_presets.py         # preset schema
│   ├── test_schemas_tree_structure.py  # tree-structure-type schema
│   └── test_taxonomy_check_and_style_refactor.py # the three helpers extracted from taxonomy_check_and_style plus a CLI smoke test
│
├── utils/                              # utility module layer tests
│   ├── __init__.py                     # package marker (empty file)
│   ├── test_color_tools.py             # color distance / gradients / taxonomy coloring
│   ├── test_constants.py               # pyitol.utils.constants values and their use in generator / taxonomy_cmd
│   ├── test_data_converters.py         # wide-long conversion / count_to_tree / group_columns / df_tree
│   ├── test_fasta.py                   # FASTA read / write / iteration
│   ├── test_io.py                      # search_tree_file / find_first_tree_file
│   ├── test_logger.py                  # RealTimeHandler / StepTracker / _format_duration / setup_logging
│   ├── test_reporter.py                # error translation and reporting
│   ├── test_session.py                 # SessionContext lifecycle and snapshots
│   ├── test_shutdown.py                # signal handling and graceful shutdown
│   └── test_tree_info.py               # extract_tree_info / get_tip_order, etc.
│
├── regression/                         # Phase-1 correctness-fix regression tests
│   ├── __init__.py                     # package marker with a module docstring
│   └── test_phase1_fixes.py            # one test per Phase-1 fix: df_tree hclust leaves, count_to_tree root, NCBI epithet, mixed monophyly, single-column collapse/prune, schema auto-registration
│
└── data/                               # test data files
    ├── 4taxa_monophyly.csv             # expected-output reference for the monophyly test
    ├── 4taxa_tax_extract.csv           # expected-output reference for taxonomy extraction
    ├── 4taxa_taxonomy.csv              # example taxonomy table
    ├── 4taxa_tree.nwk                  # example 4-tip Newick tree
    ├── template_bar.txt                # template reference files
    ├── template_branch.txt
    ├── template_colorstrip.txt
    ├── template_heatmap.txt
    ├── template_style.txt
    └── template_symbols.txt
```

---

## Key Testing Points by Layer

### API layer (`api/`)

| File | Target under test | Key testing points |
|---|---|---|
| `test_client.py` | `pyitol.api.client` | `ITOLAPIClient` initialization (key / file / missing), upload success and failure, export (including DPI), batch and single deletion, the `upload_and_export` combined call, status queries, response parsers |
| `test_error_translation.py` | `pyitol.utils.reporter` | how `translate_itol_api_error` translates keyword / common / unknown errors |

### CLI command layer (`cli/`)

| File | Target under test | Key testing points |
|---|---|---|
| `test_main.py` | `pyitol.cli.main` | the `validate` command, and `replay` over **all template types** (including the success / skipped / failure paths) |
| `test_task.py` / `test_task_run.py` | `pyitol.cli.task_cmd` | upload / export / upload-and-export / delete (interactive / confirmation) / status / task run configuration-file mode |
| `test_taxonomy.py` / `test_taxonomy_style.py` | `pyitol.cli.taxonomy_cmd` | each action of ranks / extract / extract-stats / monophyly / convert-binary / convert-connect / style |
| `test_template_*.py` | `pyitol.cli.template_cmd` / `template_advanced` / `template_datasets` / `template_tools` / `template_treeops` | generation through the unified `template create` entry point for **30+ template types**, aliases, error tolerance, bundle, validate, tree-operation types |
| `test_tree.py` | `pyitol.cli.tree_cmd` | `tree info`, `tree format-support-values` |
| `test_utils.py` | `pyitol.cli.utils_cmd` | tree-info / search-tree-file / taxonomy-parse / wide-to-long / long-to-wide / count-to-tree / group-columns / binary / connections / preview / df-tree / learn-template |
| `test_learn.py` | `pyitol.cli.learn_cmd` | learn template (single / multiple files), learn palette, learn train-theme |
| `test_common.py` | `pyitol.cli.common` | common utilities such as output formatting and argument validation |
| `test_apps.py` | `pyitol.cli.apps` | sub-application registration |
| `test_config.py` | `pyitol.cli.config_cmd` | the config command |

### Core module layer (`core/`)

| File | Target under test | Key testing points |
|---|---|---|
| `test_parser.py` | `pyitol.core.parser` | Newick / Nexus parsing, automatic detection, tip/node counting, depth, support-value format detection (IQ-TREE/raxml/posterior), `write_newick`, metadata TSV/CSV/Excel parsing, column type detection, tree-metadata consistency, `format_support_values` |
| `test_taxonomy.py` | `pyitol.core.taxonomy` | `extract_taxonomy_from_tip_names` (GTDB/embedded/NCBI/mixed/auto), `parse_taxonomy_string`, `check_monophyly`, `get_ranks` |
| `test_validator.py` | `pyitol.core.validator` | color validation, delimiter conflicts, `detect_file_type` (tree / sequence / table / content detection), the full `TemplateValidator` lifecycle, `validate_inputs` |
| `test_monophyly.py` | `pyitol.core.monophyly` | the various scenarios of monophyly detection |
| `test_binary_convert.py` / `test_connect_convert.py` / `test_column_group.py` / `test_count_tree.py` | the corresponding core conversion modules | binarization / connection conversion / column grouping / count-to-tree |

### Template module layer (`templates/`)

| File | Target under test | Key testing points |
|---|---|---|
| `test_generator.py` | `pyitol.templates.generator` | the `TemplateGenerator` engine, end-to-end generation of **all 30+ `generate_*_template()` functions** |
| `test_learner.py` | `pyitol.templates.learner` | `HEADER_REVERSE` completeness, reverse parsing of a single template, `train_theme` (empty / single / multi-file aggregation / JSON serialization / error tolerance) |
| `test_presets.py` | `pyitol.templates.presets` | all schema presets, unknown-preset errors, the Nature/Cell/Colorblind palettes, colorblind friendliness |
| `test_schemas_*.py` | `pyitol.templates.schemas.*` | completeness of the base / annotations / datasets_simple / datasets_advanced / presets / tree_structure schemas |
| `test_base.py` | `pyitol.templates.schemas.base` | the base schema classes (`TemplateSchema` / `LegendConfig` / `create_schema`) |
| `test_domain_exceptions_regression.py` | `pyitol.templates.generator` / `presets` | domain exception regression: confirms InvalidColumnError/TemplateError/TemplateTypeError instead of a bare ValueError |

### Utility module layer (`utils/`)

| File | Target under test | Key testing points |
|---|---|---|
| `test_color_tools.py` | `pyitol.utils.color_tools` | color distance, similarity ranking, gradient generation, taxonomy coloring, palette cycling |
| `test_data_converters.py` | `pyitol.utils.data_converters` | binarization, connections, wide-long conversion, count-to-tree, group_columns, df_tree |
| `test_fasta.py` | `pyitol.utils.fasta` | `fa_read` / `fa_write` / `fa_iter`, error tolerance |
| `test_io.py` | `pyitol.utils.io` | `search_tree_file` / `find_first_tree_file`, tolerance for empty directories |
| `test_session.py` | `pyitol.utils.session` | the `SessionContext` lifecycle, command / input-output recording, sanitization of API parameters, snapshot save / load / rebuild |
| `test_reporter.py` | `pyitol.utils.reporter` | error translation and reporting |
| `test_shutdown.py` | `pyitol.utils.shutdown` | signal handling and graceful shutdown |
| `test_tree_info.py` | `pyitol.utils.tree_info` | `extract_tree_info`, `get_node_count`, `get_tip_order`, `get_tree_info` |

### Top-level topic tests

| File | Key testing points |
|---|---|
| `test_concurrency.py` | concurrency and thread-safety scenarios |
| `test_exceptions.py` | the exception class hierarchy and inheritance |

---

## Running the Tests

```bash
# exactly what CI runs (see `.github/workflows/ci.yml`); the
# `-m "not integration"` part deselects nothing today, because no test is marked `integration`
pytest tests/ --cov=pyitol --cov-report=xml -m "not integration"

# run a specific layer
pytest tests/core/ -v
pytest tests/cli/test_template_create.py -v

# generate a coverage report (`addopts` in pyproject.toml already appends
# --cov=pyitol --cov-fail-under=80, so the run fails below 80% coverage)
pytest tests/ -m "not integration" --cov=pyitol --cov-report=html
```

### Test Markers

The pytest markers registered in `pyproject.toml`:

- `integration` — declared for tests that would need real iTOL API credentials, but **no test currently carries `@pytest.mark.integration`**, so the CI expression `-m "not integration"` deselects nothing and every test under `tests/` is collected and run
- `slow` — registered in `pyproject.toml` but unused today: no `@pytest.mark.slow` appears anywhere in `tests/`
- `stress` — registered in `pyproject.toml` but unused today: no `@pytest.mark.stress` appears anywhere in `tests/`
- `concurrency` — the only marker actually applied today: it decorates the two concurrent-upload tests of `TestUploadConcurrency` in `test_concurrency.py`

### Optional Dependencies

Some tests require optional dependencies (declared under `[project.optional-dependencies]` in `pyproject.toml`):

- the `excel` extra (`openpyxl`): `tests/core/test_parser.py::TestMetadataParser::test_parse_excel` tests Excel parsing. It calls `pytest.importorskip("openpyxl")` first, so when `openpyxl` is not installed the test is reported as skipped rather than failed.
- the `memory` extra (`psutil`): memory-monitoring related functionality.

To install all optional dependencies: `pip install -e ".[dev,memory,excel]"`

---

## Design Principles

1. **Single responsibility**: each test file corresponds to one source module or one CLI command group, avoiding cross-module coupling.
2. **Layer correspondence**: the `tests/` subdirectories map one-to-one onto the `src/pyitol/` package structure (`api/` / `cli/` / `core/` / `templates/` / `utils/`).
3. **Shared fixtures**: `conftest.py` centrally manages commonly used test data (tree files, taxonomy tables, API keys), eliminating fixtures duplicated across files.
4. **Mocked external dependencies**: every API call mocks the HTTP request with `unittest.mock.patch`, so the suite runs offline.
5. **Boundary coverage**: besides the happy paths, every module includes tests for empty input, missing files, illegal arguments and out-of-range values.
6. **No redundancy**: the duplicated `test_cli_template_highlight.py` (merged into `test_template_create.py`) and `test_dataset_style.py` (merged into `test_generator.py`) have been deleted.
