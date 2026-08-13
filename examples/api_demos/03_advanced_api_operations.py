#!/usr/bin/env python3
"""
Advanced API Operations Demo.

Demonstrates the full lifecycle of tree management on iTOL:
  1. Upload a tree with force=True (overwrite existing)
  2. Query rendering status before export
  3. Export in multiple formats (PNG, TIFF)
  4. Batch delete uploaded trees

This is useful for automated pipelines that need to verify rendering
success and clean up temporary uploads.
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
PROJECT_NAME = "PyiTOL_Advanced_Demo"


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

    tree_ids = []

    try:
        # 1. Upload with force=True to allow overwrite
        print("Uploading tree (force=True)...")
        tree_id = client.upload(
            tree_file=TREE_FILE,
            template_files=[],
            force=True,
            project_name=PROJECT_NAME,
        )
        tree_ids.append(tree_id)
        print(f"  Uploaded: {tree_id}")

        # 2. Query status (informational)
        print("Querying rendering status...")
        status = client.query_status(tree_id)
        print(f"  Status: {status}")

        _wait_until_ready(client, tree_id, max_wait=120)

        # 3. Export PNG at 300 DPI (suitable for PowerPoint / posters).
        #    Note: the API uses fmt= (not format=) to avoid shadowing the built-in.
        print("Exporting PNG (300 DPI)...")
        results_png = client.export(tree_ids, fmt="png", dpi=300)
        png_path = results_png[tree_id]
        target_png = OUTPUT_DIR / "advanced_demo.png"
        png_path.rename(target_png)
        print(f"  PNG saved: {target_png}")

        # 4. Export TIFF (suitable for print with transparency)
        print("Exporting TIFF...")
        results_tiff = client.export(tree_ids, fmt="tiff", dpi=300)
        tiff_path = results_tiff[tree_id]
        target_tiff = OUTPUT_DIR / "advanced_demo.tiff"
        tiff_path.rename(target_tiff)
        print(f"  TIFF saved: {target_tiff}")

        # 5. Batch delete
        print("Deleting uploaded trees...")
        del_results = client.batch_delete(tree_ids)
        for uid, ok in del_results.items():
            print(f"  {uid}: {'deleted' if ok else 'failed'}")

    except Exception as e:
        print(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
