import numpy as np
import pytest

from evaluation.metrics import (
    bootstrap_auc_interval,
    classification_metrics,
    expected_calibration_error,
    group_metrics,
)


def test_research_metrics_and_interval():
    truth = np.array([0, 0, 1, 1] * 20)
    scores = np.array([0.1, 0.3, 0.7, 0.9] * 20)
    metrics = classification_metrics(truth, scores, 0.5)
    assert metrics["roc_auc"] == 1.0
    assert metrics["brier_score"] < 0.1
    assert 0.0 <= metrics["expected_calibration_error"] <= 1.0
    low, high = bootstrap_auc_interval(truth, scores, samples=20)
    assert low == high == 1.0


def test_expected_calibration_error_is_sample_weighted_and_validated():
    truth = np.array([0, 0, 1, 1])
    scores = np.array([0.1, 0.2, 0.8, 0.9])
    assert expected_calibration_error(truth, scores) == pytest.approx(0.15)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        expected_calibration_error(truth, np.array([0.1, 0.2, 0.8, 1.2]))
    with pytest.raises(ValueError, match="binary"):
        expected_calibration_error(np.array([0, 2]), np.array([0.2, 0.8]))


def test_group_metrics_enforces_minimum_cohort():
    import pandas as pd

    groups = pd.DataFrame({"cohort": ["A"] * 40 + ["B"] * 10})
    truth = np.array([0, 1] * 25)
    scores = np.where(truth == 1, 0.8, 0.2)
    result = group_metrics(groups, "cohort", truth, scores, 0.5)
    assert set(result) == {"A"}
