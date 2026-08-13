# PyiTOL 错误码参考

## 退出码

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | 操作正常完成 |
| 1 | Runtime Error | 内部错误、依赖问题、API 失败、连接/超时/权限错误 |
| 2 | Parameter Error | 无效的 CLI 参数、验证失败、ValueError |
| 3 | Data Error | 输入文件格式/内容错误、模板错误、文件未找到 |
| 130 | User Interrupt | 收到 SIGINT (Ctrl+C) |

退出码由 `src/pyitol/cli/main.py` 的 `main()` 函数根据异常类型映射，详见异常处理逻辑。

## 结构化错误码

PyiTOL 在 `src/pyitol/utils/reporter.py` 的 `ERROR_CODE_TABLE` 中定义了 E001–E055 共 55 个结构化错误码，每个错误码对应一个异常类和用户友好的中文错误描述。

### 基础错误 (E001–E015)

| Code | 异常类 | 描述 |
|------|--------|------|
| E001 | FileNotFoundError | 文件未找到：请检查输入文件路径是否正确。 |
| E002 | ValueError | 参数错误：提供的参数值不合法或格式不正确。 |
| E003 | ConnectionError | 网络连接失败：请检查网络或iTOL服务器状态。 |
| E004 | TimeoutError | 操作超时：服务器响应时间过长，请重试。 |
| E005 | PermissionError | 权限错误：没有写入目标目录的权限。 |
| E006 | SchemaValidationError | 模板验证失败：模板格式不符合iTOL v7规范。 |
| E007 | TreeParseError | 树文件解析失败：无法识别Newick/Nexus格式。 |
| E008 | MetadataParseError | 元数据解析失败：表格文件格式错误或列不匹配。 |
| E009 | ColorCodeError | 颜色代码非法：请使用十六进制颜色值如#ff0000。 |
| E010 | SeparatorConflictError | 分隔符冲突：数据中使用了非法分隔符。 |
| E011 | MissingColumnError | 缺少必要列：请检查输入表格的列名是否正确。 |
| E012 | TaxaNotFoundError | 物种未找到：分类表格中的物种不在树文件中。 |
| E013 | APIKeyError | API密钥错误：请检查.itolapi.key文件内容。 |
| E014 | UploadError | 上传失败：iTOL服务器返回错误响应。 |
| E015 | ExportError | 导出失败：iTOL渲染未完成或格式不支持。 |

### 扩展错误 (E016–E030)

| Code | 异常类 | 描述 |
|------|--------|------|
| E016 | SessionError | 会话错误：无法加载或保存会话快照，请检查文件路径和权限。 |
| E017 | ReplayError | 复现失败：快照中缺少必要的参数或文件，请检查session.yaml内容。 |
| E018 | TemplateTypeError | 模板类型错误：不支持的模板类型，请检查类型名称拼写。 |
| E019 | FileFormatError | 文件格式不支持：请使用Newick、Nexus、CSV或Excel格式。 |
| E020 | FileTooLargeError | 文件过大：单个文件或总上传大小超过iTOL限制（2MB）。 |
| E021 | SpecialCharacterError | 特殊字符错误：节点ID包含空格或非法符号，建议替换为下划线。 |
| E022 | NodeIDMismatchError | 节点ID不匹配：元数据中的ID与树文件中的节点名称不一致。 |
| E023 | QuotaExceededError | 配额超限：已达到iTOL账户的树数量或存储上限，请删除旧树后重试。 |
| E024 | RateLimitError | 请求过于频繁：已触发iTOL速率限制，请降低请求频率后重试。 |
| E025 | ServerMaintenanceError | 服务器维护：iTOL服务器正在维护中，请稍后重试。 |
| E026 | RenderingError | 渲染失败：iTOL服务器无法渲染该树，可能树过于复杂或数据集不兼容。 |
| E027 | TreeNotFoundError | 树未找到：指定的tree_id不存在或已被删除，请检查后重试。 |
| E028 | DuplicateTreeError | 树已存在：同名的树已存在于iTOL账户中，请更换tree_name。 |
| E029 | DatasetIncompatibleError | 数据集不兼容：模板格式与树结构不匹配，请检查模板类型和数据内容。 |
| E030 | ColumnMismatchError | 列不匹配：输入表格的列数或列名与预期不符，请检查数据文件。 |

### 网络与服务错误 (E031–E040)

