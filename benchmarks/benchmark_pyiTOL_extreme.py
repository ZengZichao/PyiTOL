#!/usr/bin/env python3
"""Benchmark PyiTOL monophyly at extreme tree sizes (100k+ leaves)."""
from __future__ import annotations

import argparse
import math
import sys
import time
import tracemalloc
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.is_dir():
    sys.path.insert(0, str(_SRC_DIR))

import csv
import random

from _bench_utils import bench_provenance, build_balanced_newick_str  # noqa: E402

from pyitol.core.monophyly import check_monophyly


def generate_taxonomy(n: int, path: Path, num_groups: int = 100) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "rank"])
        writer.writeheader()
        for i in range(n):
            writer.writerow({"id": f"genome_{i:08d}", "rank": f"group_{(i // 40) % num_groups:03d}"})


def timed_run(func, *args, **kwargs):
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def fmt_time(seconds: float) -> str:
    if seconds < 1.0:
        return f"{seconds * 1000:.1f} ms"
    return f"{seconds:.2f} s"


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", type=str, default="100000,200000")
    parser.add_argument("--outdir", type=Path, default=Path("benchmarks"))
    parser.add_argument("--repeats", type=int, default=3,
                        help="Repetitions per size (median + IQR reported).")
    args = parser.parse_args()

    sizes = [int(s.strip()) for s in args.sizes.split(",")]
    args.outdir.mkdir(parents=True, exist_ok=True)

    import json
    import statistics

    print(f"{'Leaves':>10} {'Median':>12} {'IQR':>14} {'Peak Mem':>12}")
    all_results = []
    for n in sizes:
        newick = build_balanced_newick_str(n, label_width=8)
        tree_path = args.outdir / f"extreme_{n}tips.nwk"
        tax_path = args.outdir / f"extreme_{n}tips_taxonomy.csv"
        tree_path.write_text(newick, encoding="utf-8")
        generate_taxonomy(n, tax_path)

        times: list[float] = []
        peak = 0
        for _ in range(args.repeats):
            _, elapsed, mem = timed_run(
                check_monophyly,
                taxonomy_path=tax_path,
                tree_path=tree_path,
                rank="rank",
                id_column="id",
            )
            times.append(elapsed)
            peak = max(peak, mem)
        times.sort()
        median = statistics.median(times)
        q1 = times[len(times) // 4]
        q3 = times[(3 * len(times)) // 4]
        iqr = q3 - q1
        print(f"{n:>10} {fmt_time(median):>12} {fmt_time(iqr):>14} {fmt_bytes(peak):>12}")
        all_results.append({
            "n_leaves": n,
            "repeats": args.repeats,
            "times_s": times,
            "median_s": median,
            "q1_s": q1,
            "q3_s": q3,
            "iqr_s": iqr,
            "peak_mem_bytes": peak,
        })

    prov = bench_provenance()
    for r in all_results:
        r["_provenance"] = prov

    out_path = args.outdir / "extreme_scale_results.json"
    out_path.write_text(json.dumps(all_results, indent=2), encoding="utf-8")
    print(f"\nResults saved to: {out_path}")


if __name__ == "__main__":
    main()
