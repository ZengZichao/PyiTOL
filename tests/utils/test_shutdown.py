"""Tests for graceful shutdown signal handling."""

import signal
from unittest.mock import MagicMock

import pytest

from pyitol.utils.shutdown import (
    GracefulShutdownContext,
    _cleanup_resources,
    _format_progress,
    _signal_handler,
    get_progress,
    is_shutdown_requested,
    register_file_handle,
    register_signal_handlers,
    register_temp_file,
    unregister_file_handle,
    unregister_temp_file,
    update_progress,
)


@pytest.fixture(autouse=True)
def reset_shutdown_state(monkeypatch):
    """每个测试前重置所有模块级全局状态，避免测试间污染。"""
    import pyitol.utils.shutdown as mod

    monkeypatch.setattr(mod, "_shutdown_requested", False)
    monkeypatch.setattr(mod, "_temp_files", set())
    monkeypatch.setattr(mod, "_open_handles", [])
    monkeypatch.setattr(mod, "_progress_info", {})


class TestSignalHandler:
    def test_sigint_exits_with_130(self):
        with pytest.raises(SystemExit) as exc_info:
            _signal_handler(signal.SIGINT, None)
        assert exc_info.value.code == 130

    def test_sigterm_exits_with_143(self):
        with pytest.raises(SystemExit) as exc_info:
            _signal_handler(signal.SIGTERM, None)
        assert exc_info.value.code == 143

    def test_second_signal_forces_exit(self):
        # 第一次信号设置 _shutdown_requested=True 并 exit
        # 模拟已收到一次信号的状态，第二次应强制退出 130
        import pyitol.utils.shutdown as mod

        mod._shutdown_requested = True
        with pytest.raises(SystemExit) as exc_info:
            _signal_handler(signal.SIGINT, None)
        assert exc_info.value.code == 130

    def test_signal_outputs_progress(self, capsys):
        update_progress(trees_processed=5, current_step="parsing")
        with pytest.raises(SystemExit):
            _signal_handler(signal.SIGINT, None)
        captured = capsys.readouterr()
        assert "Trees processed: 5" in captured.err
        assert "Current step: parsing" in captured.err

    def test_signal_writes_shutdown_message(self, capsys):
        with pytest.raises(SystemExit):
            _signal_handler(signal.SIGTERM, None)
        captured = capsys.readouterr()
        assert "SIGTERM" in captured.err
        assert "Shutting down" in captured.err
        assert "Cleanup complete" in captured.err


class TestCleanupResources:
    def test_cleanup_removes_temp_file(self, tmp_path):
        temp = tmp_path / "temp.txt"
        temp.write_text("cleanup me")
        register_temp_file(temp)
        _cleanup_resources()
        assert not temp.exists()

    def test_cleanup_clears_temp_files_set(self, tmp_path):
        register_temp_file(tmp_path / "a.txt")
        register_temp_file(tmp_path / "b.txt")
        _cleanup_resources()
        import pyitol.utils.shutdown as mod

        assert len(mod._temp_files) == 0

    def test_cleanup_idempotent(self, tmp_path):
        # 多次调用不应抛异常
        temp = tmp_path / "temp.txt"
        temp.write_text("x")
        register_temp_file(temp)
        _cleanup_resources()
        _cleanup_resources()  # 第二次：文件已删，应静默通过
        assert not temp.exists()

    def test_cleanup_skips_nonexistent_file(self, tmp_path):
        register_temp_file(tmp_path / "never_existed.txt")
        _cleanup_resources()  # 不应抛异常

    def test_cleanup_closes_open_handle(self):
        handle = MagicMock()
        handle.closed = False
        register_file_handle(handle)
        _cleanup_resources()
        handle.close.assert_called_once()

    def test_cleanup_skips_already_closed_handle(self):
        handle = MagicMock()
        handle.closed = True
        register_file_handle(handle)
        _cleanup_resources()
        handle.close.assert_not_called()

    def test_cleanup_clears_open_handles(self):
        h1 = MagicMock()
        h1.closed = False
        h2 = MagicMock()
        h2.closed = False
        register_file_handle(h1)
        register_file_handle(h2)
        _cleanup_resources()
        import pyitol.utils.shutdown as mod

        assert len(mod._open_handles) == 0


