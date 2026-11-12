# Troubleshooting Guide

[中文](troubleshooting.md) | English

## Installation Issues

### `pip install pyitol` fails
- Ensure the Python version is >= 3.10
- If installing dendropy fails, try installing first: `pip install setuptools>=68.0`

### Import error `ModuleNotFoundError: No module named 'pyitol'`
- If installed via `pip install -e .`, confirm you are running the command in the installation directory
- Check whether the correct virtual environment is activated

## API-Related Issues

### `ValueError: No API key provided`
- Pass it in via a command-line parameter: `pyitol task upload --api-key YOUR_KEY`
- Set an environment variable: `export ITOL_API_KEY=YOUR_KEY`
- Create a `.itolapi.key` file in the current directory containing the plain-text API Key
- Ensure the API Key file permissions are secure: `chmod 600 .itolapi.key`

See [API Usage Guide](api_en.md#api-key-configuration) for details.

### Upload fails `Upload failed with status 403`
- The API Key may have expired or been restricted; please log in to your iTOL account to check
- Confirm the network can access `https://itol.embl.de`

### Export timeout
- Large file exports may take longer; increase the wait time via `--wait`
- If timeouts occur frequently, check whether the resolution/dimensions are set too large: `task upload-and-export` uses `--dpi`, `--width`, `--height`; `task export` has no such options, so they must be given as `--parameter dpi=300`, `--parameter width=2400`, etc.

## Template Generation Issues

### `Column 'xxx' not found`
- Check that the `--column` parameter exactly matches the column name in the taxonomy table (case-sensitive)
- Use `--id-column` to specify the correct ID column; the default is `id`

### Colors not displayed or displayed incorrectly
- Confirm the color format is correct: `#RRGGBB`, `rgb(r,g,b)`, `hsl(h,s,l)`, or a named color (such as `red`)
- When a categorical variable exceeds 7 values, it is recommended to use `--palette colorblind` to select a colorblind-friendly palette

### Separator conflict warning
- If data values contain commas, spaces, or tabs, use `--separator` to switch to a non-conflicting separator
- For example, when the data contains commas, use `--separator TAB`

## Tree File Issues

### Tree file parsing failure

> Note: the E-series descriptions in `src/pyitol/utils/reporter.py` and the default wording of the validation (V-code) messages in `src/pyitol/core/validator.py` are Chinese (the E-series labels themselves are Python exception names and stay in English), but not every line of terminal output is translated: the exception text and file paths printed at `src/pyitol/cli/main.py:1216,1241` stay in English, and tree-content messages such as `src/pyitol/core/validator.py:965,1058` are English-only. `_ERROR_MESSAGES` contains both a Chinese and an English table; the runtime language is thread-local and defaults to Chinese, and an unknown or missing language falls back to Chinese rather than English (`src/pyitol/core/validator.py:158-180`), while the iTOL API error translation table in `src/pyitol/utils/reporter.py` is Chinese-only. The error strings quoted in backticks inside the headings of this section correspond to what the terminal actually prints, and the untranslated English messages described above are kept as-is; the rest of each heading only describes the symptom.

- Ensure the file is in valid Newick or Nexus format
- Check that parentheses are balanced and node labels do not contain illegal characters
- Overly long comments may cause format misjudgment; removing unnecessary comments is recommended

### Monophyly detection error `Null leafset bitmask`
- Usually because the specified taxon has no matching members in the tree at all
- Check that the IDs in the taxonomy exactly match the tip labels in the tree file

## Performance Issues

### Large datasets process slowly
- For trees with 10,000+ nodes, it is recommended to filter the taxonomy table in advance to keep only IDs present in the tree
- When batch-generating multiple templates, you can use the unified `pyitol template create` command to reduce repeated I/O

## Getting Help

If the above methods do not resolve the issue, please:
1. View the complete CLI help: `pyitol --help` or `pyitol <command> --help`
2. Check the [API documentation](api_en.md) and [CLI documentation](cli_en.md)
3. Submit an Issue in the project, attaching the complete error output and a sample of the input file
