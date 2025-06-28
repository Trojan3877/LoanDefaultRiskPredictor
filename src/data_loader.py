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
from typing import Iterator, Literal, Optional

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
    def read(self, chunksize: Optional[int] = None) -> Iterator[pd.DataFrame]:
        raise NotImplementedError


# ── Local CSV / Parquet reader ──────────────────────────────────────────────
class _LocalReader(_Reader):
    def __init__(self, path: pathlib.Path):
        self.path = path

    def read(self, chunksize: Optional[int] = None) -> Iterator[pd.DataFrame]:
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

    def read(self, chunksize: Optional[int] = None) -> Iterator[pd.DataFrame]:
        resp = requests.get(self.url, timeout=30)
        resp.raise_for_status()
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

    def read(self, chunksize: Optional[int] = None) -> Iterator[pd.DataFrame]:
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
    def from_uri(cls, uri: str) -> "DataLoader":
        if uri.startswith("s3://"):
            _, bucket, *key = uri.split("/", 3)
            return cls(_S3Reader(bucket, "/".join(key)))
        if uri.startswith(("http://", "https://")):
            return cls(_HTTPReader(uri))
        return cls(_LocalReader(pathlib.Path(uri)))

    @classmethod
    def from_df(cls, df: pd.DataFrame) -> "DataLoader":
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
    """Validate columns, enforce dtypes, drop duplicates & NaNs."""

    if missing := REQUIRED_COLUMNS - set(df.columns):
        raise ValueError(f"Missing columns: {missing}")

    df = df.astype(DTYPES, errors="raise")
    df = df.drop_duplicates("loan_id").dropna()
    return df.reset_index(drop=True)
