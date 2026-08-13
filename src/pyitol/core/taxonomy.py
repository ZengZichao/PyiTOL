"""Taxonomy analysis module - classification extraction and style config."""

from __future__ import annotations

import logging
import re
from pathlib import Path

import dendropy
import pandas as pd

from pyitol.core.monophyly import (
    _find_tip_node,
    _get_lca_label,
    check_monophyly,  # noqa: F401
    check_monophyly_with_taxa_list,  # noqa: F401
)
from pyitol.core.parser import detect_tree_schema
from pyitol.exceptions import MetadataParseError

logger = logging.getLogger(__name__)


def _get_tip_labels(tree: dendropy.Tree) -> set[str]:
    """Get all tip labels from a tree."""
    return {t.taxon.label for t in tree.leaf_nodes() if t.taxon}


# Default taxonomy level configuration: prefix -> (rank_name, order)
_DEFAULT_LEVELS = {
    "d": ("Domain", 0),
    "k": ("Kingdom", 1),
    "p": ("Phylum", 2),
    "c": ("Class", 3),
    "o": ("Order", 4),
    "f": ("Family", 5),
    "g": ("Genus", 6),
    "s": ("Species", 7),
}

# GTDB-style prefix mapping: d__ = domain, p__ = phylum, c__ = class, etc.
_GTDB_PREFIX_MAP = {f"{k}__": v[0] for k, v in _DEFAULT_LEVELS.items()}

# Standard rank order
RANK_ORDER = ["Domain", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]

# Pre-compiled regex for embedded format: _X_ where X is a single letter
_EMBEDDED_MARKER_RE = re.compile(r"_(d|k|p|c|o|f|g|s)_")


def parse_taxonomy_levels_config(levels_str: str | None) -> dict[str, tuple[str, int]]:
    """Parse custom taxonomy levels configuration string.

    Format: "d:Domain,k:Kingdom,p:Phylum,c:Class,o:Order,f:Family,g:Genus,s:Species"
    Or shorthand: "d,p,c,o,f,g,s" (uses default rank names)

    Args:
        levels_str: Custom levels string, or None for defaults

    Returns:
        Dict mapping prefix -> (rank_name, order)
    """
    if not levels_str:
        return dict(_DEFAULT_LEVELS)

    result = {}
    for i, part in enumerate(levels_str.split(",")):
        part = part.strip()
        if ":" in part:
            prefix, rank_name = part.split(":", 1)
            prefix = prefix.strip().lower()
            rank_name = rank_name.strip()
        else:
            prefix = part.strip().lower()
            # Use default name if available
            rank_name = _DEFAULT_LEVELS[prefix][0] if prefix in _DEFAULT_LEVELS else prefix.capitalize()
        result[prefix] = (rank_name, i)

    return result


def parse_taxonomy_string(
    tax_string: str,
    levels: dict[str, tuple[str, int]] | None = None,
    delimiter_mode: str = "segment",
) -> dict:
    """Unified taxonomy string parser - auto-detects Format A and Format B.

    Format A (embedded): <accession>_d_Bacteria_p_Cyanobacteriota_c_..._g_Genus
        - Markers: _X_ where X is d/k/p/c/o/f/g/s
        - Values between markers, missing markers = None

    Format B (semicolon): d__Archaea;p__Thermoproteota;c__Korarchaeia;...
        - Markers: X__ where X is d/k/p/c/o/f/g/s
        - Semicolon-separated, empty values (s__) = None

    Returns dict with standard rank names as keys. Missing values are None.
    For Format A, also includes 'accession' key with the prefix before first marker.

    Args:
        tax_string: Taxonomy string in either format
        levels: Custom level config (prefix -> (rank_name, order)), None for defaults
        delimiter_mode: Parsing strategy for Format A: 'segment' (default),
            'reverse' (strict right-to-left), or 'greedy' (from first _d_)

    Returns:
        Dict with rank names as keys, values as strings or None for missing
    """
    if levels is None:
        levels = _DEFAULT_LEVELS

    # Auto-detect format
    if _is_embedded_format(tax_string):
        return _parse_embedded_unified(tax_string, levels, delimiter_mode=delimiter_mode)
    elif _is_gtdb_format(tax_string):
        return _parse_gtdb_unified(tax_string, levels)
    else:
        # Fallback: return empty
        logger.debug(f"Could not detect taxonomy format: {tax_string[:50]}")
        return {}


