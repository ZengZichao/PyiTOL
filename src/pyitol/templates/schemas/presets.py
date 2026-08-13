"""Preset color schemes - Nature, Cell, colorblind, etc."""

import warnings as _warnings

PRESET_SCHEMES = {
    "nature": {
        "colors": [
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
        "description": "Nature journal standard colors",
    },
    "cell": {
        "colors": [
            "#ff7f00",
            "#377eb8",
            "#4daf4a",
            "#984ea3",
            "#e41a1c",
            "#a65628",
            "#f781bf",
            "#999999",
            "#ffff33",
            "#66c2a5",
        ],
        "description": "Cell journal standard colors",
    },
    "colorblind": {
        "colors": ["#000000", "#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"],
        "description": "Colorblind-friendly palette (Okabe-Ito)",
    },
    "tableau": {
        "colors": [
            "#4E79A7",
            "#F28E2B",
            "#E15759",
            "#76B7B2",
            "#59A14F",
            "#EDC948",
            "#B07AA1",
            "#FF9DA7",
            "#9C755F",
            "#BAB0AC",
        ],
        "description": "Tableau standard colors",
    },
    "viridis": {
        "colors": [
            "#440154",
            "#482777",
            "#3f4a8a",
            "#31678e",
            "#26838f",
            "#1f9d8a",
            "#35b779",
            "#6ece58",
            "#a5db36",
            "#d8e219",
            "#fde725",
        ],
        "description": "Viridis colormap",
    },
    "set1": {
        "colors": ["#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#ffff33", "#a65628", "#f781bf", "#999999"],
        "description": "R ColorBrewer Set1",
    },
    "set2": {
        "colors": ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f", "#e5c494", "#b3b3b3"],
        "description": "R ColorBrewer Set2",
    },
    "set3": {
        "colors": [
            "#8dd3c7",
            "#ffffb3",
            "#bebada",
            "#fb8072",
            "#80b1d3",
            "#fdb462",
            "#b3de69",
            "#fccde5",
            "#d9d9d9",
            "#bc80bd",
            "#ccebc5",
            "#ffed6f",
        ],
        "description": "R ColorBrewer Set3",
    },
    "rainbow": {
        "colors": ["#e41a1c", "#ff7f00", "#ffff33", "#377eb8", "#4daf4a", "#984ea3", "#f781bf", "#a65628"],
        "description": "Rainbow palette",
    },
    "pastel": {
        "colors": [
            "#a6cee3",
            "#1f78b4",
            "#b2df8a",
            "#33a02c",
            "#fb9a99",
            "#e31a1c",
            "#fdbf6f",
            "#ff7f00",
            "#cab2d6",
            "#6a3d9a",
            "#ffff99",
            "#b15928",
        ],
        "description": "Pastel palette",
    },
    "taxonomy": {
        "colors": ["#e64b35", "#b4d2e7", "#4dbbd5", "#00a087", "#3c5484", "#f39b7f", "#999999"],
        "color_map": {
            "Bacteria": "#e64b35",
            "Archaea": "#b4d2e7",
            "Eukaryota": "#4dbbd5",
            "Viruses": "#00a087",
            "Fungi": "#3c5484",
            "Plantae": "#00a087",
            "Animalia": "#3c5484",
            "Protista": "#f39b7f",
            "uncultured": "#999999",
        },
        "description": "Standard taxonomy domain colors",
    },
}

# DEPRECATED: PRESET_STYLES is not used in production code and may be removed
# in a future version. It is retained only for backward compatibility with
# existing tests that reference it.
_warnings.warn(
    "PRESET_STYLES is deprecated and will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

PRESET_STYLES = {
    "minimal": {
        "tree_style": {
            "treeType": "normal",
            "normalTaxonomyLabelSize": "1",
            "normalLineWidth": "1",
            "hideNodeLabel": "1",
        },
        "description": "Minimal clean style",
    },
    "publication": {
        "tree_style": {
            "treeType": "normal",
            "normalTaxonomyLabelSize": "0.8",
            "normalLineWidth": "2",
            "normalBranchWidth": "2",
            "showInternalNodeLabel": "0",
            "datasetDisplay": "1",
        },
        "description": "Publication-ready style",
    },
    "detailed": {
        "tree_style": {
            "treeType": "normal",
            "normalTaxonomyLabelSize": "1.2",
            "normalLineWidth": "1",
            "showInternalNodeLabel": "1",
            "datasetDisplay": "1",
            "showTreeRuler": "1",
        },
        "description": "Detailed view with all annotations",
    },
    "compact": {
        "tree_style": {
            "treeType": "circular",
            "normalTaxonomyLabelSize": "0.5",
            "normalLineWidth": "0.5",
            "hideNodeLabel": "0",
        },
        "description": "Compact circular layout for large trees",
    },
}
