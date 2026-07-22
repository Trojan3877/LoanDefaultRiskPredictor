# Metrics

Offline evaluation reports ROC-AUC with bootstrap interval, PR-AUC, Brier score, log loss, expected calibration error, accuracy, precision, recall, F1, threshold, and confusion counts for the candidate and logistic baseline. Group metrics are an offline utility with minimum cohort size and must be governed separately from model features.

Online telemetry reports request count/latency, in-flight work, predictions by model version/review route, and feedback coverage. Privacy-sensitive feature values and group identities must not be Prometheus labels.

No production SLO or model-quality number is claimed until a representative environment and dataset-backed report exist.
