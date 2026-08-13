"""Nature journal color palettes for iTOL visualizations."""

from __future__ import annotations

NATURE_PALETTES = {
    "primary": [
        "#0F2080",
        "#F5793A",
        "#85C0F9",
        "#A95AA1",
        "#D55E00",
        "#CC79A7",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
    ],
    "pastel": [
        "#8DD3C7",
        "#FFFFB3",
        "#BEBADA",
        "#FB8072",
        "#80B1D3",
        "#FDB462",
        "#B3DE69",
        "#FCCDE5",
        "#D9D9D9",
        "#BC80BD",
    ],
    "vibrant": [
        "#E41A1C",
        "#377EB8",
        "#4DAF4A",
        "#984EA3",
        "#FF7F00",
        "#FFFF33",
        "#A65628",
        "#F781BF",
        "#999999",
        "#66C2A5",
    ],
    "muted": [
        "#332288",
        "#88CCEE",
        "#44AA99",
        "#117733",
        "#999933",
        "#DDCC77",
        "#CC6677",
        "#882255",
        "#AA4499",
        "#661100",
    ],
    "accessible": [
        "#000000",
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
        "#999999",
        "#FFFFFF",
    ],
}


def get_nature_palette(name: str = "primary", n: int | None = None) -> list[str]:
    """Get a Nature-style color palette.

    Args:
        name: Palette name (primary/pastel/vibrant/muted/accessible)
        n: Number of colors needed (will cycle if n > palette length)
    """
    palette = NATURE_PALETTES.get(name, NATURE_PALETTES["primary"])
    if n is None:
        return palette.copy()
    return [palette[i % len(palette)] for i in range(n)]


def list_nature_palettes() -> list[str]:
    """List available Nature palette names."""
    return list(NATURE_PALETTES.keys())
