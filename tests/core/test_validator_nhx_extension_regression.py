"""QA independent regression tests for Item 5: .nhx/.nhy classified as newick.

Verifies that _detect_tree_format maps NHX extensions (.nhx/.nhy) to
'newick' (previously they were mis-classified as 'nexus'), while the other
format mappings still hold.
"""

from pathlib import Path

import pytest

from pyitol.core.validator import _detect_tree_format


class TestNHXFormatDetection:
    @pytest.mark.parametrize(
        "fname,ext,expected",
        [
            ("tree.nhx", ".nhx", "newick"),
            ("tree.nhy", ".nhy", "newick"),
            ("tree.nex", ".nex", "nexus"),
            ("tree.nexus", ".nexus", "nexus"),
            ("tree.nwk", ".nwk", "newick"),
            ("tree.newick", ".newick", "newick"),
        ],
    )
    def test_detect_tree_format(self, tmp_path, fname, ext, expected):
        p = tmp_path / fname
        p.write_text("(A,B);")  # minimal valid content
        assert _detect_tree_format(Path(p), ext) == expected
