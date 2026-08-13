"""Input validation and conflict detection for iTOL templates."""

from __future__ import annotations

import functools
import logging
import re
import threading
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import dendropy

import pandas as pd

# Import TemplateValidationError from exceptions.py instead of defining ValidationError
from pyitol.exceptions import TemplateValidationError as ValidationError

logger = logging.getLogger(__name__)


# File format constants
TREE_EXTENSIONS = {
    ".nwk",
    ".newick",
    ".tree",
    ".treefile",
    ".tre",
    ".rooted",
    ".nexus",
    ".nex",
    ".treex",
    ".phyloxml",
    ".xml",
    ".nhx",
    ".nhy",
}

SEQUENCE_EXTENSIONS = {
    ".fa",
    ".fasta",
    ".fna",
    ".ffn",
    ".faa",
    ".frn",
    ".fq",
    ".fastq",
    ".gb",
    ".gbk",
    ".genbank",
    ".gff",
    ".gff3",
    ".bed",
    ".aln",
    ".clustal",
    ".msf",
    ".phy",
    ".phylip",
}

TABLE_EXTENSIONS = {
    ".csv",
    ".tsv",
    ".txt",
    ".xlsx",
    ".xls",
}


# Error message codes for i18n support
# Prefixed with 'V' to avoid collision with reporter.py's E001-E055 codes.
class ErrorCode:
    """Error codes for structured error reporting."""

    EMPTY_COLOR = "V001"
    MISSING_HASH_PREFIX = "V002"
    INVALID_COLOR_LENGTH = "V003"
    INVALID_COLOR_FORMAT = "V004"
    DELIMITER_CONFLICT = "V005"
    HIGH_CARDINALITY = "V006"
    RANGE_BELOW_MIN = "V007"
    RANGE_ABOVE_MAX = "V008"
    ORPHAN_NODES = "V009"
    MISSING_ANNOTATIONS = "V010"
    SPECIAL_CHARS_IN_ID = "V011"
    FILE_NOT_FOUND = "V012"
    FILE_EMPTY = "V013"
    INVALID_FORMAT = "V014"
    MISSING_HEADER = "V015"
    MISSING_SEPARATOR = "V016"
    PARSE_FAILED = "V017"
    UNSUPPORTED_TREE_FORMAT = "V018"
    UNSUPPORTED_SEQ_FORMAT = "V019"
    INVALID_TREE_CONTENT = "V020"
    INVALID_SEQ_CONTENT = "V021"
    MALICIOUS_NODE_NAME = "V022"
    CIRCULAR_DEPENDENCY = "V023"
    FILE_EMPTY_CRITICAL = "V024"


# Bilingual error message templates
_ERROR_MESSAGES = {
    "zh": {
        ErrorCode.EMPTY_COLOR: "颜色代码不能为空",
        ErrorCode.MISSING_HASH_PREFIX: "颜色代码缺少#前缀，建议改为 #{0}",
        ErrorCode.INVALID_COLOR_LENGTH: "颜色代码长度不正确，应为 #RRGGBB (6位十六进制)",
        ErrorCode.INVALID_COLOR_FORMAT: "非法颜色代码: {0}，请使用 #RRGGBB、rgb()、hsl() 或命名颜色格式",
        ErrorCode.DELIMITER_CONFLICT: "分隔符冲突: 行 {0}, 列 '{1}' 的值包含 '{2}': {3}",
        ErrorCode.HIGH_CARDINALITY: "分类变量过多警告: 列 '{0}' 有 {1} 个唯一值，超过建议上限 {2}，可能导致图例重叠和渲染问题",  # noqa: E501
        ErrorCode.RANGE_BELOW_MIN: "数值范围警告: 列 '{0}' 最小值 {1:.2f} 低于生物学合理下限 {2}",
        ErrorCode.RANGE_ABOVE_MAX: "数值范围警告: 列 '{0}' 最大值 {1:.2f} 超过生物学合理上限 {2}",
        ErrorCode.ORPHAN_NODES: "孤立节点: {0} 个 metadata ID 不在树文件中，例如: {1}",
        ErrorCode.MISSING_ANNOTATIONS: "缺失注释: {0} 个树节点在 metadata 中无对应记录，例如: {1}",
        ErrorCode.SPECIAL_CHARS_IN_ID: "节点ID包含特殊符号: {0} 个节点 ID 包含空格/tab/逗号/分号/竖线，建议替换为下划线。例如: {1}",  # noqa: E501
        ErrorCode.FILE_NOT_FOUND: "文件不存在: {0}",
        ErrorCode.FILE_EMPTY: "文件为空: {0}",
        ErrorCode.INVALID_FORMAT: "文件格式可能不正确: {0}",
        ErrorCode.MISSING_HEADER: "模板文件缺少 iTOL 头部标识: {0}",
        ErrorCode.MISSING_SEPARATOR: "模板文件未指定分隔符: {0}",
        ErrorCode.PARSE_FAILED: "解析失败: {0}",
        ErrorCode.UNSUPPORTED_TREE_FORMAT: "不支持的树文件格式: {0}。支持的格式: Newick (.nwk/.newick/.tree/.tre), Nexus (.nexus/.nex), PhyloXML (.xml)",  # noqa: E501
        ErrorCode.UNSUPPORTED_SEQ_FORMAT: "不支持的序列文件格式: {0}。支持的格式: FASTA (.fa/.fasta/.fna), FASTQ (.fq/.fastq), GenBank (.gb/.gbk), Phylip (.phy/.phylip)",  # noqa: E501
        ErrorCode.INVALID_TREE_CONTENT: "树文件内容格式不正确: {0}",
        ErrorCode.INVALID_SEQ_CONTENT: "序列文件内容格式不正确: {0}",
        ErrorCode.MALICIOUS_NODE_NAME: "节点名包含恶意字符(控制字符或双向文本): {0}",
        ErrorCode.CIRCULAR_DEPENDENCY: "分类表格中检测到循环依赖: {0}",
        ErrorCode.FILE_EMPTY_CRITICAL: "文件为空，无法处理: {0}",
    },
    "en": {
        ErrorCode.EMPTY_COLOR: "Color code cannot be empty",
        ErrorCode.MISSING_HASH_PREFIX: "Color code missing # prefix, suggest: #{0}",
        ErrorCode.INVALID_COLOR_LENGTH: "Invalid color code length, should be #RRGGBB (6 hex digits)",
        ErrorCode.INVALID_COLOR_FORMAT: "Invalid color code: {0}. Use #RRGGBB, rgb(), hsl(), or named color format",
        ErrorCode.DELIMITER_CONFLICT: "Delimiter conflict: row {0}, column '{1}' contains '{2}': {3}",
        ErrorCode.HIGH_CARDINALITY: "High cardinality warning: column '{0}' has {1} unique values, exceeds recommended limit {2}",  # noqa: E501
        ErrorCode.RANGE_BELOW_MIN: "Numeric range warning: column '{0}' minimum {1:.2f} below biological lower bound {2}",  # noqa: E501
        ErrorCode.RANGE_ABOVE_MAX: "Numeric range warning: column '{0}' maximum {1:.2f} exceeds biological upper bound {2}",  # noqa: E501
        ErrorCode.ORPHAN_NODES: "Orphan nodes: {0} metadata IDs not in tree file, e.g.: {1}",
        ErrorCode.MISSING_ANNOTATIONS: "Missing annotations: {0} tree nodes not in metadata, e.g.: {1}",
        ErrorCode.SPECIAL_CHARS_IN_ID: "Special characters in IDs: {0} node IDs contain spaces/tabs/commas/semicolons/pipes, e.g.: {1}",  # noqa: E501
        ErrorCode.FILE_NOT_FOUND: "File not found: {0}",
        ErrorCode.FILE_EMPTY: "File is empty: {0}",
        ErrorCode.INVALID_FORMAT: "File format may be incorrect: {0}",
        ErrorCode.MISSING_HEADER: "Template file missing iTOL header identifier: {0}",
        ErrorCode.MISSING_SEPARATOR: "Template file missing separator specification: {0}",
        ErrorCode.PARSE_FAILED: "Parse failed: {0}",
        ErrorCode.UNSUPPORTED_TREE_FORMAT: "Unsupported tree file format: {0}. Supported: Newick (.nwk/.newick/.tree/.tre), Nexus (.nexus/.nex), PhyloXML (.xml)",  # noqa: E501
        ErrorCode.UNSUPPORTED_SEQ_FORMAT: "Unsupported sequence file format: {0}. Supported: FASTA (.fa/.fasta/.fna), FASTQ (.fq/.fastq), GenBank (.gb/.gbk), Phylip (.phy/.phylip)",  # noqa: E501
        ErrorCode.INVALID_TREE_CONTENT: "Invalid tree file content: {0}",
        ErrorCode.INVALID_SEQ_CONTENT: "Invalid sequence file content: {0}",
        ErrorCode.MALICIOUS_NODE_NAME: "Node name contains malicious characters (control chars or bidi text): {0}",
        ErrorCode.CIRCULAR_DEPENDENCY: "Circular dependency detected in taxonomy table: {0}",
        ErrorCode.FILE_EMPTY_CRITICAL: "File is empty, cannot process: {0}",
    },
}

