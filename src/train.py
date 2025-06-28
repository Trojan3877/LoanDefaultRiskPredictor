"""
train.py
──────────────────────────────────────────────────────────────────────────────
End-to-end training script that

1) Loads & cleans data via DataLoader
2) Generates features with FeatureEngineer
3) Hyper-parameter-tunes a LightGBM model (Optuna)
4) Logs metrics & artifacts to MLflow and Snowflake
5) Serialises the final model to `models/latest.joblib`

Run:

    python src/train.py --uri data/loans.csv --trials 50

"""


from __future__ import annotations

import argparse
import os
import pathlib
import joblib
import mlflow
import optuna
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, f1_score
from sklearn.model_selection import train_test_split

from data_loader import DataLoader
from feature_engineer import FeatureEngineer

# ---------------------------------------------------------------------------#
# 1 ─ Argument parsing                                                       #
# ---------------------------------------------------------------------------#
ap = argparse.ArgumentParser()
ap.add_argument("--uri", required=True, help="CSV/Parquet path, S3 or HTTP URI")
ap.add_argument("--trials", type=int, default=40, help="Optuna trials")
ap.add_argument("--output", default="models/latest.joblib", help="Model out-path")
args = ap.parse_args()

# ---------------------------------------------------------------------------#
# 2 ─ Data loading & feature engineering                                     #
# ---------------------------------------------------------------------------#
loader = DataLoader.from_uri(args.uri)
df_full = pd.concat(loader.iter_chunks(50_000), ignore_index=True)
y_full = df_full.pop("defaulted")

fe = FeatureEngineer().fit(df_full, y_full)
X_full = fe.transform(df_full)

X_train, X_val, y_train, y_val = train_test_split(
    X_full, y_full, test_size=0.2, stratify=y_full, random_state=2025
)

# ---------------------------------------------------------------------------#
# 3 ─ Optuna objective                                                       #
# ---------------------------------------------------------------------------#
def objective(trial: optuna.Trial):
    params = {
        "objective": "binary",
        "boosting_type": "gbdt",
        "metric": "auc",
        "verbosity": -1,
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 16, 256, log=True),
        "feature_fraction": trial.suggest_float("feature_fraction", 0.6, 1.0),
        "bagging_fraction": trial.suggest_float("bagging_fraction", 0.6, 1.0),
        "bagging_freq": trial.suggest_int("bagging_freq", 1, 10),
        "min_data_in_leaf": trial.suggest_int("min_data_in_leaf", 20, 100),
    }

    lgb_train = lgb.Dataset(X_train, y_train)
    lgb_val = lgb.Dataset(X_val, y_val, reference=lgb_train)

    model = lgb.train(
        params,
        lgb_train,
        num_boost_round=2000,
        valid_sets=[lgb_val],
        early_stopping_rounds=100,
        verbose_eval=False,
    )

    preds = model.predict(X_val, num_iteration=model.best_iteration)
    auc = roc_auc_score(y_val, preds)
    return auc


study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=args.trials, show_progress_bar=True)
best_params = study.best_trial.params

# ---------------------------------------------------------------------------#
# 4 ─ Train final model                                                      #
# ---------------------------------------------------------------------------#
best_params.update({"objective": "binary", "metric": "auc", "verbosity": -1})
final_train = lgb.Dataset(X_full, y_full)
model = lgb.train(best_params, final_train, num_boost_round=study.best_trial.user_attrs.get("n_boost_round", 500))

preds_full = model.predict(X_full)
auc_full = roc_auc_score(y_full, preds_full)
f1_full = f1_score(y_full, preds_full > 0.5)

print(f"✅ Final AUC  {auc_full:.3f}  •  F1  {f1_full:.3f}")

# ---------------------------------------------------------------------------#
# 5 ─ Log to MLflow & Snowflake                                              #
# ---------------------------------------------------------------------------#
mlflow.set_experiment("LoanDefaultRisk")
with mlflow.start_run():
    mlflow.log_params(best_params)
    mlflow.log_metric("auc", auc_full)
    mlflow.log_metric("f1", f1_full)
    mlflow.lightgbm.log_model(model, "model")
    mlflow.log_artifact(args.output)

# Snowflake (placeholder)
try:
    import snowflake.connector

    conn = snowflake.connector.connect(
        account=os.getenv("SNOWFLAKE_ACCOUNT"),
        user=os.getenv("SNOWFLAKE_USER"),
        password=os.getenv("SNOWFLAKE_PASSWORD"),
        database="ML_METRICS",
        schema="PUBLIC",
    )
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO LOAN_MODEL_METRICS(VERSION, AUC, F1) VALUES (%s, %s, %s)",
        ("v0.1.0", auc_full, f1_full),
    )
    cur.close()
    conn.close()
except Exception as e:
    print("Snowflake logging skipped:", e)

# ---------------------------------------------------------------------------#
# 6 ─ Persist artefacts                                                      #
# ---------------------------------------------------------------------------#
pathlib.Path(args.output).parent.mkdir(parents=True, exist_ok=True)
joblib.dump({"model": model, "feature_engineer": fe}, args.output)
print(f"Model saved → {args.output}")
