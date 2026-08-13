"""Tree info extraction - topology stats, support values, etc."""

from __future__ import annotations

from pathlib import Path

import dendropy
import pandas as pd

from pyitol.core.parser import detect_tree_schema


def _get_tip_label(tip: dendropy.Node) -> str:
    return tip.taxon.label if tip.taxon else ""


def extract_tree_info(
    tree_path: str | Path,
    output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Extract detailed tree topology information.

    Returns DataFrame with columns:
        id, parent_id, branch_length, support, depth, is_tip,
        descendant_count, descendant_ids
    """
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)

    results = []
    node_id_map = {}
    internal_counter = 0
    for node in tree.preorder_node_iter():
        is_tip = node.is_leaf()
        if is_tip:
            label = _get_tip_label(node)
        else:
            internal_counter += 1
            label = f"internal_{internal_counter}"
        node_id_map[id(node)] = label

        parent_label = node_id_map.get(id(node.parent_node), "") if node.parent_node else ""

        branch_length = node.edge_length if node.edge_length is not None else 0.0

        descendants = [_get_tip_label(t) for t in node.leaf_nodes() if t.taxon]

        results.append(
            {
                "id": label,
                "parent_id": parent_label,
                "branch_length": branch_length,
                "depth": node.level(),
                "is_tip": is_tip,
                "descendant_count": len(descendants),
                "descendant_ids": "|".join(sorted(descendants)),
            }
        )

    df = pd.DataFrame(results)
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df


def get_node_count(tree_path: str | Path) -> dict:
    """Get tree node counts."""
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    return {
        "tip_count": len(tree.leaf_nodes()),
        "internal_node_count": len(list(tree.internal_nodes())),
        "total_count": len(list(tree.preorder_node_iter())),
    }


def get_tip_order(tree_path: str | Path) -> list[str]:
    """Get tip labels in tree traversal order."""
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    return [t.taxon.label for t in tree.leaf_nodes() if t.taxon]


_tree_info_cache: dict[str, dict] = {}


def _tree_info_cache_key(tree_path: str) -> str:
    """Generate a cache key including file modification time."""
    import os

    parts = [tree_path]
    try:
        mtime = os.path.getmtime(tree_path)
        parts.append(str(mtime))
    except OSError:
        pass
    return ":".join(parts)


def _get_tree_info_cached(tree_path: str, _cache_key: str) -> dict:
    """Cached version of get_tree_info (key includes mtime for freshness)."""
    if _cache_key in _tree_info_cache:
        return _tree_info_cache[_cache_key]
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(tree_path, schema=schema, preserve_underscores=True)
    tips = [t.taxon.label for t in tree.leaf_nodes() if t.taxon]
    internal_nodes = list(tree.internal_nodes())
    has_bl = any(n.edge_length is not None for n in tree.preorder_node_iter())
    max_depth = max((t.level() for t in tree.leaf_nodes()), default=0)

    result = {
        "tip_count": len(tips),
        "internal_node_count": len(internal_nodes),
        "total_nodes": len(tips) + len(internal_nodes),
        "has_branch_lengths": has_bl,
        "max_depth": max_depth,
        "sample_tips": ", ".join(tips[:10]),
    }
    _tree_info_cache[_cache_key] = result
    if len(_tree_info_cache) > 128:
        oldest_key = next(iter(_tree_info_cache))
        del _tree_info_cache[oldest_key]
    return result


def get_tree_info(tree_path: str | Path) -> dict:
    """Get summary tree info as a dict for CLI display."""
    path_str = str(tree_path)
    key = _tree_info_cache_key(path_str)
    return _get_tree_info_cached(path_str, key)
