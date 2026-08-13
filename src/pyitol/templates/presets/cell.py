"""Cell journal color palettes for iTOL visualizations."""

from __future__ import annotations

CELL_PALETTES = {
    "classic": [
        "#1F77B4",
        "#FF7F0E",
        "#2CA02C",
        "#D62728",
        "#9467BD",
        "#8C564B",
        "#E377C2",
        "#7F7F7F",
        "#BCBD22",
        "#17BECF",
    ],
    "deep": [
        "#4C78A8",
        "#F58518",
        "#E45756",
        "#72B7B2",
        "#54A24B",
        "#EECA3B",
        "#B279A2",
        "#FF9DA6",
        "#9D7660",
        "#BAB0AC",
    ],
    "bright": [
        "#E63946",
        "#F4A261",
        "#E9C46A",
        "#2A9D8F",
        "#264653",
        "#FF6B6B",
        "#4ECDC4",
        "#45B7D1",
        "#96CEB4",
        "#FFEAA7",
    ],
    "dark": [
        "#1D3557",
        "#457B9D",
        "#A8DADC",
        "#E63946",
        "#F1FAEE",
        "#6D6875",
        "#B5838D",
        "#E5989B",
        "#FFB4A2",
        "#FFCDB2",
    ],
    "material": [
        "#E53935",
        "#D81B60",
        "#8E24AA",
        "#5E35B1",
        "#3949AB",
        "#1E88E5",
        "#039BE5",
        "#00ACC1",
        "#00897B",
        "#43A047",
        "#7CB342",
        "#C0CA33",
        "#FDD835",
        "#FFB300",
        "#FB8C00",
        "#F4511E",
        "#6D4C41",
        "#757575",
        "#546E7A",
        "#78909C",
    ],
}


def get_cell_palette(name: str = "classic", n: int | None = None) -> list[str]:
    """Get a Cell-style color palette.

    Args:
        name: Palette name (classic/deep/bright/dark/material)
        n: Number of colors needed (will cycle if n > palette length)
    """
    palette = CELL_PALETTES.get(name, CELL_PALETTES["classic"])
    if n is None:
        return palette.copy()
    return [palette[i % len(palette)] for i in range(n)]


def list_cell_palettes() -> list[str]:
    """List available Cell palette names."""
    return list(CELL_PALETTES.keys())
