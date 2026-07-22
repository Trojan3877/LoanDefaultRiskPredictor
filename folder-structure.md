# Repository Structure

```text
api/             one supported FastAPI application and request contracts
src/             data contract, feature pipeline, artifact contract, training
evaluation/      research, calibration, uncertainty, and slice metrics
benchmarks/      reproducible engineering benchmark
scripts/         CI-only smoke-bundle tooling
tests/           critical-path unit, contract, integration, and pipeline tests
docs/            L5 quality, model card, benchmarks, operations, governance
infra/k8s/       hardened Kubernetes baseline
infra/helm/      configurable Kubernetes release chart
.github/         CI, scanning, docs, and signed-image workflows
```

Local `models/`, `outputs/`, datasets, virtual environments, and test artifacts are ignored. Production model/data artifacts belong in governed registries, not Git.
