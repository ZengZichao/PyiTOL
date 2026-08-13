"""Color utility functions - conversion, gradients, sorting."""

from __future__ import annotations

import functools
import re
from typing import Any

from pyitol.utils.constants import NAMED_COLORS

# Default color palette used across the codebase (15 colors, designed for
# maximum perceptual distinction on white backgrounds).
DEFAULT_PALETTE: list[str] = [
    "#e64b35",
    "#b4d2e7",
    "#4dbbd5",
    "#00a087",
    "#3c5484",
    "#f39b7f",
    "#8491b4",
    "#91d1c2",
    "#7e6148",
    "#b2df8a",
    "#6baed6",
    "#fb9a99",
    "#cab2d6",
    "#ffff99",
    "#a6d854",
]
DEFAULT_PALETTE_TUPLE: tuple[str, ...] = tuple(DEFAULT_PALETTE)


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to hex color string."""
    return f"#{r:02x}{g:02x}{b:02x}"


def hsl_to_rgb(h: float, s: float, lum: float) -> tuple[int, int, int]:
    """Convert HSL (0-360, 0-100, 0-100) to RGB (0-255).

    m5: Renamed parameter 'l' to 'lum' to avoid shadowing built-in and visual confusion.
    """
    s /= 100.0
    lum /= 100.0

    c = (1 - abs(2 * lum - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = lum - c / 2

    if 0 <= h < 60:
        r1, g1, b1 = c, x, 0.0
    elif 60 <= h < 120:
        r1, g1, b1 = x, c, 0.0
    elif 120 <= h < 180:
        r1, g1, b1 = 0.0, c, x
    elif 180 <= h < 240:
        r1, g1, b1 = 0.0, x, c
    elif 240 <= h < 300:
        r1, g1, b1 = x, 0.0, c
    else:
        r1, g1, b1 = c, 0.0, x

    return (int((r1 + m) * 255), int((g1 + m) * 255), int((b1 + m) * 255))


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[float, float, float]:
    """Convert RGB (0-255) to HSL (0-360, 0-100, 0-100)."""
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    cmax = max(rf, gf, bf)
    cmin = min(rf, gf, bf)
    lum = (cmax + cmin) / 2

    if cmax == cmin:
        h = s = 0.0
    else:
        d = cmax - cmin
        s = d / (2 - cmax - cmin) if lum > 0.5 else d / (cmax + cmin)
        if cmax == rf:
            h = ((gf - bf) / d + (6 if gf < bf else 0)) * 60
        elif cmax == gf:
            h = ((bf - rf) / d + 2) * 60
        else:
            h = ((rf - gf) / d + 4) * 60

    return (h, s * 100, lum * 100)


def generate_gradient_colors(start: str, end: str, n: int) -> list[str]:
    """Generate n gradient colors between start and end hex colors."""
    r1, g1, b1 = hex_to_rgb(start)
    r2, g2, b2 = hex_to_rgb(end)

    colors = []
    for i in range(n):
        t = i / (n - 1) if n > 1 else 0
        r = int(r1 + (r2 - r1) * t)
        g = int(g1 + (g2 - g1) * t)
        b = int(b1 + (b2 - b1) * t)
        colors.append(rgb_to_hex(r, g, b))
    return colors


def darken_color(hex_color: str, factor: float = 0.8) -> str:
    """Darken a color by multiplying RGB values by factor."""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex(r, g, b)


def lighten_color(hex_color: str, factor: float = 0.2) -> str:
    """Lighten a color by adding factor to each RGB channel."""
    r, g, b = hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return rgb_to_hex(r, g, b)


def color_distance(color1: str, color2: str, method: str = "euclidean") -> float:
    """Calculate distance between two colors.

    Args:
        color1: First hex color.
        color2: Second hex color.
        method: Distance metric - 'euclidean' (default) or 'manhattan'.

    Returns:
        Distance value (non-negative).
    """
    r1, g1, b1 = hex_to_rgb(color1)
    r2, g2, b2 = hex_to_rgb(color2)

    if method == "euclidean":
        return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5
    elif method == "manhattan":
        return abs(r1 - r2) + abs(g1 - g2) + abs(b1 - b2)
    else:
        raise ValueError(f"Unsupported distance method: {method}. Use 'euclidean' or 'manhattan'.")


def sort_colors_by_similarity(colors: list[str], reference: str | None = None) -> list[str]:
    """Sort colors so similar colors are adjacent.

    Provides similar functionality to itol.toolkit's sort_color(), but uses a
    different algorithm: this implementation employs a greedy nearest-neighbor
    chaining approach, while itol.toolkit uses hierarchical clustering (hclust
    with complete linkage). Both aim to place similar colors adjacent to each
    other.
    """
    if len(colors) <= 1:
        return colors

    if reference is None:
        reference = colors[0]

    remaining = list(colors)
    if reference in remaining:
        remaining.remove(reference)
    else:
        remaining = colors[:]
        reference = remaining.pop(0)

    sorted_colors = [reference]

    while remaining:
        last_color = sorted_colors[-1]
        distances = []
        for c in remaining:
            d = color_distance(last_color, c, method="euclidean")
            distances.append((d, c))

        distances.sort()
        sorted_colors.append(distances[0][1])
        remaining.remove(distances[0][1])

    return sorted_colors


def sort_color(colors: list[str], reference: str | None = None, method: str = "euclidean") -> list[str]:
    """Sort colors by similarity - alias for sort_colors_by_similarity.

    Function name kept for familiarity with itol.toolkit's sort_color();
    the underlying algorithm differs (see sort_colors_by_similarity docstring).
    """
    return sort_colors_by_similarity(colors, reference=reference)


def assign_colors_to_categories(categories: list[str], palette: list[str] | None = None) -> dict[str, str]:
    """Assign colors from palette to categories. Cycles if more categories than colors."""
    if palette is None:
        palette = DEFAULT_PALETTE
    return _assign_colors_to_categories_cached(tuple(categories), tuple(palette) if palette else None)


@functools.lru_cache(maxsize=256)
def _assign_colors_to_categories_cached(
    categories: tuple[str, ...],
    palette: tuple[str, ...] | None = None,
) -> dict[str, str]:
    """Cached color assignment (uses tuples for hashability)."""
    if palette is None:
        palette = DEFAULT_PALETTE_TUPLE
    return {cat: palette[i % len(palette)] for i, cat in enumerate(categories)}


def _assign_colors(df: Any, column: str, color_dict: dict[str, str] | None = None) -> dict[str, str]:
    """Assign colors to unique values in a DataFrame column.

    This is the canonical implementation used across the codebase
    (cli, templates, etc.) to ensure consistent color assignment.
    """
    if color_dict:
        return color_dict
    unique_vals = sorted(df[column].dropna().unique())
    return assign_colors_to_categories(unique_vals)


def validate_color(color: str) -> bool:
    """Validate a color string (hex, named, rgb).

    This is a lightweight check. For detailed error messages, use
    pyitol.core.validator.validate_color_code() instead.
    """
    if re.match(r"^#[0-9a-fA-F]{6}$", color):
        return True
    if re.match(r"^#[0-9a-fA-F]{3}$", color):
        return True
    if re.match(r"^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$", color, re.IGNORECASE):
        return True
    if re.match(r"^rgba\(", color, re.IGNORECASE):
        return True
    if re.match(r"^hsl\(", color, re.IGNORECASE):
        return True
    # P1-17: Check named colors. The color name table is defined in
    # pyitol.utils.constants to avoid a reverse dependency on pyitol.core.
    return color.lower() in NAMED_COLORS
