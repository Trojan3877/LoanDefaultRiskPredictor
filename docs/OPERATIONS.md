# Operations and Rollback

## Release gate

Require green CI/security/container checks; verified model and image signatures; dataset-specific model card; calibration/fairness/threshold review; named operator; rollback target; and environment approvals.

## Signals

Alert on readiness failure, elevated errors/latency, saturation, abrupt score/review distribution changes, missing feedback, stale model/data, schema rejection spikes, and approved drift/calibration indicators. Never place borrower values or group identity in metric labels.

## Incident response

1. Stop rollout and identify image/model/policy versions.
2. Route to manual-review-only mode or disable scoring through the environment kill switch.
3. Revoke the suspect bundle and restore the last-known-good complete bundle/image pair.
4. Verify readiness, smoke prediction, telemetry, and audit continuity.
5. Preserve privacy-safe evidence, notify owners, document scope and corrective action.

Kubernetes rollback: `kubectl rollout undo deployment/loan-risk-api`. Exercise restoration periodically; a command in documentation is not proof of recoverability.
