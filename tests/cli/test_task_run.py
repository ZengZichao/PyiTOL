"""Tests for task run CLI command with extended subcommands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import app

runner = CliRunner()

SIMPLE_NEWICK = "(A:0.1,B:0.2,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n"


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


class TestTaskRunArguments:
    def test_no_config(self):
        result = runner.invoke(app, ["task", "run"])
        assert result.exit_code == 1
        assert "必须指定 --config 或 --config-list" in result.output

    def test_both_config_and_config_list(self, tmp_path):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("command: upload\n")
        result = runner.invoke(app, ["task", "run", "--config", str(cfg), "--config-list", str(cfg)])
        assert result.exit_code == 1
        assert "不能同时使用" in result.output

    def test_config_not_found(self, tmp_path):
        result = runner.invoke(app, ["task", "run", "--config", str(tmp_path / "nope.yaml")])
        assert result.exit_code == 1
        assert "配置文件不存在" in result.output

    def test_single_config_is_list(self, tmp_path):
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("- command: upload\n  tree: foo.nwk\n")
        with patch("pyitol.cli.task_cmd.ITOLAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.upload.return_value = "tid"
            mock_cls.return_value = mock_client
            result = runner.invoke(app, ["task", "run", "--config", str(cfg)])
        assert result.exit_code == 0, result.output
        assert "不应为列表" in result.output

    def test_config_list_not_list(self, tmp_path):
        cfg = tmp_path / "list.yaml"
        cfg.write_text("command: upload\ntree: foo.nwk\n")
        with patch("pyitol.cli.task_cmd.ITOLAPIClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.upload.return_value = "tid"
            mock_cls.return_value = mock_client
            result = runner.invoke(app, ["task", "run", "--config-list", str(cfg)])
        assert result.exit_code == 0, result.output


def _make_context_mock(mock_client):
    """Configure a MagicMock to work as a context manager returning itself."""
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)
    return mock_client


class TestTaskRunUpload:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_upload_command(self, mock_client_cls, tmp_path, tree_file):
        mock_client = _make_context_mock(MagicMock())
        mock_client.upload.return_value = "tree_123"
        mock_client_cls.return_value = mock_client

        cfg = tmp_path / "cfg.yaml"
        cfg.write_text(f"""
command: upload
tree: {tree_file}
configs: []
name: my_dataset
api_key: test-key
""")
        result = runner.invoke(app, ["task", "run", "--config", str(cfg)])
        assert result.exit_code == 0, result.output
        assert "tree_123" in result.output
        mock_client.upload.assert_called_once_with(tree_file, [], project_name="my_dataset")


class TestTaskRunExport:
    @patch("pyitol.cli.task_cmd.ITOLAPIClient")
    def test_export_command(self, mock_client_cls, tmp_path):
        mock_client = _make_context_mock(MagicMock())
        mock_client.export.return_value = {"uid1": Path("/tmp/uid1.pdf")}
        mock_client_cls.return_value = mock_client

        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("""
command: export
upload_id: uid1
download: /tmp
api_key: test-key
parameters:
  format: pdf
  dpi: 300
""")
        result = runner.invoke(app, ["task", "run", "--config", str(cfg)])
        assert result.exit_code == 0, result.output
        assert "/tmp/uid1.pdf" in result.output or "导出成功" in result.output
        mock_client.export.assert_called_once_with(["uid1"], fmt="pdf", output_dir="/tmp", dpi=300)


class TestTaskRunExtract:
    def test_extract_command(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: extract
tree: {tree_file}
taxonomy: {taxonomy_file}
rank: Kingdom
output: {tmp_path}/extract.txt
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "extract.txt"
        assert output.exists()
        content = output.read_text()
        assert "Bacteria" in content
        assert "Archaea" in content

    def test_extract_missing_params(self, tmp_path, tree_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: extract
tree: {tree_file}
output: {tmp_path}/extract.txt
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 tree, taxonomy, rank 参数" in result.output


class TestTaskRunMonophyly:
    def test_monophyly_command(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: monophyly
tree: {tree_file}
taxonomy: {taxonomy_file}
rank: Kingdom
output: {tmp_path}/mono.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "mono.csv"
        assert output.exists()

    def test_monophyly_with_taxa(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: monophyly
tree: {tree_file}
taxonomy: {taxonomy_file}
taxa: Bacteria,Archaea
output: {tmp_path}/mono.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_monophyly_missing_tree_or_taxonomy(self, tmp_path, tree_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: monophyly
tree: {tree_file}
output: {tmp_path}/mono.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 tree 和 taxonomy 参数" in result.output

    def test_monophyly_missing_rank_and_taxa(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: monophyly
tree: {tree_file}
taxonomy: {taxonomy_file}
output: {tmp_path}/mono.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "必须指定 rank 或 taxa" in result.output


class TestTaskRunConvertBinary:
    def test_convert_binary(self, tmp_path):
        data = tmp_path / "data.csv"
        data.write_text("id\tA\tB\nX\t1\t\nY\t\t2\n")
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: convert-binary
input: {data}
columns: A,B
output: {tmp_path}/binary.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "binary.csv"
        assert output.exists()

    def test_convert_binary_missing_input(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text("""
