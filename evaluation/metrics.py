"""Research metrics with calibration, cost, and uncertainty support."""

from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(y_true, probabilities, threshold: float = 0.5) -> dict[str, float | int]:
    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    labels = scores >= threshold
    tn, fp, fn, tp = confusion_matrix(truth, labels, labels=[0, 1]).ravel()
    observed, predicted = calibration_curve(truth, scores, n_bins=min(10, len(truth)), strategy="quantile")
    ece = float(np.mean(np.abs(observed - predicted))) if len(observed) else 0.0
    return {
        "roc_auc": float(roc_auc_score(truth, scores)),
        "pr_auc": float(average_precision_score(truth, scores)),
        "brier_score": float(brier_score_loss(truth, scores)),
        "log_loss": float(log_loss(truth, np.column_stack([1 - scores, scores]), labels=[0, 1])),
        "expected_calibration_error": ece,
        "accuracy": float(accuracy_score(truth, labels)),
        "precision": float(precision_score(truth, labels, zero_division=0)),
        "recall": float(recall_score(truth, labels, zero_division=0)),
        "f1": float(f1_score(truth, labels, zero_division=0)),
        "threshold": float(threshold),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def bootstrap_auc_interval(y_true, probabilities, *, samples: int = 200, seed: int = 2025) -> tuple[float, float]:
    truth = np.asarray(y_true, dtype=int)
    scores = np.asarray(probabilities, dtype=float)
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(samples):
        indices = rng.integers(0, len(truth), len(truth))
        if len(np.unique(truth[indices])) == 2:
            values.append(float(roc_auc_score(truth[indices], scores[indices])))
    if not values:
        raise ValueError("Bootstrap samples require both target classes")
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def group_metrics(frame, group_column: str, y_true, probabilities, threshold: float) -> dict[str, dict[str, float | int]]:
    """Offline-only slice metrics; protected fields must never enter model features."""

    result: dict[str, dict[str, float | int]] = {}
    for value in sorted(frame[group_column].dropna().astype(str).unique()):
        mask = frame[group_column].astype(str) == value
        if int(mask.sum()) >= 30 and len(np.unique(np.asarray(y_true)[mask])) == 2:
            result[value] = classification_metrics(np.asarray(y_true)[mask], np.asarray(probabilities)[mask], threshold)
    return result
