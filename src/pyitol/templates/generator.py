"""Template generator engine - writes iTOL-compatible template files."""

from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable

from pyitol.exceptions import (
    InvalidColumnError,
    MetadataParseError,
    TaxaNotFoundError,
    TemplateError,
    TreeParseError,
)
from pyitol.templates.schemas.base import (
    SEPARATOR_MAP,
    TemplateSchema,
    create_schema,
)
from pyitol.utils.color_tools import _assign_colors, assign_colors_to_categories
from pyitol.utils.constants import (
    DEFAULT_BORDER_COLOR,
    DEFAULT_CONNECTION_COLOR,
    DEFAULT_HEATMAP_GRADIENT,
    DEFAULT_MISSING_COLOR,
    DEFAULT_PRIMARY_COLOR,
    DEFAULT_SEPARATOR,
)

logger = logging.getLogger(__name__)

# C3: Bounded LRU cache using OrderedDict for O(1) eviction.
_taxonomy_tree_cache: OrderedDict[str, tuple] = OrderedDict()
_CACHE_MAX_SIZE = 16


def _cache_key(taxonomy_path_str: str, tree_path_str: str, id_column: str) -> str:
    """Generate a cache key from file paths, modification times, and parameters."""
    import os

    parts = [taxonomy_path_str, tree_path_str, id_column]
    for p in (taxonomy_path_str, tree_path_str):
        try:
            mtime = os.path.getmtime(p)
            parts.append(str(mtime))
        except OSError:
            pass
    key_str = ":".join(parts)
    return hashlib.sha256(key_str.encode()).hexdigest()


def _cache_get(key: str) -> tuple | None:
    """Get a value from cache, updating access order (move to end)."""
    if key in _taxonomy_tree_cache:
        _taxonomy_tree_cache.move_to_end(key)
        return _taxonomy_tree_cache[key]
    return None


def _cache_put(key: str, value: tuple) -> None:
    """Put a value into cache with LRU eviction."""
    if key in _taxonomy_tree_cache:
        _taxonomy_tree_cache.move_to_end(key)
    _taxonomy_tree_cache[key] = value
    while len(_taxonomy_tree_cache) > _CACHE_MAX_SIZE:
        _taxonomy_tree_cache.popitem(last=False)


def clear_taxonomy_tree_cache() -> None:
    """Clear the taxonomy/tree cache. Useful for testing or memory management."""
    _taxonomy_tree_cache.clear()


# iTOL DATASET_EXTERNALSHAPE `type` numeric codes (1=square, 2=circle, 3=star,
# 4=right triangle, 5=left triangle, 6=checkmark).  A single shared mapping is
# used so that generate_external_shape_template and
# generate_external_shape_bubble_template can never diverge (L10).
EXTERNAL_SHAPE_MAP: dict[str, str] = {
    "circle": "2",
    "square": "1",
    "star": "3",
    "triangle_right": "4",
    "triangle_left": "5",
    "checkmark": "6",
}

# iTOL DATASET_SYMBOL `type` numeric codes (1=square, 2=circle, 3=triangle,
# 4=star, 5=left-triangle, 6=right-triangle).  Note: this encoding differs
# from EXTERNAL_SHAPE_MAP and the two must not be mixed (H3).  iTOL has no
# 'diamond'; it falls back to square (1) with a warning.
SYMBOL_SHAPE_MAP: dict[str, str] = {
    "square": "1",
    "circle": "2",
    "triangle": "3",
    "star": "4",
    "left-triangle": "5",
    "right-triangle": "6",
    "diamond": "1",  # no diamond in iTOL; falls back to square (1)
}

# iTOL DATASET_CONNECTION 5th-column `type` numeric codes:
#   0=normal curve, 1=straight line.
CONNECTION_LINE_TYPE_MAP: dict[str, str] = {
    "solid": "0",
    "straight": "1",
}


def _write_schema_file(output_path: str | Path, schema: TemplateSchema) -> Path:
    """统一收尾逻辑：将单个 schema 写出为模板文件（减少各 generate_* 的重复样板，L9）。"""
    gen = TemplateGenerator()
    gen.add_schema(schema)
    return gen.write(output_path)


class TemplateGenerator:
    """Generate iTOL template files from schema definitions."""

    def __init__(self) -> None:
        self.schemas: list[TemplateSchema] = []
        self.style_params: dict = {}
        self.template_name: str = ""

    def add_schema(self, schema: TemplateSchema) -> None:
        """Add a dataset schema to the template."""
        self.schemas.append(schema)

    def add_schema_from_data(
        self,
        type_name: str,
        label: str,
        data: list[dict],
        parameters: dict | None = None,
        separator: str = DEFAULT_SEPARATOR,
        color: str = DEFAULT_PRIMARY_COLOR,
    ) -> None:
        """Create and add a schema from raw data."""
        schema = create_schema(type_name, label=label, color=color, separator=separator)
        if data:
            schema.columns = list(data[0].keys())
        schema.data_rows = data
        if parameters:
            schema.parameters.update(parameters)
        self.schemas.append(schema)

    def set_style(self, params: dict) -> None:
        """Set tree style parameters."""
        self.style_params.update(params)

    def set_name(self, name: str) -> None:
        """Set the template display name."""
        self.template_name = name

    def _write_schema(self, schema: TemplateSchema) -> str:
        """Write a single schema to iTOL v7 format string."""
        # P1-7: Validate schema before writing; log warnings but don't block
        errors = schema.validate()
        if errors:
            for err in errors:
                logger.warning(f"Schema validation [{schema.dataset_type}]: {err}")

        sep = schema.get_separator_char()
        lines = []

        # Header line
        lines.append(schema.get_header_line())
        lines.append("")

        # Separator line (always written with space between key and value)
        lines.append(f"SEPARATOR {schema.separator}")
        lines.append("")

        # Parameters
        for pline in schema.get_parameter_lines():
            lines.append(pline)

        # Legend
        if not schema.legend.is_empty():
            lines.append("")
            for lline in schema.legend.get_lines(sep):
                lines.append(lline)

        # DATA marker
        lines.append("")
        lines.append("DATA")

        # Data rows (no column headers in iTOL v7)
        for row in schema.data_rows:
            values = [str(row.get(col, "")) for col in schema.columns]
            lines.append(sep.join(values))

        return "\n".join(lines)

    def write(self, output_path: str | Path, mode: str = "write") -> Path:
        """Write the complete template file in iTOL v7 format."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        sections: list[str] = []

        if self.template_name:
            sections.insert(0, f"TEMPLATE_NAME\t{self.template_name}")

        for schema in self.schemas:
            sections.append(self._write_schema(schema))

        # Tree style section
        if self.style_params:
            style_lines = [
                "DATASET_TREESTYLE",
                "",
                "SEPARATOR TAB",
            ]
            for key, value in self.style_params.items():
                style_lines.append(f"{key}\t{value}")
            sections.append("\n".join(style_lines))

        content = "\n\n".join(sections) + "\n"

        if mode == "write":
            path.write_text(content, encoding="utf-8")
        elif mode == "append":
            if path.exists():
                with open(path, "a", encoding="utf-8") as f:
                    f.write(content)
            else:
                path.write_text(content, encoding="utf-8")
        else:
            raise TemplateError(f"Invalid write mode: '{mode}'. Use 'write' or 'append'.")

        return path

    def write_multiple(
        self,
        output_dir: str | Path,
        prefix: str = "",
    ) -> list[Path]:
        """Write each schema as a separate template file and return paths."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i, schema in enumerate(self.schemas):
            safe_label = "".join(c if c.isalnum() or c in "_-." else "_" for c in schema.label)
            fname = f"{prefix}{safe_label}_{i + 1}.txt" if prefix else f"{safe_label}_{i + 1}.txt"
            path = output_dir / fname
            single_gen = TemplateGenerator()
            single_gen.add_schema(schema)
            if self.style_params:
                single_gen.set_style(self.style_params)
            single_gen.write(path)
            paths.append(path)
        return paths