# Default language (m4: Thread-safe using threading.local)
_lang_state = threading.local()
_lang_state.default = "zh"


def _get_error_message(code: str, *args: object, lang: str | None = None) -> str:
    """Get localized error message by code."""
    resolved_lang: str = lang if lang is not None else getattr(_lang_state, "default", "zh")
    messages = _ERROR_MESSAGES.get(resolved_lang, _ERROR_MESSAGES["zh"])
    template = messages.get(code, code)
    try:
        return template.format(*args) if args else template
    except (IndexError, KeyError):
        return template


def set_error_language(lang: str) -> None:
    """Set the default language for error messages ('zh' or 'en').

    Note: This is thread-safe - each thread has its own language setting.
    """
    if lang in _ERROR_MESSAGES:
        _lang_state.default = lang


# Color code patterns
HEX_COLOR_PATTERN = re.compile(r"^#[0-9a-fA-F]{6}$")
HEX_COLOR_SHORT_PATTERN = re.compile(r"^#[0-9a-fA-F]{3}$")
RGB_PATTERN = re.compile(r"^rgb\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$", re.IGNORECASE)
RGBA_PATTERN = re.compile(r"^rgba\s*\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*[\d.]+\s*\)$", re.IGNORECASE)
HSL_PATTERN = re.compile(r"^hsl\s*\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*\)$", re.IGNORECASE)
HSLA_PATTERN = re.compile(r"^hsla\s*\(\s*\d+\s*,\s*\d+%?\s*,\s*\d+%?\s*,\s*[\d.]+\s*\)$", re.IGNORECASE)

# Named colors supported by iTOL (comprehensive CSS named colors subset)
# m5: Extended with more CSS named colors to reduce false validation failures
NAMED_COLORS = {
    # Basic colors
    "black",
    "white",
    "red",
    "green",
    "blue",
    "yellow",
    "cyan",
    "magenta",
    "orange",
    "purple",
    "pink",
    "brown",
    "gray",
    "grey",
    "lime",
    "navy",
    "teal",
    "olive",
    "silver",
    "maroon",
    "aqua",
    "fuchsia",
    "indigo",
    "violet",
    "crimson",
    "coral",
    "salmon",
    "gold",
    "khaki",
    "plum",
    "orchid",
    "tan",
    "beige",
    "ivory",
    "linen",
    "wheat",
    # Extended colors
    "darkred",
    "darkgreen",
    "darkblue",
    "darkcyan",
    "darkmagenta",
    "darkorange",
    "darkgray",
    "darkgrey",
    "darkkhaki",
    "darkolivegreen",
    "darkorchid",
    "darksalmon",
    "darkseagreen",
    "darkslateblue",
    "darkslategray",
    "darkslategrey",
    "darkturquoise",
    "darkviolet",
    "lightblue",
    "lightcoral",
    "lightcyan",
    "lightgoldenrodyellow",
    "lightgray",
    "lightgrey",
    "lightgreen",
    "lightpink",
    "lightsalmon",
    "lightseagreen",
    "lightskyblue",
    "lightslategray",
    "lightslategrey",
    "lightsteelblue",
    "lightyellow",
    "mediumaquamarine",
    "mediumblue",
    "mediumorchid",
    "mediumpurple",
    "mediumseagreen",
    "mediumslateblue",
    "mediumspringgreen",
    "mediumturquoise",
    "mediumvioletred",
    "midnightblue",
    "mintcream",
    "mistyrose",
    "moccasin",
    "navajowhite",
    "oldlace",
    "olivedrab",
    "orangered",
    "palegoldenrod",
    "palegreen",
    "paleturquoise",
    "palevioletred",
    "papayawhip",
    "peachpuff",
    "peru",
    "powderblue",
    "rosybrown",
    "royalblue",
    "saddlebrown",
    "sandybrown",
    "seagreen",
    "seashell",
    "sienna",
    "skyblue",
    "slateblue",
    "slategray",
    "slategrey",
    "snow",
    "springgreen",
    "steelblue",
    "thistle",
    "tomato",
    "turquoise",
    "whitesmoke",
    "yellowgreen",
}

