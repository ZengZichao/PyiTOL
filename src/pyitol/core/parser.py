"""Tree file and metadata parser module."""

from __future__ import annotations

import contextlib
import logging
import re
import sys
from pathlib import Path

import dendropy
import pandas as pd

from pyitol.exceptions import MetadataParseError, TreeParseError
from pyitol.utils.io import safe_read_text

logger = logging.getLogger(__name__)


def _detect_schema_core(content: str, ext: str | None = None) -> str:
    """Internal helper: detect tree schema ('nexus' or 'newick') from raw content.

    Single source of truth shared by :func:`detect_tree_schema` and
    :meth:`TreeParser._detect_schema` so the two implementations can never diverge.

    Args:
        content: Raw file content (used for the '#NEXUS' magic-byte detection).
            May be empty.
        ext: Optional lower-cased file extension (e.g. '.nexus'); when present and
            matches a known Nexus extension, forces 'nexus'.

    Returns:
        'nexus' or 'newick'.
    """
    upper = content[:200].strip().upper()
    if upper.startswith("#NEXUS") or "#NEXUS" in upper[:100]:
        return "nexus"
    if ext is not None and ext.lower() in {".nexus", ".nex", ".treex"}:
        return "nexus"
    return "newick"


def detect_tree_schema(tree_path: Path | str) -> str:
    """Auto-detect tree file format from content and extension.

    m2: Shared utility to avoid duplicating schema detection logic.

    Args:
        tree_path: Path to the tree file

    Returns:
        'nexus' or 'newick'
    """
    tree_path = Path(tree_path)
    try:
        content = safe_read_text(tree_path)
    except Exception:
        content = ""
    ext = tree_path.suffix
    return _detect_schema_core(content, ext)


def count_trees_in_file(tree_path: Path | str) -> int:
    """Count the number of trees in a tree file.

    For Nexus files: counts 'tree' statements in TREES block.
    For Newick files: counts top-level parenthesized expressions.

    Args:
        tree_path: Path to the tree file

    Returns:
        Number of trees found
    """
    tree_path = Path(tree_path)
    schema = detect_tree_schema(tree_path)

    if schema == "nexus":
        return _count_nexus_trees(tree_path)
    else:
        return _count_newick_trees(tree_path)


def _count_nexus_trees(tree_path: Path) -> int:
    """Count trees in a Nexus file."""
    try:
        content = safe_read_text(tree_path)
        # Count 'tree' statements (case-insensitive)
        tree_statements = re.findall(r"^\s*tree\s+", content, re.MULTILINE | re.IGNORECASE)
        return len(tree_statements)
    except Exception as e:
        raise TreeParseError(f"Failed to count trees in Nexus file: {tree_path}") from e


def _count_newick_trees(tree_path: Path) -> int:
    """Count trees in a Newick file.

    A Newick tree ends with ';'. Multiple trees are separated by ';'
    possibly with whitespace/newlines between them.
    """
    try:
        content = safe_read_text(tree_path).strip()
        if not content:
            return 0

        # Count semicolons that terminate tree expressions
        # A valid Newick tree must have balanced parentheses and end with ';'.
        # NHX annotations are wrapped in '[' ... ']'; characters inside comments
        # (which may contain ';' or unbalanced parentheses) must be ignored so
        # they are not mistaken for tree terminators or depth changes.
        count = 0
        depth = 0
        comment_depth = 0
        in_quote = False
        for char in content:
            # Newick quoted labels (single quotes, '' escapes a quote) may
            # legally contain '[' , ']' , '(' , ')' , ';'.  Treat any such
            # character inside a quote as literal so it does not start/end a
            # comment or alter parenthesis depth.
            if char == "'":
                in_quote = not in_quote
                continue
            if in_quote:
                continue
            if char == "[":
                comment_depth += 1
            elif char == "]":
                if comment_depth > 0:
                    comment_depth -= 1
            elif comment_depth > 0:
                # Inside a comment: ignore tree-structure characters.
                continue
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            elif char == ";" and depth == 0:
                count += 1

        return count
    except Exception as e:
        raise TreeParseError(f"Failed to count trees in Newick file: {tree_path}") from e


def _check_large_tree(tree: dendropy.Tree, threshold: int = 10000) -> None:
    """Check if tree is large and log resource requirements."""
    tip_count = len(tree.leaf_nodes())
    if tip_count > threshold:
        logger.info(
            f"Large tree detected: {tip_count} tips. "
            f"May require significant memory and CPU time. "
            f"Consider using --low-memory mode for constrained environments."
        )
        # Try to log memory usage if psutil is available
        try:
            import psutil

            process = psutil.Process()
            mem_mb = process.memory_info().rss / 1024 / 1024
            logger.debug(f"Memory usage before processing: {mem_mb:.1f} MB")
        except ImportError:
            logger.debug("psutil not available, skipping memory usage logging")


