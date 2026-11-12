# PyiTOL Error Codes Reference

[中文](error_codes.md) | English

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed normally |
| 1 | Runtime Error | Internal error, dependency issue, API failure, connection/timeout/permission error |
| 2 | Parameter Error | Invalid CLI parameters, validation failure, ValueError |
| 3 | Data Error | Input file format/content error, template error, file not found |
| 130 | User Interrupt | Received SIGINT (Ctrl+C) |

Exit codes are mapped by the `main()` function in `src/pyitol/cli/main.py` based on exception types (`src/pyitol/cli/main.py:1192-1274`); individual commands may also raise `typer.Exit` directly — for example, `pyitol validate` exits with code 3 when validation errors were printed (`src/pyitol/cli/main.py:404`).

## Structured Error Codes

PyiTOL defines 55 structured error codes (E001–E055) in the `ERROR_CODE_TABLE` of `src/pyitol/utils/reporter.py`. Each entry is a two-element tuple `(label, description)` and carries no severity field — every entry is an error-type label; the table has no warning or info categories. The second column below is that first tuple element (the label string): E001–E005 are Python built-in exception names; E006–E022, E052, E054 and E055 match classes defined in `src/pyitol/exceptions.py`; the 30 labels E023–E051 and E053 have no exception class of that name anywhere in the package and are only display strings in this table (for instance E053's `DataSeparatorConflictError`, `src/pyitol/utils/reporter.py:62`). The descriptions in the code exist in Chinese only — there is no English fallback; for an unknown code `get_error_message()` returns the Chinese string "unknown error: {code}" (`src/pyitol/utils/reporter.py:150-155`), so the English descriptions below are this document's translation of the code's Chinese strings. The only reporter function actually called inside `src/pyitol/` is `translate_itol_api_error()` (imported by `src/pyitol/api/client.py:21`); `get_error_message()`, `translate_error()`, `translate_errors()` and `format_result_summary()` are exercised only by `tests/`, so `[E0NN]`-style codes are never printed by the `pyitol` command.

### Basic Errors (E001–E015)

| Code | Error label | Description |
|------|--------|------|
| E001 | FileNotFoundError | File not found: please check that the input file path is correct. |
| E002 | ValueError | Parameter error: the provided parameter value is invalid or incorrectly formatted. |
| E003 | ConnectionError | Network connection failed: please check the network or iTOL server status. |
| E004 | TimeoutError | Operation timed out: the server response took too long, please retry. |
| E005 | PermissionError | Permission error: no write permission for the target directory. |
| E006 | SchemaValidationError | Template validation failed: the template format does not conform to the iTOL v7 specification. |
| E007 | TreeParseError | Tree file parsing failed: unable to recognize the Newick/Nexus format. |
| E008 | MetadataParseError | Metadata parsing failed: the table file format is incorrect or columns do not match. |
| E009 | ColorCodeError | Invalid color code: please use a hexadecimal color value such as #ff0000. |
| E010 | SeparatorConflictError | Separator conflict: an illegal separator is used in the data. |
| E011 | MissingColumnError | Missing required column: please check that the column names in the input table are correct. |
| E012 | TaxaNotFoundError | Taxon not found: a species in the taxonomy table is not present in the tree file. |
| E013 | APIKeyError | API key error: please check the contents of the .itolapi.key file. |
| E014 | UploadError | Upload failed: the iTOL server returned an error response. |
| E015 | ExportError | Export failed: iTOL rendering did not complete or the format is not supported. |

### Extended Errors (E016–E030)

| Code | Error label | Description |
|------|--------|------|
| E016 | SessionError | Session error: unable to load or save the session snapshot, please check the file path and permissions. |
| E017 | ReplayError | Replay failed: the snapshot is missing required parameters or files, please check the session.yaml content. |
| E018 | TemplateTypeError | Template type error: unsupported template type, please check the spelling of the type name. |
| E019 | FileFormatError | Unsupported file format: please use Newick, Nexus, CSV, or Excel format. |
| E020 | FileTooLargeError | File too large: a single file or the total upload size exceeds the iTOL limit (2MB). |
| E021 | SpecialCharacterError | Special character error: the node ID contains spaces or illegal symbols; replacing them with underscores is recommended. |
| E022 | NodeIDMismatchError | Node ID mismatch: the IDs in the metadata do not match the node names in the tree file. |
| E023 | QuotaExceededError | Quota exceeded: the iTOL account has reached its tree count or storage limit; please delete old trees and retry. |
| E024 | RateLimitError | Requests too frequent: the iTOL rate limit has been triggered; please reduce the request frequency and retry. |
| E025 | ServerMaintenanceError | Server maintenance: the iTOL server is under maintenance, please retry later. |
| E026 | RenderingError | Rendering failed: the iTOL server cannot render the tree; the tree may be too complex or the dataset incompatible. |
| E027 | TreeNotFoundError | Tree not found: the specified tree_id does not exist or has been deleted; please verify and retry. |
| E028 | DuplicateTreeError | Tree already exists: a tree with the same name already exists in the iTOL account; please change the tree_name. |
| E029 | DatasetIncompatibleError | Dataset incompatible: the template format does not match the tree structure; please check the template type and data content. |
| E030 | ColumnMismatchError | Column mismatch: the number or names of columns in the input table do not match the expected values; please check the data file. |

### Network and Service Errors (E031–E040)

| Code | Error label | Description |
|------|--------|------|
| E031 | NetworkTimeoutError | Network timeout: connection to the iTOL server timed out; please check the network and retry. |
| E032 | SSLError | SSL certificate error: unable to establish a secure connection; please check the system time or proxy settings. |
| E033 | DNSLookupError | DNS resolution failed: unable to resolve the iTOL server address; please check the network configuration. |
| E034 | BadGatewayError | Bad gateway: the iTOL upstream service is abnormal; please retry later. |
| E035 | GatewayTimeoutError | Gateway timeout: the iTOL server response timed out; please retry later. |
| E036 | ServiceUnavailableError | Service unavailable: the iTOL server is currently unable to process requests; please retry later. |
| E037 | AuthenticationExpiredError | Authentication expired: the API Key has expired; please re-obtain or update the key. |
| E038 | AccountSuspendedError | Account suspended: the iTOL account has been suspended; please contact the iTOL support team. |
| E039 | AccessDeniedError | Access denied: the current API Key does not have permission to perform this operation; please check the permission configuration. |
| E040 | EmptyFileError | Empty file error: the uploaded file content is empty; please check whether the file is corrupted. |

### File and Rendering Errors (E041–E055)

| Code | Error label | Description |
|------|--------|------|
| E041 | CorruptFileError | File corrupted: the uploaded file cannot be parsed; please check the file integrity. |
| E042 | ExtensionNotAllowedError | File extension not allowed: please use a file format supported by iTOL. |
| E043 | LegendError | Legend error: the legend parameters are set incorrectly; please check the LEGEND-related configuration. |
| E044 | HeaderError | Template header error: a template header parameter is missing or malformed; please check the HEADER section. |
| E045 | CanvasTooLargeError | Canvas too large: the export dimensions exceed the iTOL limit; please reduce the dpi or width/height. |
| E046 | FontNotFoundError | Font not found: the iTOL server lacks the specified font; please use the default font. |
| E047 | ImageGenerationError | Image generation failed: iTOL cannot generate the image; please try another format. |
| E048 | TreeTooComplexError | Tree structure too complex: too many nodes or branches; simplifying the tree structure is recommended. |
| E049 | StorageFullError | Storage full: the iTOL account storage is insufficient; please delete old files. |
| E050 | MaxTreesReachedError | Maximum tree count reached: the number of trees in the iTOL account has reached the limit; please delete old trees. |
| E051 | TreeLockedError | Tree locked: the tree is currently locked and cannot be modified or deleted; please try again later. |
| E052 | InvalidColumnError | Invalid column: the specified column name does not exist in the data; please check the column name spelling. |
| E053 | DataSeparatorConflictError | Separator conflict: the data content contains the same character as the separator; please change the separator. |
| E054 | DataFormatError | Data format error: the template data section format is incorrect; please check against the iTOL v7 specification. |
| E055 | UnsupportedFormatError | Unsupported export format: please use the svg, png, or pdf format. |

Terminology note: the labels `SeparatorConflictError` and `DataSeparatorConflictError` of E010 and E053 (`src/pyitol/utils/reporter.py:18,62`) and the `ITOL_API_ERROR_TRANSLATIONS` keyword `"separator conflict"` (`src/pyitol/utils/reporter.py:99`) all use the word "separator", and the Chinese descriptions attached to those three entries likewise open with the phrase equivalent to "separator conflict"; validation code V005 is different: its constant is named `DELIMITER_CONFLICT` (`src/pyitol/core/validator.py:80`), its English text is `Delimiter conflict: row {0}, column '{1}' contains '{2}': {3}` (`src/pyitol/core/validator.py:135`), and its Chinese counterpart (`src/pyitol/core/validator.py:109`) is the same message rendered with the word equivalent to "separator" instead of "delimiter"; V005 is produced by `check_delimiter_conflict()` (`src/pyitol/core/validator.py:360-388`). These are two independent sets of strings from two modules and must not be substituted for one another.

## Validation Errors (V001-V024)

Validation messages are produced by `src/pyitol/core/validator.py`; they are not exception classes but output lines of the `validate` command. Their texts come from the bilingual dictionary `_ERROR_MESSAGES`, which has a `"zh"` and an `"en"` sub-dictionary (`src/pyitol/core/validator.py:103-156`). The default language is Chinese (`src/pyitol/core/validator.py:158-160`); the language is switched per thread by `set_error_language()` (`src/pyitol/core/validator.py:174-181`), and an unknown language falls back to Chinese, not to English (`src/pyitol/core/validator.py:166`). Nothing in the package calls `set_error_language()`, and neither the CLI options nor the config file expose a language switch, so command-line users always see the Chinese texts; the English texts are only emitted when Python code explicitly calls `set_error_language("en")`. ERROR- and CRITICAL-level messages make `pyitol validate` exit with code 3 (`src/pyitol/cli/main.py:399-404`), while the `TemplateValidationError` raised by `TemplateValidator.raise_if_errors()` maps to exit code 2 (`src/pyitol/cli/main.py:1228-1232`). The Description column below is the verbatim English message text from `_ERROR_MESSAGES["en"]`, where `{0}`, `{1}`, etc. are placeholders filled in at runtime.

| Code | Level | Description |
|------|-------|-------------|
| V001 | ERROR | Color code cannot be empty |
| V002 | ERROR | Color code missing # prefix, suggest: #{0} |
| V003 | ERROR | Invalid color code length, should be #RRGGBB (6 hex digits) |
| V004 | ERROR | Invalid color code: {0}. Use #RRGGBB, rgb(), hsl(), or named color format |
| V005 | ERROR | Delimiter conflict: row {0}, column '{1}' contains '{2}': {3} |
| V006 | WARNING | High cardinality warning: column '{0}' has {1} unique values, exceeds recommended limit {2} |
| V007 | WARNING | Numeric range warning: column '{0}' minimum {1:.2f} below biological lower bound {2} |
| V008 | WARNING | Numeric range warning: column '{0}' maximum {1:.2f} exceeds biological upper bound {2} |
| V009 | WARNING† | Orphan nodes: {0} metadata IDs not in tree file, e.g.: {1} |
| V010 | WARNING† | Missing annotations: {0} tree nodes not in metadata, e.g.: {1} |
| V011 | WARNING† | Special characters in IDs: {0} node IDs contain spaces/tabs/commas/semicolons/pipes, e.g.: {1} |
| V012 | ERROR | File not found: {0} |
| V013 | ERROR | File is empty: {0} |
| V014 | WARNING | File format may be incorrect: {0} |
| V015 | ERROR | Template file missing iTOL header identifier: {0} |
| V016 | WARNING | Template file missing separator specification: {0} |
| V017 | ERROR | Parse failed: {0} |
| V018 | WARNING | Unsupported tree file format: {0}. Supported: Newick (.nwk/.newick/.tree/.tre), Nexus (.nexus/.nex), PhyloXML (.xml) |
| V019 | WARNING | Unsupported sequence file format: {0}. Supported: FASTA (.fa/.fasta/.fna), FASTQ (.fq/.fastq), GenBank (.gb/.gbk), Phylip (.phy/.phylip) |
| V020 | ERROR† | Invalid tree file content: {0} |
| V021 | ERROR | Invalid sequence file content: {0} |
| V022 | ERROR | Node name contains malicious characters (control chars or bidi text): {0} |
| V023 | ERROR | Circular dependency detected in taxonomy table: {0} |
| V024 | CRITICAL | File is empty, cannot process: {0} |

The Level column reflects which list the code puts the message in; `pyitol validate` then prints it as `ERR` / `WARN` / `CRIT` (one exception: the file-check result of the taxonomy table is printed as `ERR` but does not set the failure flag, so on its own it does not change the exit code, `src/pyitol/cli/main.py:367-368`):

- ERROR: V001–V005, V012, V013, V015, V017, V021–V023. On a failed color check `validate_color_code()` returns `(False, message)` and `validate_color_codes()` appends it to `errors` (`src/pyitol/core/validator.py:334,350-357`), so V002 is an ERROR even though its wording is a suggestion; V005 is returned by `check_delimiter_conflict()` and merged into `self.errors` by `TemplateValidator.validate_dataframe()` (`src/pyitol/core/validator.py:1489-1491`).
- WARNING: V006, V007, V008 are merged into `self.warnings` by `validate_dataframe()` (`src/pyitol/core/validator.py:1493-1503`) — inside `check_categorical_cardinality()` the messages are collected in a local variable named `errors` (`src/pyitol/core/validator.py:397-403`), but its only caller routes them to warnings, so V006 is a WARNING. V014, V016, V018, V019 also go to `warnings` (`src/pyitol/core/validator.py:681,687,1423,1472`).
- CRITICAL: V024 is returned by `validate_file_not_empty()` and printed as `CRIT`, which also sets the failure flag (`src/pyitol/cli/main.py:283-286`).
- The † rows: V009–V011 are only returned by `check_tree_ids_against_metadata()` / `check_special_characters_in_ids()` (`src/pyitol/core/validator.py:451-494`), and those two functions are currently called only from `tests/`; the V020 template `ErrorCode.INVALID_TREE_CONTENT` (`src/pyitol/core/validator.py:95,124,150`) has no reference anywhere in the package, `tests/` included. None of these messages is emitted at runtime, so the levels above are inferred from the wording rather than from an actual code path. Tree-content failures are in fact reported with hard-coded messages that carry no V code (e.g. `Bracket mismatch: …`, `CRITICAL: Negative branch lengths detected …`, `src/pyitol/core/validator.py:942-1074`).

## Log Levels

| Level | Description |
|-------|-------------|
| DEBUG | Detailed debug information |
| INFO | Normal operation messages |
| WARNING | Warning messages (non-fatal) |
| ERROR | Error messages |
| CRITICAL | Critical error (exit immediately) |

Log levels are printed in full and right-padded with spaces to a width of 9 characters; they are never abbreviated (`src/pyitol/utils/logger.py:18-24`; an unmapped level name also uses `levelname.ljust(9)`, `src/pyitol/utils/logger.py:59`). Log format: `2025-03-21T10:15:30.123 | INFO     | message`. When `--log-file` is used, the file handler formats the level as `%(levelname)-8s`, i.e. 8 characters wide (`src/pyitol/utils/logger.py:191-193`), and DEBUG messages additionally get a `[module:lineno]` suffix (`src/pyitol/utils/logger.py:61-64`).

## Common Error Scenarios

### "Tree file not found" (E001/V012)
- Check the file path spelling
- Confirm the file exists at the specified location
- Using absolute paths is recommended

### "Multiple trees detected" (warning, handled by strategy)
- When multiple trees are detected, `load_tree()` first logs a WARNING with a per-tree summary and then applies the strategy given by its own `multi_tree` parameter; it does not necessarily exit with an error code (`src/pyitol/core/parser.py:216-249`). On the CLI only `taxonomy monophyly` and `taxonomy check-and-style` declare `--multi-tree-mode`, and neither forwards it; every other command calls the library with a hard-coded strategy:
  - `ask`: default; in a non-interactive terminal it automatically falls back to `first`, while in an interactive terminal it raises `TreeParseError` listing the available strategies (exit code 3)
  - `first`: use only the first tree
  - `last`: use only the last tree
  - `split`: process all trees separately (internal equivalent alias: `all`)

### "Taxon is not monophyletic" (WARNING)
- The members of the taxon do not form a single clade
- Check whether the taxonomic assignment is correct
- In `template create-collapse` the non-monophyletic taxon is printed as `WARN` and skipped (`src/pyitol/cli/template_treeops.py:233`); only `--strict` terminates with exit code 1 (`src/pyitol/cli/template_treeops.py:246-247`)
- In the `taxonomy` cluster operations, paraphyletic and polyphyletic taxa terminate directly with exit code 1 (`src/pyitol/cli/taxonomy_cmd.py:867-882`)

### "Duplicate sequence IDs" (ERROR)
- Rename duplicate sequences in the FASTA file
- Ensure all sequence IDs are unique

### "Negative branch lengths" (CRITICAL, exit 3)
- Re-check the tree building method
- The tree file may be corrupted

### "Malicious characters detected" (ERROR)
- Node names contain control characters or bidirectional text override characters
- Clean the input data

### "Circular dependency in taxonomy" (ERROR)
- There are conflicting entries in the taxonomy table (e.g., A→B and B→A)
- Check the consistency of taxonomic assignments

### "Empty file" (CRITICAL)
- The input file size is 0 bytes
- Check whether the file was transferred/created correctly

### "No API key provided" (E013)
- Pass it in via the command line `--api-key`
- Set the environment variable `ITOL_API_KEY`
- Create a `.itolapi.key` file containing the plain-text API Key
- Ensure the key file permissions are secure: `chmod 600 .itolapi.key`

## Self-Test Mode

```bash
pyitol self-test
```

`pyitol self-test` runs 20 checks in total: 8 dependency libraries + 8 internal modules + 4 functional checks (`src/pyitol/cli/main.py:1033-1184`). Example output (the version numbers in parentheses reflect what is actually installed):
```
  PyiTOL Self-Test Results
  =======================================================
  [PASS] Import typer (v0.x.x)
  [PASS] Import rich (v0.x.x)
  [PASS] Import pandas (v2.x.x)
  [PASS] Import dendropy (v4.x.x)
  [PASS] Import pydantic (v2.x.x)
  [PASS] Import PyYAML (v6.x.x)
  [PASS] Import requests (v2.x.x)
  [PASS] Import numpy (v1.x.x)
  [PASS] Import parser
  [PASS] Import taxonomy
  [PASS] Import monophyly
  [PASS] Import validator
  [PASS] Import generator
  [PASS] Import io
  [PASS] Import logger
  [PASS] Import shutdown
  [PASS] Parse sample Newick (4 tips)
  [PASS] Extract embedded taxonomy (Domain=Bacteria)
  [PASS] Monophyly detection (G1=mono, G2=mono)
  [PASS] Malicious name detection (Caught 1)
  =======================================================
  All checks passed.
```

Exit code: 0=all passed, 1=some failed
