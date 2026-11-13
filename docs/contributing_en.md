# Contributing Guide

English | [中文](contributing.md)

> This is the documentation-site version. Its content is kept in sync with the repository-root `CONTRIBUTING.md`; edit both together to avoid drift.

Thank you for your interest in contributing to PyiTOL!

## Getting Started

1. Fork the repository and clone your fork
2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run the test suite to verify your setup (skipping integration tests that require a real iTOL API key):
   ```bash
   pytest tests/ -m "not integration"
   ```

## Development Setup

**Prerequisites:**
- Python 3.10 or later
- Git

**Setup steps:**

```bash
# Clone your fork
git clone https://github.com/ZengZichao/PyiTOL.git
cd PyiTOL

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Project Structure

```
src/pyitol/
├── __main__.py             # python -m pyitol entry point
├── exceptions.py           # Exception hierarchy shared by all packages
├── api/                    # iTOL REST client
│   └── client.py           # Upload / query / export / delete over one requests.Session; the HTTPS adapter retries 429/5xx POSTs and GETs with capped exponential backoff
├── cli/                    # CLI entry points (Typer-based)
│   ├── apps.py             # Typer app definitions for the command groups
│   ├── main.py             # Main entry + validate/replay/self-test
│   ├── common.py           # Shared CLI utilities
│   ├── template_cmd.py     # Template commands aggregator (re-exports submodules)
│   ├── template_tools.py   # Unified create/bundle/validate commands
│   ├── template_datasets.py # Dataset template commands (create-xxx)
│   ├── template_treeops.py # Tree structure commands (create-xxx)
│   ├── template_advanced.py # Advanced template commands (create-xxx, incl. external-shape-bubble)
│   ├── task_cmd.py         # Task commands (upload/export/delete)
│   ├── taxonomy_cmd.py     # Taxonomy commands
│   ├── tree_cmd.py         # Tree info commands
│   ├── config_cmd.py       # Config file management commands
│   ├── utils_cmd.py        # Utility commands
│   └── learn_cmd.py        # Learn/reverse-engineer commands
├── core/                   # Core logic
│   ├── parser.py           # Tree/metadata parsing
│   ├── taxonomy.py         # Taxonomy extraction
│   ├── monophyly.py        # Monophyly detection
│   ├── validator.py        # Input validation, error codes and their messages
│   ├── binary_convert.py   # Taxonomy columns -> binary matrix
│   ├── connect_convert.py  # 0/1 matrix -> connection pairs
│   ├── column_group.py     # Data column grouping
│   └── count_tree.py       # Count data -> tree format
├── templates/              # Template engine
│   ├── generator.py        # Template generator (32 type-specific generate_* writers + generate_template)
│   ├── learner.py          # Reverse parser (template file -> structured dict)
│   ├── schemas/            # Schema classes (base, annotations, datasets_simple, datasets_advanced, tree_structure) + presets.py
│   └── presets/            # Color palettes (nature, cell, colorblind)
└── utils/                  # Utility functions
    ├── session.py          # Session snapshots
    ├── reporter.py         # iTOL API error translation (Chinese only)
    ├── color_tools.py      # Color utilities
    ├── constants.py        # Shared constants
    ├── logger.py           # Logging
    ├── fasta.py            # FASTA parsing
    ├── io.py               # File discovery, path handling, safe encoding
    ├── tree_info.py        # Tree topology / support-value stats
    ├── data_converters.py  # Data set conversion helpers
    └── shutdown.py         # Graceful shutdown
