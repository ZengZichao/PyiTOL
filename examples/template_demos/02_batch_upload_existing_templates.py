#!/usr/bin/env python3
"""
Batch Upload Existing Template Files.

This script iterates over all template files in the project's
'tests/data/' directory (which ships with sample iTOL template files) and
uploads each one together with a reference tree to iTOL. It logs
success/failure for each file, serving as a functional integration test
for the entire template collection.

Requirements:
  - Valid iTOL API key in '.itolapi.key'
  - Network access to https://itol.embl.de
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.api.client import ITOLAPIClient
from pyitol.exceptions import APIKeyError

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
TREE_FILE = str(DATA_DIR / "synthetic_32tips.nwk")
# Use the sample template files that ship with the test suite. These are
# guaranteed to exist and are valid iTOL v7 templates.
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "tests" / "data"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
PROJECT_PREFIX = "PyiTOL_Batch_Test"
WAIT_TIME = 15
# Template files known to exist in tests/data/ (avoids globbing a directory
# that may contain non-template files).
TEMPLATE_GLOB = "template_*.txt"


def main():
    if not Path(TREE_FILE).exists():
        print(f"Error: Tree file not found: {TREE_FILE}")
        sys.exit(1)

    template_files = sorted(TEMPLATE_DIR.glob(TEMPLATE_GLOB))
    if not template_files:
        print(f"Error: No template files matching '{TEMPLATE_GLOB}' in {TEMPLATE_DIR}")
        sys.exit(1)

    try:
        client = ITOLAPIClient()
    except APIKeyError as e:
        print(f"Error: {e}")
        sys.exit(1)

    log_path = OUTPUT_DIR / "batch_upload_log.txt"
    log_lines = [f"Batch upload started. Templates: {len(template_files)}\n"]

    for tpl in template_files:
        print(f"Uploading {tpl.name} ...")
        try:
            tree_id = client.upload(
                tree_file=TREE_FILE,
                template_files=[str(tpl)],
                project_name=f"{PROJECT_PREFIX}_{tpl.stem}",
            )
            time.sleep(WAIT_TIME)

            # Export a lightweight PDF for verification.
            # Note: the API uses fmt= (not format=) to avoid shadowing the built-in.
            results = client.export([tree_id], fmt="pdf")
            pdf_path = results[tree_id]
            target = OUTPUT_DIR / f"{tpl.stem}.pdf"
            pdf_path.rename(target)

            msg = f"PASS: {tpl.name} -> {tree_id} -> {target.name}"
            print(f"  {msg}")
            log_lines.append(msg + "\n")

        except Exception as e:
            msg = f"FAIL: {tpl.name} -> {e}"
            print(f"  {msg}")
            log_lines.append(msg + "\n")

    log_path.write_text("".join(log_lines), encoding="utf-8")
    print(f"\nLog written to: {log_path}")


if __name__ == "__main__":
    main()
