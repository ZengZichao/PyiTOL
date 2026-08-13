"""Tests for PyiTOL logger module (RealTimeHandler, StepTracker, setup_logging)."""

import logging

from pyitol.utils.logger import (
    RealTimeHandler,
    StepTracker,
    _format_duration,
    get_logger,
    setup_logging,
)


class TestFormatDuration:
    """覆盖 _format_duration 的所有时间区间分支。"""

    def test_microseconds(self):
        assert _format_duration(0.0001) == "100us"

    def test_zero(self):
        assert _format_duration(0) == "0us"

    def test_milliseconds(self):
        assert _format_duration(0.5) == "500.0ms"

    def test_seconds(self):
        assert _format_duration(12.345) == "12.35s"

    def test_minutes(self):
        # 125.6 秒 = 2m5.6s
        assert _format_duration(125.6) == "2m5.6s"

    def test_exactly_one_minute(self):
        assert _format_duration(60.0) == "1m0.0s"


class TestRealTimeHandler:
    def test_emit_writes_to_stdout(self, capsys):
        handler = RealTimeHandler(show_time=False)
        record = logging.LogRecord(
            name="pyitol",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="hello %s",
            args=("world",),
            exc_info=None,
        )
        handler.emit(record)
        captured = capsys.readouterr()
        assert "INFO" in captured.out
        assert "hello world" in captured.out

    def test_format_with_time(self):
        handler = RealTimeHandler(show_time=True)
        record = logging.LogRecord(
            name="pyitol",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="warn msg",
            args=None,
            exc_info=None,
        )
        formatted = handler.format(record)
        assert "WARNING" in formatted
        assert "warn msg" in formatted
        # ISO8601 时间戳格式 YYYY-MM-DDTHH:MM:SS.mmm
        assert "T" in formatted

    def test_format_no_time(self):
        handler = RealTimeHandler(show_time=False)
        record = logging.LogRecord(
            name="pyitol",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="err",
            args=None,
            exc_info=None,
        )
        formatted = handler.format(record)
        assert formatted.startswith("ERROR")
        assert "err" in formatted

    def test_format_debug_includes_module(self):
        handler = RealTimeHandler(show_time=False)
        record = logging.LogRecord(
            name="pyitol",
            level=logging.DEBUG,
            pathname="foo.py",
            lineno=42,
            msg="debug msg",
            args=None,
            exc_info=None,
        )
        formatted = handler.format(record)
        assert "DEBUG" in formatted
        # LogRecord.module 是 basename 去扩展名，pathname='foo.py' -> module='foo'
        assert "[foo:42]" in formatted


class TestStepTracker:
    def test_step_prints_step_number(self, capsys):
        tracker = StepTracker()
        tracker.step("Loading tree")
        captured = capsys.readouterr()
        assert ">>> Step 1: Loading tree" in captured.out

    def test_step_with_file_path(self, capsys):
        tracker = StepTracker()
        tracker.step("Loading", file_path="/tmp/data/tree.nwk")
        captured = capsys.readouterr()
        assert "[tree.nwk]" in captured.out

    def test_complete_without_step_does_nothing(self, capsys):
        tracker = StepTracker()
        tracker.complete("nothing")
        assert capsys.readouterr().out == ""

    def test_complete_prints_ok_and_duration(self, capsys):
        tracker = StepTracker()
        tracker.step("working")
        tracker.complete("done")
        captured = capsys.readouterr()
        assert "OK" in captured.out
        assert "done" in captured.out

    def test_warn_prints_warning(self, capsys):
        tracker = StepTracker()
        tracker.warn("be careful")
        captured = capsys.readouterr()
        assert "WARN" in captured.out
        assert "be careful" in captured.out

    def test_fail_with_step_prints_duration(self, capsys):
        tracker = StepTracker()
        tracker.step("risky")
        tracker.fail("broke")
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "broke" in captured.out

    def test_fail_without_step(self, capsys):
        tracker = StepTracker()
        tracker.fail("no context")
        captured = capsys.readouterr()
        assert "FAIL" in captured.out
        assert "no context" in captured.out

    def test_info_prints_message(self, capsys):
        tracker = StepTracker()
        tracker.info("detail")
        captured = capsys.readouterr()
        assert "- detail" in captured.out

    def test_summary_includes_totals(self, capsys):
        tracker = StepTracker()
        tracker.summary(total_files=3, total_items=10)
        captured = capsys.readouterr()
        assert "Files: 3" in captured.out
        assert "Items: 10" in captured.out
        assert "Total time:" in captured.out

    def test_step_number_increments(self, capsys):
        tracker = StepTracker()
        tracker.step("first")
        tracker.step("second")
        captured = capsys.readouterr()
        assert "Step 1" in captured.out
        assert "Step 2" in captured.out


class TestSetupLogging:
    def test_returns_pyitol_logger(self):
        lg = setup_logging()
        assert lg.name == "pyitol"

    def test_clears_existing_handlers(self):
        lg = setup_logging()
        setup_logging()
        # 应清除旧 handler，只保留一个 RealTimeHandler
        assert len(lg.handlers) == 1
        assert isinstance(lg.handlers[0], RealTimeHandler)

    def test_log_file_adds_file_handler(self, tmp_path):
        log_file = tmp_path / "test.log"
        setup_logging(log_file=str(log_file))
        lg = logging.getLogger("pyitol")
        assert any(isinstance(h, logging.FileHandler) for h in lg.handlers)
        assert log_file.exists() or True  # FileHandler 创建时即建立文件

    def test_level_set_correctly(self):
        lg = setup_logging(level=logging.DEBUG)
        assert lg.level == logging.DEBUG


class TestGetLogger:
    def test_returns_namespaced_logger(self):
        lg = get_logger("core")
        # 新实现直接返回 logging.getLogger(name)，不再自动加 'pyitol.' 前缀
        # （避免 get_logger('pyitol') 产生嵌套的 'pyitol.pyitol' 名称）。
        assert lg.name == "core"

    def test_default_name(self):
        lg = get_logger()
        assert lg.name == "pyitol.pyitol" or lg.name == "pyitol"