| Code | 异常类 | 描述 |
|------|--------|------|
| E031 | NetworkTimeoutError | 网络超时：连接iTOL服务器超时，请检查网络并重试。 |
| E032 | SSLError | SSL证书错误：无法建立安全连接，请检查系统时间或代理设置。 |
| E033 | DNSLookupError | DNS解析失败：无法解析iTOL服务器地址，请检查网络配置。 |
| E034 | BadGatewayError | 网关错误：iTOL上游服务异常，请稍后重试。 |
| E035 | GatewayTimeoutError | 网关超时：iTOL服务器响应超时，请稍后重试。 |
| E036 | ServiceUnavailableError | 服务不可用：iTOL服务器当前无法处理请求，请稍后重试。 |
| E037 | AuthenticationExpiredError | 认证过期：API Key已过期，请重新获取或更新密钥。 |
| E038 | AccountSuspendedError | 账户已暂停：iTOL账户已被暂停，请联系iTOL支持团队。 |
| E039 | AccessDeniedError | 访问被拒绝：当前API Key无权执行此操作，请检查权限配置。 |
| E040 | EmptyFileError | 空文件错误：上传的文件内容为空，请检查文件是否损坏。 |

### 文件与渲染错误 (E041–E055)

| Code | 异常类 | 描述 |
|------|--------|------|
| E041 | CorruptFileError | 文件损坏：上传的文件无法解析，请检查文件完整性。 |
| E042 | ExtensionNotAllowedError | 文件扩展名不允许：请使用iTOL支持的文件格式。 |
| E043 | LegendError | 图例错误：图例参数设置不正确，请检查LEGEND相关配置。 |
| E044 | HeaderError | 模板头部错误：模板头部参数缺失或格式错误，请检查HEADER区。 |
| E045 | CanvasTooLargeError | 画布过大：导出尺寸超出iTOL限制，请减小dpi或宽高。 |
| E046 | FontNotFoundError | 字体未找到：iTOL服务器缺少指定字体，请使用默认字体。 |
| E047 | ImageGenerationError | 图像生成失败：iTOL无法生成图像，请尝试其他格式。 |
| E048 | TreeTooComplexError | 树结构过于复杂：节点数或分支数过多，建议简化树结构。 |
| E049 | StorageFullError | 存储空间已满：iTOL账户存储空间不足，请删除旧文件。 |
| E050 | MaxTreesReachedError | 达到最大树数量：iTOL账户中树的数量已达上限，请删除旧树。 |
| E051 | TreeLockedError | 树已锁定：该树当前被锁定，无法修改或删除，请稍后再试。 |
| E052 | InvalidColumnError | 无效列：指定的列名在数据中不存在，请检查列名拼写。 |
| E053 | SeparatorConflictError | 分隔符冲突：数据内容中包含与分隔符相同的字符，请更换分隔符。 |
| E054 | DataFormatError | 数据格式错误：模板数据区格式不正确，请对照iTOL v7规范检查。 |
| E055 | UnsupportedFormatError | 不支持的导出格式：请使用svg、png或pdf格式。 |

## 验证错误 (V001-V024)

验证错误由 `src/pyitol/core/validator.py` 产生，不对应退出码，而是作为 `validate` 命令的输出和警告/错误信息。

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

## 日志级别

| Level | Tag | Description |
|-------|-----|-------------|
| DEBUG | DBG | 详细调试信息 |
| INFO | INF | 正常操作消息 |
| WARNING | WRN | 警告消息（非致命） |
| ERROR | ERR | 错误消息 |
| CRITICAL | CRT | 严重错误（立即退出） |

日志格式：`2025-03-21T10:15:30.123 | INFO     | message`

## 常见错误场景

### "Tree file not found" (E001/V012)
- 检查文件路径拼写
- 确认文件存在于指定位置
- 建议使用绝对路径

### "Multiple trees detected" (exit code 2)
- 使用 `--multi-tree-mode` 指定处理策略：
  - `ask`：提示用户（默认）
  - `first`：仅使用第一棵树
  - `last`：仅使用最后一棵树
  - `random`：随机选择一棵
  - `split`：分别处理所有树

### "Taxon is not monophyletic" (WARNING)
- 类群成员未形成单一支系
- 检查分类学分配是否正确
- 使用 `--strict` 在非单系群时强制终止

### "Duplicate sequence IDs" (ERROR)
- 在 FASTA 文件中重命名重复序列
- 确保所有序列 ID 唯一

### "Negative branch lengths" (CRITICAL, exit 3)
- 重新检查树构建方法
- 树文件可能已损坏

### "Malicious characters detected" (ERROR)
- 节点名称包含控制字符或双向文本覆盖符
- 清理输入数据

### "Circular dependency in taxonomy" (ERROR)
- 分类表格中存在冲突条目（如 A→B 且 B→A）
- 检查分类学分配的一致性

### "Empty file" (CRITICAL)
- 输入文件大小为 0 字节
- 检查文件是否正确传输/创建

### "No API key provided" (E013)
- 通过命令行 `--api-key` 传入
- 设置环境变量 `ITOL_API_KEY`
- 创建 `.itolapi.key` 文件，内容为纯文本 API Key
- 确保密钥文件权限安全：`chmod 600 .itolapi.key`

## 自检模式

```bash
pyitol self-test
```

输出示例：
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

退出码：0=全部通过，1=有失败
