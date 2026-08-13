"""Tests for task CLI commands: upload, export, upload-and-export, delete, status."""

from unittest.mock import MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def api_key_file(tmp_path):
    p = tmp_path / ".itolapi.key"
    p.write_text("test-api-key")
    return str(p)


def _make_context_mock(mock_client):
    """Configure a MagicMock to work as a context manager returning itself."""
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


class TestTaskUpload:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_success(self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_abc123"
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload",
                "--tree",
                tree_file,
                "--api-key-file",
                api_key_file,
                "--dataset-name",
                "my_tree",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "tree_abc123" in result.output
        mock_client.upload.assert_called_once()

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_with_config_files(self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file):
        cfg = tmp_path / "config.txt"
        cfg.write_text("DATASET_COLORSTRIP")
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_abc"
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload",
                "--tree",
                tree_file,
                "--api-key-file",
                api_key_file,
                "--config",
                str(cfg),
            ],
        )
        assert result.exit_code == 0, result.output
        args = mock_client.upload.call_args
        assert str(cfg) in args[0][1]

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_with_download_and_params(
        self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file
    ):
        param_file = tmp_path / "params.txt"
        param_file.write_text("format=svg\ndpi=300\n")
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_abc"
        mock_client.export.return_value = {"tree_abc": tmp_path / "tree_abc.svg"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload",
                "--tree",
                tree_file,
                "--api-key-file",
                api_key_file,
                "--download",
                str(tmp_path),
                "--parameters-file",
                str(param_file),
                "--parameter",
                "width=100",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_client.export.assert_called_once()
        call_kwargs = mock_client.export.call_args.kwargs
        assert call_kwargs["fmt"] == "svg"
        assert call_kwargs["dpi"] == "300"
        assert call_kwargs["width"] == "100"

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_with_tree_description(self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_abc"
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload",
                "--tree",
                tree_file,
                "--api-key-file",
                api_key_file,
                "--tree-description",
                "A test tree for PyiTOL",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_client.upload.assert_called_once()
        call_kwargs = mock_client.upload.call_args.kwargs
        assert call_kwargs["tree_description"] == "A test tree for PyiTOL"

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_upload_failure(self, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client_cls.side_effect = ValueError("bad key")

        result = runner.invoke(
            app,
            [
                "task",
                "upload",
                "--tree",
                tree_file,
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1
        assert "上传失败" in result.output


class TestTaskExport:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_export_success(self, mock_session_cls, mock_client_cls, tmp_path, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid123": tmp_path / "uid123.pdf"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 0, result.output
        assert "uid123.pdf" in result.output
        mock_client.export.assert_called_once_with(["uid123"], fmt="pdf", output_dir=str(tmp_path))

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_export_with_parameters_file(self, mock_session_cls, mock_client_cls, tmp_path, api_key_file):
        param_file = tmp_path / "params.txt"
        param_file.write_text("format=png\n")
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid123": tmp_path / "uid123.png"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
                "--parameters-file",
                str(param_file),
            ],
        )
        assert result.exit_code == 0, result.output
        mock_client.export.assert_called_once_with(["uid123"], fmt="png", output_dir=str(tmp_path))

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_export_with_parameters_option(self, mock_session_cls, mock_client_cls, tmp_path, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid123": tmp_path / "uid123.svg"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
                "--parameter",
                "format=svg",
                "--parameter",
                "dpi=300",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_client.export.assert_called_once_with(["uid123"], fmt="svg", dpi="300", output_dir=str(tmp_path))

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_export_with_parameter_list(self, mock_session_cls, mock_client_cls, tmp_path, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid123": tmp_path / "uid123.svg"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
                "--parameter",
                "format=svg",
                "--parameter",
                "dpi=300",
            ],
        )
        assert result.exit_code == 0, result.output
        mock_client.export.assert_called_once_with(["uid123"], fmt="svg", dpi="300", output_dir=str(tmp_path))

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_export_with_extra_params(self, mock_session_cls, mock_client_cls, tmp_path, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid123": tmp_path / "uid123.png"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
                "--parameter",
                "format=png",
                "--parameter",
                "display_mode=2",
                "--parameter",
                "ignore_branch_length=1",
                "--parameter",
                "arc=360",
                "--parameter",
                "line_width=3",
                "--parameter",
                "margin=200",
                "--parameter",
                "h_res=300",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "uid123.png" in result.output
        mock_client.export.assert_called_once()
        call_kwargs = mock_client.export.call_args.kwargs
        assert call_kwargs["fmt"] == "png"
        assert call_kwargs["extra_params"] == {
            "display_mode": "2",
            "ignore_branch_length": "1",
            "arc": "360",
            "line_width": "3",
            "margin": "200",
            "h_res": "300",
        }

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_export_failure(self, mock_client_cls, tmp_path, api_key_file):
        mock_client_cls.side_effect = RuntimeError("network error")

        result = runner.invoke(
            app,
            [
                "task",
                "export",
                "--upload-id",
                "uid123",
                "--download",
                str(tmp_path),
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1
        assert "导出失败" in result.output


class TestTaskUploadAndExport:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_and_export_success(self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_xyz"
        mock_client.export.return_value = {"tree_xyz": tmp_path / "tree_xyz.svg"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload-and-export",
                "--tree",
                tree_file,
                "--output",
                str(tmp_path / "out.svg"),
                "--api-key-file",
                api_key_file,
                "--wait",
                "0",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "tree_xyz" in result.output
        assert "out.svg" in result.output or "tree_xyz.svg" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_and_export_with_options(self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_xyz"
        mock_client.export.return_value = {"tree_xyz": tmp_path / "tree_xyz.png"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload-and-export",
                "--tree",
                tree_file,
                "--output",
                str(tmp_path / "out.png"),
                "--api-key-file",
                api_key_file,
                "--wait",
                "0",
                "--format",
                "png",
                "--dpi",
                "300",
                "--width",
                "800",
                "--height",
                "600",
            ],
        )
        assert result.exit_code == 0, result.output
        call_kwargs = mock_client.export.call_args.kwargs
        assert call_kwargs["fmt"] == "png"
        assert call_kwargs["dpi"] == 300
        assert call_kwargs["width"] == 800
        assert call_kwargs["height"] == 600

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_and_export_with_config_files(
        self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file
    ):
        cfg = tmp_path / "config.txt"
        cfg.write_text("DATASET_COLORSTRIP")
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_xyz"
        mock_client.export.return_value = {"tree_xyz": tmp_path / "tree_xyz.svg"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload-and-export",
                "--tree",
                tree_file,
                "--output",
                str(tmp_path / "out.svg"),
                "--api-key-file",
                api_key_file,
                "--wait",
                "0",
                "--config",
                str(cfg),
            ],
        )
        assert result.exit_code == 0, result.output
        args = mock_client.upload.call_args
        assert str(cfg) in args[0][1]

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_upload_and_export_failure(self, mock_client_cls, tmp_path, tree_file, api_key_file):
        mock_client_cls.side_effect = RuntimeError("fail")

        runner.invoke(
            app,
            [
                "task",
                "upload-and-export",
                "--tree",
                tree_file,
                "--output",
                str(tmp_path / "out.svg"),
                "--api-key-file",
                api_key_file,
            ],
        )

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_upload_and_export_with_parameters(
        self, mock_session_cls, mock_client_cls, tmp_path, tree_file, api_key_file
    ):
        """Verify --parameter passes datasets_visible and extra params to export."""
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_xyz"
        mock_client.export.return_value = {"tree_xyz": tmp_path / "tree_xyz.png"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "upload-and-export",
                "--tree",
                tree_file,
                "--output",
                str(tmp_path / "out.png"),
                "--api-key-file",
                api_key_file,
                "--wait",
                "0",
                "--format",
                "png",
                "--dpi",
                "300",
                "--parameter",
                "datasets_visible=0,1,2",
                "--parameter",
                "background=ffffff",
                "--parameter",
                "display_mode=2",
            ],
        )
        assert result.exit_code == 0, result.output
        call_kwargs = mock_client.export.call_args.kwargs
        assert call_kwargs["fmt"] == "png"
        assert call_kwargs["dpi"] == 300
        assert call_kwargs["datasets_visible"] == "0,1,2"
        assert call_kwargs["extra_params"]["background"] == "ffffff"
        assert call_kwargs["extra_params"]["display_mode"] == "2"


class TestTaskDelete:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_delete_success(self, mock_session_cls, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.batch_delete.return_value = {"id1": True, "id2": True}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--upload-id",
                "id1",
                "--upload-id",
                "id2",
                "--api-key-file",
                api_key_file,
                "--confirm",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "已删除" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.SessionContext")
    def test_delete_project_success(self, mock_session_cls, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.batch_delete_projects.return_value = {"MyProject": True}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--project",
                "MyProject",
                "--api-key-file",
                api_key_file,
                "--confirm",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "已删除项目" in result.output
        mock_client.batch_delete_projects.assert_called_once_with(["MyProject"])

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_delete_partial_failure(self, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.batch_delete.return_value = {"id1": True, "id2": False}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--upload-id",
                "id1",
                "--upload-id",
                "id2",
                "--api-key-file",
                api_key_file,
                "--confirm",
            ],
        )
        assert result.exit_code == 0, result.output
        assert "已删除" in result.output
        assert "删除失败" in result.output

    def test_delete_noninteractive_requires_confirm(self, api_key_file):
        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--upload-id",
                "id1",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1, result.output
        assert "--confirm" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.typer.prompt")
    def test_delete_interactive_confirm(self, mock_prompt, mock_client_cls, api_key_file):
        from pyitol.cli.task_cmd import task_delete

        mock_prompt.return_value = "y"
        mock_client = MagicMock()
        mock_client.batch_delete.return_value = {"id1": True}
        mock_client_cls.return_value = mock_client

        ctx = MagicMock()
        ctx.obj = None
        with patch("pyitol.cli.task_cmd.sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            task_delete(ctx, upload_ids=["id1"], project_names=None, api_key_file=api_key_file, confirm=False)

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    @patch("pyitol.cli.task_cmd.typer.prompt")
    def test_delete_interactive_cancel(self, mock_prompt, mock_client_cls, api_key_file):
        from pyitol.cli.task_cmd import task_delete

        mock_prompt.return_value = "n"

        ctx = MagicMock()
        ctx.obj = None
        with patch("pyitol.cli.task_cmd.sys.stdin") as mock_stdin:
            mock_stdin.isatty.return_value = True
            with pytest.raises(typer.Exit) as exc_info:
                task_delete(ctx, upload_ids=["id1"], project_names=None, api_key_file=api_key_file, confirm=False)
            assert exc_info.value.exit_code == 0

    def test_delete_no_ids(self, api_key_file):
        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1
        assert "必须指定至少一个" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_delete_exception(self, mock_client_cls, api_key_file):
        mock_client_cls.side_effect = RuntimeError("boom")

        result = runner.invoke(
            app,
            [
                "task",
                "delete",
                "--upload-id",
                "id1",
                "--api-key-file",
                api_key_file,
                "--confirm",
            ],
        )
        assert result.exit_code == 1
        assert "删除失败" in result.output


class TestTaskStatus:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_status_ready(self, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.query_status.return_value = {"status": "ready"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "status",
                "--tree-name",
                "my_tree",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 0, result.output
        assert "就绪" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_status_not_ready_with_response(self, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.query_status.return_value = {"status": "pending", "response": 202}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "status",
                "--tree-name",
                "my_tree",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1, result.output
        assert "pending" in result.output
        assert "202" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_status_not_ready_without_response(self, mock_client_cls, api_key_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.query_status.return_value = {"status": "unknown"}
        mock_client_cls.return_value = mock_client

        result = runner.invoke(
            app,
            [
                "task",
                "status",
                "--tree-name",
                "my_tree",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1, result.output
        assert "unknown" in result.output

    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_status_exception(self, mock_client_cls, api_key_file):
        mock_client_cls.side_effect = RuntimeError("down")

        result = runner.invoke(
            app,
            [
                "task",
                "status",
                "--tree-name",
                "my_tree",
                "--api-key-file",
                api_key_file,
            ],
        )
        assert result.exit_code == 1
        assert "查询失败" in result.output
