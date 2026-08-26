# Production Readiness Audit — v0.3.0

Audit date: 2026-08-26
Scope: application code, test and delivery controls, package artifacts, and release automation.

## Executive decision

The repository is ready to merge as a **research-service engineering release**. The pull request must remain blocked on its required GitHub checks. A production lending decision system is not approved by this audit: it lacks a permitted representative dataset, model-risk/fair-lending evidence, and deployment-specific governance.

## Findings and disposition

| Priority | Finding | Disposition |
|---|---|---|
| P0 | The release workflow was fixed to `v0.2.0`, could run on arbitrary `main` pushes, and never built a Python package. | Fixed. Only an existing `vMAJOR.MINOR.PATCH` tag matching `src.version.__version__` can release; the workflow rebuilds quality gates, creates sdist/wheel artifacts, validates them with Twine, and attaches them to the GitHub Release. |
| P1 | Package metadata, release version, and the FastAPI OpenAPI version could drift. | Fixed. `src/version.py` is the dynamic setuptools version source and the API imports it. |
| P1 | Release artifact provenance and integrity were incomplete for Python packages. | Fixed. GitHub build provenance attestation, per-package SHA-256 checksums, SBOM, container evidence, and aggregate checksums are generated and attached. |
| P1 | A caller could configure a non-functional rate limiter (`limit <= 0` or non-positive window). | Fixed with input validation and tests. |
| P2 | Calibration accepted targets outside the binary label contract. | Fixed with explicit validation and tests. |
| P2 | Local test execution could fail in locked-down Windows profiles because pytest used the profile temp directory. | Documented deterministic `--basetemp .testtmp` execution; `.testtmp` is ignored. This is an environment constraint, not a product defect. |

## Validation evidence

Run in a clean Python 3.12.13 virtual environment on Windows on 2026-08-26:

| Gate | Result |
|---|---:|
| Ruff | passed |
| mypy (`api`) | passed |
| Bandit (`api`, `src`, `evaluation`) | passed |
| pytest | 26 passed, 0 failed, 0 warnings |
| Branch coverage | 82.31% (required: 80%) |
| Distribution build | sdist and universal wheel built successfully |
| Twine metadata check | passed for both artifacts |
| Release workflow YAML parse | passed |
| Runtime dependency audit | no known vulnerabilities |

## Release procedure and reproducibility

1. Merge the green PR and wait for the `main` checks to pass.
2. Confirm the version in `src/version.py` and create a signed immutable tag of the same value: `v0.3.0`.
3. Push the tag. The release workflow validates the tag/source pairing, repeats code-quality and dependency checks, builds distributions, scans/signs the container, and creates the GitHub Release.
4. Verify the release’s attached wheel/sdist checksums and GitHub attestation. Verify the GHCR image with Cosign before deployment.

The pipeline publishes the container to GHCR automatically. PyPI publication is intentionally gated by repository variable `PUBLISH_PYPI=true` and the protected `pypi` environment configured for PyPI trusted publishing. This avoids embedding a long-lived package credential in source or Actions secrets.

## Residual release blockers outside this PR

- Repository administrators must configure branch protection with the CI, security, CodeQL, dependency-review, and container scan checks required before merge.
- PyPI trusted publisher configuration is an external PyPI/repository administration action; this code cannot create it safely.
- A maintainer needs permission to create and push the annotated release tag. Commit/tag signing is recommended by organizational policy.
- Any production deployment remains subject to data, privacy, legal, security, model-risk, and fair-lending approvals.
