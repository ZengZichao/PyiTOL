# 故障排除指南

## 安装问题

### `pip install pyitol` 失败
- 确保 Python 版本 >= 3.9
- 如果安装 dendropy 失败，尝试先安装：`pip install setuptools>=68.0`

### 导入错误 `ModuleNotFoundError: No module named 'pyitol'`
- 如果通过 `pip install -e .` 安装，请确认在安装目录下运行命令
- 检查是否激活了正确的虚拟环境

## API 相关问题

### `ValueError: No API key provided`
- 通过命令行参数传入：`pyitol task upload --api-key YOUR_KEY`
- 设置环境变量：`export ITOL_API_KEY=YOUR_KEY`
- 在当前目录创建 `.itolapi.key` 文件，内容为纯文本 API Key
- 确保 API Key 文件权限安全：`chmod 600 .itolapi.key`

详见 [API 使用指南](api.md#api-密钥配置)。

### 上传失败 `Upload failed with status 403`
- API Key 可能已过期或被限制，请登录 iTOL 账户检查
- 确认网络可以访问 `https://itol.embl.de`

### 导出超时
- 大文件导出可能需要更长时间，可通过 `--wait` 增加等待时间
- 如果频繁超时，检查 `--dpi` 和 `--width` 参数是否设置过大

## 模板生成问题

### `Column 'xxx' not found`
- 检查 `--column` 参数是否与 taxonomy 表格中的列名完全一致（区分大小写）
- 使用 `--id-column` 指定正确的 ID 列，默认为 `id`

### 颜色不显示或显示错误
- 确认颜色格式正确：`#RRGGBB`、`rgb(r,g,b)`、`hsl(h,s,l)` 或命名颜色（如 `red`）
- 分类变量超过 7 个时，建议使用 `--palette colorblind` 选择色盲友好配色

### 分隔符冲突警告
- 如果数据值中包含逗号、空格或 Tab，请使用 `--separator` 切换为不会冲突的分隔符
- 例如数据含逗号时，使用 `--separator TAB`

## 树文件问题

### `树文件解析失败`
- 确保文件为有效的 Newick 或 Nexus 格式
- 检查括号是否匹配、节点标签是否包含非法字符
- 超长注释可能导致格式误判，建议移除不必要的注释

### 单系性检测报错 `Null leafset bitmask`
- 通常是因为指定的分类群在树中完全没有匹配的成员
- 检查 taxonomy 中的 ID 是否与树文件中的 tip label 完全一致

## 性能问题

### 大数据集处理缓慢
- 10,000+ 节点树建议提前过滤 taxonomy 表，仅保留树中存在的 ID
- 批量生成多种模板时，可使用 `pyitol template create` 统一命令减少重复 IO

## 获取帮助

如果以上方法无法解决问题，请：
1. 查看完整 CLI 帮助：`pyitol --help` 或 `pyitol <command> --help`
2. 检查 [API 文档](api.md) 和 [CLI 文档](cli.md)
3. 在项目中提交 Issue，附上完整的错误输出和输入文件样本
