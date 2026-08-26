# Architecture

## Research path

```text
Governed dataset -> strict contract -> out-of-time split when dated
  -> training-only feature fit -> LightGBM + logistic baseline
  -> untouched holdout metrics + uncertainty -> immutable bundle/report
```

## Service path

```text
Client -> schema -> identity/rate/admission -> packaged transform/model/threshold
  -> review recommendation + reason codes + model/policy version
  -> bounded-cardinality telemetry + privacy-minimized audit/feedback
```

Startup verifies the manifest and checksum before deserialization. Production requires an API key and fails startup when the bundle is missing, corrupt, or incompatible. Liveness describes the process; readiness describes the verified model dependency.

## Deployment path

CI enforces Python 3.11/3.12 tests, 80% coverage, static/security/dependency gates, trained-bundle container smoke inference, and Compose/Kubernetes validation. Immutable semantic tags invoke the release pipeline, which rebuilds the quality gates, produces attested Python source/wheel distributions, scans and signs the GHCR image, and attaches the SBOM and checksums to a GitHub Release. Runtime identity is non-root with read-only filesystems, resource limits, probes, and no service-account token.
