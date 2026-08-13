"""Tests for PyiTOL session context module."""

from datetime import datetime
from pathlib import Path

import pytest
import yaml

from pyitol.exceptions import SessionError
from pyitol.utils.session import SessionContext, create_session_log


class TestSessionContext:
    def test_init(self, tmp_path):
        ctx = SessionContext(
            tree_path=tmp_path / "tree.nwk",
            taxonomy_path=tmp_path / "tax.tsv",
            output_dir=tmp_path / "out",
        )
        assert ctx.tree_path == tmp_path / "tree.nwk"
        assert ctx.taxonomy_path == tmp_path / "tax.tsv"
        assert ctx.output_dir == tmp_path / "out"
        assert ctx.id_column == "id"

    def test_start_finish(self):
        ctx = SessionContext()
        before = datetime.now()
        ctx.start()
        assert isinstance(ctx.start_time, datetime)
        assert ctx.start_time >= before
        ctx.finish()
        assert isinstance(ctx.end_time, datetime)
        assert ctx.end_time >= ctx.start_time

    def test_record_command(self):
        ctx = SessionContext()
        ctx.record_command(["template", "create", "color-strip"])
        assert ctx.command_line_args == ["template", "create", "color-strip"]

    def test_record_input_output(self):
        ctx = SessionContext()
        ctx.record_input("tree", "/path/to/tree.nwk")
        ctx.record_output("template", "/path/to/out.txt")
        assert ctx.input_files["tree"] == "/path/to/tree.nwk"
        assert ctx.output_files["template"] == "/path/to/out.txt"

    def test_record_api_params_redacts_key(self):
        ctx = SessionContext()
        ctx.record_api_params({"api_key": "secret123", "format": "pdf"})
        assert ctx.api_params["api_key"] == "***REDACTED***"
        assert ctx.api_params["format"] == "pdf"

    def test_compute_checksum(self, tmp_path):
        p = tmp_path / "data.txt"
        p.write_text("hello")
        ctx = SessionContext()
        ctx.compute_checksum(p)
        assert str(p) in ctx.file_checksums
        assert ctx.file_checksums[str(p)]["algorithm"] == "sha256"
        assert len(ctx.file_checksums[str(p)]["checksum"]) == 64

    def test_resolve_output(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        out = ctx.resolve_output("test.txt")
        assert out == tmp_path / "test.txt"
        assert out in ctx.generated_files

    def test_register_output(self, tmp_path):
        ctx = SessionContext()
        ctx.register_output("template", tmp_path / "out.txt")
        assert ctx.session_outputs["template"] == str(tmp_path / "out.txt")

    def test_log_helpers(self):
        ctx = SessionContext()
        ctx.log_taxonomy_extract("phylum", 5)
        ctx.log_task_upload("tree123")
        ctx.log_error("something failed")
        logs = ctx.get_logs(limit=10)
        assert len(logs) >= 3

    def test_save_and_load_snapshot(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        ctx.start()
        ctx.record_command(["test", "cmd"])
        out = tmp_path / "snap.yaml"
        ctx.save_snapshot(out)
        assert out.exists()
        data = SessionContext.load_snapshot(out)
        assert data["command_line"] == ["test", "cmd"]
        assert "session_id" in data

    def test_from_snapshot(self, tmp_path):
        ctx = SessionContext(tree_path=tmp_path / "tree.nwk", output_dir=tmp_path)
        ctx.start()
        ctx.record_input("meta", str(tmp_path / "meta.tsv"))
        out = tmp_path / "snap.yaml"
        ctx.save_snapshot(out)

        restored = SessionContext.from_snapshot(out)
        assert restored.output_dir == tmp_path
        assert restored.tree_path == tmp_path / "tree.nwk"
        assert restored.input_files.get("meta") == str(tmp_path / "meta.tsv")


class TestCreateSessionLog:
    def test_basic(self, tmp_path):
        p = tmp_path / "log.yaml"
        create_session_log(p, "template create", "success", inputs={"tree": "t.nwk"})
        assert p.exists()
        data = yaml.safe_load(p.read_text())
        assert data["command"] == "template create"
        assert data["status"] == "success"
        assert data["inputs"]["tree"] == "t.nwk"


class TestFileHelpers:
    def test_file_size_oserror(self, tmp_path):
        from pyitol.utils.session import _file_size

        # non-existent path returns 0
        assert _file_size(tmp_path / "nonexistent") == 0

    def test_file_checksum_valueerror(self, tmp_path):
        from pyitol.utils.session import _file_checksum

        # invalid algorithm raises ValueError which is caught
        p = tmp_path / "test.txt"
        p.write_text("hello")
        assert _file_checksum(p, algorithm="invalid") == ""

    def test_file_checksum_not_found(self, tmp_path):
        from pyitol.utils.session import _file_checksum

        assert _file_checksum(tmp_path / "nonexistent") == ""


class TestSessionContextEdgeCases:
    def test_record_command_default_argv(self):
        ctx = SessionContext()
        import sys

        original = sys.argv
        try:
            sys.argv = ["pyitol", "template", "create"]
            ctx.record_command()
            assert ctx.command_line_args == ["template", "create"]
        finally:
            sys.argv = original

    def test_set_output_dir(self, tmp_path):
        ctx = SessionContext()
        ctx.set_output_dir(tmp_path / "subdir")
        assert ctx.output_dir == tmp_path / "subdir"
        assert (tmp_path / "subdir").exists()

    def test_log_config(self):
        ctx = SessionContext()
        ctx.log_config({"key": "val"})
        assert any(log["action"] == "config_init" for log in ctx._logs)

    def test_log_taxonomy_monophyly(self):
        ctx = SessionContext()
        ctx.log_taxonomy_monophyly("phylum", 3)
        assert any(log["action"] == "taxonomy_monophyly" for log in ctx._logs)

    def test_log_taxonomy_ranks(self):
        ctx = SessionContext()
        ctx.log_taxonomy_ranks(["phylum", "class"])
        assert any(log["action"] == "taxonomy_ranks" for log in ctx._logs)

    def test_log_task_export(self):
        ctx = SessionContext()
        ctx.log_task_export(["t1"], "pdf")
        assert any(log["action"] == "task_export" for log in ctx._logs)

    def test_log_task_upload_export(self):
        ctx = SessionContext()
        ctx.log_task_upload_export(Path("/tmp/out.pdf"))
        assert any(log["action"] == "task_upload_export" for log in ctx._logs)

    def test_log_task_delete(self):
        ctx = SessionContext()
        ctx.log_task_delete(["t1", "t2"])
        assert any(log["action"] == "task_delete" for log in ctx._logs)

    def test_log_task_run(self):
        ctx = SessionContext()
        ctx.log_task_run({"config": "val"})
        assert any(log["action"] == "task_run" for log in ctx._logs)

    def test_log_tree_info(self):
        ctx = SessionContext()
        ctx.log_tree_info("/tmp/tree.nwk", {})
        assert any(log["action"] == "tree_info" for log in ctx._logs)

    def test_log_format_support_values(self):
        ctx = SessionContext()
        ctx.log_format_support_values("/tmp/tree.nwk", "pdf")
        assert any(log["action"] == "format_support_values" for log in ctx._logs)

    def test_log_learn(self):
        ctx = SessionContext()
        ctx.log_learn("/tmp/template.txt")
        assert any(log["action"] == "learn_template" for log in ctx._logs)

    def test_log_validate(self):
        ctx = SessionContext()
        ctx.log_validate("/tmp/file.txt", "template")
        assert any(log["action"] == "validate" for log in ctx._logs)

    def test_log_template_with_params(self):
        ctx = SessionContext()
        ctx.log_template("colorstrip", "/tmp/out.txt", params={"color": "#ff0000"})
        logs = [log for log in ctx._logs if log["action"] == "template_colorstrip"]
        assert len(logs) == 1
        assert "color=#ff0000" in logs[0]["detail"]

    def test_log_template_without_params(self):
        ctx = SessionContext()
        ctx.log_template("bar", "/tmp/out.txt")
        logs = [log for log in ctx._logs if log["action"] == "template_bar"]
        assert len(logs) == 1
        assert "output=/tmp/out.txt" in logs[0]["detail"]

    def test_get_logs_with_existing_file(self, tmp_path):
        from pyitol.utils.session import SESSION_LOG_DIR

        ctx = SessionContext()
        ctx._logs = [{"action": "test", "detail": "d", "timestamp": "2024-01-01 00:00:00"}]
        # patch SESSION_LOG_DIR temporarily
        original = SESSION_LOG_DIR
        try:
            import pyitol.utils.session as session_mod

            session_mod.SESSION_LOG_DIR = tmp_path
            log_file = tmp_path / "current_session.json"
            log_file.write_text('[{"action": "old", "detail": "x", "timestamp": "2023-01-01 00:00:00"}]')
            logs = ctx.get_logs(limit=10)
            assert len(logs) == 2
        finally:
            session_mod.SESSION_LOG_DIR = original

    def test_get_logs_decode_error(self, tmp_path):
        from pyitol.utils.session import SESSION_LOG_DIR

        ctx = SessionContext()
        original = SESSION_LOG_DIR
        try:
            import pyitol.utils.session as session_mod

            session_mod.SESSION_LOG_DIR = tmp_path
            log_file = tmp_path / "current_session.json"
            log_file.write_text("not json")
            logs = ctx.get_logs(limit=10)
            assert logs == []
        finally:
            session_mod.SESSION_LOG_DIR = original

    def test_save_logs_with_existing(self, tmp_path):
        from pyitol.utils.session import SESSION_LOG_DIR

        ctx = SessionContext()
        ctx._logs = [{"action": "test", "detail": "d", "timestamp": "2024-01-01 00:00:00"}]
        original = SESSION_LOG_DIR
        try:
            import pyitol.utils.session as session_mod

            session_mod.SESSION_LOG_DIR = tmp_path
            log_file = tmp_path / "current_session.json"
            log_file.write_text('[{"action": "old", "detail": "x", "timestamp": "2023-01-01 00:00:00"}]')
            ctx.save_logs()
            data = __import__("json").loads(log_file.read_text())
            assert len(data) == 2
        finally:
            session_mod.SESSION_LOG_DIR = original

    def test_save_logs_decode_error(self, tmp_path):
        from pyitol.utils.session import SESSION_LOG_DIR

        ctx = SessionContext()
        ctx._logs = [{"action": "test", "detail": "d", "timestamp": "2024-01-01 00:00:00"}]
        original = SESSION_LOG_DIR
        try:
            import pyitol.utils.session as session_mod

            session_mod.SESSION_LOG_DIR = tmp_path
            log_file = tmp_path / "current_session.json"
            log_file.write_text("bad json")
            ctx.save_logs()
            data = __import__("json").loads(log_file.read_text())
            assert len(data) == 1
        finally:
            session_mod.SESSION_LOG_DIR = original

    def test_get_summary(self, tmp_path):
        ctx = SessionContext(tree_path=tmp_path / "tree.nwk", output_dir=tmp_path)
        ctx.register_output("template", tmp_path / "out.txt")
        summary = ctx.get_summary()
        assert summary["tree"] == str(tmp_path / "tree.nwk")
        assert "out.txt" in summary["generated_files"][0]

    def test_save_snapshot_checksum(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        ctx.start()
        out_file = tmp_path / "test.txt"
        out_file.write_text("hello")
        ctx.generated_files.append(out_file)
        snap = tmp_path / "snap.yaml"
        ctx.save_snapshot(snap)
        data = yaml.safe_load(snap.read_text())
        files = data["files"]
        assert any(f["path"] == str(out_file) and "checksum" in f for f in files)

    def test_save_snapshot_merge_checksum(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        ctx.start()
        out_file = tmp_path / "test.txt"
        out_file.write_text("hello")
        ctx.compute_checksum(out_file)
        snap = tmp_path / "snap.yaml"
        ctx.save_snapshot(snap)
        data = yaml.safe_load(snap.read_text())
        files = data["files"]
        assert any(f["path"] == str(out_file) for f in files)

    def test_load_snapshot_not_found(self, tmp_path):
        with pytest.raises(SessionError):
            SessionContext.load_snapshot(tmp_path / "nonexistent.yaml")

    def test_load_from_file_alias(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        ctx.start()
        snap = tmp_path / "snap.yaml"
        ctx.save_snapshot(snap)
        data = SessionContext.load_from_file(snap)
        assert "session_id" in data

    def test_save_snapshot_no_args(self, tmp_path):
        from pyitol.utils.session import SESSION_LOG_DIR

        original = SESSION_LOG_DIR
        try:
            import pyitol.utils.session as session_mod

            session_mod.SESSION_LOG_DIR = tmp_path
            ctx = SessionContext(output_dir=tmp_path)
            ctx.start()
            path = ctx.save_snapshot()
            assert path.exists()
            assert path.name.startswith("pyitol_")
            assert path.suffix == ".yaml"
        finally:
            session_mod.SESSION_LOG_DIR = original

    def test_save_snapshot_no_start_time(self, tmp_path):
        ctx = SessionContext(output_dir=tmp_path)
        # Do not call start()
        snap = tmp_path / "snap.yaml"
        ctx.save_snapshot(snap)
        assert snap.exists()
        data = yaml.safe_load(snap.read_text())
        assert "duration_seconds" in data