class TestTempFileRegistry:
    def test_register_and_unregister(self, tmp_path):
        p = tmp_path / "f.txt"
        register_temp_file(p)
        import pyitol.utils.shutdown as mod

        assert p in mod._temp_files
        unregister_temp_file(p)
        assert p not in mod._temp_files

    def test_unregister_nonexistent_is_noop(self, tmp_path):
        # 取消注册未注册的文件不应抛异常
        unregister_temp_file(tmp_path / "not_registered.txt")


class TestFileHandleRegistry:
    def test_register_and_unregister(self):
        h = MagicMock()
        register_file_handle(h)
        import pyitol.utils.shutdown as mod

        assert h in mod._open_handles
        unregister_file_handle(h)
        assert h not in mod._open_handles

    def test_unregister_nonexistent_is_noop(self):
        # 取消注册未注册的 handle 不应抛异常（ValueError 被捕获）
        unregister_file_handle(MagicMock())


class TestProgress:
    def test_update_and_get_progress(self):
        update_progress(trees_processed=3, current_step="loading")
        prog = get_progress()
        assert prog["trees_processed"] == 3
        assert prog["current_step"] == "loading"

    def test_get_progress_returns_copy(self):
        update_progress(files_generated=2)
        prog = get_progress()
        prog["files_generated"] = 999  # 修改返回值不应影响内部状态
        assert get_progress()["files_generated"] == 2

    def test_format_progress_empty(self):
        assert _format_progress() == ""

    def test_format_progress_all_fields(self):
        update_progress(trees_processed=10, current_step="rendering", files_generated=5)
        result = _format_progress()
        assert "Trees processed: 10" in result
        assert "Current step: rendering" in result
        assert "Files generated: 5" in result

    def test_format_progress_partial_fields(self):
        update_progress(current_step="done")
        result = _format_progress()
        assert "Current step: done" in result
        assert "Trees processed" not in result


class TestIsShutdownRequested:
    def test_initially_false(self):
        assert is_shutdown_requested() is False

    def test_true_after_signal(self):
        import pyitol.utils.shutdown as mod

        mod._shutdown_requested = True
        assert is_shutdown_requested() is True


class TestSignalRegistration:
    def test_register_signal_handlers(self):
        # 应不抛异常
        register_signal_handlers()


class TestGracefulShutdownContext:
    def test_context_manager_no_shutdown(self):
        # 正常上下文：check_shutdown 不应抛异常
        with GracefulShutdownContext() as ctx:
            ctx.check_shutdown()  # 无异常

    def test_check_shutdown_raises_when_requested(self):
        # 新实现采用「每上下文独立标记」：shutdown 信号经由 _active_context
        # 下发到正在运行的上下文，由上下文自身的 _shutdown_requested 触发
        # KeyboardInterrupt，不再依赖模块级全局标记（修复全局状态泄漏）。
        with GracefulShutdownContext() as ctx:
            ctx._shutdown_requested = True
            with pytest.raises(KeyboardInterrupt, match="Shutdown requested"):
                ctx.check_shutdown()

    def test_register_temp_cleans_up_on_exit(self, tmp_path):
        temp = tmp_path / "ctx_temp.txt"
        temp.write_text("data")
        with GracefulShutdownContext() as ctx:
            ctx.register_temp(temp)
            assert temp.exists()
        # 退出上下文后应清理
        assert not temp.exists()

    def test_register_handle_closes_on_exit(self):
        handle = MagicMock()
        handle.closed = False
        with GracefulShutdownContext() as ctx:
            ctx.register_handle(handle)
        handle.close.assert_called_once()

    def test_update_progress_delegates(self):
        with GracefulShutdownContext() as ctx:
            ctx.update_progress(trees_processed=7)
        assert get_progress()["trees_processed"] == 7

    def test_exit_does_not_suppress_exceptions(self):
        # 上下文内抛异常时，__exit__ 返回 False，异常应向上传播
        with pytest.raises(ValueError, match="boom"), GracefulShutdownContext():
            raise ValueError("boom")
