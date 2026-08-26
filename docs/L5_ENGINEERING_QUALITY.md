# L5 Engineering Quality Standard

L5 means the repository demonstrates system ownership through explicit contracts, measurable gates, failure behavior, operational evidence, and honest boundaries. It is not a job-title claim or regulatory certification.

| Domain | Automated evidence | Owner response |
|---|---|---|
| Correctness | strict schemas, model-backed E2E tests, >=80% branch-aware coverage | fix or revert |
| Research validity | temporal-preferred split, baseline, calibration/ranking metrics, uncertainty | invalidate unsupported report |
| Artifact integrity | schema validation and SHA-256 before deserialization | reject/revoke bundle |
| Security | Ruff, mypy, Bandit, pip-audit, non-root/read-only runtime | patch or time-bound exception |
| Reliability | fail-closed startup, readiness, limits, smoke inference, probes | rollback to last-known-good |
| Supply chain | dependency audit, Trivy, SBOM, signed image | block unsigned release |
| Observability | bounded-cardinality service/model/feedback telemetry | investigate SLO or drift alert |
| Governance | model/policy versions, limitations, approval checklist | require human sign-off |

Exceptions require a GitHub issue with owner, risk, compensating control, expiration, and removal plan. New critical code requires focused tests even when aggregate coverage passes.
