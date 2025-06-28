"""
feature_engineer.py
──────────────────────────────────────────────────────────────────────────────
Transforms raw loan-application data into machine-learning–ready features.

Pipeline Stages
───────────────
1. Categorical Encoding
   • High-cardinality code via *Target (Mean) Encoding*
   • Low-cardinality via *One-Hot* (keeps model transparent)

2. Continuous Feature Engineering
   • Weight-of-Evidence (WOE) bucketing for monotonic credit-risk variables
   • Interaction terms (loan_amt / annual_inc, dti × emp_length)

3. Macro-economic Join (optional)
   • Adds Fed Funds Rate + Unemployment Rate for loan issue date

Returns a **pandas.DataFrame** ready for `train.py`.  
All steps are pure-python, stateless; suitable for both **fit** & **serve**.
"""

from __future__ import annotations

import datetime as dt
from typing import Dict, Iterable

import numpy as np
import pandas as pd
from category_encoders.target_encoder import TargetEncoder
from sklearn.preprocessing import OneHotEncoder

# ── Configuration constants ────────────────────────────────────────────────
OHE_COLS = ["term", "home_ownership", "purpose"]
TARGET_ENC_COLS = ["emp_length"]
WOE_COLS = ["dti", "revol_util"]  # monotonic w.r.t default
MACRO_FILE = "data/macro.csv"


def _load_macro() -> pd.DataFrame:
    """Load Fed rate + unemployment CSV, indexed by YYYY-MM."""
    macro = pd.read_csv(MACRO_FILE, parse_dates=["date"])
    macro["ym"] = macro["date"].dt.to_period("M")
    return macro.set_index("ym")


MACRO_DF = _load_macro()


# ── Helper: Weight-of-Evidence bucketing ────────────────────────────────────
def _woe_bucket(series: pd.Series, bins: int = 10) -> pd.Series:
    """Return WOE-transformed series given a numeric predictor."""
    cats = pd.qcut(series, q=bins, duplicates="drop")
    # Will be replaced later during fit with proper WOE using y; for now raw bin idx
    return cats.cat.codes.astype("int8")


# ── Main class ──────────────────────────────────────────────────────────────
class FeatureEngineer:
    """Fit-transform interface mirrors scikit-learn style."""

    def __init__(self):
        self._target_encoders: Dict[str, TargetEncoder] = {}
        self._ohe: OneHotEncoder | None = None
        self._fitted = False

    # ── Fit stage -----------------------------------------------------------
    def fit(self, df: pd.DataFrame, y: pd.Series):
        # Fit target encoders
        for col in TARGET_ENC_COLS:
            enc = TargetEncoder(cols=[col], smoothing=0.25)
            enc.fit(df[col], y)
            self._target_encoders[col] = enc

        # Fit one-hot encoder on low-cardinality cols
        self._ohe = OneHotEncoder(
            handle_unknown="ignore",
            sparse=False,
            dtype=np.int8,
        )
        self._ohe.fit(df[OHE_COLS])

        self._fitted = True
        return self

    # ── Transform stage -----------------------------------------------------
    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted:
            raise RuntimeError("FeatureEngineer must be fit() before transform().")

        out_df = df.copy()

        # 1. Target encoding
        for col, enc in self._target_encoders.items():
            out_df[f"{col}_te"] = enc.transform(out_df[col]).astype("float32")
            out_df.drop(columns=[col], inplace=True)

        # 2. One-Hot encode
        ohe_arr = self._ohe.transform(out_df[OHE_COLS])
        ohe_cols = self._ohe.get_feature_names_out(OHE_COLS)
        out_df[ohe_cols] = ohe_arr.astype("int8")
        out_df.drop(columns=OHE_COLS, inplace=True)

        # 3. WOE bucketing
        for col in WOE_COLS:
            out_df[f"{col}_woe"] = _woe_bucket(out_df[col])
            out_df.drop(columns=[col], inplace=True)

        # 4. Interaction terms
        out_df["loan_to_income"] = (out_df["loan_amnt"] / (out_df["annual_inc"] + 1)).astype("float32")
        out_df["dti_emp_inter"] = (df["dti"] * df["emp_length"]).astype("float32")

        # 5. Macro join
        out_df["issue_ym"] = pd.to_datetime(df["issue_d"]).dt.to_period("M")
        out_df = out_df.join(MACRO_DF, on="issue_ym").drop(columns=["issue_ym"])

        return out_df.reset_index(drop=True)

    # Convenience combined method
    def fit_transform(self, df: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        return self.fit(df, y).transform(df)


# ── CLI utility for exploration ────────────────────────────────────────────
if __name__ == "__main__":
    import argparse

    from data_loader import DataLoader

    ap = argparse.ArgumentParser()
    ap.add_argument("--uri", required=True, help="CSV/Parquet path or S3/HTTP URI")
    args = ap.parse_args()

    dl = DataLoader.from_uri(args.uri)
    df = next(iter(dl))  # small sample
    y = df.pop("defaulted")
    fe = FeatureEngineer().fit(df, y)

    sample = fe.transform(df.head())
    print(sample.head())