def load_tree(
    tree_path: Path | str,
    multi_tree: str = "ask",
    tree_index: int | None = None,
) -> dendropy.Tree | list[dendropy.Tree]:
    """Load a tree file with multi-tree handling.

    Args:
        tree_path: Path to the tree file
        multi_tree: Strategy for multi-tree files:
            - 'ask' (default): prompt user and exit with code 2
            - 'first': use only the first tree
            - 'last': use only the last tree
            - 'split'/'all': return list of all trees for separate processing

            Note: the project maintains deterministic behavior; there is no
            'random' strategy.
        tree_index: If specified, load only the tree at this 0-based index.
            Overrides multi_tree strategy.

    Returns:
        Single Tree object, or list of Trees if multi_tree='split'/'all'

    Raises:
        TreeParseError: If file not found, empty, or multi-tree with 'ask' strategy
    """
    tree_path = Path(tree_path)
    if not tree_path.exists():
        raise TreeParseError(f"Tree file not found: {tree_path}")

    schema = detect_tree_schema(tree_path)

    # If explicit index requested, load that specific tree
    if tree_index is not None:
        trees = _load_all_trees(tree_path, schema)
        if tree_index >= len(trees):
            raise TreeParseError(f"Tree index {tree_index} out of range. File contains {len(trees)} tree(s).")
        return trees[tree_index]

    # Count trees
    tree_count = count_trees_in_file(tree_path)

    if tree_count == 1:
        content = safe_read_text(tree_path)
        try:
            tree = dendropy.Tree.get_from_string(content, schema=schema, preserve_underscores=True)
        except Exception as e:
            raise TreeParseError(f"Failed to parse tree file {tree_path}: {e}") from e
        _check_large_tree(tree)
        return tree

    # Multiple trees detected - log summary
    trees = _load_all_trees(tree_path, schema)
    logger.warning(f"Detected {tree_count} trees in file. Tree summaries:")
    for i, tree in enumerate(trees):
        tips = [n.taxon.label for n in tree.leaf_nodes() if n.taxon]
        internal_count = len(list(tree.internal_nodes()))
        logger.warning(
            f"  Tree #{i + 1}: {len(tips)} tips, {internal_count} internal nodes, first tips: {', '.join(tips[:3])}"
        )

    # Apply strategy
    if multi_tree == "ask":
        if not sys.stdin.isatty():
            logger.warning(f"检测到树文件中包含 {tree_count} 棵树，当前处于非交互环境，自动回退到 'first' 策略。")
            multi_tree = "first"
        else:
            raise TreeParseError(
                f"检测到树文件中包含 {tree_count} 棵树。默认模式仅处理单棵树文件。\n"
                f"请使用 --multi-tree-mode 参数选择处理策略:\n"
                f"  first  - 仅使用第一棵树\n"
                f"  last   - 仅使用最后一棵树\n"
                f"  split  - 分别处理所有树，结果添加数字后缀\n"
                f"示例: --multi-tree-mode first"
            )

    if multi_tree == "first":
        logger.info(f"Multi-tree file ({tree_count} trees), using first tree")
        return trees[0]
    elif multi_tree == "last":
        logger.info(f"Multi-tree file ({tree_count} trees), using last tree")
        return trees[-1]
    elif multi_tree in ("split", "all"):
        logger.info(f"Multi-tree file ({tree_count} trees), returning all trees")
        return trees
    else:
        raise TreeParseError(f"Unknown multi-tree strategy: {multi_tree}")


