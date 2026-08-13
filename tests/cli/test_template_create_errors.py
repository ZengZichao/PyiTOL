"""Tests for template create missing-parameter validation branches."""

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tValue\nA\tBacteria\t10\nB\tBacteria\t20\nC\tArchaea\t30\nD\tArchaea\t40\n"


@pytest.fixture
def tree_file(tmp_path):
    p = tmp_path / "test.nwk"
    p.write_text(SIMPLE_NEWICK)
    return str(p)


@pytest.fixture
def taxonomy_file(tmp_path):
    p = tmp_path / "test.tsv"
    p.write_text(TAXONOMY_TSV)
    return str(p)


# 所有不带参数调用时应报错的 template 类型。
# 每种类型在缺失必需参数时都应返回 exit_code=1 并给出中文"需要"或英文 "required" 提示。
TEMPLATE_TYPES = [
    "color-strip",
    "branch",
    "simple-bar",
    "multi-bar",
    "heatmap",
    "symbols",
    "pie",
    "boxplot",
    "gradient",
    "connections",
    "labels",
    "popup-info",
    "domains",
    "binary",
    "text",
    "external-shape",
    "tree-colors",
    "branch-gradient",
    "collapse",
    "prune",
    "spacing",
    "ranges",
    "highlight",
    "style",
    "arrow",
    "linechart",
    "image",
    "alignment",
    "tanglegram",
    "placement",
    "timescale",
    "meme",
    "manual",
]


class TestTemplateCreateMissingParams:
    """Cover template_create() parameter validation (error) branches."""

    @pytest.mark.parametrize("template_type", TEMPLATE_TYPES)
    def test_missing_params(self, tmp_path, template_type):
        out = tmp_path / "out.txt"
        result = runner.invoke(app, ["template", "create", template_type, "--output", str(out)])
        assert result.exit_code == 1, result.output
        # 错误信息为中文（含"需要"），英文 fallback 含 "required"
        assert "需要" in result.output or "required" in result.output.lower()
