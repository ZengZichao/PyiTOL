#!/usr/bin/env python3
"""
Batch Format Export Demo.

Uploads a single tree once, then exports it in all four supported formats
(PDF, SVG, PNG, TIFF) with appropriate settings for each use case:
  - PDF: 300 DPI, vector, ideal for print publication
  - SVG: Vector, ideal for Adobe Illustrator / Inkscape editing
  - PNG: 300 DPI, raster, ideal for web / PowerPoint
  - TIFF: 300 DPI, raster, ideal for journals requiring TIFF submission

This avoids re-uploading the tree for each format, saving time and
reducing server load.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.api.client import ITOLAPIClient
from pyitol.exceptions import APIKeyError

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_NAME = "PyiTOL_Batch_Export_Demo"


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
    if not Path(TREE_FILE).exists():
        print(f"Error: Tree file not found: {TREE_FILE}")
        sys.exit(1)

    try:
        client = ITOLAPIClient()
    except APIKeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    try:
        print("Uploading tree...")
        tree_id = client.upload(
            tree_file=TREE_FILE,
            template_files=[],
            project_name=PROJECT_NAME,
        )
        print(f"  Tree ID: {tree_id}")

        _wait_until_ready(client, tree_id, max_wait=120)

        # fmt -> export kwargs. Note the API uses fmt= (not format=) to avoid
        # shadowing the built-in.
        formats = {
            "pdf": {"dpi": 300},
            "svg": {},
            "png": {"dpi": 300},
            "tiff": {"dpi": 300},
        }

        for fmt, params in formats.items():
            print(f"Exporting {fmt.upper()}...")
            results = client.export([tree_id], fmt=fmt, **params)
            src = results[tree_id]
            dst = OUTPUT_DIR / f"batch_export.{fmt}"
            src.rename(dst)
            print(f"  Saved: {dst}")

        print("\nAll formats exported successfully.")

    except Exception as e:
        print(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
