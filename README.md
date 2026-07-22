# Loan Default Risk Predictor

<p align="center"><strong>A governed, versioned LightGBM research pipeline with verified model-backed serving.</strong></p>

<p align="center">
  <a href="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml"><img src="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/ci.yml/badge.svg?branch=main" alt="L5 quality"></a>
  <a href="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/container-scan.yml"><img src="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/container-scan.yml/badge.svg?branch=main" alt="Container security"></a>
  <a href="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/docker-publish.yml"><img src="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/docker-publish.yml/badge.svg" alt="Signed release"></a>
  <a href="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/docs-deploy.yml"><img src="https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/actions/workflows/docs-deploy.yml/badge.svg?branch=main" alt="Documentation"></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/LightGBM-credit%20risk-2F855A" alt="LightGBM">
  <img src="https://img.shields.io/badge/FastAPI-model--backed-009688?logo=fastapi" alt="FastAPI">
  <img src="https://img.shields.io/badge/Coverage%20gate-75%25-16A34A" alt="Coverage gate">
  <img src="https://img.shields.io/badge/Artifact-SHA--256%20verified-6C5CE7" alt="Artifact integrity">
  <img src="https://img.shields.io/badge/Container-non--root-2496ED?logo=docker&logoColor=white" alt="Container">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow" alt="MIT"></a>
</p>

> **Important:** this is a production-candidate engineering demonstration, not an approved credit-decision system. It must not be used for lending decisions without representative-data validation, fair-lending and calibration review, privacy/legal approval, human oversight, and environment-specific security controls.

## What changed

The repository now has one supported path from a raw, validated loan request to a traceable model response. Training and serving share the fitted feature pipeline, threshold, schema version, metrics, lineage, and checksum manifest. Production startup fails when authentication or a verified model is unavailable.

## Engineering features

- Strict raw-feature contracts with bounds, enums, unknown-field rejection, and no borrower-name field.
- Training-only fitted encoders and deterministic seeds; identifiers never enter model features.
- Out-of-time splitting when `issue_d` is present, with an explicit random fallback for undated research data.
- LightGBM candidate compared with logistic regression on the untouched holdout.
- ROC-AUC, PR-AUC, Brier score, log loss, ECE, operating-point metrics, confusion counts, and bootstrap ROC-AUC interval.
- Offline group-slice metrics with minimum cohort size; protected fields remain outside model inputs.
- Immutable bundle manifest with model/preprocessor, threshold, model/policy/schema versions, dataset fingerprint, commit, metrics, and SHA-256.
- Model-aware readiness, API-key option, rate limiting, admission control, security headers, and privacy-minimized audit/feedback events.
- Prometheus request, latency, prediction, feedback, saturation, and model-version signals.
- Non-root/read-only container and Kubernetes probes, limits, seccomp, dropped capabilities, secret reference, and read-only model mount.
- Python 3.11/3.12 CI, 75% coverage floor, Ruff, mypy, Bandit, dependency audit, container smoke inference, and manifest validation.

## Architecture

```text
versioned cohort -> strict data contract -> chronological split
       |                                      |
       v                                      v
training-only transforms -> LightGBM + logistic baseline -> research report
       |
       v
weights + transforms + threshold + lineage + metrics + SHA-256 manifest
       |
       v
startup verification -> auth -> rate/admission -> transform -> score -> policy routing
                                                              |          |
                                                 Prometheus + audit + feedback
```

The API recommends review; it does not approve or decline credit. Deterministic reason codes are technical placeholders pending policy and adverse-action governance.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\Scripts\activate
python -m pip install -r requirements/dev.txt
pytest --cov --cov-fail-under=75
```

Train and package a candidate using a governed dataset:

```bash
python -m src.train \
  --uri data/loans.csv \
  --trials 20 \
  --seed 2025 \
  --test-size 0.20 \
  --threshold 0.50 \
  --model-version candidate-2026-07 \
  --output models/current \
  --metrics-output outputs/metrics.json
