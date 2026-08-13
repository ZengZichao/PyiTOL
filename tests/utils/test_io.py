"""Tests for PyiTOL I/O utilities (search_tree_file)."""

from pyitol.utils.io import TREE_EXTENSIONS, find_first_tree_file, safe_read_text, search_tree_file


class TestSearchTreeFile:
    def test_finds_tree_files(self, tmp_path):
        (tmp_path / "tree1.nwk").write_text("(A,B);")
        (tmp_path / "tree2.newick").write_text("(C,D);")
        (tmp_path / "data.csv").write_text("id,value\n")
        files = search_tree_file(tmp_path, recursive=False)
        assert len(files) == 2
        assert all(f.suffix in TREE_EXTENSIONS for f in files)

    def test_recursive_search(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.tre").write_text("(A,B);")
        (tmp_path / "root.nwk").write_text("(C,D);")
        files = search_tree_file(tmp_path, recursive=True)
        assert len(files) == 2

    def test_non_recursive(self, tmp_path):
        sub = tmp_path / "subdir"
        sub.mkdir()
        (sub / "nested.tre").write_text("(A,B);")
        files = search_tree_file(tmp_path, recursive=False)
        assert len(files) == 0

    def test_find_first(self, tmp_path):
        (tmp_path / "tree.nwk").write_text("(A,B);")
        result = find_first_tree_file(tmp_path)
        assert result is not None
        assert result.name == "tree.nwk"

    def test_find_first_none(self, tmp_path):
        result = find_first_tree_file(tmp_path)
        assert result is None

    def test_not_a_directory(self, tmp_path):
        result = search_tree_file(tmp_path / "file.txt")
        assert result == []


class TestSafeReadText:
    def test_reads_plain_utf8(self, tmp_path):
        path = tmp_path / "plain.txt"
        path.write_text("hello world", encoding="utf-8")
        assert safe_read_text(path) == "hello world"

    def test_strips_utf8_bom(self, tmp_path):
        path = tmp_path / "bom.txt"
        path.write_bytes(b"\xef\xbb\xbf(A:0.1,B:0.2);")
        content = safe_read_text(path)
        assert not content.startswith("\ufeff")
        assert content == "(A:0.1,B:0.2);"

    def test_fallback_encoding_no_bom_leftover(self, tmp_path):
        path = tmp_path / "bom2.txt"
        # utf-8-sig fallback strips BOM automatically; ensure no leftover
        path.write_bytes(b"\xef\xbb\xbf#NEXUS\nBEGIN TREES;")
        content = safe_read_text(path)
        assert content.startswith("#NEXUS")