def generate_template(
    output_path: str | Path,
    schemas: list[TemplateSchema],
    style_params: dict | None = None,
    template_name: str | None = None,
) -> Path:
    """Convenience function to generate a template file."""
    gen = TemplateGenerator()
    for schema in schemas:
        gen.add_schema(schema)
    if style_params:
        gen.set_style(style_params)
    if template_name:
        gen.set_name(template_name)
    return gen.write(output_path)


def _read_taxonomy_and_tree(taxonomy_path: str | Path, tree_path: str | Path, id_column: str = "id") -> tuple:
    """Read taxonomy table and tree, filter taxonomy to tree tips.

    Uses a bounded LRU internal cache keyed by file path hash to avoid repeated
    parsing when generating multiple templates from the same inputs.
    C3: Uses bounded LRU cache with SHA-256 key instead of unbounded dict to prevent memory leaks.
    """
    key = _cache_key(str(taxonomy_path), str(tree_path), id_column)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    result = _read_taxonomy_and_tree_impl(str(taxonomy_path), str(tree_path), id_column)
    _cache_put(key, result)
    return result


def _read_taxonomy_and_tree_impl(taxonomy_path_str: str, tree_path_str: str, id_column: str = "id") -> tuple:
    """Implementation of taxonomy and tree reading (not cached)."""
    import dendropy
    import pandas as pd

    from pyitol.core.parser import detect_tree_schema

    # Explicitly translate raw dendropy/pandas exceptions into domain exceptions.
    try:
        tree_schema = detect_tree_schema(tree_path_str)
        tree = dendropy.Tree.get_from_path(tree_path_str, schema=tree_schema, preserve_underscores=True)
    except Exception as exc:  # this try block only wraps tree parsing; any error is a parse error
        raise TreeParseError(f"无法解析树文件 {tree_path_str}: {exc}") from exc
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}

    try:
        df = pd.read_csv(taxonomy_path_str, sep=None, engine="python", dtype=str)
    except Exception as exc:  # 该 try 块仅包含分类学文件读取
        raise MetadataParseError(f"无法解析分类学文件 {taxonomy_path_str}: {exc}") from exc
    if id_column in df.columns:
        df = df.rename(columns={id_column: "id"})
    elif "id" not in df.columns:
        raise InvalidColumnError(
            f"ID column '{id_column}' not found in {taxonomy_path_str}. Available columns: {list(df.columns)}"
        )
    df = df[df["id"].isin(tip_set)]
    return tree, df, tip_set


