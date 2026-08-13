#!/usr/bin/env python3
"""Generate a synthetic large-scale phylogenetic case study for PyiTOL.

Produces:
    - A balanced binary Newick tree with a configurable number of leaves
    - A hierarchical taxonomy file (domain / phylum / class / order / family / genus)
    - A presence/absence functional trait matrix

The taxonomy is designed so that some genera are intentionally polyphyletic,
making the dataset useful for demonstrating PyiTOL's subgroup decomposition.
"""
from __future__ import annotations

import argparse
import csv
import math
import random
from pathlib import Path
from typing import Any

from _bench_utils import build_balanced_newick_str


def assign_hierarchical_taxa(n: int, rng: random.Random) -> list[dict[str, str]]:
    """Assign each leaf a 6-rank taxonomy with mostly monophyletic genera.

    Taxa are assigned in tree order so that nearby leaves share genus/family/order.
    A small number of labels are then intentionally reused on distant leaves to
    create realistic polyphyletic cases for subgroup decomposition.
    """
    domains = ["Domain_01"]
    phyla = [f"Phylum_{p:02d}" for p in range(8)]
    classes = [f"Class_{c:03d}" for c in range(24)]
    orders = [f"Order_{o:03d}" for o in range(72)]
    families = [f"Family_{f:04d}" for f in range(288)]
    genera = [f"Genus_{g:04d}" for g in range(600)]

    records: list[dict[str, str]] = []

    for i in range(n):
        # Assign taxa based on leaf index, creating contiguous blocks.
        genus_idx = min(i // 8, len(genera) - 1)
        family_idx = min(genus_idx // 2, len(families) - 1)
        order_idx = min(family_idx // 4, len(orders) - 1)
        class_idx = min(order_idx // 3, len(classes) - 1)
        phylum_idx = min(class_idx // 3, len(phyla) - 1)

        genus = genera[genus_idx]

        # Introduce a few deliberately polyphyletic genera by reusing labels
        # on distant leaves of the tree.
        if i % 4000 == 123:
            genus = "Genus_problematic_A"
        elif i % 4000 == 3123:
            genus = "Genus_problematic_A"
        elif i % 4000 == 456:
            genus = "Genus_problematic_B"
        elif i % 4000 == 3456:
            genus = "Genus_problematic_B"

        records.append({
            "id": f"genome_{i:06d}",
            "domain": domains[0],
            "phylum": phyla[phylum_idx],
            "class": classes[class_idx],
            "order": orders[order_idx],
            "family": families[family_idx],
            "genus": genus,
        })

    return records


def generate_traits(n: int, rng: random.Random, num_traits: int = 20) -> list[dict[str, Any]]:
    """Generate a sparse presence/absence trait matrix."""
    trait_names = [f"trait_{t:03d}" for t in range(num_traits)]
    rows: list[dict[str, Any]] = []
    for i in range(n):
        row: dict[str, Any] = {"id": f"genome_{i:06d}"}
        for t in trait_names:
            # Traits are correlated with leaf index to create clade-specific patterns.
            base_prob = 0.05 + 0.15 * ((i % 7) / 6.0)
            row[t] = 1 if rng.random() < base_prob else 0
        rows.append(row)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a synthetic large-scale case study.")
    parser.add_argument("--leaves", type=int, default=5_000, help="Number of tree leaves.")
    parser.add_argument("--prefix", type=str, default="synthetic", help="Output file prefix.")
    parser.add_argument("--outdir", type=Path, default=Path("examples/data"), help="Output directory.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)

    tree_path = args.outdir / f"{args.prefix}_{args.leaves}tips.nwk"
    taxonomy_path = args.outdir / f"{args.prefix}_{args.leaves}tips_taxonomy.csv"
    traits_path = args.outdir / f"{args.prefix}_{args.leaves}tips_traits.csv"

    newick = build_balanced_newick_str(args.leaves, prefix=args.prefix)
    tree_path.write_text(newick, encoding="utf-8")
    print(f"Tree written: {tree_path}")

    taxa = assign_hierarchical_taxa(args.leaves, rng)
    tax_fields = ["id", "domain", "phylum", "class", "order", "family", "genus"]
    with open(taxonomy_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=tax_fields)
        writer.writeheader()
        writer.writerows(taxa)
    print(f"Taxonomy written: {taxonomy_path}")

    traits = generate_traits(args.leaves, rng)
    trait_fields = ["id"] + [f"trait_{t:03d}" for t in range(20)]
    with open(traits_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=trait_fields)
        writer.writeheader()
        writer.writerows(traits)
    print(f"Traits written: {traits_path}")


if __name__ == "__main__":
    main()