def _load_all_trees(tree_path: Path, schema: str) -> list[dendropy.Tree]:
    """Load all trees from a file."""
    try:
        content = safe_read_text(tree_path)
        if schema == "nexus":
            # Nexus content may contain multiple trees in a single block;
            # dendropy can parse the whole string.
            trees = list(
                dendropy.Tree.yield_from_files(
                    files=[str(tree_path)],
                    schema=schema,
                    preserve_underscores=True,
                )
            )
        else:
            # Split top-level Newick statements on ';' while preserving nested
            # parentheses. Each valid tree ends with ';' at depth 0.
            trees = []
            depth = 0
            comment_depth = 0
            in_quote = False
            start = 0
            for i, ch in enumerate(content):
                # Newick quoted labels (single quotes) may contain '[', ']',
                # '(', ')', ';'.  Treat them as literal inside quotes so they do
                # not start/end a comment or change parenthesis depth.
                if ch == "'":
                    in_quote = not in_quote
                    continue
                if in_quote:
                    continue
                if ch == "[":
                    comment_depth += 1
                elif ch == "]":
                    if comment_depth > 0:
                        comment_depth -= 1
                elif comment_depth > 0:
                    # Inside an NHX/Newick comment: ignore tree-structure chars.
                    continue
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                elif ch == ";" and depth == 0:
                    stmt = content[start : i + 1].strip()
                    if stmt:
                        trees.append(dendropy.Tree.get_from_string(stmt, schema=schema, preserve_underscores=True))
                    start = i + 1
        if not trees:
            raise TreeParseError(f"No trees found in file: {tree_path}")
        return trees
    except TreeParseError:
        raise
    except Exception as e:
        raise TreeParseError(f"Failed to parse tree file {tree_path}: {e}") from e


def get_single_tree(
    tree_path: Path | str,
    multi_tree: str = "ask",
    tree_index: int | None = None,
) -> dendropy.Tree:
    """Load a single tree from a file, enforcing single-tree constraint.

    This is the primary function for commands that expect exactly one tree.

    Args:
        tree_path: Path to the tree file
        multi_tree: Strategy for multi-tree files
        tree_index: Optional specific tree index to load

    Returns:
        Single Tree object

    Raises:
        TreeParseError: If multi-tree with 'error' strategy or file issues
    """
    result = load_tree(tree_path, multi_tree=multi_tree, tree_index=tree_index)
    if isinstance(result, list):
        # Should not happen with non-'all' strategies, but handle gracefully
        if multi_tree == "all":
            raise TreeParseError(
                "get_single_tree() called but multi_tree='all'. Use load_tree() directly for multi-tree processing."
            )
        return result[0]
    return result


def _get_node_label(node: dendropy.Node) -> str:
    """Get label from a node (DendroPy v5 API)."""
    if node.taxon is not None:
        return node.taxon.label
    return ""


def _get_tip_label(tip: dendropy.Node) -> str:
    """Get label from a tip node."""
    if tip.taxon is not None:
        return tip.taxon.label
    return ""


