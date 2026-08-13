"""Tests for the python -m pyitol entry point (__main__.py)."""

import runpy
from unittest.mock import patch


class TestMainEntryPoint:
    """验证 `python -m pyitol` 入口能正确调用 cli.main.main()。"""

    def test_main_called_on_module_run(self):
        # mock main 避免真正启动 CLI（会阻塞等待参数）
        with patch("pyitol.cli.main.main") as mock_main:
            runpy.run_module("pyitol", run_name="__main__")
            mock_main.assert_called_once()

    def test_main_called_with_no_args(self):
        # 确认 main 被调用且无额外参数传递（main 自己从 sys.argv 读取）
        with patch("pyitol.cli.main.main") as mock_main:
            runpy.run_module("pyitol", run_name="__main__")
            assert mock_main.call_count == 1
            args, _kwargs = mock_main.call_args
            assert len(args) == 0
