"""QA independent regression tests for Item 3: api/client.py robustness.

Verifies:
- A network failure during upload is wrapped as UploadError containing
  "network error" (and the temp zip is cleaned up in the finally block).
- A network failure during export is wrapped as ExportError containing
  "network error".
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
        assert "network error" in str(exc.value)

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


class TestExportErrorWrapping:
    def test_export_connection_error_wrapped(self, api_client):
        api_client.session.post = mock.MagicMock(side_effect=requests.ConnectionError("down"))
        with pytest.raises(ExportError) as exc:
            api_client.export(["123456"], fmt="pdf")
        assert "network error" in str(exc.value)