# Patterns that may conflict with separators
TAB_CONFLICT_PATTERN = re.compile(r"\t")
COMMA_CONFLICT_PATTERN = re.compile(r",")
SPACE_CONFLICT_PATTERN = re.compile(r"\s+")


@functools.lru_cache(maxsize=512)
def _validate_color_code_cached(color: str, allow_rgb: bool = True) -> tuple[bool, str]:
    """Cached color validation (color must be hashable string)."""
    if not color:
        return False, _get_error_message(ErrorCode.EMPTY_COLOR)
    if HEX_COLOR_PATTERN.match(color):
        return True, ""
    if HEX_COLOR_SHORT_PATTERN.match(color):
        return True, ""
    if allow_rgb and (RGB_PATTERN.match(color) or RGBA_PATTERN.match(color)):
        return True, ""
    if allow_rgb and (HSL_PATTERN.match(color) or HSLA_PATTERN.match(color)):
        return True, ""
    if color.lower() in NAMED_COLORS:
        return True, ""
    # Try to suggest fix
    if re.match(r"^[0-9a-fA-F]{6}$", color):
        return False, _get_error_message(ErrorCode.MISSING_HASH_PREFIX, color)
    if re.match(r"^#[0-9a-fA-F]{5}$", color) or re.match(r"^#[0-9a-fA-F]{7,}$", color):
        return False, _get_error_message(ErrorCode.INVALID_COLOR_LENGTH)
    return False, _get_error_message(ErrorCode.INVALID_COLOR_FORMAT, color)


def validate_color_code(color: str, allow_rgb: bool = True) -> tuple[bool, str]:
    """Validate a single color code.

    Returns:
        (is_valid, suggestion)
    """
    color = str(color).strip()
    return _validate_color_code_cached(color, allow_rgb)


def validate_color_codes(colors: list[str]) -> list[str]:
    """Validate a list of color codes and return error messages."""
    errors: list[str] = []
    for color in colors:
        valid, suggestion = validate_color_code(color)
        if not valid:
            errors.append(f"Color error ({color}): {suggestion}")
    return errors


def check_delimiter_conflict(data: pd.DataFrame, separator: str = "TAB") -> list[str]:
    """Check if data content conflicts with the chosen separator.

    Uses vectorized string operations for better performance on large DataFrames.

    Args:
        data: DataFrame to check
        separator: TAB, SPACE, or COMMA
    """
    errors: list[str] = []
    sep_char = {"TAB": "\t", "SPACE": " ", "COMMA": ","}.get(separator, "\t")

    # For SPACE separator, only flag values that contain multiple consecutive
    # spaces or leading/trailing spaces (single embedded spaces are common in
    # biological names like "Homo sapiens" and should not be flagged).
    conflict_pattern = re.compile(r"  |^ | $") if separator == "SPACE" else None

    str_df = data.astype(str)
    if conflict_pattern is not None:
        mask = str_df.apply(lambda col: col.str.contains(conflict_pattern, na=False))
    else:
        mask = str_df.apply(lambda col: col.str.contains(sep_char, regex=False, na=False))

    conflict_rows, conflict_cols = mask.values.nonzero()
    for row_idx, col_idx in zip(conflict_rows, conflict_cols):
        col_name = data.columns[col_idx]
        val_str = str(data.iat[row_idx, col_idx]) if pd.notna(data.iat[row_idx, col_idx]) else ""
        errors.append(_get_error_message(ErrorCode.DELIMITER_CONFLICT, row_idx, col_name, sep_char, val_str[:50]))
    return errors


def check_categorical_cardinality(
    data: pd.DataFrame,
    column: str,
    max_categories: int = 50,
) -> list[str]:
    """Warn if a categorical column has too many unique values."""
    errors: list[str] = []
    if column not in data.columns:
        return errors
    n_unique = data[column].nunique(dropna=True)
    if n_unique > max_categories:
        errors.append(_get_error_message(ErrorCode.HIGH_CARDINALITY, column, n_unique, max_categories))
    return errors


# Common biological column ranges for auto-validation
_BIOLOGY_RANGES: dict[str, tuple[float | None, float | None]] = {
    "gc_content": (0.0, 100.0),
    "gc": (0.0, 100.0),
    "bootstrap": (0.0, 100.0),
    "support": (0.0, 100.0),
    "length": (0.0, None),
    "branch_length": (0.0, None),
}


def check_numeric_range(
    data: pd.DataFrame,
    column: str,
    min_val: float | None = None,
    max_val: float | None = None,
) -> list[str]:
    """Check if numeric values are within expected range."""
    errors: list[str] = []
    if column not in data.columns:
        return errors
    numeric = pd.to_numeric(data[column], errors="coerce")
    valid = numeric.dropna()
    if len(valid) == 0:
        return errors
    # Apply biology auto-ranges if no explicit bounds given
    col_lower = column.lower().strip().replace(" ", "_")
    if min_val is None and max_val is None and col_lower in _BIOLOGY_RANGES:
        auto_min, auto_max = _BIOLOGY_RANGES[col_lower]
        if auto_min is not None and valid.min() < auto_min:
            errors.append(_get_error_message(ErrorCode.RANGE_BELOW_MIN, column, valid.min(), auto_min))
        if auto_max is not None and valid.max() > auto_max:
            errors.append(_get_error_message(ErrorCode.RANGE_ABOVE_MAX, column, valid.max(), auto_max))
        return errors
    if min_val is not None and valid.min() < min_val:
        errors.append(
            f"Numeric range warning: column '{column}' minimum {valid.min()} below recommended minimum {min_val}"
        )
    if max_val is not None and valid.max() > max_val:
        errors.append(
            f"Numeric range warning: column '{column}' maximum {valid.max()} exceeds recommended maximum {max_val}"
        )
    return errors


def check_tree_ids_against_metadata(
    tree_ids: set[str],
    metadata_ids: set[str],
) -> list[str]:
    """Check for orphan nodes in metadata not present in tree."""
    errors: list[str] = []
    orphan = metadata_ids - tree_ids
    missing = tree_ids - metadata_ids
    if orphan:
        orphan_sample = list(orphan)[:10]
        errors.append(
            _get_error_message(
                ErrorCode.ORPHAN_NODES, len(orphan), ", ".join(orphan_sample) + ("..." if len(orphan) > 10 else "")
            )
        )
    if missing:
        missing_sample = list(missing)[:10]
        errors.append(
            _get_error_message(
                ErrorCode.MISSING_ANNOTATIONS,
                len(missing),
                ", ".join(missing_sample) + ("..." if len(missing) > 10 else ""),
            )
        )
    return errors


