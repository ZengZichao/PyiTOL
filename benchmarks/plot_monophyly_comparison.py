#!/usr/bin/env python3
"""Generate the monophyly cross-library comparison chart (PyiTOL vs ete3 vs ete4 vs DendroPy)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("benchmarks/monophyly_comparison_results.json"))
    parser.add_argument("--output", type=Path, default=Path("benchmarks/monophyly_comparison_chart.png"))
    parser.add_argument("--dpi", type=int, default=300)
    args = parser.parse_args()

    with open(args.input, encoding="utf-8") as fh:
        results = json.load(fh)

    leaves = [r["n_leaves"] for r in results]
    # Only plot libraries actually present in the results JSON (ete4 may be absent
    # if the benchmark was run without ete4 installed).
    all_libs = [
        ("pyitol", "PyiTOL", "#e64b35"),
        ("ete3", "ete3", "#4dbbd5"),
        ("ete4", "ete4", "#3c5488"),
        ("dendropy", "DendroPy", "#00a087"),
    ]
    libs = [lib for lib in all_libs if all(lib[0] in r for r in results)]

    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=args.dpi)
    x = np.arange(len(leaves))
    width = 0.8 / max(len(libs), 1)

    for i, (key, label, color) in enumerate(libs):
        times = [r[key]["median_s"] for r in results]
        mins = [r[key]["min_s"] for r in results]
        maxs = [r[key]["max_s"] for r in results]
        errs = [[t - mn for t, mn in zip(times, mins)], [mx - t for t, mx in zip(times, maxs)]]
        bars = ax.bar(x + i * width, times, width, label=label, color=color, yerr=errs, capsize=3)
        for bar, t in zip(bars, times):
            ax.text(bar.get_x() + bar.get_width() / 2, t, f"{t:.2f}s", ha="center", va="bottom", fontsize=7)

    ax.set_xlabel("Number of tree leaves")
    ax.set_ylabel("Median wall-clock time (s)")
    ax.set_title("Monophyly check performance: PyiTOL vs ete3 vs ete4 vs DendroPy")
    ax.set_xticks(x + width * (len(libs) - 1) / 2)
    ax.set_xticklabels([str(n) for n in leaves])
    ax.set_yscale("log")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=args.dpi, bbox_inches="tight")
    print(f"Chart saved to: {args.output}")


if __name__ == "__main__":
    main()
