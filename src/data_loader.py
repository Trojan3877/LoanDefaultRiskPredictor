"""
data_loader.py
──────────────────────────────────────────────────────────────────────────────
Responsibilities
────────────────
1. Locate an input dataset (local path, HTTP, or S3 URL).
2. Load it into a typed **pandas.DataFrame** with explicit dtypes.
3. Perform lightweight schema validation + basic cleaning (NaNs, duplicates).
4. Yield a DataFrame or stream batches to the training pipeline.

Design in a Nutshell
────────────────────
» `DataLoader` is a thin façade that chooses the correct `_Reader`
  implementation based on the URI scheme.
»  All readers return the SAME clean DataFrame so downstream code doesn’t care
   where the data came from.
»  The module is *unit-test friendly* – pass a `pandas.DataFrame` to
   `DataLoader.from_df()` and skip I/O entirely.
"""

from __future__ import annotations

import io
import os
import pathlib
from collections.abc import Iterator
from urllib.parse import urlparse

import boto3
import pandas as pd
import requests

# ── Expected schema & dtypes ────────────────────────────────────────────────
DTYPES = {
    "loan_id": "int64",
    "loan_amnt": "float32",
    "term": "category",
    "emp_length": "float32",
    "home_ownership": "category",
    "annual_inc": "float32",
    "purpose": "category",
    "dti": "float32",
    "delinq_2yrs": "int8",
    "open_acc": "int8",
    "pub_rec": "int8",
    "revol_util": "float32",
    "total_acc": "int8",
    "defaulted": "int8",  # target (0 or 1)
}

REQUIRED_COLUMNS = set(DTYPES.keys())


# ── Abstract Reader Interface ───────────────────────────────────────────────
class _Reader:
    def read(self, chunksize: int | None = None) -> Iterator[pd.DataFrame]:
        raise NotImplementedError


# ── Local CSV / Parquet reader ──────────────────────────────────────────────
class _LocalReader(_Reader):
    def __init__(self, path: pathlib.Path):
        self.path = path

    def read(self, chunksize: int | None = None) -> Iterator[pd.DataFrame]:
        if self.path.suffix in {".parquet", ".pq"}:
            df = pd.read_parquet(self.path, engine="pyarrow").astype(DTYPES)
            yield _clean(df)
        else:  # assume CSV
            for df in pd.read_csv(self.path, chunksize=chunksize, dtype=DTYPES):
                yield _clean(df)


# ── HTTP(S) reader ──────────────────────────────────────────────────────────
class _HTTPReader(_Reader):
    def __init__(self, url: str):
        self.url = url

    def read(self, chunksize: int | None = None) -> Iterator[pd.DataFrame]:
        resp = requests.get(self.url, timeout=30, allow_redirects=False)
        resp.raise_for_status()
        if len(resp.content) > 100 * 1024 * 1024:
            raise ValueError("Remote dataset exceeds 100 MiB limit")
        # Stream into memory; assume CSV for simplicity
        buf = io.StringIO(resp.text)
        for df in pd.read_csv(buf, chunksize=chunksize, dtype=DTYPES):
            yield _clean(df)


# ── S3 reader ───────────────────────────────────────────────────────────────
class _S3Reader(_Reader):
    def __init__(self, bucket: str, key: str):
        self.bucket = bucket
        self.key = key
        self.s3 = boto3.client("s3")

    def read(self, chunksize: int | None = None) -> Iterator[pd.DataFrame]:
        obj = self.s3.get_object(Bucket=self.bucket, Key=self.key)
        body = io.BytesIO(obj["Body"].read())
        if self.key.endswith((".parquet", ".pq")):
            df = pd.read_parquet(body, engine="pyarrow").astype(DTYPES)
            yield _clean(df)
        else:
            for df in pd.read_csv(body, chunksize=chunksize, dtype=DTYPES):
                yield _clean(df)


# ── Public façade ───────────────────────────────────────────────────────────
class DataLoader:
    """Factory that returns an iterable over cleaned DataFrame chunks."""

    def __init__(self, reader: _Reader):
        self._reader = reader

    @classmethod
    def from_uri(cls, uri: str) -> DataLoader:
        if uri.startswith("s3://"):
            parsed = urlparse(uri)
            if not parsed.netloc or not parsed.path.lstrip("/"):
                raise ValueError("S3 URI must include bucket and key")
            return cls(_S3Reader(parsed.netloc, parsed.path.lstrip("/")))
        if uri.startswith(("http://", "https://")):
            parsed = urlparse(uri)
            if parsed.scheme != "https" and os.getenv("ALLOW_INSECURE_DATA_HTTP") != "1":
                raise ValueError("Remote datasets require HTTPS")
            allowed = {
                host.strip()
                for host in os.getenv("ALLOWED_DATA_HOSTS", "").split(",")
                if host.strip()
            }
            if allowed and parsed.hostname not in allowed:
                raise ValueError("Remote dataset host is not allowlisted")
            return cls(_HTTPReader(uri))
        return cls(_LocalReader(pathlib.Path(uri)))

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> DataLoader:
        """Utility for tests—wrap an in-memory DataFrame."""

        class _MemReader(_Reader):
            def read(self, chunksize=None):
                yield _clean(df)

        return cls(_MemReader())

    def __iter__(self):
        return self._reader.read(chunksize=None)

    def iter_chunks(self, chunksize: int = 20_000):
        return self._reader.read(chunksize=chunksize)


# ── Cleaning / validation helpers ───────────────────────────────────────────
def _clean(df: pd.DataFrame) -> pd.DataFrame:
    """Validate a strict research cohort without silently changing membership."""

    if missing := REQUIRED_COLUMNS - set(df.columns):
        raise ValueError(f"Missing columns: {missing}")

    if df.empty:
        raise ValueError("Dataset is empty")
    if df["loan_id"].duplicated().any():
        raise ValueError("Duplicate loan_id values are not allowed")
    if df[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("Missing required values require an explicit imputation policy")
    df = df.astype(DTYPES, errors="raise")
    if not set(df["defaulted"].unique()).issubset({0, 1}):
        raise ValueError("defaulted must be binary")
    ranges = {
        "loan_amnt": (0, 5_000_000),
        "emp_length": (0, 70),
        "annual_inc": (0, 100_000_000),
        "dti": (0, 200),
        "delinq_2yrs": (0, 100),
        "open_acc": (0, 500),
        "pub_rec": (0, 100),
        "revol_util": (0, 500),
        "total_acc": (0, 1000),
    }
    for column, (lower, upper) in ranges.items():
        if not df[column].between(lower, upper, inclusive="both").all():
            raise ValueError(f"{column} contains values outside [{lower}, {upper}]")
    if (df["loan_amnt"] <= 0).any() or (df["annual_inc"] <= 0).any():
        raise ValueError("loan_amnt and annual_inc must be positive")
    return df.reset_index(drop=True)
