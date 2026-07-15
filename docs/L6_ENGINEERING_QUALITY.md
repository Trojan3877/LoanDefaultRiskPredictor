# L6 Engineering Quality Standard

This document defines L6 as evidence-backed engineering maturity for this repository. A control is complete only when it has implementation, automated verification, an owner, and an operational response.

## Quality gates

| Domain | Required evidence | Automated gate | Owner response |
|---|---|---|---|
| Correctness | typed contracts and deterministic transforms | mypy, compile, pytest | fix or revert |
| Research validity | holdout isolation and provenance record | feature/training tests | invalidate affected benchmark |
| Maintainability | bounded modules and dependency layers | Ruff and coverage >=45% | refactor before expansion |
| Security | minimal runtime, non-root, vulnerability policy | Bandit, pip-audit, Trivy | patch or document exception |
| Reliability | health/readiness and resource bounds | container smoke test, kubeconform | rollback unhealthy release |
| Supply chain | SBOM and signed immutable image | publish workflow | block unsigned deployment |
| Observability | request count and latency telemetry | API contract tests | investigate SLO breach |
| Governance | owners, limitations, disclosure path | CODEOWNERS and SECURITY.md | human approval |
| Delivery | repeatable build and rollback | CI, Compose, Kubernetes | rollout status and undo |

## Nine deployment tiers

1. **Reproducible source:** bounded dependencies, deterministic seed, versioned metrics schema.
2. **Data/model integrity:** validated schema, training-only learned transforms, identifiers excluded.
3. **Code quality:** static analysis, typing, security lint, branch coverage, contract tests.
4. **Artifact quality:** minimal non-root image, health check, runtime-only dependencies.
5. **Environment parity:** Compose enforces health, read-only filesystem, and restart behavior.
6. **Orchestration safety:** offline schema validation, probes, resource limits, rolling updates, restricted security context.
7. **Supply-chain trust:** dependency audit, Trivy gate, SPDX SBOM, GHCR, Cosign signature.
8. **Production telemetry:** liveness, readiness, Prometheus counts and latency.
9. **Operational governance:** ownership, private disclosure, release gates, limitations, rollback.

## Exception policy

A failing gate may be waived only through a time-bounded issue that identifies the risk, owner, compensating control, expiration date, and removal plan. Acceptance targets are not measured benchmark results. Production deployment additionally requires dataset governance, fairness/calibration review, secrets management, IAM, network policy, and environment-specific incident procedures.