def _is_embedded_format(s: str) -> bool:
    """Check if string uses embedded format (_X_ markers)."""
    return bool(re.search(r"_(d|k|p|c|o|f|g|s)_", s))


def _is_gtdb_format(s: str) -> bool:
    """Check if string uses GTDB format (X__ prefixes with semicolons)."""
    return bool(re.search(r"(d|k|p|c|o|f|g|s)__\w", s))


def _parse_embedded_unified(
    tip: str,
    levels: dict[str, tuple[str, int]],
    delimiter_mode: str = "segment",
) -> dict:
    """Parse embedded format with unified structure.

    Format: <accession>_d_<domain>_p_<phylum>_c_<class>_o_<order>_f_<family>_g_<genus>

    Missing levels are set to None.

    Args:
        tip: Tip label string with embedded taxonomy markers
        levels: Dict mapping prefix -> (rank_name, order)
        delimiter_mode: Parsing strategy for ambiguous names:
            - 'segment': Forward regex matching (default, current behavior)
            - 'reverse': Right-to-left strict reverse order (g→f→o→c→p→d)
            - 'greedy': Extract from first _d_ marker to end of string
    """
    result: dict[str, str | None] = {}

    # Build prefix-to-rank mapping from levels config
    prefix_to_rank = {k: v[0] for k, v in levels.items()}

    # Find positions of all rank markers
    marker_positions = []
    for match in _EMBEDDED_MARKER_RE.finditer(tip):
        marker_positions.append((match.start(), match.group(1), match.end()))

    if not marker_positions:
        return result

    # Accession is everything before the first marker
    result["accession"] = tip[: marker_positions[0][0]]

    # Initialize all ranks as None
    for _prefix, (rank_name, _) in levels.items():
        result[rank_name] = None

    if delimiter_mode == "reverse":
        # Reverse mode: validate strict reverse order (g, f, o, c, p, d)
        # Markers must appear in strict reverse rank order from right to left
        sorted_levels = sorted(levels.items(), key=lambda x: x[1][1])  # by order
        expected_reverse = [prefix for prefix, _ in reversed(sorted_levels)]

        # Check if markers appear in strict reverse order
        found_markers = [m[1] for m in marker_positions]
        # Build the expected sequence from found markers
        is_strict_reverse = True
        for i, marker_key in enumerate(found_markers):
            if i < len(expected_reverse) and marker_key != expected_reverse[i]:
                is_strict_reverse = False
                break

        if not is_strict_reverse:
            logger.warning(
                f"Embedded taxonomy markers not in strict reverse order: {tip[:80]}. "
                f"Falling back to greedy extraction from first _d_ marker."
            )
            delimiter_mode = "greedy"

    if delimiter_mode == "greedy":
        # Greedy mode: extract from first _d_ marker to end, then parse segments
        first_d_match = re.search(r"_d_", tip)
        if first_d_match:
            # Split by markers to get values
            markers_in_tax = list(_EMBEDDED_MARKER_RE.finditer(tip[first_d_match.start() :]))
            if markers_in_tax:
                result["accession"] = tip[: first_d_match.start()]
                for i, m in enumerate(markers_in_tax):
                    rank_key = m.group(1)
                    rank_name_val = prefix_to_rank.get(rank_key)
                    if not rank_name_val:
                        continue
                    val_start = first_d_match.start() + m.end()
                    if i + 1 < len(markers_in_tax):
                        val_end = first_d_match.start() + markers_in_tax[i + 1].start()
                    else:
                        val_end = len(tip)
                    value = tip[val_start:val_end].strip()
                    result[rank_name_val] = value if value else None
            return result
        else:
            # No _d_ found, fall back to segment
            delimiter_mode = "segment"

    # Segment mode (default): forward regex matching
    # Extract value between each marker end and the next marker start
    for i, (start, rank_key, value_start) in enumerate(marker_positions):
        rank_name_val = prefix_to_rank.get(rank_key)
        if not rank_name_val:
            logger.debug(f"Unknown rank marker: _{rank_key}_ at position {start}")
            continue
        value_end = marker_positions[i + 1][0] if i + 1 < len(marker_positions) else len(tip)
        value = tip[value_start:value_end].strip()
        result[rank_name_val] = value if value else None

    return result


