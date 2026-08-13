"""Session context manager - tracks input/output across a PyiTOL workflow.

Supports YAML session snapshots and replay functionality.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

from pyitol.exceptions import SessionError

# Use XDG_DATA_HOME for session logs directory (falls back to ~/.pyitol/session_logs)
_xdg_data_home = os.environ.get("XDG_DATA_HOME")
if _xdg_data_home:
    SESSION_LOG_DIR = Path(_xdg_data_home) / "pyitol" / "session_logs"
else:
    SESSION_LOG_DIR = Path.home() / ".pyitol" / "session_logs"


# Sensitive parameter name patterns that must be redacted in logs/snapshots.
_REDACT_PATTERNS = ("key", "token", "secret", "password")


def _redact_command_line(args: list[str]) -> list[str]:
    """Return a copy of command-line args with sensitive values redacted.

    Redacts the value attached to any flag whose name contains a sensitive
    pattern, for both ``--flag value`` and ``--flag=value`` forms, e.g.
    ``--api-key SECRET`` -> ``--api-key ***REDACTED***``.
    """
    redacted = list(args)
    for i, tok in enumerate(redacted):
        if not tok.startswith("-"):
            continue
        lowered = tok.lstrip("-").lower()
        if not any(p in lowered for p in _REDACT_PATTERNS):
            continue
        if "=" in tok:
            key, _, _value = tok.partition("=")
            redacted[i] = f"{key}=***REDACTED***"
        elif i + 1 < len(redacted) and not redacted[i + 1].startswith("-"):
            redacted[i + 1] = "***REDACTED***"
    return redacted


class FileMeta(BaseModel):
    """Metadata for a file in a session snapshot."""

    path: str
    size: int = 0
    checksum: str = ""
    algorithm: str = "sha256"


class SessionSnapshot(BaseModel):
    """Pydantic model for validating session snapshot YAML structure."""

    session_id: str = ""
    timestamp: str = ""
    environment: dict = Field(default_factory=dict)
    command_line: list[str] = Field(default_factory=list)
    duration_seconds: float = 0.0
    inputs: dict = Field(default_factory=dict)
    outputs: dict = Field(default_factory=dict)
    api_params: dict = Field(default_factory=dict)
    files: list[FileMeta] = Field(default_factory=list)
    logs: list[dict] = Field(default_factory=list)

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_timestamp(cls, v: datetime | str | None) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return str(v) if v else ""


def _file_size(path: Path) -> int:
    """Return file size in bytes, or 0 if not exists."""
    try:
        return path.stat().st_size
    except (OSError, FileNotFoundError):
        return 0


def _file_checksum(path: Path, algorithm: str = "sha256") -> str:
    """Return hex digest of file content, or empty string if not readable.

    Default algorithm is SHA-256 for scientific reproducibility.
    MD5 is available via algorithm='md5' for backward compatibility.
    Reads in 64KB chunks to avoid loading large files entirely into memory.
    """
    try:
        hasher = hashlib.new(algorithm)
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except (OSError, FileNotFoundError, ValueError):
        return ""


class SessionContext:
    """Manage input/output context for a PyiTOL session."""

    def __init__(
        self,
        tree_path: str | Path | None = None,
        taxonomy_path: str | Path | None = None,
        id_column: str = "id",
        output_dir: str | Path | None = None,
    ) -> None:
        self.tree_path = Path(tree_path) if tree_path else None
        self.taxonomy_path = Path(taxonomy_path) if taxonomy_path else None
        self.id_column = id_column
        self.output_dir = Path(output_dir) if output_dir else Path(".")
        self.generated_files: list[Path] = []
        self.session_outputs: dict = {}
        self._logs: list[dict] = []

        # Enhanced tracking fields
        self.command_line_args: list[str] = []
        self.input_files: dict[str, str | None] = {}
        self.output_files: dict[str, str | None] = {}
        self.api_params: dict = {}
        self.start_time: datetime = datetime.now()
        self.end_time: datetime | None = None
        self.file_checksums: dict[str, dict] = {}

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Mark the start of the session."""
        self.start_time = datetime.now()

    def finish(self) -> None:
        """Mark the end of the session."""
        self.end_time = datetime.now()

    # ------------------------------------------------------------------
    # Command / input / API recording
    # ------------------------------------------------------------------
    def record_command(self, args: list[str] | None = None) -> None:
        """Record the full command-line arguments (sensitive values are redacted)."""
        if args is None:
            args = sys.argv[1:]
        self.command_line_args = _redact_command_line([str(a) for a in args])

    def record_input(self, name: str, path: str | Path | None) -> None:
        """Record an input file path."""
        self.input_files[name] = str(path) if path else None

    def record_output(self, name: str, path: str | Path | None) -> None:
        """Record an output file path."""
        self.output_files[name] = str(path) if path else None

    def record_api_params(self, params: dict) -> None:
        """Record API parameters (api_key_file, tree_name, format, dpi, etc.)."""
        # Do NOT store raw api_key values for security; keep file path only
        safe = {}
        for k, v in params.items():
            if v and any(p in k.lower() for p in _REDACT_PATTERNS):
                safe[k] = "***REDACTED***"
            else:
                safe[k] = v
        self.api_params.update(safe)

    def compute_checksum(self, path: str | Path, algorithm: str = "sha256") -> str:
        """Compute and store checksum and size for a generated file.

        Returns the hex digest string.
        """
        p = Path(path)
        key = str(p)
        checksum = _file_checksum(p, algorithm)
        self.file_checksums[key] = {
            "size": _file_size(p),
            "checksum": checksum,
            "algorithm": algorithm,
        }
        return checksum

    # ------------------------------------------------------------------
    # Legacy helpers
    # ------------------------------------------------------------------
    def _append_log(self, action: str, detail: str = "") -> None:
        entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "detail": detail,
        }
        self._logs.append(entry)

    def set_output_dir(self, path: str | Path) -> None:
        self.output_dir = Path(path)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def resolve_output(self, filename: str) -> Path:
        path = self.output_dir / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        self.generated_files.append(path)
        return path

    def register_output(self, key: str, path: str | Path) -> None:
        p = Path(path)
        self.session_outputs[key] = str(p)
        self.generated_files.append(p)

    # ------------------------------------------------------------------
    # Log helpers (legacy)
    # ------------------------------------------------------------------
    def log_config(self, config: dict) -> None:
        self._append_log("config_init", f"配置文件: {config}")

    def log_taxonomy_extract(self, rank: str, count: int) -> None:
        self._append_log("taxonomy_extract", f"rank={rank}, count={count}")

    def log_taxonomy_monophyly(self, rank: str, group_count: int) -> None:
        self._append_log("taxonomy_monophyly", f"rank={rank}, groups={group_count}")

    def log_taxonomy_ranks(self, ranks: list[str]) -> None:
        self._append_log("taxonomy_ranks", f"ranks={ranks}")

    def log_task_upload(self, tree_id: str) -> None:
        self._append_log("task_upload", f"tree_id={tree_id}")

    def log_task_export(self, tree_ids: list[str], fmt: str) -> None:
        self._append_log("task_export", f"tree_ids={tree_ids}, format={fmt}")

    def log_task_upload_export(self, path: Path) -> None:
        self._append_log("task_upload_export", f"path={path}")

    def log_task_delete(self, tree_ids: list[str]) -> None:
        self._append_log("task_delete", f"tree_ids={tree_ids}")

    def log_task_run(self, config: dict) -> None:
        self._append_log("task_run", f"config={config}")

    def log_tree_info(self, tree_path: str, info: dict) -> None:
        self._append_log("tree_info", f"tree={tree_path}")

    def log_format_support_values(self, tree_path: str, fmt: str) -> None:
        self._append_log("format_support_values", f"tree={tree_path}, format={fmt}")

    def log_validate(self, file_path: str, file_type: str) -> None:
        self._append_log("validate", f"file={file_path}, type={file_type}")

    def log_learn(self, template_path: str) -> None:
        self._append_log("learn_template", f"template={template_path}")

    def log_error(self, error: str) -> None:
        self._append_log("error", error)

    # ------------------------------------------------------------------
    # Template generation logs
    # ------------------------------------------------------------------
    def log_template(self, template_type: str, output: str | Path, params: dict | None = None) -> None:
        """Log a template generation action with structured parameters."""
        detail_parts = [f"output={output}"]
        if params:
            for k, v in params.items():
                detail_parts.append(f"{k}={v}")
        self._append_log(f"template_{template_type}", ", ".join(detail_parts))

    # ------------------------------------------------------------------
    # Logs persistence (legacy)
    # ------------------------------------------------------------------
    def get_logs(self, limit: int = 20) -> list[dict]:
        all_logs = []
        log_file = SESSION_LOG_DIR / "current_session.json"
        if log_file.exists():
            try:
                all_logs = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                all_logs = []
        # Deduplicate: skip entries already present in the persisted log file.
        seen = {(e.get("timestamp"), e.get("action"), e.get("detail")) for e in all_logs}
        for entry in self._logs:
            key = (entry.get("timestamp"), entry.get("action"), entry.get("detail"))
            if key not in seen:
                all_logs.append(entry)
                seen.add(key)
        return all_logs[-limit:]

    def save_logs(self) -> None:
        SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
        log_file = SESSION_LOG_DIR / "current_session.json"
        existing = []
        if log_file.exists():
            try:
                existing = json.loads(log_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                existing = []
        all_logs = existing + self._logs
        log_file.write_text(json.dumps(all_logs, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_summary(self) -> dict:
        return {
            "tree": str(self.tree_path) if self.tree_path else None,
            "taxonomy": str(self.taxonomy_path) if self.taxonomy_path else None,
            "id_column": self.id_column,
            "output_dir": str(self.output_dir),
            "generated_files": [str(f) for f in self.generated_files],
            "outputs": self.session_outputs,
        }

    # ------------------------------------------------------------------
    # Version helpers for snapshot reproducibility
    # ------------------------------------------------------------------
    @staticmethod
    def _get_pyitol_version() -> str:
        """Return PyiTOL version string."""
        try:
            from pyitol import __version__

            return str(__version__)
        except (ImportError, AttributeError):
            return "unknown"

    @staticmethod
    def _get_dendropy_version() -> str:
        """Return DendroPy version string."""
        try:
            import dendropy

            return str(dendropy.__version__)
        except (ImportError, AttributeError):
            return "unknown"

    # ------------------------------------------------------------------
    # Snapshot (enhanced session.yaml)
    # ------------------------------------------------------------------
    def save_snapshot(
        self,
        output_path: str | Path | None = None,
        generated_files: list[str | Path] | None = None,
    ) -> Path:
        """Save a session snapshot YAML file for replay.

        Args:
            output_path: Path to save the snapshot YAML. Auto-generated if None.
            generated_files: Optional list of output file paths to register before saving.

        Returns:
            Path to the saved snapshot file.
        """
        if generated_files:
            for f in generated_files:
                p = Path(f)
                if p not in self.generated_files:
                    self.generated_files.append(p)
        if output_path is None:
            SESSION_LOG_DIR.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = SESSION_LOG_DIR / f"pyitol_{timestamp}.yaml"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure end_time is set (start_time is set in __init__)
        if self.end_time is None:
            self.end_time = datetime.now()

        duration = (self.end_time - self.start_time).total_seconds()

        # Auto-capture command line if not explicitly recorded
        cmd_line = self.command_line_args
        if not cmd_line:
            try:
                cmd_line = _redact_command_line(list(sys.argv[1:]))
            except (AttributeError, IndexError):
                cmd_line = []

        # Build files metadata for all generated files
        files_meta = []
        for p in self.generated_files:
            meta = {
                "path": str(p),
                "size": _file_size(p),
            }
            csum = _file_checksum(p)
            if csum:
                meta["checksum"] = csum
                meta["algorithm"] = "sha256"
            files_meta.append(meta)

        # Merge explicit checksum records
        for path_str, meta in self.file_checksums.items():
            if not any(f["path"] == path_str for f in files_meta):
                files_meta.append(
                    {
                        "path": path_str,
                        "size": meta.get("size", 0),
                        "checksum": meta.get("checksum", ""),
                        "algorithm": meta.get("algorithm", "sha256"),
                    }
                )

        snapshot = {
            "session_id": f"pyitol_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.getpid():05d}",
            "timestamp": self.start_time.isoformat() if self.start_time else datetime.now().isoformat(),
            "environment": {
                "pyitol_version": self._get_pyitol_version(),
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "dendropy_version": self._get_dendropy_version(),
            },
            "command_line": cmd_line,
            "duration_seconds": round(duration, 2),
            "inputs": {
                "tree": str(self.tree_path) if self.tree_path else None,
                "taxonomy": str(self.taxonomy_path) if self.taxonomy_path else None,
                "id_column": self.id_column,
                **{k: v for k, v in self.input_files.items() if v is not None},
            },
            "outputs": {
                "output_dir": str(self.output_dir),
                **self.session_outputs,
                **{k: v for k, v in self.output_files.items() if v is not None},
                "generated_files": [str(f) for f in self.generated_files],
            },
            "api_params": self.api_params,
            "files": files_meta,
            "logs": self._logs,
        }

        output_path.write_text(
            yaml.dump(snapshot, default_flow_style=False, allow_unicode=True, sort_keys=False),
            encoding="utf-8",
        )
        return output_path

    @staticmethod
    def load_snapshot(snapshot_path: str | Path) -> dict:
        """Load and validate a session snapshot from YAML file.

        Validates the snapshot structure against the SessionSnapshot pydantic model.
        Returns the raw dict (for backward compatibility with replay command).
        """
        path = Path(snapshot_path)
        if not path.exists():
            raise SessionError(f"Snapshot file not found: {snapshot_path}")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        # Validate structure (raises ValidationError on malformed snapshots)
        SessionSnapshot.model_validate(data)
        return data

    # Alias for replay command compatibility
    load_from_file = load_snapshot

    @classmethod
    def from_snapshot(cls, snapshot_path: str | Path) -> SessionContext:
        """Reconstruct a SessionContext from a snapshot file."""
        data = cls.load_snapshot(snapshot_path)
        ctx = cls(
            tree_path=data.get("inputs", {}).get("tree"),
            taxonomy_path=data.get("inputs", {}).get("taxonomy"),
            id_column=data.get("inputs", {}).get("id_column", "id"),
            output_dir=data.get("outputs", {}).get("output_dir", "."),
        )
        ctx.command_line_args = data.get("command_line", [])
        ctx.input_files = {
            k: v for k, v in data.get("inputs", {}).items() if k not in ("tree", "taxonomy", "id_column")
        }
        ctx.output_files = {
            k: v for k, v in data.get("outputs", {}).items() if k not in ("output_dir", "generated_files")
        }
        ctx.api_params = data.get("api_params", {})
        ctx.file_checksums = {f["path"]: f for f in data.get("files", [])}
        ctx._logs = data.get("logs", [])
        ctx.generated_files = [Path(p) for p in data.get("outputs", {}).get("generated_files", [])]
        # Restore session_outputs (non-file outputs like tree_id, etc.)
        ctx.session_outputs = {
            k: v
            for k, v in data.get("outputs", {}).items()
            if k not in ("output_dir", "generated_files") and k not in ctx.output_files
        }
        # Restore original timestamps from snapshot
        ts = data.get("timestamp")
        if ts:
            with contextlib.suppress(ValueError, TypeError):
                ctx.start_time = datetime.fromisoformat(ts) if isinstance(ts, str) else ts
        duration = data.get("duration_seconds")
        if duration is not None and ctx.start_time:
            ctx.end_time = ctx.start_time + timedelta(seconds=duration)
        return ctx


def create_session_log(
    output_path: str | Path,
    command: str,
    status: str,
    inputs: dict | None = None,
    outputs: dict | None = None,
    errors: list[str] | None = None,
    warnings: list[str] | None = None,
) -> Path:
    """Create a session log YAML file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    log = {
        "session_time": datetime.now().isoformat(),
        "command": command,
        "status": status,
        "inputs": inputs or {},
        "outputs": outputs or {},
        "errors": errors or [],
        "warnings": warnings or [],
    }

    path.write_text(yaml.dump(log, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    return path
