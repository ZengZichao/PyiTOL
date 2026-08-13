# PyiTOL API 使用指南

PyiTOL 封装了 iTOL 的三个批量 API 端点，支持自动重试、错误翻译和多格式导出。

## API 端点

| 端点 | 功能 | PyiTOL 命令 |
|------|------|------------|
| `https://itol.embl.de/batch_uploader.cgi` | 上传树文件 + 模板 | `pyitol task upload` |
| `https://itol.embl.de/batch_downloader.cgi` | 导出渲染后的图片 | `pyitol task export` |
| `https://itol.embl.de/batch_delete.cgi` | 删除已上传的树 | `pyitol task delete` |

## API 密钥配置

支持三种方式（优先级从高到低）：

### 方式1：命令行参数

```bash
pyitol task upload --tree tree.nwk --api-key YOUR_API_KEY
```

### 方式2：环境变量

```bash
export ITOL_API_KEY=YOUR_API_KEY
pyitol task upload --tree tree.nwk
```

### 方式3：密钥文件

在项目目录创建 `.itolapi.key` 文件，写入纯文本 API Key：

```bash
echo "YOUR_API_KEY" > .itolapi.key
chmod 600 .itolapi.key
```

或指定自定义路径：

```bash
pyitol task upload --tree tree.nwk --api-key-file /path/to/.itolapi.key
```

> **安全提示**：PyiTOL 会检查密钥文件权限，如果 group/other 有读写权限会发出警告。建议使用 `chmod 600 .itolapi.key`。

## task 命令总览

| 命令 | 说明 |
|------|------|
| `pyitol task upload` | 上传树和模板到 iTOL |
| `pyitol task export` | 从 iTOL 导出渲染图片 |
| `pyitol task upload-and-export` | 上传并导出（一步完成） |
| `pyitol task delete` | 删除已上传的树 |
| `pyitol task status` | 查询树的状态 |
| `pyitol task run` | 运行配置文件（单配置或批量列表） |

## 上传流程

### 基本上传

```bash
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt \
  --dataset-name MyTree
```

### 多模板上传

```bash
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt \
  --config bars.txt \
  --config heatmap.txt \
  --dataset-name MyTree
```

PyiTOL 会自动将多个模板文件打包为 zip 上传。

### 上传后自动导出

```bash
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt \
  --output result.svg --format svg --wait 60
```

`--wait` 指定等待 iTOL 渲染的最长时间（秒），超时后命令失败。

## 导出控制

### 支持的格式

PyiTOL 支持 8 种导出格式：

| 格式 | 说明 | 额外参数 |
|------|------|---------|
| `svg` | 矢量图（推荐） | |
| `png` | 位图 | `--dpi` |
| `pdf` | 文档 | `--dpi` |
| `tiff` | TIFF 图像 | `--dpi` |
| `eps` | Encapsulated PostScript | `--dpi` |
| `newick` | Newick 树格式 | |
| `nexus` | Nexus 树格式 | |
| `phyloxml` | PhyloXML 格式 | |

### 导出尺寸

```bash
pyitol task export \
  --upload-id TREE_ID \
  --download ./output \
  --format png \
  --parameter dpi=300 \
  --parameter width=2400 \
  --parameter height=1600
```

支持的尺寸参数：`--dpi`、`--width`、`--height`。

## 删除操作

```bash
# 删除单棵树
pyitol task delete --upload-id TREE_ID

# 批量删除
pyitol task delete --upload-id ID1 --upload-id ID2
```

## 状态查询

```bash
pyitol task status --upload-id TREE_ID
```

## 批量操作

### 批量上传导出（配置文件）

`pyitol task run` 支持通过 YAML/JSON 配置文件执行批量任务。配置文件为列表格式，每项通过 `command` 字段指定要执行的操作。

支持的 `command` 值：`upload`、`export`、`extract`、`monophyly`、`convert-binary`、`convert-connect`、`template`。

创建 `batch.yaml`：

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

执行：

```bash
# 批量执行列表
pyitol task run --config-list batch.yaml

# 单配置执行
pyitol task run --config single_workflow.yaml
```

单配置文件示例 `single_workflow.yaml`：

```yaml
command: upload
tree: tree.nwk
configs: [colors.txt, bars.txt]
api_key: YOUR_KEY
name: MyTree
```

## 错误处理

PyiTOL 内置了 iTOL API 错误翻译表，将英文错误信息转换为用户友好的中文建议：

| iTOL 错误关键词 | PyiTOL 翻译 |
|----------------|------------|
| `invalid api key` | API Key 无效：请检查 --api-key 参数或 .itolapi.key 文件 |
| `file too large` | 文件过大：iTOL 限制上传文件总大小不超过 2MB |
| `tree format` | 树文件格式错误：请确保文件为标准的 Newick 或 Nexus 格式 |
| `rate limit` | 请求过于频繁：请稍后重试 |
| `rendering` | 渲染失败：iTOL 服务器渲染超时 |

完整错误代码表见 [错误码参考](error_codes.md) 或 `src/pyitol/utils/reporter.py`。

## 网络重试

