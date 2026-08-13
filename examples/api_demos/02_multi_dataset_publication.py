#!/usr/bin/env python3
"""
Publication-Quality Multi-Dataset Upload Demo.

This example demonstrates how to upload a tree together with multiple
visualization datasets (color strip, heatmap, simple bar) and export with
journal-grade parameters:
  - 300 DPI resolution (suitable for print)
  - Colorblind-friendly palette (Tol Bright)
  - Proper English project name and dataset labels
  - PDF output for vector graphics

This workflow mirrors a typical phylogenomic figure for academic journals
such as Nature, Cell, or ISME J.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.api.client import ITOLAPIClient
from pyitol.templates.generator import generate_color_strip_template
from pyitol.templates.presets import get_palette
from pyitol.exceptions import APIKeyError

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
TAXONOMY_FILE = str(DATA_DIR / "synthetic_32tips_enriched.csv")
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_NAME = "PyiTOL_Publication_Demo"


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

    try:
        client = ITOLAPIClient()
    except APIKeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # -----------------------------------------------------------------------
    # Step 1: Generate a color-strip template programmatically with a
    #         colorblind-friendly palette. The enriched CSV has a "Phylum"
    #         column (capitalized) and numeric columns "Size" / "GC" / "Genes".
    # -----------------------------------------------------------------------
    palette = get_palette("colorblind", "tol_bright", n=5)
    print(f"Using colorblind-friendly palette: {palette[:3]}...")

    cs_path = OUTPUT_DIR / "colorstrip.txt"
    generate_color_strip_template(
        cs_path, TAXONOMY_FILE, TREE_FILE, "Phylum",
        label="Phylum",
        colors={"Phylum_01": palette[0], "Phylum_02": palette[1]},
    )
    templates = [str(cs_path)]

    # -----------------------------------------------------------------------
    # Step 2: Upload tree + templates, poll for readiness, then export.
    #         Note: the API uses fmt= (not format=) to avoid shadowing the
    #         built-in.
    # -----------------------------------------------------------------------
    print(f"Uploading tree + {len(templates)} template(s)...")
    try:
        tree_id = client.upload(
            tree_file=TREE_FILE,
            template_files=templates,
            project_name=PROJECT_NAME,
        )
        print(f"Upload successful: {tree_id}")

        _wait_until_ready(client, tree_id, max_wait=120)

        # Export PDF at 300 DPI for journal quality
        results = client.export([tree_id], fmt="pdf", dpi=300)
        pdf_path = results[tree_id]
        target = OUTPUT_DIR / "publication_quality.pdf"
        pdf_path.rename(target)
        print(f"Exported 300-DPI PDF to: {target.resolve()}")

        # Also export SVG for vector editing
        results_svg = client.export([tree_id], fmt="svg")
        svg_path = results_svg[tree_id]
        target_svg = OUTPUT_DIR / "publication_quality.svg"
        svg_path.rename(target_svg)
        print(f"Exported SVG to: {target_svg.resolve()}")

    except Exception as e:
        print(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
