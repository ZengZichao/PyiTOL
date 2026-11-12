# 变更日志

[English](CHANGELOG.md) | 中文

本文件记录本项目的所有重要变更。

本格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [未发布]

## [1.0.3] - 2026-08-26

### 新增
- **基准**：模板可扩展性基准的存档结果（`benchmarks/template_scalability_results.json`）新增 50,000 叶
  数据点（论文表 S7 即取自该数据点）。该数据点由显式运行
  `python benchmarks/benchmark_scalability.py --sizes 100,1000,10000,50000` 得到：默认
  `TREE_SIZES` 仍为 `[100, 1_000, 10_000]`，超过 10,000 叶的规模仍需自行指定。

### 变更
- **验证器**：重复叶标签由警告升级为硬错误（原始 Newick 预解析检查与解析后树检查两处）。
  重复标签会在基于集合的单系诊断中静默合并不同的叶，因此必须在分类前拒绝此类输入。
- **API 客户端**：对非幂等 POST 请求的每次重试现在会输出明确警告（`_LoggingRetry`），
  提示服务器可能已处理上一次请求，因为 iTOL 批量接口不提供幂等键；
  用户应在重试后检查项目内是否产生重复上传。

## [1.0.2] - 2026-08-22

### 新增
- 基准产物版本戳：全部基准结果 JSON 内嵌 `_provenance`（`pyitol_version` + `git_commit`），
  由 `benchmarks/_bench_utils.py` 的 `bench_provenance()` 提供。

### 变更
- 在参考环境（Apple M5 / 32 GiB / macOS 26.6.2，Python 3.11.15）重跑全部基准（B1–B5），
  刷新 `benchmarks/` 下的规范结果文件（canonical）。

### 修复
- `benchmark_itol_acceptance.py`：诊断重发改用客户端解析后的 API 密钥（兼容环境变量 / 密钥文件），
  并使 zip 内树文件名与 `treeName` 对齐，从而暴露真实的服务端错误，
  而非误导性的报错原文 `"ERR 0: Please provide your iTOL API key"`。

## [1.0.1] - 2026-08-21

### 变更
- 投稿元数据修复：pyproject Documentation URL、CITATION.cff 与 RELEASE.md 的 DOI 记录
  （Zenodo 22046669）；版本回退值同步为 1.0.1。代码逻辑与 1.0.0 完全一致。

## [1.0.0] - 2026-08-13

PyiTOL 首次发布。
