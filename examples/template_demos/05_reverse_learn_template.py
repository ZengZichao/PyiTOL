#!/usr/bin/env python3
"""
Reverse-Learn Template Demo.

Demonstrates PyiTOL's ability to parse existing iTOL template files
back into structured JSON, and to train a "theme" from a directory
of templates to derive recommended default parameters.

This is useful for:
  - Migrating legacy iTOL templates into PyiTOL's programmatic workflow
  - Extracting color schemes and parameters from published figures
  - Building institutional style guides from a corpus of templates

Data: tests/data/template_*.txt (sample iTOL v7 templates shipped with
the test suite, guaranteed to exist and be valid).
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from pyitol.templates.learner import learn_template, train_theme

# Use the sample templates that ship with the test suite. The original
# example referenced 'iTOL-模板文件/' which does not exist in the repo.
TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "tests" / "data"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main():
    # 1. Learn a single template. Pick the first template_*.txt that exists.
    template_files = sorted(TEMPLATE_DIR.glob("template_*.txt"))
    if not template_files:
        print(f"Error: No template files found in {TEMPLATE_DIR}")
        sys.exit(1)

    example_template = template_files[0]
    print(f"Learning single template: {example_template.name}")
    learned = learn_template(str(example_template))
    out_single = OUTPUT_DIR / "learned_single.json"
    out_single.write_text(json.dumps(learned, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Structured JSON written to: {out_single}")
    print(f"  Detected type: {learned.get('type', 'unknown')}")
    print(f"  Parameters: {list(learned.get('parameters', {}).keys())}")

    # 2. Train a theme from the entire template directory
    print(f"\nTraining theme from: {TEMPLATE_DIR}")
    theme = train_theme(str(TEMPLATE_DIR), min_freq=0.3)
    out_theme = OUTPUT_DIR / "trained_theme.json"
    out_theme.write_text(json.dumps(theme, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  Theme JSON written to: {out_theme}")

    summary = theme.get("summary", {})
    print(f"  Files processed: {summary.get('total_files', 0)}")
    print(f"  Datasets found: {summary.get('total_datasets', 0)}")

    # 3. Print recommended defaults for each dataset type
    recommendations = theme.get("recommendations", {})
    if recommendations:
        print("\nRecommended defaults by dataset type:")
        for dtype, rec in recommendations.items():
            print(f"  {dtype}: {rec}")


if __name__ == "__main__":
    main()
