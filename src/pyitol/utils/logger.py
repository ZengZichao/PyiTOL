"""Real-time logging system with immediate flush (no color).

Provides timestamped log output that streams to stdout in real-time
without buffering. Supports DEBUG, INFO, WARNING, ERROR, CRITICAL levels.

Format: 2025-03-21T10:15:30.123 | INFO     | message
"""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Level tag mapping (right-padded to 8 chars)
_LEVEL_TAGS = {
    "DEBUG": "DEBUG    ",
    "INFO": "INFO     ",
    "WARNING": "WARNING  ",
    "ERROR": "ERROR    ",
    "CRITICAL": "CRITICAL ",
}


class RealTimeHandler(logging.Handler):
    """Logging handler that flushes immediately to stdout (plain text, no color).

    Features:
    - Real-time flush (no buffering)
    - ISO8601 timestamps with millisecond precision
    - Format: 2025-03-21T10:15:30.123 | INFO     | message
    """

    def __init__(self, show_time: bool = True) -> None:
        super().__init__()
        self.show_time = show_time

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record with real-time flush."""
        try:
            msg = self.format(record)
            sys.stdout.write(msg + "\n")
            # Force immediate flush
            sys.stdout.flush()
        except Exception:
            self.handleError(record)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text with ISO8601 timestamp."""
        # ISO8601 timestamp: 2025-03-21T10:15:30.123
        time_str = ""
        if self.show_time:
            ts = datetime.fromtimestamp(record.created)
            time_str = f"{ts.strftime('%Y-%m-%dT%H:%M:%S')}.{ts.strftime('%f')[:3]} | "

        # Level tag (right-padded)
        tag = _LEVEL_TAGS.get(record.levelname, record.levelname.ljust(9))

        # Module context (only for DEBUG)
        module_str = ""
        if record.levelno <= logging.DEBUG and record.module:
            module_str = f" [{record.module}:{record.lineno}]"

        return f"{time_str}{tag} | {record.getMessage()}{module_str}"


class StepTracker:
    """Track and display workflow steps with timing (plain text, no color).

    Usage:
        tracker = StepTracker()
        tracker.step("Loading tree file")
        # ... do work ...
        tracker.complete("Tree loaded successfully")
    """

    def __init__(self) -> None:
        self._step_num = 0
        self._step_start: float | None = None
        self._step_name = ""
        self._overall_start = time.time()

    def _print(self, msg: str) -> None:
        """Print and flush immediately."""
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    def step(self, description: str, file_path: str | None = None) -> None:
        """Start a new step."""
        self._step_num += 1
        self._step_start = time.time()
        self._step_name = description

        file_info = ""
        if file_path:
            name = Path(file_path).name
            file_info = f" [{name}]"

        self._print(f">>> Step {self._step_num}: {description}{file_info}")

    def complete(self, message: str = "", extra: str = "") -> None:
        """Complete the current step."""
        if self._step_start is None:
            return

        duration = time.time() - self._step_start
        duration_str = _format_duration(duration)

        extra_info = f" {extra}" if extra else ""
        self._print(f"    OK {message} ({duration_str}){extra_info}")
        self._step_start = None

    def warn(self, message: str) -> None:
        """Display a warning within the current step."""
        self._print(f"    WARN {message}")

    def fail(self, message: str) -> None:
        """Display a failure within the current step."""
        if self._step_start is not None:
            duration = time.time() - self._step_start
            duration_str = _format_duration(duration)
            self._print(f"    FAIL {message} ({duration_str})")
        else:
            self._print(f"    FAIL {message}")
        self._step_start = None

    def info(self, message: str) -> None:
        """Display an info message within the current step."""
        self._print(f"    - {message}")

    def summary(self, total_files: int = 0, total_items: int = 0) -> None:
        """Display overall summary."""
        total_duration = time.time() - self._overall_start
        duration_str = _format_duration(total_duration)

        parts = [f"Total time: {duration_str}"]
        if total_files:
            parts.append(f"Files: {total_files}")
        if total_items:
            parts.append(f"Items: {total_items}")

        self._print(f"\n=== {' | '.join(parts)} ===")


def _format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}us"
    elif seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    else:
        mins = int(seconds // 60)
        secs = seconds % 60
        return f"{mins}m{secs:.1f}s"


def setup_logging(
    level: int = logging.INFO,
    show_time: bool = True,
    log_file: str | Path | None = None,
) -> logging.Logger:
    """Setup the real-time logging system.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        show_time: Whether to show timestamps
        log_file: Optional file path for log output

    Returns:
        Configured root logger
    """
    root_logger = logging.getLogger("pyitol")
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Console handler with real-time flush
    handler = RealTimeHandler(show_time=show_time)
    handler.setLevel(level)
    root_logger.addHandler(handler)

    # Optional file handler (same format, with stack traces for DEBUG)
    if log_file:
        file_handler = logging.FileHandler(str(log_file), encoding="utf-8")
        file_handler.setLevel(level)
        file_fmt = logging.Formatter(
            "%(asctime)s.%(msecs)03d | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
        )
        file_handler.setFormatter(file_fmt)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str = "pyitol") -> logging.Logger:
    """Get a named logger.

    Args:
        name: Logger name. Defaults to ``pyitol`` (the root pyitol logger
            configured by :func:`setup_logging`). Returns ``logging.getLogger(name)``
            so callers get the expected logger instead of a nested ``pyitol.pyitol`` name.

    Returns:
        The named :class:`logging.Logger`.
    """
    return logging.getLogger(name)
