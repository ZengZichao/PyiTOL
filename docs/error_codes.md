# PyiTOL 错误码参考

[English](error_codes_en.md) | 中文

## 退出码

| 退出码 | 含义 | 描述 |
|------|---------|-------------|
| 0 | 成功 | 操作正常完成 |
| 1 | 运行时错误 | 内部错误、依赖问题、API 失败、连接/超时/权限错误 |
| 2 | 参数错误 | 无效的 CLI 参数、验证失败、ValueError |
| 3 | 数据错误 | 输入文件格式/内容错误、模板错误、文件未找到 |
| 130 | 用户中断 | 收到 SIGINT (Ctrl+C) |

退出码由 `src/pyitol/cli/main.py` 的 `main()` 函数根据异常类型映射（`src/pyitol/cli/main.py:1192-1274`）；个别命令也会直接抛出 `typer.Exit`，例如 `pyitol validate` 在出现验证错误时抛出退出码 3（`src/pyitol/cli/main.py:404`）。

## 结构化错误码

PyiTOL 在 `src/pyitol/utils/reporter.py` 的 `ERROR_CODE_TABLE` 中定义了 E001–E055 共 55 个结构化错误码；每个条目的值是二元组 `(错误标签, 中文错误描述)`，本身不带级别字段——表中所有条目都是错误型标签，没有 warning/info 之分。下表第二列就是这个元组的第一个字段（标签字符串）：E001–E005 是 Python 内置异常名；E006–E022、E052、E054、E055 与 `src/pyitol/exceptions.py` 中定义的同名异常类一致；E023–E051 与 E053 共 30 个标签在代码中并没有同名异常类，仅是本表的显示字符串（例如 E053 的 `DataSeparatorConflictError`，`src/pyitol/utils/reporter.py:62`）。描述文案在代码中只有中文一种，没有英文回退，因此下表第三列即代码内置的中文原文（未作翻译）；`get_error_message()` 找不到代码时返回 `未知错误: {code}`（`src/pyitol/utils/reporter.py:150-155`）。在 `src/pyitol/` 内真正被调用的 reporter 函数只有 `translate_itol_api_error()`（由 `src/pyitol/api/client.py:21` 引入），`get_error_message()`、`translate_error()`、`translate_errors()`、`format_result_summary()` 仅被 `tests/` 调用，因此 `[E0NN]` 形式的错误码不会出现在 `pyitol` 命令的输出里。

### 基础错误 (E001–E015)

| 代码 | 错误标签 | 描述 |
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

| 代码 | 错误标签 | 描述 |
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

| 代码 | 错误标签 | 描述 |
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

| 代码 | 错误标签 | 描述 |
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
| E053 | DataSeparatorConflictError | 分隔符冲突：数据内容中包含与分隔符相同的字符，请更换分隔符。 |
| E054 | DataFormatError | 数据格式错误：模板数据区格式不正确，请对照iTOL v7规范检查。 |
| E055 | UnsupportedFormatError | 不支持的导出格式：请使用svg、png或pdf格式。 |

术语说明：E010 与 E053 的标签 `SeparatorConflictError`、`DataSeparatorConflictError`（`src/pyitol/utils/reporter.py:18,62`）以及 `ITOL_API_ERROR_TRANSLATIONS` 的关键字 `"separator conflict"`（`src/pyitol/utils/reporter.py:99`）用的是 "separator"，三处对应的中文描述也都写作"分隔符冲突：…"；而校验器的 V005 常量名为 `DELIMITER_CONFLICT`（`src/pyitol/core/validator.py:80`），英文文案是 `Delimiter conflict: row {0}, column '{1}' contains '{2}': {3}`（`src/pyitol/core/validator.py:135`）、中文文案是 `分隔符冲突: 行 {0}, 列 '{1}' 的值包含 '{2}': {3}`（`src/pyitol/core/validator.py:109`），由 `check_delimiter_conflict()` 产生（`src/pyitol/core/validator.py:360-388`）。这是两个模块各自的两套文案，不应互相替换。

## 验证错误 (V001-V024)