```

Serve the verified bundle:

```bash
export MODEL_BUNDLE_PATH=models/current
export LOAN_RISK_API_KEY="use-a-secret-manager-in-production"
uvicorn api.inference_api:app --host 0.0.0.0 --port 8000
```

`GET /healthz` is process liveness. `GET /readyz` returns 503 until a verified bundle is loaded. `POST /predict` accepts the versioned raw-loan schema and returns a probability, review routing, reason codes, request ID, model version, and policy version.

## Research metrics

No credit-model performance result is claimed because this repository does not contain a versioned, representative lending dataset or approved external cohort. The trainer produces the following evidence for a supplied dataset:

| Evidence | Candidate | Baseline | Promotion expectation |
|---|---:|---:|---|
| ROC-AUC + bootstrap 95% CI | Yes | Logistic ROC-AUC | Dataset-specific gate |
| PR-AUC and prevalence context | Yes | Yes | Must exceed reviewed baseline |
| Brier score and log loss | Yes | Yes | Calibrated-probability review |
| Expected calibration error | Yes | Yes | Segment review required |
| Precision, recall, F1, confusion counts | Yes | Yes | Threshold-cost review |
| Out-of-time cohort | When dated | Same cohort | Required for production study |
| External cohort | Not bundled | Not bundled | Required before lending use |
| Group/intersectional analysis | Utility provided | Same method | Approval-owned acceptance criteria |

The JSON report is canonical. Publish a redacted record only with dataset version/hash, cohort definition, exclusions, commit, hardware, uncertainty, limitations, and reviewer status.

## Reproducible engineering benchmark

Command:

```bash
python -m benchmarks.inference --iterations 300 --warmup 30
```

Observed on 2026-07-22:

| Scope | Mean | p50 | p95 | p99 | Sequential rate |
|---|---:|---:|---:|---:|---:|
| Batch-1 preprocessing + logistic smoke-model inference | 4.248 ms | 4.239 ms | 4.328 ms | 4.676 ms | 235.396/s |

Environment: Python 3.12.13, Windows 11 build 26200, AMD64 Family 25 Model 97. The deterministic synthetic bundle validates plumbing only. This excludes HTTP, network, concurrency, autoscaling, storage, and production LightGBM quality; it is not an availability or throughput SLO.

## L5 engineering decisions

| Decision | Why | Tradeoff / follow-up |
|---|---|---|
| One API and one artifact contract | Prevents training-serving skew and false-green CI | Requires migration from older demo entrypoints |
| Production fails closed | Avoids random, stale, or unverifiable scoring | Deployment must provide model and secret before readiness |
| Manifest + checksum before joblib load | Detects corruption and binds metadata | Joblib still requires an administrator-controlled trusted source |
| Model threshold is packaged | Keeps evaluation and serving policy aligned | Threshold changes require versioned policy approval |
| Temporal split preferred | Better approximates future-cohort behavior | External validation is still necessary |
| Deterministic reason codes | Auditable and testable | Must be validated for faithfulness and legally approved wording |
| Local limits plus gateway ownership | Protects a process without pretending it is distributed control | Production gateway must enforce global identity and quotas |
| Honest synthetic benchmark | Reproducible engineering evidence | Does not establish model accuracy or production capacity |

## Production-readiness checklist

- [x] Connected training, packaging, verification, and serving contract
- [x] Model-aware health/readiness and container smoke inference
- [x] Critical-path tests and 75% coverage gate
- [x] Research metrics, baseline, temporal option, and uncertainty
- [x] Artifact lineage, checksum, model/policy version, and rollback-compatible directory
- [x] Non-root container, Kubernetes controls, SBOM/signing workflows
- [ ] Representative versioned dataset and out-of-time benchmark report
- [ ] Independent external validation cohort
- [ ] Reviewed calibration, group/intersectional error analysis, and threshold-cost policy
- [ ] Approved adverse-action reasons and human-review workflow
- [ ] Cloud IAM, TLS ingress, network policy, managed secrets, encrypted storage, and audit retention
- [ ] Canary/shadow release, drift alerts, last-known-good rollback, and exercised incident runbooks
- [ ] Legal, privacy, fair-lending, security, and independent model-risk approval

## Extended recruiter Q&A

### What was the highest-leverage engineering change?

Replacing a validated but non-model score facade with one verified vertical slice. The deployed endpoint now proves it can load the same preprocessing/model contract produced by training, which makes readiness and CI meaningful.

### Why not describe this as “fully production-ready”?

Production readiness in lending depends on data representativeness, external validation, regulatory interpretation, operational ownership, and live infrastructure. Code can enforce evidence gates, but it cannot manufacture those approvals or outcomes.

### How is leakage controlled?

The outer holdout is separated before fitting encoders. Hyperparameter selection uses only an inner training split, and the final holdout is evaluated once. Dated cohorts use chronological separation; undated data is explicitly labeled as a weaker random fallback.

### Why retain logistic regression as a baseline?

A complex model should justify its operational and governance cost. The baseline exposes whether LightGBM provides meaningful ranking or calibration improvement and supplies an interpretable fallback comparison.

### How is training-serving skew prevented?

The fitted `FeatureEngineer`, estimator, threshold, schema version, and metadata are promoted together. Serving verifies the checksum and transforms a DataFrame through that exact fitted object.

### How would you evolve artifact security?

Store bundles in an authenticated registry, sign the manifest, verify provenance at deployment admission, restrict the runtime identity to read-only access, and revoke compromised versions. The checksum detects tampering; registry trust controls who may introduce an artifact.

### What happens when the model is missing or corrupt?

Development remains live but not ready. Production startup fails. This prevents Kubernetes from routing traffic and makes rollback to a complete last-known-good directory deterministic.

### Why are reason codes not generated by an LLM?

Credit explanations must be stable, faithful, reviewable, and mapped to approved policy language. Free-form generation introduces nondeterminism and unsupported causal claims. An LLM may assist offline drafting, never become the authoritative decision explanation without governance.

### What would you monitor after launch?

Service latency/errors/saturation; model and policy versions; input validity and unknown-category rates; score/review distributions; data freshness and drift; delayed calibration and performance; privacy-safe group metrics; feedback coverage; and rollback/canary health.

### What is the rollback unit?

The complete immutable bundle plus its compatible application image and policy version. Individual model files must never be mixed across versions.

### What remains the hardest problem?

Obtaining representative, legally usable data and proving stable, calibrated, equitable behavior across future and external cohorts. That is a cross-functional model-risk problem, not a library-selection problem.

## Supporting evidence

- [Model card](docs/MODEL_CARD.md)
- [Benchmark protocol](docs/BENCHMARKS.md)
- [Operations and rollback](docs/OPERATIONS.md)
- [Governance boundaries](docs/GOVERNANCE.md)
- [L5 quality standard](docs/L5_ENGINEERING_QUALITY.md)
- [Production-readiness audit](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor/issues/6)

## License

MIT. Dataset licenses, privacy duties, lending regulations, and model approvals are separate from the source-code license.