def _generate_categorical_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    column: str,
    template_type: str,
    schema_columns: list[str],
    row_builder: Callable[[Any, Any], dict[str, Any] | None],
    colors: dict | None = None,
    label: str = "dataset",
    id_column: str = "id",
    separator: str = DEFAULT_SEPARATOR,
    extra_params: dict | None = None,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generic helper for templates driven by a categorical taxonomy column.

    Args:
        row_builder: Callable(df_row, colors_dict) -> dict or None.
                   Receives a pandas Series (the row) and the colors mapping.
                   Should return a data-row dict, or None to skip.
        extra_params: Optional dict of additional schema parameters.
    """
    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    # When the categorical data is empty (no overlap between df and tree
    # tips), no longer silently emit an empty dataset — warn and raise a clear
    # TaxaNotFoundError instead.
    if df.empty:
        logger.warning(
            "分类数据为空：列 '%s' 与树 %s 的 tip 无交集，将生成空数据集",
            column,
            tree_path,
        )
        raise TaxaNotFoundError(
            f"分类数据为空：分类列 '{column}' 与树 {tree_path} 的 tip 没有交集，请检查 id 列或分类列取值是否正确。"
        )

    if column not in df.columns:
        raise InvalidColumnError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors_map = _assign_colors(df, column, colors)

    data = []
    for _, row in df.iterrows():
        built = row_builder(row, colors_map)
        if built is not None:
            data.append(built)

    schema = create_schema(template_type, label=label, separator=separator)
    schema.columns = schema_columns
    schema.data_rows = data
    if extra_params:
        for k, v in extra_params.items():
            schema.parameters[k] = v

    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    # Auto-position legend to avoid tree overlap
    from pyitol.templates.schemas.base import LegendConfig

    n_categories = len(colors_map) if colors_map else 1
    legend_x, legend_y = LegendConfig.auto_position(n_items=n_categories, position="bottom-right")
    schema.legend.title = label
    schema.legend.position_x = legend_x
    schema.legend.position_y = legend_y
    schema.legend.horizontal = "1"
    schema.legend.shapes = ["1"] * min(n_categories, 10)
    schema.legend.colors = list(colors_map.values())[:10] if colors_map else [DEFAULT_MISSING_COLOR]
    schema.legend.labels = list(colors_map.keys())[:10] if colors_map else [label]

    return _write_schema_file(output_path, schema)


def generate_color_strip_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    column: str,
    colors: dict | None = None,
    label: str = "color_strip",
    id_column: str = "id",
    strip_width: str = "50",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
    color_branches: str = "0",
    complete_border: str = "0",
    show_strip_labels: str = "0",
    strip_label_position: str = "0",
    strip_label_color: str = "#000000",
    strip_label_size: str = "10",
) -> Path:
    """Generate a color strip template from taxonomy data."""
    import pandas as pd

    def _row_builder(row: Any, colors_map: dict[str, str]) -> dict[str, Any] | None:
        val = row[column]
        if pd.isna(val):
            return None
        # iTOL DATASET_COLORSTRIP data rows are `ID <sep> COLOR <sep> LABEL`
        # (see official template tol_color_strip.txt).
        return {
            "id": row["id"],
            "color": colors_map.get(val, DEFAULT_MISSING_COLOR),
            "value": val,
        }

    extra_params = {
        "STRIP_WIDTH": strip_width,
        "COLOR_BRANCHES": color_branches,
        "COMPLETE_BORDER": complete_border,
        "SHOW_STRIP_LABELS": show_strip_labels,
        "STRIP_LABEL_POSITION": strip_label_position,
        "STRIP_LABEL_COLOR": strip_label_color,
        "STRIP_LABEL_SIZE": strip_label_size,
    }

    return _generate_categorical_template(
        output_path,
        taxonomy_path,
        tree_path,
        column,
        template_type="color_strip",
        schema_columns=["id", "color", "value"],
        row_builder=_row_builder,
        colors=colors,
        label=label,
        id_column=id_column,
        separator=separator,
        extra_params=extra_params,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )


def generate_manual_template(
    output_path: str | Path,
    data_rows: list[dict],
    custom_header: dict[str, str] | None = None,
    label: str = "manual",
    color: str = DEFAULT_PRIMARY_COLOR,
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a DATASET_MANUAL template for free-form annotations.

    Allows users to define custom data formats for special needs beyond
    standard iTOL dataset types.
    """
    schema = create_schema("manual", label=label, color=color, separator=separator)
    if data_rows:
        schema.columns = list(data_rows[0].keys())
    else:
        schema.columns = ["id"]
    schema.data_rows = data_rows
    if custom_header:
        for key, value in custom_header.items():
            schema.parameters[key] = value

    return _write_schema_file(output_path, schema)


def generate_simple_bar_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_column: str,
    label: str = "simple_bar",
    id_column: str = "id",
    bar_color: str = "#3c5484",
    bar_width: str = "50",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
    maximum_width: str | None = None,
    bar_shift: str = "0",
    bar_zero: str = "0",
    show_value: str = "0",
    show_labels: str = "1",
    label_position: str = "0",
    label_shift_x: str = "0",
    label_shift_y: str = "0",
    log_scale: str = "0",
) -> Path:
    """Generate a simple bar template from numeric data."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    if value_column not in df.columns:
        raise InvalidColumnError(f"Column '{value_column}' not found. Available: {list(df.columns)}")

    data = []
    for _, row in df.iterrows():
        val = row[value_column]
        if pd.isna(val):
            continue
        try:
            float(val)
        except ValueError:
            continue
        data.append({"id": row["id"], "bar_height": val})

    schema = create_schema("simple_bar", label=label, color=bar_color, separator=separator)
    schema.columns = ["id", "bar_height"]
    schema.data_rows = data
    schema.parameters["WIDTH"] = maximum_width if maximum_width is not None else bar_width
    schema.parameters["BAR_SHIFT"] = bar_shift
    schema.parameters["BAR_ZERO"] = bar_zero
    schema.parameters["SHOW_VALUE"] = show_value
    schema.parameters["SHOW_LABELS"] = show_labels
    schema.parameters["LABEL_POSITION"] = label_position
    schema.parameters["LABEL_SHIFT_X"] = label_shift_x
    schema.parameters["LABEL_SHIFT_Y"] = label_shift_y
    schema.parameters["LOG_SCALE"] = log_scale
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_branch_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    column: str,
    colors: dict | None = None,
    label: str = "branch",
    id_column: str = "id",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a branch coloring template."""
    import pandas as pd

    def _row_builder(row: Any, colors_map: dict[str, str]) -> dict[str, Any] | None:
        val = row[column]
        if pd.isna(val):
            return None
        return {"id": row["id"], "type": "clade", "color": colors_map.get(val, DEFAULT_MISSING_COLOR)}

    return _generate_categorical_template(
        output_path,
        taxonomy_path,
        tree_path,
        column,
        template_type="tree_colors",
        schema_columns=["id", "type", "color"],
        row_builder=_row_builder,
        colors=colors,
        label=label,
        id_column=id_column,
        separator=separator,
    )


