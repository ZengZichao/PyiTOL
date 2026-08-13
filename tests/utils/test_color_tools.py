"""Tests for PyiTOL color tools module."""

import pytest

from pyitol.utils.color_tools import (
    _assign_colors_to_categories_cached,
    assign_colors_to_categories,
    color_distance,
    generate_gradient_colors,
    hex_to_rgb,
    sort_color,
    sort_colors_by_similarity,
)


class TestColorDistance:
    def test_euclidean_same_color(self):
        assert color_distance("#ff0000", "#ff0000", "euclidean") == 0.0

    def test_euclidean_red_blue(self):
        d = color_distance("#ff0000", "#0000ff", "euclidean")
        expected = (255**2 + 255**2) ** 0.5
        assert abs(d - expected) < 0.01

    def test_manhattan(self):
        d = color_distance("#ff0000", "#0000ff", "manhattan")
        assert d == 255 + 255

    def test_invalid_method(self):
        with pytest.raises(ValueError):
            color_distance("#ff0000", "#0000ff", "ciede2000")


class TestSortColors:
    def test_sort_by_similarity(self):
        colors = ["#ff0000", "#ff0001", "#00ff00", "#0000ff"]
        sorted_colors = sort_colors_by_similarity(colors)
        # Red and near-red should be adjacent
        assert sorted_colors.index("#ff0000") + 1 == sorted_colors.index("#ff0001") or sorted_colors.index(
            "#ff0001"
        ) + 1 == sorted_colors.index("#ff0000")

    def test_sort_color_alias(self):
        colors = ["#ff0000", "#00ff00", "#0000ff"]
        result = sort_color(colors)
        assert len(result) == 3

    def test_single_color(self):
        assert sort_colors_by_similarity(["#ff0000"]) == ["#ff0000"]

    def test_empty_list(self):
        assert sort_colors_by_similarity([]) == []


class TestGradientColors:
    def test_two_colors(self):
        colors = generate_gradient_colors("#ff0000", "#0000ff", 3)
        assert len(colors) == 3
        assert colors[0] == "#ff0000"
        assert colors[-1] == "#0000ff"

    def test_single_color(self):
        colors = generate_gradient_colors("#ff0000", "#0000ff", 1)
        assert len(colors) == 1


class TestAssignColors:
    def test_assign_to_categories(self):
        cats = ["A", "B", "C"]
        mapping = assign_colors_to_categories(cats)
        assert len(mapping) == 3
        assert all(v.startswith("#") for v in mapping.values())

    def test_cycles_palette(self):
        cats = list(range(20))
        mapping = assign_colors_to_categories([str(c) for c in cats])
        assert len(mapping) == 20


class TestHexToRgb:
    def test_six_char(self):
        assert hex_to_rgb("#ff0000") == (255, 0, 0)

    def test_three_char(self):
        assert hex_to_rgb("#f00") == (255, 0, 0)


class TestHslToRgb:
    def test_red(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(0, 100, 50) == (255, 0, 0)

    def test_green(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(120, 100, 50) == (0, 255, 0)

    def test_blue(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(240, 100, 50) == (0, 0, 255)

    def test_yellow(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(60, 100, 50) == (255, 255, 0)

    def test_cyan(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(180, 100, 50) == (0, 255, 255)

    def test_magenta(self):
        from pyitol.utils.color_tools import hsl_to_rgb

        assert hsl_to_rgb(300, 100, 50) == (255, 0, 255)


class TestRgbToHsl:
    def test_red(self):
        from pyitol.utils.color_tools import rgb_to_hsl

        h, s, lightness = rgb_to_hsl(255, 0, 0)
        assert abs(h - 0) < 1
        assert abs(s - 100) < 1
        assert abs(lightness - 50) < 1

    def test_green(self):
        from pyitol.utils.color_tools import rgb_to_hsl

        h, s, lightness = rgb_to_hsl(0, 255, 0)
        assert abs(h - 120) < 1
        assert abs(s - 100) < 1
        assert abs(lightness - 50) < 1

    def test_blue(self):
        from pyitol.utils.color_tools import rgb_to_hsl

        h, s, lightness = rgb_to_hsl(0, 0, 255)
        assert abs(h - 240) < 1
        assert abs(s - 100) < 1
        assert abs(lightness - 50) < 1

    def test_gray(self):
        from pyitol.utils.color_tools import rgb_to_hsl

        _h, s, lightness = rgb_to_hsl(128, 128, 128)
        assert abs(s - 0) < 1
        assert abs(lightness - 50) < 1


class TestDarkenColor:
    def test_darken(self):
        from pyitol.utils.color_tools import darken_color

        result = darken_color("#ff0000", factor=0.5)
        r, g, b = hex_to_rgb(result)
        assert r == 127
        assert g == 0
        assert b == 0


class TestLightenColor:
    def test_lighten(self):
        from pyitol.utils.color_tools import lighten_color

        result = lighten_color("#000000", factor=0.5)
        r, g, b = hex_to_rgb(result)
        assert r == 127
        assert g == 127
        assert b == 127

    def test_lighten_clamp(self):
        from pyitol.utils.color_tools import lighten_color

        result = lighten_color("#ffffff", factor=0.5)
        r, g, b = hex_to_rgb(result)
        assert r == 255
        assert g == 255
        assert b == 255


class TestSortColorsEdgeCases:
    def test_reference_not_in_list(self):
        colors = ["#00ff00", "#0000ff"]
        result = sort_colors_by_similarity(colors, reference="#ff0000")
        assert len(result) == 2
        assert result[0] == "#00ff00"


class TestAssignColorsToCategoriesEdgeCases:
    def test_custom_palette(self):
        mapping = assign_colors_to_categories(["A", "B"], palette=["#111111", "#222222"])
        assert mapping["A"] == "#111111"
        assert mapping["B"] == "#222222"


class TestAssignColorsDf:
    def test_with_color_dict(self):
        import pandas as pd

        from pyitol.utils.color_tools import _assign_colors

        df = pd.DataFrame({"cat": ["A", "B", "C"]})
        result = _assign_colors(df, "cat", color_dict={"A": "#111111"})
        assert result == {"A": "#111111"}

    def test_without_color_dict(self):
        import pandas as pd

        from pyitol.utils.color_tools import _assign_colors

        df = pd.DataFrame({"cat": ["B", "A"]})
        result = _assign_colors(df, "cat")
        assert "A" in result
        assert "B" in result


class TestValidateColor:
    def test_hex6(self):
        from pyitol.utils.color_tools import validate_color

        assert validate_color("#ff0000") is True

    def test_hex3(self):
        from pyitol.utils.color_tools import validate_color

        assert validate_color("#f00") is True

    def test_rgb(self):
        from pyitol.utils.color_tools import validate_color

        assert validate_color("rgb(255, 0, 0)") is True

    def test_invalid(self):
        from pyitol.utils.color_tools import validate_color

        # P1-17: 'red' is a valid CSS named color (now recognized)
        assert validate_color("red") is True
        assert validate_color("#gg0000") is False
        assert validate_color("notacolor123") is False


class TestAssignColorsToCategoriesCached:
    def test_default_palette(self):
        result = _assign_colors_to_categories_cached(("A", "B", "C"))
        assert "A" in result
        assert "B" in result
        assert "C" in result
        assert result["A"] != result["B"]
