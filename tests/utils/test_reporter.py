"""Tests for PyiTOL reporter module."""

import yaml

from pyitol.utils.reporter import (
    create_session_log,
    format_result_summary,
    get_error_message,
    translate_error,
    translate_errors,
)


class TestGetErrorMessage:
    def test_known_code(self):
        msg = get_error_message("E001")
        assert "文件未找到" in msg

    def test_unknown_code(self):
        msg = get_error_message("E999")
        assert "未知错误" in msg
        assert "E999" in msg


class TestTranslateError:
    def test_known_type(self):
        msg = translate_error("FileNotFoundError", "some file")
        assert "文件未找到" in msg

    def test_value_error_with_placeholder(self):
        msg = translate_error("ValueError", "bad value")
        assert "参数错误" in msg
        assert "bad value" in msg

    def test_unknown_type(self):
        msg = translate_error("CustomError", "oops")
        assert msg == "CustomError: oops"


class TestTranslateErrors:
    def test_known_error_type(self):
        errors = ["FileNotFoundError: file not found"]
        result = translate_errors(errors)
        assert any("E001" in r for r in result)

    def test_unknown_error(self):
        errors = ["SomeUnknownError: oops"]
        result = translate_errors(errors)
        assert result == errors

    def test_multiple_errors(self):
        errors = ["ValueError: bad", "ConnectionError: timeout"]
        result = translate_errors(errors)
        assert len(result) == 2


class TestCreateSessionLog:
    def test_create_log(self, tmp_path):
        p = tmp_path / "session.yaml"
        result = create_session_log(
            p,
            command="template create",
            status="success",
            inputs={"tree": "tree.nwk"},
            outputs={"template": "out.txt"},
            errors=["err1"],
            warnings=["warn1"],
        )
        assert result.exists()
        data = yaml.safe_load(p.read_text())
        assert data["command"] == "template create"
        assert data["status"] == "success"
        assert data["inputs"]["tree"] == "tree.nwk"
        assert data["outputs"]["template"] == "out.txt"
        assert data["errors"] == ["err1"]
        assert data["warnings"] == ["warn1"]

    def test_create_log_defaults(self, tmp_path):
        p = tmp_path / "session.yaml"
        result = create_session_log(p, "cmd", "ok")
        assert result.exists()
        data = yaml.safe_load(p.read_text())
        assert data["inputs"] == {}
        assert data["outputs"] == {}
        assert data["errors"] == []
        assert data["warnings"] == []


class TestFormatResultSummary:
    def test_basic(self):
        summary = format_result_summary("cmd", "success")
        assert "Command: cmd" in summary
        assert "Status: success" in summary

    def test_with_outputs(self):
        summary = format_result_summary("cmd", "ok", outputs={"file": "out.txt"})
        assert "Outputs:" in summary
        assert "file: out.txt" in summary

    def test_with_errors(self):
        summary = format_result_summary("cmd", "fail", errors=["err1"])
        assert "Errors:" in summary
        assert "- err1" in summary

    def test_full(self):
        summary = format_result_summary(
            "cmd",
            "ok",
            outputs={"a": "1"},
            errors=["e1"],
        )
        assert "Outputs:" in summary
        assert "Errors:" in summary
