# Loan Default Risk Predictor

[![CI](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/CoreyLeath-code/LoanDefaultRiskPredictor)](LICENSE)

Loan Default Risk Predictor is a research-oriented LightGBM pipeline and model-backed FastAPI service. It demonstrates traceable model packaging, input validation, and serving controls for experimentation with loan-risk data.

> This repository is **not an approved credit-decision system**. Do not use it to make lending decisions without representative-data validation, fair-lending and calibration review, privacy and legal approval, human oversight, and environment-specific security controls.

## Implemented capabilities

- Leakage-conscious feature engineering, training-only fitted transformations, and identifier exclusion.
- A versioned model bundle with a SHA-256 manifest, threshold, policy version, dataset identifier, and training metadata.
- Model-backed `POST /predict`; serving starts only with a verified bundle in production.
- Strict loan-request validation and deterministic reason-code placeholders for research review.
- API-key support, in-process rate limiting, bounded concurrency, security headers, readiness, and Prometheus metrics.
- Feedback capture with a required timezone-aware observation timestamp.
- API, artifact-integrity, data-contract, metrics, and training-pipeline tests.

## Architecture

```mermaid
flowchart LR
    Data["Versioned research data"] --> Train["Training-only feature fitting"]
    Train --> Bundle["Model + transforms + manifest + SHA-256"]
    Bundle --> Verify["Startup verification"]
    Client --> Contract["Strict loan request"]
    Contract --> Controls["Auth, rate limit, admission"]
    Controls --> Score["Transform and score"]
    Verify --> Score
    Score --> Response["Research risk response"]
    Score --> Metrics["Prometheus and privacy-minimized audit events"]
```

The supported service is [`api/inference_api.py`](api/inference_api.py). Training and bundle handling are implemented under [`src/`](src/).

## Quick start

Python 3.11 and 3.12 are the CI-supported versions.

```bash
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements/dev.txt
python -m pytest -q
```

The CI-only bundle command makes a deterministic local artifact for API experiments; it is not a validated lending model.

```bash
python -m scripts.build_smoke_bundle --output models/ci
MODEL_BUNDLE_PATH=models/ci LOAN_RISK_API_KEY=local-dev \
  uvicorn api.inference_api:app --reload
```

In Windows PowerShell:

```powershell
python -m scripts.build_smoke_bundle --output models/ci
$env:MODEL_BUNDLE_PATH = "models/ci"
$env:LOAN_RISK_API_KEY = "local-dev"
uvicorn api.inference_api:app --reload
```

## API contract

| Endpoint | Purpose |
|---|---|
| `GET /healthz` | Process liveness |
| `GET /readyz` | Verified model-bundle readiness |
| `GET /metrics` | Prometheus exposition format |
| `POST /predict` | Model-backed research prediction |
| `POST /feedback` | Record an observed research outcome |

`POST /predict` requires the validated raw loan fields defined by [`LoanRequest`](api/schemas.py). Unknown fields are rejected. When `LOAN_RISK_API_KEY` is configured, pass it via `X-API-Key`. A successful response is a research signal with a model and policy version; it is not an approval, denial, or adverse-action notice.