API 客户端内置指数退避重试策略：
- 自动重试 HTTP 429, 500, 502, 503, 504
- 默认重试 3 次
- 可通过 `--retry` 参数调整

```bash
pyitol task upload --tree tree.nwk --retry 5
```

---

## Python API 参考

除命令行外，PyiTOL 的所有能力都可通过 Python 直接调用。下面按模块列出最常用的公共类与函数，并给出最小可运行示例。所有签名以源码为准，运行时可用 `help(函数名)` 查看完整参数。

### `pyitol.api.client.ITOLAPIClient` — iTOL 批量 API 客户端

封装上传、导出、删除与状态查询，内置指数退避重试与错误翻译。

**构造函数**：`ITOLAPIClient(api_key=None, api_key_file='.itolapi.key', max_retries=3, backoff_factor=1.0, timeout=120.0, strict_permissions=False)`。API Key 也可通过环境变量 `ITOL_API_KEY` 提供。

**主要方法**：

| 方法 | 说明 |
|------|------|
| `upload(tree_file, template_files, force=False, datasets_visible=None, project_name=None, tree_description=None)` | 打包 zip 上传，返回树 ID（字符串） |
| `export(tree_ids, fmt='pdf', output_dir=None, dpi=None, width=None, height=None, extra_params=None)` | 导出，返回 `{tree_id: 本地路径}` |
| `delete(tree_id)` / `batch_delete(tree_ids)` | 删除单棵 / 批量删除树 |
| `delete_project(name)` / `batch_delete_projects(names)` | 删除项目 |
| `upload_and_export(tree_file, template_files, fmt='pdf', output_dir='.', wait_time=120, poll_interval=10, ...)` | 上传后轮询就绪再导出，返回本地路径 |
| `query_status(tree_name, timeout=10)` | 间接探测渲染状态，返回字典 |
| `close()` | 关闭会话（亦可用上下文管理器） |

```python
from pyitol.api.client import ITOLAPIClient

# 方式一：显式管理
client = ITOLAPIClient(api_key_file='.itolapi.key')
tree_id = client.upload(
    "tree.nwk",
    ["colors.txt", "bars.txt"],
    project_name="MyTree",
    tree_description="示例树",
)
print("已上传:", tree_id)
paths = client.export([tree_id], fmt="png", output_dir="./out", dpi=300)
print("已导出:", paths)
client.delete(tree_id)
client.close()

# 方式二：上下文管理器（推荐）
with ITOLAPIClient(api_key="YOUR_API_KEY") as client:
    out = client.upload_and_export(
        tree_file="tree.nwk",
        template_files=["colors.txt"],
        fmt="svg",
        output_dir="./output",
        wait_time=120,
    )
    print("一键上传并导出:", out)
```

### `pyitol.templates.generator.TemplateGenerator` — 模板生成引擎

以编程方式组装多个数据集 schema 并写出 iTOL v7 模板文件。

**主要方法**：

| 方法 | 说明 |
|------|------|
| `add_schema(schema)` | 添加一个已构建的 `TemplateSchema` |
| `add_schema_from_data(type_name, label, data, parameters=None, separator='TAB', color='#ff0000')` | 从原始数据列表快速添加数据集 |
| `set_style(params)` / `set_name(name)` | 设置树样式参数 / 模板显示名 |
| `write(output_path, mode='write' \| 'append')` | 写出单个模板文件，返回 `Path` |
| `write_multiple(output_dir, prefix='')` | 每个 schema 单独成文件，返回 `Path` 列表 |

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
path = gen.write("my_template.txt")          # 写出合并模板
paths = gen.write_multiple("./templates", prefix="ds_")  # 分文件写出
```

> `type_name` 取值见 `pyitol.templates.presets.list_presets()`（共 31 种，如 `color_strip`、`simple_bar`、`heatmap`、`tree_colors` 等）。

### `pyitol.templates.learner` — 模板反向学习

| 函数 | 说明 |
|------|------|
| `learn_template(template_path)` | 解析一个 iTOL 模板文件，返回含 `template_name`、`datasets` 等字段的字典 |
| `train_theme(template_dir, min_freq=0.5)` | 汇总目录下所有 `*.txt` 模板，为每种数据集类型生成推荐默认参数 |

```python
from pyitol.templates.learner import learn_template, train_theme

info = learn_template("colors.txt")
print(info["template_name"], info["datasets"])

theme = train_theme("./templates_dir", min_freq=0.5)
print(theme)
```

等效命令行：`pyitol learn template --template colors.txt --output learned.json` 与 `pyitol learn train-theme --dir ./templates_dir --output theme.json`。

### `pyitol.templates.presets` — 配色与模板预设

| 函数 | 说明 |
|------|------|
| `list_presets()` | 列出全部 31 种数据集模板预设名 |
| `get_preset(name)` | 按名获取模板 schema 类实例 |
| `get_palette(preset_name, palette_name='primary', n=None)` | 获取调色板颜色列表（`preset_name` 为 `nature`/`cell`/`colorblind`） |
| `list_all_palettes()` | 分组列出所有可用调色板名 |

```python
from pyitol.templates.presets import get_palette, list_all_palettes, list_presets

