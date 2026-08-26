# L6 Engineering Audit — v0.2.0

Audit target: `CoreyLeath-code/LoanDefaultRiskPredictor`

Baseline reviewed: `cbf5ee6f0524b98f1616ba4e0b75f192462cdccd`

## Executive assessment

The repository has a credible senior-engineering foundation because it separates engineering evidence from regulated model-quality claims. Its strongest areas are model-artifact integrity, fail-closed serving, explicit research boundaries, CI/security coverage, and container/Kubernetes validation. The v0.2.0 audit focuses on scientific precision, release integrity, and reproducible evidence rather than adding unsupported maturity claims.

## Scorecard

| Area | Assessment | Evidence / remaining gap |
|---|---|---|
| API contract and failure handling | Strong | Strict request validation, verified bundle readiness, auth requirement in production, bounded admission, sanitized scoring failures |
| Model artifact integrity | Strong | SHA-256 verified before joblib deserialization; path confinement; administrator-controlled source required |
| Test discipline | Strong | Baseline 20/20 tests and 81.79% branch coverage; v0.2.0 raises CI floor to 80% and adds contract tests |
| Evaluation methodology | Good / improving | Candidate vs logistic baseline, temporal-preferred split, bootstrap interval; v0.2.0 corrects ECE to sample-weighted form |
| Reproducibility | Good procedure, not byte-exact | Dataset fingerprinting/recorded environment; dependency specs use bounded ranges rather than hash locks |
| Observability | Good | Request/latency/in-flight/prediction/feedback metrics and privacy-minimized audit events |
| Security | Good | CodeQL, Gitleaks, Bandit, pip-audit, Trivy filesystem/image scanning, non-root container |
| Supply chain | Stronger in v0.2.0 | SPDX SBOM, semantic + immutable GHCR tags, keyless Cosign signing, release checksums |
| Container / Kubernetes | Good | Non-root UID, read-only smoke run, Compose validation, strict kubeconform validation |
| Distributed-systems maturity | Partial | Rate limiter and admission are process-local; external identity and shared control plane are deployment concerns |
| Performance evidence | Scoped and reproducible | Synthetic local microbenchmark only; no HTTP/network/concurrency/SLO claim |
| Model-quality evidence | Not release-qualified for lending | No representative approved dataset bundled; no real-world quality claim |
| Fair-lending / regulatory approval | Not established | Explicitly requires independent model-risk, fair-lending, privacy, legal, and policy review |

## Findings and treatments

### 1. Calibration metric naming was scientifically imprecise

**Finding:** The previous `expected_calibration_error` used an unweighted mean of calibration-bin gaps. That is useful as a calibration-gap summary but is not the canonical sample-weighted ECE commonly expected by reviewers.

**Treatment:** v0.2.0 implements sample-weighted ECE over fixed-width probability bins and validates that probability inputs are finite and lie in `[0, 1]`.

### 2. Serving silently clamped invalid model outputs

**Finding:** The API previously clamped a score below 0 or above 1 into the probability interval. That can hide a broken model/scoring contract.

**Treatment:** v0.2.0 rejects non-finite and out-of-range scores and returns a sanitized service-unavailable response.

### 3. Training evidence did not record every advertised protocol field

**Finding:** README stated that `protocol.threshold` was recorded, but the JSON protocol object omitted the threshold even though it appeared in model metrics/manifest.

**Treatment:** v0.2.0 records `threshold` and `training_commit` explicitly in `outputs/metrics.json` and uses the same commit value in the model manifest.

### 4. CI evidence was stronger than the enforced coverage floor

**Finding:** Baseline branch coverage was 81.79%, while CI enforced only 75%.

**Treatment:** v0.2.0 raises the floor to 80%. The audit deliberately does not claim 90%+ because the measured code does not support that claim.

### 5. Benchmark output was human-readable but weak as an evidence artifact

**Finding:** The local microbenchmark omitted a commit, model checksum, input hash, memory observation, and machine-readable output path.

**Treatment:** v0.2.0 emits JSON with commit, environment, model checksum/version, input hash, workload, latency distribution, sequential throughput, traced Python memory, success count/rate, and explicit limitations. CI uploads the JSON artifact.

### 6. Release engineering did not create an auditable GitHub Release

**Finding:** The existing tag workflow only built/pushed a GHCR image and signed it. The current repository had no GitHub Release object.

**Treatment:** v0.2.0 adds an evidence-backed publisher that scans the release image, generates an SPDX SBOM, publishes semantic and immutable image tags, signs the digest with Cosign, generates checksums/evidence, and creates a GitHub Release. It refuses to mutate an existing tag.

### 7. Version claims conflicted

**Finding:** Package metadata reported `0.2.0` while FastAPI reported `1.0.0`.

**Treatment:** v0.2.0 aligns the service version with package/release version `0.2.0`.

## Merge gate

The audit PR must not merge until the relevant pull-request checks complete successfully. At minimum:

- Python 3.11 and 3.12 test jobs;
- Ruff, mypy, Bandit and runtime dependency audit;
- coverage >= 80%;
- deployment/container smoke validation;
- Security workflow and CodeQL;
- container Trivy HIGH/CRITICAL gate if the Docker/runtime paths change.

Any failing test or security gate is a release blocker; the correct response is to fix the implementation or evidence, not weaken the gate.

## Release gate

The release is acceptable only when:

1. the audit PR is merged from a green head commit;
2. main CI/security complete successfully on the released source;
3. the release image passes the HIGH/CRITICAL Trivy gate;
4. semantic and immutable GHCR tags resolve to the released source;
5. a digest is signed with keyless Cosign;
6. SBOM, release evidence, and checksums are attached to the GitHub Release;
7. no README text converts synthetic benchmark observations into production or model-quality claims.

## Remaining P0 risk

The dominant remaining risk is not software plumbing; it is **model qualification**. No real-world lending quality, fairness, calibration suitability, adverse-action explainability, or regulatory approval should be asserted until a representative permitted dataset and independent governance process produce versioned evidence.