def _parse_gtdb_unified(
    tax_string: str,
    levels: dict[str, tuple[str, int]],
) -> dict:
    """Parse GTDB semicolon format with unified structure.

    Format: d__Domain;p__Phylum;c__Class;o__Order;f__Family;g__Genus;s__

    Empty values (like s__) are set to None.
    Missing prefixes are also set to None.
    """
    result: dict[str, str | None] = {}

    # Build prefix-to-rank mapping from levels config
    prefix_to_rank = {f"{k}__": v[0] for k, v in levels.items()}

    # Initialize all ranks as None
    for rank_name, _ in levels.values():
        result[rank_name] = None

    # Parse each semicolon-separated part
    found_prefixes = set()
    parts = tax_string.split(";")
    for part in parts:
        part = part.strip()
        if not part:
            continue

        for prefix, rank_name in prefix_to_rank.items():
            if part.startswith(prefix):
                found_prefixes.add(prefix)
                value = part[len(prefix) :]
                result[rank_name] = value if value else None
                if not value:
                    logger.debug(f"Empty value for rank {rank_name} ({prefix}): {part}")
                break

    return result


def _parse_embedded_taxonomy(tip: str) -> dict:
    """Parse a tip name with embedded taxonomy markers like _d_Bacteria_p_Proteo...

    Format: <accession>_d_<domain>_p_<phylum>_c_<class>_o_<order>_f_<family>_g_<genus>
    Example: GB_GCA_000252485.1_d_Bacteria_p_Cyanobacteriota_c_Cyanobacteriia_o_Cyanobacteriales_f_Prochloraceae_g_Prochloron

    Returns dict with rank names as keys and taxonomy values as values.
    The accession portion (before the first rank marker) is returned as 'accession'.
    """  # noqa: E501
    _marker_to_rank = {
        "d": "Domain",
        "k": "Kingdom",
        "p": "Phylum",
        "c": "Class",
        "o": "Order",
        "f": "Family",
        "g": "Genus",
        "s": "Species",
    }
    result: dict[str, str | None] = {}

    # Find positions of all rank markers (_X_ where X is d/k/p/c/o/f/g/s)
    marker_positions = []
    for match in re.finditer(r"_(d|k|p|c|o|f|g|s)_", tip):
        marker_positions.append((match.start(), match.group(1), match.end()))

    if not marker_positions:
        return result

    # Accession is everything before the first marker
    result["accession"] = tip[: marker_positions[0][0]]

    # Extract value between each marker end and the next marker start (or end of string)
    for i, (_start, rank_key, value_start) in enumerate(marker_positions):
        rank_name = _marker_to_rank.get(rank_key)
        if not rank_name:
            continue
        value_end = marker_positions[i + 1][0] if i + 1 < len(marker_positions) else len(tip)
        value = tip[value_start:value_end].strip()
        if value:
            result[rank_name] = value

    return result