验证消息由 `src/pyitol/core/validator.py` 产生，本身不是异常类，而是作为 `validate` 命令的输出信息。文案来自双语字典 `_ERROR_MESSAGES` 的 `"zh"` / `"en"` 两个子表（`src/pyitol/core/validator.py:103-156`）：默认语言是中文（`src/pyitol/core/validator.py:158-160`），语言由 `set_error_language()` 按线程切换（`src/pyitol/core/validator.py:174-181`），传入未知语言时同样回退到中文而不是英文（`src/pyitol/core/validator.py:166`）。包内没有任何代码调用 `set_error_language()`，CLI 选项和配置文件也不提供语言开关，因此命令行用户看到的始终是下表中的中文原文；英文文案只有在 Python 代码里显式调用 `set_error_language("en")` 后才会输出。ERROR/CRITICAL 级消息会让 `pyitol validate` 以退出码 3 结束（`src/pyitol/cli/main.py:399-404`）；`TemplateValidator.raise_if_errors()` 抛出的 `TemplateValidationError` 则映射到退出码 2（`src/pyitol/cli/main.py:1228-1232`）。下表描述列即代码内置的中文文案原文，其中 `{0}`、`{1}` 等为运行时填充的占位符。

| 代码 | 级别 | 描述 |
|------|-------|-------------|
| V001 | ERROR | 颜色代码不能为空 |
| V002 | ERROR | 颜色代码缺少#前缀，建议改为 #{0} |
| V003 | ERROR | 颜色代码长度不正确，应为 #RRGGBB (6位十六进制) |
| V004 | ERROR | 非法颜色代码: {0}，请使用 #RRGGBB、rgb()、hsl() 或命名颜色格式 |
| V005 | ERROR | 分隔符冲突: 行 {0}, 列 '{1}' 的值包含 '{2}': {3} |
| V006 | WARNING | 分类变量过多警告: 列 '{0}' 有 {1} 个唯一值，超过建议上限 {2}，可能导致图例重叠和渲染问题 |
| V007 | WARNING | 数值范围警告: 列 '{0}' 最小值 {1:.2f} 低于生物学合理下限 {2} |
| V008 | WARNING | 数值范围警告: 列 '{0}' 最大值 {1:.2f} 超过生物学合理上限 {2} |
| V009 | WARNING† | 孤立节点: {0} 个 metadata ID 不在树文件中，例如: {1} |
| V010 | WARNING† | 缺失注释: {0} 个树节点在 metadata 中无对应记录，例如: {1} |
| V011 | WARNING† | 节点ID包含特殊符号: {0} 个节点 ID 包含空格/tab/逗号/分号/竖线，建议替换为下划线。例如: {1} |
| V012 | ERROR | 文件不存在: {0} |
| V013 | ERROR | 文件为空: {0} |
| V014 | WARNING | 文件格式可能不正确: {0} |
| V015 | ERROR | 模板文件缺少 iTOL 头部标识: {0} |
| V016 | WARNING | 模板文件未指定分隔符: {0} |
| V017 | ERROR | 解析失败: {0} |
| V018 | WARNING | 不支持的树文件格式: {0}。支持的格式: Newick (.nwk/.newick/.tree/.tre), Nexus (.nexus/.nex), PhyloXML (.xml) |
| V019 | WARNING | 不支持的序列文件格式: {0}。支持的格式: FASTA (.fa/.fasta/.fna), FASTQ (.fq/.fastq), GenBank (.gb/.gbk), Phylip (.phy/.phylip) |
| V020 | ERROR† | 树文件内容格式不正确: {0} |
| V021 | ERROR | 序列文件内容格式不正确: {0} |
| V022 | ERROR | 节点名包含恶意字符(控制字符或双向文本): {0} |
| V023 | ERROR | 分类表格中检测到循环依赖: {0} |
| V024 | CRITICAL | 文件为空，无法处理: {0} |

级别列的依据是代码把消息放进了哪个列表，`pyitol validate` 再据此打印 `ERR` / `WARN` / `CRIT`（一处例外：分类表格的文件检查结果虽打印为 `ERR`，但不设置错误标志，单独出现时不会改变退出码，`src/pyitol/cli/main.py:367-368`）：

