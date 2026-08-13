# 快速入门：从安装到出图

本教程带你用 10 分钟完成 PyiTOL 的首次使用，生成一张发表级系统发育树图。

## 前提条件

- Python 3.9+
- iTOL API Key（在 https://itol.embl.de/ 注册后获取）

## 步骤1：安装

```bash
cd /path/to/PyiTOL
pip install -e .
```

验证安装：

```bash
pyitol --help
```

## 步骤2：准备数据

准备两个文件：

**tree.nwk** — 系统发育树（Newick 格式）
```
(A:0.1,B:0.2,(C:0.15,D:0.1):0.05);
```

**taxonomy.csv** — 末端节点分类信息
```csv
id,Phylum,Genus,GC_content
A,Proteobacteria,Escherichia,52
B,Firmicutes,Bacillus,35
C,Proteobacteria,Pseudomonas,58
D,Actinobacteria,Streptomyces,72
```

## 步骤3：查看分类等级

```bash
pyitol taxonomy ranks --taxonomy taxonomy.csv
```

输出：
```
可用分类等级:
  1. Phylum
  2. Genus
  3. GC_content
```

## 步骤4：单系性检测

```bash
pyitol taxonomy monophyly \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --rank Phylum --output monophyly.csv
```

查看结果：
```bash
cat monophyly.csv
```

## 步骤5：生成模板

### 生成分类色带

```bash
pyitol template create color-strip \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column Phylum --output colors.txt
```

### 生成 GC 含量柱状图

```bash
pyitol template create simple-bar \
  --taxonomy taxonomy.csv --tree tree.nwk \
  --column GC_content --output bars.txt
```

## 步骤6：上传到 iTOL

```bash
# 先保存 API Key
echo "YOUR_API_KEY" > .itolapi.key

# 上传
pyitol task upload \
  --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --dataset-name MyFirstTree
```

## 步骤7：导出图片

```bash
pyitol task export \
  --upload-id YOUR_TREE_ID \
  --download ./output --format svg
```

或者一步完成上传+导出：

```bash
pyitol task upload-and-export \
  --tree tree.nwk \
  --config colors.txt --config bars.txt \
  --output result.svg --format svg --wait 60
```

## 步骤8：使用配置文件简化操作

> **提示**：项目根目录提供 `config.example.yaml` 模板，包含所有可配置项及注释，可直接 `cp config.example.yaml my_config.yaml` 后修改使用。

`pyitol task run` 通过配置文件执行批量任务，每个配置项通过 `command` 字段指定操作类型。支持的 `command` 值包括：`upload`、`export`、`extract`、`monophyly`、`convert-binary`。

创建单配置文件 `workflow.yaml`：

```yaml
command: upload
tree: tree.nwk
configs: [colors.txt, bars.txt]
api_key: YOUR_API_KEY
name: MyFirstTree
```

```bash
pyitol task run --config workflow.yaml
```

如果需要一步完成上传和导出，可以创建批量列表文件 `batch.yaml`：

```yaml
- command: upload
  tree: tree.nwk
  configs: [colors.txt, bars.txt]
  api_key: YOUR_API_KEY
  name: MyFirstTree
- command: export
  upload_id: TREE_ID_FROM_UPLOAD
  download: ./output
  parameters:
    format: svg
    dpi: 300
```

```bash
pyitol task run --config-list batch.yaml
```

更多配置文件示例见 [API 使用指南](../api.md#批量操作)。

## 下一步

- [分类分析教程](taxonomy.md) — 深入了解单系性检测和美化配置
- [模板生成教程](templates.md) — 探索 30+ 种模板类型
