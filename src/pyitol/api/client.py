"""API client for interacting with iTOL batch endpoints."""

from __future__ import annotations

import logging
import os
import stat
import tempfile
import time
import zipfile
from pathlib import Path
from types import TracebackType
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pyitol.exceptions import APIError, APIKeyError, ExportError, UploadError
from pyitol.utils.reporter import translate_itol_api_error

logger = logging.getLogger(__name__)


def parse_upload_response(response_text: str) -> tuple[bool, str, list[str]]:
    """Parse iTOL upload response text.

    Improved robustness - checks for actual success patterns more carefully
    and extracts tree ID from URLs properly (handles query parameters).

    Returns:
        Tuple of (success, tree_id_or_error, warnings)
    """
    text = response_text.strip()
    lines = text.split("\n")

    # Empty server responses still indicate a rejected upload; surface a
    # diagnostic marker instead of an empty error string.
    if not text:
        return False, "(iTOL 服务器返回空响应，请检查模板文件格式或稍后重试)", []

    # Error indicators are matched on whole-line/prefix basis so that a SUCCESS
    # substring inside prose cannot bypass detection (e.g. "your key is invalid,
    # see the SUCCESS page" must not be misread as success).
    error_indicators = ["ERROR", "FAIL", "INVALID", "UNAUTHORIZED"]
    for line in lines:
        u = line.strip().upper()
        for indicator in error_indicators:
            if u == indicator or u.startswith(f"{indicator} ") or u.startswith(f"{indicator}:"):
                return False, text, []

    # Only judge NOT FOUND when there is no success line at all (whole-line /
    # prefix match to avoid false positives).
    has_success_line = any(line.strip().upper().startswith("SUCCESS") for line in lines)
    if not has_success_line:
        for line in lines:
            stripped = line.strip().upper()
            if stripped == "NOT FOUND" or stripped.startswith("NOT FOUND "):
                return False, text, []

    # Look for success indicators
    has_success = False
    tree_id = ""
    warnings_list = []

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for SUCCESS keyword
        if line.upper().startswith("SUCCESS"):
            has_success = True
            if ":" in line:
                tree_id = line.split(":", 1)[1].strip()
            continue

        # Check for URL with tree ID
        if line.startswith("http://") or line.startswith("https://"):
            has_success = True
            # M1/m3: Use urlparse for proper URL parsing (handles query params)
            # Only set tree_id if not already extracted from a SUCCESS line
            if not tree_id:
                parsed = urlparse(line)
                path_parts = parsed.path.rstrip("/").split("/")
                if path_parts:
                    tree_id = path_parts[-1]
            continue

        # Check for tree ID pattern
        if "tree ID" in line or "treeId" in line:
            has_success = True
            parts = line.split()
            for i, part in enumerate(parts):
                if part.lower() in ("id:", "id"):
                    tree_id = parts[i + 1] if i + 1 < len(parts) else ""
                    break
            if not tree_id:
                tree_id = parts[-1] if parts else ""
            continue

        # Other lines are potential warnings
        if has_success:
            warnings_list.append(line)

    # Fallback: if we found a URL-like pattern in the text
    if not tree_id and text.startswith("http"):
        parsed = urlparse(text)
        if parsed.scheme in ("http", "https") and parsed.path:
            path_parts = parsed.path.rstrip("/").split("/")
            if path_parts:
                tree_id = path_parts[-1]
        elif not parsed.scheme or parsed.scheme not in ("http", "https"):
            # Fallback to simple split for malformed URLs
            tree_id = text.rstrip("/").split("/")[-1]

    # Guard: if server reported success but we couldn't extract a tree ID,
    # treat it as a parse failure so callers don't silently proceed with ''
    if has_success and not tree_id:
        return False, f"Server reported success but no tree ID could be extracted: {text}", []

    return has_success, tree_id, warnings_list


def parse_delete_response(response_text: str) -> tuple[bool, str]:
    """Parse iTOL delete response text.

    Returns:
        Tuple of (success, message)
    """
    text = response_text.strip()
    upper = text.upper()
    # Success indicators: SUCCESS (substring, tolerant of "SUCCESS: ..."), OK, DONE, true
    if "SUCCESS" in text or upper in ("OK", "DONE", "TRUE"):
        return True, text
    return False, text