def generate_symbols_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    column: str,
    symbol_type: str = "diamond",
    colors: dict | None = None,
    label: str = "symbols",
    id_column: str = "id",
    size: str = "30",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate a symbols template from categorical data."""
    import pandas as pd

    # iTOL DATASET_SYMBOL `type` is a numeric code (see SYMBOL_SHAPE_MAP):
    # 1=square, 2=circle, 3=triangle, 4=star, 5=left-triangle, 6=right-triangle.
    # 'diamond' does not exist in iTOL; kept for backward compatibility but
    # falls back to square(1) with a warning.
    if symbol_type not in SYMBOL_SHAPE_MAP:
        raise TemplateError(f"无效的符号类型: {symbol_type}。可选: {sorted(SYMBOL_SHAPE_MAP.keys())}")
    shape_code = SYMBOL_SHAPE_MAP[symbol_type]
    if symbol_type == "diamond":
        logger.warning("iTOL DATASET_SYMBOL 不支持 'diamond'，已回退到 square（类型编号 1）。")

    def _row_builder(row: Any, colors_map: dict[str, str]) -> dict[str, Any] | None:
        val = row[column]
        if pd.isna(val):
            return None
        return {
            "id": row["id"],
            "type": shape_code,
            "value": size,
            "color": colors_map.get(val, DEFAULT_MISSING_COLOR),
            "label": val,
        }

    return _generate_categorical_template(
        output_path,
        taxonomy_path,
        tree_path,
        column,
        template_type="symbols",
        schema_columns=["id", "type", "value", "color", "label"],
        row_builder=_row_builder,
        colors=colors,
        label=label,
        id_column=id_column,
        separator=separator,
        extra_params={"MAXIMUM_SIZE": size},
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )


def generate_heatmap_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_columns: list[str],
    color_gradient: list[str] | None = None,
    label: str = "heatmap",
    id_column: str = "id",
    column_labels: dict | None = None,
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
    field_tree: str | None = None,
    show_tree: str = "0",
    tree_height: str = "50",
    color_nan: str = "#FFFFFF",
    normalization: str = "0",
    display_values: str = "0",
    value_size: str = "10",
    value_color: str = "#000000",
    value_format: str = "0",
    value_position: str = "0",
) -> Path:
    """Generate a heatmap template from numeric data columns."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    for vc in value_columns:
        if vc not in df.columns:
            raise InvalidColumnError(f"Column '{vc}' not found. Available: {list(df.columns)}")

    if color_gradient is None:
        color_gradient = DEFAULT_HEATMAP_GRADIENT

    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for vc in value_columns:
            val = row[vc]
            row_data[vc] = "" if pd.isna(val) else val
        data.append(row_data)

    schema = create_schema("heatmap", label=label, separator=separator)
    schema.columns = ["id", *value_columns]
    schema.data_rows = data
    schema.parameters["COLOR_MIN"] = color_gradient[0]
    if len(color_gradient) > 2:
        schema.parameters["COLOR_MID"] = color_gradient[1]
        schema.parameters["COLOR_MAX"] = color_gradient[-1]
        schema.parameters["USE_MID_COLOR"] = "1"
    else:
        schema.parameters["COLOR_MAX"] = color_gradient[-1]
    schema.parameters["FIELD_LABELS"] = sep_of(separator).join(value_columns)
    if field_tree is not None:
        schema.parameters["FIELD_TREE"] = field_tree
    schema.parameters["SHOW_TREE"] = show_tree
    schema.parameters["TREE_HEIGHT"] = tree_height
    schema.parameters["COLOR_NAN"] = color_nan
    schema.parameters["NORMALIZATION"] = normalization
    schema.parameters["DISPLAY_VALUES"] = display_values
    schema.parameters["VALUE_SIZE"] = value_size
    schema.parameters["VALUE_COLOR"] = value_color
    schema.parameters["VALUE_FORMAT"] = value_format
    schema.parameters["VALUE_POSITION"] = value_position
    if column_labels:
        for col_name, display in column_labels.items():
            schema.parameters[f"COLUMN_LABEL:{col_name}"] = display
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def get_separator_char(sep_name: str) -> str:
    """Get the actual separator character from separator name (TAB, SPACE, COMMA)."""
    return SEPARATOR_MAP.get(sep_name, "\t")


# Keep backward-compatible alias
sep_of = get_separator_char


def _apply_common_visual_params(
    schema: TemplateSchema,
    separator: str,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> None:
    """Apply common visual parameters shared by many dataset types."""
    sep = get_separator_char(separator)
    schema.parameters["MARGIN"] = margin
    schema.parameters["HEIGHT_FACTOR"] = height_factor
    schema.parameters["SHOW_INTERNAL"] = show_internal
    schema.parameters["BORDER_WIDTH"] = border_width
    schema.parameters["BORDER_COLOR"] = border_color
    if dataset_scale is not None:
        schema.parameters["DATASET_SCALE"] = sep.join(str(s) for s in dataset_scale)


def generate_connection_template(
    output_path: str | Path,
    connections: list[tuple[str, str]],
    color: str = DEFAULT_CONNECTION_COLOR,
    line_width: str = "2",
    line_type: str = "solid",
    label: str = "connections",
    arrow_head_size: str = "1",
    separator: str = DEFAULT_SEPARATOR,
    curve_angle: str = "0",
    center_curves: str = "0",
    maximum_line_width: str = "10",
    draw_arrows: str = "0",
    loop_size: str = "10",
    connection_label_size: str = "10",
    connection_label_color: str = "#000000",
) -> Path:
    """Generate a connections template from node pairs."""
    # iTOL DATASET_CONNECTION 5th-column `type` is a numeric code:
    #   0=normal curve (solid), 1=straight line.
    line_type_code = CONNECTION_LINE_TYPE_MAP.get(line_type, "0")
    if line_type not in CONNECTION_LINE_TYPE_MAP:
        logger.warning(
            "未知的连接线类型 '%s'，已按曲线(solid, 类型 0)处理。可选: %s",
            line_type,
            sorted(CONNECTION_LINE_TYPE_MAP.keys()),
        )

    data = []
    for pair in connections:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            data.append(
                {
                    "id1": pair[0],
                    "id2": pair[1],
                    "color": color,
                    "width": line_width,
                    "type": line_type_code,
                }
            )

    schema = create_schema("connection", label=label, separator=separator)
    schema.columns = ["id1", "id2", "color", "width", "type"]
    schema.data_rows = data
    schema.parameters["ARROW_SIZE"] = arrow_head_size
    schema.parameters["CURVE_ANGLE"] = curve_angle
    schema.parameters["CENTER_CURVES"] = center_curves
    schema.parameters["MAXIMUM_LINE_WIDTH"] = maximum_line_width
    schema.parameters["DRAW_ARROWS"] = draw_arrows
    schema.parameters["LOOP_SIZE"] = loop_size
    schema.parameters["CONNECTION_LABEL_SIZE"] = connection_label_size
    schema.parameters["CONNECTION_LABEL_COLOR"] = connection_label_color

    return _write_schema_file(output_path, schema)


def generate_pie_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_columns: list[str],
    colors: list[str] | None = None,
    label: str = "pie",
    id_column: str = "id",
    pie_size: str = "50",
    separator: str = DEFAULT_SEPARATOR,
    position_column: str = "position",
    radius_column: str = "radius",
    default_position: str = "0",
    default_radius: str = "1",
) -> Path:
    """Generate a pie chart template from proportion data.

    Official iTOL format requires each data row to be:
        id <sep> position <sep> radius <sep> value1 <sep> value2 ...

    Position and radius are read from ``position_column`` and ``radius_column``
    when present in the input DataFrame; otherwise the defaults are used, which
    keeps old-style callers (that only pass ``value_columns``) working.
    """
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    # Avoid conflicts if position/radius accidentally appear in value_columns.
    value_columns = [vc for vc in value_columns if vc not in (position_column, radius_column)]

    # NOTE: colors must be derived from the *filtered* value_columns so that
    # FIELD_COLORS aligns 1:1 with FIELD_LABELS (and the per-row value columns).
    # Computing them before filtering would yield one extra color whenever
    # 'position'/'radius' were passed as value columns -> pie field misalignment.
    if colors is None:
        colors = list(assign_colors_to_categories(value_columns).values())

    has_position = position_column in df.columns
    has_radius = radius_column in df.columns

    data = []
    for _, row in df.iterrows():
        row_data: dict[str, str] = {"id": row["id"]}
        row_data[position_column] = str(row[position_column]) if has_position else default_position
        row_data[radius_column] = str(row[radius_column]) if has_radius else default_radius
        for vc in value_columns:
            val = row[vc]
            row_data[vc] = "0" if pd.isna(val) else str(val)
        data.append(row_data)

    schema = create_schema("pie", label=label, separator=separator)
    schema.columns = ["id", position_column, radius_column, *value_columns]
    schema.data_rows = data
    schema.parameters["MAXIMUM_SIZE"] = pie_size
    schema.parameters["FIELD_LABELS"] = sep_of(separator).join(value_columns)
    schema.parameters["FIELD_COLORS"] = sep_of(separator).join(colors)

    return _write_schema_file(output_path, schema)


