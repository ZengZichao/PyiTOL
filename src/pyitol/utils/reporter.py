"""Reporter and error message management."""

from __future__ import annotations

# Re-export from session.py for backward compatibility
from pyitol.utils.session import create_session_log  # noqa: F401

ERROR_CODE_TABLE = {
    "E001": ("FileNotFoundError", "文件未找到：请检查输入文件路径是否正确。"),
    "E002": ("ValueError", "参数错误：提供的参数值不合法或格式不正确。"),
    "E003": ("ConnectionError", "网络连接失败：请检查网络或iTOL服务器状态。"),
    "E004": ("TimeoutError", "操作超时：服务器响应时间过长，请重试。"),
    "E005": ("PermissionError", "权限错误：没有写入目标目录的权限。"),
    "E006": ("SchemaValidationError", "模板验证失败：模板格式不符合iTOL v7规范。"),
    "E007": ("TreeParseError", "树文件解析失败：无法识别Newick/Nexus格式。"),
    "E008": ("MetadataParseError", "元数据解析失败：表格文件格式错误或列不匹配。"),
    "E009": ("ColorCodeError", "颜色代码非法：请使用十六进制颜色值如#ff0000。"),
    "E010": ("SeparatorConflictError", "分隔符冲突：数据中使用了非法分隔符。"),
    "E011": ("MissingColumnError", "缺少必要列：请检查输入表格的列名是否正确。"),
    "E012": ("TaxaNotFoundError", "物种未找到：分类表格中的物种不在树文件中。"),
    "E013": ("APIKeyError", "API密钥错误：请检查.itolapi.key文件内容。"),
    "E014": ("UploadError", "上传失败：iTOL服务器返回错误响应。"),
    "E015": ("ExportError", "导出失败：iTOL渲染未完成或格式不支持。"),
    # Extended internal error codes
    "E016": ("SessionError", "会话错误：无法加载或保存会话快照，请检查文件路径和权限。"),
    "E017": ("ReplayError", "复现失败：快照中缺少必要的参数或文件，请检查session.yaml内容。"),
    "E018": ("TemplateTypeError", "模板类型错误：不支持的模板类型，请检查类型名称拼写。"),
    "E019": ("FileFormatError", "文件格式不支持：请使用Newick、Nexus、CSV或Excel格式。"),
    "E020": ("FileTooLargeError", "文件过大：单个文件或总上传大小超过iTOL限制（2MB）。"),
    "E021": ("SpecialCharacterError", "特殊字符错误：节点ID包含空格或非法符号，建议替换为下划线。"),
    "E022": ("NodeIDMismatchError", "节点ID不匹配：元数据中的ID与树文件中的节点名称不一致。"),
    "E023": ("QuotaExceededError", "配额超限：已达到iTOL账户的树数量或存储上限，请删除旧树后重试。"),
    "E024": ("RateLimitError", "请求过于频繁：已触发iTOL速率限制，请降低请求频率后重试。"),
    "E025": ("ServerMaintenanceError", "服务器维护：iTOL服务器正在维护中，请稍后重试。"),
    "E026": ("RenderingError", "渲染失败：iTOL服务器无法渲染该树，可能树过于复杂或数据集不兼容。"),
    "E027": ("TreeNotFoundError", "树未找到：指定的tree_id不存在或已被删除，请检查后重试。"),
    "E028": ("DuplicateTreeError", "树已存在：同名的树已存在于iTOL账户中，请更换tree_name。"),
    "E029": ("DatasetIncompatibleError", "数据集不兼容：模板格式与树结构不匹配，请检查模板类型和数据内容。"),
    "E030": ("ColumnMismatchError", "列不匹配：输入表格的列数或列名与预期不符，请检查数据文件。"),
    "E031": ("NetworkTimeoutError", "网络超时：连接iTOL服务器超时，请检查网络并重试。"),
    "E032": ("SSLError", "SSL证书错误：无法建立安全连接，请检查系统时间或代理设置。"),
    "E033": ("DNSLookupError", "DNS解析失败：无法解析iTOL服务器地址，请检查网络配置。"),
    "E034": ("BadGatewayError", "网关错误：iTOL上游服务异常，请稍后重试。"),
    "E035": ("GatewayTimeoutError", "网关超时：iTOL服务器响应超时，请稍后重试。"),
    "E036": ("ServiceUnavailableError", "服务不可用：iTOL服务器当前无法处理请求，请稍后重试。"),
    "E037": ("AuthenticationExpiredError", "认证过期：API Key已过期，请重新获取或更新密钥。"),
    "E038": ("AccountSuspendedError", "账户已暂停：iTOL账户已被暂停，请联系iTOL支持团队。"),
    "E039": ("AccessDeniedError", "访问被拒绝：当前API Key无权执行此操作，请检查权限配置。"),
    "E040": ("EmptyFileError", "空文件错误：上传的文件内容为空，请检查文件是否损坏。"),
    "E041": ("CorruptFileError", "文件损坏：上传的文件无法解析，请检查文件完整性。"),
    "E042": ("ExtensionNotAllowedError", "文件扩展名不允许：请使用iTOL支持的文件格式。"),
    "E043": ("LegendError", "图例错误：图例参数设置不正确，请检查LEGEND相关配置。"),
    "E044": ("HeaderError", "模板头部错误：模板头部参数缺失或格式错误，请检查HEADER区。"),
    "E045": ("CanvasTooLargeError", "画布过大：导出尺寸超出iTOL限制，请减小dpi或宽高。"),
    "E046": ("FontNotFoundError", "字体未找到：iTOL服务器缺少指定字体，请使用默认字体。"),
    "E047": ("ImageGenerationError", "图像生成失败：iTOL无法生成图像，请尝试其他格式。"),
    "E048": ("TreeTooComplexError", "树结构过于复杂：节点数或分支数过多，建议简化树结构。"),
    "E049": ("StorageFullError", "存储空间已满：iTOL账户存储空间不足，请删除旧文件。"),
    "E050": ("MaxTreesReachedError", "达到最大树数量：iTOL账户中树的数量已达上限，请删除旧树。"),
    "E051": ("TreeLockedError", "树已锁定：该树当前被锁定，无法修改或删除，请稍后再试。"),
    "E052": ("InvalidColumnError", "无效列：指定的列名在数据中不存在，请检查列名拼写。"),
    "E053": ("DataSeparatorConflictError", "分隔符冲突：数据内容中包含与分隔符相同的字符，请更换分隔符。"),
    "E054": ("DataFormatError", "数据格式错误：模板数据区格式不正确，请对照iTOL v7规范检查。"),
    "E055": ("UnsupportedFormatError", "不支持的导出格式：请使用svg、png或pdf格式。"),
}