def parse_gtdb_taxonomy_string(tax_string: str) -> dict:
    """Parse a GTDB-style taxonomy string into a dict of rank -> value.

    Format: d__Domain;p__Phylum;c__Class;o__Order;f__Family;g__Genus;s__Species
    Example: d__Archaea;p__Thermoproteota;c__Korarchaeia;o__Korarchaeales;f__Korarchaeaceae;g__WALU01;s__

    Empty values (like s__ with nothing after the prefix) are skipped.
    Missing values (no prefix present at all) are not included in the result.

    Args:
        tax_string: GTDB-style semicolon-separated taxonomy string

    Returns:
        Dict mapping rank names (Domain, Phylum, etc.) to their values
    """
    result = {}
    parts = tax_string.split(";")
    for part in parts:
        part = part.strip()
        for prefix, rank_name in _GTDB_PREFIX_MAP.items():
            if part.startswith(prefix):
                value = part[len(prefix) :]
                if value:  # Skip empty values like 's__'
                    result[rank_name] = value
                break
    return result


def extract_taxonomy_from_tip_names(
    tree_path: str | Path,
    output_path: str | Path | None = None,
    name_format: str = "auto",
    delimiter: str = "_",
    taxonomy_levels: str | None = None,
    delimiter_mode: str = "segment",
) -> pd.DataFrame:
    """Extract taxonomy information directly from tree tip names.

    Supports multiple naming conventions:
    - GTDB (Format B): d__Bacteria;p__Proteobacteria;...;s__Escherichia_coli
    - Embedded (Format A): <accession>_d_Bacteria_p_Proteo_c_... (rank markers embedded in name)
    - Mixed: tips may use either format (auto-detected per tip)
    - NCBI: Genus_species (extracts Genus as genus rank)
    - auto: auto-detect format

    Args:
        tree_path: Path to the tree file
        output_path: Optional path to save the taxonomy CSV
        name_format: 'auto', 'gtdb', 'embedded', 'ncbi', or 'underscore'
        delimiter: Delimiter for splitting names (default '_')
        taxonomy_levels: Custom level config string (e.g., "d:Domain,p:Phylum,...")
        delimiter_mode: Parsing strategy for embedded format: 'segment' (default),
            'reverse' (strict right-to-left), or 'greedy' (from first _d_)

    Returns:
        DataFrame with columns: id, and detected rank columns
    """
    levels = parse_taxonomy_levels_config(taxonomy_levels)

    schema = detect_tree_schema(tree_path)
    tree = dendropy.Tree.get_from_path(str(tree_path), schema=schema, preserve_underscores=True)
    tips = sorted([t.taxon.label for t in tree.leaf_nodes() if t.taxon])

    if not tips:
        raise MetadataParseError("No tip labels found in tree")

    # Auto-detect format
    if name_format == "auto":
        # Sample first few tips to detect format
        sample = tips[: min(10, len(tips))]
        embedded_count = sum(1 for t in sample if _is_embedded_format(t))
        gtdb_count = sum(1 for t in sample if _is_gtdb_format(t))

        if gtdb_count > embedded_count and gtdb_count > 0:
            name_format = "gtdb"
        elif embedded_count > 0:
            name_format = "embedded"
        elif any("_" in t for t in sample):
            name_format = "ncbi"
        else:
            name_format = "ncbi"

    # Build rank names from levels config
    rank_names = [v[0] for v in sorted(levels.values(), key=lambda x: x[1])]

    rows = []
    if name_format in ("gtdb", "embedded", "mixed"):
        # Unified parsing for Format A and Format B (and mixed)
        for tip in tips:
            row = {"id": tip}
            parsed = parse_taxonomy_string(tip, levels, delimiter_mode=delimiter_mode)
            for rank_name, value in parsed.items():
                if rank_name != "accession" and value is not None:
                    row[rank_name] = value
            rows.append(row)
    else:
        # NCBI/underscore format: Genus_species or Family_Genus_species etc.
        # P2-26: Properly extract ranks from right to left
        # Convention: last=species epithet, second-to-last=Genus,
        # third-to-last=Family, fourth-to-last=Order, etc.
        _ncbi_ranks = ["Species", "Genus", "Family", "Order", "Class", "Phylum"]
        for tip in tips:
            row = {"id": tip}
            parts = tip.split(delimiter)
            if len(parts) >= 2:
                # P1-xx: `Species` must be the species epithet (e.g. 'sapiens'),
                # not the full binomial (e.g. 'Homo_sapiens'). `Genus` already holds
                # the genus part (parts[-2]).
                row["Species"] = parts[-1]
                row["Genus"] = parts[-2] if len(parts) >= 2 else parts[0]
                # Assign ranks right-to-left: parts[-2]=Genus, parts[-3]=Family, ...
                for rank_idx, rank_name in enumerate(_ncbi_ranks[1:], start=1):  # skip Species
                    part_idx = -(rank_idx + 1)  # -2 for Genus, -3 for Family, ...
                    if abs(part_idx) <= len(parts):
                        row[rank_name] = parts[part_idx]
            elif len(parts) == 1:
                row["Genus"] = parts[0]
            rows.append(row)

    df = pd.DataFrame(rows)

    # Reorder columns: id first, then ranks in order
    ordered_cols = ["id"] + [c for c in rank_names if c in df.columns]
    other_cols = [c for c in df.columns if c not in ordered_cols and c != "id"]
    df = df[ordered_cols + other_cols]

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)

    return df


