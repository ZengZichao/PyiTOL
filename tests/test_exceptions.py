"""Tests for pyitol.exceptions - custom exception hierarchy."""

from __future__ import annotations

import pytest

from pyitol.exceptions import (
    APIError,
    APIKeyError,
    ColorCodeError,
    ExportError,
    MetadataParseError,
    PyiTOLBaseError,
    ReplayError,
    SeparatorConflictError,
    SessionError,
    TemplateError,
    TemplateValidationError,
    TreeParseError,
    UploadError,
)


class TestExceptionHierarchy:
    """Verify the exception class hierarchy is correct."""

    def test_base_error_is_exception(self):
        assert issubclass(PyiTOLBaseError, Exception)

    def test_tree_parse_error(self):
        assert issubclass(TreeParseError, PyiTOLBaseError)

    def test_metadata_parse_error(self):
        assert issubclass(MetadataParseError, PyiTOLBaseError)

    def test_template_error(self):
        assert issubclass(TemplateError, PyiTOLBaseError)

    def test_template_validation_error(self):
        assert issubclass(TemplateValidationError, TemplateError)
        assert issubclass(TemplateValidationError, PyiTOLBaseError)

    def test_api_error(self):
        assert issubclass(APIError, PyiTOLBaseError)

    def test_api_key_error(self):
        assert issubclass(APIKeyError, APIError)
        assert issubclass(APIKeyError, PyiTOLBaseError)

    def test_upload_error(self):
        assert issubclass(UploadError, APIError)
        assert issubclass(UploadError, PyiTOLBaseError)

    def test_export_error(self):
        assert issubclass(ExportError, APIError)
        assert issubclass(ExportError, PyiTOLBaseError)

    def test_color_code_error(self):
        assert issubclass(ColorCodeError, PyiTOLBaseError)

    def test_separator_conflict_error(self):
        from pyitol.exceptions import DataError

        assert issubclass(SeparatorConflictError, DataError)
        assert issubclass(SeparatorConflictError, PyiTOLBaseError)

    def test_session_error(self):
        assert issubclass(SessionError, PyiTOLBaseError)

    def test_replay_error(self):
        assert issubclass(ReplayError, SessionError)
        assert issubclass(ReplayError, PyiTOLBaseError)


class TestExceptionMessages:
    """Verify exceptions carry messages correctly."""

    @pytest.mark.parametrize(
        "exc_cls",
        [
            PyiTOLBaseError,
            TreeParseError,
            MetadataParseError,
            TemplateError,
            TemplateValidationError,
            APIError,
            APIKeyError,
            UploadError,
            ExportError,
            ColorCodeError,
            SeparatorConflictError,
            SessionError,
            ReplayError,
        ],
    )
    def test_message_preserved(self, exc_cls):
        msg = f"test message for {exc_cls.__name__}"
        exc = exc_cls(msg)
        assert str(exc) == msg

    @pytest.mark.parametrize(
        "exc_cls",
        [
            PyiTOLBaseError,
            TreeParseError,
            APIError,
            SessionError,
        ],
    )
    def test_raise_and_catch_base(self, exc_cls):
        with pytest.raises(PyiTOLBaseError):
            raise exc_cls("test")

    def test_catch_template_validation_as_template_error(self):
        with pytest.raises(TemplateError):
            raise TemplateValidationError("validation failed")

    def test_catch_api_key_error_as_api_error(self):
        with pytest.raises(APIError):
            raise APIKeyError("missing key")

    def test_catch_replay_error_as_session_error(self):
        with pytest.raises(SessionError):
            raise ReplayError("replay failed")

    def test_catch_upload_error_as_api_error(self):
        with pytest.raises(APIError):
            raise UploadError("upload failed")

    def test_catch_export_error_as_api_error(self):
        with pytest.raises(APIError):
            raise ExportError("export failed")
