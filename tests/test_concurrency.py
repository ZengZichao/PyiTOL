"""Concurrency safety tests for PyiTOL."""

import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pyitol.api.client import ITOLAPIClient


class TestUploadConcurrency:
    """Test concurrent upload operations."""

    @pytest.mark.concurrency
    def test_concurrent_upload_different_zip_names(self, tmp_path):
        """Concurrent uploads must use unique temp zip filenames."""
        api_key_file = tmp_path / ".itolapi.key"
        api_key_file.write_text("test-key")
        api_key_file.chmod(0o600)

        tree_file = tmp_path / "tree.nwk"
        tree_file.write_text("(A:1,B:1);")
        template_file = tmp_path / "template.txt"
        template_file.write_text("DATASET_LABEL test\nSEPARATOR TAB\n")

        zip_paths = []
        lock = threading.Lock()

        def mock_post(url, files=None, data=None, timeout=None):
            # Capture the zip path from the file object
            if files and "zipFile" in files:
                zf = files["zipFile"][1]
                if hasattr(zf, "name"):
                    with lock:
                        zip_paths.append(Path(zf.name))
            resp = MagicMock()
            resp.status_code = 200
            resp.text = "SUCCESS: 12345"
            return resp

        client = ITOLAPIClient(api_key_file=str(api_key_file))

        threads = []
        for _ in range(5):
            t = threading.Thread(target=lambda: client.upload(str(tree_file), [str(template_file)]))
            threads.append(t)

        with patch.object(client.session, "post", side_effect=mock_post):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        assert len(zip_paths) == 5
        assert len(set(zip_paths)) == 5, f"Duplicate zip paths found: {zip_paths}"

    @pytest.mark.concurrency
    def test_concurrent_upload_no_file_leak(self, tmp_path):
        """Temp zip files must be cleaned up after concurrent uploads."""
        api_key_file = tmp_path / ".itolapi.key"
        api_key_file.write_text("test-key")
        api_key_file.chmod(0o600)

        tree_file = tmp_path / "tree.nwk"
        tree_file.write_text("(A:1,B:1);")
        template_file = tmp_path / "template.txt"
        template_file.write_text("DATASET_LABEL test\nSEPARATOR TAB\n")

        def mock_post(url, files=None, data=None, timeout=None):
            resp = MagicMock()
            resp.status_code = 200
            resp.text = "SUCCESS: 12345"
            return resp

        client = ITOLAPIClient(api_key_file=str(api_key_file))

        threads = []
        for _ in range(5):
            t = threading.Thread(target=lambda: client.upload(str(tree_file), [str(template_file)]))
            threads.append(t)

        with patch.object(client.session, "post", side_effect=mock_post):
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        # After a short delay, no .pyitol_upload_*.zip files should remain
        time.sleep(0.2)
        remaining = list(tmp_path.glob(".pyitol_upload_*.zip"))
        assert remaining == [], f"Leaked temp zip files: {remaining}"