# iTOL API dynamic error message translation
# Maps common iTOL API English error messages to friendly Chinese suggestions
ITOL_API_ERROR_TRANSLATIONS = {
    # --- Authentication ---
    "invalid api key": "API Key 无效：请检查 --api-key 参数或 .itolapi.key 文件中的密钥是否正确。",
    "api key": "API Key 错误：请检查密钥是否有效或已过期。",
    "invalid project name": "无效的 iTOL 项目名称：请确认 --dataset-name 对应的 project 已预先在 iTOL 账户中创建，且当前 API Key 具有 batch upload 权限（需 active standard subscription）。",  # noqa: E501
    "unauthorized": "未授权：API Key 无效或权限不足，请检查密钥配置。",
    "authentication": "认证失败：请检查 API Key 是否正确，或账户是否被暂停。",
    "access denied": "访问被拒绝：当前 API Key 无权执行此操作，请检查账户权限。",
    "forbidden": "请求被禁止：请确认 API Key 具有执行该操作的权限。",
    "login required": "需要登录：会话已过期，请重新验证 API Key。",
    "session expired": "会话过期：请更新 API Key 或重新登录 iTOL 获取新密钥。",
    "account suspended": "账户已暂停：请联系 iTOL 支持团队了解详情并恢复账户。",
    "key revoked": "API Key 已被撤销：请登录 iTOL 重新生成 API Key。",
    # --- File ---
    "tree file too large": "树文件过大：iTOL 限制上传文件总大小不超过 2MB。建议简化树文件或减少模板数据量。",
    "file too large": "文件过大：iTOL 限制上传文件总大小不超过 2MB。建议压缩数据。",
    "upload file size": "上传文件过大：iTOL 限制上传文件总大小不超过 2MB。",
    "tree format": "树文件格式错误：请确保文件为标准的 Newick 或 Nexus 格式。",
    "invalid tree": "树文件无效：请检查 Newick/Nexus 格式是否正确，节点ID是否包含特殊字符。",
    "node id": "节点ID包含特殊字符：建议将节点ID中的空格替换为下划线，移除非法符号。",
    "special character": "特殊字符错误：节点ID或标签中包含iTOL不支持的字符，建议清理后再上传。",
    "format not supported": "文件格式不支持：iTOL 仅支持 Newick、Nexus 等格式，请转换后重试。",
    "extension not allowed": "文件扩展名不允许：请检查文件扩展名是否符合 iTOL 要求。",
    "empty file": "空文件错误：上传的文件内容为空，请检查文件是否损坏或未正确保存。",
    "corrupt file": "文件损坏：上传的文件无法解析，请检查文件完整性或重新生成。",
    "duplicate file": "重复文件：检测到同名文件已上传，请更换文件名或先删除旧文件。",
    # --- Template / Dataset ---
    "template format": "模板格式错误：请检查生成的模板文件是否符合 iTOL v7 规范。",
    "dataset format": "数据集格式错误：请检查数据列是否完整，分隔符是否与数据内容冲突。",
    "separator conflict": "分隔符冲突：数据内容中包含了当前分隔符字符，请在生成模板时更换分隔符。",
    "missing columns": "缺少必要列：模板数据区缺少必需的列，请检查输入数据文件。",
    "invalid column": "列无效：指定的列不存在或类型不匹配，请检查列名和数据内容。",
    "column mismatch": "列不匹配：数据列数或列名与模板定义不符，请检查数据文件。",
    "header error": "模板头部错误：HEADER 区参数缺失或格式错误，请对照 iTOL v7 规范检查。",
    "legend error": "图例错误：LEGEND 区配置不正确，请检查 LEGEND_TITLE、LEGEND_SHAPES 等参数。",
    "data format": "数据格式错误：DATA 区格式不符合要求，请检查每行字段数是否正确。",
    # --- Network ---
    "timeout": "服务器超时：iTOL 响应时间过长，请稍后重试。",
    "connection refused": "连接被拒绝：无法连接到 iTOL 服务器，请检查网络或防火墙设置。",
    "dns": "DNS 解析失败：无法解析 iTOL 服务器地址，请检查网络配置。",
    "network error": "网络错误：请检查本地网络连接是否正常。",
    "rate limit": "请求过于频繁：请稍后重试，或降低批量操作的速度。",
    "too many requests": "请求过于频繁：已触发速率限制，请降低请求频率后重试。",
    "server unavailable": "服务暂时不可用：iTOL 服务器负载过高，请稍后重试。",
    "bad gateway": "网关错误：iTOL 上游服务异常，请稍后重试。",
    "gateway timeout": "网关超时：iTOL 服务器响应超时，请稍后重试。",
    "ssl": "SSL 证书错误：无法建立安全连接，请检查系统时间或代理设置。",
    # --- Rendering ---
    "rendering": "渲染失败：iTOL 服务器渲染超时，请稍后重试或减小树规模。",
    "rendering failed": "渲染失败：iTOL 无法完成渲染，请检查树文件和数据集是否兼容。",
    "tree too complex": "树结构过于复杂：节点数或分支数超出 iTOL 处理能力，建议简化树结构。",
    "dataset incompatible": "数据集不兼容：当前数据集与树结构不匹配，请检查模板类型和数据内容。",
    "render timeout": "渲染超时：iTOL 渲染时间过长，请减小树规模或数据集数量后重试。",
    "canvas too large": "画布过大：导出尺寸超出 iTOL 限制，请减小 dpi 或输出宽高。",
    "font not found": "字体未找到：iTOL 服务器缺少指定字体，请使用默认字体或常用字体。",
    "image generation": "图像生成失败：iTOL 无法生成图像，请尝试其他导出格式或降低分辨率。",
    # --- Resource ---
    "tree not found": "树未找到：请检查 tree_id 是否正确，或该树是否已被删除。",
    "not found": "资源未找到：请检查 tree_id 或文件名是否正确。",
    "already exists": "树已存在：同名的树已存在于 iTOL 账户中，请更换 tree_name 或先删除旧树。",
    "quota exceeded": "配额超限：已达到 iTOL 账户的树数量或存储上限，请删除旧树后重试。",
    "storage full": "存储空间已满：iTOL 账户存储空间不足，请清理旧文件后重试。",
    "max trees reached": "达到最大树数量：iTOL 账户中树的数量已达上限，请删除不再使用的树。",
    "tree locked": "树已锁定：该树当前被锁定，无法修改或删除，请稍后再试。",
    # --- Server ---
    "server error": "iTOL 服务器内部错误：请稍后重试，或联系 iTOL 支持团队。",
    "maintenance": "iTOL 服务器维护中：请稍后重试。",
    "internal error": "iTOL 内部错误：请稍后重试，如果持续出现请联系 iTOL 支持。",
}


