# Metrics

## Offline research evaluation

The candidate evaluator can report:

- ROC-AUC with a seeded bootstrap interval;
- PR-AUC;
- Brier score;
- log loss;
- sample-weighted expected calibration error over fixed-width probability bins;
- accuracy, precision, recall, F1, threshold, and confusion counts;
- the same operating evidence for a logistic-regression baseline on the holdout.

Group metrics are an **offline governance utility** with a minimum cohort size of 30 and both target classes present. Governance/group attributes must be reviewed separately and must not enter the model merely because slice evaluation exists.

No dataset-specific number in this repository establishes real-world loan-default quality. A result must be tied to a permitted versioned dataset, source commit, protocol, threshold, environment, and retained output before it is treated as research evidence.

## Online engineering telemetry

The API exposes request count/latency, in-flight work, predictions by model version/review route, and feedback coverage. These are service observations, not model-quality metrics.

Privacy-sensitive feature values and governance-group identities must not be Prometheus labels.

## Claims intentionally not made

The repository does not claim a production SLO, real-world ROC-AUC/PR-AUC, calibration adequacy, fairness compliance, approval/decline quality, adverse-action validity, or regulatory readiness until representative dataset-backed and deployment-backed evidence exists.