def check_special_characters_in_ids(ids: list[str]) -> list[str]:
    """Check for special characters in node IDs that may cause iTOL rendering errors."""
    errors: list[str] = []
    problematic: list[str] = []
    for nid in ids:
        if " " in nid or "\t" in nid or "," in nid or ";" in nid or "|" in nid:
            problematic.append(nid)
    if problematic:
        sample = problematic[:10]
        errors.append(
            _get_error_message(
                ErrorCode.SPECIAL_CHARS_IN_ID,
                len(problematic),
                ", ".join(sample) + ("..." if len(problematic) > 10 else ""),
            )
        )
    return errors


# =============================================================================
# Adversarial Input Protection
# =============================================================================

# Control characters (C0 range except common whitespace, DEL, C1 range)
_CONTROL_CHAR_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]")

# Unicode bidirectional text override characters
_BIDI_CHARS = set("\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069")


def detect_malicious_node_names(names: list[str]) -> list[str]:
    """Detect node names containing malicious characters.

    Checks for:
    - Control characters (\x00-\x1f except tab/newline, \x7f-\x9f)
    - Unicode bidirectional text override (\u202e etc.)

    Args:
        names: List of node names to check

    Returns:
        List of names that contain malicious characters
    """
    malicious: list[str] = []
    for name in names:
        if not name:
            continue
        # Check control characters
        if _CONTROL_CHAR_RE.search(name):
            malicious.append(name)
            continue
        # Check bidi override characters
        if any(ch in _BIDI_CHARS for ch in name):
            malicious.append(name)
    return malicious


def validate_node_names(names: list[str]) -> list[str]:
    """Validate node names and return error messages for malicious ones.

    Args:
        names: List of node names

    Returns:
        List of error messages (empty if all clean)
    """
    errors: list[str] = []
    malicious = detect_malicious_node_names(names)
    if malicious:
        sample = malicious[:5]
        errors.append(
            _get_error_message(
                ErrorCode.MALICIOUS_NODE_NAME, f"{len(malicious)} names, e.g.: {', '.join(repr(n) for n in sample)}"
            )
        )
    return errors


def detect_taxonomy_circular_dependencies(taxonomy_path: str | Path, id_column: str = "id") -> list[str]:
    """Detect circular dependencies in taxonomy tables.

    Checks if any taxonomy value at one rank appears as a value at another rank
    in a way that creates a logical circular dependency.

    Example: Row1 has d__A;p__B and Row2 has d__B;p__A

    Args:
        taxonomy_path: Path to taxonomy CSV/TSV file
        id_column: Name of the ID column

    Returns:
        List of error messages describing circular dependencies
    """
    import pandas as pd

    errors: list[str] = []

    df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    first_col = df.columns[0]
    if id_column in df.columns and id_column != "id":
        df = df.rename(columns={id_column: "id"})
    elif first_col != "id" and first_col.lower() in ("id", "name", "tip", "leaf", "node"):
        df = df.rename(columns={first_col: "id"})

    # Get rank columns (non-id columns)
    rank_cols = [c for c in df.columns if c != "id"]
    if len(rank_cols) < 2:
        return errors

    # Build value pairs between adjacent ranks
    for i in range(len(rank_cols) - 1):
        rank_a = rank_cols[i]
        rank_b = rank_cols[i + 1]

        # Collect all (rank_a_value, rank_b_value) pairs
        pairs = set()
        for _, row in df.iterrows():
            va = str(row.get(rank_a, "")).strip()
            vb = str(row.get(rank_b, "")).strip()
            if va and vb and va != "nan" and vb != "nan":
                pairs.add((va, vb))

        # Check for circular: (A, B) and (B, A) both exist as rank_a->rank_b mappings
        seen: set[tuple[str, str]] = set()
        for va, vb in pairs:
            if (va, vb) in seen:
                continue
            # Check if (vb, va) also exists - meaning value at rank_a and rank_b are swapped
            if (vb, va) in pairs and va != vb:
                errors.append(
                    _get_error_message(
                        ErrorCode.CIRCULAR_DEPENDENCY, f"{rank_a}={va}<->{rank_b}={vb} (swapped in another row)"
                    )
                )
                seen.add((va, vb))
                seen.add((vb, va))

    return errors


def validate_file_not_empty(file_path: str | Path) -> list[str]:
    """Check that a file is not empty (CRITICAL if it is).

    Args:
        file_path: Path to check

    Returns:
        List of error messages (empty if file is non-empty)
    """
    path = Path(file_path)
    errors: list[str] = []
    if path.exists() and path.stat().st_size == 0:
        errors.append(_get_error_message(ErrorCode.FILE_EMPTY_CRITICAL, str(file_path)))
    return errors


def detect_file_type(file_path: str | Path) -> dict:
    """Detect file type and format with detailed information.

    Supports tree files, sequence files, and table files.

    Args:
        file_path: Path to the file

    Returns:
        Dict with keys:
            - exists: bool
            - category: 'tree', 'sequence', 'table', 'template', 'unknown'
            - format: detected format name (e.g., 'newick', 'nexus', 'fasta', 'fastq')
            - extension: file extension
            - size: file size in bytes
            - errors: list of error messages
            - warnings: list of warning messages
    """
    path = Path(file_path)
    result: dict[str, Any] = {
        "exists": False,
        "category": "unknown",
        "format": "unknown",
        "extension": path.suffix.lower(),
        "size": 0,
        "errors": [],
        "warnings": [],
    }

    if not path.exists():
        result["errors"].append(_get_error_message(ErrorCode.FILE_NOT_FOUND, str(file_path)))
        return result

    result["exists"] = True
    result["size"] = path.stat().st_size

    if result["size"] == 0:
        result["errors"].append(_get_error_message(ErrorCode.FILE_EMPTY, str(file_path)))
        return result

    ext = result["extension"]

    # Detect tree files
    if ext in TREE_EXTENSIONS:
        result["category"] = "tree"
        result["format"] = _detect_tree_format(path, ext)
        if result["format"] == "unknown":
            result["warnings"].append(_get_error_message(ErrorCode.UNSUPPORTED_TREE_FORMAT, str(file_path)))
    # Detect sequence files
    elif ext in SEQUENCE_EXTENSIONS:
        result["category"] = "sequence"
        result["format"] = _detect_sequence_format(path, ext)
        if result["format"] == "unknown":
            result["warnings"].append(_get_error_message(ErrorCode.UNSUPPORTED_SEQ_FORMAT, str(file_path)))
    # Detect table files
    elif ext in TABLE_EXTENSIONS:
        # Ambiguous extensions such as .txt may actually hold tree/sequence
        # files; let content-based detection take precedence first.
        content_type = _detect_by_content(path)
        if content_type:
            result["category"] = content_type["category"]
            result["format"] = content_type["format"]
        else:
            result["category"] = "table"
            result["format"] = _detect_table_format(path, ext)
    else:
        # Try to detect by content
        content_type = _detect_by_content(path)
        if content_type:
            result["category"] = content_type["category"]
            result["format"] = content_type["format"]
        else:
            result["warnings"].append(f"Unknown file type: {ext}")

    return result