def _normalize_taxonomy_df(df: pd.DataFrame, id_column: str = "id") -> pd.DataFrame:
    """Normalize a taxonomy DataFrame, auto-detecting 2-column GTDB compact format.

    If the DataFrame has exactly 2 columns (after renaming the id column) and the
    second column contains GTDB-style semicolon-separated taxonomy strings, parse
    them into individual rank columns.

    Args:
        df: Raw DataFrame read from CSV
        id_column: Name of the ID column

    Returns:
        Normalized DataFrame with 'id' and individual rank columns
    """
    # Rename id column if needed
    first_col = df.columns[0]
    if id_column in df.columns and id_column != "id":
        df = df.rename(columns={id_column: "id"})
    elif first_col != "id" and first_col.lower() in ("id", "name", "tip", "leaf", "node"):
        df = df.rename(columns={first_col: "id"})

    # Detect two-column GTDB compact format
    non_id_cols = [c for c in df.columns if c != "id"]
    if len(non_id_cols) == 1:
        second_col = non_id_cols[0]
        sample = df[second_col].dropna().head(5).astype(str)
        if any(";" in str(v) and any(v.startswith(p) or (";" + p) in v for p in _GTDB_PREFIX_MAP) for v in sample):
            parsed_rows = []
            for _, row in df.iterrows():
                tip_id = str(row["id"])
                tax_str = str(row[second_col])
                parsed = parse_gtdb_taxonomy_string(tax_str)
                parsed["id"] = tip_id
                parsed_rows.append(parsed)
            df = pd.DataFrame(parsed_rows)

    # Reorder columns
    rank_order = ["Domain", "Kingdom", "Phylum", "Class", "Order", "Family", "Genus", "Species"]
    ordered_cols = ["id"] + [c for c in rank_order if c in df.columns]
    other_cols = [c for c in df.columns if c not in ordered_cols and c != "id"]
    if "id" in df.columns:
        df = df[ordered_cols + other_cols]

    return df


def get_ranks(taxonomy_path: str | Path, id_column: str = "id") -> list[str]:
    """Get available taxonomy rank columns from a table."""
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", nrows=10, dtype=str)
    df = _normalize_taxonomy_df(df, id_column)
    ranks = [c for c in df.columns if c != "id"]
    return ranks


