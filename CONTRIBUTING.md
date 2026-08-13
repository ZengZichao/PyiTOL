# Contributing to PyiTOL

Thank you for your interest in contributing to PyiTOL!

## Getting Started / 开始之前

1. Fork the repository and clone your fork
2. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```
3. Run the test suite to verify your setup:
   ```bash
   pytest tests/ -v
   ```

## Development Setup / 开发环境配置

**Prerequisites / 前置条件:**
- Python 3.9 or later
- Git

**Setup steps / 配置步骤:**

```bash
# Clone your fork
git clone https://github.com/ZengZichao/PyiTOL.git
cd pyitol

# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Install pre-commit hooks (if configured)
pre-commit install
```

## Project Structure / 项目结构

```
src/pyitol/
├── cli/                    # CLI entry points (Typer-based)
│   ├── apps.py             # Typer app definitions for 7 command groups
│   ├── main.py             # Main entry + validate/replay/self-test
│   ├── common.py           # Shared CLI utilities
│   ├── template_cmd.py     # Template commands aggregator (re-exports submodules)
│   ├── template_tools.py   # Unified create/bundle/validate commands
│   ├── template_datasets.py # Dataset template commands (create-xxx)
│   ├── template_treeops.py # Tree structure commands (create-xxx)
│   ├── template_advanced.py # Advanced template commands (create-xxx)
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
│   ├── validator.py        # Input validation
│   └── ...                 # Converters, grouping, etc.
├── templates/              # Template engine
│   ├── generator.py        # Template generator (30+ types)
│   ├── learner.py          # Template reverse-parsing
│   ├── schemas/            # Schema definitions
│   └── presets/            # Color palettes (including colorblind-friendly)
├── api/                    # iTOL API client
│   └── client.py           # Upload/export/delete with retry
└── utils/                  # Utility functions
    ├── session.py          # Session snapshots
    ├── reporter.py         # Bilingual error messages
    ├── color_tools.py      # Color utilities
    └── ...                 # I/O, FASTA, tree info
```

## Code Standards / 代码规范

- **Linting**: PEP 8 enforced by `ruff`, line length 120
- **Type hints**: Required for all function signatures and return types
- **Docstrings**: All public functions and classes must have docstrings
- **Comments and docstrings**: Write in English. Bilingual (Chinese/English) text is reserved for *user-facing* messages (CLI help, error reports via `utils/reporter.py`, log output), not for developer-facing code documentation.
- **CLI flags**: All CLI parameters use `--long-flag` format
- **Error messages**: Bilingual (Chinese primary, English fallback) via `utils/reporter.py`

### Fix-tag legend / 修复标签说明

Historical QA/fix tags appear in comments across the codebase (e.g. `C1`–`C5`, `M1`–`M7`, `H2`–`H4`, `L3`–`L12`, `P1`–`P3`, `R1`–`R9`, `V3`). They are traceability markers from internal review rounds:

- **C***: core algorithm correctness fixes (e.g. monophyly classification)
- **M***: module-level bug fixes
- **H***: iTOL format/header conformance fixes
- **L***: fixes from lint/static-review rounds
- **P***: parser/performance-related fixes
- **R***: robustness/review hardening fixes
- **V***: feature additions from version milestones

New contributions should not add new tags of this kind; describe the change directly in the comment and in the CHANGELOG instead.

Run the linter before submitting:

```bash
ruff check src/ tests/
ruff format src/ tests/
```

## Testing Requirements / 测试要求

All new code must include tests. The project uses `pytest`.

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ --cov=pyitol --cov-report=term-missing

# Run specific module tests
pytest tests/test_core_monophyly.py -v

# Skip integration tests (require real iTOL API key)
pytest tests/ -m "not integration"
```

**Coverage target**: Aim for at least 80% coverage on new code.

**Test naming convention**: `tests/test_<module>_<feature>.py`

## Adding a New iTOL Template Type / 添加新iTOL模板类型

PyiTOL supports 31+ iTOL template types. To add support for a new type:

1. **Define the template name** in `src/pyitol/templates/schemas/`. Add schema validation for the template's parameters.

2. **Implement generation logic** in `src/pyitol/templates/generator.py`. Add a new method following the existing pattern (e.g., `generate_binary`, `generate_colorstrip`).

3. **Add CLI command** in the appropriate CLI module under `src/pyitol/cli/`:
   - Dataset templates (color-strip, heatmap, bar, pie, symbols, etc.) go in `template_datasets.py`
   - Tree operation templates (tree-colors, collapse, prune, spacing, highlight, style, etc.) go in `template_treeops.py`
   - Advanced templates (linechart, image, alignment, tanglegram, placement, timescale, meme, manual, external-shape-bubble) go in `template_advanced.py`

4. **Add tests** in `tests/` covering:
   - Template generation with valid inputs
   - Edge cases (empty data, missing fields)
   - Output format validation

5. **Update documentation** and add an example if applicable.

## Deterministic Behavior / 确定性行为

**This project contains no random algorithms or stochastic processes.** All outputs (color assignment, tree parsing, template generation) are deterministic. No random seed configuration is needed.

## Pull Request Process / 提交流程

1. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** with tests. Keep commits focused and well-described.

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

## Code of Conduct / 行为准则

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
