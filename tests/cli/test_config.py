"""Tests for PyiTOL CLI config commands and config overrides."""

from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()


class TestConfigInit:
    def test_config_init_default(self, tmp_path):
        out = tmp_path / "pyitol_config.yaml"
        result = runner.invoke(app, ["config", "init", "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "api_key_file" in content
        assert "default_format" in content

    def test_config_init_custom(self, tmp_path):
        out = tmp_path / "custom.yaml"
        key_file = tmp_path / "my.key"
        key_file.write_text("secret")
        result = runner.invoke(
            app,
            [
                "config",
                "init",
                "--output",
                str(out),
                "--api-key-file",
                str(key_file),
                "--default-format",
                "pdf",
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        content = out.read_text()
        assert "pdf" in content


class TestConfigOverrides:
    def test_template_create_uses_config_tree_and_taxonomy(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text(
            "tree: examples/data/synthetic_130tips.nwk\n"
            "taxonomy: examples/data/synthetic_130tips_taxonomy.csv\n"
            "column: Phylum\n"
            "label: from_config\n",
            encoding="utf-8",
        )
        out = tmp_path / "strip.txt"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config),
                "template",
                "create",
                "color-strip",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert "DATASET_LABEL\tfrom_config" in out.read_text()

    def test_template_create_cli_wins_over_config(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text(
            "tree: examples/data/synthetic_130tips.nwk\n"
            "taxonomy: examples/data/synthetic_130tips_taxonomy.csv\n"
            "column: Phylum\n"
            "label: from_config\n",
            encoding="utf-8",
        )
        out = tmp_path / "strip.txt"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config),
                "template",
                "create",
                "color-strip",
                "--output",
                str(out),
                "--label",
                "from_cli",
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert "DATASET_LABEL\tfrom_cli" in out.read_text()

    def test_multiple_config_files_merge(self, tmp_path):
        c1 = tmp_path / "c1.yaml"
        c1.write_text(
            "tree: examples/data/synthetic_130tips.nwk\ntaxonomy: examples/data/synthetic_130tips_taxonomy.csv\n",
            encoding="utf-8",
        )
        c2 = tmp_path / "c2.yaml"
        c2.write_text(
            "column: Phylum\nlabel: merged\n",
            encoding="utf-8",
        )
        out = tmp_path / "strip.txt"
        result = runner.invoke(
            app,
            [
                "--config",
                str(c1),
                "--config",
                str(c2),
                "template",
                "create",
                "color-strip",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert "DATASET_LABEL\tmerged" in out.read_text()

    def test_taxonomy_monophyly_uses_config(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text(
            "tree: examples/data/synthetic_130tips.nwk\n"
            "taxonomy: examples/data/synthetic_130tips_taxonomy.csv\n"
            "rank: Phylum\n",
            encoding="utf-8",
        )
        out = tmp_path / "mono.csv"
        result = runner.invoke(
            app,
            [
                "--config",
                str(config),
                "taxonomy",
                "monophyly",
                "--output",
                str(out),
            ],
        )
        assert result.exit_code == 0, result.output
        assert out.exists()
        assert "Phylum_01" in out.read_text()