print(list_presets())            # 31 种模板类型名
print(list_all_palettes())       # 按 nature/cell/colorblind 分组的调色板名
colors = get_palette("nature")            # 默认取 primary
colors = get_palette("nature", "vibrant") # 指定子调色板
```

等效命令行：`pyitol learn palette --preset-name nature`。

### `pyitol.core.taxonomy` — 分类分析

| 函数 | 说明 |
|------|------|
| `get_ranks(taxonomy_path, id_column='id')` | 返回分类等级列表 |
| `extract_taxonomy(taxonomy_path, tree_path, rank, id_column='id', multi_tree='error')` | 提取指定等级的分类信息，返回 `list[dict]` |
| `extract_taxonomy_with_stats(...)` | 提取并附带成员数、LCA 等统计 |
| `extract_taxonomy_from_tip_names(tree_path, format='auto', ...)` | 从末端名称反推分类表 |

```python
from pyitol.core.taxonomy import get_ranks, extract_taxonomy

ranks = get_ranks("taxonomy.csv")
print(ranks)  # ['Domain', 'Phylum', 'Class', ...]

rows = extract_taxonomy("taxonomy.csv", "tree.nwk", rank="Phylum")
for r in rows:
    print(r["id"], r["label"])
```

### `pyitol.core.monophyly` — 单系性检测

| 函数 | 说明 |
|------|------|
| `check_monophyly(taxonomy_path, tree_path, rank, id_column='id', polytomy_mode='strict')` | 检测某等级下所有类群的单系性，返回 `list[dict]` |
| `check_monophyly_with_taxa_list(taxonomy_path, tree_path, rank=None, taxa_list=None, taxa_file=None, id_column='id', polytomy_mode='strict')` | 检测指定类群列表（支持 `LUCA`/`LACA`/`LBCA`/`ROOT`） |

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

### `pyitol.core.parser` — 树解析

| 函数 | 说明 |
|------|------|
| `detect_tree_schema(tree_path)` | 返回 `'newick'` 或 `'nexus'` |
| `get_single_tree(tree_path, ...)` | 读取并返回单棵树（dendropy `Tree`） |
| `format_support_values(...)` | 格式化支持值（IQ-TREE / RAxML / ALRT 等） |

```python
from pyitol.core.parser import detect_tree_schema

schema = detect_tree_schema("tree.nwk")
print(schema)  # 'newick'
```

### `pyitol.utils.data_converters` — 数据格式转换

| 函数 | 说明 |
|------|------|
| `wide_to_long(input_file, output_file, id_column='id', value_name='value', var_name='variable')` | 宽表转长表 |
| `long_to_wide(input_file, output_file, id_column='id', variable_column='variable', value_column='value')` | 长表转宽表 |
| `df_tree(df_or_path, columns=None, main='col', order='none', metric='euclidean', linkage_method='average')` | 从数据框构建 Newick 树 |
| `convert_to_binary_matrix(...)` / `category_to_connect(...)` | 分类转二元矩阵 / 共现转连接对 |

```python
from pyitol.utils.data_converters import wide_to_long, long_to_wide, df_tree

wide_to_long("wide.csv", "long.csv", id_column="id")
long_to_wide("long.csv", "wide.csv", id_column="id")
tree_path = df_tree("data.csv", columns=["A", "B", "C"], main="col", order="hclust")
```

### `pyitol.utils.io` — 文件检索

| 函数 | 说明 |
|------|------|
| `search_tree_file(directory, recursive=True, extensions=None)` | 递归搜索树文件，返回 `list[Path]` |
| `find_first_tree_file(directory, recursive=True, extensions=None)` | 返回首个树文件路径或 `None` |

```python
from pyitol.utils.io import search_tree_file, find_first_tree_file

files = search_tree_file("./data", recursive=True)
first = find_first_tree_file("./data")
print(files, first)
```

### `pyitol.utils.tree_info` — 树信息

| 函数 | 说明 |
|------|------|
| `get_tree_info(tree_path)` | 返回树的概要信息字典（末端数、内部节点数等） |
| `get_tip_order(tree_path)` | 返回末端名称顺序列表 |
| `extract_tree_info(...)` | 底层提取函数 |

```python
from pyitol.utils.tree_info import get_tree_info

info = get_tree_info("tree.nwk")
print(info)  # {'tip_count': ..., 'internal_count': ..., ...}
```

### `pyitol.utils.color_tools` — 颜色工具

| 函数 | 说明 |
|------|------|
| `assign_colors_to_categories(categories, palette=None)` | 为分类列表分配颜色，返回 `{类别: 颜色}` |
| `generate_gradient_colors(start, end, n)` | 生成 n 个渐变颜色 |
| `hex_to_rgb` / `rgb_to_hex` / `darken_color` / `lighten_color` / `validate_color` | 颜色转换与调整 |

```python
from pyitol.utils.color_tools import assign_colors_to_categories, generate_gradient_colors

color_map = assign_colors_to_categories(["Proteobacteria", "Firmicutes", "Bacteroidetes"])
print(color_map)
gradient = generate_gradient_colors("#ff0000", "#0000ff", 5)
print(gradient)
```