def generate_multibar_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_columns: list[str],
    colors: list[str] | None = None,
    field_labels: list[str] | None = None,
    label: str = "multi_bar",
    id_column: str = "id",
    width: str = "1000",
    alignment: str = "center",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
    align_fields: str = "0",
    on_branch: str = "0",
    show_value: str = "0",
    bar_label_color: str = "#000000",
    label_auto_color: str = "0",
    log_scale: str = "0",
) -> Path:
    """Generate a multi-value bar chart template."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    if colors is None:
        colors = list(assign_colors_to_categories(value_columns).values())
    if field_labels is None:
        field_labels = value_columns

    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for vc in value_columns:
            val = row[vc]
            row_data[vc] = "0" if pd.isna(val) else val
        data.append(row_data)

    schema = create_schema("multi_bar", label=label, separator=separator)
    schema.columns = ["id", *value_columns]
    schema.data_rows = data
    schema.parameters["WIDTH"] = width
    schema.parameters["ALIGN_FIELDS"] = align_fields
    schema.parameters["ON_BRANCH"] = on_branch
    schema.parameters["SHOW_VALUE"] = show_value
    schema.parameters["BAR_LABEL_COLOR"] = bar_label_color
    schema.parameters["LABEL_AUTO_COLOR"] = label_auto_color
    schema.parameters["LOG_SCALE"] = log_scale
    schema.parameters["FIELD_LABELS"] = sep_of(separator).join(field_labels)
    schema.parameters["FIELD_COLORS"] = sep_of(separator).join(colors)
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_boxplot_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    id_column: str = "id",
    min_column: str = "minimum",
    q1_column: str = "q1",
    median_column: str = "median",
    q3_column: str = "q3",
    max_column: str = "maximum",
    extremes_columns: list[str] | None = None,
    label: str = "boxplot",
    color: str = "#00ff00",
    width: str = "1500",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate a boxplot template from distribution data."""

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    for col in [min_column, q1_column, median_column, q3_column, max_column]:
        if col not in df.columns:
            raise InvalidColumnError(f"Column '{col}' not found. Available: {list(df.columns)}")

    cols = ["id", min_column, q1_column, median_column, q3_column, max_column]
    if extremes_columns:
        for ec in extremes_columns:
            if ec not in df.columns:
                raise InvalidColumnError(f"Extremes column '{ec}' not found. Available: {list(df.columns)}")
        cols.extend(extremes_columns)

    data = []
    for _, row in df.iterrows():
        row_data = {c: row[c] for c in cols}
        data.append(row_data)

    schema = create_schema("boxplot", label=label, color=color, separator=separator)
    schema.columns = cols
    schema.data_rows = data
    schema.parameters["WIDTH"] = width
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_domain_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "domains",
    color: str = "#ff00aa",
    scale: str | None = None,
    separator: str = DEFAULT_SEPARATOR,
    shape_scale: str = "1",
    data_set_scale: str | None = None,
) -> Path:
    """Generate a protein domains template.

    Accepts both the legacy column layout (id, from, to, type, color) and the
    official iTOL format where each row contains ``id`` and ``domain`` with a
    value like ``SHAPE|START|END|COLOR|LABEL``.
    """
    schema = create_schema("domains", label=label, color=color, separator=separator)
    if data_rows:
        keys = list(data_rows[0].keys())
        if "domain" in keys:
            schema.columns = ["id", "domain"]
        else:
            schema.columns = keys
    else:
        schema.columns = ["id", "from", "to", "type", "color"]
    schema.data_rows = data_rows
    schema.parameters["SHAPE_SCALE"] = shape_scale
    if data_set_scale is not None:
        schema.parameters["DATASET_SCALE"] = data_set_scale
    elif scale is not None:
        schema.parameters["DATASET_SCALE"] = scale

    return _write_schema_file(output_path, schema)