class TreeParser:
    """Parser for phylogenetic tree files."""

    SUPPORTED_EXTENSIONS = {".nwk", ".newick", ".nexus", ".nex", ".tree", ".treefile", ".tre", ".treex"}  # noqa: RUF012

    def __init__(self, tree_path: str | Path | None = None) -> None:
        self.tree: dendropy.Tree | None = None
        self.tree_path: Path | None = Path(tree_path) if tree_path else None
        self.tip_labels: list[str] = []
        self.node_labels: list[str] = []
        self.has_branch_lengths: bool = False
        self.support_values: dict[object, float] = {}
        if self.tree_path:
            if self.tree_path.exists():
                self.parse_auto()
            else:
                logger.warning("Tree file not found: %s (parser initialized with empty state)", tree_path)

    def parse(self, tree_path: str | Path, schema: str | None = None) -> TreeParser:
        """Parse a tree file and extract structure information.

        Args:
            tree_path: Path to the tree file
            schema: Tree format schema (newick, nexus). Auto-detected if None.

        Raises:
            TreeParseError: If the file is not found, empty, or cannot be parsed.
        """
        self.tree_path = Path(tree_path)
        if not self.tree_path.exists():
            raise TreeParseError(f"Tree file not found: {tree_path}")

        content = safe_read_text(tree_path).strip()
        if not content:
            raise TreeParseError(f"Tree file is empty: {tree_path}")

        if schema is None:
            schema = self._detect_schema(content)

        try:
            self.tree = dendropy.Tree.get_from_string(
                content,
                schema=schema,
                preserve_underscores=True,
            )
        except Exception as e:
            raise TreeParseError(f"Failed to parse tree file {tree_path}: {e}") from e

        self._extract_tree_info()
        return self

    def parse_auto(self) -> TreeParser:
        """Auto-detect format and parse."""
        if self.tree_path is None:
            raise TreeParseError("Tree path is not set")
        return self.parse(self.tree_path)

    def _detect_schema(self, content: str) -> str:
        """Auto-detect tree file format (delegates to shared helper)."""
        ext = self.tree_path.suffix if self.tree_path is not None else None
        return _detect_schema_core(content, ext)

    def _extract_tree_info(self) -> None:
        """Extract tip labels, node labels, branch lengths, and support values."""
        if self.tree is None:
            return
        self.tip_labels = [_get_tip_label(t) for t in self.tree.leaf_nodes() if _get_tip_label(t)]
        self.node_labels = [_get_node_label(n) for n in self.tree.internal_nodes() if _get_node_label(n)]
        self.has_branch_lengths = any(n.edge_length is not None for n in self.tree.postorder_node_iter())

        self._extract_support_values()

    def _extract_support_values(self) -> None:
        """Extract bootstrap/posterior support values from node labels/comments/annotations."""
        if self.tree is None:
            return
        for node in self.tree.internal_nodes():
            labels = []
            # Primary source: node.label (where dendropy stores Newick bootstrap values)
            if node.label:
                labels.append(str(node.label).strip())
            if node.comments:
                labels.extend(str(c).strip() for c in node.comments)
            if node.annotations:
                labels.extend(str(a.value).strip() for a in node.annotations)
            for label in labels:
                if re.match(r"^[\d.]+$", label):
                    with contextlib.suppress(ValueError):
                        self.support_values[node] = float(label)

    def detect_support_value_format(self) -> str:
        """Detect the support value format in raw tree string."""
        if self.tree_path is None:
            return "general"
        raw = safe_read_text(self.tree_path)
        has_iqtree_bootstrap = bool(re.search(r"\)\d+:\d+\.\d+", raw))
        has_raxml_bootstrap = bool(re.search(r"\)\{?[\d]+\}?:", raw))
        has_alrt = bool(re.search(r"&support=", raw))
        has_posterior = bool(re.search(r"&prob=", raw))

        if has_alrt and has_iqtree_bootstrap:
            return "iqtree_both"
        if has_iqtree_bootstrap:
            return "iqtree"
        if has_raxml_bootstrap:
            return "raxml"
        if has_posterior:
            return "posterior"
        return "general"

    def get_tip_count(self) -> int:
        if self.tree is None:
            return 0
        return len(self.tree.leaf_nodes())

    def get_node_count(self) -> int:
        if self.tree is None:
            return 0
        return len(list(self.tree.internal_nodes()))

    def get_depth(self) -> int:
        if self.tree is None:
            return 0
        max_depth = 0
        for tip in self.tree.leaf_nodes():
            max_depth = max(max_depth, tip.level())
        return max_depth

    def get_all_ids(self) -> list[str]:
        """Return all node IDs (tips + internal nodes with labels)."""
        if self.tree is None:
            return []
        ids = [t.taxon.label for t in self.tree.leaf_nodes() if t.taxon]
        ids.extend([n.taxon.label for n in self.tree.internal_nodes() if n.taxon])
        return ids

    def get_tree_object(self) -> dendropy.Tree | None:
        return self.tree

    def write_newick(self, output_path: str | Path) -> None:
        if self.tree is None:
            raise TreeParseError("No tree loaded")
        self.tree.write_to_path(str(output_path), schema="newick")


