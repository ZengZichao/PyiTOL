# 变更日志

本文件记录本项目的所有重要变更。

本格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [1.0.2] - 2026-08-22

### 新增
- 基准产物版本戳：全部基准结果 JSON 内嵌 `_provenance`（`pyitol_version` + `git_commit`），
  由 `benchmarks/_bench_utils.py` 的 `bench_provenance()` 提供。

### 变更
- 在参考环境（Apple M5 / 32 GiB / macOS 26.6.2，Python 3.11.15）重跑全部基准（B1–B5），
  刷新 `benchmarks/` 下的 canonical 结果文件。

### 修复
- `benchmark_itol_acceptance.py`：诊断重发改用客户端解析后的 API key（兼容环境变量 / key 文件），
  并使 zip 内树文件名与 `treeName` 对齐，暴露真实服务端错误而非误导性的 "ERR 0"。

## [1.0.1] - 2026-08-21

### 变更
- 投稿元数据修复：pyproject Documentation URL、CITATION.cff 与 RELEASE.md 的 DOI 记录
  （Zenodo 22046669）；版本回退值同步为 1.0.1。代码逻辑与 1.0.0 完全一致。

## [1.0.0] - 2026-08-13

PyiTOL 首次发布。