def extract_taxonomy_ranks(taxonomy_path: str | Path) -> list[str]:
    """Auto-detect taxonomy rank columns from a table."""
    df = pd.read_csv(taxonomy_path, sep=None, engine="python", nrows=1)
    known_ranks = {
        "domain",
        "kingdom",
        "phylum",
        "class",
        "order",
        "family",
        "genus",
        "species",
        "strain",
        "superkingdom",
        "subspecies",
        "varietas",
        "forma",
        "clade",
        "group",
        "subgroup",
        # Extended NCBI Taxonomy ranks
        "superphylum",
        "subphylum",
        "infraphylum",
        "parvphylum",
        "superclass",
        "subclass",
        "infraclass",
        "parvclass",
        "superorder",
        "suborder",
        "infraorder",
        "parvorder",
        "superfamily",
        "subfamily",
        "infrafamily",
        "tribe",
        "subtribe",
        "subgenus",
        "section",
        "subsection",
        "series",
        "species group",
        "species subgroup",
    }
    ranks = []
    for col in df.columns:
        if col.lower().strip() in known_ranks:
            ranks.append(col)
    if not ranks:
        ranks = list(df.columns)
        if "id" in ranks or "ID" in ranks:
            ranks = [c for c in ranks if c not in ("id", "ID")]
    return ranks


def extract_taxonomy(
    taxonomy_path: str | Path,
    tree_path: str | Path,
    rank: str,
    id_column: str = "id",
    multi_tree: str = "error",
) -> list[dict]:
    """Extract taxonomy information at a specified rank level.

    Returns list of dicts with 'id' and 'name' keys for each tip.
    """
    from pyitol.core.parser import get_single_tree

    tree = get_single_tree(tree_path, multi_tree=multi_tree)
    tip_set = _get_tip_labels(tree)

    tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    tax_df = _normalize_taxonomy_df(tax_df, id_column)

    tax_df["id"] = tax_df["id"].astype(str)
    tax_df = tax_df[tax_df["id"].isin(tip_set)]

    if rank not in tax_df.columns:
        raise MetadataParseError(f"Rank column '{rank}' not found. Available: {list(tax_df.columns)}")

    results = []
    for _, row in tax_df.iterrows():
        results.append({"id": row["id"], "name": str(row[rank])})

    return results


def extract_taxonomy_with_stats(
    taxonomy_path: str | Path,
    tree_path: str | Path,
    rank: str,
    output_path: str | Path,
    id_column: str = "id",
    multi_tree: str = "error",
) -> pd.DataFrame:
    """Extract taxonomy information with LCA and member statistics.

    Groups tip nodes by the specified taxonomy rank and outputs class lists
    with member IDs, tip counts, and LCA node info.
    """
    from pyitol.core.parser import get_single_tree

    tree = get_single_tree(tree_path, multi_tree=multi_tree)
    tip_set = _get_tip_labels(tree)

    tax_df = pd.read_csv(taxonomy_path, sep=None, engine="python", dtype=str)
    tax_df = _normalize_taxonomy_df(tax_df, id_column)

    tax_df["id"] = tax_df["id"].astype(str)
    tax_df = tax_df[tax_df["id"].isin(tip_set)]

    if rank not in tax_df.columns:
        raise MetadataParseError(f"Rank column '{rank}' not found in taxonomy table. Available: {list(tax_df.columns)}")

    results = []
    for group_name, group_df in tax_df.groupby(rank):
        members = group_df["id"].tolist()

        tip_nodes = []
        for m in members:
            node = _find_tip_node(tree, m)
            if node:
                tip_nodes.append(node)

        lca_label = _get_lca_label(tree, tip_nodes)

        results.append(
            {
                "rank": rank,
                "group": group_name,
                "member_count": len(members),
                "lca_node": lca_label,
                "members": "|".join(sorted(members)),
            }
        )

    result_df = pd.DataFrame(results)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(output_path, index=False)
    return result_df
