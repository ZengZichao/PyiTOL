#!/usr/bin/env python3
"""
Generate All iTOL Template Types.

This script programmatically generates one example file for every
template / dataset type supported by PyiTOL (30+ types). It serves as:
  1. A comprehensive compatibility test for the TemplateGenerator engine
  2. A reference collection of iTOL v7 template syntax
  3. A starting point for customizing your own templates

Output files are written to outputs/all_types/.

Data source: examples/data/synthetic_32tips.nwk + _enriched.csv (real strain
names like 'strain_001' so generated templates match the tree's tip labels).
"""

import sys
from pathlib import Path

import dendropy
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.templates.generator import (
    generate_color_strip_template,
    generate_simple_bar_template,
    generate_multibar_template,
    generate_heatmap_template,
    generate_symbols_template,
    generate_pie_template,
    generate_boxplot_template,
    generate_gradient_template,
    generate_connection_template,
    generate_domain_template,
    generate_text_template,
    generate_external_shape_template,
    generate_linechart_template,
    generate_image_template,
    generate_alignment_template,
    generate_tanglegram_template,
    generate_placement_template,
    generate_timescale_template,
    generate_meme_template,
    generate_arrow_template,
    generate_binary_template,
    generate_collapse_template,
    generate_prune_template,
    generate_spacing_template,
    generate_labels_template,
    generate_popup_info_template,
    generate_tree_colors_template,
    generate_ranges_template,
    generate_style_template,
    generate_branch_template,
    generate_manual_template,
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
TAXONOMY_FILE = str(DATA_DIR / "synthetic_32tips_enriched.csv")
OUTPUT_DIR = Path(__file__).parent / "outputs" / "all_types"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Real tip names from the synthetic tree (avoids templates that reference
# non-existent tips like 'tipA'/'tipB'). Pull dynamically so the script
# stays correct if the tree changes.
_tree = dendropy.Tree.get_from_path(TREE_FILE, schema="newick", preserve_underscores=True)
TIPS = [t.taxon.label for t in _tree.leaf_nodes() if t.taxon]
TIP_A, TIP_B, TIP_C, TIP_D = TIPS[0], TIPS[1], TIPS[2], TIPS[3]


def main():
    generated = []

    # Datasets requiring taxonomy + tree.
    # The enriched CSV columns are: id,Phylum,Class,Order,Family,Genus,GC,Size,Genes
    generate_color_strip_template(OUTPUT_DIR / "color_strip.txt", TAXONOMY_FILE, TREE_FILE, "Phylum")
    generated.append("color_strip")

    generate_simple_bar_template(OUTPUT_DIR / "simple_bar.txt", TAXONOMY_FILE, TREE_FILE, "Size")
    generated.append("simple_bar")

    generate_multibar_template(OUTPUT_DIR / "multibar.txt", TAXONOMY_FILE, TREE_FILE, ["Size", "GC"])
    generated.append("multibar")

    generate_heatmap_template(OUTPUT_DIR / "heatmap.txt", TAXONOMY_FILE, TREE_FILE, ["Size", "GC", "Genes"])
    generated.append("heatmap")

    generate_symbols_template(OUTPUT_DIR / "symbols.txt", TAXONOMY_FILE, TREE_FILE, "Phylum")
    generated.append("symbols")

    generate_gradient_template(OUTPUT_DIR / "gradient.txt", TAXONOMY_FILE, TREE_FILE, "GC")
    generated.append("gradient")

    generate_text_template(OUTPUT_DIR / "text.txt", TAXONOMY_FILE, TREE_FILE, "Genus")
    generated.append("text")

    generate_external_shape_template(OUTPUT_DIR / "external_shape.txt", TAXONOMY_FILE, TREE_FILE, "Phylum")
    generated.append("external_shape")

    generate_tree_colors_template(
        OUTPUT_DIR / "tree_colors.txt",
        [{"id": TIP_A, "type": "clade", "color": "#e64b35"}],
    )
    generated.append("tree_colors")

    generate_ranges_template(
        OUTPUT_DIR / "ranges.txt",
        [{"id": TIP_A, "label": "Group1", "color": "#4dbbd5"}],
    )
    generated.append("ranges")

    generate_style_template(
        OUTPUT_DIR / "style.txt",
        [{"id": TIP_A, "type": "label_background", "color": "#00a087"}],
    )
    generated.append("style")

    generate_branch_template(OUTPUT_DIR / "branch.txt", TAXONOMY_FILE, TREE_FILE, "Phylum")
    generated.append("branch")

    # Datasets with special data structures
    generate_pie_template(OUTPUT_DIR / "pie.txt", TAXONOMY_FILE, TREE_FILE, ["Size", "GC"])
    generated.append("pie")

    generate_binary_template(
        OUTPUT_DIR / "binary.txt",
        [{"id": TIP_A, "col1": "1", "col2": "0"}, {"id": TIP_B, "col1": "0", "col2": "1"}],
        ["col1", "col2"],
        ["#e64b35", "#4dbbd5"],
        ["1", "2"],
    )
    generated.append("binary")

    generate_connection_template(
        OUTPUT_DIR / "connections.txt",
        [(TIP_A, TIP_B), (TIP_C, TIP_D)],
    )
    generated.append("connections")

    generate_domain_template(
        OUTPUT_DIR / "domains.txt",
        [{"id": TIP_A, "from": "10", "to": "50", "type": "domain", "color": "#ff00aa"}],
    )
    generated.append("domains")

    generate_linechart_template(
        OUTPUT_DIR / "linechart.txt",
        [{"id": TIP_A, "position": "1", "value": "0.5"}, {"id": TIP_A, "position": "2", "value": "0.8"}],
    )
    generated.append("linechart")

    generate_image_template(
        OUTPUT_DIR / "images.txt",
        [{"id": TIP_A, "image_file": "img.png", "image_url": "http://example.com/img.png"}],
    )
    generated.append("images")

    generate_alignment_template(
        OUTPUT_DIR / "alignment.txt",
        [{"id": TIP_A, "alignment": "ATCG"}, {"id": TIP_B, "alignment": "GCTA"}],
    )
    generated.append("alignment")

    generate_tanglegram_template(
        OUTPUT_DIR / "tanglegram.txt",
        [(TIP_A, TIP_B), (TIP_C, TIP_D)],
    )
    generated.append("tanglegram")

    generate_placement_template(
        OUTPUT_DIR / "placement.txt",
        [{"id": TIP_A, "position": "100", "count": "5", "color": "#ff0000"}],
    )
    generated.append("placement")

    generate_timescale_template(
        OUTPUT_DIR / "timescale.txt",
        [{"time_point": "0", "label": "Present", "color": "#000000"}],
    )
    generated.append("timescale")

    generate_meme_template(
        OUTPUT_DIR / "meme.txt",
        [{"id": TIP_A, "start": "10", "end": "20", "name": "motif1", "color": "#ff0000"}],
    )
    generated.append("meme")

    generate_arrow_template(
        OUTPUT_DIR / "arrows.txt",
        [{"id": TIP_A, "position": "100", "direction": "right", "color": "#ff0000"}],
    )
    generated.append("arrows")

    generate_collapse_template(OUTPUT_DIR / "collapse.txt", [TIP_A, TIP_B])
    generated.append("collapse")

    generate_prune_template(OUTPUT_DIR / "prune.txt", [TIP_A])
    generated.append("prune")

    generate_spacing_template(OUTPUT_DIR / "spacing.txt", [{"id": TIP_A, "factor": "2"}])
    generated.append("spacing")

    generate_labels_template(OUTPUT_DIR / "labels.txt", [{"id": TIP_A, "label": "Species_A"}])
    generated.append("labels")

    generate_popup_info_template(
        OUTPUT_DIR / "popup_info.txt",
        [{"id": TIP_A, "title": "Info", "content": "Details"}],
    )
    generated.append("popup_info")

    generate_manual_template(OUTPUT_DIR / "manual.txt", [{"id": TIP_A, "label": "manual data"}])
    generated.append("manual")

    # Boxplot requires specific columns; build a minimal data frame with real tip IDs.
    bp_df = pd.DataFrame({
        "id": [TIP_A, TIP_B, TIP_C, TIP_D],
        "minimum": [1, 2, 1.5, 0.5],
        "q1": [2, 3, 2.5, 1.5],
        "median": [3, 4, 3.5, 2.5],
        "q3": [4, 5, 4.5, 3.5],
        "maximum": [5, 6, 5.5, 4.5],
    })
    bp_path = OUTPUT_DIR / "boxplot_data.tsv"
    bp_df.to_csv(bp_path, sep="\t", index=False)
    generate_boxplot_template(OUTPUT_DIR / "boxplot.txt", str(bp_path), TREE_FILE)
    generated.append("boxplot")

    print(f"Generated {len(generated)} template types in {OUTPUT_DIR}:")
    for name in generated:
        print(f"  - {name}.txt")


if __name__ == "__main__":
    main()
