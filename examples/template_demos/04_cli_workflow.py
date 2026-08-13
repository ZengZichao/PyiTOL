#!/usr/bin/env python3
"""
CLI Workflow Demo.

Demonstrates a complete command-line workflow without writing Python code:
  1. Validate inputs (tree + taxonomy + colors)
  2. Generate a color-strip template via CLI
  3. Generate a heatmap template via CLI
  4. Generate a simple-bar template via CLI
  5. (Optional) Upload via CLI task commands

This is the recommended approach for users who prefer shell scripting
or need to integrate PyiTOL into Snakemake / Nextflow pipelines.

Data: tests/data/4taxa_* (small 8-tip tree with lowercase column names
'phylum', 'genome_size', 'gc_content' that match the original example).
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "tests" / "data"
TREE_FILE = DATA_DIR / "4taxa_tree.nwk"
TAXONOMY_FILE = DATA_DIR / "4taxa_taxonomy.csv"
OUTPUT_DIR = Path(__file__).parent / "outputs" / "cli_workflow"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run(cmd: list[str]) -> None:
    """Invoke the pyitol CLI (installed entry point) and print output."""
    print(f"$ pyitol {' '.join(cmd)}")
    result = subprocess.run(
        ["pyitol"] + cmd,
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.returncode != 0:
        print(f"Error (exit {result.returncode}): {result.stderr}")
    else:
        print("OK\n")


def main():
    # 1. Validate inputs
    run([
        "validate",
        "--tree", str(TREE_FILE),
        "--taxonomy", str(TAXONOMY_FILE),
        "--color", "#e64b35",
        "--color", "#4dbbd5",
    ])

    # 2. Generate color-strip template (column 'phylum' in the taxonomy CSV)
    run([
        "template", "create", "color-strip",
        "--taxonomy", str(TAXONOMY_FILE),
        "--tree", str(TREE_FILE),
        "--column", "phylum",
        "--output", str(OUTPUT_DIR / "colorstrip.txt"),
    ])

    # 3. Generate heatmap template (multiple numeric columns)
    run([
        "template", "create", "heatmap",
        "--taxonomy", str(TAXONOMY_FILE),
        "--tree", str(TREE_FILE),
        "--columns", "genome_size,gc_content",
        "--output", str(OUTPUT_DIR / "heatmap.txt"),
    ])

    # 4. Generate simple-bar template (single numeric column)
    run([
        "template", "create", "simple-bar",
        "--taxonomy", str(TAXONOMY_FILE),
        "--tree", str(TREE_FILE),
        "--column", "genome_size",
        "--output", str(OUTPUT_DIR / "simplebar.txt"),
    ])

    print(f"\nAll CLI outputs written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
