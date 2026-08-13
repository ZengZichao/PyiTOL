"""Tests for PyiTOL CLI main/top-level commands."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from pyitol.cli.main import _load_taxonomy_tree_data, app, main
from pyitol.core.validator import ValidationError

runner = CliRunner()

SIMPLE_NEWICK = "((A:0.1,B:0.2):0.3,(C:0.4,D:0.5):0.6);"
TAXONOMY_TSV = "id\tKingdom\tPhylum\tcount\tvalue\nA\tBacteria\tProteobacteria\t10\t0.5\nB\tBacteria\tProteobacteria\t20\t0.8\nC\tArchaea\tEuryarchaeota\t15\t0.3\nD\tArchaea\tEuryarchaeota\t25\t0.6\n"  # noqa: E501
TAXONOMY_SIMPLE_TSV = "id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n"


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


@pytest.fixture
def simple_taxonomy_file(tmp_path):
    p = tmp_path / "simple.tsv"
    p.write_text(TAXONOMY_SIMPLE_TSV)
    return str(p)


# =============================================================================
# CALLBACK TESTS
# =============================================================================


class TestMainCallback:
    def test_quiet_flag(self, tree_file):
        result = runner.invoke(app, ["--quiet", "validate", "--tree", tree_file])
        assert result.exit_code == 0, result.output

    def test_config_success(self, tree_file, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("key: value\n")
        result = runner.invoke(app, ["--config", str(config), "validate", "--tree", tree_file])
        assert result.exit_code == 0, result.output

    def test_config_failure(self, tree_file, tmp_path):
        config = tmp_path / "config.yaml"
        config.write_text("{bad")
        result = runner.invoke(app, ["--config", str(config), "validate", "--tree", tree_file])
        # Should continue with warning, not crash
        assert result.exit_code == 0, result.output


# =============================================================================
# VALIDATE COMMAND TESTS
# =============================================================================


class TestValidateCommand:
    def test_validate_tree(self, tree_file):
        result = runner.invoke(app, ["validate", "--tree", tree_file])
        assert result.exit_code == 0, result.output

    def test_validate_taxonomy(self, taxonomy_file):
        result = runner.invoke(app, ["validate", "--taxonomy", taxonomy_file])
        assert result.exit_code == 0, result.output

    def test_validate_colors(self):
        result = runner.invoke(app, ["validate", "--color", "#FF0000", "--color", "#00FF00"])
        assert result.exit_code == 0, result.output

    def test_validate_invalid_colors(self):
        result = runner.invoke(app, ["validate", "--color", "badcolor"])
        assert result.exit_code == 3

    def test_validate_warnings(self, tree_file):
        with patch("pyitol.cli.main.validate_inputs") as mock_validate:
            mock_validate.return_value = {"warnings": ["warn1"], "errors": []}
            result = runner.invoke(app, ["validate", "--tree", tree_file])
            assert result.exit_code == 0, result.output
            assert "warn1" in result.output
            mock_validate.assert_called_once()

    def test_validate_exception(self, tree_file):
        with patch("pyitol.cli.main.validate_inputs") as mock_validate:
            mock_validate.side_effect = RuntimeError("boom")
            result = runner.invoke(app, ["validate", "--tree", tree_file])
            assert result.exit_code == 1
            mock_validate.assert_called_once()


# =============================================================================
# LOAD TAXONOMY TREE DATA TESTS
# =============================================================================


class TestLoadTaxonomyTreeData:
    def test_load(self, tree_file, taxonomy_file):
        _tree, df, tip_set = _load_taxonomy_tree_data(tree_file, taxonomy_file, id_column="id")
        assert tip_set == {"A", "B", "C", "D"}
        assert set(df["id"].tolist()) == {"A", "B", "C", "D"}

    def test_load_rename_id_column(self, tree_file, tmp_path):
        tax = tmp_path / "tax.tsv"
        tax.write_text("sample\tKingdom\nA\tBacteria\nB\tBacteria\nC\tArchaea\nD\tArchaea\n")
        _tree, df, _tip_set = _load_taxonomy_tree_data(tree_file, str(tax), id_column="sample")
        assert "id" in df.columns


# =============================================================================
# REPLAY COMMAND TESTS
# =============================================================================


class TestReplayCommand:
    def _make_session(self, tmp_path, **kwargs):
        snap = tmp_path / "session.yaml"
        defaults = {
            "session_id": "test_001",
            "timestamp": "2024-01-01T00:00:00",
            "command_line": [],
            "inputs": {
                "tree": None,
                "taxonomy": None,
                "id_column": "id",
            },
            "outputs": {
                "output_dir": str(tmp_path),
                "generated_files": [],
            },
            "api_params": {},
            "files": [],
            "logs": [],
        }
        defaults.update(kwargs)
        import yaml

        snap.write_text(yaml.dump(defaults, default_flow_style=False, allow_unicode=True))
        return str(snap)

    # ------------------------------------------------------------------
    # Strategy 1: direct CLI replay
    # ------------------------------------------------------------------
    def test_replay_cli_success(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=["validate", "--tree", tree_file],
            logs=[],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "命令复现成功" in result.output

    def test_replay_cli_failure(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            command_line=["validate", "--color", "badcolor"],
            logs=[],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "命令复现失败" in result.output

    def test_replay_cli_dry_run(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=["validate", "--tree", tree_file],
            logs=[],
        )
        result = runner.invoke(app, ["replay", "--session", snap, "--dry-run"])
        assert result.exit_code == 0, result.output
        assert "dry-run" in result.output

    def test_replay_cli_no_logs_early_return(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=["validate", "--tree", tree_file],
            logs=[],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "回放完成" in result.output

    def test_replay_no_cli_uses_logs(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "tree_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.get_tree_info") as mock_info:
            mock_info.return_value = {"tip_count": 4}
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "tree_info" in result.output
            mock_info.assert_called_once()

    # ------------------------------------------------------------------
    # Old format compatibility
    # ------------------------------------------------------------------
    def test_replay_old_format(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            tree=tree_file,
            taxonomy=taxonomy_file,
            id_column="id",
            command_line=[],
            logs=[{"action": "tree_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        # Remove inputs so old top-level keys are used
        import yaml

        data = yaml.safe_load(Path(snap).read_text())
        del data["inputs"]
        del data["outputs"]
        Path(snap).write_text(yaml.dump(data, default_flow_style=False, allow_unicode=True))
        with patch("pyitol.cli.main.get_tree_info") as mock_info:
            mock_info.return_value = {"tip_count": 4}
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            mock_info.assert_called_once()

    # ------------------------------------------------------------------
    # Log-by-log dry_run
    # ------------------------------------------------------------------
    def test_replay_dry_run_logs(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[
                {"action": "tree_info", "detail": "", "timestamp": "2024-01-01 00:00:00"},
                {"action": "unknown", "detail": "", "timestamp": "2024-01-01 00:00:00"},
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap, "--dry-run"])
        assert result.exit_code == 0, result.output
        assert "回放完成" in result.output

    # ------------------------------------------------------------------
    # Action: tree_info
    # ------------------------------------------------------------------
    def test_replay_tree_info(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "tree_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.get_tree_info") as mock_info:
            mock_info.return_value = {"tip_count": 4}
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 tree-info" in result.output
            mock_info.assert_called_once()

    # ------------------------------------------------------------------
    # Action: taxonomy_ranks
    # ------------------------------------------------------------------
    def test_replay_taxonomy_ranks(self, tmp_path, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "taxonomy_ranks", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.get_ranks") as mock_ranks:
            mock_ranks.return_value = ["Kingdom", "Phylum"]
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 taxonomy-ranks" in result.output
            mock_ranks.assert_called_once()

    # ------------------------------------------------------------------
    # Action: taxonomy_extract
    # ------------------------------------------------------------------
    def test_replay_taxonomy_extract(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"taxonomy_extract": str(tmp_path / "extract.csv")},
            command_line=[],
            logs=[{"action": "taxonomy_extract", "detail": "rank=phylum", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.extract_taxonomy_with_stats") as mock_ext:
            mock_ext.return_value = ["Proteobacteria", "Euryarchaeota"]
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 taxonomy-extract" in result.output
            mock_ext.assert_called_once()

    # ------------------------------------------------------------------
    # Action: taxonomy_monophyly
    # ------------------------------------------------------------------
    def test_replay_taxonomy_monophyly(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"taxonomy_monophyly": str(tmp_path / "mono.csv")},
            command_line=[],
            logs=[{"action": "taxonomy_monophyly", "detail": "rank=phylum", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.check_monophyly") as mock_mono:
            mock_mono.return_value = [{"group": "Proteobacteria", "monophyletic": True}]
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 taxonomy-monophyly" in result.output
            mock_mono.assert_called_once()

    # ------------------------------------------------------------------
    # Action: validate
    # ------------------------------------------------------------------
    def test_replay_validate(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "validate", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.core.validator.validate_inputs") as mock_val:
            mock_val.return_value = {"warnings": [], "errors": []}
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 validate" in result.output
            mock_val.assert_called_once()

    # ------------------------------------------------------------------
    # Action: task_upload
    # ------------------------------------------------------------------
    def test_replay_task_upload_with_key(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "task_upload", "detail": "api_key=testkey", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.ITOLAPIClient") as mock_client:
            mock_inst = MagicMock()
            mock_inst.upload.return_value = "tree123"
            mock_client.return_value = mock_inst
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 upload" in result.output
            mock_client.assert_called_once()
            mock_inst.upload.assert_called_once()

    def test_replay_task_upload_no_key(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "task_upload", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "缺少 API 密钥" in result.output

    # ------------------------------------------------------------------
    # Action: task_export
    # ------------------------------------------------------------------
    def test_replay_task_export_with_params(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[
                {
                    "action": "task_export",
                    "detail": "upload_id=tree123,api_key=testkey,format=pdf",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        with patch("pyitol.cli.main.ITOLAPIClient") as mock_client:
            mock_inst = MagicMock()
            mock_inst.export.return_value = ["ok"]
            mock_client.return_value = mock_inst
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 export" in result.output
            mock_client.assert_called_once()
            mock_inst.export.assert_called_once()

    def test_replay_task_export_no_params(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "task_export", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "缺少 upload_id 或 API 密钥" in result.output

    # ------------------------------------------------------------------
    # Action: task_delete
    # ------------------------------------------------------------------
    def test_replay_task_delete_with_params(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[
                {
                    "action": "task_delete",
                    "detail": "upload_ids=tree123,api_key=testkey",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        with patch("pyitol.cli.main.ITOLAPIClient") as mock_client:
            mock_inst = MagicMock()
            mock_inst.batch_delete.return_value = ["ok"]
            mock_client.return_value = mock_inst
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现 delete" in result.output
            mock_client.assert_called_once()
            mock_inst.batch_delete.assert_called_once()

    def test_replay_task_delete_no_params(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "task_delete", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "缺少 upload_id 或 API 密钥" in result.output

    # ------------------------------------------------------------------
    # Template actions: color_strip
    # ------------------------------------------------------------------
    def test_replay_template_color_strip_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_color_strip": str(tmp_path / "color_strip.txt")},
            command_line=[],
            logs=[{"action": "template_color_strip", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_color_strip" in result.output

    def test_replay_template_color_strip_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_color_strip", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: branch
    # ------------------------------------------------------------------
    def test_replay_template_branch_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_branch": str(tmp_path / "branch.txt")},
            command_line=[],
            logs=[{"action": "template_branch", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_branch" in result.output

    def test_replay_template_branch_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_branch", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: simple_bar
    # ------------------------------------------------------------------
    def test_replay_template_simple_bar_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_simple_bar": str(tmp_path / "simple_bar.txt")},
            command_line=[],
            logs=[{"action": "template_simple_bar", "detail": "column=count", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_simple_bar" in result.output

    def test_replay_template_simple_bar_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_simple_bar", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: multi_bar
    # ------------------------------------------------------------------
    def test_replay_template_multi_bar_with_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_multi_bar": str(tmp_path / "multi_bar.txt")},
            command_line=[],
            logs=[
                {"action": "template_multi_bar", "detail": "columns=count,value", "timestamp": "2024-01-01 00:00:00"}
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_multi_bar" in result.output

    def test_replay_template_multi_bar_no_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_multi_bar", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: heatmap
    # ------------------------------------------------------------------
    def test_replay_template_heatmap_with_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_heatmap": str(tmp_path / "heatmap.txt")},
            command_line=[],
            logs=[{"action": "template_heatmap", "detail": "columns=count,value", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_heatmap" in result.output

    def test_replay_template_heatmap_no_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_heatmap", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: symbols
    # ------------------------------------------------------------------
    def test_replay_template_symbols_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_symbols": str(tmp_path / "symbols.txt")},
            command_line=[],
            logs=[{"action": "template_symbols", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_symbols" in result.output

    def test_replay_template_symbols_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_symbols", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: pie
    # ------------------------------------------------------------------
    def test_replay_template_pie_with_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_pie": str(tmp_path / "pie.txt")},
            command_line=[],
            logs=[{"action": "template_pie", "detail": "columns=count,value", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_pie" in result.output

    def test_replay_template_pie_no_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_pie", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: boxplot
    # ------------------------------------------------------------------
    def test_replay_template_boxplot(self, tmp_path, tree_file):
        # boxplot 模板需要 minimum/q1/median/q3/maximum 列，使用专用 taxonomy 文件
        boxplot_tsv = tmp_path / "boxplot_meta.tsv"
        boxplot_tsv.write_text("id\tminimum\tq1\tmedian\tq3\tmaximum\nA\t1\t2\t3\t4\t5\nB\t2\t3\t4\t5\t6\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(boxplot_tsv), "id_column": "id"},
            outputs={"template_boxplot": str(tmp_path / "boxplot.txt")},
            command_line=[],
            logs=[{"action": "template_boxplot", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_boxplot" in result.output

    def test_replay_template_boxplot_skipped(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_boxplot": str(tmp_path / "boxplot.txt")},
            command_line=[],
            logs=[{"action": "template_boxplot", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: gradient
    # ------------------------------------------------------------------
    def test_replay_template_gradient_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_gradient": str(tmp_path / "gradient.txt")},
            command_line=[],
            logs=[{"action": "template_gradient", "detail": "column=value", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_gradient" in result.output

    def test_replay_template_gradient_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_gradient", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: tree_colors
    # ------------------------------------------------------------------
    def test_replay_template_tree_colors_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_tree_colors": str(tmp_path / "tree_colors.txt")},
            command_line=[],
            logs=[{"action": "template_tree_colors", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_tree_colors" in result.output

    def test_replay_template_tree_colors_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax_na.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(tax), "id_column": "id"},
            outputs={"template_tree_colors": str(tmp_path / "tree_colors.txt")},
            command_line=[],
            logs=[{"action": "template_tree_colors", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_tree_colors" in result.output

    def test_replay_template_tree_colors_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_tree_colors", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: binary
    # ------------------------------------------------------------------
    def test_replay_template_binary_with_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_binary": str(tmp_path / "binary.txt")},
            command_line=[],
            logs=[
                {"action": "template_binary", "detail": "columns=Kingdom,Phylum", "timestamp": "2024-01-01 00:00:00"}
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_binary" in result.output

    def test_replay_template_binary_no_columns(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_binary", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: labels
    # ------------------------------------------------------------------
    def test_replay_template_labels_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_labels": str(tmp_path / "labels.txt")},
            command_line=[],
            logs=[{"action": "template_labels", "detail": "label_column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_labels" in result.output

    def test_replay_template_labels_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_labels", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: popup_info
    # ------------------------------------------------------------------
    def test_replay_template_popup_info(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_popup_info": str(tmp_path / "popup_info.txt")},
            command_line=[],
            logs=[{"action": "template_popup_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_popup_info" in result.output

    def test_replay_template_popup_info_skipped(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_popup_info": str(tmp_path / "popup_info.txt")},
            command_line=[],
            logs=[{"action": "template_popup_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: collapse
    # ------------------------------------------------------------------
    def test_replay_template_collapse_with_ids(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_collapse": str(tmp_path / "collapse.txt")},
            command_line=[],
            logs=[{"action": "template_collapse", "detail": "node_ids=A,B", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_collapse" in result.output

    def test_replay_template_collapse_no_ids(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_collapse", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: prune
    # ------------------------------------------------------------------
    def test_replay_template_prune_with_ids(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_prune": str(tmp_path / "prune.txt")},
            command_line=[],
            logs=[{"action": "template_prune", "detail": "node_ids=A,B", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_prune" in result.output

    def test_replay_template_prune_no_ids(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_prune", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: ranges
    # ------------------------------------------------------------------
    def test_replay_template_ranges_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_ranges": str(tmp_path / "ranges.txt")},
            command_line=[],
            logs=[{"action": "template_ranges", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_ranges" in result.output

    def test_replay_template_ranges_single_member(self, tmp_path, tree_file):
        tax = tmp_path / "tax_single.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\tBacteria\nC\tBacteria\nD\tArchaea\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(tax), "id_column": "id"},
            outputs={"template_ranges": str(tmp_path / "ranges.txt")},
            command_line=[],
            logs=[{"action": "template_ranges", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_ranges" in result.output

    def test_replay_template_ranges_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_ranges", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: text
    # ------------------------------------------------------------------
    def test_replay_template_text_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_text": str(tmp_path / "text.txt")},
            command_line=[],
            logs=[{"action": "template_text", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_text" in result.output

    def test_replay_template_text_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_text", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: external_shape
    # ------------------------------------------------------------------
    def test_replay_template_external_shape_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_external_shape": str(tmp_path / "external_shape.txt")},
            command_line=[],
            logs=[
                {"action": "template_external_shape", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_external_shape" in result.output

    def test_replay_template_external_shape_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_external_shape", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: connections, domains, spacing (skipped with message)
    # ------------------------------------------------------------------
    def test_replay_template_connections(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_connections": str(tmp_path / "connections.txt")},
            command_line=[],
            logs=[{"action": "template_connections", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "connections" in result.output

    def test_replay_template_domains(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_domains": str(tmp_path / "domains.txt")},
            command_line=[],
            logs=[{"action": "template_domains", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "domains" in result.output

    def test_replay_template_spacing(self, tmp_path):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": None, "taxonomy": None, "id_column": "id"},
            outputs={"template_spacing": str(tmp_path / "spacing.txt")},
            command_line=[],
            logs=[{"action": "template_spacing", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "spacing" in result.output

    # ------------------------------------------------------------------
    # Template actions: highlight
    # ------------------------------------------------------------------
    def test_replay_template_highlight_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_highlight": str(tmp_path / "highlight.txt")},
            command_line=[],
            logs=[{"action": "template_highlight", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_highlight" in result.output

    def test_replay_template_highlight_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax_na.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(tax), "id_column": "id"},
            outputs={"template_highlight": str(tmp_path / "highlight.txt")},
            command_line=[],
            logs=[{"action": "template_highlight", "detail": "column=Kingdom", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_highlight" in result.output

    def test_replay_template_highlight_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_highlight", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: style
    # ------------------------------------------------------------------
    def test_replay_template_style_branch(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_style": str(tmp_path / "style.txt")},
            command_line=[],
            logs=[
                {
                    "action": "template_style",
                    "detail": "column=Kingdom,style_type=branch",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_style" in result.output

    def test_replay_template_style_label(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_style": str(tmp_path / "style.txt")},
            command_line=[],
            logs=[
                {
                    "action": "template_style",
                    "detail": "column=Kingdom,style_type=label",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_style" in result.output

    def test_replay_template_style_label_background(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_style": str(tmp_path / "style.txt")},
            command_line=[],
            logs=[
                {
                    "action": "template_style",
                    "detail": "column=Kingdom,style_type=label_background",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_style" in result.output

    def test_replay_template_style_with_na(self, tmp_path, tree_file):
        tax = tmp_path / "tax_na.tsv"
        tax.write_text("id\tKingdom\nA\tBacteria\nB\t\nC\tArchaea\nD\tArchaea\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(tax), "id_column": "id"},
            outputs={"template_style": str(tmp_path / "style.txt")},
            command_line=[],
            logs=[
                {
                    "action": "template_style",
                    "detail": "column=Kingdom,style_type=branch",
                    "timestamp": "2024-01-01 00:00:00",
                }
            ],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_style" in result.output

    def test_replay_template_style_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_style", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Template actions: branch_gradient
    # ------------------------------------------------------------------
    def test_replay_template_branch_gradient_with_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_branch_gradient": str(tmp_path / "branch_gradient.txt")},
            command_line=[],
            logs=[{"action": "template_branch_gradient", "detail": "column=value", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_branch_gradient" in result.output

    def test_replay_template_branch_gradient_with_na_and_string(self, tmp_path, tree_file):
        tax = tmp_path / "tax_bg.tsv"
        tax.write_text("id\tvalue\nA\t1.0\nB\t\nC\tbad\nD\t2.0\n")
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": str(tax), "id_column": "id"},
            outputs={"template_branch_gradient": str(tmp_path / "branch_gradient.txt")},
            command_line=[],
            logs=[{"action": "template_branch_gradient", "detail": "column=value", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "复现 template_branch_gradient" in result.output

    def test_replay_template_branch_gradient_no_column(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            command_line=[],
            logs=[{"action": "template_branch_gradient", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output

    # ------------------------------------------------------------------
    # Fallback / unknown actions
    # ------------------------------------------------------------------
    def test_replay_unknown_template(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"template_foobar": str(tmp_path / "foobar.txt")},
            command_line=[],
            logs=[{"action": "template_foobar", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "foobar" in result.output

    def test_replay_taxonomy_fallback(self, tmp_path, tree_file, taxonomy_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": taxonomy_file, "id_column": "id"},
            outputs={"taxonomy_foobar": str(tmp_path / "out.txt")},
            command_line=[],
            logs=[{"action": "taxonomy_foobar", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "分类分析历史输出" in result.output

    def test_replay_unknown_action(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "magic", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        result = runner.invoke(app, ["replay", "--session", snap])
        assert result.exit_code == 0, result.output
        assert "暂不支持自动复现" in result.output

    def test_replay_exception_in_log(self, tmp_path, tree_file):
        snap = self._make_session(
            tmp_path,
            inputs={"tree": tree_file, "taxonomy": None, "id_column": "id"},
            command_line=[],
            logs=[{"action": "tree_info", "detail": "", "timestamp": "2024-01-01 00:00:00"}],
        )
        with patch("pyitol.cli.main.get_tree_info") as mock_info:
            mock_info.side_effect = RuntimeError("boom")
            result = runner.invoke(app, ["replay", "--session", snap])
            assert result.exit_code == 0, result.output
            assert "复现失败" in result.output
            mock_info.assert_called_once()


# =============================================================================
# MAIN ENTRY POINT TESTS
# =============================================================================


class TestMainEntryPoint:
    def test_main_filenotfound(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = FileNotFoundError("missing")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 3  # Data error
            mock_app.assert_called_once()

    def test_main_valueerror(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = ValueError("bad")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # Parameter error
            mock_app.assert_called_once()

    def test_main_connectionerror(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = ConnectionError("down")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            mock_app.assert_called_once()

    def test_main_timeouterror(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = TimeoutError("slow")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            mock_app.assert_called_once()

    def test_main_permissionerror(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = PermissionError("denied")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            mock_app.assert_called_once()

    def test_main_validationerror(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = ValidationError("invalid")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 2  # Validation error
            mock_app.assert_called_once()

    def test_main_generic_exception(self):
        with patch("pyitol.cli.main.app") as mock_app:
            mock_app.side_effect = RuntimeError("oops")
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1
            mock_app.assert_called_once()
