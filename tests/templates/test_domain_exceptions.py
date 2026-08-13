"""Independent QA regression tests for Item 2: domain exceptions in templates.

Verifies, independently of the other QA engineers' suites, that the generator
and presets modules raise the *domain* exceptions
(``InvalidColumnError``, ``TemplateError``, ``TemplateTypeError``) instead of
bare ``ValueError`` when inputs are invalid. Uses the public generator
functions and preset entry points (a different angle from the sibling suite).
"""

import pytest

from pyitol.exceptions import (
    InvalidColumnError,
    TemplateError,
    TemplateTypeError,
)
from pyitol.templates.generator import (
    TemplateGenerator,
    generate_color_strip_template,
    generate_simple_bar_template,
    generate_symbols_template,
)
from pyitol.templates.presets import get_palette, get_preset

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tGroup\tValue\nA\tG1\t10\nB\tG1\t20\nC\tG2\t30\nD\tG2\t40\n"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "t.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "tax.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


class TestDomainExceptionsOnGenerators:
    def test_missing_column_raises_invalid_column_error(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        with pytest.raises(InvalidColumnError):
            generate_color_strip_template(str(out), taxonomy_file, tree_file, column="NO_SUCH_COLUMN")

    def test_invalid_symbol_type_raises_template_error(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        with pytest.raises(TemplateError):
            generate_symbols_template(
                str(out),
                taxonomy_file,
                tree_file,
                column="Group",
                symbol_type="not_a_real_shape",
            )

    def test_invalid_write_mode_raises_template_error(self, tmp_path):
        out = tmp_path / "out.txt"
        with pytest.raises(TemplateError) as exc:
            TemplateGenerator().write(out, mode="bogus_mode")
        msg = str(exc.value).lower()
        assert "write" in msg and "append" in msg

    def test_simple_bar_missing_value_column(self, tmp_path, tree_file, taxonomy_file):
        out = tmp_path / "out.txt"
        with pytest.raises(InvalidColumnError):
            generate_simple_bar_template(str(out), taxonomy_file, tree_file, value_column="MISSING")


class TestPresetDomainExceptions:
    def test_unknown_preset_raises_template_type_error(self):
        with pytest.raises(TemplateTypeError):
            get_preset("definitely_not_a_preset")

    def test_unknown_color_preset_raises_template_type_error(self):
        with pytest.raises(TemplateTypeError):
            get_palette("no_such_collection", "primary")


class TestDomainExceptionHierarchy:
    def test_not_value_error(self):
        # The whole point of the fix: these must not be bare ValueError.
        assert not issubclass(InvalidColumnError, ValueError)
        assert not issubclass(TemplateError, ValueError)
        assert not issubclass(TemplateTypeError, ValueError)

    def test_subclass_relationship(self):
        assert issubclass(InvalidColumnError, TemplateError)
        assert issubclass(TemplateTypeError, TemplateError)