```

Every directory also has an `__init__.py`; `src/pyitol/` additionally contains `py.typed` and the setuptools_scm-generated `_version.py`. There is **no** `parser.py` under `templates/`; all reverse parsing lives in `templates/learner.py`.

## Code Standards

- **Linting**: PEP 8 enforced by `ruff` (`ruff check`) and `ruff format`, line length 120
- **Type hints**: Required for all function signatures and return types. This is actually enforced by ruff's `ANN` rule series (`select` in `[tool.ruff.lint]` of `pyproject.toml`), with `src/pyitol/cli/*` currently exempting `ANN001`/`ANN201`/`ANN202` among other `ANN` codes and `tests/**` exempting all of `ANN`. `mypy` (`[tool.mypy]`) only checks type consistency and does not enable `disallow_untyped_defs`
- **Docstrings**: All public functions and classes must have docstrings
- **Comments and docstrings**: Write in English. Chinese/English text is reserved for *user-facing* messages (CLI help, validation error strings from `core/validator.py`, iTOL API error translations from `utils/reporter.py`, log output), not for developer-facing code documentation.
- **CLI flags**: Every option exposes a long `--flag` name, and none is short-only; frequently used options additionally declare a short alias, whose meaning is command-specific — `-o` is `--output` almost everywhere (only `template bundle` uses `--output-dir`), while `-t` is `--taxonomy` on `taxonomy monophyly`, `--template` on `template validate` and `--tree` on the top-level `validate` command, and `-c` is `--config` at the global level, `--column` under `template create`, `--columns` under `template create-heatmap` and `--connections` under `template create-connections`
- **Error messages**: Validation messages come from `_ERROR_MESSAGES` in `src/pyitol/core/validator.py`, which keeps a Chinese and an English variant per error code. Chinese is both the default and the fallback language: the active language is thread-local (default `zh`), an unknown language key resolves to the Chinese table, and `set_error_language()` accepts only `zh`/`en`. iTOL API error text, by contrast, is translated into Chinese only (`src/pyitol/utils/reporter.py`). Nothing in the package calls `set_error_language()`, and neither the CLI options nor the config file expose a language switch, so command-line users always get the Chinese texts; see `error_codes_en.md`.

### Fix-tag legend

Comments under `src/pyitol` still carry traceability markers from historical QA review rounds. A full census of the current code (`grep -rhoE "\b(C|M|H|L|P|R)[0-9]+\b" src/pyitol --include="*.py"`, plus the lowercase `m[0-9]+` series) shows that only the following families actually exist:

- **C1**-**C5**: correctness fixes in the monophyly classification of `core/monophyly.py` (strict paraphyly vs. polyphyly separation, clearing stale tip-index caches, polytomy handling, per-tree locks and the descendant cache)
- **H1**, **H3**: iTOL protocol and numeric-encoding consistency notes (iTOL offers no official "tree ready" status endpoint; the `SYMBOL_SHAPE_MAP` and `EXTERNAL_SHAPE_MAP` encodings must not be mixed)
- **M1** plus the lowercase **m2**-**m5**, **m9**: small one-off review fixes (URL parsing, extraction of a shared schema-detection helper, thread-local language state, a larger CSS named-color table, removal of the insecure `http://` mount)
- **L9**, **L10**: boilerplate consolidation in `templates/generator.py` (a single shared schema write-out path) and shared map consistency
- **P1-x**, **P2-x**: review items numbered by priority (P1 ahead of P2); the actual IDs are `P1-7`...`P1-12`, `P1-17`, `P2-26`, `P2-29`, with `P1-xx` marking items of the same batch that were never individually numbered

The following values do not exist in the code and must not be cited: there is no `R*` series at all, and `M2`-`M7`, `H2`/`H4`, `L3`-`L8`, `L11`-`L12` and `P3` have no matching tag either. Two look-alikes are not fix tags: the `V001`-`V024` members of `ErrorCode` in `core/validator.py` are validation error codes (see `error_codes_en.md`), and the "C0/C1 range" in a `core/validator.py` comment denotes Unicode control-character ranges; the lone `V3` in `core/monophyly.py` is a leftover from an older numbering.

New contributions should not add new tags of this kind; describe the change directly in the comment and in the CHANGELOG instead.

Run the linter before submitting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

### Toolchain & Quality Gates

PyiTOL's local gates do not cover everything CI checks: `pre-commit` mirrors only the two ruff gates, while `mypy`, `pyitol self-test` and the test suite run in CI only:

- **pre-commit** (`.pre-commit-config.yaml`): defines exactly two hooks, `ruff` (with `--fix`) and `ruff-format`; both run on every commit.
- **ruff / ruff-format**: linting and formatting with a line length of 120; CI runs `ruff check src/ tests/` and `ruff format --check src/ tests/`.
- **mypy**: static type checking of `src/pyitol` (configuration in `[tool.mypy]` of `pyproject.toml`). It is **not** a pre-commit hook — CI runs `mypy src/pyitol` as a separate step (`.github/workflows/ci.yml`), so run it locally yourself before pushing.
- **pytest**: the CI test command is `pytest tests/ --cov=pyitol --cov-report=xml -m "not integration"`, executed across the Python matrix **3.10, 3.11, 3.12, 3.13** on Ubuntu, macOS and Windows; the coverage report is uploaded to Codecov only from the Python 3.12 / Ubuntu job. In addition, `[tool.pytest.ini_options] addopts` in `pyproject.toml` already passes `--cov=pyitol --cov-fail-under=80`, so a plain `pytest` run enforces the coverage gate too.

Install and run the hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Commit Message Convention

This project follows [Conventional Commits](https://www.conventionalcommits.org/). Use the format `<type>(<scope>): <summary>`, where `<type>` is one of:

- `feat`: a new feature
- `fix`: a bug fix
- `docs`: documentation-only changes
- `test`: adding or updating tests
- `refactor`: code changes that neither add a feature nor fix a bug
- `chore`: maintenance, tooling, or release changes

The scope is optional and names the affected area (e.g. `api`, `core`, `templates`, `cli`). In the examples below the leading `feat` line is an illustrative, convention-compliant subject (the current commit history contains no `feat` commits); the other three are taken from real commits:

```
feat(cli): add create-external-shape-bubble subcommand
fix(core,api): reject duplicate tip labels; warn on retried POST uploads
docs: add PyiTOL bioRxiv preprint citation
chore(release): prepare v1.0.3 (version bump, changelogs, pending DOI)
```

## Testing Requirements

All new code must include tests. The project uses `pytest`.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=pyitol --cov-report=term-missing

# Run specific module tests
pytest tests/core/test_monophyly.py -v

# Skip integration tests (require real iTOL API key)
pytest tests/ -m "not integration"
```

**Coverage gate**: Code coverage **must be at least 80%**. This is a hard gate enforced by CI through `--cov-fail-under=80` in `pyproject.toml`; a pull request that lowers coverage below 80% will fail.

**Test layout convention**: tests are grouped by area under `tests/<area>/test_<feature>.py`, for example `tests/core/test_monophyly.py`.

## Adding a New iTOL Template Type

PyiTOL exposes the unified entry point `pyitol template create <type>` for **33 template types**, plus **34 dedicated `pyitol template create-*` subcommands** (the 33 above together with the `external-shape-bubble` variant). To add support for a new type:

1. **Define the template name** in the matching submodule under `src/pyitol/templates/schemas/` (`datasets_simple.py`, `datasets_advanced.py`, `tree_structure.py`, `annotations.py`): decorate the schema class with `@register_template` so it lands in `SCHEMA_MAP` in `schemas/base.py`, which is what makes `create_schema("<type>", ...)` validate the template's parameters.

2. **Implement generation logic** in `src/pyitol/templates/generator.py`. The writers there are **module-level functions, not methods**: add a `generate_<type>_template()` following the existing ones (e.g. `generate_binary_template`, `generate_color_strip_template`), building the schema via `create_schema()` and writing it out through `_write_schema_file()`.

3. **Add CLI command** in the appropriate CLI module under `src/pyitol/cli/`:
   - Dataset templates (color-strip, heatmap, bar, pie, symbols, etc.) go in `template_datasets.py`
   - Tree operation templates (tree-colors, collapse, prune, spacing, highlight, style, etc.) go in `template_treeops.py`
   - Advanced templates (linechart, image, alignment, tanglegram, placement, timescale, meme, manual, external-shape-bubble) go in `template_advanced.py`

4. **Register the alias** in the `template_tools.py` dispatch table by decorating the handler with `@_register_create("<type>", "<alias>", ...)` so that `pyitol template create <type>` also routes to the new generator.

5. **Add tests** in `tests/` covering:
   - Template generation with valid inputs
   - Edge cases (empty data, missing fields)
   - Output format validation

6. **Update documentation** and add an example if applicable.

## Deterministic Behavior

**This project contains no random algorithms or stochastic processes.** All outputs (color assignment, tree parsing, template generation) are deterministic. No random seed configuration is needed.

## Pull Request Process

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with tests. Keep commits focused and follow the Commit Message Convention above.

3. **Verify before submitting**:
   ```bash
   # All tests pass
   pytest tests/ -v

   # Linter passes
   ruff check src/ tests/

   # Type hints checked by mypy (configuration in [tool.mypy] of pyproject.toml)
   mypy src/pyitol/
   ```

4. **Submit a pull request** with:
   - A clear description of what changed and why
   - Reference to the related issue (if applicable)
   - Updated CHANGELOG entry (for user-facing changes)

5. **Respond to review feedback**. A maintainer will review your PR within a reasonable timeframe.

## Code of Conduct

This project follows the Contributor Covenant Code of Conduct (see `CODE_OF_CONDUCT.md` at the repository root, and its Chinese translation `CODE_OF_CONDUCT_CN.md`).
