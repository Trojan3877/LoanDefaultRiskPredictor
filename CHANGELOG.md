# Changelog

All notable changes to **LoanDefaultRiskPredictor** are documented here. This project uses Semantic Versioning.

## [0.2.0] - 2026-08-26

### Added

- Evidence-backed GitHub Release and GHCR publishing workflow with semantic and immutable image tags.
- HIGH/CRITICAL release-image vulnerability gate, SPDX SBOM, keyless Cosign signing, and release checksums.
- CI-generated inference benchmark artifact carrying commit, model checksum, input hash, environment, distribution statistics, memory observation, success count/rate, and limitations.
- L6 engineering audit scorecard, expanded README system design, hard-evidence dashboard, Q&A, and engineering roadmap.

### Changed

- Corrected expected calibration error to a sample-weighted definition over fixed-width probability bins.
- Model serving now rejects non-finite or out-of-range probability outputs instead of silently clamping them.
- Training evidence now records `protocol.threshold` and `training_commit` explicitly.
- Aligned FastAPI service version with package version `0.2.0`.
- Raised the measured CI branch-coverage floor from 75% to 80%.
- Reframed reproducibility as a recorded procedure/environment because dependency specifications are bounded ranges rather than hash-locked builds.

### Evidence boundary

- No real-world lending-model quality, fair-lending compliance, calibration suitability, adverse-action validity, production SLO, or regulatory approval is claimed by this release.

## [0.1.0] - 2025-07-04

Historical pre-migration development milestone. The old changelog referenced release material under the former `Trojan3877` repository identity; those artifacts are not treated as evidence for the current repository.

[0.2.0]: https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/releases/tag/v0.2.0
