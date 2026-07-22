# Loan Default Risk Predictor

A model-backed credit-risk research pipeline with an evidence-backed L5 production-candidate baseline.

## Project status

- Temporal-preferred evaluation, logistic baseline, calibration/ranking metrics, and uncertainty
- Verified model-backed FastAPI service with model-aware readiness and Prometheus telemetry
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

Set `MODEL_BUNDLE_PATH` to a bundle produced by `python -m src.train`. Readiness remains false without a verified model.

Operational endpoints:

- `/healthz`
- `/readyz`
- `/metrics`
- `/docs`

See the repository [README](https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor#readme) for the experimental protocol, metrics policy, deployment commands, and known limitations.
