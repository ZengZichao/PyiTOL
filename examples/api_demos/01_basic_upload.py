#!/usr/bin/env python3
"""
Basic API Demo: Upload a phylogenetic tree to iTOL and export as PDF.

This example demonstrates the minimal workflow:
  1. Initialize ITOLAPIClient (reads .itolapi.key or accepts api_key parameter)
  2. Upload a Newick tree file
  3. Wait for server-side rendering (built-in polling)
  4. Export the rendered tree as a publication-ready PDF

Requirements:
  - A valid iTOL API key (https://itol.embl.de/help.cgi#batch)
  - Place your API key in a file named '.itolapi.key' in the project root
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.api.client import ITOLAPIClient
from pyitol.exceptions import APIKeyError

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
OUTPUT_DIR = str(Path(__file__).parent / "outputs")
FMT = "pdf"
WAIT_TIME = 120         # seconds; increase for large trees
PROJECT_NAME = "pyitol_basic_demo"


def main():
    if not Path(TREE_FILE).exists():
        print(f"Error: Tree file not found: {TREE_FILE}")
        sys.exit(1)

    try:
        client = ITOLAPIClient()
    except APIKeyError as e:
        print(f"Error: {e}")
        print("\nPlease provide your iTOL API key in one of these ways:")
        print("  1. Create '.itolapi.key' in the project root")
        print("  2. Pass api_key='your-key' to ITOLAPIClient()")
        sys.exit(1)

    print(f"API key loaded: {client.api_key[:4]}...{client.api_key[-4:]}")
    print(f"Uploading tree: {TREE_FILE}")

    try:
        # upload_and_export() handles upload, polling, and export in one call.
        # It uses fmt= (not format=) to avoid shadowing the built-in.
        result_path = client.upload_and_export(
            tree_file=TREE_FILE,
            template_files=[],
            fmt=FMT,
            output_dir=OUTPUT_DIR,
            wait_time=WAIT_TIME,
            project_name=PROJECT_NAME,
        )
        print(f"\nSuccess! PDF saved to: {result_path.resolve()}")
    except Exception as e:
        print(f"\nAPI call failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
