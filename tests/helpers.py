from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.artifacts import save_bundle
from src.feature_engineer import FeatureEngineer


def loan_frame(rows: int = 80) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    return pd.DataFrame(
        {
            "loan_id": np.arange(1, rows + 1),
            "loan_amnt": rng.uniform(1_000, 40_000, rows).astype("float32"),
            "term": np.where(np.arange(rows) % 2, "36 months", "60 months"),
            "emp_length": rng.integers(0, 25, rows).astype("float32"),
            "home_ownership": np.where(np.arange(rows) % 2, "RENT", "MORTGAGE"),
            "annual_inc": rng.uniform(25_000, 180_000, rows).astype("float32"),
            "purpose": np.where(np.arange(rows) % 2, "debt_consolidation", "car"),
            "dti": rng.uniform(1, 45, rows).astype("float32"),
            "delinq_2yrs": rng.integers(0, 3, rows).astype("int8"),
            "open_acc": rng.integers(1, 30, rows).astype("int8"),
            "pub_rec": rng.integers(0, 2, rows).astype("int8"),
            "revol_util": rng.uniform(1, 120, rows).astype("float32"),
            "total_acc": rng.integers(2, 60, rows).astype("int8"),
            "defaulted": (np.arange(rows) % 4 == 0).astype("int8"),
        }
    )


def create_test_bundle(destination: Path) -> Path:
    frame = loan_frame()
    target = frame.pop("defaulted")
    engineer = FeatureEngineer().fit(frame, target)
    transformed = engineer.transform(frame)
    model = LogisticRegression(max_iter=500, random_state=7, solver="liblinear").fit(
        transformed, target
    )
    save_bundle(
        destination,
        {"model": model, "feature_engineer": engineer},
        model_version="test-v1",
        threshold=0.4,
        dataset_id="synthetic-test-only",
        training_commit="test",
        metrics={"roc_auc": 0.5},
    )
    return destination


def valid_request() -> dict:
    return {
        "loan_id": 999,
        "loan_amnt": 12000,
        "term": "36 months",
        "emp_length": 5,
        "home_ownership": "RENT",
        "annual_inc": 65000,
        "purpose": "debt_consolidation",
        "dti": 22,
        "delinq_2yrs": 0,
        "open_acc": 8,
        "pub_rec": 0,
        "revol_util": 48,
        "total_acc": 18,
    }
