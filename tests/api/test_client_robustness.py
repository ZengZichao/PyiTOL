"""Independent QA regression tests for Item 3: api/client.py robustness.

Verifies, independently of the other QA engineers' suites:
- A network failure during ``upload`` is wrapped as ``UploadError`` that
  contains the substring "network error".
- A network failure during ``export`` is wrapped as ``ExportError`` that
  contains the substring "network error".
- The temporary upload zip is cleaned up by the ``try/finally`` block both
  when the network request fails AND when an earlier error (a missing
  template file -> FileNotFoundError) occurs before the request is made.
"""

import tempfile as _tempfile
from pathlib import Path
from unittest import mock

import pytest
import requests

from pyitol.api.client import ITOLAPIClient
from pyitol.exceptions import ExportError, UploadError


@pytest.fixture
def api_client():
    return ITOLAPIClient(api_key="test-key")


@pytest.fixture
def tree_and_template(tmp_path):
    tree = tmp_path / "tree.nwk"
    tree.write_text("(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);")
    tmpl = tmp_path / "tmpl.txt"
    tmpl.write_text("DATASET_COLORSTRIP\nSEPARATOR TAB\n")
    return str(tree), str(tmpl)


class TestUploadErrorWrapping:
    def test_connection_error_wrapped_as_upload_error(self, api_client, tree_and_template):
        tree, tmpl = tree_and_template
        api_client.session.post = mock.MagicMock(side_effect=requests.ConnectionError("boom"))
        with pytest.raises(UploadError) as exc:
            api_client.upload(tree, [tmpl])
        assert "network error" in str(exc.value).lower()

    def test_temp_zip_cleaned_on_network_error(self, api_client, tree_and_template, tmp_path, monkeypatch):
        tree, tmpl = tree_and_template
        created = []
        orig = _tempfile.NamedTemporaryFile

        def fake_named_tempfile(**kwargs):
            kwargs = dict(kwargs)
            kwargs["dir"] = str(tmp_path)
            f = orig(**kwargs)
            created.append(f.name)
            return f

        monkeypatch.setattr("tempfile.NamedTemporaryFile", fake_named_tempfile)
        api_client.session.post = mock.MagicMock(side_effect=requests.ConnectionError("boom"))
        with pytest.raises(UploadError):
            api_client.upload(tree, [tmpl])

        assert created, "NamedTemporaryFile was never called"
        for name in created:
            assert not Path(name).exists(), f"temp zip {name} was not cleaned up"

    def test_temp_zip_cleaned_on_missing_template_error(self, api_client, tree_and_template, tmp_path, monkeypatch):
        # The error happens BEFORE the network request (zf.write of a missing
        # template file raises FileNotFoundError). The finally block must still
        # clean up the zip. This exercises a distinct code path from the
        # network-error case above.
        tree, _ = tree_and_template
        missing_tmpl = str(tmp_path / "does_not_exist.txt")
        created = []
        orig = _tempfile.NamedTemporaryFile

        def fake_named_tempfile(**kwargs):
            kwargs = dict(kwargs)
            kwargs["dir"] = str(tmp_path)
            f = orig(**kwargs)
            created.append(f.name)
            return f

        monkeypatch.setattr("tempfile.NamedTemporaryFile", fake_named_tempfile)

        with pytest.raises(FileNotFoundError):
            api_client.upload(tree, [missing_tmpl])

        assert created, "NamedTemporaryFile was never called"
        for name in created:
            assert not Path(name).exists(), f"temp zip {name} was not cleaned up"


class TestExportErrorWrapping:
    def test_export_connection_error_wrapped(self, api_client):
        api_client.session.post = mock.MagicMock(side_effect=requests.ConnectionError("down"))
        with pytest.raises(ExportError) as exc:
            api_client.export(["123456"], fmt="pdf")
        assert "network error" in str(exc.value).lower()
