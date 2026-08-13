"""FASTA file I/O utilities - provides equivalent functionality to itol.toolkit's fa_read/fa_write."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path


def fa_read(fasta_path: str | Path) -> dict[str, str]:
    """Read a FASTA file and return a dict of {sequence_id: sequence}.

    Provides equivalent functionality to itol.toolkit's fa_read()
    (independent Python implementation; itol.toolkit delegates to R's ape::read.FASTA).
    Handles multi-line sequences and strips whitespace.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {path}")

    sequences: dict[str, str] = {}
    current_id: str | None = None
    current_seq: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    sequences[current_id] = "".join(current_seq)
                current_id = line[1:].split()[0]  # Take first word as ID
                current_seq = []
            else:
                current_seq.append(line)

    if current_id is not None:
        sequences[current_id] = "".join(current_seq)

    return sequences


def fa_write(fasta_path: str | Path, sequences: dict[str, str], line_width: int = 60) -> Path:
    """Write sequences to a FASTA file.

    Provides equivalent functionality to itol.toolkit's fa_write()
    (independent Python implementation; itol.toolkit delegates to R's seqinr::write.fasta).
    Args:
        fasta_path: Output file path.
        sequences: Dict of {sequence_id: sequence}.
        line_width: Number of characters per line (default 60).
    """
    path = Path(fasta_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for seq_id, seq in sequences.items():
            f.write(f">{seq_id}\n")
            for i in range(0, len(seq), line_width):
                f.write(f"{seq[i : i + line_width]}\n")

    return path


def fa_iter(fasta_path: str | Path) -> Iterator[tuple[str, str]]:
    """Iterate over FASTA records as (sequence_id, sequence) tuples.

    Memory-efficient for large FASTA files.
    """
    path = Path(fasta_path)
    if not path.exists():
        raise FileNotFoundError(f"FASTA file not found: {path}")

    current_id: str | None = None
    current_seq: list[str] = []

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    yield current_id, "".join(current_seq)
                current_id = line[1:].split()[0]
                current_seq = []
            else:
                current_seq.append(line)

    if current_id is not None:
        yield current_id, "".join(current_seq)
