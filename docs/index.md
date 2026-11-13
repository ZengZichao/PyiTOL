# PyiTOL 文档

[English](index_en.md) | 中文

PyiTOL 是一个基于 Python 的 iTOL (Interactive Tree Of Life) 可视化全流程自动化命令行工具。

## 文档导航

| 文档 | 说明 |
|------|------|
| [CLI 完整参考](cli.md) | 所有命令和参数的详细说明 |
| [模板生成专用子命令参考](templates-reference.md) | 34 个 `template create-*` 专用子命令的完整选项与示例 |
| [API 使用指南](api.md) | iTOL API 交互与自动化上传导出 |
| [错误码参考](error_codes.md) | 退出码、E 系列错误码与 V 系列验证错误码对照表 |
| [故障排除指南](troubleshooting.md) | 常见问题及其解决方法 |
| [快速入门教程](tutorials/quickstart.md) | 从安装到出图的 10 分钟教程 |
| [分类分析教程](tutorials/taxonomy.md) | 单系性检测与分类信息提取 |
| [模板生成教程](tutorials/templates.md) | 33 种 iTOL v7 模板生成指南（另有 `external-shape-bubble` 变体，合计 34 个专用子命令） |
| [贡献指南](contributing.md) | 项目结构、代码规范与参与开发流程 |

## 核心功能

```
PyiTOL 功能体系：
├── 树结构操作 (Tree Structure)
│   ├── 折叠分支 (Collapse Clades)
│   ├── 修剪分支 (Prune Branches)
│   ├── 节点间距 (Node Spacing)
│   └── 节点标识 (Node Labels)
├── 注释配置 (Annotation)
│   ├── 标签与弹出信息 (Labels & Popup Info)
│   ├── 树颜色 (Tree Colors)
│   ├── 分支渐变 (Branch Gradients)
│   └── 彩色范围 (Colored Ranges)
├── 数据集 (Datasets)
│   ├── 二元数据 (Binary Data)
│   ├── 条形图 (Simple Bar / Multibar)
│   ├── 饼图 (Pie Chart)
│   ├── 色带 (Color Strip)
│   ├── 热图 (Heatmap)
│   ├── 箱线图 (Boxplot)
│   ├── 符号标记 (Symbols)
│   ├── 蛋白结构域 (Protein Domains)
│   ├── 渐变色带 (Color Gradients)
│   ├── 外部形状 (External Shapes)
│   ├── 文本标签 (Text Labels)
│   ├── 箭头注释 (Arrows)
│   ├── 连接线 (Connections)
│   ├── 纠缠图 (Tanglegrams)
│   ├── 折线图 (Line Charts)
│   ├── 图像嵌入 (Images)
│   ├── 序列比对 (Alignments)
│   ├── 系统发育放置 (Phylogenetic Placements)
│   ├── 时间尺度 (Timescales)
│   └── 手动注释 (Manual Annotations)
├── 分类分析 (Taxonomy Analysis)
│   ├── 分类等级识别 (Auto Ranks)
│   ├── 分类提取 (Taxonomy Extract)
│   ├── 单系性检测 (Monophyly Check)
│   ├── 美化配置 (Style Config)
│   ├── 二元数据转换 (Binary Conversion)
│   └── 连接对转换 (Connect Pairs)
├── API 交互 (API Operations)
│   ├── 上传 (Upload)
│   ├── 删除 (Delete)
│   ├── 导出 (Export)
│   └── 状态查询 (Status)
└── 工具模块 (Utilities)
    ├── 模板反向学习 (Learning from Existing Templates)
    ├── 树信息统计 (Tree Info)
    ├── 颜色工具 (Color Tools)
    ├── 计数数据建树 (Count to Tree)
    └── 注释列分组 (Column Grouping)
```

## 安装

```bash
pip install -e .
```

依赖：Python 3.10+, typer, pandas, dendropy, numpy, requests, pydantic, PyYAML, rich, scipy

## 快速验证

```bash
pyitol --help
pyitol template create --help
pyitol taxonomy monophyly --help
```
