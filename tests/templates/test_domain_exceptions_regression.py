"""Regression tests for domain exceptions in templates.

Verifies that the generator / presets modules raise the *domain* exceptions
(InvalidColumnError, TemplateError, TemplateTypeError) instead of bare
ValueError when inputs are invalid.
"""

import pytest

from pyitol.exceptions import (
    InvalidColumnError,
    TemplateError,
    TemplateTypeError,
)
from pyitol.templates.generator import TemplateGenerator, _read_taxonomy_and_tree
from pyitol.templates.presets import get_palette, get_preset

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"


class TestDomainExceptions:
    def test_invalid_write_mode_raises_template_error(self, tmp_path):
        out = tmp_path / "out.txt"
        with pytest.raises(TemplateError) as exc:
            TemplateGenerator().write(out, mode="bogus_mode")
        msg = str(exc.value).lower()
        assert "write" in msg and "append" in msg

    def test_missing_id_column_raises_invalid_column_error(self, tmp_path):
        tree = tmp_path / "t.nwk"
        tree.write_text(SIMPLE_NEWICK)
        tax = tmp_path / "tax.tsv"
        # No 'id' column and the requested id_column is absent too.
        tax.write_text("name\tKingdom\nA\tBacteria\nB\tArchaea\nC\tBacteria\nD\tArchaea\n")
        with pytest.raises(InvalidColumnError):
            _read_taxonomy_and_tree(str(tax), str(tree), id_column="taxon")

    def test_unknown_preset_raises_template_type_error(self):
        with pytest.raises(TemplateTypeError):
            get_preset("definitely_not_a_preset")

    def test_unknown_color_preset_raises_template_type_error(self):
        with pytest.raises(TemplateTypeError):
            get_palette("no_such_collection", "primary")

    def test_domain_exceptions_are_not_value_error(self):
        # The whole point of the fix: these must not be bare ValueError.
        assert not issubclass(InvalidColumnError, ValueError)
        assert not issubclass(TemplateError, ValueError)
        assert not issubclass(TemplateTypeError, ValueError)
        # And InvalidColumnError / TemplateTypeError are TemplateError family.
        assert issubclass(InvalidColumnError, TemplateError)
        assert issubclass(TemplateTypeError, TemplateError)
