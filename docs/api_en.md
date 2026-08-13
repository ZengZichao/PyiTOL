# PyiTOL API Usage Guide

PyiTOL wraps iTOL's three batch API endpoints, supporting automatic retry, error translation, and multi-format export.

## API Endpoints

| Endpoint | Function | PyiTOL Command |
|------|------|------------|
| `https://itol.embl.de/batch_uploader.cgi` | Upload tree files + templates | `pyitol task upload` |
| `https://itol.embl.de/batch_downloader.cgi` | Export rendered images | `pyitol task export` |
| `https://itol.embl.de/batch_delete.cgi` | Delete uploaded trees | `pyitol task delete` |

## API Key Configuration

Three methods are supported (in descending order of priority):

### Method 1: Command-line parameter

```bash
pyitol task upload --tree tree.nwk --api-key YOUR_API_KEY
```

### Method 2: Environment variable

```bash
export ITOL_API_KEY=YOUR_API_KEY
pyitol task upload --tree tree.nwk
```

### Method 3: Key file

Create a `.itolapi.key` file in the project directory and write the plain-text API Key into it:

```bash
echo "YOUR_API_KEY" > .itolapi.key
chmod 600 .itolapi.key
```

Or specify a custom path:

```bash
pyitol task upload --tree tree.nwk --api-key-file /path/to/.itolapi.key
```

> **Security note**: PyiTOL checks the key file permissions and issues a warning if group/other have read or write permissions. It is recommended to use `chmod 600 .itolapi.key`.

## task Command Overview

| Command | Description |
|------|------|
| `pyitol task upload` | Upload trees and templates to iTOL |
| `pyitol task export` | Export rendered images from iTOL |
| `pyitol task upload-and-export` | Upload and export (in one step) |
| `pyitol task delete` | Delete uploaded trees |
| `pyitol task status` | Query the status of a tree |
| `pyitol task run` | Run a configuration file (single config or batch list) |

## Upload Workflow

### Basic Upload

```bash
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt \
  --dataset-name MyTree
```

### Multi-template Upload

```bash
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt \
  --config bars.txt \
  --config heatmap.txt \
  --dataset-name MyTree
```

PyiTOL automatically packages multiple template files into a zip for upload.

### Auto-export After Upload

```bash
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt \
  --output result.svg --format svg --wait 60
```

`--wait` specifies the maximum time (in seconds) to wait for iTOL rendering; the command fails after timeout.

## Export Control

### Supported Formats

PyiTOL supports 8 export formats:

| Format | Description | Extra Parameters |
|------|------|---------|
| `svg` | Vector graphic (recommended) | |
| `png` | Bitmap image | `--dpi` |
| `pdf` | Document | `--dpi` |
| `tiff` | TIFF image | `--dpi` |
| `eps` | Encapsulated PostScript | `--dpi` |
| `newick` | Newick tree format | |
| `nexus` | Nexus tree format | |
| `phyloxml` | PhyloXML format | |

### Export Dimensions

```bash
pyitol task export \
  --upload-id TREE_ID \
  --download ./output \
  --format png \
  --parameter dpi=300 \
  --parameter width=2400 \
  --parameter height=1600
```

Supported dimension parameters: `--dpi`, `--width`, `--height`.

## Delete Operation

```bash
# Delete a single tree
pyitol task delete --upload-id TREE_ID

# Batch delete
pyitol task delete --upload-id ID1 --upload-id ID2
```

## Status Query

```bash
pyitol task status --upload-id TREE_ID
```

## Batch Operations

### Batch Upload/Export (Configuration File)

`pyitol task run` supports executing batch tasks via YAML/JSON configuration files. The configuration file is in list format, with each item specifying the operation to perform via the `command` field.

Supported `command` values: `upload`, `export`, `extract`, `monophyly`, `convert-binary`, `convert-connect`, `template`.

Create `batch.yaml`:

```yaml
- command: upload
  tree: tree1.nwk
  configs: [colors1.txt, bars1.txt]
  api_key: YOUR_KEY
  name: Tree1
- command: upload
  tree: tree2.nwk
  configs: [colors2.txt]
  api_key: YOUR_KEY
  name: Tree2
- command: export
  upload_id: TREE_ID_1
  download: ./output
  parameters:
    format: svg
    dpi: 300
```

