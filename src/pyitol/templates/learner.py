"""Template learner engine - reverse-parse iTOL template files.

Provides equivalent functionality to itol.toolkit's learn module
(independent Python reimplementation; itol.toolkit is an R package):
type, separator, profile, field, common_themes, specific_themes, data.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pyitol.templates.schemas.base import SEPARATOR_MAP

logger = logging.getLogger(__name__)


def _build_header_reverse() -> dict[str, str]:
    """Build HEADER_REVERSE by merging static mapping with registry.

    P1-8: Starts from a comprehensive static mapping (including aliases like
    'SYMBOL' -> 'dataset_symbols') and then enriches it with any additional
    types registered dynamically via @register_template.
    """
    # Start with the comprehensive static mapping (includes aliases)
    reverse = dict(_HEADER_REVERSE_STATIC)
    # Enrich from registry for any types not in the static mapping
    try:
        from pyitol.templates.schemas.base import default_registry

        for type_name, header_str in default_registry.type_header.items():
            if header_str not in reverse:
                reverse[header_str] = type_name
    except Exception:  # noqa: S110
        pass
    return reverse


# Comprehensive static mapping (primary headers + known aliases)
_HEADER_REVERSE_STATIC: dict[str, str] = {
    "DATASET_SIMPLEBAR": "dataset_simple_bar",
    "DATASET_MULTIBAR": "dataset_multibar",
    "DATASET_COLORSTRIP": "dataset_colorstrip",
    "DATASET_HEATMAP": "dataset_heatmap",
    "DATASET_SYMBOLS": "dataset_symbols",
    "DATASET_SYMBOL": "dataset_symbols",  # alias
    "SYMBOL": "dataset_symbols",  # alias
    "DATASET_PIECHART": "dataset_piechart",
    "DATASET_BINARY": "dataset_binary",
    "DATASET_RANGE": "dataset_range",
    "DATASET_EXTERNALSHAPE": "dataset_externalshape",
    "DATASET_CONNECTION": "dataset_connections",
    "CONNECTION": "dataset_connections",  # alias
    "DATASET_DOMAINS": "dataset_domains",
    "DATASET_ALIGNMENT": "dataset_alignment",
    "DATASET_IMAGE": "dataset_image",
    "DATASET_TEXT": "dataset_text",
    "DATASET_GRADIENT": "dataset_gradient",
    "DATASET_BOXPLOT": "dataset_boxplot",
    "DATASET_LINECHART": "dataset_linechart",
    "DATASET_ARROWS": "dataset_arrows",
    "DATASET_TANGLEGRAM": "dataset_tanglegram",
    "DATASET_PLACEMENT": "dataset_placement",
    "DATASET_TIMESCALE": "dataset_timescale",
    "DATASET_MANUAL": "dataset_manual",
    "DATASET_MEME": "dataset_meme",
    "DATASET_STYLE": "dataset_style",
    "TREE_COLORS": "dataset_tree_colors",
    "COLLAPSE": "dataset_collapse",
    "PRUNE": "dataset_prune",
    "SPACING": "dataset_spacing",
    "LABELS": "dataset_labels",
    "POPUP_INFO": "dataset_popup_info",
}

# Build on import; enriches static mapping with any registry-only types
HEADER_REVERSE = _build_header_reverse()

_NON_DATASET_HEADERS = frozenset(
    {
        "TREE_COLORS",
        "COLLAPSE",
        "PRUNE",
        "SPACING",
        "LABELS",
        "POPUP_INFO",
    }
)

# Theme parameter grouping inspired by itol.toolkit's learn.R (independent implementation)
COMMON_THEME_KEYS = {
    "legend": [
        "LEGEND_TITLE",
        "LEGEND_POSITION_X",
        "LEGEND_POSITION_Y",
        "LEGEND_HORIZONTAL",
        "LEGEND_SHAPES",
        "LEGEND_COLORS",
        "LEGEND_LABELS",
        "LEGEND_SHAPE_SCALES",
    ],
    "basic_theme": [
        "SHOW_INTERNAL",
        "MARGIN",
        "SIZE_FACTOR",
    ],
    "label": [
        "SHOW_LABELS",
        "LABEL_SIZE_FACTOR",
        "LABELS_ON_TOP",
        "LABELS_BELOW",
        "LABEL_ROTATION",
        "STRAIGHT_LABELS",
        "VERTICAL_SHIFT",
        "LABEL_SHIFT",
        "EXTERNAL_LABEL_SHIFT",
    ],
    "border": [
        "BORDER_WIDTH",
        "BORDER_COLOR",
        "COMPLETE_BORDER",
    ],
    "align": [
        "ALIGN_TO_LABELS",
        "ALIGN_FIELDS",
        "ALIGN_TO_TREE",
    ],
}

SPECIFIC_THEME_KEYS = {
    "basic_plot": [
        "DATASET_SCALE",
        "WIDTH",
        "HEIGHT_FACTOR",
        "MAXIMUM_SIZE",
        "SHOW_VALUES",
        "SHOW_VALUE",
        "DASHED_LINES",
    ],
    "bar": ["BAR_SHIFT", "BAR_ZERO"],
    "strip_label": [
        "SHOW_STRIP_LABELS",
        "STRIP_WIDTH",
        "STRIP_LABEL_SIZE_FACTOR",
        "STRIP_LABEL_COLOR",
        "COLOR_BRANCHES",
        "STRIP_LABEL_POSITION",
        "STRIP_LABEL_SHIFT",
        "STRIP_LABEL_ROTATION",
        "STRIP_LABEL_OUTLINE",
    ],
    "heatmap": [
        "COLOR_NAN",
        "COLOR_MIN",
        "COLOR_MID",
        "COLOR_MAX",
        "USER_MIN_VALUE",
        "USER_MID_VALUE",
        "USER_MAX_VALUE",
        "FIELD_TREE",
        "SHOW_TREE",
        "USE_MID_COLOR",
        "AUTO_LEGEND",
    ],
    "binary": ["SYMBOL_SPACING"],
    "domain": [
        "SHOW_DOMAIN_LABELS",
        "GRADIENT_FILL",
        "BACKBONE_COLOR",
        "BACKBONE_HEIGHT",
    ],
    "linechart": [
        "LINE_COLORS",
        "AXIS_X",
        "AXIS_Y",
        "VERTICAL_CHART",
        "CHART_SHIFT",
        "SHOW_LINE",
        "LINE_WIDTH",
        "DEFAULT_LINE_COLOR",
        "SHOW_DOTS",
        "DOT_SIZE",
        "SHOW_TITLE",
        "TITLE_SIZE",
        "TITLE_COLOR",
        "TITLE_SHIFT_X",
        "TITLE_SHIFT_Y",
    ],
    "piechart": ["POLAR_AREA_DIAGRAM"],
    "alignment": [
        "CUSTOM_COLOR_SCHEME",
        "COLOR_SCHEME",
        "HIGHLIGHT_REFERENCES",
        "MARK_REFERENCES",
        "REFERENCE_BOX_BORDER_WIDTH",
        "REFERENCE_BOX_BORDER_COLOR",
        "REFERENCE_BOX_FILL_COLOR",
        "START_POSITION",
        "END_POSITION",
        "HIGHLIGHT_TYPE",
        "HIGHLIGHT_DISAGREEMENTS",
        "COLORED_DOTS",
        "INVERSE_GAPS",
        "IGNORE_GAPS",
        "DISPLAY_CONSENSUS",
        "CONSENSUS_THRESHOLD",
        "DISPLAY_CONSERVATION",
        "COLOR_GRAPH",
    ],
    "connection": [
        "DRAW_ARROWS",
        "ARROW_SIZE",
        "LOOP_SIZE",
        "MAXIMUM_LINE_WIDTH",
        "CURVE_ANGLE",
        "CENTER_CURVES",
    ],
    "image": ["IMAGE_ROTATION", "IMAGE_SHIFT_V", "IMAGE_SHIFT_H"],
    "externalshape": [
        "HORIZONTAL_GRID",
        "VERTICAL_GRID",
        "SHAPE_SPACING",
        "SHAPE_TYPE",
        "COLOR_FILL",
    ],
}


def learn_type(lines: list[str]) -> str:
    """Extract template type from the first non-empty, non-comment line."""
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return ""


def learn_separator(lines: list[str]) -> str:
    """Learn separator type from SEPARATOR line."""
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("SEPARATOR"):
            parts = stripped.split(None, 1)
            if len(parts) >= 2:
                sep_name = parts[1].strip()
                return SEPARATOR_MAP.get(sep_name, "\t")
    return "\t"  # default


def learn_profile(parameters: dict[str, str]) -> dict:
    """Extract profile parameters (dataset name and color)."""
    return {
        "name": parameters.get("DATASET_LABEL", ""),
        "color": parameters.get("COLOR", ""),
    }


def learn_field(parameters: dict[str, str], sep: str) -> dict:
    """Extract field parameters (labels, colors, shapes)."""
    field = {}
    if "FIELD_LABELS" in parameters:
        field["labels"] = parameters["FIELD_LABELS"].split(sep)
    if "FIELD_COLORS" in parameters:
        field["colors"] = parameters["FIELD_COLORS"].split(sep)
    if "FIELD_SHAPES" in parameters:
        field["shapes"] = parameters["FIELD_SHAPES"].split(sep)
    return field


def learn_common_themes(parameters: dict[str, str]) -> dict:
    """Extract common theme parameters grouped by category."""
    common = {}
    for theme_name, keys in COMMON_THEME_KEYS.items():
        theme_data = {}
        for key in keys:
            if key in parameters:
                theme_data[_normalize_key(key)] = parameters[key]
        if theme_data:
            common[theme_name] = theme_data
    return common


def learn_specific_themes(parameters: dict[str, str], ds_type: str) -> dict:
    """Extract type-specific theme parameters."""
    specific = {}
    # Determine which specific theme groups are relevant
    relevant_groups = _get_relevant_specific_groups(ds_type)
    for group_name in relevant_groups:
        keys = SPECIFIC_THEME_KEYS.get(group_name, [])
        group_data = {}
        for key in keys:
            if key in parameters:
                group_data[_normalize_key(key)] = parameters[key]
        if group_data:
            specific[group_name] = group_data
    return specific


def _get_relevant_specific_groups(ds_type: str) -> list[str]:
    """Determine relevant specific theme groups based on dataset type."""
    type_upper = ds_type.upper().replace("DATASET_", "")
    mapping = {
        "BINARY": ["basic_plot", "binary"],
        "COLORSTRIP": ["basic_plot", "strip_label", "heatmap"],
        "GRADIENT": ["basic_plot", "strip_label", "heatmap"],
        "HEATMAP": ["basic_plot", "strip_label", "heatmap"],
        "EXTERNALSHAPE": ["basic_plot", "externalshape"],
        "SYMBOLS": ["basic_plot", "bar", "domain"],
        "SYMBOL": ["basic_plot", "bar", "domain"],
        "SIMPLEBAR": ["basic_plot", "bar", "domain"],
        "MULTIBAR": ["basic_plot", "bar", "domain"],
        "DOMAINS": ["basic_plot", "bar", "domain"],
        "BOXPLOT": ["basic_plot", "bar", "domain"],
        "LINECHART": ["basic_plot", "linechart"],
        "PIECHART": ["basic_plot", "piechart"],
        "ALIGNMENT": ["alignment"],
        "CONNECTION": ["connection"],
        "IMAGE": ["image"],
    }
    return mapping.get(type_upper, ["basic_plot"])


def _normalize_key(key: str) -> str:
    """Normalize parameter key to snake_case."""
    return key.lower().replace("strip_label_", "").replace("label_", "").replace("reference_box_", "ref_")


def learn_template(template_path: str) -> dict:
    """Parse an iTOL template file and extract its full structure.

    Returns dict with:
        - template_name
        - datasets: list of parsed dataset dicts, each containing:
            - type, header
            - separator
            - profile (name, color)
            - field (labels, colors, shapes)
            - common_themes (legend, basic_theme, label, border, align)
            - specific_themes (type-dependent)
            - parameters (raw)
            - data (list of row dicts)
            - columns
    """
    path = Path(template_path)
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    template_name = ""
    datasets: list[dict[str, Any]] = []
    current_dataset: dict[str, Any] | None = None
    in_data = False
    columns: list[str] = []
    sep = "\t"

    for idx, line in enumerate(lines):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("TEMPLATE_NAME"):
            template_name = stripped[len("TEMPLATE_NAME") :].strip()
            continue

        # Detect dataset header
        if stripped in HEADER_REVERSE or stripped.startswith("DATASET "):
            if current_dataset:
                datasets.append(current_dataset)
            header = stripped if stripped in _NON_DATASET_HEADERS else stripped.replace("DATASET ", "DATASET_").strip()
            ds_type = HEADER_REVERSE.get(header, HEADER_REVERSE.get(stripped, header))
            current_dataset = {
                "type": ds_type,
                "header": header,
                "original_header": stripped,
                "separator": "\t",
                "parameters": {},
                "profile": {},
                "field": {},
                "common_themes": {},
                "specific_themes": {},
                "data": [],
                "columns": [],
            }
            in_data = False
            columns = []
            continue

        if current_dataset is None:
            continue

        if stripped.startswith("SEPARATOR"):
            parts = stripped.split(None, 1)
            if len(parts) >= 2:
                sep_name = parts[1].strip()
                sep = SEPARATOR_MAP.get(sep_name, "\t")
                current_dataset["separator"] = sep
            continue

        if stripped == "DATA":
            in_data = True
            continue

        # P1-10: Handle TANGLEGRAM_TREE block
        if stripped == "TANGLEGRAM_TREE":
            if current_dataset is not None:
                tanglegram_lines = []
                # Locate subsequent content via the enumeration index idx of
                # the current line, avoiding lines.index(line) which would jump to
                # the first occurrence when the tree content contains duplicate lines.
                for tline in lines[idx + 1 :]:
                    tstripped = tline.strip()
                    if tstripped == "END_TANGLEGRAM_TREE":
                        break
                    tanglegram_lines.append(tline)
                current_dataset["tanglegram_tree"] = "\n".join(tanglegram_lines)
            continue
        if stripped == "END_TANGLEGRAM_TREE":
            continue

        if in_data:
            # P1-xx: Skip empty lines so they never trigger column inference on a
            # single empty field, which would otherwise silently drop single-column
            # data rows (e.g. COLLAPSE/PRUNE node IDs) parsed below.
            if not stripped:
                continue
            parts = line.split(sep)
            if not columns:
                # Infer column structure from the first data row based on header type.
                # iTOL v7 format has no column header row after DATA;
                # all lines after DATA are actual data rows.
                columns = [f"col_{i}" for i in range(len(parts))]
                header_check = current_dataset.get("original_header", current_dataset["header"])
                if header_check == "TREE_COLORS":
                    columns = ["id", "type", "color", "style", "size"][: len(parts)]
                elif header_check in ("DATASET_SIMPLEBAR", "SIMPLEBAR"):
                    columns = ["id", "bar_height"][: len(parts)]
                elif header_check in ("DATASET_COLORSTRIP", "COLORSTRIP"):
                    columns = ["id", "value", "color"][: len(parts)]
                elif header_check in ("DATASET_SYMBOLS", "SYMBOL"):
                    columns = ["id", "type", "value", "color", "label"][: len(parts)]
                elif header_check == "COLLAPSE" or header_check == "PRUNE":
                    columns = ["id"][: len(parts)]
                elif header_check == "SPACING":
                    columns = ["id", "factor"][: len(parts)]
                elif header_check == "LABELS":
                    columns = ["id", "label"][: len(parts)]
                elif header_check == "POPUP_INFO":
                    columns = ["id", "title", "content"][: len(parts)]
                elif header_check in ("DATASET_CONNECTION", "CONNECTION"):
                    columns = ["id1", "id2", "color", "width", "type"][: len(parts)]
                elif header_check in ("DATASET_BINARY", "BINARY"):
                    columns = ["id"] + [f"field_{i}" for i in range(1, len(parts))]
                # P1-9: Column inference for remaining 18 types
                elif (
                    header_check in ("DATASET_MULTIBAR", "MULTIBAR")
                    or header_check in ("DATASET_HEATMAP", "HEATMAP")
                    or header_check in ("DATASET_PIECHART", "PIECHART")
                ):
                    columns = ["id"] + [f"value_{i}" for i in range(1, len(parts))]
                elif header_check in ("DATASET_GRADIENT", "GRADIENT"):
                    columns = ["id", "value", "color"][: len(parts)]
                elif header_check in ("DATASET_EXTERNALSHAPE", "EXTERNALSHAPE"):
                    # Single-shape externalshape is isomorphic to symbols;
                    # align column names to ['id','type','value','color','label']
                    # to keep semantic names for round-tripping.  The bubble
                    # multi-value variant (column count != 5) still falls back
                    # to value_N inference.
                    if len(parts) == 5:
                        columns = ["id", "type", "value", "color", "label"][: len(parts)]
                    else:
                        columns = ["id"] + [f"value_{i}" for i in range(1, len(parts))]
                elif header_check in ("DATASET_TEXT", "TEXT"):
                    columns = ["id", "text"][: len(parts)]
                elif header_check in ("DATASET_BOXPLOT", "BOXPLOT"):
                    columns = ["id"] + [f"value_{i}" for i in range(1, len(parts))]
                elif header_check in ("DATASET_DOMAINS", "DOMAINS"):
                    if len(parts) == 2:
                        columns = ["id", "domain"]
                    else:
                        columns = ["id", "from", "to", "type", "label", "color"][: len(parts)]
                elif header_check in ("DATASET_ARROWS", "ARROWS"):
                    columns = ["id", "position", "value"][: len(parts)]
                elif header_check in ("DATASET_TANGLEGRAM", "TANGLEGRAM"):
                    columns = ["id1", "id2", "color", "width"][: len(parts)]
                elif header_check in ("DATASET_LINECHART", "LINECHART"):
                    columns = ["id", "position", "value"][: len(parts)]
                elif header_check in ("DATASET_IMAGE", "IMAGE"):
                    columns = ["id", "image_file", "width"][: len(parts)]
                elif header_check in ("DATASET_ALIGNMENT", "ALIGNMENT"):
                    columns = ["id", "alignment"][: len(parts)]
                elif header_check in ("DATASET_PLACEMENT", "PLACEMENT"):
                    columns = ["id", "position", "count", "label", "color"][: len(parts)]
                elif header_check in ("DATASET_TIMESCALE", "TIMESCALE"):
                    columns = ["time_point", "label"][: len(parts)]
                elif header_check in ("DATASET_MEME", "MEME"):
                    columns = ["id", "start", "end", "name"][: len(parts)]
                elif header_check in ("DATASET_MANUAL", "MANUAL"):
                    columns = ["id"] + [f"field_{i}" for i in range(1, len(parts))]
                elif header_check in ("DATASET_STYLE", "STYLE"):
                    columns = ["id", "type", "color", "style"][: len(parts)]
                elif header_check == "RANGE":
                    columns = ["id", "label", "color"][: len(parts)]
                current_dataset["columns"] = columns

            if columns and len(parts) >= len(columns):
                row = {}
                for i, col in enumerate(columns):
                    row[col] = parts[i] if i < len(parts) else ""
                current_dataset["data"].append(row)
            else:
                # Row has fewer fields than the inferred column count: it cannot
                # be mapped reliably, so skip it and warn instead of dropping it
                # silently (see code-review 2.5 learner.py:415).
                logger.warning("数据行字段不足，已跳过: %r", line)
            continue

        # Parameter lines use the dataset separator (same as DATA lines);
        # no longer hard-coded TAB.  The SEPARATOR line itself was already
        # split on whitespace above, so it is unaffected here.
        parts = stripped.split(sep, 1)
        if len(parts) == 2:
            key, value = parts
            current_dataset["parameters"][key] = value
        elif len(parts) == 1:
            current_dataset["parameters"][parts[0]] = ""

    if current_dataset:
        datasets.append(current_dataset)

    # Post-process each dataset to extract structured themes
    for ds in datasets:
        ds["profile"] = learn_profile(ds["parameters"])
        ds["field"] = learn_field(ds["parameters"], ds["separator"])
        ds["common_themes"] = learn_common_themes(ds["parameters"])
        ds["specific_themes"] = learn_specific_themes(ds["parameters"], ds["header"])

    return {
        "template_name": template_name,
        "datasets": datasets,
    }


def train_theme(template_dir: str, min_freq: float = 0.5) -> dict:
    """Train a theme by learning from multiple template files in a directory.

    Iterates through all template files in the given directory, parses each
    one using :func:`learn_template`, and aggregates statistics across
    dataset types. The result is a JSON-serializable theme configuration
    containing recommended default parameters, field distributions, and
    color distributions per dataset type.

    Args:
        template_dir: Path to the directory containing iTOL template files.
            All files with a ``.txt`` extension are processed.
        min_freq: Minimum frequency threshold (0.0–1.0) for a parameter
            value to be included in the recommended defaults.

    Returns:
        A dictionary with the following top-level keys:

        - ``summary``: overall counts (``total_files``, ``total_datasets``,
          ``type_counts``).
        - ``themes``: per-dataset-type aggregated data. Each key is a dataset
          type (e.g. ``dataset_colorstrip``) and contains:

          - ``count``: number of occurrences.
          - ``recommended_defaults``: most common parameter values whose
            frequency meets ``min_freq``.
          - ``parameter_frequencies``: raw frequency tables for every
            parameter.
          - ``field_distribution``: counts of field labels / colors / shapes.
          - ``color_distribution``: most frequently used colors.

    Example:
        >>> theme = train_theme("./iTOL_templates")
        >>> json.dumps(theme, indent=2)
    """
    path = Path(template_dir)
    if not path.is_dir():
        raise NotADirectoryError(f"Not a directory: {template_dir}")

    template_files = sorted(path.glob("*.txt"))
    if not template_files:
        return {"summary": {"total_files": 0, "total_datasets": 0, "type_counts": {}}, "themes": {}}

    type_stats: dict[str, dict] = defaultdict(
        lambda: {
            "dataset_count": 0,
            "parameters": defaultdict(list),
            "field_labels_len": [],
            "field_colors_len": [],
            "field_shapes_len": [],
            "colors": [],
        }
    )
    total_datasets = 0

    for tf in template_files:
        try:
            parsed = learn_template(str(tf))
        except (OSError, UnicodeDecodeError, ValueError) as e:
            # Log specific errors instead of silently swallowing all exceptions
            logger.warning("Skipping template file %s: %s", tf, e)
            continue
        except Exception as e:
            # Log unexpected errors with more detail
            logger.warning("Unexpected error parsing template file %s: %s", tf, e)
            continue
        for ds in parsed.get("datasets", []):
            ds_type = ds.get("type", "unknown")
            total_datasets += 1
            stats = type_stats[ds_type]
            stats["dataset_count"] += 1

            # Collect raw parameter values
            for key, value in ds.get("parameters", {}).items():
                stats["parameters"][key].append(value)

            # Collect field metadata
            field = ds.get("field", {})
            if "labels" in field:
                stats["field_labels_len"].append(len(field["labels"]))
            if "colors" in field:
                stats["field_colors_len"].append(len(field["colors"]))
                stats["colors"].extend(field["colors"])
            if "shapes" in field:
                stats["field_shapes_len"].append(len(field["shapes"]))

            # Collect profile color
            profile = ds.get("profile", {})
            color = profile.get("color", "")
            if color:
                stats["colors"].append(color)

    themes: dict[str, dict] = {}
    for ds_type, stats in type_stats.items():
        count = stats["dataset_count"]

        # Parameter frequencies and recommended defaults
        param_freqs: dict[str, dict[str, int]] = {}
        recommended: dict[str, str] = {}
        for key, values in stats["parameters"].items():
            if not values:  # pragma: no cover
                continue
            counter = Counter(values)
            param_freqs[key] = dict(counter.most_common())
            most_common_val, most_common_count = counter.most_common(1)[0]
            freq = most_common_count / len(values)
            if freq >= min_freq:
                recommended[key] = most_common_val

        # Field distribution
        field_dist: dict[str, dict[str, float | int]] = {}
        for field_name in ("field_labels_len", "field_colors_len", "field_shapes_len"):
            lengths = stats[field_name]
            if lengths:
                field_dist[field_name.replace("_len", "")] = {
                    "mean": round(sum(lengths) / len(lengths), 2),
                    "min": min(lengths),
                    "max": max(lengths),
                    "count": len(lengths),
                }

        # Color distribution (top 10)
        color_dist: list[dict[str, str | int]] = []
        if stats["colors"]:
            for color, ccount in Counter(stats["colors"]).most_common(10):
                color_dist.append({"color": color, "count": ccount})

        themes[ds_type] = {
            "count": count,
            "recommended_defaults": recommended,
            "parameter_frequencies": param_freqs,
            "field_distribution": field_dist,
            "color_distribution": color_dist,
        }

    return {
        "summary": {
            "total_files": len(template_files),
            "total_datasets": total_datasets,
            "type_counts": {t: s["count"] for t, s in themes.items()},
        },
        "themes": themes,
    }
