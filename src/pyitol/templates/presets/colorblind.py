"""Colorblind-friendly palettes for iTOL visualizations.

Palette sources and references:
    - tol_bright, tol_vibrant, tol_muted, tol_light:
      Paul Tol's colour schemes (https://personal.sron.nl/~pault/)
    - ibm: IBM Design Library color blind safe palette
    - wong: Wong, B. (2011). Points of view: Color blindness.
      Nature Methods, 8(6), 441. doi:10.1038/nmeth.1618
    - okabeito: Okabe, M. & Ito, K. (2008). Color universal design.
      https://jfly.uni-koeln.de/color/
"""

from __future__ import annotations

COLORBLIND_PALETTES = {
    "tol_bright": [
        "#4477AA",
        "#EE6677",
        "#228833",
        "#CCBB44",
        "#66CCEE",
        "#AA3377",
        "#BBBBBB",
    ],
    "tol_vibrant": [
        "#EE7733",
        "#0077BB",
        "#33BBEE",
        "#EE3377",
        "#CC3311",
        "#009988",
        "#BBBBBB",
    ],
    "tol_muted": [
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
    "tol_light": [
        "#77AADD",
        "#EE8866",
        "#EEDD88",
        "#FFAABB",
        "#99DDFF",
        "#44BB99",
        "#BBCC33",
        "#AAAA00",
        "#DDDDDD",
    ],
    "ibm": [
        "#648FFF",
        "#785EF0",
        "#DC267F",
        "#FE6100",
        "#FFB000",
    ],
    "wong": [
        "#000000",
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
    ],
    "okabeito": [
        "#E69F00",
        "#56B4E9",
        "#009E73",
        "#F0E442",
        "#0072B2",
        "#D55E00",
        "#CC79A7",
        "#000000",
    ],
}


def get_colorblind_palette(name: str = "tol_bright", n: int | None = None) -> list[str]:
    """Get a colorblind-friendly palette.

    Args:
        name: Palette name (tol_bright/tol_vibrant/tol_muted/tol_light/ibm/wong/okabeito)
        n: Number of colors needed (will cycle if n > palette length)
    """
    palette = COLORBLIND_PALETTES.get(name, COLORBLIND_PALETTES["tol_bright"])
    if n is None:
        return palette.copy()
    return [palette[i % len(palette)] for i in range(n)]


def list_colorblind_palettes() -> list[str]:
    """List available colorblind-friendly palette names."""
    return list(COLORBLIND_PALETTES.keys())


def is_colorblind_friendly(colors: list[str]) -> bool:
    """Rough check if a color list is likely colorblind-friendly.

    This is a heuristic that checks for problematic red-green pairs.
    """
    from pyitol.utils.color_tools import hex_to_rgb

    rg_pairs = 0
    for i, c1 in enumerate(colors):
        for c2 in colors[i + 1 :]:
            r1, g1, _b1 = hex_to_rgb(c1)
            r2, g2, _b2 = hex_to_rgb(c2)
            # Check if one is strongly red and the other strongly green
            if (r1 > 180 and g1 < 100 and g2 > 150 and r2 < 120) or (r2 > 180 and g2 < 100 and g1 > 150 and r1 < 120):
                rg_pairs += 1
    return rg_pairs == 0