Execute:

```bash
# Batch execute a list
pyitol task run --config-list batch.yaml

# Single config execution
pyitol task run --config single_workflow.yaml
```

Single configuration file example `single_workflow.yaml`:

```yaml
command: upload
tree: tree.nwk
configs: [colors.txt, bars.txt]
api_key: YOUR_KEY
name: MyTree
```

## Error Handling

PyiTOL has a built-in iTOL API error translation table that converts English error messages into user-friendly suggestions:

| iTOL Error Keyword | PyiTOL Translation |
|----------------|------------|
| `invalid api key` | Invalid API Key: please check the --api-key parameter or the .itolapi.key file |
| `file too large` | File too large: iTOL limits the total upload size to no more than 2MB |
| `tree format` | Tree file format error: please ensure the file is in standard Newick or Nexus format |
| `rate limit` | Requests too frequent: please retry later |
| `rendering` | Rendering failed: iTOL server rendering timed out |

For the complete error code table, see [Error Codes Reference](error_codes.md) or `src/pyitol/utils/reporter.py`.

## Network Retry

The API client has a built-in exponential backoff retry strategy:
- Automatically retries HTTP 429, 500, 502, 503, 504
- Default retry count: 3
- Adjustable via the `--retry` parameter

```bash
pyitol task upload --tree tree.nwk --retry 5
```

---

## Python API Reference

Beyond the command line, every PyiTOL capability is callable directly from Python. The most commonly used public classes and functions are listed below by module, each with a minimal runnable example. Signatures follow the source; use `help(function)` at runtime for full parameters.

### `pyitol.api.client.ITOLAPIClient` — iTOL Batch API Client

Wraps upload, export, delete, and status queries, with built-in exponential-backoff retry and error translation.

**Constructor**: `ITOLAPIClient(api_key=None, api_key_file='.itolapi.key', max_retries=3, backoff_factor=1.0, timeout=120.0, strict_permissions=False)`. The API key can also be supplied via the `ITOL_API_KEY` environment variable.

**Key methods**:

| Method | Description |
|--------|-------------|
| `upload(tree_file, template_files, force=False, datasets_visible=None, project_name=None, tree_description=None)` | Package a zip and upload; returns the tree ID (string) |
| `export(tree_ids, fmt='pdf', output_dir=None, dpi=None, width=None, height=None, extra_params=None)` | Export; returns `{tree_id: local_path}` |
| `delete(tree_id)` / `batch_delete(tree_ids)` | Delete a single / batch of trees |
| `delete_project(name)` / `batch_delete_projects(names)` | Delete projects |
| `upload_and_export(tree_file, template_files, fmt='pdf', output_dir='.', wait_time=120, poll_interval=10, ...)` | Upload, poll until ready, then export; returns the local path |
| `query_status(tree_name, timeout=10)` | Indirectly probe render status; returns a dict |
| `close()` | Close the session (also usable as a context manager) |

```python
from pyitol.api.client import ITOLAPIClient

# Option 1: explicit management
client = ITOLAPIClient(api_key_file='.itolapi.key')
tree_id = client.upload(
    "tree.nwk",
    ["colors.txt", "bars.txt"],
    project_name="MyTree",
    tree_description="Example tree",
)
print("Uploaded:", tree_id)
paths = client.export([tree_id], fmt="png", output_dir="./out", dpi=300)
print("Exported:", paths)
client.delete(tree_id)
client.close()

# Option 2: context manager (recommended)
with ITOLAPIClient(api_key="YOUR_API_KEY") as client:
    out = client.upload_and_export(
        tree_file="tree.nwk",
        template_files=["colors.txt"],
        fmt="svg",
        output_dir="./output",
        wait_time=120,
    )
    print("Upload and export:", out)
```

### `pyitol.templates.generator.TemplateGenerator` — Template Generation Engine

Programmatically assemble multiple dataset schemas and write iTOL v7 template files.

**Key methods**:

| Method | Description |
|--------|-------------|
| `add_schema(schema)` | Add a prebuilt `TemplateSchema` |
| `add_schema_from_data(type_name, label, data, parameters=None, separator='TAB', color='#ff0000')` | Quickly add a dataset from a list of row dicts |
| `set_style(params)` / `set_name(name)` | Set tree style params / template display name |
| `write(output_path, mode='write' \| 'append')` | Write a single template file; returns `Path` |
| `write_multiple(output_dir, prefix='')` | Write each schema as a separate file; returns `list[Path]` |

```python
from pyitol.templates.generator import TemplateGenerator

gen = TemplateGenerator()
gen.set_name("MyTemplate")
gen.add_schema_from_data(
    type_name="color_strip",
    label="Phylum",
    data=[
        {"id": "TaxonA", "label": "Proteobacteria"},
        {"id": "TaxonB", "label": "Firmicutes"},
    ],
    separator="TAB",
)
gen.add_schema_from_data(
    type_name="simple_bar",
    label="Abundance",
    data=[
        {"id": "TaxonA", "value": "12.3"},
        {"id": "TaxonB", "value": "8.1"},
    ],
)
path = gen.write("my_template.txt")              # merged template
paths = gen.write_multiple("./templates", prefix="ds_")  # separate files
```

> `type_name` values: see `pyitol.templates.presets.list_presets()` (31 types, e.g. `color_strip`, `simple_bar`, `heatmap`, `tree_colors`).

### `pyitol.templates.learner` — Template Reverse Learning

| Function | Description |
|----------|-------------|
| `learn_template(template_path)` | Parse an iTOL template file; returns a dict with `template_name`, `datasets`, etc. |
| `train_theme(template_dir, min_freq=0.5)` | Aggregate all `*.txt` templates in a directory; produce recommended default params per dataset type |

```python
from pyitol.templates.learner import learn_template, train_theme

info = learn_template("colors.txt")
print(info["template_name"], info["datasets"])

theme = train_theme("./templates_dir", min_freq=0.5)
print(theme)
```

Equivalent CLI: `pyitol learn template --template colors.txt --output learned.json` and `pyitol learn train-theme --dir ./templates_dir --output theme.json`.

### `pyitol.templates.presets` — Palette & Template Presets

| Function | Description |
|----------|-------------|
| `list_presets()` | List all 31 dataset template preset names |
| `get_preset(name)` | Get a template schema class instance by name |
| `get_palette(preset_name, palette_name='primary', n=None)` | Get a color list (`preset_name` is `nature`/`cell`/`colorblind`) |
| `list_all_palettes()` | List all available palette names grouped by preset |

```python
from pyitol.templates.presets import get_palette, list_all_palettes, list_presets

print(list_presets())            # 31 template type names
print(list_all_palettes())       # palette names grouped by nature/cell/colorblind
colors = get_palette("nature")            # default primary
colors = get_palette("nature", "vibrant") # specific sub-palette
```

Equivalent CLI: `pyitol learn palette --preset-name nature`.

### `pyitol.core.taxonomy` — Taxonomy Analysis

| Function | Description |
|----------|-------------|
| `get_ranks(taxonomy_path, id_column='id')` | Return the list of taxonomic ranks |
| `extract_taxonomy(taxonomy_path, tree_path, rank, id_column='id', multi_tree='error')` | Extract taxonomy at a rank; returns `list[dict]` |
| `extract_taxonomy_with_stats(...)` | Extract with member counts, LCA stats, etc. |
| `extract_taxonomy_from_tip_names(tree_path, format='auto', ...)` | Infer a taxonomy table from tip names |

```python
from pyitol.core.taxonomy import get_ranks, extract_taxonomy

ranks = get_ranks("taxonomy.csv")
print(ranks)  # ['Domain', 'Phylum', 'Class', ...]

rows = extract_taxonomy("taxonomy.csv", "tree.nwk", rank="Phylum")
for r in rows:
    print(r["id"], r["label"])
```

### `pyitol.core.monophyly` — Monophyly Checking

