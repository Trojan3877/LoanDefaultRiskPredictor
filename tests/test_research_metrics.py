import numpy as np

from evaluation.metrics import bootstrap_auc_interval, classification_metrics, group_metrics


def test_research_metrics_and_interval():
    truth = np.array([0, 0, 1, 1] * 20)
    scores = np.array([0.1, 0.3, 0.7, 0.9] * 20)
    metrics = classification_metrics(truth, scores, 0.5)
    assert metrics["roc_auc"] == 1.0
    assert metrics["brier_score"] < 0.1
    low, high = bootstrap_auc_interval(truth, scores, samples=20)
    assert low == high == 1.0


def test_group_metrics_enforces_minimum_cohort():
    import pandas as pd

    groups = pd.DataFrame({"cohort": ["A"] * 40 + ["B"] * 10})
    truth = np.array(([0, 1] * 25))
    scores = np.where(truth == 1, 0.8, 0.2)
    result = group_metrics(groups, "cohort", truth, scores, 0.5)
    assert set(result) == {"A"}
