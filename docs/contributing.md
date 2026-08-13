# 贡献指南

感谢您对 PyiTOL 的兴趣！以下是参与项目开发的指南。

## 项目结构

```
src/pyitol/
├── cli/                    # CLI 入口（已拆分为子模块）
│   ├── main.py             # 主入口 + validate/replay
│   ├── common.py           # 公共辅助函数
│   ├── apps.py             # Typer app 定义
│   ├── config_cmd.py       # config 子命令
│   ├── template_cmd.py     # template 子命令
│   ├── taxonomy_cmd.py     # taxonomy 子命令
│   ├── task_cmd.py         # task 子命令
│   ├── tree_cmd.py         # tree 子命令
│   ├── utils_cmd.py        # utils 子命令
│   └── learn_cmd.py        # learn 子命令
├── core/                   # 核心逻辑
│   ├── parser.py           # 树文件/元数据解析
│   ├── taxonomy.py         # 分类提取
│   ├── monophyly.py        # 单系性检测
│   ├── validator.py        # 冲突检测
│   ├── binary_convert.py   # 二元数据转换
│   ├── connect_convert.py  # 连接对转换
│   ├── count_tree.py       # 计数数据建树
│   └── column_group.py     # 注释列分组
├── templates/              # 模板引擎
│   ├── generator.py        # 模板生成器
│   ├── learner.py          # 模板反向解析
│   ├── schemas/            # Schema 定义
│   │   ├── base.py         # 统一入口
│   │   ├── tree_structure.py
│   │   ├── annotations.py
│   │   ├── datasets_simple.py
│   │   └── datasets_advanced.py
│   ├── presets/            # 预设样式库
├── api/                    # iTOL API 封装
│   └── client.py           # API 客户端
└── utils/                  # 工具函数
    ├── color_tools.py
    ├── io.py
    ├── data_converters.py
    ├── session.py
    ├── tree_info.py
    └── reporter.py
```

## 运行测试

```bash
python -m pytest tests/ -v
```

## 代码规范

- 所有 CLI 参数使用 `--long-flag` 格式
- 保持向后兼容的导入路径
- 新增命令需添加对应测试

## 随机过程说明

**本项目不包含任何随机算法或随机过程。** 所有输出（包括颜色分配、树解析、模板生成）都是确定性的。因此无需设置随机种子，也不存在结果可复现性方面的随机性风险。