def generate_gradient_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_column: str,
    label: str = "gradient",
    id_column: str = "id",
    color_min: str = DEFAULT_HEATMAP_GRADIENT[0],
    color_max: str = DEFAULT_HEATMAP_GRADIENT[-1],
    strip_width: str = "25",
    use_mid_color: bool = False,
    color_mid: str = "#ffff00",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate a gradient color template."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    if value_column not in df.columns:
        raise InvalidColumnError(f"Column '{value_column}' not found. Available: {list(df.columns)}")

    data = []
    for _, row in df.iterrows():
        val = row[value_column]
        if pd.isna(val):
            continue
        data.append({"id": row["id"], "value": val})

    schema = create_schema("gradient", label=label, separator=separator)
    schema.columns = ["id", "value"]
    schema.data_rows = data
    schema.parameters["STRIP_WIDTH"] = strip_width
    schema.parameters["COLOR_MIN"] = color_min
    schema.parameters["COLOR_MAX"] = color_max
    if use_mid_color:
        schema.parameters["USE_MID_COLOR"] = "1"
        schema.parameters["COLOR_MID"] = color_mid
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_external_shape_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    column: str,
    shape_type: str = "circle",
    colors: dict | None = None,
    label: str = "external_shape",
    id_column: str = "id",
    size: str = "20",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate an external shape template."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    if column not in df.columns:
        raise InvalidColumnError(f"Column '{column}' not found. Available: {list(df.columns)}")

    colors = _assign_colors(df, column, colors)

    # Reuse the shared EXTERNAL_SHAPE_MAP so both externalshape generator
    # functions stay consistent.
    if shape_type not in EXTERNAL_SHAPE_MAP:
        logger.warning(
            "未知的外部形状 '%s'，已回退到 circle (类型 2)。可选: %s",
            shape_type,
            sorted(EXTERNAL_SHAPE_MAP.keys()),
        )
    shape_code = EXTERNAL_SHAPE_MAP.get(shape_type, "2")

    data = []
    for _, row in df.iterrows():
        val = row[column]
        if pd.isna(val):
            continue
        data.append(
            {
                "id": row["id"],
                "type": shape_code,
                "value": size,
                "color": colors.get(val, DEFAULT_MISSING_COLOR),
                "label": val,
            }
        )

    schema = create_schema("externalshape", label=label, separator=separator)
    schema.columns = ["id", "type", "value", "color", "label"]
    schema.data_rows = data
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_external_shape_bubble_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    value_columns: list[str],
    colors: list[str] | None = None,
    field_labels: list[str] | None = None,
    shape_type: str = "circle",
    label: str = "external_shape",
    id_column: str = "id",
    fill: str = "1",
    height_factor: str = "1",
    separator: str = DEFAULT_SEPARATOR,
    margin: str = "0",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate a DATASET_EXTERNALSHAPE bubble/shape plot template from numeric columns.

    Values in each column are mapped to shape sizes proportionally (largest value
    in the column is rendered at the maximum size). This matches the iTOL
    dataset_external_shapes_template.txt format.
    """
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    for vc in value_columns:
        if vc not in df.columns:
            raise InvalidColumnError(f"Column '{vc}' not found. Available: {list(df.columns)}")

    if colors is None:
        colors = list(assign_colors_to_categories(value_columns).values())
    if field_labels is None:
        field_labels = value_columns

    # Reuse the shared EXTERNAL_SHAPE_MAP (bubble does not support
    # checkmark; falls back to circle).
    if shape_type not in EXTERNAL_SHAPE_MAP:
        logger.warning(
            "未知的外部形状 '%s'，已回退到 circle (类型 2)。可选: %s",
            shape_type,
            sorted(EXTERNAL_SHAPE_MAP.keys()),
        )
    shape_code = EXTERNAL_SHAPE_MAP.get(shape_type, "2")

    sep = get_separator_char(separator)
    data = []
    for _, row in df.iterrows():
        row_data = {"id": row["id"]}
        for vc in value_columns:
            val = row[vc]
            row_data[vc] = "" if pd.isna(val) else val
        data.append(row_data)

    schema = create_schema("externalshape", label=label, color=colors[0], separator=separator)
    schema.columns = ["id", *value_columns]
    schema.data_rows = data
    schema.parameters["FIELD_COLORS"] = sep.join(colors[: len(value_columns)])
    schema.parameters["FIELD_LABELS"] = sep.join(field_labels[: len(value_columns)])
    schema.parameters["SHAPE_TYPE"] = shape_code
    schema.parameters["COLOR_FILL"] = fill
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_text_template(
    output_path: str | Path,
    taxonomy_path: str | Path,
    tree_path: str | Path,
    text_column: str,
    label: str = "text",
    id_column: str = "id",
    font_size: str = "12",
    font_style: str = "normal",
    separator: str = DEFAULT_SEPARATOR,
    label_position: str = "0",
    label_color: str = "#000000",
    label_size: str = "10",
    label_style: str = "normal",
    label_rotation: str = "0",
    straight_labels: str = "0",
    align: str = "0",
) -> Path:
    """Generate a text label template."""
    import pandas as pd

    _, df, _ = _read_taxonomy_and_tree(taxonomy_path, tree_path, id_column)

    if text_column not in df.columns:
        raise InvalidColumnError(f"Column '{text_column}' not found. Available: {list(df.columns)}")

    data = []
    for _, row in df.iterrows():
        val = row[text_column]
        if pd.isna(val) or str(val).strip() == "":
            continue
        data.append({"id": row["id"], "text": str(val)})

    schema = create_schema("text", label=label, separator=separator)
    schema.columns = ["id", "text"]
    schema.data_rows = data
    # iTOL DATASET_TEXT's label font-size multiplier parameter is exactly
    # LABEL_SIZE_FACTOR (multiplier, 1.0 = original size); the parameter name
    # here already matches the official one, no change needed.
    schema.parameters["LABEL_SIZE_FACTOR"] = font_size
    schema.parameters["LABEL_POSITION"] = label_position
    schema.parameters["LABEL_COLOR"] = label_color
    schema.parameters["LABEL_SIZE"] = label_size
    schema.parameters["LABEL_STYLE"] = label_style
    schema.parameters["LABEL_ROTATION"] = label_rotation
    schema.parameters["STRAIGHT_LABELS"] = straight_labels
    schema.parameters["ALIGN"] = align

    return _write_schema_file(output_path, schema)


def generate_arrow_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "arrows",
    color: str = DEFAULT_PRIMARY_COLOR,
    arrow_size: str = "30",
    separator: str = DEFAULT_SEPARATOR,
    arrow_width: str = "1",
) -> Path:
    """Generate an arrows template.

    Supports the legacy layout (id, position, direction, color) as well as the
    official backbone/arrow/mark format by using the keys present in the first
    data row.
    """
    schema = create_schema("arrows", label=label, color=color, separator=separator)
    if data_rows:
        schema.columns = list(data_rows[0].keys())
    else:
        schema.columns = ["id", "position", "direction", "color"]
    schema.data_rows = data_rows
    schema.parameters["MAXIMUM_SIZE"] = arrow_size
    schema.parameters["ARROW_WIDTH"] = arrow_width

    return _write_schema_file(output_path, schema)


def generate_linechart_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "linechart",
    color: str = "#3c5484",
    line_width: str = "2",
    show_points: str = "1",
    separator: str = DEFAULT_SEPARATOR,
    axis_x: str = "1",
    axis_y: str = "1",
    chart_direction: str = "0",
    fill_under: str = "0",
) -> Path:
    """Generate a line chart template."""
    schema = create_schema("linechart", label=label, color=color, separator=separator)
    schema.columns = ["id", "position", "value"]
    schema.data_rows = data_rows
    schema.parameters["LINE_WIDTH"] = line_width
    schema.parameters["SHOW_DOTS"] = show_points
    schema.parameters["AXIS_X"] = axis_x
    schema.parameters["AXIS_Y"] = axis_y
    schema.parameters["CHART_DIRECTION"] = chart_direction
    schema.parameters["FILL_UNDER"] = fill_under

    return _write_schema_file(output_path, schema)


def generate_image_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "images",
    image_width: str = "50",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate an image annotation template."""
    schema = create_schema("image", label=label, separator=separator)
    schema.columns = ["id", "image_file", "image_url"]
    schema.data_rows = data_rows
    schema.parameters["MAXIMUM_SIZE"] = image_width

    return _write_schema_file(output_path, schema)


