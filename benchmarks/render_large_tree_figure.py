#!/usr/bin/env python3
"""Render a publication-quality figure of a large phylogenetic tree.

Produces a circular cladogram colored by phylum, with an inset zoom highlighting a
polyphyletic genus and its PyiTOL-decomposed subgroups.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.is_dir():
    sys.path.insert(0, str(_SRC_DIR))

from dendropy import Tree


def parse_taxonomy(taxonomy_path: Path) -> dict[str, dict[str, str]]:
    mapping: dict[str, dict[str, str]] = {}
    with open(taxonomy_path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            mapping[row["id"]] = row
    return mapping


def compute_circular_cladogram(tree: Tree) -> tuple[dict[Any, tuple[float, float]], float]:
    """Compute (angle, radius) positions for every node in a circular cladogram.

    Root sits at the center and leaves are evenly spaced around the outer circle.
    Internal nodes are placed at the circular mean of their descendants and at a
    radius proportional to their topological depth from the root.
    """
    positions: dict[Any, tuple[float, float]] = {}

    # Assign angles to leaves.
    leaves = [n for n in tree.leaf_node_iter() if n.taxon]
    n_leaves = len(leaves)
    for idx, leaf in enumerate(leaves):
        positions[leaf] = (2.0 * math.pi * idx / n_leaves, 0.0)

    # Post-order traversal: internal node radius = max child radius + 1.
    for node in tree.postorder_internal_node_iter():
        children = node.child_nodes()
        if not children:
            continue
        child_radii = [positions[child][1] for child in children]
        radius = max(child_radii) + 1.0
        child_angles = [positions[child][0] for child in children]
        s = sum(math.sin(a) for a in child_angles)
        c = sum(math.cos(a) for a in child_angles)
        angle = math.atan2(s, c)
        positions[node] = (angle, radius)

    max_radius = max(r for _, r in positions.values())

    # Invert so root is at center and leaves are at the outer circle.
    for node, (angle, radius) in positions.items():
        positions[node] = (angle, max_radius - radius)

    return positions, max_radius


def draw_cladogram_edges(ax, tree: Tree, positions: dict[Any, tuple[float, float]], lw: float = 0.05):
    """Draw the tree edges of a circular cladogram."""
    for node in tree.postorder_internal_node_iter():
        p_angle, p_radius = positions[node]
        for child in node.child_nodes():
            c_angle, c_radius = positions[child]
            # Draw two segments: vertical (radial) from parent radius down to child
            # radius at parent angle, then arc to child angle at child radius.
            # For very small angular differences the arc is essentially a straight line.
            # We draw a polyline in polar coordinates for simplicity.
            if abs(c_angle - p_angle) > math.pi:
                # Wrap around the circle for the shorter arc.
                if c_angle > p_angle:
                    c_angle -= 2 * math.pi
                else:
                    c_angle += 2 * math.pi
            n_interp = max(2, int(abs(c_angle - p_angle) * 100))
            mid_angles = np.linspace(p_angle, c_angle, n_interp)
            # First radial segment at parent angle from parent radius to child radius.
            ax.plot([p_angle, p_angle], [p_radius, c_radius], "-", color="#333333", lw=lw)
            # Then angular arc at child radius.
            ax.plot(mid_angles, [c_radius] * n_interp, "-", color="#333333", lw=lw)


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a large tree figure.")
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--taxonomy", type=Path, required=True)
    parser.add_argument("--highlight-genus", type=str, default="Genus_problematic_A")
    parser.add_argument("--output", type=Path, default=Path("examples/data/synthetic_large_tree_figure.png"))
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    tree = Tree.get(path=str(args.tree), schema="newick", preserve_underscores=True)
    taxa = parse_taxonomy(args.taxonomy)
    positions, max_radius = compute_circular_cladogram(tree)

    # Phylum colors.
    phyla = sorted({row["phylum"] for row in taxa.values()})
    cmap = plt.cm.get_cmap("tab20", len(phyla))
    phylum_color = {p: matplotlib.colors.to_hex(cmap(i)) for i, p in enumerate(phyla)}

    leaf_angles = []
    leaf_radii = []
    leaf_colors = []
    for leaf in tree.leaf_node_iter():
        if not leaf.taxon:
            continue
        label = leaf.taxon.label
        angle, radius = positions[leaf]
        leaf_angles.append(angle)
        leaf_radii.append(radius)
        leaf_colors.append(phylum_color.get(taxa[label]["phylum"], "#888888"))

    highlight = {
        leaf_id for leaf_id, row in taxa.items()
        if row.get("genus") == args.highlight_genus and leaf_id in {n.taxon.label for n in tree.leaf_node_iter() if n.taxon}
    }

    fig = plt.figure(figsize=(10, 10), dpi=args.dpi)
    ax = fig.add_subplot(111, polar=True)

    draw_cladogram_edges(ax, tree, positions, lw=0.03)

    ax.scatter(
        leaf_angles,
        leaf_radii,
        c=leaf_colors,
        s=2.0,
        linewidths=0,
        zorder=3,
    )

    if highlight:
        h_angles = []
        h_radii = []
        for leaf in tree.leaf_node_iter():
            if leaf.taxon and leaf.taxon.label in highlight:
                angle, radius = positions[leaf]
                h_angles.append(angle)
                h_radii.append(radius)
        ax.scatter(
            h_angles,
            h_radii,
            facecolors="none",
            edgecolors="black",
            s=20,
            linewidths=0.4,
            zorder=4,
        )

    ax.set_ylim(0, max_radius * 1.02)
    ax.set_yticks([])
    ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title("Large-scale circular cladogram colored by phylum\n(polyphyletic genus highlighted)", fontsize=12, pad=20)

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    print(f"Figure saved to: {args.output}")


if __name__ == "__main__":
    main()