- ERROR：V001–V005、V012、V013、V015、V017、V021–V023。颜色校验失败时 `validate_color_code()` 返回 `(False, 文案)`，`validate_color_codes()` 将其并入 `errors`（`src/pyitol/core/validator.py:334,350-357`），所以 V002 虽以"建议"措辞、级别仍是 ERROR；V005 由 `check_delimiter_conflict()` 返回并经 `TemplateValidator.validate_dataframe()` 并入 `self.errors`（`src/pyitol/core/validator.py:1489-1491`）。
- WARNING：V006、V007、V008 由 `validate_dataframe()` 并入 `self.warnings`（`src/pyitol/core/validator.py:1493-1503`）——V006 在 `check_categorical_cardinality()` 内部虽然用名为 `errors` 的局部列表返回（`src/pyitol/core/validator.py:397-403`），其唯一调用方仍把它归入 warnings；V014、V016、V018、V019 分别进入 `warnings`（`src/pyitol/core/validator.py:1423,1472,681,687`）。
- CRITICAL：V024 由 `validate_file_not_empty()` 返回，`pyitol validate` 打印为 `CRIT` 并置错误标志（`src/pyitol/cli/main.py:283-286`）。
- 标 † 的 V009–V011 只由 `check_tree_ids_against_metadata()` / `check_special_characters_in_ids()` 返回（`src/pyitol/core/validator.py:451-494`），而这两个函数目前仅被 `tests/` 调用；V020 的消息模板 `ErrorCode.INVALID_TREE_CONTENT`（`src/pyitol/core/validator.py:95,124,150`）在包内（含 `tests/`）没有任何引用点。这些消息在运行时不会输出，表中对应的级别是按文案语义推定，而非代码实际路由的结果。树内容类错误实际使用的是不带 V 码的硬编码消息（如 `Bracket mismatch: …`、`CRITICAL: Negative branch lengths detected …`，`src/pyitol/core/validator.py:942-1074`）。

## 日志级别

| 级别 | 描述 |
|-------|-------------|
| DEBUG | 详细调试信息 |
| INFO | 正常操作消息 |
| WARNING | 警告消息（非致命） |
| ERROR | 错误消息 |
| CRITICAL | 严重错误（立即退出） |

日志级别输出全称，右侧补空格对齐至 9 个字符宽度，不缩写（`src/pyitol/utils/logger.py:18-24`，未知级别同样用 `levelname.ljust(9)`，`src/pyitol/utils/logger.py:59`）。日志格式：`2025-03-21T10:15:30.123 | INFO     | message`；用 `--log-file` 写文件时级别字段为 `%(levelname)-8s`（8 个字符宽度，`src/pyitol/utils/logger.py:191-193`），DEBUG 级消息还会在末尾追加 `[模块:行号]`（`src/pyitol/utils/logger.py:61-64`）。

## 常见错误场景

### "Tree file not found" (E001/V012)
- 检查文件路径拼写
- 确认文件存在于指定位置
- 建议使用绝对路径

### "Multiple trees detected"（告警，按策略处理）
- 检测到多棵树时，`load_tree()` 先以 WARNING 输出每棵树的摘要，再按其 `multi_tree` 形参指定的策略处理，不必然以错误码退出（`src/pyitol/core/parser.py:216-249`）。命令行目前只有 `taxonomy monophyly` 与 `taxonomy check-and-style` 声明 `--multi-tree-mode`，且两者都不转发该值；其余命令以源码内硬编码的策略调用库函数：
  - `ask`：默认。非交互终端自动回退到 `first`；交互终端下抛出 `TreeParseError` 并列出可选策略（退出码 3）
  - `first`：仅使用第一棵树
  - `last`：仅使用最后一棵树
  - `split`：分别处理所有树（代码内部等价别名 `all`）

### "Taxon is not monophyletic" (WARNING)
- 类群成员未形成单系群（clade）
- 检查分类学分配是否正确
- 在 `template create-collapse` 中，非单系群打印为 `WARN` 并跳过（`src/pyitol/cli/template_treeops.py:233`），加 `--strict` 才以退出码 1 终止（`src/pyitol/cli/template_treeops.py:246-247`）
- 在 `taxonomy` 的类群操作中，并系群/复系群会直接以退出码 1 终止（`src/pyitol/cli/taxonomy_cmd.py:867-882`）

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

`pyitol self-test` 共执行 20 项检查：8 个依赖库 + 8 个内部模块 + 4 项功能自检（`src/pyitol/cli/main.py:1033-1184`）。输出示例（括号内的版本号按实际安装显示）：
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

退出码：0=全部通过，1=有失败
