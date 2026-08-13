#!/usr/bin/env python3
"""Compare monophyly-checking performance across PyiTOL, ete3 and DendroPy.

Generates synthetic trees of increasing size and times how long each library
takes to evaluate the monophyletic status of all groups at a given taxonomic
rank.

Two PyiTOL workloads are benchmarked:

* **Full mode** — ``check_monophyly()`` returning 10 structured fields
  (LCA, extra_nodes, missing_nodes, subgroups, polytomy_details, etc.)
* **Lightweight mode** — Boolean-only determination via MRCA + descendant-set
  comparison, producing output equivalent to ete3/DendroPy's Boolean API.

This dual-mode design lets us disentangle "functional throughput"
(information output comparison) from "raw performance" (equal-task comparison).

Run standalone:
    python benchmarks/benchmark_monophyly_comparison.py
    python benchmarks/benchmark_monophyly_comparison.py --sizes 1000,10000,50000
    python benchmarks/benchmark_monophyly_comparison.py --profile  # cProfile DendroPy@50K
"""
from __future__ import annotations

import argparse
import cProfile
import csv
import io
import json
import math
import pstats
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent
_SRC_DIR = _REPO_ROOT / "src"
if _SRC_DIR.is_dir():
    sys.path.insert(0, str(_SRC_DIR))

import dendropy
from dendropy import Tree
from ete3 import Tree as EteTree

try:  # ete4 (ETE toolkit v4) is optional; benchmark it when available
    from ete4 import Tree as Ete4Tree
except Exception:  # pragma: no cover - environment without ete4
    Ete4Tree = None

from pyitol.core.monophyly import check_monophyly as pyitol_check_monophyly
from pyitol.core.monophyly import (  # noqa: E402
    _build_tip_to_group_mapping,
    _check_monophyly_full,
    clear_tip_index_cache,
)

DEFAULT_SIZES = [1_000, 10_000, 50_000]
REPEATS = 3
NUM_GROUPS = 20  # number of taxonomic groups in the synthetic taxonomy

# ---------------------------------------------------------------------------
# Tree generation
# ---------------------------------------------------------------------------


def generate_exact_newick(n: int) -> str:
    """Return a balanced binary Newick string for exactly *n* leaves.

    Labels are written without quotes so that ete3 parses them verbatim.
    """
    labels = [f"leaf_{i:08d}" for i in range(n)]

    def _build(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        mid = len(items) // 2
        left = _build(items[:mid])
        right = _build(items[mid:])
        return f"({left},{right})"

    return _build(labels) + ";"


def generate_tree(n: int) -> tuple[Tree, str]:
    """Generate a DendroPy tree and return it together with an unquoted Newick string."""
    newick = generate_exact_newick(n)
    tree = Tree.get(data=newick, schema="newick", preserve_underscores=True)
    return tree, newick


def generate_taxonomy(n: int, path: Path, num_groups: int = NUM_GROUPS) -> dict[str, list[str]]:
    """Write a CSV with *num_groups* random groups and return group->members map.

    Leaves are assigned to groups round-robin (``i % num_groups``), producing
    a taxonomy where nearly every group is polyphyletic.  This is the
    **worst-case** workload for PyiTOL's full mode because every call triggers
    the O(k^2 log n) subgroup decomposition path, whereas ete3/DendroPy can
    early-exit after a single Boolean mismatch.
    """
    group_names = [f"group_{g:03d}" for g in range(num_groups)]
    members: dict[str, list[str]] = {g: [] for g in group_names}

    for i in range(n):
        g = group_names[i % num_groups]
        members[g].append(f"leaf_{i:08d}")

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["id", "rank"])
        writer.writeheader()
        for g, ids in members.items():
            for leaf_id in ids:
                writer.writerow({"id": leaf_id, "rank": g})
    return members


# ---------------------------------------------------------------------------
# Timing helpers
# ---------------------------------------------------------------------------


def timed_run(func, *args, **kwargs):
    """Return (result, elapsed_seconds, peak_mem_bytes)."""
    tracemalloc.start()
    t0 = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return result, elapsed, peak


