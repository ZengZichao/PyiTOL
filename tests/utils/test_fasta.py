"""Tests for PyiTOL FASTA I/O utilities."""

import pytest

from pyitol.utils.fasta import fa_iter, fa_read, fa_write

FASTA_CONTENT = """>seq1 description
ATCGATCGATCG
ATCG
>seq2
GGGGGGGG
>seq3
ATATATAT
"""


@pytest.fixture
def fasta_file(tmp_path):
    p = tmp_path / "test.fa"
    p.write_text(FASTA_CONTENT, encoding="utf-8")
    return str(p)


class TestFaRead:
    def test_reads_all_sequences(self, fasta_file):
        seqs = fa_read(fasta_file)
        assert len(seqs) == 3
        assert "seq1" in seqs
        assert "seq2" in seqs
        assert "seq3" in seqs

    def test_joins_multiline_sequences(self, fasta_file):
        seqs = fa_read(fasta_file)
        assert seqs["seq1"] == "ATCGATCGATCGATCG"
        assert seqs["seq2"] == "GGGGGGGG"

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            fa_read("/nonexistent/path.fa")

    def test_empty_lines_ignored(self, tmp_path):
        p = tmp_path / "empty_lines.fa"
        p.write_text(">seq1\nATCG\n\n\n>seq2\nGGGG\n", encoding="utf-8")
        seqs = fa_read(str(p))
        assert len(seqs) == 2
        assert seqs["seq1"] == "ATCG"
        assert seqs["seq2"] == "GGGG"


class TestFaWrite:
    def test_writes_correct_format(self, tmp_path):
        sequences = {"A": "ATCGATCGATCG", "B": "GGGG"}
        output = tmp_path / "out.fa"
        fa_write(output, sequences, line_width=6)
        content = output.read_text(encoding="utf-8")
        assert ">A\nATCGAT\nCGATCG\n" in content
        assert ">B\nGGGG\n" in content

    def test_default_line_width(self, tmp_path):
        sequences = {"long": "A" * 100}
        output = tmp_path / "out.fa"
        fa_write(output, sequences)
        lines = output.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines[1]) == 60


class TestFaIter:
    def test_iterates_correctly(self, fasta_file):
        items = list(fa_iter(fasta_file))
        assert len(items) == 3
        ids = [i[0] for i in items]
        assert ids == ["seq1", "seq2", "seq3"]

    def test_memory_efficient(self, fasta_file):
        it = fa_iter(fasta_file)
        first = next(it)
        assert first[0] == "seq1"
        second = next(it)
        assert second[0] == "seq2"

    def test_iter_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            list(fa_iter("/nonexistent/path.fa"))

    def test_iter_empty_lines_ignored(self, tmp_path):
        p = tmp_path / "empty_lines.fa"
        p.write_text(">seq1\nATCG\n\n\n>seq2\nGGGG\n", encoding="utf-8")
        items = list(fa_iter(str(p)))
        assert len(items) == 2
        assert items[0] == ("seq1", "ATCG")
        assert items[1] == ("seq2", "GGGG")
