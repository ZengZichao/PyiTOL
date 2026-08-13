#!/usr/bin/env python3
"""Benchmark local file I/O performance for PyiTOL.

Measures:
  1. Time to write iTOL template files of varying sizes
  2. Time to compute MD5 checksums on generated files
  3. Time to load and parse session snapshot YAML files

All benchmarks operate on locally-generated synthetic data -- no actual
API calls are made.

Run standalone:
    python benchmarks/benchmark_api.py
    python benchmarks/benchmark_api.py --output results.json

Requires: dendropy, pandas, pyyaml, pydantic (project dependencies) + stdlib.
matplotlib is an optional dependency for chart generation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
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

import dendropy  # noqa: E402

from _bench_utils import build_balanced_newick  # noqa: E402

from pyitol.templates.generator import (  # noqa: E402
    TemplateGenerator,
    generate_color_strip_template,
    generate_heatmap_template,
    generate_simple_bar_template,
)
from pyitol.templates.schemas.base import create_schema  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TREE_SIZES = [100, 1_000, 10_000]
REPEATS = 3
CHECKSUM_ALGORITHM = "md5"
SNAPSHOT_SIZES = [50, 200, 500]  # number of entries in a synthetic snapshot


# ---------------------------------------------------------------------------
# Synthetic data generators
# ---------------------------------------------------------------------------

def generate_synthetic_tree(n_leaves: int) -> dendropy.Tree:
    """Generate a synthetic tree with *n_leaves* tips using dendropy."""
    rng = random.Random(42)
    tau = 2.0 * (1.0 + (n_leaves / 500.0))
    for _ in range(10):
        try:
            tree = dendropy.simulate.birth_death(
                birth_rate=1.0,
                death_rate=0.0,
                ntax=n_leaves,
                tree_length=tau,
            )
        except Exception:
            tree = build_balanced_newick(n_leaves)

        tips = [n for n in tree.leaf_node_iter() if n.taxon]
        if len(tips) >= n_leaves:
            break

    # Prune to exact count if overshoot
    tips = list(tree.leaf_node_iter())
    if len(tips) > n_leaves:
        taxa_to_remove = [node.taxon for node in tips[n_leaves:] if node.taxon]
        tree.prune_taxa(taxa_to_remove)

    for i, node in enumerate(tree.leaf_node_iter()):
        if node.taxon:
            node.taxon.label = f"leaf_{i:06d}"

    return tree


def generate_synthetic_taxonomy_csv(
    tree: dendropy.Tree,
    path: Path,
) -> Path:
    """Write a taxonomy CSV with categorical and numeric columns."""
    categorical = ["phylum", "class", "order"]
    numeric = ["abundance", "coverage", "diversity"]
    all_cols = ["id"] + categorical + numeric
    rng = random.Random(42)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=all_cols)
        writer.writeheader()
        for node in tree.leaf_node_iter():
            if not node.taxon:
                continue
            row: dict[str, Any] = {"id": node.taxon.label}
            for col in categorical:
                row[col] = f"{col}_{rng.randint(0, 4)}"
            for col in numeric:
                row[col] = f"{rng.uniform(0, 100):.2f}"
            writer.writerow(row)
    return path


def _generate_synthetic_snapshot(n_entries: int) -> dict:
    """Create a synthetic session snapshot dict with *n_entries* log entries."""
    rng = random.Random(42)
    logs = []
    for i in range(n_entries):
        logs.append({
            "timestamp": f"2026-01-01 00:{i % 60:02d}:{rng.randint(0, 59):02d}",
            "action": rng.choice(["template_color_strip", "template_heatmap", "upload", "export"]),
            "detail": f"output=/tmp/template_{i}.txt, leaves={rng.randint(100, 10000)}",
        })

    files = []
    for i in range(min(n_entries, 20)):
        files.append({
            "path": f"/tmp/template_{i}.txt",
            "size": rng.randint(1024, 1_000_000),
            "checksum": hashlib.md5(str(rng.random()).encode()).hexdigest(),
            "algorithm": "md5",
        })

    return {
        "session_id": f"pyitol_bench_{n_entries}",
        "timestamp": "2026-01-01T00:00:00",
        "command_line": ["pyitol", "template", "color-strip", "--tree", "tree.nwk"],
        "duration_seconds": rng.uniform(1.0, 60.0),
        "inputs": {
            "tree": "/tmp/tree.nwk",
            "taxonomy": "/tmp/taxonomy.csv",
            "id_column": "id",
        },
        "outputs": {
            "output_dir": "/tmp/output",
            "generated_files": [f"/tmp/template_{i}.txt" for i in range(min(n_entries, 20))],
        },
        "api_params": {"format": "png", "dpi": 300},
        "files": files,
        "logs": logs,
    }


# ---------------------------------------------------------------------------
# Benchmark helpers
# ---------------------------------------------------------------------------

def _timed_run(func, *args, **kwargs):
    """Execute *func*, returning (result, elapsed_seconds, peak_mem_bytes)."""
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def _run_repeated(func, *args, repeats: int = REPEATS, **kwargs):
    """Run *func* multiple times, return (min_time, median_time, max_time, peak_mem)."""
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
# Formatting
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
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    def _sep() -> str:
        return "+-" + "-+-".join("-" * w for w in col_widths) + "-+"

    def _row(vals: list[str]) -> str:
        parts = [v.rjust(w) for v, w in zip(vals, col_widths)]
        return "| " + " | ".join(parts) + " |"

    print(_sep())
    print(_row(headers))
    print(_sep())
    for row in rows:
        print(_row(row))
    print(_sep())


# ---------------------------------------------------------------------------
# Benchmark: template file write
# ---------------------------------------------------------------------------

def benchmark_template_write(
    tree: dendropy.Tree, taxonomy_path: Path, tmpdir: Path, repeats: int = REPEATS,
) -> list[dict]:
    """Benchmark writing templates of each type and return results."""
    results = []
    template_dir = tmpdir / "templates"
    template_dir.mkdir()

    templates = [
        {
            "name": "Color Strip",
            "func": generate_color_strip_template,
            "kwargs": {"column": "phylum", "label": "color_strip"},
        },
        {
            "name": "Heatmap",
            "func": generate_heatmap_template,
            "kwargs": {"value_columns": ["abundance", "coverage", "diversity"], "label": "heatmap"},
        },
        {
            "name": "Simple Bar",
            "func": generate_simple_bar_template,
            "kwargs": {"value_column": "abundance", "label": "simple_bar"},
        },
    ]

    tree_path = tmpdir / "tree.nwk"
    tree.write(path=str(tree_path), schema="newick")

    for tmpl in templates:
        out_path = template_dir / f"{tmpl['name'].lower().replace(' ', '_')}.txt"
        t_min, t_med, t_max, mem = _run_repeated(
            tmpl["func"],
            out_path,
            taxonomy_path,
            tree_path,
            repeats=repeats,
            **tmpl["kwargs"],
        )
        file_size = out_path.stat().st_size if out_path.exists() else 0
        results.append({
            "template": tmpl["name"],
            "min_s": t_min,
            "median_s": t_med,
            "max_s": t_max,
            "peak_mem_bytes": mem,
            "file_size_bytes": file_size,
        })

    return results


# ---------------------------------------------------------------------------
# Benchmark: MD5 checksum
# ---------------------------------------------------------------------------

def _compute_md5(path: Path) -> str:
    """Compute MD5 hex digest of a file."""
    hasher = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def benchmark_checksum(tree: dendropy.Tree, taxonomy_path: Path, tmpdir: Path, repeats: int = REPEATS) -> list[dict]:
    """Benchmark MD5 checksum computation on template files of varying sizes."""
    results = []
    tree_path = tmpdir / "tree.nwk"
    tree.write(path=str(tree_path), schema="newick")

    checksum_dir = tmpdir / "checksum_files"
    checksum_dir.mkdir()

    # Generate files of varying sizes by using different template types and
    # tree sizes embedded in the same tree.
    file_specs = [
        ("Small (color strip)", generate_color_strip_template, {"column": "phylum"}),
        ("Medium (heatmap)", generate_heatmap_template, {"value_columns": ["abundance", "coverage", "diversity"]}),
        ("Large (simple bar)", generate_simple_bar_template, {"value_column": "abundance"}),
    ]

    for name, func, kwargs in file_specs:
        out_path = checksum_dir / f"{name.split()[0].lower()}.txt"
        func(out_path, taxonomy_path, tree_path, label=name, **kwargs)
        file_size = out_path.stat().st_size if out_path.exists() else 0

        t_min, t_med, t_max, mem = _run_repeated(_compute_md5, out_path, repeats=repeats)
        results.append({
            "file": name,
            "file_size_bytes": file_size,
            "min_s": t_min,
            "median_s": t_med,
            "max_s": t_max,
            "peak_mem_bytes": mem,
        })

    return results


# ---------------------------------------------------------------------------
# Benchmark: session snapshot load/parse
# ---------------------------------------------------------------------------

def _load_snapshot(path: Path) -> dict:
    """Load and validate a YAML session snapshot."""
    from pyitol.utils.session import SessionContext
    return SessionContext.load_snapshot(path)


def benchmark_snapshot_load(tmpdir: Path, snapshot_sizes: list[int] | None = None, repeats: int = REPEATS) -> list[dict]:
    """Benchmark loading session snapshots of varying sizes."""
    snapshot_sizes = snapshot_sizes or SNAPSHOT_SIZES
    results = []
    snapshot_dir = tmpdir / "snapshots"
    snapshot_dir.mkdir()

    try:
        import yaml
    except ImportError:
        print("  [PyYAML not installed -- skipping snapshot benchmarks]")
        return results

    for n_entries in snapshot_sizes:
        snapshot_data = _generate_synthetic_snapshot(n_entries)
        snapshot_path = snapshot_dir / f"snapshot_{n_entries}.yaml"
        snapshot_path.write_text(
            yaml.dump(snapshot_data, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        file_size = snapshot_path.stat().st_size

        t_min, t_med, t_max, mem = _run_repeated(_load_snapshot, snapshot_path, repeats=repeats)
        results.append({
            "n_log_entries": n_entries,
            "file_size_bytes": file_size,
            "min_s": t_min,
            "median_s": t_med,
            "max_s": t_max,
            "peak_mem_bytes": mem,
        })

    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_all_benchmarks(repeats: int = REPEATS, tree_sizes: list[int] | None = None) -> dict:
    """Run all I/O benchmarks and return structured results."""
    sizes = tree_sizes or TREE_SIZES
    print("=" * 70)
    print("PyiTOL File I/O / Session Benchmark")
    print(f"Repeats per measurement: {repeats}")
    print("=" * 70)
    print()

    all_results: dict[str, Any] = {}

    for n_leaves in sizes:
        print(f"=== Tree size: {n_leaves} leaves ===")
        tree = generate_synthetic_tree(n_leaves)
        actual = sum(1 for _ in tree.leaf_node_iter())
        print(f"    Generated tree with {actual} leaves.")

        with tempfile.TemporaryDirectory(prefix="pyitol_io_bench_") as tmpdir:
            tmpdir_path = Path(tmpdir)
            taxonomy_path = tmpdir_path / "taxonomy.csv"
            generate_synthetic_taxonomy_csv(tree, taxonomy_path)

            # ---- Template Write ---------------------------------------------
            print("  [Template file write]")
            write_results = benchmark_template_write(tree, taxonomy_path, tmpdir_path, repeats=repeats)
            for r in write_results:
                print(f"    {r['template']:15s}: median {_fmt_time(r['median_s'])}, "
                      f"file {_fmt_bytes(r['file_size_bytes'])}")

            # ---- Checksum --------------------------------------------------
            print("  [MD5 checksum]")
            checksum_results = benchmark_checksum(tree, taxonomy_path, tmpdir_path, repeats=repeats)
            for r in checksum_results:
                print(f"    {r['file']:20s}: median {_fmt_time(r['median_s'])}, "
                      f"file {_fmt_bytes(r['file_size_bytes'])}")

            all_results[f"n{n_leaves}"] = {
                "n_leaves": n_leaves,
                "template_write": write_results,
                "checksum": checksum_results,
            }

        print()

    # ---- Snapshot load -------------------------------------------------------
    print("=== Session Snapshot Load/Parse ===")
    with tempfile.TemporaryDirectory(prefix="pyitol_snap_bench_") as tmpdir:
        snapshot_results = benchmark_snapshot_load(Path(tmpdir), repeats=repeats)
        for r in snapshot_results:
            print(f"    {r['n_log_entries']:5d} entries: median {_fmt_time(r['median_s'])}, "
                  f"file {_fmt_bytes(r['file_size_bytes'])}")
        all_results["snapshot_load"] = snapshot_results

    # ---- Summary tables ------------------------------------------------------
    print()
    print("=" * 70)
    print("SUMMARY TABLES")
    print("=" * 70)

    # Table 1: Template Write
    print()
    print("Template File Write Performance")
    print()
    h1 = ["Leaves", "Template", "Min", "Median", "Max", "Peak Mem", "File Size"]
    r1: list[list[str]] = []
    for key in sorted(all_results.keys()):
        if not key.startswith("n"):
            continue
        entry = all_results[key]
        for t in entry["template_write"]:
            r1.append([
                str(entry["n_leaves"]),
                t["template"],
                _fmt_time(t["min_s"]),
                _fmt_time(t["median_s"]),
                _fmt_time(t["max_s"]),
                _fmt_bytes(t["peak_mem_bytes"]),
                _fmt_bytes(t["file_size_bytes"]),
            ])
    _print_table(h1, r1)

    # Table 2: Checksum
    print()
    print("MD5 Checksum Performance")
    print()
    h2 = ["Leaves", "File", "Min", "Median", "Max", "Peak Mem", "File Size"]
    r2: list[list[str]] = []
    for key in sorted(all_results.keys()):
        if not key.startswith("n"):
            continue
        entry = all_results[key]
        for c in entry["checksum"]:
            r2.append([
                str(entry["n_leaves"]),
                c["file"],
                _fmt_time(c["min_s"]),
                _fmt_time(c["median_s"]),
                _fmt_time(c["max_s"]),
                _fmt_bytes(c["peak_mem_bytes"]),
                _fmt_bytes(c["file_size_bytes"]),
            ])
    _print_table(h2, r2)

    # Table 3: Snapshot Load
    if snapshot_results:
        print()
        print("Session Snapshot Load Performance")
        print()
        h3 = ["Log Entries", "Min", "Median", "Max", "Peak Mem", "File Size"]
        r3: list[list[str]] = []
        for s in snapshot_results:
            r3.append([
                str(s["n_log_entries"]),
                _fmt_time(s["min_s"]),
                _fmt_time(s["median_s"]),
                _fmt_time(s["max_s"]),
                _fmt_bytes(s["peak_mem_bytes"]),
                _fmt_bytes(s["file_size_bytes"]),
            ])
        _print_table(h3, r3)

    return all_results


# ---------------------------------------------------------------------------
# Optional matplotlib chart
# ---------------------------------------------------------------------------

def plot_results(results: dict, output_path: Path | None = None) -> None:
    """Generate charts of benchmark results using matplotlib.

    Silently returns if matplotlib is not installed.
    """
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("\n[matplotlib not installed -- skipping chart generation]")
        return

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # --- Chart 1: Template write time by tree size ---
    ax1 = axes[0]
    template_names = ["Color Strip", "Heatmap", "Simple Bar"]
    colors = ("#e64b35", "#4dbbd5", "#00a087")
    tree_keys = sorted(k for k in results if k.startswith("n"))
    x_pos = list(range(len(tree_keys)))
    bar_width = 0.25

    for i, (tname, color) in enumerate(zip(template_names, colors)):
        medians = []
        for key in tree_keys:
            entry = results[key]
            match = [t for t in entry["template_write"] if t["template"] == tname]
            medians.append(match[0]["median_s"] * 1000 if match else 0)
        bars = ax1.bar(
            [p + i * bar_width for p in x_pos],
            medians,
            bar_width,
            label=tname,
            color=color,
        )
        for bar, val in zip(bars, medians):
            if val > 0:
                ax1.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height(),
                    f"{val:.1f}",
                    ha="center", va="bottom", fontsize=7,
                )

    ax1.set_xlabel("Number of tree leaves")
    ax1.set_ylabel("Median write time (ms)")
    ax1.set_title("Template File Write Time")
    ax1.set_xticks([p + bar_width for p in x_pos])
    ax1.set_xticklabels([results[k]["n_leaves"] for k in tree_keys])
    ax1.legend()
    ax1.set_yscale("log")

    # --- Chart 2: Checksum time vs file size ---
    ax2 = axes[1]
    file_sizes = []
    checksum_times = []
    checksum_labels = []
    for key in tree_keys:
        for c in results[key]["checksum"]:
            file_sizes.append(c["file_size_bytes"] / 1024)  # KB
            checksum_times.append(c["median_s"] * 1000)  # ms
            checksum_labels.append(f"{results[key]['n_leaves']}-{c['file'].split()[0]}")

    scatter_colors = []
    for key in tree_keys:
        n = results[key]["n_leaves"]
        for c in results[key]["checksum"]:
            if n <= 100:
                scatter_colors.append("#e64b35")
            elif n <= 1000:
                scatter_colors.append("#4dbbd5")
            else:
                scatter_colors.append("#00a087")

    ax2.scatter(file_sizes, checksum_times, c=scatter_colors, s=60, alpha=0.8, edgecolors="black", linewidths=0.5)
    for fs, ct, lbl in zip(file_sizes, checksum_times, checksum_labels):
        ax2.annotate(lbl, (fs, ct), fontsize=6, ha="left", va="bottom")

    ax2.set_xlabel("File size (KB)")
    ax2.set_ylabel("Median checksum time (ms)")
    ax2.set_title("MD5 Checksum Time vs File Size")

    # --- Chart 3: Snapshot load time ---
    if "snapshot_load" in results and results["snapshot_load"]:
        ax3 = axes[2]
        snap = results["snapshot_load"]
        entries = [s["n_log_entries"] for s in snap]
        times = [s["median_s"] * 1000 for s in snap]
        file_sizes_snap = [s["file_size_bytes"] / 1024 for s in snap]

        ax3.bar(range(len(entries)), times, color="#3c5484", alpha=0.8)
        for i, (t, fs) in enumerate(zip(times, file_sizes_snap)):
            ax3.text(i, t, f"{t:.1f} ms\n({fs:.0f} KB)", ha="center", va="bottom", fontsize=8)

        ax3.set_xlabel("Snapshot log entries")
        ax3.set_ylabel("Median load time (ms)")
        ax3.set_title("Session Snapshot Load Time")
        ax3.set_xticks(range(len(entries)))
        ax3.set_xticklabels([str(e) for e in entries])
    else:
        axes[2].text(0.5, 0.5, "No snapshot data\n(YAML not available)",
                     ha="center", va="center", transform=axes[2].transAxes)
        axes[2].set_title("Session Snapshot Load Time")

    fig.suptitle("PyiTOL File I/O Benchmark", fontsize=14, fontweight="bold")
    fig.tight_layout()

    if output_path is None:
        output_path = _REPO_ROOT / "benchmarks" / "io_benchmark_chart.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\nChart saved to: {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark PyiTOL local file I/O and session snapshot performance.",
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
        help="Path to save benchmark chart image (optional, requires matplotlib).",
    )
    args = parser.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",")] if args.sizes else None
    results = run_all_benchmarks(repeats=args.repeats, tree_sizes=sizes)

    # Save JSON
    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False, default=str)
        print(f"\nResults saved to: {out_path}")

    # Chart
    chart_path = Path(args.chart) if args.chart else None
    plot_results(results, output_path=chart_path)


if __name__ == "__main__":
    main()