class ITOLAPIClient:
    """Client for iTOL batch upload/export/delete APIs with retry support."""

    UPLOAD_URL = "https://itol.embl.de/batch_uploader.cgi"
    EXPORT_URL = "https://itol.embl.de/batch_downloader.cgi"
    DELETE_URL = "https://itol.embl.de/batch_delete.cgi"
    FORMAT_EXT_MAP = {  # noqa: RUF012
        "pdf": "pdf",
        "svg": "svg",
        "png": "png",
        "tiff": "tiff",
        "eps": "eps",
        "newick": "newick",
        "nexus": "nexus",
        "phyloxml": "phyloxml",
    }

    def __init__(
        self,
        api_key: str | None = None,
        api_key_file: str | None = ".itolapi.key",
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        timeout: float = 120.0,
        strict_permissions: bool = False,
    ) -> None:
        self.api_key = api_key or os.environ.get("ITOL_API_KEY")
        self.api_key_file = Path(api_key_file) if api_key_file else None
        self.timeout = timeout
        if not self.api_key and self.api_key_file and self.api_key_file.exists():
            # Enhanced security check for API key file permissions
            mode = self.api_key_file.stat().st_mode
            has_group_perms = mode & stat.S_IRWXG
            has_other_perms = mode & stat.S_IRWXO
            if has_group_perms or has_other_perms:
                msg = (
                    f"API key file {self.api_key_file} has overly permissive permissions. "
                    f"Consider running: chmod 600 {self.api_key_file}"
                )
                if strict_permissions:
                    raise APIKeyError(msg)
                logger.warning(msg)
            self.api_key = self.api_key_file.read_text(encoding="utf-8").strip()
        if not self.api_key:
            raise APIKeyError(
                "No API key provided. Either pass --api-key, set ITOL_API_KEY env var, "
                f"or create a key file at {self.api_key_file or '.itolapi.key'}"
            )

        # Configure session with retry strategy
        self.session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        # m9: Removed insecure http:// mount - all iTOL endpoints use HTTPS

    def close(self) -> None:
        """Close the underlying HTTP session."""
        self.session.close()

    def __enter__(self) -> ITOLAPIClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def upload(
        self,
        tree_file: str,
        template_files: list[str] | str,
        force: bool = False,
        datasets_visible: str | None = None,
        project_name: str | None = None,
        tree_description: str | None = None,
    ) -> str:
        """Upload tree and one or more template files to iTOL, return tree ID.

        All files are packed into a single zip archive (required by the
        batch uploader when using an API key).
        """
        if isinstance(template_files, str):
            template_files = [template_files] if template_files else []

        tree_path = Path(tree_file)
        # iTOL requires tree files inside the zip to have a .tree extension
        tree_arcname = tree_path.with_suffix(".tree").name

        # Use system temp directory instead of tree_path.parent for portability.
        # Build the zip and send it inside a single try/finally so the temp file is
        # always removed -- even if a template file is missing (FileNotFoundError)
        # or the network request fails (requests.RequestException).
        zip_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".zip", prefix=".pyitol_upload_", delete=False) as tmp:
                zip_path = Path(tmp.name)
            # Set secure permissions for temp file (HPC safety)
            os.chmod(zip_path, 0o600)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(tree_file, arcname=tree_arcname)
                for tf in template_files:
                    zf.write(tf, Path(tf).name)

            data = {
                "APIkey": self.api_key,
                "treeName": tree_path.stem,
                "projectName": project_name or tree_path.stem,
            }
            if force:
                data["force"] = "1"
            if datasets_visible:
                data["datasets_visible"] = datasets_visible
            if tree_description:
                data["treeDescription"] = tree_description

            response = None  # 避免非 requests 异常导致下方引用未绑定变量
            try:
                with open(zip_path, "rb") as f:
                    files = {"zipFile": ("upload.zip", f)}
                    response = self.session.post(self.UPLOAD_URL, files=files, data=data, timeout=self.timeout)
            except requests.RequestException as e:
                raise UploadError(f"Upload failed: network error - {e}") from e
        finally:
            if zip_path is not None:
                try:
                    zip_path.unlink(missing_ok=True)
                except OSError as e:
                    logger.warning(f"Failed to clean up temp zip {zip_path}: {e}")

        if response.status_code != 200:
            raise UploadError(f"Upload failed with status {response.status_code}: {response.text}")

        success, tree_id, warnings = parse_upload_response(response.text)
        if not success:
            friendly = translate_itol_api_error(tree_id)
            raise UploadError(friendly)

        for w in warnings:
            if w.strip():
                logger.warning("iTOL upload warning: %s", w)

        return tree_id

    def _validate_export_response(self, response: requests.Response, tree_id: str, format: str) -> None:
        """Validate that an export response contains actual file content, not an error page."""
        content = response.content
        content_type = response.headers.get("content-type", "").lower()

        # Check for HTML error pages (iTOL returns 200 with HTML error bodies)
        if "text/html" in content_type:
            friendly = translate_itol_api_error(response.text)
            raise ExportError(f"Export failed for {tree_id}: server returned HTML error page. {friendly}")

        # Check for short text responses that are likely errors, not real files
        if len(content) < 100 and ("text" in content_type or not content_type):
            text = content.decode("utf-8", errors="replace").strip()
            if text and not content.startswith(b"%PDF") and not content.startswith(b"\x89PNG"):
                friendly = translate_itol_api_error(text)
                raise ExportError(f"Export failed for {tree_id}: {friendly}")

        # Format-specific minimum size checks
        min_sizes = {"pdf": 500, "png": 200, "svg": 100, "tiff": 200, "eps": 200}
        min_size = min_sizes.get(format, 50)
        if len(content) < min_size:
            # Could be an error message saved as file content
            try:
                text = content.decode("utf-8", errors="replace").strip()
                if text and any(
                    kw in text.lower() for kw in ["error", "invalid", "failed", "not found", "unauthorized"]
                ):
                    friendly = translate_itol_api_error(text)
                    raise ExportError(f"Export failed for {tree_id}: {friendly}")
            except ExportError:
                raise
            except Exception:  # noqa: S110
                pass

    def export(
        self,
        tree_ids: list[str],
        fmt: str = "pdf",
        output_dir: str | Path | None = None,
        datasets_visible: str | None = None,
        dpi: int | None = None,
        width: int | None = None,
        height: int | None = None,
        extra_params: dict[str, str | int | float | bool] | None = None,
    ) -> dict[str, Path]:
        """Export trees from iTOL. Returns {tree_id: local_path}.

        Args:
            extra_params: Any additional iTOL batch export parameters
                (e.g. display_mode, ignore_branch_length, line_width, arc,
                current_font_size, margin, h_res, v_res, etc.). Values will
                be stringified automatically.
        """
        if not tree_ids:
            raise ValueError("tree_ids must not be empty")
        results = {}
        for tree_id in tree_ids:
            params: dict[str, str] = {"APIkey": self.api_key or "", "tree": tree_id, "format": fmt}
            if datasets_visible:
                params["datasets_visible"] = datasets_visible
            if dpi:
                params["dpi"] = str(dpi)
            if width:
                params["width"] = str(width)
            if height:
                params["height"] = str(height)
            if extra_params:
                for key, value in extra_params.items():
                    if value is None:
                        continue
                    if isinstance(value, bool):
                        params[key] = "1" if value else "0"
                    else:
                        params[key] = str(value)

            try:
                response = self.session.post(self.EXPORT_URL, data=params, timeout=self.timeout)
            except requests.RequestException as e:
                raise ExportError(f"Export failed for {tree_id}: network error - {e}") from e
            if response.status_code != 200:
                friendly = translate_itol_api_error(response.text)
                raise ExportError(f"Export failed for {tree_id}: status {response.status_code}. {friendly}")

            self._validate_export_response(response, tree_id, fmt)

            ext = self.FORMAT_EXT_MAP.get(fmt, "pdf")
            if output_dir:
                out_path = Path(output_dir)
                out_path.mkdir(parents=True, exist_ok=True)
                path = out_path / f"{tree_id}.{ext}"
            else:
                # With no directory given, files are written into the current
                # working directory and may overwrite same-name files — warn clearly.
                logger.warning(
                    "未指定 output_dir，导出文件 %s.%s 将写入当前工作目录，可能覆盖同名文件",
                    tree_id,
                    ext,
                )
                path = Path(f"{tree_id}.{ext}")
            path.write_bytes(response.content)
            results[tree_id] = path
        return results

    def delete(self, tree_id: str) -> bool:
        """Delete a single tree from iTOL."""
        results = self.batch_delete([tree_id])
        return results.get(tree_id, False)

    def batch_delete(self, tree_ids: list[str]) -> dict[str, bool]:
        """Delete multiple trees from iTOL. Returns {tree_id: success}.

        Consistent with upload/export: transport-layer exceptions (connection,
        timeout) are raised as ``APIError`` (retryable upstream); only server-side
        business failures (4xx/5xx) return ``False``.
        """
        results = {}
        for tree_id in tree_ids:
            data = {"APIkey": self.api_key, "tree": tree_id}
            try:
                response = self.session.post(self.DELETE_URL, data=data, timeout=self.timeout)
            except requests.RequestException as e:
                # Propagate transport errors instead of silently returning False
                raise APIError(f"删除树 {tree_id} 失败：网络错误 - {e}") from e
            if response.status_code != 200:
                friendly = translate_itol_api_error(response.text)
                logger.warning("删除树 %s 失败：%s", tree_id, friendly)
                results[tree_id] = False
                continue
            success, _ = parse_delete_response(response.text)
            results[tree_id] = success
        return results

    def delete_project(self, project_name: str) -> bool:
        """Delete a single project from iTOL."""
        results = self.batch_delete_projects([project_name])
        return results.get(project_name, False)

    def batch_delete_projects(self, project_names: list[str]) -> dict[str, bool]:
        """Delete multiple projects from iTOL. Returns {project_name: success}.

        Consistent with upload/export: transport-layer exceptions (connection,
        timeout) are raised as ``APIError``; only server-side business failures
        (4xx/5xx) return ``False``.
        """
        results = {}
        for project_name in project_names:
            data = {"APIkey": self.api_key, "project": project_name}
            try:
                response = self.session.post(self.DELETE_URL, data=data, timeout=self.timeout)
            except requests.RequestException as e:
                # Propagate transport errors instead of silently returning False
                raise APIError(f"删除项目 {project_name} 失败：网络错误 - {e}") from e
            if response.status_code != 200:
                friendly = translate_itol_api_error(response.text)
                logger.warning("删除项目 %s 失败：%s", project_name, friendly)
                results[project_name] = False
                continue
            success, _ = parse_delete_response(response.text)
            results[project_name] = success
        return results

    def upload_and_export(
        self,
        tree_file: str,
        template_files: list[str] | str,
        fmt: str = "pdf",
        output_dir: str = ".",
        wait_time: int = 120,
        poll_interval: int = 10,
        force: bool = False,
        datasets_visible: str | None = None,
        project_name: str | None = None,
        tree_description: str | None = None,
        dpi: int | None = None,
        width: int | None = None,
        height: int | None = None,
        extra_params: dict[str, str | int | float | bool] | None = None,
    ) -> Path:
        """Upload tree, wait briefly, then export. Returns local file path.

        Args:
            fmt: Output format (pdf/svg/png/tiff). Renamed from 'format' to avoid
                shadowing the built-in.
            wait_time: 最大等待秒数（用于约束首次等待时长）。
            poll_interval: 首次导出前的初始等待秒数（iTOL 无官方就绪接口，
                仅作为一次最小等待，不再逐轮轮询）。
            extra_params: Any additional iTOL batch export parameters.

        说明（H1）：iTOL 未提供官方的"树就绪状态"查询接口。原实现在每次轮询中
        都触发一次完整导出（``query_status`` 内部即一次 SVG 导出），既浪费导出
        配额、加重服务端延迟，判定也不稳定。现改为：做一次最小等待（不超过
        ``wait_time``）后直接导出一次。代价：本方法每次调用只会发起一次真实导出。
        """
        tree_id = self.upload(
            tree_file,
            template_files,
            force=force,
            datasets_visible=datasets_visible,
            project_name=project_name,
            tree_description=tree_description,
        )

        # iTOL has no official "readiness" endpoint.  We wait once (minimally)
        # and export exactly once, avoiding a poll loop in which every round
        # would trigger a full export (quota cost and unstable determination).
        initial_wait = min(poll_interval, wait_time)
        if initial_wait > 0:
            logger.info(
                "等待 %ds 后导出树 %s（iTOL 无官方就绪接口，每次调用仅一次导出）",
                initial_wait,
                tree_id,
            )
            time.sleep(initial_wait)

        results = self.export(
            [tree_id],
            fmt=fmt,
            output_dir=output_dir,
            datasets_visible=datasets_visible,
            dpi=dpi,
            width=width,
            height=height,
            extra_params=extra_params,
        )
        return results[tree_id]

    def query_status(self, tree_name: str, timeout: int = 10) -> dict:
        """Query the status of an uploaded tree by name.

        Note: iTOL does not provide a direct status query API.  This method
        issues one full SVG export against the export endpoint to decide whether
        the tree is ready (cost note: **every ``query_status`` call triggers one
        real export**).  Only ``requests.RequestException`` (connection/timeout
        and other transport errors) is caught; any other exception (e.g. a
        ``ValueError``/``KeyError`` caused by a code bug) propagates normally to
        aid debugging.

        Args:
            tree_name: The tree ID or name to query.
            timeout: Request timeout in seconds.

        Returns:
            Dict with 'status' ('ready' or 'unknown'), 'tree_name', and optional
            'response' (HTTP status code) or 'error' (error message).
        """
        # iTOL has no direct readiness endpoint; probe the export endpoint with
        # a single SVG export instead.
        params = {"APIkey": self.api_key, "tree": tree_name, "format": "svg"}
        try:
            response = self.session.post(self.EXPORT_URL, data=params, timeout=timeout)
        except requests.RequestException as e:
            # Catch transport errors only; let everything else propagate
            return {"status": "unknown", "tree_name": tree_name, "error": str(e)}

        if response.status_code != 200:
            return {"status": "unknown", "tree_name": tree_name, "response": response.status_code}

        # Check if the response looks like a valid SVG rather than an error page
        content = response.content
        is_svg = content.startswith(b"<?xml") or content.startswith(b"<svg")
        is_text_error = b"<html" in content[:200].lower() or b"<!doctype" in content[:200].lower()

        if is_svg and not is_text_error and len(content) > 100:
            return {"status": "ready", "tree_name": tree_name}
        return {"status": "unknown", "tree_name": tree_name, "response": response.status_code}
