#!/usr/bin/env python3
"""Benchmark scalability of PyiTOL template generation.

Measures wall-clock time and peak memory for color-strip, heatmap, and
simple-bar template generation on synthetic trees of increasing size
(100, 1000, 10000 leaves).

Run standalone:
    python benchmarks/benchmark_scalability.py
    python benchmarks/benchmark_scalability.py --output results.json

Requires: dendropy, pandas (project dependencies) + stdlib.
matplotlib is an optional dependency for chart generation.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import tempfile
import time
import tracemalloc
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Make sure the project's src/ is importable when running from the repo root.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.is_dir():
    sys.path.insert(0, str(_SRC_DIR))

import dendropy

from _bench_utils import build_balanced_newick  # noqa: E402  -- project dependency

from pyitol.templates.generator import (  # noqa: E402
    generate_color_strip_template,
    generate_heatmap_template,
    generate_simple_bar_template,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TREE_SIZES = [100, 1_000, 10_000]
TAXONOMY_COLUMNS = ["phylum", "class", "order"]
NUMERIC_COLUMNS = ["abundance", "coverage", "diversity"]
BIRTH_RATE = 1.0  # passed to pure-birth tree simulator
REPEATS = 10  # number of repetitions per measurement


# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------

def generate_synthetic_tree(n_leaves: int, birth_rate: float = BIRTH_RATE) -> dendropy.Tree:
    """Generate a synthetic ultrametric tree with *n_leaves* extant tips.

    Uses the Yule (pure-birth) process available in dendropy's
    ``BirthDeathDistribution``.  A retry loop handles the stochastic
    overshoot/undershoot common for large target tip counts.
    """
    # We overshoot the number of tips and prune; dendropy's simulation does
    # not always produce the exact requested number.
    attempts = 0
    max_attempts = 10
    while attempts < max_attempts:
        attempts += 1
        # Scale tau (tree length) roughly logarithmically so that all trees
        # have comparable total height regardless of *n_leaves*.
        tau = 2.0 * (1.0 + (n_leaves / 500.0))
        try:
            tree = dendropy.simulate.birth_death(
                birth_rate=birth_rate,
                death_rate=0.0,
                ntax=n_leaves,
                tree_length=tau,
            )
        except Exception:
            # Very large trees may trigger numerical edge-cases; fall back to
            # a simpler approach: just keep a balanced Newick string.
            tree = build_balanced_newick(n_leaves)

        tip_labels = [n.taxon.label for n in tree.leaf_node_iter() if n.taxon]
        if len(tip_labels) >= n_leaves:
            break

    # If we ended up with more tips than requested, prune extras.
    tips = list(tree.leaf_node_iter())
    if len(tips) > n_leaves:
        taxa_to_remove = [node.taxon for node in tips[n_leaves:] if node.taxon]
        tree.prune_taxa(taxa_to_remove)

    # Relabel tips to simple sequential names
    for i, node in enumerate(tree.leaf_node_iter()):
        if node.taxon:
            node.taxon.label = f"leaf_{i:06d}"

    return tree


def generate_synthetic_taxonomy_csv(
    tree: dendropy.Tree,
    path: Path,
    categorical_cols: list[str] | None = None,
    numeric_cols: list[str] | None = None,
) -> Path:
    """Write a CSV file with one row per leaf in *tree*.

    Columns:
        id  - leaf label (matches Newick tip labels)
        categorical columns - random category assignment (phylum_0..phylum_4, etc.)
        numeric columns     - random floats in [0, 100]
    """
    categorical_cols = categorical_cols or TAXONOMY_COLUMNS
    numeric_cols = numeric_cols or NUMERIC_COLUMNS
    all_cols = ["id"] + categorical_cols + numeric_cols

    rng = __import__("random").Random(42)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_cols)
        writer.writeheader()
        for node in tree.leaf_node_iter():
            if not node.taxon:
                continue
            row: dict[str, Any] = {"id": node.taxon.label}
            for col in categorical_cols:
                row[col] = f"{col}_{rng.randint(0, 4)}"
            for col in numeric_cols:
                row[col] = f"{rng.uniform(0, 100):.2f}"
            writer.writerow(row)

    return path


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------

def _timed_run(func, *args, **kwargs):
    """Execute *func*, returning (result, elapsed_seconds, peak_mem_bytes).

    Uses ``time.perf_counter`` for wall-clock timing and ``tracemalloc`` for
    peak memory measurement.
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def _run_repeated(func, *args, repeats: int = REPEATS, **kwargs):
    """Run *func* multiple times and return (min_time, median_time, max_time, peak_mem)."""
    times: list[float] = []
    peak_mem = 0
    for _ in range(repeats):
        _, elapsed, mem = _timed_run(func, *args, **kwargs)
        times.append(elapsed)
        peak_mem = max(peak_mem, mem)
    times.sort()
    median_idx = len(times) // 2
    return times[0], times[median_idx], times[-1], peak_mem


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_time(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} us"
    if seconds < 1.0:
        return f"{seconds * 1_000:.1f} ms"
    return f"{seconds:.2f} s"


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n:.1f} TB"