`POST /feedback` accepts an outcome and an ISO 8601 timestamp with a timezone, for example `2026-07-22T00:00:00Z`. The service rejects malformed or timezone-naive timestamps so outcome records have unambiguous temporal context.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_BUNDLE_PATH` | `models/current` | Directory containing `manifest.json` and the checksummed model bundle. |
| `LOAN_RISK_API_KEY` | unset | Enables API-key validation; mandatory when `ENVIRONMENT=production`. |
| `ENVIRONMENT` | `development` | In production, missing or invalid model bundles fail startup. |

The model bundle contains joblib-serialized objects. Treat its source path as administrator-controlled and do not load untrusted artifacts.

## Verification and reproducibility

The CI workflow runs a Python 3.11/3.12 matrix with syntax checks, Ruff, mypy, Bandit, coverage enforcement, dependency audit, and a model-backed container readiness smoke test. It uploads coverage artifacts for each Python version.

Run the critical serving checks locally:

```bash
python -m pytest -q tests/test_api.py tests/test_artifacts.py
python -m compileall -q api src evaluation tests scripts
ruff check api src evaluation tests scripts
```

Training and evaluation commands are intentionally separate from serving because model performance must be evaluated against a versioned, representative dataset. See [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md), [`docs/GOVERNANCE.md`](docs/GOVERNANCE.md), and [`metrics.md`](metrics.md) for research and governance context.

## Research benchmark protocol

### Offline candidate evidence

This repository deliberately publishes **no dataset-specific quality number**. A result is valid only when it is regenerated from a versioned, permitted dataset at the commit under review. The training command emits a self-describing `outputs/metrics.json` record so candidate and baseline evidence can be inspected without relying on README claims.

| Evidence | Repository implementation | Recorded output |
|---|---|---|
| Cohort split | Uses an out-of-time split when `issue_d` exists; otherwise uses a seeded stratified split. | `split_method`, `rows`, `train_rows`, `test_rows` |
| Candidate comparison | Compares the LightGBM candidate with a logistic-regression baseline on the same holdout. | `candidate_metrics`, `logistic_regression_baseline` |
| Discrimination and probability quality | Calculates ROC-AUC, PR-AUC, Brier score, log loss, expected calibration error, and a seeded 100-sample ROC-AUC bootstrap interval. | Metric values and `roc_auc_ci95_low`/`roc_auc_ci95_high` |
| Operating point | Calculates accuracy, precision, recall, F1, threshold, and confusion counts. | Metric values and `protocol.threshold` |
| Reproducibility context | Captures data fingerprint, commit, split seed, trial count, Python/package versions, and wall-clock training time. | `dataset_id`, `protocol`, `environment`, `training_seconds` and bundle manifest |

To reproduce an offline record, use an approved versioned dataset and retain both the Git commit and resulting JSON. The default seed, test fraction, and threshold below are explicit experiment settings—not quality claims.

```bash
git rev-parse HEAD
python -m src.train \
  --uri /path/to/versioned-loans.csv \
  --trials 20 \
  --seed 2025 \
  --test-size 0.2 \
  --threshold 0.5 \
  --output models/candidate \
  --metrics-output outputs/metrics.json \
  --model-version candidate-local
```

Never compare results from different dataset fingerprints, split methods, seeds, thresholds, or package versions as though they were the same experiment. Review calibration, cohort evidence, and fair-lending obligations separately before any real-world use.

### Online service telemetry

The API exposes operational counters and histograms at `GET /metrics`. These are observability signals, not model-performance metrics; do not use borrower attributes or group identities as labels.

| Prometheus metric | What it measures | Labels |
|---|---|---|
| `loan_risk_requests_total` | Completed requests by route and response code. | `route`, `status` |
| `loan_risk_request_duration_seconds` | Request-latency histogram for the observed route. | `route` |
| `loan_risk_in_flight` | Requests currently holding inference admission. | none |
| `loan_risk_predictions_total` | Completed predictions by model version and review recommendation. | `review`, `model_version` |
| `loan_risk_feedback_total` | Accepted feedback by outcome and model version. | `outcome`, `model_version` |

Use these signals to detect service degradation and version mix. Establish latency, availability, drift, calibration, and fairness thresholds only in a governed deployment with an approved monitoring plan.

## Security and data boundaries

- Input schemas reject unknown fields and enforce physical bounds for request fields.
- Model checksum verification occurs before deserialization.
- API responses use `Cache-Control: no-store`; audit events omit raw borrower feature values.
- Rate limiting and concurrency admission are local controls; use a managed gateway for distributed enforcement.
- Never commit customer data, secrets, private keys, or real model artifacts.

## Limitations and next work

- No model-quality, fairness, or calibration claim is valid without a documented, representative evaluation dataset and independent review.
- Reason codes are deterministic placeholders and are not approved adverse-action reasons.
- The in-process rate limiter is unsuitable as the sole production abuse-control mechanism.
- Production use requires model-risk, fair-lending, privacy, security, and legal sign-off, plus monitored rollout and rollback procedures.

See the open audit work in [issue #12](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/issues/12).

## License

MIT. See [LICENSE](LICENSE).