| Function | Description |
|----------|-------------|
| `check_monophyly(taxonomy_path, tree_path, rank, id_column='id', polytomy_mode='strict')` | Check monophyly of all groups at a rank; returns `list[dict]` |
| `check_monophyly_with_taxa_list(taxonomy_path, tree_path, rank=None, taxa_list=None, taxa_file=None, id_column='id', polytomy_mode='strict')` | Check a given taxon list (supports `LUCA`/`LACA`/`LBCA`/`ROOT`) |

```python
from pyitol.core.monophyly import check_monophyly_with_taxa_list

results = check_monophyly_with_taxa_list(
    taxonomy_path="taxonomy.csv",
    tree_path="tree.nwk",
    rank="Phylum",
    taxa_list=["Proteobacteria", "Firmicutes"],
)
for r in results:
    print(r["taxon"], r["status"])   # monophyletic / paraphyletic / polyphyletic
```

### `pyitol.core.parser` — Tree Parsing

| Function | Description |
|----------|-------------|
| `detect_tree_schema(tree_path)` | Return `'newick'` or `'nexus'` |
| `get_single_tree(tree_path, ...)` | Read and return a single tree (dendropy `Tree`) |
| `format_support_values(...)` | Format support values (IQ-TREE / RAxML / ALRT, etc.) |

```python
from pyitol.core.parser import detect_tree_schema

schema = detect_tree_schema("tree.nwk")
print(schema)  # 'newick'
```

### `pyitol.utils.data_converters` — Data Format Conversion

| Function | Description |
|----------|-------------|
| `wide_to_long(input_file, output_file, id_column='id', value_name='value', var_name='variable')` | Wide to long |
| `long_to_wide(input_file, output_file, id_column='id', variable_column='variable', value_column='value')` | Long to wide |
| `df_tree(df_or_path, columns=None, main='col', order='none', metric='euclidean', linkage_method='average')` | Build a Newick tree from a dataframe |
| `convert_to_binary_matrix(...)` / `category_to_connect(...)` | Category to binary matrix / co-occurrence to connection pairs |

```python
from pyitol.utils.data_converters import wide_to_long, long_to_wide, df_tree

wide_to_long("wide.csv", "long.csv", id_column="id")
long_to_wide("long.csv", "wide.csv", id_column="id")
tree_path = df_tree("data.csv", columns=["A", "B", "C"], main="col", order="hclust")
```

### `pyitol.utils.io` — File Search

| Function | Description |
|----------|-------------|
| `search_tree_file(directory, recursive=True, extensions=None)` | Recursively search tree files; returns `list[Path]` |
| `find_first_tree_file(directory, recursive=True, extensions=None)` | Return the first tree file path or `None` |

```python
from pyitol.utils.io import search_tree_file, find_first_tree_file

files = search_tree_file("./data", recursive=True)
first = find_first_tree_file("./data")
print(files, first)
```

### `pyitol.utils.tree_info` — Tree Information

| Function | Description |
|----------|-------------|
| `get_tree_info(tree_path)` | Return a summary dict (tip count, internal node count, etc.) |
| `get_tip_order(tree_path)` | Return the ordered list of tip names |
| `extract_tree_info(...)` | Low-level extraction |

```python
from pyitol.utils.tree_info import get_tree_info

info = get_tree_info("tree.nwk")
print(info)  # {'tip_count': ..., 'internal_count': ..., ...}
```

### `pyitol.utils.color_tools` — Color Utilities

| Function | Description |
|----------|-------------|
| `assign_colors_to_categories(categories, palette=None)` | Assign colors to a category list; returns `{category: color}` |
| `generate_gradient_colors(start, end, n)` | Generate n gradient colors |
| `hex_to_rgb` / `rgb_to_hex` / `darken_color` / `lighten_color` / `validate_color` | Color conversion and adjustment |

```python
from pyitol.utils.color_tools import assign_colors_to_categories, generate_gradient_colors

color_map = assign_colors_to_categories(["Proteobacteria", "Firmicutes", "Bacteroidetes"])
print(color_map)
gradient = generate_gradient_colors("#ff0000", "#0000ff", 5)
print(gradient)
```
