# Design

## Purpose and boundary

Loan Default Risk Predictor is a research-oriented LightGBM pipeline and FastAPI service for evaluating loan-risk signals. Its output is a review recommendation, not an approval, decline, pricing, limit, collection, eligibility, or adverse-action decision. The repository does not bundle representative lending data or establish real-world quality, fairness, calibration, or legal suitability.

## Research path

The training path accepts a governed dataset through a strict contract, excludes identifiers and offline governance attributes from predictive features, and fits transformations only on training data. When an issue date is available, the trainer uses an out-of-time split; otherwise it uses a seeded stratified split. It compares a LightGBM candidate with a logistic-regression baseline on the same untouched holdout and records the dataset identifier, split method, seed, environment, metrics, and training time in the output record.

## Model bundle

Training packages the model, fitted transformations, threshold, policy version, training metadata, and a SHA-256 manifest as a bundle. The serving process verifies the manifest and checksum before deserializing the bundle. Production configuration fails closed when a required bundle is missing, corrupt, or incompatible.

## Serving path

The FastAPI entry point is `api/inference_api.py`. It validates the request schema before scoring, then applies authentication when configured, local rate limiting, and bounded-concurrency admission. Responses include the research signal together with model and policy versions; Prometheus metrics and privacy-minimized audit/feedback events support operational observation.

## Operational limits

The in-process admission and rate-limit controls protect a single process and are not distributed enforcement. A deployed system needs a managed gateway, governed data/model access, environment-specific security controls, monitoring, rollback procedures, and approval by model-risk, fair-lending, privacy, security, legal/compliance, product-policy, and operational owners.

## Evidence in this repository

- `src/train.py` provides the training and metric-record generation path.
- `scripts/build_smoke_bundle.py` creates a deterministic local bundle for service testing; it is not a validated lending model.
- `docs/architecture.md`, `docs/MODEL_CARD.md`, and `docs/GOVERNANCE.md` describe the architecture, model boundary, and governance context.
