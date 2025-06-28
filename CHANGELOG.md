# Changelog
All notable changes to **LoanDefaultRiskPredictor** will be documented here.

This project follows **Semantic Versioning 2.0.0** and the  
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) specification.

---

## [Unreleased]
### Added
- Grafana dashboard JSON
- Synthetic-data generator script
- MkDocs docs-deploy workflow
- Pre-commit config & Makefile

---

## [0.1.0] – 2025-07-04
### Added
- Modular Python package (`data_loader.py`, `feature_engineer.py`, `train.py`,
  `predict_api.py`, `inference.py`)
- LightGBM + Optuna training with MLflow & optional Snowflake logging
- FastAPI scoring service with Prometheus metrics & OTEL hooks
- Dockerfile (multi-stage) and `.dockerignore`
- GitHub Actions: build-test-coverage, Trivy container scan, GHCR publish
- Helm chart (`values.yaml`, deployment, service, HPA) + chart metadata
- README with badges, KPIs, architecture visual
- Unit & integration tests with Codecov upload
- MIT license

[Unreleased]: https://github.com/Trojan3877/LoanDefaultRiskPredictor/compare/v0.1.0...HEAD  
[0.1.0]: https://github.com/Trojan3877/LoanDefaultRiskPredictor/releases/tag/v0.1.0
