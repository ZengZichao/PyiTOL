"""Graceful shutdown handler for SIGINT and SIGTERM.

Registers signal handlers that:
- Stop current operations gracefully
- Output progress information
- Close open file handles
- Delete incomplete temporary files
- Exit with code 130 (SIGINT) or 143 (SIGTERM)
"""

from __future__ import annotations

import atexit
import contextlib
import logging
import signal
import sys
import threading
from pathlib import Path
from types import FrameType, TracebackType
from typing import IO, Any, Literal

logger = logging.getLogger(__name__)

# Global state for shutdown handling
_shutdown_requested = False
_shutdown_lock = threading.Lock()
_temp_files: set[Path] = set()
_open_handles: list = []
_progress_info: dict = {}
# Currently active GracefulShutdownContext (if any). Used to deliver a shutdown
# signal to the context that owns the running operation, instead of relying on
# the module-level _shutdown_requested flag (which, once set, would leak into
# unrelated later contexts).
_active_context: GracefulShutdownContext | None = None


def is_shutdown_requested() -> bool:
    """Check if shutdown has been requested. Thread-safe."""
    return _shutdown_requested


def register_temp_file(path: str | Path) -> None:
    """Register a temporary file for cleanup on shutdown."""
    _temp_files.add(Path(path))


def unregister_temp_file(path: str | Path) -> None:
    """Unregister a temp file (e.g., after successful completion)."""
    _temp_files.discard(Path(path))


def register_file_handle(handle: IO[Any]) -> None:
    """Register an open file handle for cleanup on shutdown."""
    _open_handles.append(handle)


def unregister_file_handle(handle: IO[Any]) -> None:
    """Unregister a file handle after closing."""
    with contextlib.suppress(ValueError):
        _open_handles.remove(handle)


def update_progress(**kwargs: object) -> None:
    """Update progress information for shutdown reporting."""
    _progress_info.update(kwargs)


def get_progress() -> dict:
    """Get current progress information."""
    return dict(_progress_info)


def _cleanup_resources() -> None:
    """Clean up all registered resources."""
    # Close open file handles
    for handle in list(_open_handles):
        try:
            if hasattr(handle, "close") and not handle.closed:
                handle.close()
        except Exception:  # noqa: S110
            pass
    _open_handles.clear()

    # Delete temporary files
    for path in list(_temp_files):
        try:
            p = Path(path)
            if p.exists():
                p.unlink()
                logger.debug(f"Cleaned up temp file: {path}")
        except OSError as e:
            logger.debug(f"Failed to clean up temp file {path}: {e}")
    _temp_files.clear()


def _format_progress() -> str:
    """Format current progress for display."""
    if not _progress_info:
        return ""

    parts = []
    if "trees_processed" in _progress_info:
        parts.append(f"Trees processed: {_progress_info['trees_processed']}")
    if "current_step" in _progress_info:
        parts.append(f"Current step: {_progress_info['current_step']}")
    if "files_generated" in _progress_info:
        parts.append(f"Files generated: {_progress_info['files_generated']}")
    return ", ".join(parts)


def _signal_handler(signum: int, frame: FrameType | None) -> None:
    """Handle SIGINT and SIGTERM signals."""
    global _shutdown_requested

    with _shutdown_lock:
        # Deliver the shutdown signal to the currently active context (if any)
        # so that only the operation that is actually running reacts to it,
        # rather than every future context via a leaked module-level flag.
        if _active_context is not None:
            _active_context._shutdown_requested = True

        if _shutdown_requested:
            # Second signal - force exit
            sys.stderr.write("\nForced exit.\n")
            sys.stderr.flush()
            _cleanup_resources()
            sys.exit(130)

        _shutdown_requested = True

    sig_name = signal.Signals(signum).name
    sys.stderr.write(f"\nReceived {sig_name}. Shutting down gracefully...\n")

    # Output progress
    progress = _format_progress()
    if progress:
        sys.stderr.write(f"Progress: {progress}\n")

    # Clean up resources
    _cleanup_resources()

    sys.stderr.write("Cleanup complete. Exiting.\n")
    sys.stderr.flush()

    # Determine exit code
    exit_code = 130 if signum == signal.SIGINT else 143
    sys.exit(exit_code)


def register_signal_handlers() -> None:
    """Register signal handlers for graceful shutdown.

    Call this once at application startup.
    """
    try:
        signal.signal(signal.SIGINT, _signal_handler)
        signal.signal(signal.SIGTERM, _signal_handler)
        logger.debug("Signal handlers registered for SIGINT and SIGTERM")
    except (OSError, ValueError) as e:
        # Some environments don't support signal registration
        logger.debug(f"Could not register signal handlers: {e}")

    # Register cleanup with atexit as fallback
    atexit.register(_cleanup_resources)


class GracefulShutdownContext:
    """Context manager for graceful shutdown handling.

    Usage:
        with GracefulShutdownContext() as ctx:
            for i, tree in enumerate(trees):
                ctx.check_shutdown()
                # process tree...
                ctx.update_progress(trees_processed=i+1)
    """

    def __init__(self) -> None:
        self._temp_files: list[Path] = []
        self._handles: list = []
        self._shutdown_requested = False

    def __enter__(self) -> GracefulShutdownContext:
        global _active_context
        _active_context = self
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> Literal[False]:
        # Clean up local resources AND unregister them from the global
        # tracking sets so they do not leak across contexts.
        for path in self._temp_files:
            unregister_temp_file(path)
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass

        for handle in self._handles:
            unregister_file_handle(handle)
            try:
                if hasattr(handle, "close") and not handle.closed:
                    handle.close()
            except Exception:  # noqa: S110
                pass

        # Drop this context from the global active slot so a later context
        # starts clean (no leaked shutdown state).
        global _active_context
        if _active_context is self:
            _active_context = None

        return False  # Don't suppress exceptions

    def check_shutdown(self) -> None:
        """Check if shutdown was requested and raise KeyboardInterrupt if so.

        Uses this context's own (per-operation) shutdown flag rather than the
        module-level flag, so a signal delivered to a previous operation can
        never cause a spurious interrupt in an unrelated later context.
        """
        if self._shutdown_requested:
            raise KeyboardInterrupt("Shutdown requested")

    def update_progress(self, **kwargs: object) -> None:
        """Update progress information."""
        update_progress(**kwargs)

    def register_temp(self, path: str | Path) -> Path:
        """Register a temp file for cleanup."""
        p = Path(path)
        self._temp_files.append(p)
        register_temp_file(p)
        return p

    def register_handle(self, handle: IO[Any]) -> IO[Any]:
        """Register a file handle for cleanup."""
        self._handles.append(handle)
        register_file_handle(handle)
        return handle
