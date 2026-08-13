"""Tests for template_datasets CLI commands - color strip, bar, heatmap, etc."""

from pathlib import Path

from typer.testing import CliRunner

from pyitol.cli.apps import template_app

runner = CliRunner()


# ---------------------------------------------------------------------------
# Importability tests - verify every command function exists and is importable
# ---------------------------------------------------------------------------


class TestTemplateDatasetsImportability:
    """Verify all dataset template command functions are importable."""

    def test_import_template_color_strip(self):
        from pyitol.cli.template_datasets import template_color_strip

        assert callable(template_color_strip)

    def test_import_template_branch(self):
        from pyitol.cli.template_datasets import template_branch

        assert callable(template_branch)

    def test_import_template_simple_bar(self):
        from pyitol.cli.template_datasets import template_simple_bar

        assert callable(template_simple_bar)

    def test_import_template_multi_bar(self):
        from pyitol.cli.template_datasets import template_multi_bar

        assert callable(template_multi_bar)

    def test_import_template_heatmap(self):
        from pyitol.cli.template_datasets import template_heatmap

        assert callable(template_heatmap)

    def test_import_template_symbols(self):
        from pyitol.cli.template_datasets import template_symbols

        assert callable(template_symbols)

    def test_import_template_pie(self):
        from pyitol.cli.template_datasets import template_pie

        assert callable(template_pie)

    def test_import_template_boxplot(self):
        from pyitol.cli.template_datasets import template_boxplot

        assert callable(template_boxplot)

    def test_import_template_gradient(self):
        from pyitol.cli.template_datasets import template_gradient

        assert callable(template_gradient)

    def test_import_template_connections(self):
        from pyitol.cli.template_datasets import template_connections

        assert callable(template_connections)

    def test_import_template_labels(self):
        from pyitol.cli.template_datasets import template_labels

        assert callable(template_labels)

    def test_import_template_popup_info(self):
        from pyitol.cli.template_datasets import template_popup_info

        assert callable(template_popup_info)

    def test_import_template_domains(self):
        from pyitol.cli.template_datasets import template_domains

        assert callable(template_domains)

    def test_import_template_binary(self):
        from pyitol.cli.template_datasets import template_binary

        assert callable(template_binary)

    def test_import_template_text(self):
        from pyitol.cli.template_datasets import template_text

        assert callable(template_text)

    def test_import_template_external_shape(self):
        from pyitol.cli.template_datasets import template_external_shape

        assert callable(template_external_shape)


# ---------------------------------------------------------------------------
# CliRunner integration tests for key commands
# ---------------------------------------------------------------------------


class TestColorStripCommand:
    """Test 'create-color-strip' via CliRunner."""

    def test_color_strip_produces_output(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "color_strip.txt")
        result = runner.invoke(
            template_app,
            [
                "create-color-strip",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "Phylum",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_COLORSTRIP" in content

    def test_color_strip_with_custom_colors(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "color_strip_custom.txt")
        result = runner.invoke(
            template_app,
            [
                "create-color-strip",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "Phylum",
                "--colors",
                '{"Proteobacteria": "#ff0000"}',
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()

    def test_color_strip_missing_column(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "color_strip_err.txt")
        result = runner.invoke(
            template_app,
            [
                "create-color-strip",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "nonexistent",
                "--output",
                output,
            ],
        )
        # Should fail with a non-zero exit code or produce an error message
        assert result.exit_code != 0 or "error" in result.output.lower() or "not found" in result.output.lower()


class TestSimpleBarCommand:
    """Test 'create-simple-bar' via CliRunner."""

    def test_simple_bar_produces_output(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "simple_bar.txt")
        result = runner.invoke(
            template_app,
            [
                "create-simple-bar",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "count",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_SIMPLEBAR" in content

    def test_simple_bar_with_color(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "simple_bar_color.txt")
        result = runner.invoke(
            template_app,
            [
                "create-simple-bar",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--column",
                "value",
                "--bar-color",
                "#ff6600",
                "--bar-width",
                "80",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()


class TestHeatmapCommand:
    """Test 'create-heatmap' via CliRunner."""

    def test_heatmap_produces_output(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "heatmap.txt")
        result = runner.invoke(
            template_app,
            [
                "create-heatmap",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--columns",
                "count,value",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_HEATMAP" in content

    def test_heatmap_with_gradient(self, tmp_path, tree_file, taxonomy_file):
        output = str(tmp_path / "heatmap_gradient.txt")
        result = runner.invoke(
            template_app,
            [
                "create-heatmap",
                "--tree",
                tree_file,
                "--taxonomy",
                taxonomy_file,
                "--columns",
                "count,value",
                "--gradient",
                "#ff0000,#ffffff,#0000ff",
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()


class TestDomainsCommand:
    """Test 'create-domains' via CliRunner with JSON data file."""

    def test_domains_produces_output(self, tmp_path):
        domains_json = tmp_path / "domains.json"
        domains_json.write_text(
            '[{"id": "A", "from": 10, "to": 50, "type": 1, "color": "#ff0000"}]',
            encoding="utf-8",
        )
        output = str(tmp_path / "domains.txt")
        result = runner.invoke(
            template_app,
            [
                "create-domains",
                "--data",
                str(domains_json),
                "--output",
                output,
            ],
        )
        assert result.exit_code == 0, result.output
        assert Path(output).exists()
        content = Path(output).read_text()
        assert "DATASET_DOMAINS" in content
        assert "A" in content

    def test_domains_invalid_data_format(self, tmp_path):
        bad_csv = tmp_path / "domains.csv"
        bad_csv.write_text("id,from,to\nA,10,50\n", encoding="utf-8")
        output = str(tmp_path / "domains_err.txt")
        result = runner.invoke(
            template_app,
            [
                "create-domains",
                "--data",
                str(bad_csv),
                "--output",
                output,
            ],
        )
        # JSON decode error should produce a non-zero exit
        assert result.exit_code != 0