def _detect_tree_format(path: Path, ext: str) -> str:
    """Detect tree file format from extension and content."""
    # Extension-based detection
    if ext in {".nexus", ".nex", ".treex"}:
        return "nexus"
    if ext in {".phyloxml", ".xml"}:
        return "phyloxml"
    # NHX (.nhx/.nhy) are Newick-with-comments; treat as newick to stay
    # consistent with parser.detect_tree_schema (which returns 'newick' for them).
    if ext in {".nhx", ".nhy"}:
        return "newick"

    # Content-based detection for ambiguous extensions
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")[:500].strip()
        upper = content.upper()

        if upper.startswith("#NEXUS") or "#NEXUS" in upper[:100]:
            return "nexus"
        if content.startswith("(") or content.startswith("["):
            return "newick"
        if "<phyloxml" in content.lower() or "<phylogeny" in content.lower():
            return "phyloxml"
    except Exception:  # noqa: S110
        pass

    # Default based on extension
    if ext in {".nwk", ".newick", ".tree", ".treefile", ".tre", ".rooted"}:
        return "newick"

    return "unknown"


def _detect_sequence_format(path: Path, ext: str) -> str:
    """Detect sequence file format from extension and content."""
    # Extension-based detection
    if ext in {".fa", ".fasta", ".fna", ".ffn", ".faa", ".frn"}:
        return "fasta"
    if ext in {".fq", ".fastq"}:
        return "fastq"
    if ext in {".gb", ".gbk", ".genbank"}:
        return "genbank"
    if ext in {".gff", ".gff3"}:
        return "gff"
    if ext == ".bed":
        return "bed"
    if ext in {".aln", ".clustal", ".msf"}:
        return "clustal"
    if ext in {".phy", ".phylip"}:
        return "phylip"

    # Content-based detection
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")[:500].strip()
        if content.startswith(">"):
            return "fasta"
        if content.startswith("@"):
            return "fastq"
        if content.startswith("LOCUS") or content.startswith("DEFINITION"):
            return "genbank"
        if content.startswith("##gff-version"):
            return "gff"
        if content.startswith("CLUSTAL"):
            return "clustal"
    except Exception:  # noqa: S110
        pass

    return "unknown"


def _detect_table_format(path: Path, ext: str) -> str:
    """Detect table file format."""
    if ext in {".xlsx", ".xls"}:
        return "excel"
    if ext == ".csv":
        return "csv"
    if ext == ".tsv":
        return "tsv"
    return "text"