def run_repeated(func, *args, repeats: int = REPEATS, **kwargs):
    """Run *func* repeatedly and return (min, median, max, peak_mem)."""
    times: list[float] = []
    peak_mem = 0
    for _ in range(repeats):
        _, elapsed, mem = timed_run(func, *args, **kwargs)
        times.append(elapsed)
        peak_mem = max(peak_mem, mem)
    times.sort()
    median_idx = len(times) // 2
    return times[0], times[median_idx], times[-1], peak_mem


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------


def benchmark_pyiTOL(tree_path: Path, taxonomy_path: Path) -> tuple[float, float, float, int]:
    """Benchmark PyiTOL's **full** check_monophyly (all groups at rank).

    Returns 10 structured fields per group including LCA, extra_nodes,
    missing_nodes, subgroups, polytomy_details.  This is the information-rich
    mode — the comparison with ete3/DendroPy is a *functional* benchmark, not
    an equal-task benchmark.
    """
    def _run():
        return pyitol_check_monophyly(
            taxonomy_path=taxonomy_path,
            tree_path=tree_path,
            rank="rank",
            id_column="id",
        )
    return run_repeated(_run)


def benchmark_pyiTOL_lightweight(
    tree: Tree, members_map: dict[str, list[str]]
) -> tuple[float, float, float, int]:
    """Benchmark PyiTOL's **lightweight** Boolean-only path.

    Equivalent to what ete3 and DendroPy do: MRCA + descendant-set comparison,
    returning a single Boolean per group.  This enables an *equal-task* (raw
    performance) comparison.  ``tree.is_rooted = True`` is set before the run
    and passed to ``mrca()`` to match PyiTOL's ``_safe_mrca()`` behaviour and
    the DendroPy control benchmark, eliminating rooted-state as a confounding
    variable.
    """
    def _run():
        tree.is_rooted = True
        results = []
        for group, members in members_map.items():
            taxa = [tree.taxon_namespace.get_taxon(label) for label in members]
            taxa = [tx for tx in taxa if tx is not None]
            if not taxa:
                results.append((group, False))
                continue
            mrca = tree.mrca(taxa=taxa, is_rooted=True)
            descendants = {node.taxon.label for node in mrca.leaf_iter() if node.taxon}
            is_mono = descendants == set(members)
            results.append((group, is_mono))
        return results
    return run_repeated(_run)


def benchmark_pyiTOL_inmemory(
    tree: Tree, taxonomy_path: Path, members_map: dict[str, list[str]]
) -> tuple[float, float, float, int]:
    """Benchmark PyiTOL's **full** mode on a pre-parsed in-memory tree.

    Matched-scope variant of ``benchmark_pyiTOL``: tree parsing and taxonomy
    loading happen once *outside* the timed loop (the same scope as the
    DendroPy control), while the timed path still returns the full 10-field
    structured result per group.  The tip-index cache is cleared and rebuilt
    inside each timed run (it is built lazily on first query per batch run).
    """
    import pandas as pd
    from pyitol.core.taxonomy import _normalize_taxonomy_df

    tax_df = pd.read_csv(taxonomy_path, sep=None, engine='python', dtype=str)
    tax_df = _normalize_taxonomy_df(tax_df, 'id')
    tip_to_group = _build_tip_to_group_mapping(tax_df, 'rank')

    def _run():
        clear_tip_index_cache()
        results = []
        for group, members in members_map.items():
            results.append(
                _check_monophyly_full(tree, group, members,
                                      tip_to_group=tip_to_group)
            )
        return results
    return run_repeated(_run)


def benchmark_ete3(newick: str, members_map: dict[str, list[str]]) -> tuple[float, float, float, int]:
    """Benchmark ete3 Tree.check_monophyly for all groups.

    Returns (is_monophyletic: bool, clade_names: list, leaves: list).
    """
    def _run():
        t = EteTree(newick, format=1)
        results = []
        for group, members in members_map.items():
            is_mono, _, _ = t.check_monophyly(
                values=members, target_attr="name", ignore_missing=True
            )
            results.append((group, is_mono))
        return results
    return run_repeated(_run)