def generate_alignment_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "alignment",
    color_scheme: str = "nucleotide",
    separator: str = DEFAULT_SEPARATOR,
    consensus_threshold: str = "0",
    ignore_gaps: str = "1",
    highlight_type: str = "0",
    mark_references: str = "0",
) -> Path:
    """Generate a sequence alignment template."""
    schema = create_schema("alignment", label=label, separator=separator)
    schema.columns = ["id", "alignment"]
    schema.data_rows = data_rows
    schema.parameters["COLOR_SCHEME"] = color_scheme
    schema.parameters["CONSENSUS_THRESHOLD"] = consensus_threshold
    schema.parameters["IGNORE_GAPS"] = ignore_gaps
    schema.parameters["HIGHLIGHT_TYPE"] = highlight_type
    schema.parameters["MARK_REFERENCES"] = mark_references

    return _write_schema_file(output_path, schema)


def generate_tanglegram_template(
    output_path: str | Path,
    connections: list[tuple],
    label: str = "tanglegram",
    color: str = DEFAULT_MISSING_COLOR,
    line_width: str = "1",
    separator: str = DEFAULT_SEPARATOR,
    second_tree: str | None = None,
    style_params: dict | None = None,
    template_name: str | None = None,
) -> Path:
    """Generate a tanglegram template.

    If ``second_tree`` is provided, it will be embedded between
    ``TANGLEGRAM_TREE`` and ``END_TANGLEGRAM_TREE`` markers, matching the
    official iTOL format.
    """
    data = []
    for pair in connections:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            data.append({"id1": pair[0], "id2": pair[1], "color": color, "width": line_width})

    schema = create_schema("tanglegram", label=label, separator=separator)
    schema.columns = ["id1", "id2", "color", "width"]
    schema.data_rows = data

    gen = TemplateGenerator()
    gen.add_schema(schema)
    if style_params:
        gen.set_style(style_params)
    if template_name:
        gen.set_name(template_name)

    if second_tree is not None:
        # When second_tree is provided, we need to insert the TANGLEGRAM_TREE
        # block before the DATA marker. Use _write_schema to get content,
        # then insert and write manually (preserving style_params/template_name).
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        content = gen._write_schema(schema)
        lines = content.splitlines()
        data_idx = next((i for i, line in enumerate(lines) if line.strip() == "DATA"), len(lines))
        tree_block = [
            "TANGLEGRAM_TREE",
            second_tree,
            "END_TANGLEGRAM_TREE",
        ]
        lines[data_idx:data_idx] = tree_block
        # Prepend template_name if set
        if gen.template_name:
            lines.insert(0, f"TEMPLATE_NAME\t{gen.template_name}")
            lines.insert(1, "")
        # Prepend style_params section if set
        if gen.style_params:
            style_lines = ["DATASET_TREESTYLE", "", "SEPARATOR TAB"]
            for k, v in gen.style_params.items():
                style_lines.append(f"{k}\t{v}")
            style_section = "\n".join(style_lines)
            content = "\n\n".join([style_section, "\n".join(lines)])
        else:
            content = "\n".join(lines)
        path.write_text(content + "\n", encoding="utf-8")
        return path
    else:
        return gen.write(output_path)


