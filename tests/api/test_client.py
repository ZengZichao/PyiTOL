"""Tests for PyiTOL API client module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyitol.api.client import ITOLAPIClient, parse_delete_response, parse_upload_response
from pyitol.exceptions import APIKeyError, ExportError, UploadError


class TestResponseParsers:
    def test_parse_upload_response_url(self):
        success, tree_id, warnings = parse_upload_response("http://itol.embl.de/tree/abc123")
        assert success is True
        assert tree_id == "abc123"
        assert warnings == []

    def test_parse_upload_response_success(self):
        success, tree_id, _warnings = parse_upload_response("SUCCESS: abc123")
        assert success is True
        assert tree_id == "abc123"

    def test_parse_upload_response_error(self):
        success, tree_id, _warnings = parse_upload_response("ERROR: invalid key")
        assert success is False
        assert "invalid key" in tree_id

    def test_parse_upload_response_empty_response(self):
        """Empty server responses must surface a diagnostic marker, not a blank error."""
        success, detail, warnings = parse_upload_response("")
        assert success is False
        assert detail  # non-empty diagnostic message
        assert warnings == []
        success_ws, detail_ws, _ = parse_upload_response("   \n  ")
        assert success_ws is False
        assert detail_ws == detail

    def test_parse_upload_response_with_warnings(self):
        text = "SUCCESS: xyz\nSome warning message"
        success, tree_id, warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "xyz"
        assert len(warnings) == 1
        assert "warning" in warnings[0].lower()

    def test_parse_delete_response_success(self):
        success, msg = parse_delete_response("OK")
        assert success is True
        assert msg == "OK"

    def test_parse_delete_response_error(self):
        success, _msg = parse_delete_response("ERROR: not found")
        assert success is False


class TestITOLAPIClient:
    def test_init_with_key(self):
        client = ITOLAPIClient(api_key="test-key")
        assert client.api_key == "test-key"

    def test_init_with_file(self, tmp_path):
        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("file-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        assert client.api_key == "file-key"

    def test_init_no_key_raises(self):
        with pytest.raises(APIKeyError, match="No API key provided"):
            ITOLAPIClient(api_key_file="/nonexistent/.itolapi.key")

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_success(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "http://itol.embl.de/tree/abc123"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B,(C,D));")
        template_file = tmp_path / "test.txt"
        template_file.write_text("DATASET_SIMPLEBAR")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), str(template_file))
        assert result == "abc123"
        # Verify the correct endpoint and API key were used
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args.args[0] == client.UPLOAD_URL
        assert call_args.kwargs["data"]["APIkey"] == "test-key"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_error(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "ERROR: invalid key"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B,(C,D));")
        template_file = tmp_path / "test.txt"
        template_file.write_text("DATASET_SIMPLEBAR")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(UploadError, match="ERROR"):
            client.upload(str(tree_file), str(template_file))
        mock_post.assert_called_once()
        assert mock_post.call_args.args[0] == client.UPLOAD_URL

    @patch("pyitol.api.client.requests.Session.post")
    def test_export(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF_CONTENT"
        mock_response.headers = {"content-type": "application/pdf"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        results = client.export(["abc123"], fmt="pdf", output_dir=tmp_path)
        assert "abc123" in results
        assert results["abc123"].name == "abc123.pdf"
        assert results["abc123"].parent == tmp_path
        # Verify endpoint and key parameters
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert mock_post.call_args.args[0] == client.EXPORT_URL
        assert call_kwargs["data"]["tree"] == "abc123"
        assert call_kwargs["data"]["format"] == "pdf"

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_with_dpi(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PNG_CONTENT"
        mock_response.headers = {"content-type": "image/png"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        results = client.export(["abc123"], fmt="png", output_dir=tmp_path, dpi=300)
        assert "abc123" in results
        assert results["abc123"].name == "abc123.png"
        assert results["abc123"].parent == tmp_path
        # Verify dpi parameter was sent
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["dpi"] == "300"

    @patch("pyitol.api.client.requests.Session.post")
    def test_batch_delete(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        results = client.batch_delete(["abc123", "def456"])
        assert results["abc123"] is True
        assert results["def456"] is True
        # Verify official endpoint and parameter names
        assert client.DELETE_URL == "https://itol.embl.de/batch_delete.cgi"
        for call in mock_post.call_args_list:
            assert call.args[0] == client.DELETE_URL
            assert "tree" in call.kwargs["data"]
            assert "treeId" not in call.kwargs["data"]

    @patch("pyitol.api.client.requests.Session.post")
    def test_single_delete(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "OK"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.delete("abc123")
        assert result is True
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert mock_post.call_args.args[0] == client.DELETE_URL
        assert call_kwargs["data"]["tree"] == "abc123"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_and_export(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200

        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            resp = MagicMock()
            resp.status_code = 200
            if "uploader" in url:
                resp.text = "SUCCESS: tree_xyz"
            else:
                resp.content = b"SVG_CONTENT"
                resp.headers = {"content-type": "image/svg+xml"}
            return resp

        mock_post.side_effect = side_effect

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B,(C,D));")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload_and_export(str(tree_file), [], fmt="svg", output_dir=tmp_path, wait_time=0)
        assert result.name == "tree_xyz.svg"
        assert result.parent == tmp_path
        # Verify both upload and export endpoints were called
        assert mock_post.call_count == 2
        urls_called = [call.args[0] for call in mock_post.call_args_list]
        assert client.UPLOAD_URL in urls_called
        assert client.EXPORT_URL in urls_called

    @patch("pyitol.api.client.requests.Session.post")
    def test_query_status_ready(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<svg>" + b"x" * 200 + b"</svg>"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.query_status("my_tree")
        assert result["status"] == "ready"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args.kwargs
        assert mock_post.call_args.args[0] == client.EXPORT_URL
        assert call_kwargs["data"]["tree"] == "my_tree"

    @patch("pyitol.api.client.requests.Session.post")
    def test_query_status_unknown(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.query_status("my_tree")
        assert result["status"] == "unknown"
        mock_post.assert_called_once()

    @patch("pyitol.api.client.requests.Session.post")
    def test_delete_project(self, mock_post, tmp_path):
        """Test deleting a project by name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.delete_project("MyProject")
        assert result is True
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["project"] == "MyProject"
        assert "tree" not in call_kwargs["data"]

    @patch("pyitol.api.client.requests.Session.post")
    def test_batch_delete_projects(self, mock_post, tmp_path):
        """Test batch deleting multiple projects by name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        results = client.batch_delete_projects(["Proj1", "Proj2"])
        assert results["Proj1"] is True
        assert results["Proj2"] is True
        for call in mock_post.call_args_list:
            assert "project" in call.kwargs["data"]

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_extra_params(self, mock_post, tmp_path):
        """Test export with arbitrary iTOL visual parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PNG_CONTENT"
        mock_response.headers = {"content-type": "image/png"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")

        client = ITOLAPIClient(api_key_file=str(key_file))
        results = client.export(
            ["abc123"],
            fmt="png",
            output_dir=tmp_path,
            extra_params={
                "display_mode": 2,
                "ignore_branch_length": True,
                "line_width": 3,
                "arc": 360,
                "current_font_size": 12,
                "margin": 200,
                "h_res": 300,
                "label_display": False,
            },
        )
        assert "abc123" in results
        call_kwargs = mock_post.call_args.kwargs
        data = call_kwargs["data"]
        assert data["display_mode"] == "2"
        assert data["ignore_branch_length"] == "1"
        assert data["line_width"] == "3"
        assert data["arc"] == "360"
        assert data["current_font_size"] == "12"
        assert data["margin"] == "200"
        assert data["h_res"] == "300"
        assert data["label_display"] == "0"


class TestParseUploadResponseEdgeCases:
    def test_empty_line_skipped(self):
        text = "SUCCESS: abc\n\nSome warning"
        success, tree_id, warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "abc"
        assert len(warnings) == 1

    def test_http_fallback_when_no_tree_id(self):
        text = "http\nSUCCESS"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "http\nSUCCESS"

    def test_tree_id_with_id_prefix(self):
        text = "tree ID: xyz123"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "xyz123"

    def test_tree_id_with_id_word(self):
        text = "treeId id abc456"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "abc456"

    def test_tree_id_fallback_last_part(self):
        text = "treeId something"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "something"

    def test_success_line_only(self):
        text = "SUCCESS\nhttp://itol.embl.de/tree/abc789"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "abc789"

    def test_http_fallback(self):
        text = "http://itol.embl.de/tree/abc999"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is True
        assert tree_id == "abc999"

    def test_plain_success_no_id(self):
        text = "SUCCESS"
        success, tree_id, _warnings = parse_upload_response(text)
        assert success is False
        assert "no tree ID" in tree_id


class TestITOLAPIClientEdgeCases:
    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_force(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), [], force=True)
        assert result == "abc"
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["force"] == "1"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_datasets_visible(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), [], datasets_visible="1,2")
        assert result == "abc"
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["datasets_visible"] == "1,2"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_zip_cleanup_exception(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with patch.object(Path, "unlink", side_effect=PermissionError("denied")):
            result = client.upload(str(tree_file), [])
        assert result == "abc"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_request_exception(self, mock_post, tmp_path):
        """A network error (requests.RequestException) during upload must be
        wrapped as UploadError. Session.post never returns None in practice, so
        the previous dead `response is None` guard was removed (review item 9)."""
        import requests as _req

        mock_post.side_effect = _req.ConnectionError("Network down")

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(UploadError, match="network error"):
            client.upload(str(tree_file), [])

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_bad_status(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Server Error"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(UploadError, match="500"):
            client.upload(str(tree_file), [])

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_warnings(self, mock_post, tmp_path, caplog):
        import logging

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc\nWarning: something"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with caplog.at_level(logging.WARNING):
            result = client.upload(str(tree_file), [])
        assert result == "abc"
        assert "iTOL upload warning" in caplog.text

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_datasets_visible(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF"
        mock_response.headers = {"content-type": "application/pdf"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        client.export(["abc"], output_dir=tmp_path, datasets_visible="1")
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["datasets_visible"] == "1"

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_width_height(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"PDF"
        mock_response.headers = {"content-type": "application/pdf"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        client.export(["abc"], output_dir=tmp_path, width=100, height=200)
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["width"] == "100"
        assert call_kwargs["data"]["height"] == "200"

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_bad_status(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "invalid api key"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="Export failed"):
            client.export(["abc"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_text_error_in_body(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "error: invalid tree"
        mock_response.content = b"error: invalid tree"
        mock_response.headers = {"content-type": "text/html"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="Export failed"):
            client.export(["abc"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_delete_bad_status(self, mock_post, tmp_path, caplog):
        import logging

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "invalid api key"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with caplog.at_level(logging.WARNING):
            result = client.delete("abc")
        assert result is False
        # 业务失败仍返回 False，且日志使用中文错误信息
        assert "失败" in caplog.text

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_and_export_params(self, mock_post, tmp_path):
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            resp = MagicMock()
            resp.status_code = 200
            if "uploader" in url:
                resp.text = "SUCCESS: tree_xyz"
            else:
                resp.content = b"PDF"
                resp.headers = {"content-type": "application/pdf"}
            return resp

        mock_post.side_effect = side_effect

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")
        out_dir = tmp_path / "out"

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload_and_export(
            str(tree_file),
            [],
            fmt="pdf",
            output_dir=str(out_dir),
            wait_time=0,
            datasets_visible="1,2",
            dpi=300,
            width=100,
            height=200,
        )
        assert result.name == "tree_xyz.pdf"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_and_export_error(self, mock_post, tmp_path):
        def side_effect(*args, **kwargs):
            url = args[0] if args else kwargs.get("url", "")
            resp = MagicMock()
            if "uploader" in url:
                resp.status_code = 200
                resp.text = "SUCCESS: tree_xyz"
            else:
                resp.status_code = 500
                resp.text = "Server Error"
            return resp

        mock_post.side_effect = side_effect

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="Export failed"):
            client.upload_and_export(str(tree_file), [], wait_time=0)

    @patch("pyitol.api.client.requests.Session.post")
    def test_query_status_exception(self, mock_post, tmp_path):
        # 仅捕获 requests.RequestException；内置 ConnectionError 非其子类，
        # 应原样上抛而非被吞掉返回 unknown。
        mock_post.side_effect = ConnectionError("Network down")

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ConnectionError):
            client.query_status("my_tree")

    @patch("pyitol.api.client.requests.Session.post")
    def test_query_status_not_svg(self, mock_post, tmp_path):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>error</body></html>"
        mock_response.headers = {"content-type": "text/html"}
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.query_status("my_tree")
        assert result["status"] == "unknown"

    def test_context_manager(self, tmp_path):
        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        with ITOLAPIClient(api_key_file=str(key_file)) as client:
            assert isinstance(client, ITOLAPIClient)
            assert client.api_key == "test-key"

    def test_close(self, tmp_path):
        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        client.close()


class TestITOLAPIClientExceptionPaths:
    """Tests for exception handling paths in API client (coverage improvement)."""

    @patch("pyitol.api.client.requests.Session.post")
    def test_export_request_exception(self, mock_post, tmp_path):
        """Test export raises ExportError on network exception."""
        mock_post.side_effect = ConnectionError("Network unreachable")

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ConnectionError):
            client.export(["abc123"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_batch_delete_request_exception(self, mock_post, tmp_path):
        """batch_delete 在网络传输错误时抛出 APIError，而非静默返回 False。"""
        import requests as req

        from pyitol.exceptions import APIError

        mock_post.side_effect = req.ConnectionError("Network timeout")

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(APIError, match="网络错误"):
            client.batch_delete(["abc123"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_validate_export_html_error_page(self, mock_post, tmp_path):
        """Test _validate_export_response detects HTML error pages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"<html><body>Error: Tree not found</body></html>"
        mock_response.headers = {"content-type": "text/html; charset=utf-8"}
        mock_response.text = "<html><body>Error: Tree not found</body></html>"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="HTML error page"):
            client.export(["abc123"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_validate_export_short_text_error(self, mock_post, tmp_path):
        """Test _validate_export_response detects short text error responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"ERROR: invalid tree id"
        mock_response.headers = {"content-type": "text/plain"}
        mock_response.text = "ERROR: invalid tree id"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="Export failed"):
            client.export(["abc123"])

    @patch("pyitol.api.client.requests.Session.post")
    def test_validate_export_small_pdf(self, mock_post, tmp_path):
        """Test _validate_export_response rejects suspiciously small PDF files."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"error: failed"  # Less than 500 bytes
        mock_response.headers = {"content-type": "application/pdf"}
        mock_response.text = "error: failed"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        client = ITOLAPIClient(api_key_file=str(key_file))
        with pytest.raises(ExportError, match="Export failed"):
            client.export(["abc123"], fmt="pdf")

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_project_name(self, mock_post, tmp_path):
        """Test upload with custom project name."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc123"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), [], project_name="MyProject")
        assert result == "abc123"
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["projectName"] == "MyProject"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_tree_description(self, mock_post, tmp_path):
        """Test upload with tree description."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc123"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), [], tree_description="My test tree")
        assert result == "abc123"
        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["data"]["treeDescription"] == "My test tree"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_template_list(self, mock_post, tmp_path):
        """Test upload with list of template files."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc123"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")
        template1 = tmp_path / "strip.txt"
        template1.write_text("DATASET_COLORSTRIP")
        template2 = tmp_path / "heatmap.txt"
        template2.write_text("DATASET_HEATMAP")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), [str(template1), str(template2)])
        assert result == "abc123"

    @patch("pyitol.api.client.requests.Session.post")
    def test_upload_with_single_template_string(self, mock_post, tmp_path):
        """Test upload with single template file as string."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "SUCCESS: abc123"
        mock_post.return_value = mock_response

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        tree_file = tmp_path / "test.nwk"
        tree_file.write_text("(A,B);")
        template = tmp_path / "strip.txt"
        template.write_text("DATASET_COLORSTRIP")

        client = ITOLAPIClient(api_key_file=str(key_file))
        result = client.upload(str(tree_file), str(template))
        assert result == "abc123"

    def test_api_key_file_permissions_warning(self, tmp_path, caplog):
        """Test that overly permissive API key file generates warning."""
        import logging

        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        key_file.chmod(0o644)  # World-readable

        with caplog.at_level(logging.WARNING):
            client = ITOLAPIClient(api_key_file=str(key_file))
        assert "overly permissive" in caplog.text
        assert client.api_key == "test-key"

    def test_api_key_file_permissions_strict(self, tmp_path):
        """Test that strict_permissions raises error for permissive key file."""
        key_file = tmp_path / ".itolapi.key"
        key_file.write_text("test-key")
        key_file.chmod(0o644)  # World-readable

        with pytest.raises(APIKeyError, match="overly permissive"):
            ITOLAPIClient(api_key_file=str(key_file), strict_permissions=True)