def _detect_by_content(path: Path) -> dict | None:
    """Try to detect file type by reading content."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")[:500].strip()
        upper = content.upper()

        # Tree formats
        if upper.startswith("#NEXUS") or "#NEXUS" in upper[:100]:
            return {"category": "tree", "format": "nexus"}
        if content.startswith("("):
            return {"category": "tree", "format": "newick"}
        if "<phyloxml" in content.lower() or "<phylogeny" in content.lower():
            return {"category": "tree", "format": "phyloxml"}

        # Sequence formats
        if content.startswith(">"):
            return {"category": "sequence", "format": "fasta"}
        if content.startswith("@"):
            return {"category": "sequence", "format": "fastq"}
        if content.startswith("LOCUS") or content.startswith("DEFINITION"):
            return {"category": "sequence", "format": "genbank"}
    except Exception:  # noqa: S110
        pass

    return None


def validate_tree_file_format(tree_path: str | Path) -> dict:
    """Validate a tree file with comprehensive format checking.

    Returns:
        Dict with 'valid', 'format', 'errors', 'warnings', 'info' keys.
    """
    info = detect_file_type(tree_path)
    result: dict[str, Any] = {
        "valid": info["exists"] and not info["errors"],
        "format": info["format"],
        "errors": info["errors"],
        "warnings": info["warnings"],
        "info": {
            "size": info["size"],
            "category": info["category"],
        },
    }

    if not info["exists"] or info["errors"]:
        return result

    # Attempt to parse the tree
    try:
        from pyitol.core.parser import load_tree

        tree = load_tree(tree_path, multi_tree="first")
        if isinstance(tree, list):
            tree = tree[0]
        tip_count = len(tree.leaf_nodes())
        result["info"]["tip_count"] = tip_count
        result["info"]["has_branch_lengths"] = any(n.edge_length is not None for n in tree.postorder_node_iter())
    except Exception as e:
        result["errors"].append(_get_error_message(ErrorCode.PARSE_FAILED, str(e)))
        result["valid"] = False

    return result


def deep_validate_tree(tree_path: str | Path) -> dict:
    """Deep validation of tree files with detailed error location.

    Checks:
    - Bracket balancing (parentheses)
    - Quote escaping
    - Non-negative branch lengths (CRITICAL if negative)
    - Empty node names
    - Duplicate node names (WARNING)
    - Multi-root nodes
    - Self-loop edges
    - Multi-tree detection

    Returns:
        Dict with keys: valid, format, errors, warnings, info, trees
    """
    path = Path(tree_path)
    result: dict[str, Any] = {
        "valid": True,
        "format": "unknown",
        "errors": [],
        "warnings": [],
        "info": {},
        "trees": [],
    }

    if not path.exists():
        result["errors"].append(_get_error_message(ErrorCode.FILE_NOT_FOUND, str(tree_path)))
        result["valid"] = False
        return result

    if path.stat().st_size == 0:
        result["errors"].append(_get_error_message(ErrorCode.FILE_EMPTY, str(tree_path)))
        result["valid"] = False
        return result

    from pyitol.core.parser import count_trees_in_file, detect_tree_schema

    schema = detect_tree_schema(path)
    result["format"] = schema

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        result["errors"].append(f"File read error: {e}")
        result["valid"] = False
        return result

    if schema == "newick":
        _check_bracket_balance(raw, result)
        _check_raw_newick_duplicates(raw, result)

    tree_count = count_trees_in_file(path)
    result["info"]["tree_count"] = tree_count
    if tree_count > 1:
        result["warnings"].append(
            f"Tree file contains {tree_count} trees. Use --multi-tree-mode to specify strategy (first/last/split)."
        )

    try:
        from pyitol.core.parser import load_tree

        loaded = load_tree(path, multi_tree="all")
        if not isinstance(loaded, list):
            loaded = [loaded]
        for i, tree in enumerate(loaded):
            tree_info = _validate_single_tree(tree, result, tree_index=i if len(loaded) > 1 else -1)
            result["trees"].append(tree_info)

        if result["trees"]:
            result["info"].update(result["trees"][0])
            if len(result["trees"]) > 1:
                result["info"]["tip_count"] = sum(t.get("tip_count", 0) for t in result["trees"])
                result["info"]["total_nodes"] = sum(t.get("node_count", 0) for t in result["trees"])

    except Exception as e:
        result["errors"].append(_get_error_message(ErrorCode.PARSE_FAILED, str(e)))
        result["valid"] = False

    if result["errors"]:
        result["valid"] = False

    return result


def _check_bracket_balance(raw: str, result: dict[str, Any]) -> None:
    """Check parentheses balance in Newick string."""
    depth = 0
    in_quote = False
    quote_char = None

    for i, ch in enumerate(raw):
        if in_quote:
            if ch == quote_char:
                in_quote = False
            continue

        if ch in ("'", '"'):
            in_quote = True
            quote_char = ch
            continue

        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                line_num = raw[:i].count("\n") + 1
                result["errors"].append(f'Bracket mismatch: extra ")" at line {line_num}, char {i}')
                break
        elif ch == ";" and depth != 0:
            line_num = raw[:i].count("\n") + 1
            result["warnings"].append(f"Semicolon at line {line_num} while bracket depth is {depth}")

    if depth > 0:
        result["errors"].append(f'Bracket mismatch: {depth} unclosed "(" (missing closing parenthesis)')


def _check_raw_newick_duplicates(raw: str, result: dict[str, Any]) -> None:
    """Check for duplicate tip names in raw Newick string before parsing.

    Extracts leaf labels by finding tokens after ')' or ',' that are followed
    by ':' or ',' or ')' or ';'. This catches duplicates even if dendropy
    would merge them.
    """
    import re as _re

    # Match leaf labels: sequences of non-special chars after ) or , that precede : or , or ) or ;
    # Exclude things that look like numbers (internal node labels)
    labels = _re.findall(r"[,(]\s*([A-Za-z_][A-Za-z0-9_.\-|/]*)\s*[:),;]", raw)

    seen: dict[str, int] = {}
    duplicates: dict[str, int] = {}
    for label in labels:
        if label in seen:
            if label not in duplicates:
                duplicates[label] = seen[label]  # store first occurrence line
        else:
            # Estimate line number (rough)
            pos = raw.find(label)
            line_num = raw[:pos].count("\n") + 1 if pos >= 0 else 0
            seen[label] = line_num

    if duplicates:
        dup_sample = list(duplicates.keys())[:5]
        result["warnings"].append(
            f"Duplicate tip names in Newick: {len(duplicates)} duplicates, e.g.: {', '.join(dup_sample)}"
        )


def _validate_single_tree(tree: dendropy.Tree, result: dict[str, Any], tree_index: int = -1) -> dict:
    """Validate a single parsed tree object."""
    prefix = f"Tree #{tree_index + 1}: " if tree_index >= 0 else ""
    info = {}

    tips = [n for n in tree.leaf_nodes() if n.taxon]
    internal = list(tree.internal_nodes())

    info["tip_count"] = len(tips)
    info["node_count"] = len(tips) + len(internal)

    # Check empty node names
    empty_tips = [n for n in tips if not n.taxon.label or n.taxon.label.strip() == ""]
    if empty_tips:
        result["errors"].append(f"{prefix}{len(empty_tips)} tip(s) have empty names")

    # Check duplicate node names
    tip_labels = [n.taxon.label for n in tips if n.taxon and n.taxon.label]
    seen: set[str] = set()
    duplicates: set[str] = set()
    for label in tip_labels:
        if label in seen:
            duplicates.add(label)
        seen.add(label)
    if duplicates:
        dup_sample = list(duplicates)[:5]
        result["warnings"].append(
            f"{prefix}Duplicate tip names: {len(duplicates)} duplicates, e.g.: {', '.join(dup_sample)}"
        )

    # Check branch lengths
    has_negative = False
    has_branch_lengths = False
    negative_nodes = []
    for node in tree.postorder_node_iter():
        if node.edge_length is not None:
            has_branch_lengths = True
            if node.edge_length < 0:
                has_negative = True
                label = node.taxon.label if node.taxon else f"internal_{node.level()}"
                negative_nodes.append((label, node.edge_length))

    info["has_branch_lengths"] = has_branch_lengths
    if has_negative:
        sample = negative_nodes[:3]
        sample_str = ", ".join(f"{n}={v}" for n, v in sample)
        result["errors"].append(
            f"{prefix}CRITICAL: Negative branch lengths detected ({len(negative_nodes)} nodes): {sample_str}"
        )

    # Check for multi-root (forest)
    roots = [n for n in tree.preorder_node_iter() if n.parent_node is None]
    if len(roots) > 1:
        result["errors"].append(f"{prefix}Multiple root nodes detected ({len(roots)} roots)")
    info["root_count"] = len(roots)

    # Check self-loops
    for node in tree.preorder_node_iter():
        if node.parent_node and node.parent_node is node:
            result["errors"].append(
                f"{prefix}Self-loop detected at node {node.taxon.label if node.taxon else 'internal'}"
            )

    return info


# Alphabet character sets
_DNA_CHARS = set("ACGTacgtNnRrYySsWwKkMmBbDdHhVv-")
_RNA_CHARS = set("ACGUacguNnRrYySsWwKkMmBbDdHhVv-")
_PROTEIN_CHARS = set("ACDEFGHIKLMNPQRSTVWYacdefghiklmnpqrstvwyBbXxZz*-")


def _classify_alphabet(sequences: list[str]) -> str:
    """Classify the alphabet of a list of sequences."""
    all_chars: set[str] = set()
    for seq in sequences:
        all_chars.update(seq)

    if all_chars <= _DNA_CHARS:
        return "DNA"
    elif all_chars <= _RNA_CHARS:
        return "RNA"
    elif all_chars <= _PROTEIN_CHARS:
        return "protein"
    else:
        return "unknown"


def deep_validate_sequence(seq_path: str | Path, expected_alphabet: str = "auto") -> dict:
    """Deep validation of sequence files with detailed error location.

    Checks:
    - Auto-detect FASTA/FASTQ
    - Sequence alphabet (DNA/RNA/protein) with invalid character line numbers
    - Sequence ID uniqueness (ERROR on duplicates)
    - Sequence length consistency (WARNING if inconsistent)

    Args:
        seq_path: Path to the sequence file
        expected_alphabet: 'auto', 'DNA', 'RNA', 'protein', or 'any'

    Returns:
        Dict with keys: valid, format, alphabet, errors, warnings, info
    """
    path = Path(seq_path)
    result: dict[str, Any] = {
        "valid": True,
        "format": "unknown",
        "alphabet": "unknown",
        "errors": [],
        "warnings": [],
        "info": {},
    }

    if not path.exists():
        result["errors"].append(_get_error_message(ErrorCode.FILE_NOT_FOUND, str(seq_path)))
        result["valid"] = False
        return result

    if path.stat().st_size == 0:
        result["errors"].append(_get_error_message(ErrorCode.FILE_EMPTY, str(seq_path)))
        result["valid"] = False
        return result

    info = detect_file_type(seq_path)
    result["format"] = info["format"]
    result["info"]["size"] = info["size"]

    if info["format"] == "fasta":
        _deep_validate_fasta(path, result, expected_alphabet)
    elif info["format"] == "fastq":
        _deep_validate_fastq(path, result, expected_alphabet)
    else:
        result["warnings"].append(f"Deep validation not supported for format: {info['format']}")

    if result["errors"]:
        result["valid"] = False

    return result


def _deep_validate_fasta(path: Path, result: dict[str, Any], expected_alphabet: str) -> None:
    """Deep validate FASTA file."""
    sequences: dict[str, tuple[str, int]] = {}
    current_id: str | None = None
    current_seq: list[str] = []
    line_num = 0
    id_line_map: dict[str, int] = {}  # Track line numbers for duplicate detection
    duplicate_ids: list[tuple[str, int, int]] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_num += 1
            line = line.strip()
            if not line:
                continue

            if line.startswith(">"):
                if current_id is not None:
                    seq = "".join(current_seq)
                    sequences[current_id] = (seq, id_line_map.get(current_id, line_num))

                header = line[1:].strip()
                if not header:
                    result["errors"].append(f'Line {line_num}: Empty FASTA header (">" with no ID)')
                    continue
                current_id = header.split()[0]
                current_seq = []

                # Check duplicate IDs
                if current_id in id_line_map:
                    duplicate_ids.append((current_id, line_num, id_line_map[current_id]))
                else:
                    id_line_map[current_id] = line_num
            else:
                current_seq.append(line)

    if current_id is not None:
        seq = "".join(current_seq)
        sequences[current_id] = (seq, id_line_map.get(current_id, line_num))

    result["info"]["sequence_count"] = len(sequences)
    if not sequences:
        result["errors"].append("No sequences found in FASTA file")
        return

    # Report duplicate IDs
    if duplicate_ids:
        for dup_id, new_line, old_line in duplicate_ids[:5]:
            result["errors"].append(
                f'Duplicate sequence ID "{dup_id}": first at line {old_line}, again at line {new_line}'
            )
        if len(duplicate_ids) > 5:
            result["errors"].append(f"... and {len(duplicate_ids) - 5} more duplicates")

    # Detect and validate alphabet
    seq_values = [v[0] for v in sequences.values()]
    detected_alphabet = _classify_alphabet(seq_values)

    if expected_alphabet == "auto":
        result["alphabet"] = detected_alphabet
    else:
        result["alphabet"] = detected_alphabet
        if detected_alphabet != expected_alphabet and expected_alphabet != "any":
            result["warnings"].append(f"Expected {expected_alphabet} alphabet but detected {detected_alphabet}")

    # Check invalid characters
    valid_chars = (
        _DNA_CHARS if result["alphabet"] == "DNA" else (_RNA_CHARS if result["alphabet"] == "RNA" else _PROTEIN_CHARS)
    )
    for seq_id, (seq, _end_line) in sequences.items():
        invalid = [ch for ch in set(seq) if ch not in valid_chars]
        if invalid:
            result["warnings"].append(
                f'Sequence "{seq_id}": invalid characters for {result["alphabet"]}: '
                f"{', '.join(repr(c) for c in invalid)}"
            )

    # Check length consistency
    lengths = [len(v[0]) for v in sequences.values()]
    if lengths:
        min_len = min(lengths)
        max_len = max(lengths)
        result["info"]["min_length"] = min_len
        result["info"]["max_length"] = max_len
        result["info"]["mean_length"] = sum(lengths) / len(lengths)

        if min_len != max_len:
            result["warnings"].append(
                f"Sequence lengths vary: min={min_len}, max={max_len}. "
                f"Alignment may be required before tree construction."
            )


def _deep_validate_fastq(path: Path, result: dict[str, Any], expected_alphabet: str) -> None:
    """Deep validate FASTQ file."""
    sequences: dict[str, tuple[str, int]] = {}
    line_num = 0
    block_lines: list[str] = []

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line_num += 1
            block_lines.append(line.strip())

            if len(block_lines) == 4:
                header, seq, plus, qual = block_lines

                if not header.startswith("@"):
                    result["errors"].append(
                        f'Line {line_num - 3}: Expected "@" at start of FASTQ header, got: {header[:30]}'
                    )

                seq_id = header[1:].split()[0]

                if seq_id in sequences:
                    result["errors"].append(f'Line {line_num - 3}: Duplicate sequence ID "{seq_id}"')
                sequences[seq_id] = (seq, line_num - 3)

                if not plus.startswith("+"):
                    result["warnings"].append(f'Line {line_num - 1}: Expected "+" separator, got: {plus[:20]}')

                if len(seq) != len(qual):
                    result["warnings"].append(
                        f"Line {line_num - 3}: Quality length ({len(qual)}) does not match sequence length ({len(seq)})"
                    )

                block_lines = []

    result["info"]["sequence_count"] = len(sequences)

    if not sequences:
        result["errors"].append("No sequences found in FASTQ file")
        return

    seq_values = [v[0] for v in sequences.values()]
    detected_alphabet = _classify_alphabet(seq_values)
    result["alphabet"] = detected_alphabet

    valid_chars = (
        _DNA_CHARS if detected_alphabet == "DNA" else (_RNA_CHARS if detected_alphabet == "RNA" else _PROTEIN_CHARS)
    )
    for seq_id, (seq, start_line) in sequences.items():
        invalid = [ch for ch in set(seq) if ch not in valid_chars]
        if invalid:
            result["warnings"].append(
                f'Sequence "{seq_id}" (line {start_line}): invalid characters: {", ".join(repr(c) for c in invalid)}'
            )

    lengths = [len(v[0]) for v in sequences.values()]
    if lengths:
        min_len = min(lengths)
        max_len = max(lengths)
        result["info"]["min_length"] = min_len
        result["info"]["max_length"] = max_len
        if min_len != max_len:
            result["warnings"].append(f"Sequence lengths vary: min={min_len}, max={max_len}")


def validate_sequence_file_format(seq_path: str | Path) -> dict:
    """Validate a sequence file with comprehensive format checking.

    Returns:
        Dict with 'valid', 'format', 'errors', 'warnings', 'info' keys.
    """
    info = detect_file_type(seq_path)
    result: dict[str, Any] = {
        "valid": info["exists"] and not info["errors"],
        "format": info["format"],
        "errors": info["errors"],
        "warnings": info["warnings"],
        "info": {
            "size": info["size"],
            "category": info["category"],
        },
    }

    if not info["exists"] or info["errors"]:
        return result

    # Validate content based on format
    path = Path(seq_path)
    try:
        if info["format"] == "fasta":
            _validate_fasta_content(path, result)
        elif info["format"] == "fastq":
            _validate_fastq_content(path, result)
        elif info["format"] == "genbank":
            _validate_genbank_content(path, result)
    except Exception as e:
        result["warnings"].append(f"Content validation skipped: {e}")

    return result


def _validate_fasta_content(path: Path, result: dict[str, Any]) -> None:
    """Validate FASTA file content."""
    seq_count = 0
    has_sequences = False
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if line.startswith(">"):
                    seq_count += 1
                else:
                    has_sequences = True
    except Exception as e:
        result["warnings"].append(f"FASTA read error: {e}")
        return

    result["info"]["sequence_count"] = seq_count
    if seq_count == 0:
        result["errors"].append(_get_error_message(ErrorCode.INVALID_SEQ_CONTENT, "No FASTA headers found"))
        result["valid"] = False
    elif not has_sequences:
        result["warnings"].append("FASTA headers found but no sequences")


def _validate_fastq_content(path: Path, result: dict[str, Any]) -> None:
    """Validate FASTQ file content."""
    seq_count = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                if line_num % 4 == 1:  # Header line
                    if not line.startswith("@"):
                        result["warnings"].append(f"Line {line_num}: Expected @ header, got: {line[:20]}")
                    seq_count += 1
    except Exception as e:
        result["warnings"].append(f"FASTQ read error: {e}")
        return

    result["info"]["sequence_count"] = seq_count
    if seq_count == 0:
        result["errors"].append(_get_error_message(ErrorCode.INVALID_SEQ_CONTENT, "No FASTQ reads found"))
        result["valid"] = False


def _validate_genbank_content(path: Path, result: dict[str, Any]) -> None:
    """Validate GenBank file content."""
    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if "LOCUS" not in content:
            result["warnings"].append("GenBank file missing LOCUS line")
        if "FEATURES" not in content:
            result["warnings"].append("GenBank file missing FEATURES section")
    except Exception as e:
        result["warnings"].append(f"GenBank read error: {e}")


class TemplateValidator:
    """Validate iTOL template inputs before generation."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def validate_tree_file(self, tree_path: str | Path) -> bool:
        """Validate tree file exists and is parseable."""
        path = Path(tree_path)
        if not path.exists():
            self.errors.append(_get_error_message(ErrorCode.FILE_NOT_FOUND, tree_path))
            return False
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            self.errors.append(_get_error_message(ErrorCode.FILE_EMPTY, tree_path))
            return False
        upper = content[:200].upper()
        if not (upper.startswith("#NEXUS") or upper.startswith("(") or content.startswith("[")):
            self.warnings.append(_get_error_message(ErrorCode.INVALID_FORMAT, tree_path))
        # Attempt lightweight dendropy parse for Newick files
        if upper.startswith("("):
            try:
                import dendropy

                from pyitol.core.parser import detect_tree_schema

                schema = detect_tree_schema(path)
                dendropy.Tree.get(path=str(path), schema=schema, preserve_underscores=True)
            except Exception as e:
                self.errors.append(_get_error_message(ErrorCode.PARSE_FAILED, e))
                return False
        return True

    def validate_metadata_file(self, metadata_path: str | Path) -> bool:
        """Validate metadata/taxonomy file."""
        path = Path(metadata_path)
        if not path.exists():
            self.errors.append(_get_error_message(ErrorCode.FILE_NOT_FOUND, metadata_path))
            return False
        suffix = path.suffix.lower()
        if suffix not in {".csv", ".tsv", ".txt", ".xlsx", ".xls"}:
            self.warnings.append(f"Unsupported metadata file format: {suffix}")
        return True

    def validate_template_file(self, template_path: str | Path) -> bool:
        """Validate an existing iTOL template file."""
        path = Path(template_path)
        if not path.exists():
            self.errors.append(_get_error_message(ErrorCode.FILE_NOT_FOUND, template_path))
            return False
        content = path.read_text(encoding="utf-8")
        has_header = any(
            marker in content
            for marker in [
                "DATASET_",
                "TREE_COLORS",
                "COLLAPSE",
                "PRUNE",
                "SPACING",
                "LABELS",
                "POPUP_INFO",
            ]
        )
        if not has_header:
            self.errors.append(_get_error_message(ErrorCode.MISSING_HEADER, template_path))
            return False
        if "SEPARATOR" not in content:
            self.warnings.append(_get_error_message(ErrorCode.MISSING_SEPARATOR, template_path))
        return True

    def validate_color_values(self, colors: list[str]) -> bool:
        """Validate color codes."""
        errs = validate_color_codes(colors)
        self.errors.extend(errs)
        return len(errs) == 0

    def validate_dataframe(
        self,
        df: pd.DataFrame,
        separator: str = "TAB",
        categorical_columns: list[str] | None = None,
        numeric_columns: list[str] | None = None,
    ) -> bool:
        """Validate a DataFrame for iTOL template generation."""
        # Check delimiter conflicts
        delim_errs = check_delimiter_conflict(df, separator)
        self.errors.extend(delim_errs)

        # Check categorical cardinality
        if categorical_columns:
            for col in categorical_columns:
                warns = check_categorical_cardinality(df, col)
                self.warnings.extend(warns)

        # Check numeric ranges
        if numeric_columns:
            for col in numeric_columns:
                warns = check_numeric_range(df, col)
                self.warnings.extend(warns)

        return len(self.errors) == 0

    def get_summary(self) -> dict:
        """Get validation summary."""
        return {
            "valid": len(self.errors) == 0,
            "errors": self.errors,
            "warnings": self.warnings,
        }

    def raise_if_errors(self) -> None:
        """Raise ValidationError if there are errors."""
        if self.errors:
            raise ValidationError("\n".join(self.errors))


def validate_inputs(
    tree_path: str | Path | None = None,
    metadata_path: str | Path | None = None,
    template_paths: list[str | Path] | None = None,
    colors: list[str] | None = None,
) -> dict:
    """Convenience function to validate all inputs.

    Returns a summary dict with 'valid', 'errors', and 'warnings' keys.
    """
    validator = TemplateValidator()

    if tree_path:
        validator.validate_tree_file(tree_path)

    if metadata_path:
        validator.validate_metadata_file(metadata_path)

    if template_paths:
        for tp in template_paths:
            validator.validate_template_file(tp)

    if colors:
        validator.validate_color_values(colors)

    return validator.get_summary()