def generate_ranges_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "ranges",
    color: str = DEFAULT_PRIMARY_COLOR,
    margin: str = "0",
    size_factor: str = "1",
    show_labels: str = "1",
    separator: str = DEFAULT_SEPARATOR,
    height_factor: str = "1",
    show_internal: str = "0",
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
    range_type: str = "1",
    range_cover: str = "1",
    unrooted_smooth: str = "0",
    cover_labels: str = "0",
    cover_datasets: str = "0",
    fit_labels: str = "0",
    label_position: str = "0",
    label_size: str = "10",
    label_color: str = "#000000",
    bracket_width: str = "1",
    bracket_color: str = "#000000",
    bracket_style: str = "0",
    gradient_fill: str = "0",
) -> Path:
    """Generate a colored/labeled ranges template."""
    schema = create_schema("range", label=label, color=color, separator=separator)
    if data_rows:
        schema.columns = list(data_rows[0].keys())
    else:
        schema.columns = ["id", "label", "color"]
    schema.data_rows = data_rows
    schema.parameters["SIZE_FACTOR"] = size_factor
    schema.parameters["SHOW_LABELS"] = show_labels
    schema.parameters["RANGE_TYPE"] = range_type
    schema.parameters["RANGE_COVER"] = range_cover
    schema.parameters["UNROOTED_SMOOTH"] = unrooted_smooth
    schema.parameters["COVER_LABELS"] = cover_labels
    schema.parameters["COVER_DATASETS"] = cover_datasets
    schema.parameters["FIT_LABELS"] = fit_labels
    schema.parameters["LABEL_POSITION"] = label_position
    schema.parameters["LABEL_SIZE"] = label_size
    schema.parameters["LABEL_COLOR"] = label_color
    schema.parameters["BRACKET_WIDTH"] = bracket_width
    schema.parameters["BRACKET_COLOR"] = bracket_color
    schema.parameters["BRACKET_STYLE"] = bracket_style
    schema.parameters["GRADIENT_FILL"] = gradient_fill
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_placement_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "placement",
    color: str = DEFAULT_PRIMARY_COLOR,
    spacing: str = "5",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a phylogenetic placement template."""
    schema = create_schema("placement", label=label, color=color, separator=separator)
    schema.columns = ["id", "position", "count", "color"]
    schema.data_rows = data_rows
    schema.parameters["PLACEMENT_SPACING"] = spacing

    return _write_schema_file(output_path, schema)


def generate_timescale_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "timescale",
    color: str = "#000000",
    scale_position: str = "bottom",
    separator: str = DEFAULT_SEPARATOR,
    scaling_factor: str = "1",
    auto_scale: str = "1",
    cover_tree: str = "0",
    show_ranges: str = "0",
) -> Path:
    """Generate a timescale template."""
    schema = create_schema("timescale", label=label, color=color, separator=separator)
    schema.columns = ["time_point", "label", "color"]
    schema.data_rows = data_rows
    schema.parameters["SCALE_POSITION"] = scale_position
    schema.parameters["SCALING_FACTOR"] = scaling_factor
    schema.parameters["AUTO_SCALE"] = auto_scale
    schema.parameters["COVER_TREE"] = cover_tree
    schema.parameters["SHOW_RANGES"] = show_ranges

    return _write_schema_file(output_path, schema)


def generate_meme_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "meme",
    color: str = DEFAULT_PRIMARY_COLOR,
    show_labels: str = "1",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a MEME motifs template."""
    schema = create_schema("meme", label=label, color=color, separator=separator)
    schema.columns = ["id", "start", "end", "name", "color"]
    schema.data_rows = data_rows
    schema.parameters["SHOW_MOTIF_LABELS"] = show_labels

    return _write_schema_file(output_path, schema)


def generate_labels_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "labels",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a node labels renaming template."""
    schema = create_schema("labels", label=label, separator=separator)
    schema.columns = ["id", "label"]
    schema.data_rows = data_rows

    return _write_schema_file(output_path, schema)


def generate_popup_info_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "popup_info",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a popup info template."""
    schema = create_schema("popup_info", label=label, separator=separator)
    schema.columns = ["id", "title", "content"]
    schema.data_rows = data_rows

    return _write_schema_file(output_path, schema)


def generate_tree_colors_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "tree_colors",
    color: str = DEFAULT_PRIMARY_COLOR,
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a tree colors template (branch/label/clade coloring)."""
    schema = create_schema("tree_colors", label=label, color=color, separator=separator)
    schema.columns = ["id", "type", "color", "what"]
    schema.data_rows = data_rows

    return _write_schema_file(output_path, schema)


def generate_collapse_template(
    output_path: str | Path,
    node_ids: list[str],
    label: str = "collapse",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a collapse clades template."""
    data = [{"id": nid} for nid in node_ids]

    schema = create_schema("collapse", label=label, separator=separator)
    schema.columns = ["id"]
    schema.data_rows = data

    return _write_schema_file(output_path, schema)


def generate_prune_template(
    output_path: str | Path,
    node_ids: list[str],
    label: str = "prune",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a prune tree template."""
    data = [{"id": nid} for nid in node_ids]

    schema = create_schema("prune", label=label, separator=separator)
    schema.columns = ["id"]
    schema.data_rows = data

    return _write_schema_file(output_path, schema)


def generate_spacing_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "spacing",
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a node spacing template."""
    schema = create_schema("spacing", label=label, separator=separator)
    schema.columns = ["id", "factor"]
    schema.data_rows = data_rows

    return _write_schema_file(output_path, schema)


def generate_binary_template(
    output_path: str | Path,
    data_rows: list[dict],
    field_labels: list[str],
    field_colors: list[str],
    field_shapes: list[str],
    label: str = "binary",
    color: str = DEFAULT_PRIMARY_COLOR,
    show_internal: str = "1",
    margin: str = "0",
    height_factor: str = "1",
    symbol_spacing: str = "10",
    separator: str = DEFAULT_SEPARATOR,
    border_width: str = "0",
    border_color: str = DEFAULT_BORDER_COLOR,
    dataset_scale: list[str] | None = None,
) -> Path:
    """Generate a binary data template."""
    schema = create_schema("binary", label=label, color=color, separator=separator)
    schema.columns = ["id", *field_labels]
    schema.data_rows = data_rows
    schema.parameters["FIELD_LABELS"] = sep_of(separator).join(field_labels)
    schema.parameters["FIELD_COLORS"] = sep_of(separator).join(field_colors)
    schema.parameters["FIELD_SHAPES"] = sep_of(separator).join(field_shapes)
    schema.parameters["SYMBOL_SPACING"] = symbol_spacing
    _apply_common_visual_params(
        schema,
        separator,
        margin=margin,
        height_factor=height_factor,
        show_internal=show_internal,
        border_width=border_width,
        border_color=border_color,
        dataset_scale=dataset_scale,
    )

    return _write_schema_file(output_path, schema)


def generate_style_template(
    output_path: str | Path,
    data_rows: list[dict],
    label: str = "style",
    color: str = DEFAULT_PRIMARY_COLOR,
    separator: str = DEFAULT_SEPARATOR,
) -> Path:
    """Generate a DATASET_STYLE template (v7 modern replacement for TREE_COLORS).

    Each data row should contain: id, type, color, and optionally:
    - for branch styles: size, style (solid/dashed/dotted)
    - for label styles: font, size, style
    - for label_background: size, style
    """
    schema = create_schema("style", label=label, color=color, separator=separator)
    if data_rows:
        schema.columns = list(data_rows[0].keys())
    else:
        schema.columns = ["id", "type", "color"]
    schema.data_rows = data_rows

    return _write_schema_file(output_path, schema)