command: convert-binary
output: out.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 input 参数" in result.output


class TestTaskRunConvertConnect:
    def test_convert_connect(self, tmp_path):
        data = tmp_path / "data.csv"
        data.write_text("id\tA\tB\nX\t1\t1\nY\t1\t0\nZ\t0\t1\n")
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: convert-connect
input: {data}
columns: A,B
output: {tmp_path}/connect.csv
min_weight: 0.1
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "connect.csv"
        assert output.exists()

    def test_convert_connect_missing_input(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text("""
command: convert-connect
output: out.csv
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 input 参数" in result.output


class TestTaskRunTemplate:
    def test_template_bundle(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: color-strip
    column: Kingdom
    label: kingdom_strip
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "kingdom_strip_1.txt"
        assert output.exists()
        content = output.read_text()
        assert "DATASET_COLORSTRIP" in content

    def test_template_missing_bundle(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 bundle 配置列表" in result.output

    def test_template_missing_tree_or_taxonomy(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text("""
command: template
output_dir: .
bundle:
  - type: color-strip
    column: Kingdom
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "需要 tree 和 taxonomy 参数" in result.output

    def test_template_highlight(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: highlight
    column: Kingdom
    label: kingdom_highlight
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_simple_bar(self, tmp_path, tree_file):
        tax = tmp_path / "tax.tsv"
        tax.write_text("id\tKingdom\tcount\nA\tBacteria\t10\nB\tBacteria\t20\nC\tArchaea\tNA\nD\tArchaea\t25\n")
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {tax}
output_dir: {tmp_path}
bundle:
  - type: simple-bar
    column: count
    label: my_bar
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_heatmap(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: heatmap
    column: value
    columns:
      - value
    label: my_heatmap
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_heatmap_two_colors(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: heatmap
    column: value
    columns:
      - value
    label: my_heatmap_2c
    color_gradient:
      - '#ff0000'
      - '#0000ff'
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_tree_colors(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: tree-colors
    column: Kingdom
    label: kingdom_colors
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_binary(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: binary
    column: Kingdom
    columns:
      - Kingdom
    label: kingdom_binary
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output

    def test_template_simple_bar_with_na_and_string(self, tmp_path, tree_file):
        taxonomy = tmp_path / "tax.tsv"
        taxonomy.write_text("id\tKingdom\tcount\nA\tBacteria\t10\nB\tBacteria\t\nC\tArchaea\tfoo\nD\tArchaea\t20\n")
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy}
output_dir: {tmp_path}
bundle:
  - type: simple-bar
    column: count
    label: my_bar
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "my_bar_1.txt"
        assert output.exists()
        content = output.read_text()
        assert "DATASET_SIMPLEBAR" in content
        assert "10" in content
        assert "20" in content

    def test_template_heatmap_two_color_gradient(self, tmp_path, tree_file):
        taxonomy = tmp_path / "tax.tsv"
        taxonomy.write_text("id\tKingdom\tvalue\nA\tBacteria\t1\nB\tBacteria\t2\nC\tArchaea\t3\nD\tArchaea\t4\n")
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy}
output_dir: {tmp_path}
bundle:
  - type: heatmap
    column: value
    columns:
      - value
    label: my_heatmap
    color_gradient:
      - '#ff0000'
      - '#0000ff'
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        output = tmp_path / "my_heatmap_1.txt"
        assert output.exists()
        content = output.read_text()
        assert "DATASET_HEATMAP" in content
        assert "COLOR_MAX" in content
        assert "USE_MID_COLOR" not in content

    def test_template_unknown_type(self, tmp_path, tree_file, taxonomy_file):
        config = tmp_path / "cfg.yaml"
        config.write_text(f"""
command: template
tree: {tree_file}
taxonomy: {taxonomy_file}
output_dir: {tmp_path}
bundle:
  - type: unknown-type
    column: Kingdom
    label: unk
""")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "忽略未知类型" in result.output


class TestTaskRunUnknownCommand:
    def test_unknown_command(self, tmp_path):
        config = tmp_path / "cfg.yaml"
        config.write_text("command: foobar\n")
        result = runner.invoke(app, ["task", "run", "--config", str(config)])
        assert result.exit_code == 0, result.output
        assert "未知命令" in result.output


class TestTaskRunException:
    @patch("pyitol.cli.task_cmd._load_config_file")
    def test_run_exception(self, mock_load, tmp_path):
        mock_load.side_effect = RuntimeError("boom")
        cfg = tmp_path / "cfg.yaml"
        cfg.write_text("command: upload\n")
        result = runner.invoke(app, ["task", "run", "--config", str(cfg)])
        assert result.exit_code == 1
        assert "运行失败" in result.output
