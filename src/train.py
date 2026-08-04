"""Train, evaluate, and package a reproducible LightGBM credit-risk candidate."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import time
from datetime import UTC, datetime

import lightgbm as lgb
import numpy as np
import optuna
import pandas as pd
import sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from evaluation.metrics import bootstrap_auc_interval, classification_metrics
from src.artifacts import dataset_fingerprint, save_bundle
from src.data_loader import DataLoader
from src.feature_engineer import FeatureEngineer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True)
    parser.add_argument("--trials", type=int, default=20)
    parser.add_argument("--output", default="models/candidate")
    parser.add_argument("--metrics-output", default="outputs/metrics.json")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--model-version", default="candidate-local")
    return parser.parse_args()


def split_cohort(df: pd.DataFrame, test_size: float, seed: int):
    if not 0.1 <= test_size <= 0.5:
        raise ValueError("test_size must be between 0.1 and 0.5")
    if "issue_d" in df.columns:
        ordered = df.assign(issue_d=pd.to_datetime(df["issue_d"], errors="raise")).sort_values(
            "issue_d"
        )
        boundary = int(len(ordered) * (1 - test_size))
        return ordered.iloc[:boundary].copy(), ordered.iloc[boundary:].copy(), "out-of-time"
    train, test = train_test_split(
        df, test_size=test_size, stratify=df["defaulted"], random_state=seed
    )
    return train.copy(), test.copy(), "stratified-random-fallback"


def _model_score(model, frame: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        return np.asarray(model.predict_proba(frame)[:, 1], dtype=float)
    return np.asarray(model.predict(frame), dtype=float)


def train_candidate(
    df: pd.DataFrame, *, trials: int, seed: int, test_size: float, threshold: float
):
    train_frame, test_frame, split_method = split_cohort(df, test_size, seed)
    y_train = train_frame.pop("defaulted")
    y_test = test_frame.pop("defaulted")
    features = FeatureEngineer().fit(train_frame, y_train)
    X_train = features.transform(train_frame)
    X_test = features.transform(test_frame)

    def objective(trial: optuna.Trial) -> float:
        inner_train, inner_valid, y_inner_train, y_inner_valid = train_test_split(
            X_train, y_train, test_size=0.2, stratify=y_train, random_state=seed
        )
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbosity": -1,
            "seed": seed,
            "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.2, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 8, 64),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 10, 80),
        }
        model = lgb.train(
            params,
            lgb.Dataset(inner_train, y_inner_train),
            num_boost_round=500,
            valid_sets=[lgb.Dataset(inner_valid, y_inner_valid)],
            callbacks=[lgb.early_stopping(50, verbose=False), lgb.log_evaluation(0)],
        )
        trial.set_user_attr("best_iteration", model.best_iteration)
        return float(
            classification_metrics(y_inner_valid, model.predict(inner_valid), threshold)["roc_auc"]
        )

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=seed))
    study.optimize(objective, n_trials=max(1, trials))
    params = {
        **study.best_params,
        "objective": "binary",
        "metric": "auc",
        "verbosity": -1,
        "seed": seed,
    }
    rounds = int(study.best_trial.user_attrs.get("best_iteration", 100))
    model = lgb.train(params, lgb.Dataset(X_train, y_train), num_boost_round=rounds)
    probabilities = _model_score(model, X_test)
    metrics = classification_metrics(y_test, probabilities, threshold)
    low, high = bootstrap_auc_interval(y_test, probabilities, samples=100, seed=seed)
    metrics.update({"roc_auc_ci95_low": low, "roc_auc_ci95_high": high})

    baseline = LogisticRegression(max_iter=1000, random_state=seed).fit(X_train, y_train)
    baseline_metrics = classification_metrics(
        y_test, baseline.predict_proba(X_test)[:, 1], threshold
    )
    return (
        model,
        features,
        metrics,
        baseline_metrics,
        split_method,
        len(train_frame),
        len(test_frame),
    )


def main() -> None:
    args = _parse_args()
    started = time.perf_counter()
    source = pathlib.Path(args.uri)
    df = pd.concat(DataLoader.from_uri(args.uri).iter_chunks(50_000), ignore_index=True)
    model, features, metrics, baseline, split_method, train_rows, test_rows = train_candidate(
        df, trials=args.trials, seed=args.seed, test_size=args.test_size, threshold=args.threshold
    )
    dataset_id = dataset_fingerprint(source) if source.is_file() else f"external:{args.uri}"
    training_commit = os.getenv("GITHUB_SHA", "local-uncommitted")
    record = {
        "schema_version": 2,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_id": dataset_id,
        "training_commit": training_commit,
        "split_method": split_method,
        "rows": len(df),
        "train_rows": train_rows,
        "test_rows": test_rows,
        "protocol": {"seed": args.seed, "test_size": args.test_size, "trials": args.trials},
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "lightgbm": lgb.__version__,
        },
        "candidate_metrics": metrics,
        "logistic_regression_baseline": baseline,
        "training_seconds": round(time.perf_counter() - started, 3),
        "limitations": [
            "External validation not supplied",
            "Fair-lending approval not encoded by software",
        ],
    }
    save_bundle(
        args.output,
        {"model": model, "feature_engineer": features},
        model_version=args.model_version,
        threshold=args.threshold,
        dataset_id=dataset_id,
        training_commit=training_commit,
        metrics=metrics,
    )
    metrics_path = pathlib.Path(args.metrics_output)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
