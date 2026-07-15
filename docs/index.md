# Loan Default Risk Predictor

A research-oriented credit-risk classification pipeline with an evidence-backed L6 engineering baseline.

## Project status

- Leakage-controlled holdout evaluation and machine-readable metrics provenance
- Validated FastAPI facade with health, readiness, and Prometheus telemetry
- Minimal non-root runtime container
- Compose and Kubernetes deployment controls
- Static analysis, tests, dependency audit, container scan, SBOM, and signed releases
- Explicit ownership, security disclosure, limitations, and rollback guidance

!!! warning "Decision-use boundary"
    This project is an engineering demonstration. It is not approved for lending decisions without representative-data validation, calibration, fairness analysis, legal review, production monitoring, and human oversight.

## Start locally

```bash
python -m pip install -r requirements/dev.txt
uvicorn api.inference_api:app --host 127.0.0.1 --port 8000
```

Operational endpoints:

- `/healthz`
- `/readyz`
- `/metrics`
- `/docs`

See the repository [README](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor#readme) for the experimental protocol, metrics policy, deployment commands, and known limitations.