def translate_itol_api_error(error_text: str) -> str:
    """Translate iTOL API error text to user-friendly Chinese message."""
    text_lower = error_text.lower()
    for keyword, suggestion in ITOL_API_ERROR_TRANSLATIONS.items():
        if keyword in text_lower:
            return f"[iTOL API] {suggestion} (原始信息: {error_text})"
    return f"[iTOL API] 操作失败: {error_text}"


def get_error_message(error_code: str) -> str:
    """Get error message by error code."""
    entry = ERROR_CODE_TABLE.get(error_code)
    if entry:
        return entry[1]
    return f"未知错误: {error_code}"


# --- O(1) lookup structures derived from ERROR_CODE_TABLE (single source) ---

# Error types whose translated message embeds the raw error text via a
# ``{msg}`` placeholder (e.g. ``参数错误：{msg}``).
_INTERPOLATED_TYPES: frozenset[str] = frozenset(
    {
        "ValueError",
        "SchemaValidationError",
        "SessionError",
        "ReplayError",
        "TreeParseError",
        "MetadataParseError",
        "APIKeyError",
        "UploadError",
        "ExportError",
        "MissingColumnError",
        "TaxaNotFoundError",
        "TemplateTypeError",
        "InvalidColumnError",
        "FileFormatError",
        "FileTooLargeError",
        "SpecialCharacterError",
        "NodeIDMismatchError",
        "SeparatorConflictError",
        "DataFormatError",
        "UnsupportedFormatError",
    }
)

