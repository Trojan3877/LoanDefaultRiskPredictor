# Loan Default Risk Predictor

[![CI](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml/badge.svg)](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml)
[![Container scan](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/container-scan.yml/badge.svg)](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/container-scan.yml)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A research-oriented credit-risk classification pipeline built with pandas, LightGBM, Optuna, MLflow, FastAPI, Docker, and Kubernetes.

> This project is an engineering demonstration, not a credit decision system. It must not be used for lending decisions without representative-data validation, fairness analysis, calibration, legal review, monitoring, and human oversight.

## Research question

Given structured borrower and loan attributes, how accurately can a gradient-boosted classifier rank default risk on observations that were not used for preprocessing, hyperparameter selection, or fitting?

The primary endpoint is ROC-AUC. PR-AUC is reported because default is commonly a minority outcome. Recall, precision, F1, Brier score, accuracy, the decision threshold, and the full confusion matrix are recorded so ranking, calibration, and operating-point behavior are not collapsed into one number.

## Experimental design

- Unit of analysis: one loan record.
- Outcome: binary `defaulted` column.
- Split: stratified 80/20 holdout with seed 2025 by default.
- Leakage control: target encoding and all other learned transforms are fitted on the training partition only.
- Model selection: Optuna tunes LightGBM on an inner split of the training partition.
- Final evaluation: exactly one pass over the untouched outer holdout.
- Provenance: the metrics JSON records row counts, seed, split fraction, trial count, package versions, parameters, boosting rounds, elapsed training time, threshold, and timestamp.

A random row split does not estimate temporal or institution-to-institution generalization. For a production study, replace it with an out-of-time test set and an external validation cohort.

## Metrics and benchmarks

No empirical score is claimed in this README yet because the repository does not include a redistributable, versioned evaluation dataset or a committed metrics artifact. Earlier console metrics were computed on training data and are not treated as benchmark evidence.

| Measure | Recorded by trainer | Acceptance target* | Published result |
|---|---:|---:|---:|
| ROC-AUC | Yes | >= 0.82 | Pending dataset-backed run |
| PR-AUC | Yes | Report with prevalence | Pending |
| Recall | Yes | >= 0.70 | Pending |
| Precision | Yes | Context dependent | Pending |
| F1 | Yes | Context dependent | Pending |
| Brier score | Yes | Lower than prevalence baseline | Pending |
| Confusion matrix | Yes | Report counts | Pending |
| Training time | Yes | Report hardware with result | Pending |

*Targets are deployment gates, not measured performance. They must be reviewed against business costs, group-level error rates, and the dataset's default prevalence.

Run a reproducible benchmark:

```bash
python -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
python -m pip install -r requirements/dev.txt
python -m src.train \
  --uri data/loans.csv \
  --trials 40 \
  --seed 2025 \
  --test-size 0.20 \
  --threshold 0.50 \
  --output models/latest.joblib \
  --metrics-output outputs/metrics.json
```

The JSON output is the canonical result record. When publishing a result, commit a small redacted record under `benchmarks/` with the dataset name/version/hash, commit SHA, hardware, cohort definition, and any exclusions. Do not commit borrower-level data or model artifacts.

## Data contract

Required columns are defined in `src/data_loader.py`:

`loan_id`, `loan_amnt`, `term`, `emp_length`, `home_ownership`, `annual_inc`, `purpose`, `dti`, `delinq_2yrs`, `open_acc`, `pub_rec`, `revol_util`, `total_acc`, and `defaulted`.

The loader rejects missing columns, enforces dtypes, removes duplicate loan IDs, and drops incomplete rows. Dataset licensing, collection period, target observation window, and exclusion criteria remain the responsibility of each benchmark report.

## API

The current FastAPI service is a validated explanation facade. It validates a supplied risk score and feature contributions; it does not yet load `models/latest.joblib` or compute a risk score from raw borrower fields.

```bash
uvicorn api.inference_api:app --host 0.0.0.0 --port 8000
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/metrics
curl -X POST http://localhost:8000/predict \
  -H "content-type: application/json" \
  -d '{"risk_score":0.68,"top_features":{"dti":0.42,"revol_util":0.31}}'
```

Interactive API documentation is available at `http://localhost:8000/docs`.

## Nine-tier deployment hygiene

| Tier | Control | Repository evidence |
|---:|---|---|
| 1 | Reproducibility | Seeded split/tuning, package constraints, versioned metrics schema |
| 2 | Data and model contracts | Required schema, dtype checks, strict API request model |
| 3 | Test and quality gates | Ruff, mypy, Bandit, pytest/coverage, dependency audit, Compose and manifest validation in CI |
| 4 | Container hygiene | Slim image, non-root UID/GID, no pip cache, health check |
| 5 | Local orchestration | Compose health check, restart policy, read-only filesystem, pinned MLflow image |
| 6 | Kubernetes runtime | Probes, requests/limits, rolling update, dropped capabilities, seccomp, no service-account token |
| 7 | Supply chain | Trivy HIGH/CRITICAL gate, SPDX SBOM, GHCR publishing, keyless Cosign signing |
| 8 | Observability | Health/readiness endpoints and Prometheus request/latency metrics |
| 9 | Operational governance | Explicit model limitations, benchmark protocol, immutable-image guidance, rollback procedure |

The measurable L6 definition, ownership model, gate evidence, and exception policy are documented in [`docs/L6_ENGINEERING_QUALITY.md`](docs/L6_ENGINEERING_QUALITY.md).\n\nThe controls are a deployable baseline, not proof of compliance. Cloud IAM, network policy, secrets management, encrypted storage, audit retention, fairness monitoring, and incident response must be implemented in the target environment.

## Deployment and rollback

Build and verify locally:

```bash
docker build -t loan-risk-api:local .
docker compose up --build
docker run --rm -v "$PWD:/work" ghcr.io/yannh/kubeconform:v0.7.0 -strict -summary /work/infra/k8s
```

Release images are published by semantic-version tags and signed in GitHub Actions. Before applying Kubernetes manifests, replace the example image tag with the released image digest. Use an immutable digest in production.

```bash
kubectl apply -f infra/k8s/
kubectl rollout status deployment/loan-risk-api
kubectl rollout undo deployment/loan-risk-api   # rollback
```

Release gates should include: passing CI, container scan, signature verification, dataset-specific metric gates, calibration review, group-level error analysis, smoke tests, and an approved rollback owner.

## Repository layout

```text
api/                    FastAPI service and operational endpoints
src/                    data loading, feature engineering, training
tests/                  unit and contract tests
requirements/           separated runtime, training, and quality dependencies
docs/                   L6 quality standard and operational evidence
infra/k8s/              Kubernetes baseline
.github/workflows/      CI, scanning, publishing and signing
models/                 ignored runtime artifacts
outputs/                ignored local metrics and reports
```

## Known limitations

- No versioned benchmark dataset or publishable result record is included.
- The default evaluation is a single random holdout, not temporal or external validation.
- The service does not yet perform raw-feature model inference.
- Probability calibration, drift detection, protected-class fairness tests, and adverse-action reason governance are not implemented.
- Dropping missing rows can introduce selection bias and should be replaced by a documented missingness policy.

## License

MIT. Dataset licenses and regulatory obligations are separate from the source-code license.
