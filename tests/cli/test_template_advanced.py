"""Tests for template_advanced CLI commands - linechart, image, alignment, tanglegram, etc."""

from pathlib import Path

from typer.testing import CliRunner

from pyitol.cli.apps import template_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Importability tests
# ---------------------------------------------------------------------------


class TestTemplateAdvancedImportability:
    """Verify all advanced template command functions are importable."""

    def test_import_template_linechart(self):
        from pyitol.cli.template_advanced import template_linechart

        assert callable(template_linechart)

    def test_import_template_image(self):
        from pyitol.cli.template_advanced import template_image

        assert callable(template_image)

    def test_import_template_alignment(self):
        from pyitol.cli.template_advanced import template_alignment

        assert callable(template_alignment)

    def test_import_template_tanglegram(self):
        from pyitol.cli.template_advanced import template_tanglegram

        assert callable(template_tanglegram)

    def test_import_template_placement(self):
        from pyitol.cli.template_advanced import template_placement

        assert callable(template_placement)

    def test_import_template_timescale(self):
        from pyitol.cli.template_advanced import template_timescale

        assert callable(template_timescale)

    def test_import_template_meme(self):
        from pyitol.cli.template_advanced import template_meme

        assert callable(template_meme)

    def test_import_template_manual(self):
        from pyitol.cli.template_advanced import template_manual

        assert callable(template_manual)


# ---------------------------------------------------------------------------
# CliRunner tests for tanglegram (takes --connections string)
# ---------------------------------------------------------------------------


class TestTanglegramCommand:
    """Test 'create-tanglegram' via CliRunner."""

    def test_tanglegram_produces_output(self, tmp_path):
        output = str(tmp_path / "tanglegram.txt")
        result = runner.invoke(
            template_app,
            [
                "create-tanglegram",
                "--connections",
                "A1,B1;A2,B2",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "TANGLEGRAM" in content.upper()

    def test_tanglegram_single_pair(self, tmp_path):
        output = str(tmp_path / "tanglegram_single.txt")
        result = runner.invoke(
            template_app,
            [
                "create-tanglegram",
                "-c",
                "leafX,leafY",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()

    def test_tanglegram_with_custom_color(self, tmp_path):
        output = str(tmp_path / "tanglegram_color.txt")
        result = runner.invoke(
            template_app,
            [
                "create-tanglegram",
                "--connections",
                "A,B",
                "--color",
                "#00aa00",
                "--line-width",
                "3",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
