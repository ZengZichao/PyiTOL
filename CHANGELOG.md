# Changelog

English | [中文](CHANGELOG_CN.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.3] - 2026-08-26

### Added
- **Benchmarks**: the archived template scalability results
  (`benchmarks/template_scalability_results.json`) now also carry a 50,000-leaf
  data point (manuscript Table S7 draws on it). That point is produced by an
  explicit `python benchmarks/benchmark_scalability.py --sizes 100,1000,10000,50000`
  run: the default `TREE_SIZES` is still `[100, 1_000, 10_000]`, so anything
  above 10,000 leaves remains opt-in.

### Changed
- **Validator**: duplicate tip labels are now reported as hard errors (both the
  raw-Newick pre-parse check and the parsed-tree check) instead of warnings.
  Duplicate labels silently collapse distinct leaves in set-based monophyly
  diagnostics, so such inputs must be rejected before classification.
- **API client**: retries of non-idempotent POST requests now log an explicit
  warning that the server may have already processed the previous attempt
  (`_LoggingRetry`), because iTOL batch endpoints expose no idempotency keys;
  users should check the project after a retry to see whether duplicate uploads
  were created.

## [1.0.2] - 2026-08-22

### Added
- Benchmark provenance stamping: all benchmark result artifacts now embed
  `_provenance` (`pyitol_version` + `git_commit`) via `bench_provenance()` in
  `benchmarks/_bench_utils.py`.

### Changed
- Regenerated all benchmarks (B1–B5) on the reference environment
  (Apple M5 / 32 GiB / macOS 26.6.2, Python 3.11.15); refreshed canonical
  result files under `benchmarks/`.

### Fixed
- `benchmark_itol_acceptance.py`: diagnostic re-post now uses the
  client-resolved API key (supports env-var / key-file sources) and aligns the
  zip tree filename with `treeName`, surfacing real server errors instead of a
  misleading `ERR 0: Please provide your iTOL API key`.

## [1.0.1] - 2026-08-21

### Changed
- Metadata fixes for submission: pyproject Documentation URL, CITATION.cff and
  RELEASE.md DOI records (Zenodo 22046669); version fallback synced to 1.0.1.
  No code-logic changes relative to 1.0.0.

## [1.0.0] - 2026-08-13

Initial release of PyiTOL.
