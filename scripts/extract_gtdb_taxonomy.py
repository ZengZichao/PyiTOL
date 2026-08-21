#!/usr/bin/env python3
"""Extract terminal taxonomy from GTDB reference tree internal-node labels.

GTDB reference trees (e.g. ar53_r232.tree / bac120_r232.tree) annotate internal
nodes with bootstrap support and rank tokens such as ``g__Naiadarchaeum`` or
``100.0:c__CAZHTU01; o__CAZHTU01``. This script propagates those rank tokens
from every internal node down to its descendant leaves, producing a six-rank
taxonomy table (id,domain,phylum,class,order,family,genus) that feeds the
PyiTOL validation / template / monophyly workflow, and optionally a taxa list
of groups (per ``--rank``) with at least two members for batch monophyly
checking.

Usage (as in the manuscript Section 3.7.1):

    python scripts/extract_gtdb_taxonomy.py \
        --tree data/gtdb_r232/ar53_r232.tree \
        --output data/gtdb_r232/ar53_r232_taxonomy.csv \
        --rank genus \
        --taxa-output data/gtdb_r232/ar53_r232_genera.txt

The derivation is purely label-based; no external database is queried.
Suffixed GTDB taxa (e.g. ``Bacillota_I``) are kept verbatim and treated as
distinct taxa, following GTDB's rank-tree convention.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from pathlib import Path

import dendropy

# GTDB rank prefix -> output column, in root-to-tip order.
_RANK_PREFIXES = ["d__", "p__", "c__", "o__", "f__", "g__"]
_COLUMNS = ["domain", "phylum", "class", "order", "family", "genus"]
_TOKEN_RE = re.compile(r"([dpcfgso]__)")


def _tokens_from_label(label: str | None) -> dict[str, str]:
    """Parse GTDB rank tokens out of an internal-node label.

    Labels look like ``100.0:g__Naiadarchaeum`` or
    ``100.0:c__CAZHTU01; o__CAZHTU01``; bootstrap prefixes and support
    values are ignored. Returns {prefix: value} for tokens present.
    """
    if not label:
        return {}
    found: dict[str, str] = {}
    for part in re.split(r"[;,\s]+", label):
        part = part.strip().strip("'\"")
        idx = _TOKEN_RE.search(part)
        if not idx:
            continue
        prefix = idx.group(1)
        value = part[idx.end():].strip()
        if value:
            found[prefix] = value
    return found


def _infer_domain(tree: dendropy.Tree, tree_path: Path) -> str:
    """Return the domain for tips lacking a d__ annotation.

    GTDB rank trees carry a single d__ token near the root; fall back to the
    GTDB dataset convention encoded in the file name (ar53 -> Archaea,
    bac120 -> Bacteria).
    """
    for node in tree.preorder_node_iter():
        tokens = _tokens_from_label(node.label)
        if "d__" in tokens:
            return tokens["d__"]
    name = tree_path.name.lower()
    if name.startswith("ar53"):
        return "Archaea"
    if name.startswith("bac120"):
        return "Bacteria"
    return ""


def extract_taxonomy(tree_path: Path, rank: str = "genus") -> tuple[list[str], list[list[str]], str]:
    """Return (header, rows, domain) with one row per leaf."""
    tree = dendropy.Tree.get(
        path=str(tree_path),
        schema="newick",
        preserve_underscores=True,
    )
    depth = min(len(_COLUMNS), _COLUMNS.index(rank) + 1) if rank in _COLUMNS else len(_COLUMNS)
    default_domain = _infer_domain(tree, tree_path)

    header = ["id"] + _COLUMNS[:depth]
    rows: list[list[str]] = []
    # Propagate accumulated lineage top-down.
    stack: list[tuple[dendropy.Node, dict[str, str]]] = [(tree.seed_node, {})]
    while stack:
        node, parent_lineage = stack.pop()
        lineage = dict(parent_lineage)
        lineage.update(_tokens_from_label(node.label))
        if node.is_leaf():
            label = node.taxon.label if node.taxon else (node.label or "")
            row = [label]
            for col in _COLUMNS[:depth]:
                prefix = _RANK_PREFIXES[_COLUMNS.index(col)]
                value = lineage.get(prefix, "")
                if col == "domain" and not value:
                    value = default_domain
                row.append(value)
            rows.append(row)
        else:
            for child in node.child_node_iter():
                stack.append((child, lineage))
    return header, rows, default_domain


def write_taxa_list(rows: list[list[str]], rank: str, output: Path) -> int:
    """Write groups at ``rank`` with >= 2 members, one per line."""
    col_idx = _COLUMNS.index(rank) + 1
    counts = Counter(row[col_idx] for row in rows if row[col_idx])
    groups = sorted(g for g, n in counts.items() if n >= 2)
    output.write_text("\n".join(groups) + "\n", encoding="utf-8")
    return len(groups)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Extract terminal taxonomy from GTDB reference tree internal-node labels."
    )
    parser.add_argument("--tree", required=True, help="GTDB reference tree (Newick)")
    parser.add_argument("--output", required=True, help="Output taxonomy CSV path")
    parser.add_argument(
        "--rank",
        default="genus",
        choices=_COLUMNS,
        help="Deepest rank column to extract (default: genus -> six-rank table)",
    )
    parser.add_argument(
        "--taxa-output",
        default=None,
        help="Optional: write the list of groups at --rank with >= 2 members",
    )
    args = parser.parse_args(argv)

    tree_path = Path(args.tree)
    if not tree_path.exists():
        print(f"Error: tree file not found: {tree_path}", file=sys.stderr)
        return 1

    header, rows, domain = extract_taxonomy(tree_path, args.rank)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {out_path} (domain: {domain or 'unknown'})")

    if args.taxa_output:
        n_groups = write_taxa_list(rows, args.rank, Path(args.taxa_output))
        print(f"Wrote {n_groups} groups (>= 2 members) to {args.taxa_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
