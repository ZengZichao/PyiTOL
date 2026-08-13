"""Tests for template schema presets constants."""

import warnings

with warnings.catch_warnings():
    warnings.simplefilter("ignore", DeprecationWarning)
    import pyitol.templates.schemas.presets as presets


def test_preset_schemes_exist():
    assert len(presets.PRESET_SCHEMES) > 0
    assert "nature" in presets.PRESET_SCHEMES
    assert "colors" in presets.PRESET_SCHEMES["nature"]
    assert "description" in presets.PRESET_SCHEMES["nature"]


def test_preset_styles_exist():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        assert len(presets.PRESET_STYLES) > 0
        assert "minimal" in presets.PRESET_STYLES
        assert "tree_style" in presets.PRESET_STYLES["minimal"]
