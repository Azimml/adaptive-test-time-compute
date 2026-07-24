# Changelog

All notable changes to this project are documented here. The format is based
on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- MIT `LICENSE` file (previously only declared in metadata).
- `.editorconfig`, `.gitattributes`, and `.env.example` for consistent setup.
- `Makefile` with `install`, `lint`, `test`, `check`, and `run` targets.
- `CONTRIBUTING.md` describing the development workflow.

## [0.1.0]

Initial release.

### Added
- Consensus-based adaptive sampling controller with a triple stopping gate
  (`min_samples`, `min_agreement_count`, `confidence_threshold`).
- Fixed-N majority-vote baselines (`fixed_1`, `fixed_4`, `fixed_8`).
- Deterministic answer extraction and agreement computation (`evaluator.py`).
- GSM8K loader with preset-question fallback.
- Experiment runner with per-question details and JSON output.
- FastAPI server exposing REST and WebSocket APIs, plus an interactive web demo.
- Unit and behavioral test suite (26 tests) and GitHub Actions CI across
  Python 3.10–3.12.
- Pre-computed 300-question GSM8K results in `results/`.

[Unreleased]: https://github.com/Azimml/adaptive-test-time-compute/compare/main...HEAD
[0.1.0]: https://github.com/Azimml/adaptive-test-time-compute/releases/tag/v0.1.0
