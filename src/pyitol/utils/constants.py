"""Shared module-level constants for PyiTOL.

Centralizes magic strings and default values that previously appeared as
hard-coded literals across the codebase (separator names, default colors,
default multi-field palettes).  Keeping them in one place makes behaviour
consistent and tuning happen in a single location.

保守范围 (Phase 3): 本阶段仅在范围内的模块 (``templates/generator``、
``cli/taxonomy_cmd``) 引用这些常量; 其余调用点的字面量保留, 以规避跨文件
回归风险 (见 code-review 2.4 / 2.5 的 Low 级建议 "不要为统一而做跨 20 文件
破坏性重命名")。
"""

from __future__ import annotations

# Separator names accepted by iTOL templates / CLI ``--separator`` options.
DEFAULT_SEPARATOR: str = "TAB"

# Commonly reused default colors (HEX).
DEFAULT_PRIMARY_COLOR: str = "#ff0000"  # 默认强调/分支/标签色
DEFAULT_MISSING_COLOR: str = "#999999"  # 类别映射缺失时的回退色
DEFAULT_BORDER_COLOR: str = "#000000"  # 边框/标签默认色
DEFAULT_CONNECTION_COLOR: str = "#e64b35"  # 连接注释默认色

# Default multi-field palettes.
PRIMARY_RGB_PALETTE: list[str] = ["#ff0000", "#00ff00", "#0000ff"]  # binary / multi-field 回退
DEFAULT_HEATMAP_GRADIENT: list[str] = ["#ff0000", "#ffffff", "#0000ff"]  # 热图默认渐变

# Named colors supported by iTOL (comprehensive CSS named colors subset).
# Defined here (instead of pyitol.core.validator) so that pyitol.utils does not
# need to import from pyitol.core, avoiding a reverse dependency.
# m5: Extended with more CSS named colors to reduce false validation failures.
NAMED_COLORS: frozenset[str] = frozenset(
    {
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
)
