#!/usr/bin/env python3
"""
Publication-Quality Figure Workflow.

This example demonstrates a complete academic-journal figure pipeline:
  1. Load taxonomy metadata and a phylogenetic tree
  2. Generate three complementary dataset templates:
       - Color strip (phylum-level taxonomy)
       - Heatmap (genomic features: Size, GC, Genes)
       - Simple bar (genome size)
  3. Apply a Nature-journal color palette
  4. Upload all datasets together
  5. Poll until rendering is ready, then export at 300 DPI in both
     PDF and PNG formats

This produces a multi-layer figure suitable for high-impact journals.
"""

import sys
import time
from pathlib import Path

import dendropy
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.api.client import ITOLAPIClient
from pyitol.templates.generator import (
    generate_color_strip_template,
    generate_heatmap_template,
    generate_simple_bar_template,
)
from pyitol.templates.presets import get_palette
from pyitol.exceptions import APIKeyError

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
TAXONOMY_FILE = str(DATA_DIR / "synthetic_32tips_enriched.csv")
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_NAME = "PyiTOL_Publication_Figure"


def _wait_until_ready(client, tree_id: str, max_wait: int = 120) -> None:
    """Poll iTOL rendering status until ready or timeout (replaces fixed sleep)."""
    elapsed = 0
    interval = 10
    while elapsed < max_wait:
        status = client.query_status(tree_id)
        if status.get("status") == "ready":
            print(f"  Tree ready after {elapsed}s")
            return
        print(f"  Waiting for rendering... ({elapsed}s elapsed, status={status.get('status')})")
        time.sleep(interval)
        elapsed += interval
    print(f"  Polling timeout after {elapsed}s; attempting export anyway")


def main():
    for f in [TREE_FILE, TAXONOMY_FILE]:
        if not Path(f).exists():
            print(f"Error: File not found: {f}")
            sys.exit(1)

    # Load data to filter rows whose IDs are present in the tree.
    tree = dendropy.Tree.get_from_path(TREE_FILE, schema="newick", preserve_underscores=True)
    tip_set = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}
    df = pd.read_csv(TAXONOMY_FILE, sep=None, engine="python", dtype=str)
    df = df[df["id"].isin(tip_set)]

    # Nature palette
    palette = get_palette("nature", "primary", n=8)
    print(f"Using Nature primary palette: {palette[:4]}...")

    # 1. Color strip - Phylum (use the generator function for correctness)
    cs_path = OUTPUT_DIR / "pub_colorstrip.txt"
    phylum_colors = {
        "Phylum_01": palette[0],
        "Phylum_02": palette[1],
        "Phylum_03": palette[2],
    }
    generate_color_strip_template(
        cs_path, TAXONOMY_FILE, TREE_FILE, "Phylum",
        label="Phylum", colors=phylum_colors, strip_width="50",
    )

    # 2. Simple bar - genome size (Size column in the enriched CSV)
    bar_path = OUTPUT_DIR / "pub_simple_bar.txt"
    generate_simple_bar_template(
        bar_path, TAXONOMY_FILE, TREE_FILE, "Size",
        label="Genome Size (Mb)", bar_color=palette[3], bar_width="50",
    )

    # 3. Heatmap - Size + GC + Genes
    hm_path = OUTPUT_DIR / "pub_heatmap.txt"
    generate_heatmap_template(
        hm_path, TAXONOMY_FILE, TREE_FILE, ["Size", "GC", "Genes"],
        label="Genomic Features",
    )

    paths = [cs_path, bar_path, hm_path]
    print(f"Generated {len(paths)} templates:")
    for p in paths:
        print(f"  {p.name}")

    # Upload and export
    try:
        client = ITOLAPIClient()
    except APIKeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        tree_id = client.upload(
            tree_file=TREE_FILE,
            template_files=[str(p) for p in paths],
            project_name=PROJECT_NAME,
        )
        print(f"Uploaded: {tree_id}")

        _wait_until_ready(client, tree_id, max_wait=120)

        # Note: the API uses fmt= (not format=) to avoid shadowing the built-in.
        for fmt, dpi in [("pdf", 300), ("png", 300)]:
            print(f"Exporting {fmt.upper()} @ {dpi} DPI...")
            results = client.export([tree_id], fmt=fmt, dpi=dpi)
            src = results[tree_id]
            dst = OUTPUT_DIR / f"publication_figure.{fmt}"
            src.rename(dst)
            print(f"  Saved: {dst}")

    except Exception as e:
        print(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
