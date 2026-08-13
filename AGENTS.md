# PyiTOL Agent Guide

## Project Overview

PyiTOL is a Python CLI tool for automating iTOL (Interactive Tree Of Life) phylogenetic tree visualization. The main package is located in `src/pyitol/`, with the entry point being the `pyitol` command or `python -m pyitol`.

## Code Structure

- `src/pyitol/api/` — iTOL HTTP API client
- `src/pyitol/cli/` — Typer command-line interface
- `src/pyitol/core/` — Tree parsing, taxonomy, monophyly, input validation
- `src/pyitol/templates/` — iTOL v7 template generation and reverse parsing
- `src/pyitol/utils/` — Logging, session, color, I/O and other utilities
- `tests/` — pytest test suite

## Common Commands

```bash
# Development installation
pip install -e ".[dev]"

# Run tests (skipping integration tests that require a real iTOL API key)
pytest tests/ -m "not integration"

# Run self-test
pyitol self-test

# Code checking and formatting
ruff check src/ tests/
ruff format src/ tests/
```

## Code Conventions

- Follow PEP 8, with a line width of 120 characters
- All public functions require type hints and docstrings
- Error messages prefer Chinese, with English as fallback
- Maintain deterministic behavior and avoid randomized algorithms

## Version Notes

`pyproject.toml` uses `setuptools_scm` to dynamically generate versions; when not in a git repository, it falls back to version `1.0.0`. `src/pyitol/__init__.py` first attempts to read the version from `_version.py`, falling back to `1.0.0` on failure.