def benchmark_ete4(newick: str, members_map: dict[str, list[str]]) -> tuple[float, float, float, int]:
    """Benchmark ete4 (ETE toolkit v4) Tree.check_monophyly for all groups.

    ete4 shares ete3's API contract: ``check_monophyly`` returns
    (is_monophyletic: bool, clade_type: str, leaves_extra: set).  The signature
    differs slightly — ``prop=`` replaces ete3's ``target_attr=`` and there is no
    ``ignore_missing`` argument (unmatched members are simply not found).
    ``parser=1`` mirrors ete3's ``format=1`` (internal node names).
    """
    def _run():
        t = Ete4Tree(newick, parser=1)
        results = []
        for group, members in members_map.items():
            is_mono, _, _ = t.check_monophyly(members, prop="name")
            results.append((group, is_mono))
        return results
    return run_repeated(_run)


def benchmark_dendropy(tree: Tree, members_map: dict[str, list[str]]) -> tuple[float, float, float, int]:
    """Benchmark DendroPy MRCA + descendant comparison for all groups.

    **Important**: ``tree.is_rooted = True`` is set before ``tree.mrca()``
    to match PyiTOL's ``_safe_mrca()`` behaviour and eliminate rooted-state
    as a confounding variable.
    """
    def _run():
        # Ensure rooted state matches PyiTOL's _safe_mrca handling
        tree.is_rooted = True
        results = []
        for group, members in members_map.items():
            taxa = [tree.taxon_namespace.get_taxon(label) for label in members]
            taxa = [tx for tx in taxa if tx is not None]
            if not taxa:
                results.append((group, False))
                continue
            mrca = tree.mrca(taxa=taxa, is_rooted=True)
            descendants = {node.taxon.label for node in mrca.leaf_iter() if node.taxon}
            is_mono = descendants == set(members)
            results.append((group, is_mono))
        return results
    return run_repeated(_run)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------


def fmt_time(seconds: float) -> str:
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.0f} us"
    if seconds < 1.0:
        return f"{seconds * 1_000:.1f} ms"
    return f"{seconds:.2f} s"


def fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if abs(n) < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


# ---------------------------------------------------------------------------
# cProfile helper
# ---------------------------------------------------------------------------