class MetadataParser:
    """Parser for metadata/taxonomy tables."""

    def __init__(self, table_path: str | Path | None = None) -> None:
        self.dataframe: pd.DataFrame | None = None
        self.column_types: dict[str, str] = {}
        self.orphan_nodes: list[str] = []
        if table_path:
            self.parse(table_path)

    def parse(self, table_path: str | Path, id_column: str | None = None) -> MetadataParser:
        """Parse a CSV/Excel metadata table.

        Args:
            table_path: Path to the table file
            id_column: Column name for node IDs. Auto-detected if None.

        Raises:
            MetadataParseError: If the file is not found, empty, or cannot be parsed.
        """
        path = Path(table_path)
        if not path.exists():
            raise MetadataParseError(f"Table file not found: {table_path}")

        suffix = path.suffix.lower()
        try:
            if suffix in {".csv", ".txt", ".tsv"}:
                if suffix == ".csv":
                    self.dataframe = pd.read_csv(path, dtype=str)
                else:
                    self.dataframe = pd.read_csv(path, sep=None, engine="python", dtype=str)
            elif suffix in {".xlsx", ".xls"}:
                self.dataframe = pd.read_excel(path, dtype=str)
            else:
                raise MetadataParseError(f"Unsupported table format: {suffix}")
        except MetadataParseError:
            raise
        except Exception as e:
            raise MetadataParseError(f"Failed to parse table file {table_path}: {e}") from e

        if id_column is None:
            id_column = self._detect_id_column()

        if id_column and self.dataframe is not None and id_column in self.dataframe.columns:
            self.dataframe = self.dataframe.rename(columns={id_column: "id"})
            self.dataframe["id"] = self.dataframe["id"].astype(str)

        self._detect_column_types()
        return self

    def _detect_id_column(self) -> str | None:
        """Auto-detect the ID column."""
        if self.dataframe is None:
            return None
        id_candidates = [
            "id",
            "ID",
            "name",
            "Name",
            "label",
            "Label",
            "taxon",
            "Taxon",
            "tip",
            "Tip",
            "node",
            "Node",
            "species",
            "Species",
            "OTU",
            "otu",
        ]
        for col in id_candidates:
            if col in self.dataframe.columns:
                return col
        return self.dataframe.columns[0]

    def _detect_column_types(self) -> None:
        """Detect column types (numeric, categorical, color)."""
        if self.dataframe is None:
            return
        color_pattern = re.compile(r"^(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3}|rgb|RGBA)", re.IGNORECASE)
        for col in self.dataframe.columns:
            if col == "id":
                continue
            values = self.dataframe[col].dropna()
            if len(values) == 0:
                self.column_types[col] = "unknown"
                continue
            if all(color_pattern.match(str(v)) for v in values):
                self.column_types[col] = "color"
            elif pd.to_numeric(values, errors="coerce").notna().all():
                self.column_types[col] = "numeric"
            else:
                self.column_types[col] = "categorical"

    def validate_against_tree(self, tree_ids: list[str]) -> list[str]:
        """Find orphan nodes in metadata not present in tree."""
        if self.dataframe is None or "id" not in self.dataframe.columns:
            return []
        meta_ids = set(self.dataframe["id"].astype(str).tolist())
        tree_id_set = set(tree_ids)
        self.orphan_nodes = list(meta_ids - tree_id_set)
        return self.orphan_nodes


def format_support_values(
    tree_path: str | Path | None = None,
    output_path: str | Path | None = None,
    content: str | None = None,
    fmt: str = "iqtree",
    support_type: str = "auto",
) -> str | Path:
    """Format support values in tree files.

    Args:
        tree_path: Input tree file path (optional if content is provided)
        output_path: Output tree file path (optional, returns string if omitted)
        content: Raw Newick string (optional, alternative to tree_path)
        fmt: Tree program format (iqtree/raxml/general). Renamed from 'format'
            to avoid shadowing the built-in.
        support_type: Support type (auto/bootstrap/aLRT/both)

    Note:
        Regex patterns are now more specific to avoid false matches.
        The general format pattern requires support values to appear
        immediately after ')' and before ':' (branch length separator).
    """
    if content is not None:
        raw = content
    elif tree_path is not None:
        path = Path(tree_path)
        raw = safe_read_text(path)
    else:
        raise TreeParseError("Either tree_path or content must be provided")

    # Relaxed regex supporting integer branch lengths (:0 / :12), scientific
    # notation (:1.5e-3), and aLRT values with more than 4 digits.  Branch lengths
    # are uniformly expressed by the branch_len fragment (optional decimal/scientific).
    branch_len = r":\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
    if fmt == "iqtree":
        if support_type in ("auto", "both"):
            # IQ-TREE: )bootstrap/aLRT:branch_length
            pattern = r"\)(\d{1,8})/(\d{1,8})(" + branch_len + r")"
            replacement = r")\1\3"
            raw = re.sub(pattern, replacement, raw)
        elif support_type == "bootstrap":
            # IQ-TREE: )bootstrap:branch_length
            pattern = r"\)(\d{1,8})(" + branch_len + r")"
            replacement = r")\1\2"
            raw = re.sub(pattern, replacement, raw)
        elif support_type == "aLRT":
            # IQ-TREE: )bootstrap/aLRT:branch_length
            pattern = r"\)(\d{1,8})/(\d{1,8})(" + branch_len + r")"
            replacement = r")\2\3"
            raw = re.sub(pattern, replacement, raw)
    elif fmt == "raxml":
        # RAxML: ){bootstrap}:branch_length
        pattern = r"\)\{(\d+)\}(" + branch_len + r")"
        replacement = r")\1\2"
        raw = re.sub(pattern, replacement, raw)
    else:
        # More specific general pattern - support values are typically
        # integers or short decimals (up to 8 digits) appearing right after ')'
        # and before ':' (branch length separator)
        # This avoids matching species names like "Species_90:0.3"
        pattern = r"\)(\d{1,8}(?:\.\d{1,2})?)(" + branch_len + r")"
        replacement = r")\1\2"
        raw = re.sub(pattern, replacement, raw)

    if output_path is not None:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(raw, encoding="utf-8")
        return out
    return raw
