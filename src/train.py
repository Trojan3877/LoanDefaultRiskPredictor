"""Train a LightGBM credit-risk model and write reproducible holdout metrics."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import platform
import time
from datetime import datetime, timezone

import joblib
import lightgbm as lgb
import mlflow
import optuna
import pandas as pd
import sklearn
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

try:
    from src.data_loader import DataLoader
    from src.feature_engineer import FeatureEngineer
except ModuleNotFoundError:
    from data_loader import DataLoader
    from feature_engineer import FeatureEngineer


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", required=True, help="CSV/Parquet path, S3 or HTTP URI")
    parser.add_argument("--trials", type=int, default=40)
    parser.add_argument("--output", default="models/latest.joblib")
    parser.add_argument("--metrics-output", default="outputs/metrics.json")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=2025)
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args()


def _metrics(y_true, probabilities, threshold: float) -> dict:
    labels = probabilities >= threshold
    tn, fp, fn, tp = confusion_matrix(y_true, labels, labels=[0, 1]).ravel()
    return {
        "roc_auc": float(roc_auc_score(y_true, probabilities)),
        "pr_auc": float(average_precision_score(y_true, probabilities)),
        "accuracy": float(accuracy_score(y_true, labels)),
        "precision": float(precision_score(y_true, labels, zero_division=0)),
        "recall": float(recall_score(y_true, labels, zero_division=0)),
        "f1": float(f1_score(y_true, labels, zero_division=0)),
        "brier_score": float(brier_score_loss(y_true, probabilities)),
        "threshold": threshold,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def main() -> None:
    args = _parse_args()
    started = time.perf_counter()

    df = pd.concat(DataLoader.from_uri(args.uri).iter_chunks(50_000), ignore_index=True)
    y = df.pop("defaulted")
    X_train_raw, X_test_raw, y_train, y_test = train_test_split(
        df,
        y,
        test_size=args.test_size,
        stratify=y,
        random_state=args.seed,
    )

    # Fit every target-aware transform on training data only.
    features = FeatureEngineer().fit(X_train_raw, y_train)
    X_train = features.transform(X_train_raw)
    X_test = features.transform(X_test_raw)

    def objective(trial: optuna.Trial) -> float:
        params = {
            "objective": "binary",
            "metric": "auc",
            "verbosity": -1,
            "seed": args.seed,
            "feature_fraction_seed": args.seed,
            "bagging_seed": args.seed,
            "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
            "num_leaves": trial.suggest_int("num_leaves", 16, 256, log=True),
            "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
            "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
            "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),
            "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 20, 100),
        }
        inner_train, inner_valid, inner_y_train, inner_y_valid = train_test_split(
            X_train, y_train, test_size=0.2, stratify=y_train, random_state=args.seed
        )
        model = lgb.train(
            params,
            lgb.Dataset(inner_train, inner_y_train),
            num_boost_round=2000,
            valid_sets=[lgb.Dataset(inner_valid, inner_y_valid)],
            callbacks=[lgb.early_stopping(100, verbose=False), lgb.log_evaluation(0)],
        )
        trial.set_user_attr("best_iteration", model.best_iteration)
        return roc_auc_score(inner_y_valid, model.predict(inner_valid, num_iteration=model.best_iteration))

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=args.seed))
    study.optimize(objective, n_trials=args.trials)

    params = {
        **study.best_trial.params,
        "objective": "binary",
        "metric": "auc",
        "verbosity": -1,
        "seed": args.seed,
    }
    rounds = int(study.best_trial.user_attrs.get("best_iteration", 500))
    model = lgb.train(params, lgb.Dataset(X_train, y_train), num_boost_round=rounds)
    probabilities = model.predict(X_test)
    results = _metrics(y_test, probabilities, args.threshold)
    record = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "evaluation": "single stratified holdout; untouched during tuning",
        "dataset": {"uri": args.uri, "rows": len(df), "train_rows": len(X_train), "test_rows": len(X_test)},
        "protocol": {"seed": args.seed, "test_size": args.test_size, "trials": args.trials},
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "scikit_learn": sklearn.__version__,
            "lightgbm": lgb.__version__,
        },
        "metrics": results,
        "best_params": study.best_trial.params,
        "best_iteration": rounds,
        "training_seconds": round(time.perf_counter() - started, 3),
    }

    output = pathlib.Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_engineer": features, "threshold": args.threshold}, output)

    metrics_output = pathlib.Path(args.metrics_output)
    metrics_output.parent.mkdir(parents=True, exist_ok=True)
    metrics_output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")

    mlflow.set_experiment("LoanDefaultRisk")
    with mlflow.start_run():
        mlflow.log_params(study.best_trial.params)
        mlflow.log_metrics({key: value for key, value in results.items() if isinstance(value, float)})
        mlflow.log_artifact(str(metrics_output))
        mlflow.lightgbm.log_model(model, "model")

    print(json.dumps(record, indent=2))
    print(f"Model saved to {output}; metrics saved to {metrics_output}")


if __name__ == "__main__":
    main()
