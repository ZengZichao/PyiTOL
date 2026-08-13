"""Independent QA regression tests for Item 5: .nhx/.nhy mapped to newick.

Verifies, independently of the other QA engineers' suites, that
``_detect_tree_format`` classifies NHX extensions (.nhx / .nhy) as
``'newick'`` (previously they were misclassified as nexus), while the
established mappings (nexus -> 'nexus', newick -> 'newick',
phyloxml -> 'phyloxml') still hold.
"""

from pyitol.core.validator import _detect_tree_format


class TestDetectTreeFormatNHX:
    def test_nhx_extension_is_newick(self, tmp_path):
        p = tmp_path / "tree.nhx"
        p.write_text("((A,B),(C,D));")
        assert _detect_tree_format(p, ".nhx") == "newick"

    def test_nhy_extension_is_newick(self, tmp_path):
        p = tmp_path / "tree.nhy"
        p.write_text("((A,B),(C,D));")
        assert _detect_tree_format(p, ".nhy") == "newick"

    def test_nexus_still_nexus(self, tmp_path):
        p = tmp_path / "tree.nexus"
        p.write_text("#NEXUS\nbegin trees; tree t1 = ((A,B),(C,D)); end;")
        assert _detect_tree_format(p, ".nexus") == "nexus"

    def test_newick_still_newick(self, tmp_path):
        p = tmp_path / "tree.newick"
        p.write_text("((A,B),(C,D));")
        assert _detect_tree_format(p, ".newick") == "newick"

    def test_phyloxml_still_phyloxml(self, tmp_path):
        p = tmp_path / "tree.xml"
        p.write_text("<phyloxml><phylogeny></phylogeny></phyloxml>")
        assert _detect_tree_format(p, ".xml") == "phyloxml"

    def test_nhx_content_with_nexus_like_comment(self, tmp_path):
        # Even when an NHX file contains a '#NEXUS'-looking token inside a
        # comment, the extension rule must win and return 'newick'.
        p = tmp_path / "tree.nhx"
        p.write_text("((A,B)[&&NHX:note=#NEXUS],(C,D));")
        assert _detect_tree_format(p, ".nhx") == "newick"
