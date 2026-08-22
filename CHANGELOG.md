# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
  misleading "ERR 0: Please provide your iTOL API key".

## [1.0.1] - 2026-08-21

### Changed
- Metadata fixes for submission: pyproject Documentation URL, CITATION.cff and
  RELEASE.md DOI records (Zenodo 22046669); version fallback synced to 1.0.1.
  No code-logic changes relative to 1.0.0.

## [1.0.0] - 2026-08-13

Initial release of PyiTOL.
