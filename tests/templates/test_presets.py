"""Tests for PyiTOL template presets and color palettes."""

import pytest

from pyitol.exceptions import TemplateTypeError
from pyitol.templates.presets import (
    get_palette,
    get_preset,
    list_all_palettes,
    list_presets,
)
from pyitol.templates.presets.cell import get_cell_palette, list_cell_palettes
from pyitol.templates.presets.colorblind import get_colorblind_palette, is_colorblind_friendly, list_colorblind_palettes
from pyitol.templates.presets.nature import get_nature_palette, list_nature_palettes


class TestSchemaPresets:
    def test_all_presets_instantiable(self):
        for name in list_presets():
            schema = get_preset(name)
            assert schema is not None
            assert True  # Just ensure no crash

    def test_unknown_preset_raises(self):
        with pytest.raises(TemplateTypeError, match="Unknown preset"):
            get_preset("nonexistent")

    def test_list_presets(self):
        names = list_presets()
        assert "simple_bar" in names
        assert "heatmap" in names
        assert "color_strip" in names


class TestColorPalettes:
    def test_nature_palettes(self):
        for name in list_nature_palettes():
            colors = get_nature_palette(name)
            assert isinstance(colors, list)
            assert all(c.startswith("#") for c in colors)

    def test_cell_palettes(self):
        for name in list_cell_palettes():
            colors = get_cell_palette(name)
            assert isinstance(colors, list)
            assert all(c.startswith("#") for c in colors)

    def test_colorblind_palettes(self):
        for name in list_colorblind_palettes():
            colors = get_colorblind_palette(name)
            assert isinstance(colors, list)
            assert all(c.startswith("#") for c in colors)

    def test_get_palette_with_n(self):
        colors = get_palette("nature", "primary", n=5)
        assert len(colors) == 5

    def test_get_palette_unknown_preset(self):
        with pytest.raises(TemplateTypeError, match="Unknown color preset"):
            get_palette("unknown", "primary")

    def test_list_all_palettes(self):
        all_p = list_all_palettes()
        assert "nature" in all_p
        assert "cell" in all_p
        assert "colorblind" in all_p

    def test_is_colorblind_friendly_true(self):
        friendly = ["#4477AA", "#EE6677"]
        assert is_colorblind_friendly(friendly) is True

    def test_is_colorblind_friendly_false(self):
        unfriendly = ["#FF0000", "#00FF00"]
        assert is_colorblind_friendly(unfriendly) is False


class TestSchemaPresetsModule:
    def test_preset_schemes_exist(self):
        from pyitol.templates.schemas import presets as schemas_presets

        assert "nature" in schemas_presets.PRESET_SCHEMES
        assert "minimal" in schemas_presets.PRESET_STYLES


class TestColorPalettesExtended:
    def test_cell_palette_with_n(self):
        colors = get_cell_palette("classic", n=15)
        assert len(colors) == 15

    def test_colorblind_palette_with_n(self):
        colors = get_colorblind_palette("tol_bright", n=10)
        assert len(colors) == 10
