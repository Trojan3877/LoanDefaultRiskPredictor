# Architecture

## Research path

```text
Versioned dataset
  -> schema validation and cleaning
  -> stratified outer holdout
  -> training-only feature fitting
  -> inner model selection
  -> untouched holdout evaluation
  -> metrics.json + model bundle
```

The model trainer records ranking, classification, calibration, confusion-matrix, environment, parameter, and runtime metadata. Acceptance targets are kept separate from measured results.

## Service path

```text
Client
  -> FastAPI request validation
  -> explanation facade
  -> structured response
  -> request count and latency metrics
```

The current deployed API is an explanation facade. It does not load the trained model or calculate a risk score from raw borrower data.

## Deployment path

```text
GitHub Actions
  -> static analysis and tests
  -> runtime dependency audit
  -> minimal container build and smoke test
  -> Compose and Kubernetes validation
  -> vulnerability scan + SBOM
  -> signed GHCR release
  -> controlled Kubernetes rollout
```

Kubernetes uses health probes, resource bounds, rolling updates, a read-only root filesystem, non-root execution, dropped Linux capabilities, RuntimeDefault seccomp, and no mounted service-account token.