def _print_table(headers: list[str], rows: list[list[str]]) -> None:
    """Print a simple aligned ASCII table."""
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def _sep() -> str:
        return "+-" + "-+-".join("-" * w for w in col_widths) + "-+"

    def _row(vals: list[str]) -> str:
        parts = []
        for v, w in zip(vals, col_widths):
            parts.append(v.rjust(w))
        return "| " + " | ".join(parts) + " |"

    print(_sep())
    print(_row(headers))
    print(_sep())
    for row in rows:
        print(_row(row))
    print(_sep())


# ---------------------------------------------------------------------------
# Main benchmark
# ---------------------------------------------------------------------------

def run_benchmarks(tree_sizes: list[int] | None = None, repeats: int = REPEATS) -> list[dict]:
    """Execute all scalability benchmarks and return structured results."""
    tree_sizes = tree_sizes or TREE_SIZES
    all_results: list[dict] = []

    print("=" * 70)
    print("PyiTOL Template Generation Scalability Benchmark")
    print(f"Repeats per measurement: {repeats}")
    print("=" * 70)
    print()

    # ---- Warm-up -----------------------------------------------------------
    # Run all three template types once on a tiny tree before any measurement
    # so that lazy module imports and first-call caches do not bias the peak
    # memory of whichever type happens to be measured first.  All reported
    # memory values are therefore tracemalloc incremental allocations since
    # tracemalloc.start() (uniform methodology across template types).
    warm_tree = generate_synthetic_tree(50)
    with tempfile.TemporaryDirectory(prefix="pyitol_warm_") as warm_dir:
        warm_path = Path(warm_dir)
        warm_tree_file = warm_path / "tree.nwk"
        warm_tax_file = warm_path / "taxonomy.csv"
        warm_tree.write(path=str(warm_tree_file), schema="newick")
        generate_synthetic_taxonomy_csv(warm_tree, warm_tax_file)
        generate_color_strip_template(
            warm_path / "cs.txt", warm_tax_file, warm_tree_file,
            column="phylum", label="warm")
        generate_heatmap_template(
            warm_path / "hm.txt", warm_tax_file, warm_tree_file,
            value_columns=NUMERIC_COLUMNS, label="warm")
        generate_simple_bar_template(
            warm_path / "sb.txt", warm_tax_file, warm_tree_file,
            value_column="abundance", label="warm")
    print("Warm-up complete (lazy imports/caches primed).")
    print()

    for n_leaves in tree_sizes:
        print(f"--- Generating synthetic tree with {n_leaves} leaves ...")
        tree = generate_synthetic_tree(n_leaves)
        actual_leaves = sum(1 for _ in tree.leaf_node_iter())
        print(f"    Tree generated: {actual_leaves} leaves.")

        with tempfile.TemporaryDirectory(prefix="pyitol_bench_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            tree_path = tmpdir_path / "tree.nwk"
            taxonomy_path = tmpdir_path / "taxonomy.csv"

            # Write Newick
            tree.write(path=str(tree_path), schema="newick")

            # Write taxonomy CSV
            generate_synthetic_taxonomy_csv(tree, taxonomy_path)

            template_dir = tmpdir_path / "templates"
            template_dir.mkdir()

            # ---- Color Strip --------------------------------------------------
            out_cs = template_dir / "color_strip.txt"
            _, t_cs_min, t_cs_med, t_cs_max, mem_cs = (
                n_leaves,
                *_run_repeated(
                    generate_color_strip_template,
                    out_cs,
                    taxonomy_path,
                    tree_path,
                    column="phylum",
                    label="color_strip",
                    repeats=repeats,
                ),
            )

            # ---- Heatmap ------------------------------------------------------
            out_hm = template_dir / "heatmap.txt"
            _, t_hm_min, t_hm_med, t_hm_max, mem_hm = (
                n_leaves,
                *_run_repeated(
                    generate_heatmap_template,
                    out_hm,
                    taxonomy_path,
                    tree_path,
                    value_columns=NUMERIC_COLUMNS,
                    label="heatmap",
                    repeats=repeats,
                ),
            )

            # ---- Simple Bar ---------------------------------------------------
            out_sb = template_dir / "simple_bar.txt"
            _, t_sb_min, t_sb_med, t_sb_max, mem_sb = (
                n_leaves,
                *_run_repeated(
                    generate_simple_bar_template,
                    out_sb,
                    taxonomy_path,
                    tree_path,
                    value_column="abundance",
                    label="simple_bar",
                    repeats=repeats,
                ),
            )

        result = {
            "n_leaves": n_leaves,
            "color_strip": {
                "min_s": t_cs_min,
                "median_s": t_cs_med,
                "max_s": t_cs_max,
                "peak_mem_bytes": mem_cs,
            },
            "heatmap": {
                "min_s": t_hm_min,
                "median_s": t_hm_med,
                "max_s": t_hm_max,
                "peak_mem_bytes": mem_hm,
            },
            "simple_bar": {
                "min_s": t_sb_min,
                "median_s": t_sb_med,
                "max_s": t_sb_max,
                "peak_mem_bytes": mem_sb,
            },
        }
        all_results.append(result)

        print(f"    Color Strip : median {_fmt_time(t_cs_med)}, peak mem {_fmt_bytes(mem_cs)}")
        print(f"    Heatmap     : median {_fmt_time(t_hm_med)}, peak mem {_fmt_bytes(mem_hm)}")
        print(f"    Simple Bar  : median {_fmt_time(t_sb_med)}, peak mem {_fmt_bytes(mem_sb)}")
        print()

    # ---- Summary table -------------------------------------------------------
    print()
    print("Summary (median wall-clock time / peak memory)")
    print()

    headers = [
        "Leaves",
        "Color Strip (time)",
        "Color Strip (mem)",
        "Heatmap (time)",
        "Heatmap (mem)",
        "Simple Bar (time)",
        "Simple Bar (mem)",
    ]
    rows: list[list[str]] = []
    for r in all_results:
        rows.append([
            str(r["n_leaves"]),
            _fmt_time(r["color_strip"]["median_s"]),
            _fmt_bytes(r["color_strip"]["peak_mem_bytes"]),
            _fmt_time(r["heatmap"]["median_s"]),
            _fmt_bytes(r["heatmap"]["peak_mem_bytes"]),
            _fmt_time(r["simple_bar"]["median_s"]),
            _fmt_bytes(r["simple_bar"]["peak_mem_bytes"]),
        ])
    _print_table(headers, rows)

    return all_results


# ---------------------------------------------------------------------------
# Optional matplotlib chart
# ---------------------------------------------------------------------------

def plot_results(results: list[dict], output_path: Path | None = None) -> None:
    """Generate bar charts of benchmark results using matplotlib.

    Silently returns if matplotlib is not installed.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[matplotlib not installed -- skipping chart generation]")
        return

    leaves = [r["n_leaves"] for r in results]
    templates = ("color_strip", "heatmap", "simple_bar")
    template_labels = ("Color Strip", "Heatmap", "Simple Bar")
    colors = ("#e64b35", "#4dbbd5", "#00a087")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # --- Time chart ---
    ax_time = axes[0]
    x_positions = list(range(len(leaves)))
    bar_width = 0.25
    for i, (tmpl, label, color) in enumerate(zip(templates, template_labels, colors)):
        times = [r[tmpl]["median_s"] * 1000 for r in results]  # convert to ms
        bars = ax_time.bar(
            [p + i * bar_width for p in x_positions],
            times,
            bar_width,
            label=label,
            color=color,
        )
        # Annotate bars with values
        for bar, t in zip(bars, times):
            if t > 0:
                ax_time.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{t:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )
    ax_time.set_xlabel("Number of tree leaves")
    ax_time.set_ylabel("Median wall-clock time (ms)")
    ax_time.set_title("Template Generation Time")
    ax_time.set_xticks([p + bar_width for p in x_positions])
    ax_time.set_xticklabels([str(n) for n in leaves])
    ax_time.legend()
    ax_time.set_yscale("log")

    # --- Memory chart ---
    ax_mem = axes[1]
    for i, (tmpl, label, color) in enumerate(zip(templates, template_labels, colors)):
        mems = [r[tmpl]["peak_mem_bytes"] / (1024 * 1024) for r in results]  # MB
        bars = ax_mem.bar(
            [p + i * bar_width for p in x_positions],
            mems,
            bar_width,
            label=label,
            color=color,
        )
        for bar, m in zip(bars, mems):
            if m > 0:
                ax_mem.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{m:.1f}",
                    ha="center",
                    va="bottom",
                    fontsize=7,
                )
    ax_mem.set_xlabel("Number of tree leaves")
    ax_mem.set_ylabel("Peak memory (MB)")
    ax_mem.set_title("Template Generation Peak Memory")
    ax_mem.set_xticks([p + bar_width for p in x_positions])
    ax_mem.set_xticklabels([str(n) for n in leaves])
    ax_mem.legend()

    fig.suptitle("PyiTOL Template Generation Scalability", fontsize=14, fontweight="bold")
    fig.tight_layout()

    if output_path is None:
        output_path = _REPO_ROOT / "benchmarks" / "scalability_chart.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark PyiTOL template generation scalability.",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Path to save results as JSON (optional).",
    )
    parser.add_argument(
        "--sizes",
        type=str,
        default=None,
        help="Comma-separated list of tree sizes to test (default: 100,1000,10000).",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=REPEATS,
        help=f"Number of repetitions per measurement (default: {REPEATS}).",
    )
    parser.add_argument(
        "--chart",
        type=str,
        default=None,
        help="Path to save scalability chart image (optional, requires matplotlib).",
    )
    args = parser.parse_args()

    sizes = TREE_SIZES
    if args.sizes:
        sizes = [int(s.strip()) for s in args.sizes.split(",")]

    results = run_benchmarks(sizes, repeats=args.repeats)

    # Save JSON
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {out_path}")

    # Chart
    chart_path = Path(args.chart) if args.chart else None
    plot_results(results, output_path=chart_path)


if __name__ == "__main__":
    main()
