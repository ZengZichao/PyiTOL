"""Tests for PyiTOL CLI learn commands."""

from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()


class TestLearnTemplate:
    def test_learn_single(self, tmp_path):
        tpl = tmp_path / "template.txt"
        tpl.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nDATASET_LABEL test\nCOLOR #ff0000\nDATA\nA\t10\n")
        out = tmp_path / "learned.json"
        result = runner.invoke(app, ["learn", "template", "--template", str(tpl), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()

    def test_learn_multiple(self, tmp_path):
        tpl1 = tmp_path / "t1.txt"
        tpl1.write_text("DATASET_COLORSTRIP\nSEPARATOR TAB\nDATA\nA\t#ff0000\n")
        tpl2 = tmp_path / "t2.txt"
        tpl2.write_text("DATASET_HEATMAP\nSEPARATOR TAB\nDATA\nA\t1\n")
        out = tmp_path / "learned.json"
        result = runner.invoke(
            app, ["learn", "template", "--template", str(tpl1), "--template", str(tpl2), "--output", str(out)]
        )
        assert result.exit_code == 0, result.output


class TestLearnPalette:
    def test_valid_preset(self):
        result = runner.invoke(app, ["learn", "palette", "--preset-name", "nature"])
        assert result.exit_code == 0, result.output

    def test_invalid_preset(self):
        result = runner.invoke(app, ["learn", "palette", "--preset-name", "nonexistent"])
        assert result.exit_code == 0  # prints error but doesn't crash
        assert "未知预设" in result.output or "Unknown" in result.output or "✗" in result.output


class TestLearnTrainTheme:
    def test_train_theme(self, tmp_path):
        tpl = tmp_path / "template.txt"
        tpl.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\nDATASET_LABEL test\nCOLOR #ff0000\nDATA\nA\t10\n")
        out = tmp_path / "theme.json"
        result = runner.invoke(app, ["learn", "train-theme", "--dir", str(tmp_path), "--output", str(out)])
        assert result.exit_code == 0, result.output
        assert out.exists()
