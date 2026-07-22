import pandas as pd

from src.train import split_cohort, train_candidate
from tests.helpers import loan_frame


def test_temporal_split_and_candidate_evaluation():
    frame = loan_frame(100)
    frame["issue_d"] = pd.date_range("2020-01-01", periods=len(frame), freq="D")
    train, test, method = split_cohort(frame, 0.2, 7)
    assert method == "out-of-time"
    assert train["issue_d"].max() < test["issue_d"].min()
    model, engineer, metrics, baseline, split_method, train_rows, test_rows = train_candidate(
        frame, trials=1, seed=7, test_size=0.2, threshold=0.5
    )
    assert model is not None and engineer is not None
    assert split_method == "out-of-time"
    assert train_rows == 80 and test_rows == 20
    assert 0 <= metrics["roc_auc"] <= 1
    assert 0 <= baseline["roc_auc"] <= 1


def test_random_fallback_is_explicit():
    train, test, method = split_cohort(loan_frame(), 0.25, 7)
    assert method == "stratified-random-fallback"
    assert len(train) == 60 and len(test) == 20
