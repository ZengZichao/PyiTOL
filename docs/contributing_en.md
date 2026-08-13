# Contributing Guide

Thank you for your interest in PyiTOL! Below is the guide for participating in project development.

## Project Structure

```
src/pyitol/
├── cli/                    # CLI entry (split into submodules)
│   ├── main.py             # Main entry + validate/replay
│   ├── common.py           # Common helper functions
│   ├── apps.py             # Typer app definitions
│   ├── config_cmd.py       # config subcommand
│   ├── template_cmd.py     # template subcommand
│   ├── taxonomy_cmd.py     # taxonomy subcommand
│   ├── task_cmd.py         # task subcommand
│   ├── tree_cmd.py         # tree subcommand
│   ├── utils_cmd.py        # utils subcommand
│   └── learn_cmd.py        # learn subcommand
├── core/                   # Core logic
│   ├── parser.py           # Tree file/metadata parsing
│   ├── taxonomy.py         # Taxonomy extraction
│   ├── monophyly.py        # Monophyly detection
│   ├── validator.py        # Conflict detection
│   ├── binary_convert.py   # Binary data conversion
│   ├── connect_convert.py  # Connection pair conversion
│   ├── count_tree.py       # Count-data tree building
│   └── column_group.py     # Annotation column grouping
├── templates/              # Template engine
│   ├── generator.py        # Template generator
│   ├── learner.py          # Template reverse parser
│   ├── schemas/            # Schema definitions
│   │   ├── base.py         # Unified entry
│   │   ├── tree_structure.py
│   │   ├── annotations.py
│   │   ├── datasets_simple.py
│   │   └── datasets_advanced.py
│   ├── presets/            # Preset style library
├── api/                    # iTOL API wrapper
│   └── client.py           # API client
└── utils/                  # Utility functions
    ├── color_tools.py
    ├── io.py
    ├── data_converters.py
    ├── session.py
    ├── tree_info.py
    └── reporter.py
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Code Conventions

- All CLI parameters use the `--long-flag` format
- Maintain backward-compatible import paths
- New commands must be accompanied by corresponding tests

## Random Process Note

**This project does not contain any random algorithms or random processes.** All outputs (including color assignment, tree parsing, and template generation) are deterministic. Therefore, there is no need to set random seeds, and there is no randomness risk regarding result reproducibility.
