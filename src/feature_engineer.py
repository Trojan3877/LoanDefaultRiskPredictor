"""Leakage-safe feature engineering fitted once and reused for inference."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from category_encoders.target_encoder import TargetEncoder
from sklearn.preprocessing import OneHotEncoder

OHE_COLS = ["term", "home_ownership", "purpose"]
TARGET_ENC_COLS = ["emp_length"]
BINNED_COLS = ["dti", "revol_util"]
MACRO_FILE = Path("data/macro.csv")


class FeatureEngineer:
    """Fit deterministic encoders and numeric bin boundaries on training data only."""

    def __init__(self, bins: int = 10) -> None:
        self._bins = bins
        self._target_encoders: dict[str, TargetEncoder] = {}
        self._bin_edges: dict[str, np.ndarray] = {}
        self._ohe: OneHotEncoder | None = None
        self._macro: pd.DataFrame | None = None
        self._fitted = False

    def fit(self, df: pd.DataFrame, y: pd.Series) -> "FeatureEngineer":
        for col in TARGET_ENC_COLS:
            encoder = TargetEncoder(cols=[col], smoothing=0.25)
            encoder.fit(df[[col]], y)
            self._target_encoders[col] = encoder

        self._ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False, dtype=np.int8)
        self._ohe.fit(df[OHE_COLS])

        for col in BINNED_COLS:
            quantiles = np.linspace(0.0, 1.0, self._bins + 1)
            edges = np.unique(df[col].quantile(quantiles).to_numpy(dtype=float))
            if len(edges) < 2:
                edges = np.array([-np.inf, np.inf])
            else:
                edges[0], edges[-1] = -np.inf, np.inf
            self._bin_edges[col] = edges

        if MACRO_FILE.exists() and "issue_d" in df.columns:
            macro = pd.read_csv(MACRO_FILE, parse_dates=["date"])
            macro["issue_ym"] = macro["date"].dt.to_period("M")
            self._macro = macro.drop(columns=["date"]).set_index("issue_ym")

        self._fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        if not self._fitted or self._ohe is None:
            raise RuntimeError("FeatureEngineer must be fitted before transform")

        output = df.copy()

        for col, encoder in self._target_encoders.items():
            encoded = encoder.transform(output[[col]])
            output[f"{col}_te"] = encoded[col].astype("float32")
            output.drop(columns=[col], inplace=True)

        encoded_ohe = self._ohe.transform(output[OHE_COLS])
        output[self._ohe.get_feature_names_out(OHE_COLS)] = encoded_ohe.astype("int8")
        output.drop(columns=OHE_COLS, inplace=True)

        for col, edges in self._bin_edges.items():
            output[f"{col}_bin"] = pd.cut(
                output[col], bins=edges, labels=False, include_lowest=True
            ).astype("int8")
            output.drop(columns=[col], inplace=True)

        output["loan_to_income"] = (
            output["loan_amnt"] / output["annual_inc"].clip(lower=1.0)
        ).astype("float32")
        output["dti_emp_inter"] = (df["dti"] * df["emp_length"]).astype("float32")

        # Identifiers must never become predictive inputs.
        output.drop(columns=["loan_id"], errors="ignore", inplace=True)

        if self._macro is not None and "issue_d" in df.columns:
            issue_ym = pd.to_datetime(df["issue_d"]).dt.to_period("M")
            output = output.assign(issue_ym=issue_ym).join(self._macro, on="issue_ym")
            output.drop(columns=["issue_ym"], inplace=True)

        return output.reset_index(drop=True)

    def fit_transform(self, df: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
        return self.fit(df, y).transform(df)
