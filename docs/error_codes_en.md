# PyiTOL Error Codes Reference

## Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Operation completed normally |
| 1 | Runtime Error | Internal error, dependency issue, API failure, connection/timeout/permission error |
| 2 | Parameter Error | Invalid CLI parameters, validation failure, ValueError |
| 3 | Data Error | Input file format/content error, template error, file not found |
| 130 | User Interrupt | Received SIGINT (Ctrl+C) |

Exit codes are mapped by the `main()` function in `src/pyitol/cli/main.py` based on exception types; see the exception handling logic for details.

## Structured Error Codes

PyiTOL defines 55 structured error codes (E001–E055) in the `ERROR_CODE_TABLE` of `src/pyitol/utils/reporter.py`. Each error code corresponds to an exception class and a user-friendly error description.

### Basic Errors (E001–E015)

| Code | Exception Class | Description |
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
| E010 | SeparatorConflictError | Delimiter conflict: an illegal delimiter is used in the data. |
| E011 | MissingColumnError | Missing required column: please check that the column names in the input table are correct. |
| E012 | TaxaNotFoundError | Taxon not found: a species in the taxonomy table is not present in the tree file. |
| E013 | APIKeyError | API key error: please check the contents of the .itolapi.key file. |
| E014 | UploadError | Upload failed: the iTOL server returned an error response. |
| E015 | ExportError | Export failed: iTOL rendering did not complete or the format is not supported. |

### Extended Errors (E016–E030)

| Code | Exception Class | Description |
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

| Code | Exception Class | Description |
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

| Code | Exception Class | Description |
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
| E053 | SeparatorConflictError | Separator conflict: the data content contains the same character as the separator; please change the separator. |
| E054 | DataFormatError | Data format error: the template data section format is incorrect; please check against the iTOL v7 specification. |
| E055 | UnsupportedFormatError | Unsupported export format: please use the svg, png, or pdf format. |

## Validation Errors (V001-V024)

Validation errors are produced by `src/pyitol/core/validator.py` and do not correspond to exit codes; instead, they appear as output and warning/error messages from the `validate` command.

| Code | Level | Description |
|------|-------|-------------|
| V001 | ERROR | Color code cannot be empty |
| V002 | WARNING | Color code missing `#` prefix |
| V003 | ERROR | Invalid color code length (should be `#RRGGBB`) |
| V004 | ERROR | Invalid color code format |
| V005 | ERROR | Delimiter conflict in data |
| V006 | WARNING | High cardinality categorical variable |
| V007 | WARNING | Numeric value below biological lower bound |
| V008 | WARNING | Numeric value exceeds biological upper bound |
| V009 | WARNING | Orphan nodes: metadata IDs not in tree |
| V010 | WARNING | Missing annotations: tree nodes not in metadata |
| V011 | WARNING | Special characters in node IDs |
| V012 | ERROR | File not found |
| V013 | ERROR | File is empty |
| V014 | WARNING | File format may be incorrect |
| V015 | ERROR | Template file missing iTOL header |
| V016 | WARNING | Template file missing separator specification |
| V017 | ERROR | Parse failed |
| V018 | WARNING | Unsupported tree file format |
| V019 | WARNING | Unsupported sequence file format |
| V020 | ERROR | Invalid tree file content |
| V021 | ERROR | Invalid sequence file content |
| V022 | ERROR | Malicious characters in node names (control chars or bidi text) |
| V023 | ERROR | Circular dependency in taxonomy table |
| V024 | CRITICAL | File is empty, cannot process |

## Log Levels

| Level | Tag | Description |
|-------|-----|-------------|
| DEBUG | DBG | Detailed debug information |
| INFO | INF | Normal operation messages |
| WARNING | WRN | Warning messages (non-fatal) |
| ERROR | ERR | Error messages |
| CRITICAL | CRT | Critical error (exit immediately) |

Log format: `2025-03-21T10:15:30.123 | INFO     | message`

## Common Error Scenarios

### "Tree file not found" (E001/V012)
- Check the file path spelling
- Confirm the file exists at the specified location
- Using absolute paths is recommended

### "Multiple trees detected" (exit code 2)
- Use `--multi-tree-mode` to specify a processing strategy:
  - `ask`: prompt the user (default)
  - `first`: use only the first tree
  - `last`: use only the last tree
  - `random`: randomly select one tree
  - `split`: process all trees separately

### "Taxon is not monophyletic" (WARNING)
- The members of the taxon do not form a single clade
- Check whether the taxonomic assignment is correct
- Use `--strict` to force termination on non-monophyletic taxa

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

Example output:
```
  PyiTOL Self-Test Results
  =======================================================
  [PASS] Import typer (v0.x.x)
  [PASS] Import pandas (v2.x.x)
  [PASS] Parse sample Newick (4 tips)
  [PASS] Extract embedded taxonomy (Domain=Bacteria)
  [PASS] Monophyly detection (G1=mono, G2=mono)
  [PASS] Malicious name detection (Caught 1)
  =======================================================
  All checks passed.
```

Exit code: 0=all passed, 1=some failed
