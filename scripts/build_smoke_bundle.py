"""Build a deterministic synthetic bundle for CI plumbing tests only."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from src.artifacts import save_bundle
from src.feature_engineer import FeatureEngineer


def synthetic_frame(rows: int = 160) -> pd.DataFrame:
    rng = np.random.default_rng(2025)
    dti = rng.uniform(1, 45, rows)
    utilization = rng.uniform(1, 120, rows)
    return pd.DataFrame(
        {
            "loan_id": np.arange(1, rows + 1),
            "loan_amnt": rng.uniform(1_000, 40_000, rows),
            "term": np.where(np.arange(rows) % 2, "36 months", "60 months"),
            "emp_length": rng.integers(0, 25, rows),
            "home_ownership": np.where(np.arange(rows) % 2, "RENT", "MORTGAGE"),
            "annual_inc": rng.uniform(25_000, 180_000, rows),
            "purpose": np.where(np.arange(rows) % 2, "debt_consolidation", "car"),
            "dti": dti,
            "delinq_2yrs": rng.integers(0, 3, rows),
            "open_acc": rng.integers(1, 30, rows),
            "pub_rec": rng.integers(0, 2, rows),
            "revol_util": utilization,
            "total_acc": rng.integers(2, 60, rows),
            "defaulted": ((dti + utilization / 4 + rng.normal(0, 8, rows)) > 45).astype(int),
        }
    )


def build(destination: Path) -> Path:
    frame = synthetic_frame()
    target = frame.pop("defaulted")
    engineer = FeatureEngineer().fit(frame, target)
    transformed = engineer.transform(frame)
    model = LogisticRegression(max_iter=1000, random_state=2025, solver="liblinear").fit(
        transformed, target
    )
    save_bundle(
        destination,
        {"model": model, "feature_engineer": engineer},
        model_version="test-smoke-v1",
        threshold=0.5,
        dataset_id="synthetic-ci-only",
        training_commit="ci",
        metrics={"purpose": "plumbing-only-not-model-evidence"},
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
