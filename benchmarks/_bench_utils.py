"""Shared utilities for benchmark scripts.

Provides common tree-building functions used across multiple benchmark
modules to avoid code duplication and ensure consistent synthetic data
generation.
"""
from __future__ import annotations

import math
from pathlib import Path

import dendropy

import pyitol


def bench_provenance() -> dict:
    """Return {pyitol_version, git_commit} for result attribution."""
    return {
        "pyitol_version": getattr(pyitol, "__version__", "unknown"),
        "git_commit": pyitol.get_git_hash() or "unknown",
    }


def build_balanced_newick(n: int) -> dendropy.Tree:
    """Build a balanced binary tree with exactly *n* leaves.

    Uses power-of-two padding with dummy leaves that are pruned after
    construction.  The resulting tree is rooted and all leaf labels
    follow the ``leaf_NNNNNN`` format.

    Parameters
    ----------
    n : int
        Number of desired leaves.

    Returns
    -------
    dendropy.Tree
        A balanced binary tree with *n* labelled leaves.
    """
    depth = max(1, int(math.ceil(math.log2(n))))
    labels = [f"leaf_{i:06d}" for i in range(n)]
    while len(labels) < 2 ** depth:
        labels.append(f"_dummy_{len(labels):06d}")

    def _build(level: int, idx: int) -> str:
        if level == 0:
            return labels[idx]
        half = 2 ** (level - 1)
        left = _build(level - 1, idx)
        right = _build(level - 1, idx + half)
        return f"({left},{right})"

    tree = dendropy.Tree.get(data=_build(depth, 0) + ";", schema="newick")
    to_prune = [
        node.taxon for node in tree.leaf_node_iter()
        if node.taxon and node.taxon.label.startswith("_dummy_")
    ]
    tree.prune_taxa(to_prune)
    tree.is_rooted = True
    return tree


def generate_synthetic_taxonomy_csv(
    tree: dendropy.Tree,
    path: Path,
) -> Path:
    """Write a taxonomy CSV with categorical and numeric columns.

    Used by *benchmark_scalability.py* and *benchmark_api.py* for
    generating synthetic annotation data.
    """
    import csv

    categorical = ["phylum", "class", "order"]
    numeric = ["abundance", "coverage", "diversity"]

    labels = [node.taxon.label for node in tree.leaf_node_iter() if node.taxon]
    if not labels:
        raise ValueError("Tree has no labelled leaves — cannot generate taxonomy.")

    fieldnames = ["id"] + categorical + numeric
    rows = []
    for i, label in enumerate(labels):
        row = {"id": label}
        idx = i
        for col in categorical:
            row[col] = f"{col}_{idx % 10:03d}"
            idx //= 10
        for col in numeric:
            row[col] = round((i * 0.73 + 0.1) % 100, 3)
        rows.append(row)

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return path


def build_balanced_newick_str(
    n: int,
    prefix: str = "genome",
    label_width: int = 6,
) -> str:
    """Return a balanced binary Newick *string* with exactly *n* leaves.

    Unlike :func:`build_balanced_newick` (which returns a ``dendropy.Tree``),
    this returns a plain Newick string suitable for feeding directly into
    DendroPy, ete3, or file-based workflows.  The string uses unquoted leaf
    labels of the form ``{prefix}_{i:0{label_width}d}``.

    Parameters
    ----------
    n : int
        Number of desired leaves.
    prefix : str
        Prefix for each leaf label (default ``"genome"``).
    label_width : int
        Zero-padded width for the numeric suffix (default 6).

    Returns
    -------
    str
        A balanced Newick string ending with ``;``.
    """
    labels = [f"{prefix}_{i:0{label_width}d}" for i in range(n)]

    def _build(items: list[str]) -> str:
        if len(items) == 1:
            return items[0]
        mid = len(items) // 2
        return f"({_build(items[:mid])},{_build(items[mid:])})"

    return _build(labels) + ";"
