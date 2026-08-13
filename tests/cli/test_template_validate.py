"""Tests for template validate CLI command."""

from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()


@pytest.fixture
def valid_template_file(tmp_path):
    p = tmp_path / "test_template.txt"
    p.write_text(
        "DATASET_COLORSTRIP\n"
        "SEPARATOR TAB\n"
        "DATASET_LABEL\ttest\n"
        "COLOR\t#ff0000\n"
        "STRIP_WIDTH\t50\n"
        "\n"
        "DATA\n"
        "A\tGroup1\t#ff0000\n"
        "B\tGroup1\t#ff0000\n"
    )
    return str(p)


@pytest.fixture
def invalid_template_file(tmp_path):
    p = tmp_path / "bad_template.txt"
    p.write_text("UNKNOWN_TYPE\nSEPARATOR TAB\n\nDATA\n")
    return str(p)


@pytest.fixture
def empty_template_file(tmp_path):
    p = tmp_path / "empty_template.txt"
    p.write_text("")
    return str(p)


class TestTemplateValidate:
    def test_valid_template(self, valid_template_file):
        result = runner.invoke(app, ["template", "validate", "--template", valid_template_file])
        assert result.exit_code == 0
        assert "格式正确" in result.output

    def test_invalid_template(self, invalid_template_file):
        result = runner.invoke(app, ["template", "validate", "--template", invalid_template_file])
        assert result.exit_code == 1

    def test_empty_template_no_datasets(self, empty_template_file):
        result = runner.invoke(app, ["template", "validate", "--template", empty_template_file])
        assert result.exit_code == 1
        assert "未检测到数据集" in result.output

    def test_validation_errors_present(self, tmp_path):
        p = tmp_path / "has_errors.txt"
        p.write_text("DATASET_SIMPLEBAR\nSEPARATOR TAB\n\nDATA\nA\t10\n")
        with patch("pyitol.templates.learner.learn_template") as mock_learn:
            mock_learn.return_value = {
                "datasets": [
                    {
                        "type": "simplebar",
                        "validation_errors": ["Missing required header"],
                        "parameters": {},
                        "data": [],
                    }
                ]
            }
            result = runner.invoke(app, ["template", "validate", "--template", str(p)])
        assert result.exit_code == 1
        assert "个错误" in result.output
        assert "验证失败" in result.output

    def test_validation_exception(self, tmp_path):
        p = tmp_path / "exc.txt"
        p.write_text("DATASET_SIMPLEBAR\n")
        with patch("pyitol.templates.learner.learn_template") as mock_learn:
            mock_learn.side_effect = RuntimeError("parse error")
            result = runner.invoke(app, ["template", "validate", "--template", str(p)])
        assert result.exit_code == 1
        assert "验证失败" in result.output

    def test_nonexistent_file(self):
        result = runner.invoke(app, ["template", "validate", "--template", "/nonexistent/file.txt"])
        assert result.exit_code == 1
        assert "验证失败" in result.output


class TestTemplateValidateBranches:
    def test_validate_with_errors(self, valid_template_file):
        with patch("pyitol.templates.learner.learn_template") as mock_learn:
            mock_learn.return_value = {
                "datasets": [
                    {
                        "type": "colorstrip",
                        "validation_errors": ["missing color parameter"],
                        "parameters": {},
                        "data": [],
                    }
                ]
            }
            result = runner.invoke(app, ["template", "validate", "--template", valid_template_file])
            assert result.exit_code == 1, result.output
            assert "1 个错误" in result.output

    def test_validate_mixed(self, valid_template_file):
        with patch("pyitol.templates.learner.learn_template") as mock_learn:
            mock_learn.return_value = {
                "datasets": [
                    {
                        "type": "colorstrip",
                        "validation_errors": [],
                        "parameters": {"x": "y"},
                        "data": [{"id": "A", "value": "1"}],
                    },
                    {
                        "type": "heatmap",
                        "validation_errors": ["bad gradient"],
                        "parameters": {},
                        "data": [],
                    },
                ]
            }
            result = runner.invoke(app, ["template", "validate", "--template", valid_template_file])
            assert result.exit_code == 1, result.output
            assert "格式正确" in result.output
            assert "1 个错误" in result.output
            assert "模板验证失败" in result.output

    def test_validate_exception(self, valid_template_file):
        with patch("pyitol.templates.learner.learn_template") as mock_learn:
            mock_learn.side_effect = RuntimeError("parse error")
            result = runner.invoke(app, ["template", "validate", "--template", valid_template_file])
            assert result.exit_code == 1, result.output
            assert "parse error" in result.output
