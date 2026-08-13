"""Monophyly detection module - check phylogenetic group monophyly.

Implements three-way classification of taxonomic groups (monophyletic,
paraphyletic, polyphyletic) based on tree topology analysis.

References:
    - Wiley, E.O. & Lieberman, B.S. (2011). Phylogenetics: Theory and
      Practice of Phylogenetic Systematics. 2nd ed. Wiley.
    - Farris, J.S. (1974). Formal definitions of paraphyly and polyphyly.
      Systematic Zoology, 23(4), 548-554.
    - Hennig, W. (1966). Phylogenetic Systematics. University of Illinois Press.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import TypedDict

import dendropy
import pandas as pd

from pyitol.core.parser import detect_tree_schema
from pyitol.exceptions import MetadataParseError

logger = logging.getLogger(__name__)

# Special taxonomy identifiers that map to domain-level groups or tree root


class _SpecialIdentifierInfo(TypedDict):
    domains: list[str] | None
    description: str


_SPECIAL_IDENTIFIERS: dict[str, _SpecialIdentifierInfo] = {
    "LUCA": {
        "domains": ["Bacteria", "Archaea"],
        "description": "Last Universal Common Ancestor (all Bacteria + Archaea)",
    },
    "LACA": {"domains": ["Archaea"], "description": "Last Archaeal Common Ancestor (all Archaea)"},
    "LBCA": {"domains": ["Bacteria"], "description": "Last Bacterial Common Ancestor (all Bacteria)"},
    "ROOT": {"domains": None, "description": "Tree root (all tips in the tree)"},
}


def resolve_special_identifier(
    identifier: str,
    taxonomy_path: str | Path,
    id_column: str = "id",
    domain_column: str = "Domain",
    tax_df: pd.DataFrame | None = None,
) -> list[str] | None:
    """Resolve special identifiers (LUCA/LACA/LBCA/ROOT) to a list of tip IDs.

    Args:
        identifier: One of 'LUCA', 'LACA', 'LBCA', 'ROOT' (case-insensitive)
        taxonomy_path: Path to the taxonomy CSV file
        id_column: Name of the ID column in the taxonomy table
        domain_column: Name of the domain column in the taxonomy table
        tax_df: Optional pre-loaded (and already normalised) taxonomy table.
            Pass this when resolving multiple identifiers so the CSV is
            parsed only once instead of once per identifier.

    Returns:
        List of tip IDs belonging to the specified domains, or None if
        the identifier is not a special identifier.
    """
    key = identifier.upper().strip()
    if key not in _SPECIAL_IDENTIFIERS:
        return None

    info = _SPECIAL_IDENTIFIERS[key]
    target_domains = info["domains"]

    if tax_df is None:
        from pyitol.core.taxonomy import _normalize_taxonomy_df

        tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
        tax_df = _normalize_taxonomy_df(tax_df, id_column)

    # ROOT: return all tip IDs from the taxonomy table
    if target_domains is None:
        members = tax_df["id"].astype(str).tolist()
        if not members:
            raise MetadataParseError(f"No tips found in taxonomy table for identifier '{identifier}'.")
        return members

    if domain_column not in tax_df.columns:
        # Try case-insensitive match
        for col in tax_df.columns:
            if col.lower() == domain_column.lower():
                domain_column = col
                break
        else:
            raise MetadataParseError(
                f"Domain column '{domain_column}' not found for identifier '{identifier}'. "
                f"Available columns: {list(tax_df.columns)}"
            )

    members = tax_df[tax_df[domain_column].isin(target_domains)]["id"].astype(str).tolist()
    if not members:
        raise MetadataParseError(
            f"No tips found for identifier '{identifier}' (domains: {target_domains}). "
            f"Check that the '{domain_column}' column contains values like 'Bacteria' or 'Archaea'."
        )

    return members


def is_special_identifier(identifier: str) -> bool:
    """Check if an identifier is a special taxonomy identifier (LUCA/LACA/LBCA)."""
    return identifier.upper().strip() in _SPECIAL_IDENTIFIERS


def get_special_identifier_description(identifier: str) -> str:
    """Get the description of a special identifier."""
    key = identifier.upper().strip()
    if key in _SPECIAL_IDENTIFIERS:
        return _SPECIAL_IDENTIFIERS[key]["description"]
    return ""


# Module-level cache for tip indices.
# Protected by a threading.Lock for thread-safe access.
# Cache is cleared at the start of each check_monophyly() call to prevent stale data.
_tip_index_cache: dict[tuple[int, int], dict[str, dendropy.Node]] = {}
_tip_index_lock = threading.Lock()

# Per-tree locks for MRCA access (C5).  Replaces the single global _mrca_lock so
# that independent trees are no longer serialized through one shared lock.
# The mapping is bounded (oldest entries evicted beyond _MAX_TREE_LOCKS)
# and fully cleared by clear_tip_index_cache() to prevent unbounded growth in
# long-lived processes such as notebooks.
_tree_locks: dict[int, threading.Lock] = {}
_tree_locks_meta = threading.Lock()
_MAX_TREE_LOCKS = 128

# Cache mapping a node object id to the frozenset of its descendant tip labels
# (C5).  Avoids repeated O(n) descendant traversals when classifying
# paraphyly/polyphyly.  Cleared together with the tip-index cache to prevent
# cross-tree staleness.
_descendant_cache: dict[int, frozenset[str]] = {}
_descendant_cache_lock = threading.Lock()

# Low-memory mode: when enabled, skip tip-index caching to reduce memory usage
# at the cost of repeated O(n) leaf-node traversals for each MRCA call.
_LOW_MEMORY: bool = False


def set_low_memory(enabled: bool = True) -> None:
    """Enable or disable low-memory mode globally.

    In low-memory mode the tip-index cache is cleared and not rebuilt,
    trading speed for lower peak memory.  Useful for extremely large trees
    (100k+ leaves) on consumer hardware.
    """
    global _LOW_MEMORY
    _LOW_MEMORY = enabled
    if enabled:
        with _tip_index_lock:
            _tip_index_cache.clear()


def _is_low_memory() -> bool:
    """Return the current low-memory mode state."""
    return _LOW_MEMORY


def _tree_cache_key(tree: dendropy.Tree) -> tuple[int, int]:
    """Generate a cache key that combines tree id and taxon namespace id.

    Using two ids reduces the chance of ABA collisions when a tree is GC'd
    and a new tree is allocated at the same memory address.
    """
    return (id(tree), id(tree.taxon_namespace))


def _get_tree_lock(tree: dendropy.Tree) -> threading.Lock:
    """Return a per-tree lock so concurrent operations on *different* trees do
    not serialize through a single global lock (C5).

    The mapping is bounded — once more than _MAX_TREE_LOCKS distinct trees
    have been seen, the oldest entries are evicted (dicts preserve insertion
    order).  Eviction only affects trees not currently in use in practice,
    because public entry points clear caches/locks between batch calls.
    """
    tid = id(tree)
    with _tree_locks_meta:
        lock = _tree_locks.get(tid)
        if lock is None:
            lock = threading.Lock()
            _tree_locks[tid] = lock
            while len(_tree_locks) > _MAX_TREE_LOCKS:
                _tree_locks.pop(next(iter(_tree_locks)))
    return lock


def _safe_mrca(tree: dendropy.Tree, taxa: list[dendropy.Taxon]) -> dendropy.Node | None:
    """Call tree.mrca() after temporarily setting tree.is_rooted to avoid warnings.

    Thread-safe: uses a per-tree lock (see ``_get_tree_lock``) so operations on
    independent trees are not serialized.  Restores the original is_rooted value
    to prevent mutating shared state.
    """
    lock = _get_tree_lock(tree)
    with lock:
        original = tree.is_rooted
        tree.is_rooted = True
        try:
            return tree.mrca(taxa=taxa)
        finally:
            tree.is_rooted = original


def _build_tip_index(tree: dendropy.Tree) -> dict[str, dendropy.Node]:
    """Build a lookup dictionary from taxon label to tip node."""
    return {n.taxon.label: n for n in tree.leaf_nodes() if n.taxon}


def _find_tip_node(tree: dendropy.Tree, label: str) -> dendropy.Node | None:
    """Find a tip node by its taxon label.

    Uses a module-level cache keyed by (tree_id, namespace_id) for O(1) lookup after first call.
    Thread-safe: protected by _tip_index_lock.
    Returns None if the label is not found or if the cached node has no taxon.

    In low-memory mode the cache is bypassed entirely — each call performs an
    O(n) leaf-node traversal to avoid storing the full tip index in memory.
    """
    # Low-memory path: linear scan, no caching
    if _LOW_MEMORY:
        for leaf in tree.leaf_node_iter():
            if leaf.taxon and leaf.taxon.label == label:
                return leaf
        return None

    cache_key = _tree_cache_key(tree)
    with _tip_index_lock:
        index = _tip_index_cache.get(cache_key)
        if index is None:
            index = _build_tip_index(tree)
            _tip_index_cache[cache_key] = index
        node = index.get(label)
    if node is None:
        return None
    if node.taxon is None:
        # Stale cache entry (e.g. taxon was removed externally)
        with _tip_index_lock:
            index = _tip_index_cache.get(cache_key)
            if index is not None:
                index.pop(label, None)
        return None
    return node


def clear_tip_index_cache(tree: dendropy.Tree | None = None) -> None:
    """Clear the tip index cache (and descendant-label cache) for a specific
    tree or all trees.

    Thread-safe. Call this after tree topology modifications (collapse/prune)
    to avoid stale data.
    """
    with _tip_index_lock:
        if tree is not None:
            _tip_index_cache.pop(_tree_cache_key(tree), None)
        else:
            _tip_index_cache.clear()
    with _descendant_cache_lock:
        _descendant_cache.clear()
    if tree is None:
        # Also drop per-tree locks on a full clear so they cannot
        # accumulate across many trees in long-lived processes.
        with _tree_locks_meta:
            _tree_locks.clear()


def _get_lca_label(tree: dendropy.Tree, tip_nodes: list[dendropy.Node]) -> str:
    """Get a readable label for the LCA node."""
    if not tip_nodes:
        return "N/A"
    taxa = [n.taxon for n in tip_nodes if n.taxon]
    if not taxa:
        return "N/A"
    lca = _safe_mrca(tree, taxa=taxa)
    if lca is None:
        return "N/A"
    if lca.taxon and lca.taxon.label:
        return lca.taxon.label
    return f"internal_{lca.level()}"


def _get_descendant_labels(node: dendropy.Node) -> set[str]:
    """Get all descendant tip labels from a node (cached, C5).

    The result is cached by node identity to avoid repeated O(n) descendant
    traversals during paraphyly/polyphyly classification.  The cache is cleared
    by ``clear_tip_index_cache`` (called at the start of every public check).
    """
    key = id(node)
    with _descendant_cache_lock:
        cached = _descendant_cache.get(key)
    if cached is not None:
        return set(cached)
    labels = frozenset(t.taxon.label for t in node.leaf_nodes() if t.taxon)
    with _descendant_cache_lock:
        _descendant_cache[key] = labels
    return set(labels)


def _is_polytomy(node: dendropy.Node | None) -> bool:
    """Return True if *node* has more than two child branches."""
    if node is None:
        return False
    return sum(1 for _ in node.child_node_iter()) > 2


def _classify_paraphyletic_vs_polyphyletic(lca: dendropy.Node, member_set: set[str]) -> str:
    """Distinguish paraphyly from polyphyly under strict phylogenetic definitions (C1).

    Let L = MRCA(S) and E = descendants(L) \\ S (E must be non-empty, otherwise
    the group is monophyletic / has no extra nodes).  Each child c of L is
    inspected to see whether it contains both S members and non-S members
    (a "mixed" child):

    - If ≥ 2 mixed children exist, E shreds S across ≥ 2 mutually non-nested
      independent subclades → polyphyletic (``'polyphyletic'``).
    - Otherwise (E non-empty but every child is either pure-S or pure-non-S),
      S equals L minus one or more whole sister clades → paraphyletic
      (``'paraphyletic'``).

    The criterion is purely topological and does not rely on taxonomic group
    names.  It avoids the old implementation's over-calling of polyphyly
    ("members spanning ≥ 2 child clades → polyphyletic"), which misclassified
    classical paraphyly as polyphyly.

    Args:
        lca: The least common ancestor node of the member set S.
        member_set: The set of member tip labels S.

    Returns:
        ``'polyphyletic'`` or ``'paraphyletic'``.
    """
    mixed_children = 0
    for child in lca.child_node_iter():
        child_descendants = _get_descendant_labels(child)
        has_s = bool(member_set & child_descendants)
        has_non_s = bool(child_descendants - member_set)
        if has_s and has_non_s:
            mixed_children += 1
            if mixed_children >= 2:
                return "polyphyletic"
    return "paraphyletic"


def _resolve_polytomy_lca(
    tree: dendropy.Tree,
    lca: dendropy.Node,
    member_set: set[str],
    polytomy_mode: str,
) -> tuple[dendropy.Node, dict | None]:
    """Adjust LCA handling when the MRCA is a polytomy.

    In a resolved (binary) LCA the normal three-way classification applies.
    When the LCA is a polytomy and the members occupy only a *strict subset*
    of its child clades, the unresolved topology prevents any definitive
    mono/para/poly call.  We therefore return an explicit polytomy annotation
    (carrying the caller's mode) so the result becomes ``'data_insufficient'``
    (strict / data-insufficient modes) or conservatively ``'paraphyletic'``
    (relaxed mode) instead of a forced ``'polyphyletic'`` (C4).

    If the members span *every* child clade of the polytomy, the polytomy is
    the effective LCA and normal classification proceeds.

    Returns:
        (effective_lca, polytomy_info).  *polytomy_info* is None unless the
        LCA is a polytomy whose members span multiple but not all child clades.
    """
    if not _is_polytomy(lca):
        return lca, None

    children = list(lca.child_node_iter())
    occupied = 0
    for child in children:
        child_tips = _get_descendant_labels(child)
        if member_set & child_tips:
            occupied += 1

    if occupied == len(children):
        # Members span every child clade; the polytomy is the true LCA.
        return lca, None

    lca_label = lca.taxon.label if lca.taxon else f"internal_{lca.level()}"
    polytomy_info = {
        "mode": polytomy_mode,
        "lca": lca_label,
        "occupied_children": occupied,
        "total_children": len(children),
    }
    return lca, polytomy_info


def _find_lca(tree: dendropy.Tree, node_ids: list[str]) -> dendropy.Node | None:
    """Find the Last Common Ancestor for a set of tip nodes."""
    tip_nodes = []
    for nid in node_ids:
        node = _find_tip_node(tree, nid)
        if node is None or node.taxon is None:
            continue
        tip_nodes.append(node.taxon)
    if not tip_nodes:
        return None
    return _safe_mrca(tree, taxa=tip_nodes)


def _build_tip_to_group_mapping(tax_df: pd.DataFrame, rank: str) -> dict[str, str]:
    """Build a mapping from tip ID to its group name at the given rank.

    Note (C3 — implicit assumption): at a given rank, each group name is
    assumed to correspond to exactly one contiguous set of same-group tips,
    and distinct group names do not share tips.  If this assumption is
    violated (e.g. the same name appears at different ranks, or one group
    name is scattered across disconnected branches), downstream nested-
    monophyly classification may produce false positives.  Callers should
    ensure ``tip_to_group`` satisfies this assumption.
    """
    if rank not in tax_df.columns:
        return {}
    sub = tax_df[["id", rank]].dropna(subset=[rank])
    return dict(zip(sub["id"].astype(str), sub[rank].astype(str)))


def check_monophyly(
    taxonomy_path: str | Path,
    tree_path: str | Path,
    rank: str,
    id_column: str = "id",
    polytomy_mode: str = "strict",
) -> list[dict]:
    """Check monophyly for all groups at a given rank level.

    Returns list of dicts with group info including monophyly status
    (monophyletic/paraphyletic/polyphyletic), LCA, extra nodes, missing nodes,
    and subgroup details for polyphyletic groups.

    Implements the 6-step algorithm from Farris (1974) and Hennig (1966):
    1. Compute LCA of group members
    2. Get all descendants of LCA
    3. If L = S (no extra, no missing): monophyletic
    4. If L ⊃ S and L\\S all belong to G: monophyletic (nested subgroup)
    5. If L ⊃ S and some L\\S belong to different group: paraphyletic
    6. If members span multiple independent clades: polyphyletic

    Args:
        polytomy_mode: 'strict', 'relaxed', or 'data-insufficient'.  See `_check_monophyly_full`.
    """
    # C2: Clear tip index cache to prevent stale data from previous trees
    clear_tip_index_cache()

    tree_path = Path(tree_path)
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    all_tips = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}

    from pyitol.core.taxonomy import _normalize_taxonomy_df

    tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    tax_df = _normalize_taxonomy_df(tax_df, id_column)
    tax_df["id"] = tax_df["id"].astype(str)

    if rank not in tax_df.columns:
        raise MetadataParseError(f"Rank column '{rank}' not found. Available: {list(tax_df.columns)}")

    tip_to_group = _build_tip_to_group_mapping(tax_df, rank)

    # Members absent from the tree are kept in the member lists so that
    # `_check_monophyly_full` records them in `missing_nodes` and flags the
    # affected groups as 'incomplete_sampling', instead of silently dropping
    # them.  A single WARNING summarises the total count.
    groups = {}
    n_missing_total = 0
    for group_name, group_df in tax_df.groupby(rank):
        ids = group_df["id"].tolist()
        n_missing_total += sum(1 for x in ids if x not in all_tips)
        if ids:
            groups[group_name] = ids
    if n_missing_total:
        logger.warning(
            "%d taxonomy row(s) reference tips not present in the tree; they are "
            "reported as missing_nodes and the affected groups are classified as "
            "incomplete_sampling.",
            n_missing_total,
        )

    results = []
    for group_name, members in groups.items():
        result = _check_monophyly_full(
            tree, group_name, members, tip_to_group=tip_to_group, polytomy_mode=polytomy_mode
        )
        results.append(result)

    return results


def check_monophyly_with_taxa_list(
    taxonomy_path: str | Path,
    tree_path: str | Path,
    rank: str | None = None,
    taxa_list: list[str] | None = None,
    taxa_file: str | Path | None = None,
    id_column: str = "id",
    polytomy_mode: str = "strict",
) -> list[dict]:
    """Check monophyly for specific taxa groups.

    Supports special identifiers LUCA, LACA, LBCA which resolve to
    domain-level groups (Bacteria, Archaea, or both).

    Returns list of dicts with columns: group, status, lca_node, member_count,
    extra_nodes, missing_nodes, subgroups, polytomy_details.

    Args:
        polytomy_mode: 'strict', 'relaxed', or 'data-insufficient'.  See `_check_monophyly_full`.
    """
    # C2: Clear tip index cache to prevent stale data from previous trees
    clear_tip_index_cache()

    tree_path = Path(tree_path)
    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    all_tips = {t.taxon.label for t in tree.leaf_nodes() if t.taxon}

    if taxa_file:
        taxa_list = Path(taxa_file).read_text(encoding="utf-8").strip().splitlines()

    # Resolve special identifiers (LUCA/LACA/LBCA)
    # P1-xx: Initialize before the conditional so special groups are always
    # available to merge back into `groups`, even when mixed with normal taxa.
    resolved_groups: dict[str, list[str]] = {}
    if taxa_list:
        # When special identifiers are present, parse the taxonomy table
        # once and reuse it for every identifier (previously one CSV parse
        # per identifier — expensive at GTDB scale).
        special_tax_df = None
        if any(is_special_identifier(n) for n in taxa_list):
            from pyitol.core.taxonomy import _normalize_taxonomy_df

            special_tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
            special_tax_df = _normalize_taxonomy_df(special_tax_df, id_column)
        remaining_taxa = []
        for name in taxa_list:
            name_stripped = name.strip()
            if is_special_identifier(name_stripped):
                members = resolve_special_identifier(
                    name_stripped, taxonomy_path, id_column=id_column, tax_df=special_tax_df
                )
                if members:
                    n_present = sum(1 for x in members if x in all_tips)
                    if n_present < len(members):
                        n_missing_special = len(members) - n_present
                        logger.warning(
                            "Special identifier '%s': %d of %d resolved tips are not "
                            "present in the tree and were excluded.",
                            name_stripped,
                            n_missing_special,
                            len(members),
                        )
                    resolved_groups[name_stripped] = [x for x in members if x in all_tips]
            else:
                remaining_taxa.append(name_stripped)
        # If all taxa were special identifiers, we have our groups
        if not remaining_taxa and resolved_groups:
            groups = resolved_groups
            tip_to_group = {}  # type: dict[str, str]
            results = []
            for group_name, members in groups.items():
                result = _check_monophyly_full(
                    tree, group_name, members, tip_to_group=tip_to_group, polytomy_mode=polytomy_mode
                )
                results.append(result)
            return results
        # Otherwise, continue with remaining taxa in normal flow
        taxa_list = remaining_taxa if remaining_taxa else taxa_list

    tip_to_group = {}
    n_missing_total = 0  # Track members absent from the tree
    if rank:
        from pyitol.core.taxonomy import _normalize_taxonomy_df

        tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
        tax_df = _normalize_taxonomy_df(tax_df, id_column)
        tax_df["id"] = tax_df["id"].astype(str)
        tip_to_group = _build_tip_to_group_mapping(tax_df, rank)

        if taxa_list:
            tax_df = tax_df[tax_df[rank].isin(taxa_list)]

        groups = {}
        for group_name, group_df in tax_df.groupby(rank):
            # Keep absent members so they are reported as missing_nodes
            # (status 'incomplete_sampling') rather than silently dropped.
            ids = group_df["id"].tolist()
            n_missing_total += sum(1 for x in ids if x not in all_tips)
            if ids:
                groups[group_name] = ids
    elif taxa_list and taxonomy_path:
        from pyitol.core.taxonomy import _normalize_taxonomy_df

        tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
        tax_df = _normalize_taxonomy_df(tax_df, id_column)
        tax_df["id"] = tax_df["id"].astype(str)
        groups = {}
        for name in taxa_list:
            members = tax_df.loc[tax_df["id"] == name, "id"].tolist()
            if members:
                groups[name] = members
                n_missing_total += sum(1 for x in members if x not in all_tips)
    else:
        # V3: support monophyly checks on a bare list of tip names
        # (rank=None, taxonomy_path=None).  Each supplied name that occurs as
        # a tip forms a single-tip group; classification is delegated to
        # `_check_monophyly_full`, which decides via "does the descendant set
        # of the LCA equal the member set" (no taxonomic group names needed).
        # An error is raised only when no input is usable at all.
        if taxa_list:
            groups = {}
            skipped = []
            for name in taxa_list:
                name_stripped = name.strip()
                if name_stripped and name_stripped in all_tips:
                    groups[name_stripped] = [name_stripped]
                elif name_stripped:
                    skipped.append(name_stripped)
            if skipped:
                # Surface skipped names instead of dropping them silently
                logger.warning(
                    "%d supplied taxa are not present in the tree and were skipped: %s",
                    len(skipped),
                    ", ".join(skipped[:5]) + (", ..." if len(skipped) > 5 else ""),
                )
            if not groups:
                raise MetadataParseError(
                    "None of the supplied taxa appear as tips in the tree; "
                    "either --rank with --taxonomy or valid --taxa must be specified"
                )
        else:
            raise MetadataParseError("Either --rank with --taxonomy or --taxa must be specified")

    # P1-xx: Merge special-identifier groups (LUCA/LACA/LBCA) back into the result.
    # The normal flow above only builds rank/normal-taxa groups; without this merge,
    # special groups passed alongside normal names would be silently dropped. On key
    # conflict we union the member lists to avoid losing data from either source.
    for _name, _members in resolved_groups.items():
        if _name in groups:
            _seen = set(groups[_name])
            groups[_name] = groups[_name] + [m for m in _members if m not in _seen]
        else:
            groups[_name] = _members

    if n_missing_total:
        logger.warning(
            "%d member(s) are not present in the tree; they are reported as "
            "missing_nodes and the affected groups are classified as "
            "incomplete_sampling.",
            n_missing_total,
        )

    results = []
    for group_name, members in groups.items():
        result = _check_monophyly_full(
            tree, group_name, members, tip_to_group=tip_to_group, polytomy_mode=polytomy_mode
        )
        results.append(result)

    return results


def _check_monophyly_full(
    tree: dendropy.Tree,
    group_name: str,
    members: list[str],
    tip_to_group: dict[str, str] | None = None,
    polytomy_mode: str = "strict",
) -> dict:
    """Full monophyly check with classification: monophyletic / paraphyletic /
    polyphyletic / incomplete_sampling / data_insufficient / unknown.

    Implements the 6-step algorithm from Farris (1974) and Hennig (1966):
    1. Find LCA of all member tips (S)
    2. Get all descendants of LCA (set L)
    3. Calculate extra nodes E = L - S (descendants not in the group)
    4. Calculate missing nodes M = S - L (group members not in LCA descendants)
    5. Classification:
       - E empty AND M empty -> monophyletic (L = S)
       - E non-empty AND all E tips belong to group G -> monophyletic (nested subgroup, L⊃S but all L\\S in G)
       - M non-empty -> incomplete_sampling (some members absent from the tree;
         kept distinct from topological polyphyly, C2)
       - E non-empty: strict phylogenetic-definition classification (C1):
           * ≥ 2 children of L are "mixed" (contain both S and non-S members) -> polyphyletic
           * otherwise (E non-empty but no mixed child, i.e. S = L minus whole
             sister clades) -> paraphyletic
       - unresolved topology (LCA is a polytomy and members occupy only a
         subset of child clades):
           strict / data-insufficient modes -> data_insufficient; relaxed -> paraphyletic (C4)

    Note (C3 — implicit assumption): at a given rank, each group name is
    assumed to correspond to exactly one contiguous set of same-group tips,
    and distinct group names do not share tips.  If this assumption is
    violated (e.g. the same name appears at different ranks, or one group
    name is scattered across disconnected branches), nested-monophyly
    classification may produce false positives.  Callers should ensure
    ``tip_to_group`` satisfies this assumption.

    Args:
        tree: DendroPy tree object
        group_name: Name of the taxonomic group being checked
        members: List of tip IDs belonging to the group
        tip_to_group: Optional mapping from tip ID to group name at the checked rank.
            Required for correct nested-monophyly classification (step 4).
            Use None (not empty dict) when taxonomy mapping is unavailable.
        polytomy_mode: How to handle multifurcating LCA nodes.  'strict' (default)
            returns 'data_insufficient' for groups caught in an unresolved polytomy
            (members span multiple but not all child clades), because the unresolved
            topology prevents any definitive call (C4); 'relaxed' treats such groups as
            'paraphyletic' rather than forcing 'polyphyletic'; 'data-insufficient'
            returns 'data_insufficient' explicitly.
    """
    tip_nodes = []
    for m in members:
        node = _find_tip_node(tree, m)
        if node is not None and node.taxon is not None:
            tip_nodes.append(node)

    if not tip_nodes:
        # No member could be located in the tree — record all of them as
        # missing so batch callers can see what was dropped by topology.
        return {
            "group": group_name,
            "status": "unknown",
            "lca_node": "N/A",
            "member_count": len(members),
            "extra_nodes": "",
            "missing_nodes": "|".join(sorted(members)) if members else "",
            "subgroups": "",
            "extra_count": 0,
            "missing_count": len(members),
        }

    lca_label = _get_lca_label(tree, tip_nodes)

    lca_taxa = [n.taxon for n in tip_nodes if n.taxon]
    lca = _safe_mrca(tree, taxa=lca_taxa)
    if lca is None:
        return {
            "group": group_name,
            "status": "unknown",
            "lca_node": "N/A",
            "member_count": len(members),
            "extra_nodes": "",
            "missing_nodes": "",
            "subgroups": "",
            "extra_count": 0,
            "missing_count": 0,
        }

    all_descendants = _get_descendant_labels(lca)
    member_set = set(members)

    # Adjust for polytomies when requested.
    lca, polytomy_info = _resolve_polytomy_lca(tree, lca, member_set, polytomy_mode)
    # Recompute descendants if the LCA was conceptually adjusted (currently it
    # is not replaced, only annotated; kept for forward compatibility).
    all_descendants = _get_descendant_labels(lca)

    extra_nodes = all_descendants - member_set
    missing_nodes = member_set - all_descendants

    # Classification aligned with paper algorithm (C1)
    # Explicitly distinguish None (no mapping provided) from empty dict (mapping provided but empty)
    has_taxonomy_mapping = tip_to_group is not None and len(tip_to_group) > 0

    # Polytomy handling (C4): when the LCA is a polytomy and members occupy
    # only a subset of its child clades, the topology is unresolved and no
    # definitive mono/para/poly call is possible.  'strict' and
    # 'data-insufficient' modes return 'data_insufficient'; 'relaxed' mode
    # conservatively returns 'paraphyletic'.  Members spanning every child
    # clade proceed to normal classification.
    if polytomy_info is not None:
        if missing_nodes:
            # Some members are absent from the tree (incomplete sampling);
            # kept distinct from topological polyphyly (C2)
            status = "incomplete_sampling"
        elif polytomy_info.get("mode") in ("data-insufficient", "strict") and extra_nodes:
            status = "data_insufficient"
        elif extra_nodes:
            status = "paraphyletic"
        else:
            status = "monophyletic"
        subgroups_str = ""
        polytomy_details = (
            f"polytomy at {polytomy_info['lca']}: "
            f"members occupy {polytomy_info['occupied_children']}/{polytomy_info['total_children']} child clades"
        )
        return {
            "group": group_name,
            "status": status,
            "lca_node": lca_label,
            "member_count": len(members),
            "extra_nodes": "|".join(sorted(extra_nodes)) if extra_nodes else "",
            "missing_nodes": "|".join(sorted(missing_nodes)) if missing_nodes else "",
            "subgroups": subgroups_str,
            "extra_count": len(extra_nodes),
            "missing_count": len(missing_nodes),
            "polytomy_details": polytomy_details,
        }

    if not extra_nodes and not missing_nodes:
        # Step 3: L = S -> monophyletic
        status = "monophyletic"
    elif missing_nodes:
        # Step 6: some members of S are not descendants of the LCA (i.e. they
        # are absent from the tree) — this is incomplete sampling, kept
        # distinct from topological polyphyly (C2).
        status = "incomplete_sampling"
    elif extra_nodes and has_taxonomy_mapping:
        # Step 4-5: L ⊃ S, need to check if L\S all belong to G
        # Distinguish between:
        #   - extra node mapped to same group -> monophyletic (nested subgroup)
        #   - extra node mapped to DIFFERENT group -> paraphyletic
        #   - extra node NOT in mapping (incomplete taxonomy) -> paraphyletic (conservative)
        assert tip_to_group is not None, "has_taxonomy_mapping implies tip_to_group is not None"  # noqa: S101
        extras_in_same_group = []
        extras_in_diff_group = []
        extras_unmapped = []
        for tip in extra_nodes:
            mapped_group = tip_to_group.get(tip)
            if mapped_group is None:
                extras_unmapped.append(tip)
            elif mapped_group == group_name:
                extras_in_same_group.append(tip)
            else:
                extras_in_diff_group.append(tip)

        if not extras_in_diff_group and not extras_unmapped:
            # Step 4: L⊃S and all L\S in G -> monophyletic (nested subgroup)
            status = "monophyletic"
        elif extras_in_diff_group:
            # Step 5 (C1): classify paraphyly vs polyphyly strictly by the
            # phylogenetic definitions, independent of group names.
            # See the docstring of _classify_paraphyletic_vs_polyphyletic.
            status = _classify_paraphyletic_vs_polyphyletic(lca, member_set)
        else:
            # Only unmapped extras: taxonomy data is incomplete for these nodes.
            # Cannot determine if they belong to the same group or a different one.
            # Return 'data_insufficient' rather than assuming paraphyletic.
            status = "data_insufficient"
    elif extra_nodes:
        # No taxonomy mapping available: still classify paraphyly vs
        # polyphyly strictly by the definitions (C1), purely on topology.
        status = _classify_paraphyletic_vs_polyphyletic(lca, member_set)
    else:
        status = "paraphyletic"

    subgroups_str = ""
    if status == "polyphyletic":
        subgroups = _find_subgroups(tree, members)
        subgroups_str = "; ".join(
            f"{i}:LCA={sg['lca']},members={','.join(sorted(sg['members']))}" for i, sg in enumerate(subgroups)
        )

    return {
        "group": group_name,
        "status": status,
        "lca_node": lca_label,
        "member_count": len(members),
        "extra_nodes": "|".join(sorted(extra_nodes)) if extra_nodes else "",
        "missing_nodes": "|".join(sorted(missing_nodes)) if missing_nodes else "",
        "subgroups": subgroups_str,
        "extra_count": len(extra_nodes),
        "missing_count": len(missing_nodes),
        "polytomy_details": "",
    }


def _find_subgroups(tree: dendropy.Tree, node_ids: list[str]) -> list[dict]:
    """Decompose a polyphyletic group into maximal monophyletic subgroups.

    For polyphyletic groups, partitions the group members into subgroups based
    on their topological distribution, helping users understand the actual
    spread of the group and providing actionable boundaries for taxonomic
    revision.

    A subgroup is monophyletic iff its member set equals the full leaf set of
    its LCA, i.e. it is the leaf set of some tree node containing only group
    members.  The maximal such clades are therefore exactly the maximal
    monophyletic subgroups: they are mutually disjoint, cover every member,
    and form the unique minimum-cardinality partition into monophyletic
    subgroups.  They are collected in a single deterministic post-order pass
    (no seed selection, no greedy heuristics).

    Time complexity: O(n) per group (two tree traversals), independent of the
    number of members k.  An earlier greedy MRCA-expansion implementation was
    O(k^2 * n) per seed in the worst case and could both fragment genuine
    clades (subgroups degraded into singletons) and depend on seed order; it
    was replaced by this pass after the simulation-based accuracy evaluation
    of the accompanying manuscript exposed both defects.
    """
    if len(node_ids) <= 1:
        lca_label = "N/A"
        if node_ids:
            node = _find_tip_node(tree, node_ids[0])
            if node and node.taxon:
                lca_label = node.taxon.label
        return [{"lca": lca_label, "members": set(node_ids)}]

    # Clear stale cache entries for this tree to avoid namespace conflicts
    clear_tip_index_cache(tree)

    # Pre-compute all tip nodes to avoid repeated lookups
    tip_node_map: dict[str, dendropy.Node | None] = {}
    for nid in node_ids:
        tip_node_map[nid] = _find_tip_node(tree, nid)

    # Filter out invalid nodes and collect member tip labels
    member_labels: set[str] = set()
    for nid in node_ids:
        node = tip_node_map[nid]
        if node is not None and node.taxon is not None:
            member_labels.add(node.taxon.label)
    if not member_labels:
        return []

    # Single post-order pass: leaf counts and member counts per node.
    leaf_count: dict[dendropy.Node, int] = {}
    member_count: dict[dendropy.Node, int] = {}
    for node in tree.postorder_node_iter():
        if node.is_leaf():
            leaf_count[node] = 1
            member_count[node] = int(node.taxon is not None and node.taxon.label in member_labels)
        else:
            children = node.child_nodes()
            leaf_count[node] = sum(leaf_count[c] for c in children)
            member_count[node] = sum(member_count[c] for c in children)

    # Collect maximal clades whose leaves are all group members.  A clade is
    # maximal iff its parent (if any) is not itself member-pure.
    subgroups: list[dict] = []
    for node in tree.postorder_node_iter():
        if member_count[node] == 0 or member_count[node] < leaf_count[node]:
            continue
        parent = node.parent_node
        if parent is not None and member_count[parent] == leaf_count[parent]:
            continue
        members = {
            leaf.taxon.label
            for leaf in node.leaf_iter()
            if leaf.taxon is not None and leaf.taxon.label in member_labels
        }
        label = node.taxon.label if node.taxon else f"internal_{node.level()}"
        subgroups.append({"lca": label, "members": members})

    return subgroups
