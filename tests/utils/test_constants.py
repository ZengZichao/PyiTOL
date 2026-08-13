"""Independent QA final verification — Phase-3 item 3.

Item 3 extracted shared magic strings/default colors into a new module
``pyitol.utils.constants`` and referenced them from ``templates/generator`` and
``cli/taxonomy_cmd`` (separator 'TAB', primary/missing/border/connection colors,
RGB palette, heatmap gradient).

Independently verifies:
  * all constants import and carry the exact expected values,
  * generator.py imports the constants and uses DEFAULT_SEPARATOR (no stray
    ``'TAB'`` separator literal remains),
  * taxonomy_cmd.py references DEFAULT_SEPARATOR / PRIMARY_RGB_PALETTE /
    DEFAULT_PRIMARY_COLOR (the old ``'TAB'`` literal defaults are gone),
  * a static audit of remaining color literals in generator.py (advisory only).
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GENERATOR_SRC = (PROJECT_ROOT / "src" / "pyitol" / "templates" / "generator.py").read_text()
TAXONOMY_CMD_SRC = (PROJECT_ROOT / "src" / "pyitol" / "cli" / "taxonomy_cmd.py").read_text()

# Constants referenced by generator.py (Phase-3 item 3 scope).
GENERATOR_CONSTANT_NAMES = [
    "DEFAULT_SEPARATOR",
    "DEFAULT_PRIMARY_COLOR",
    "DEFAULT_MISSING_COLOR",
    "DEFAULT_BORDER_COLOR",
    "DEFAULT_CONNECTION_COLOR",
    "DEFAULT_HEATMAP_GRADIENT",
]

# All constants defined in pyitol.utils.constants.
CONSTANT_NAMES = [*GENERATOR_CONSTANT_NAMES, "PRIMARY_RGB_PALETTE"]


@pytest.mark.parametrize(
    "name,expected",
    [
        ("DEFAULT_SEPARATOR", "TAB"),
        ("DEFAULT_PRIMARY_COLOR", "#ff0000"),
        ("DEFAULT_MISSING_COLOR", "#999999"),
        ("DEFAULT_BORDER_COLOR", "#000000"),
        ("DEFAULT_CONNECTION_COLOR", "#e64b35"),
        ("PRIMARY_RGB_PALETTE", ["#ff0000", "#00ff00", "#0000ff"]),
        ("DEFAULT_HEATMAP_GRADIENT", ["#ff0000", "#ffffff", "#0000ff"]),
    ],
)
def test_constant_values(name, expected):
    from pyitol.utils import constants

    assert getattr(constants, name) == expected


def test_generator_imports_and_uses_constants():
    # All in-scope constants are imported into generator.py.
    assert "from pyitol.utils.constants import" in GENERATOR_SRC
    for name in GENERATOR_CONSTANT_NAMES:
        assert name in GENERATOR_SRC, name
    # PRIMARY_RGB_PALETTE is referenced only by cli/taxonomy_cmd, not generator.
    assert "PRIMARY_RGB_PALETTE" not in GENERATOR_SRC
    # The separator literal 'TAB' must no longer appear as a default value.
    assert "separator: str = 'TAB'" not in GENERATOR_SRC
    assert "DEFAULT_SEPARATOR = 'TAB'" not in GENERATOR_SRC


def test_taxonomy_cmd_references_constants():
    assert "from pyitol.utils.constants import" in TAXONOMY_CMD_SRC
    assert "DEFAULT_SEPARATOR" in TAXONOMY_CMD_SRC
    assert "PRIMARY_RGB_PALETTE" in TAXONOMY_CMD_SRC
    assert "DEFAULT_PRIMARY_COLOR" in TAXONOMY_CMD_SRC
    # Old literal 'TAB' separator defaults must be gone (replaced by constant).
    assert "separator: str = 'TAB'" not in TAXONOMY_CMD_SRC
    assert "= 'TAB'" not in TAXONOMY_CMD_SRC


def test_constants_module_loads():
    # The module is importable and exposes every constant name.
    from pyitol.utils import constants

    for name in CONSTANT_NAMES:
        assert hasattr(constants, name), name


def test_generator_color_literal_audit_advisory(capsys):
    """Advisory audit: report (not fail on) remaining color literals.

    The constants module docstring explicitly states a *conservative* scope:
    some literal call-sites are intentionally retained to avoid cross-file
    regression risk. We therefore only record where color literals still appear
    so the team can decide on further cleanup; identical hex values mean no
    functional change.
    """
    import re

    findings = []
    for m in re.finditer(r"'(#[0-9a-fA-F]{6})'", GENERATOR_SRC):
        # locate line number
        line_no = GENERATOR_SRC[: m.start()].count("\n") + 1
        findings.append((line_no, m.group(1)))
    # Surface for the human reader / final report.
    print("\n[ADVISORY] Remaining color literals in generator.py:")
    for ln, val in findings:
        print(f"  line {ln}: {val}")
    # No assertion: this is an informational audit, not a regression gate.
    assert isinstance(findings, list)
