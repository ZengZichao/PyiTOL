#!/usr/bin/env python3
"""Watch for the iTOL project 'iTOL-API' to (re)appear, then run the full
template acceptance benchmark. Polls every 60 s for up to 60 minutes."""
from __future__ import annotations

import io
import os
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import requests

KEY = os.environ.get('ITOL_API_KEY', '')
if not KEY:
    raise SystemExit('Set the ITOL_API_KEY environment variable before running this watcher.')
PROJECT = 'iTOL-API'
URL = 'https://itol.embl.de/batch_uploader.cgi'
HERE = Path(__file__).resolve().parent
WORK = HERE / 'itol_acceptance'


def probe() -> bool:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as z:
        z.write(WORK / 'acceptance_test.tree', 'acceptance_test.tree')
        z.write(WORK / 'simple_bar.txt', 'simple_bar.txt')
    buf.seek(0)
    try:
        r = requests.post(URL, files={'zipFile': ('upload.zip', buf)},
                          data={'APIkey': KEY, 'treeName': 'watcher_probe',
                                'projectName': PROJECT}, timeout=120)
        return r.text.strip().startswith('SUCCESS')
    except Exception:  # noqa: BLE001
        return False


def main() -> None:
    deadline = time.time() + 3600
    while time.time() < deadline:
        if probe():
            print('PROJECT AVAILABLE — running acceptance benchmark', flush=True)
            proc = subprocess.run(
                [sys.executable, str(HERE / 'benchmark_itol_acceptance.py'),
                 '--api-key', KEY, '--project', PROJECT],
                cwd=str(HERE.parent), text=True)
            print(f'acceptance benchmark exit code: {proc.returncode}', flush=True)
            return
        print(f'{time.strftime("%H:%M:%S")} project not available yet', flush=True)
        time.sleep(60)
    print('TIMEOUT: project still not available after 60 minutes', flush=True)


if __name__ == '__main__':
    main()