def profile_dendropy_50k(tree: Tree, members_map: dict[str, list[str]]) -> None:
    """Run cProfile on DendroPy at 50K leaves to identify the bottleneck.

    Reports top-20 functions sorted by cumulative time.  Invoke with
    ``--profile`` flag.
    """
    profiler = cProfile.Profile()
    profiler.enable()
    # Run once — profiling overhead makes repeats noisy.
    tree.is_rooted = True
    for group, members in members_map.items():
        taxa = [tree.taxon_namespace.get_taxon(label) for label in members]
        taxa = [tx for tx in taxa if tx is not None]
        if not taxa:
            continue
        mrca = tree.mrca(taxa=taxa, is_rooted=True)
        _descendants = {node.taxon.label for node in mrca.leaf_iter() if node.taxon}
    profiler.disable()

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats("cumulative")
    stats.print_stats(20)
    print("\n" + "=" * 80)
    print("cProfile — DendroPy @ 50K leaves (top-20 by cumulative time)")
    print("=" * 80)
    print(stream.getvalue())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark monophyly checks across libraries (full + lightweight)"
    )
    parser.add_argument(
        "--sizes", type=str, default=None,
        help="Comma-separated tree sizes (default: 1000,10000,50000)",
    )
    parser.add_argument(
        "--repeats", type=int, default=REPEATS,
        help="Repetitions per measurement.",
    )
    parser.add_argument(
        "--libs", type=str, default=None,
        help="Comma-separated subset of libraries to run "
             "(pyitol_full,pyitol_light,ete3,ete4,dendropy; default: all). "
             "Useful for splitting very large sizes across several invocations.",
    )
    parser.add_argument("--output", "-o", type=str, default=None, help="JSON output path.")
    parser.add_argument(
        "--profile", action="store_true",
        help="Run cProfile on DendroPy @ 50K to identify performance bottleneck.",
    )
    args = parser.parse_args()

    sizes = DEFAULT_SIZES
    if args.sizes:
        sizes = [int(s.strip()) for s in args.sizes.split(",")]

    ALL_LIBS = ("pyitol_full", "pyitol_inmem", "pyitol_light", "ete3", "ete4", "dendropy")
    libs = set(ALL_LIBS)
    if args.libs:
        libs = {s.strip() for s in args.libs.split(",") if s.strip()}
        unknown = libs - set(ALL_LIBS)
        if unknown:
            parser.error(f"unknown libraries: {sorted(unknown)} (choose from {ALL_LIBS})")
    if Ete4Tree is None:
        libs.discard("ete4")

    print("=" * 80)
    print("Monophyly benchmark: PyiTOL (full + lightweight) vs ete3 vs ete4 vs DendroPy")
    print(f"  PyiTOL-full : 10-field structured output (functional benchmark)")
    print(f"  PyiTOL-light: Boolean-only MRCA+descendants (equal-task benchmark)")
    print(f"  ete3         : (is_monophyletic, clade_names, leaves)")
    print(f"  ete4         : (is_monophyletic, clade_type, leaves) [ETE v4; skipped if not installed]")
    print(f"  DendroPy     : MRCA + descendant-set Boolean, with is_rooted=True")
    print(f"Repeats per measurement: {args.repeats}")
    print("=" * 80)

    results: list[dict[str, Any]] = []

    for n in sizes:
        print(f"\n--- Tree size: {n} leaves ---")
        tree, newick = generate_tree(n)
        print(f"    Tree generated.")

        import tempfile
        with tempfile.TemporaryDirectory(prefix="pyitol_mono_bench_") as tmpdir:
            tmp = Path(tmpdir)
            tree_path = tmp / "tree.nwk"
            taxonomy_path = tmp / "taxonomy.csv"
            tree.write(path=str(tree_path), schema="newick")
            members_map = generate_taxonomy(n, taxonomy_path)

            # --- PyiTOL full ---
            if "pyitol_full" in libs:
                print("    Benchmarking PyiTOL (full, 10-field) ...")
                py_min, py_med, py_max, py_mem = benchmark_pyiTOL(tree_path, taxonomy_path)
                print(f"    PyiTOL-full  : median {fmt_time(py_med)}, peak mem {fmt_bytes(py_mem)}")
            else:
                py_min = py_med = py_max = float("nan")
                py_mem = 0

            # --- PyiTOL in-memory full (matched scope with DendroPy) ---
            if "pyitol_inmem" in libs:
                print("    Benchmarking PyiTOL (full, in-memory tree) ...")
                py_im = benchmark_pyiTOL_inmemory(tree, taxonomy_path, members_map)
                print(f"    PyiTOL-inmem : median {fmt_time(py_im[1])}, peak mem {fmt_bytes(py_im[3])}")
            else:
                py_im = (float("nan"), float("nan"), float("nan"), 0)

            # --- PyiTOL lightweight ---
            if "pyitol_light" in libs:
                print("    Benchmarking PyiTOL (lightweight, Boolean-only) ...")
                py_light = benchmark_pyiTOL_lightweight(tree, members_map)
                print(f"    PyiTOL-light : median {fmt_time(py_light[1])}, peak mem {fmt_bytes(py_light[3])}")
            else:
                py_light = (float("nan"), float("nan"), float("nan"), 0)

            # --- ete3 ---
            if "ete3" in libs:
                print("    Benchmarking ete3 ...")
                et_min, et_med, et_max, et_mem = benchmark_ete3(newick, members_map)
                print(f"    ete3         : median {fmt_time(et_med)}, peak mem {fmt_bytes(et_mem)}")
            else:
                et_min = et_med = et_max = float("nan")
                et_mem = 0

            # --- ete4 (optional) ---
            if "ete4" in libs:
                print("    Benchmarking ete4 ...")
                e4_min, e4_med, e4_max, e4_mem = benchmark_ete4(newick, members_map)
                print(f"    ete4         : median {fmt_time(e4_med)}, peak mem {fmt_bytes(e4_mem)}")
            else:
                e4_min = e4_med = e4_max = float("nan")
                e4_mem = 0
                if Ete4Tree is None:
                    print("    ete4         : SKIPPED (ete4 not installed)")

            # --- DendroPy ---
            if "dendropy" in libs:
                print("    Benchmarking DendroPy ...")
                dp_min, dp_med, dp_max, dp_mem = benchmark_dendropy(tree, members_map)
                print(f"    DendroPy     : median {fmt_time(dp_med)}, peak mem {fmt_bytes(dp_mem)}")
            else:
                dp_min = dp_med = dp_max = float("nan")
                dp_mem = 0

            # --- Optional cProfile ---
            if args.profile and n == 50_000:
                profile_dendropy_50k(tree, members_map)

        results.append({
            "n_leaves": n,
            "pyitol_full": {
                "min_s": py_min, "median_s": py_med, "max_s": py_max,
                "peak_mem_bytes": py_mem,
                "note": "10-field structured output (functional benchmark)",
            },
            "pyitol_light": {
                "min_s": py_light[0], "median_s": py_light[1], "max_s": py_light[2],
                "peak_mem_bytes": py_light[3],
                "note": "Boolean-only MRCA+descendants (equal-task benchmark)",
            },
            "pyitol_inmem": {
                "min_s": py_im[0], "median_s": py_im[1], "max_s": py_im[2],
                "peak_mem_bytes": py_im[3],
                "note": "full 10-field mode on pre-parsed tree (matched scope with DendroPy)",
            },
            "ete3": {
                "min_s": et_min, "median_s": et_med, "max_s": et_max,
                "peak_mem_bytes": et_mem,
            },
            "ete4": {
                "min_s": e4_min, "median_s": e4_med, "max_s": e4_max,
                "peak_mem_bytes": e4_mem,
                "note": "ETE v4; check_monophyly(prop='name'); NaN if ete4 unavailable",
            },
            "dendropy": {
                "min_s": dp_min, "median_s": dp_med, "max_s": dp_max,
                "peak_mem_bytes": dp_mem,
                "note": "is_rooted=True set before mrca()",
            },
        })

    # --- Print summary ---
    print("\n" + "=" * 80)
    print("Summary — Functional benchmark (information output comparison)")
    print("=" * 80)
    print(f"{'Leaves':>8} {'PyiTOL-full':>14} {'ete3':>12} {'ete4':>12} {'DendroPy':>12}")
    for r in results:
        print(
            f"{r['n_leaves']:>8} "
            f"{fmt_time(r['pyitol_full']['median_s']):>14} "
            f"{fmt_time(r['ete3']['median_s']):>12} "
            f"{fmt_time(r['ete4']['median_s']):>12} "
            f"{fmt_time(r['dendropy']['median_s']):>12}"
        )

    print("\n" + "=" * 80)
    print("Summary — Matched-scope full-mode benchmark (pre-parsed tree)")
    print("=" * 80)
    print(f"{'Leaves':>8} {'PyiTOL-inmem':>14} {'ete3':>12} {'ete4':>12} {'DendroPy':>12}")
    for r in results:
        print(
            f"{r['n_leaves']:>8} "
            f"{fmt_time(r['pyitol_inmem']['median_s']):>14} "
            f"{fmt_time(r['ete3']['median_s']):>12} "
            f"{fmt_time(r['ete4']['median_s']):>12} "
            f"{fmt_time(r['dendropy']['median_s']):>12}"
        )
    print("(note: ete3/ete4 timed paths above include in-loop Newick parsing;"
          " DendroPy and PyiTOL-inmem reuse pre-parsed trees)")

    print("\n" + "=" * 80)
    print("Summary — Equal-task benchmark (raw Boolean-only performance)")
    print("=" * 80)
    print(f"{'Leaves':>8} {'PyiTOL-light':>14} {'ete3':>12} {'ete4':>12} {'DendroPy':>12}")
    for r in results:
        print(
            f"{r['n_leaves']:>8} "
            f"{fmt_time(r['pyitol_light']['median_s']):>14} "
            f"{fmt_time(r['ete3']['median_s']):>12} "
            f"{fmt_time(r['ete4']['median_s']):>12} "
            f"{fmt_time(r['dendropy']['median_s']):>12}"
        )

    print(
        "\nNote: 'PyiTOL-full' returns 10 structured fields per group "
        "(functional benchmark).\n"
        "      'PyiTOL-light' returns a single Boolean per group "
        "(equal-task benchmark).\n"
        "      The workload (round-robin assignment → near-100% polyphyletic groups)\n"
        "      represents a *worst case* for PyiTOL's full mode because every call\n"
        "      triggers the O(k^2 log n) subgroup decomposition."
    )

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=2, ensure_ascii=False)
        print(f"\nResults saved to: {out}")


if __name__ == "__main__":
    main()