# A few error types use a shorter interpolation template than the base table
# message; everything else is derived from ERROR_CODE_TABLE so the table
# remains the single source of truth (no duplicated Chinese strings).
_INTERPOLATED_OVERRIDES: dict[str, str] = {
    "ValueError": "参数错误：{msg}",
}

# Build interpolation templates directly from ERROR_CODE_TABLE.
_INTERPOLATED_MSG: dict[str, str] = {
    exc: _INTERPOLATED_OVERRIDES.get(exc, f"{msg} 详情：{{msg}}")
    for _code, (exc, msg) in ERROR_CODE_TABLE.items()
    if exc in _INTERPOLATED_TYPES
}

# O(1) reverse lookup: exception class name -> (error_code, message).
_ERROR_CODE_BY_EXC: dict[str, tuple[str, str]] = {exc: (code, msg) for code, (exc, msg) in ERROR_CODE_TABLE.items()}


def translate_error(error_type: str, error_msg: str) -> str:
    """Translate raw errors to user-friendly messages.

    Uses ERROR_CODE_TABLE as the single source of truth. Errors listed in
    :data:`_INTERPOLATED_TYPES` embed the raw error text via a ``{msg}``
    placeholder; all others append ``详情：{error_msg}``. Lookups are O(1).
    """
    if error_type in _INTERPOLATED_TYPES:
        return _INTERPOLATED_MSG[error_type].format(msg=error_msg)

    entry = _ERROR_CODE_BY_EXC.get(error_type)
    if entry is not None:
        _code, msg = entry
        return f"{msg} 详情：{error_msg}"

    return f"{error_type}: {error_msg}"


def translate_errors(errors: list[str]) -> list[str]:
    """Translate a list of errors using O(1) table lookups."""
    translated = []
    for err in errors:
        matched = False
        for exc_name, (code, msg) in _ERROR_CODE_BY_EXC.items():
            if exc_name in err:
                translated.append(f"[{code}] {msg}")
                matched = True
                break
        if not matched:
            translated.append(err)
    return translated


def format_result_summary(
    command: str,
    status: str,
    outputs: dict[str, str] | None = None,
    errors: list[str] | None = None,
) -> str:
    """Format a human-readable result summary."""
    lines = [f"Command: {command}", f"Status: {status}"]

    if outputs:
        lines.append("Outputs:")
        for key, value in outputs.items():
            lines.append(f"  {key}: {value}")

    if errors:
        lines.append("Errors:")
        for e in errors:
            lines.append(f"  - {e}")

    return "\n".join(lines)
