"""General I/O utilities for file discovery, path handling, and safe encoding."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# Common tree file extensions used by phylogenetic software
TREE_EXTENSIONS = {
    ".nwk",
    ".newick",
    ".tre",
    ".tree",
    ".treefile",
    ".nex",
    ".nexus",
    ".phy",
    ".phylip",
    ".contree",
    ".support",
    ".raxml.support",
    ".fasttree",
    ".ft",
}


def safe_read_text(
    path: str | Path,
    encoding: str = "utf-8",
    fallback_encoding: str = "utf-8-sig",
) -> str:
    """Read text file with encoding fallback and BOM stripping.

    Tries primary encoding first, falls back to fallback encoding on failure.
    Logs a WARNING when fallback is used. Automatically strips UTF-8 BOM
    (\ufeff) from the beginning of the content so downstream parsers
    (e.g. dendropy) do not choke on it.

    Args:
        path: File path
        encoding: Primary encoding (default 'utf-8')
        fallback_encoding: Fallback encoding (default 'utf-8-sig' for BOM files)

    Returns:
        File content as string
    """
    path = Path(path)
    try:
        with open(path, encoding=encoding, newline="") as f:
            content = f.read()
    except UnicodeDecodeError:
        logger.warning(f"UTF-8 decode failed for {path.name}, trying {fallback_encoding}")
        try:
            with open(path, encoding=fallback_encoding, newline="") as f:
                content = f.read()
        except UnicodeDecodeError:
            logger.warning(f"{fallback_encoding} also failed for {path.name}, trying latin-1")
            with open(path, encoding="latin-1", newline="") as f:
                content = f.read()

    # Strip UTF-8 BOM if present (fallback_encoding already removes it, but
    # utf-8 leaves \ufeff in place).
    if content.startswith("\ufeff"):
        logger.debug(f"Removed UTF-8 BOM from {path.name}")
        content = content[1:]
    return content


def search_tree_file(
    directory: str | Path,
    recursive: bool = True,
    extensions: set[str] | None = None,
) -> list[Path]:
    """Search for phylogenetic tree files in a directory.

    Provides equivalent functionality to itol.toolkit's search_tree_file()
    (independent implementation: this version matches by file extension,
    while itol.toolkit inspects the first line of each file).

    Args:
        directory: Directory to search in.
        recursive: Whether to search subdirectories.
        extensions: Set of extensions to look for. Defaults to common tree formats.

    Returns:
        List of Path objects for found tree files, sorted alphabetically.
        Returns an empty list (with a warning) if the path is not a directory.
    """
    path = Path(directory)
    if not path.is_dir():
        logger.warning("search_tree_file: not a directory, returning empty list: %s", path)
        return []

    exts = extensions or TREE_EXTENSIONS
    pattern = "**/*" if recursive else "*"
    files = [f for f in path.glob(pattern) if f.is_file() and f.suffix.lower() in exts]
    return sorted(files)


def find_first_tree_file(
    directory: str | Path,
    recursive: bool = True,
    extensions: set[str] | None = None,
) -> Path | None:
    """Find the first tree file in a directory.

    Returns None if no tree file is found.
    """
    files = search_tree_file(directory, recursive, extensions)
    return files[0] if files else None
