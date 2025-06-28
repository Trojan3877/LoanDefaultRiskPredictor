"""
synthetic_data.py
──────────────────────────────────────────────────────────────────────────────
Generates a realistic loan-application dataset for demos, unit tests, and CI
pipelines so you don’t have to commit proprietary banking data.

Usage
─────
python scripts/synthetic_data.py --rows 100_000 --out data/synthetic_loans.csv

Arguments
─────────
--rows   Number of rows to generate (default 10 000)
--out    Output path (.csv or .parquet)  [default: synthetic_loans.csv]
"""

from __future__ import annotations

import argparse
import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()


def gen_rows(n: int) -> pd.DataFrame:
    rng = np.random.default_rng(2025)

    df = pd.DataFrame(
        {
            "loan_id": np.arange(1, n + 1, dtype="int64"),
            "loan_amnt": rng.normal(15_000, 8_000, n).clip(1_000, 60_000).round(0),
            "term": rng.choice([" 36 months", " 60 months"], n, p=[0.7, 0.3]),
            "emp_length": rng.integers(0, 11, n).astype("float32"),
            "home_ownership": rng.choice(
                ["RENT", "OWN", "MORTGAGE", "OTHER"], n, p=[0.4, 0.1, 0.45, 0.05]
            ),
            "annual_inc": rng.normal(82_000, 37_000, n).clip(15_000, 250_000).round(0),
            "purpose": rng.choice(
                ["debt_consolidation", "credit_card", "home_improvement", "other"], n
            ),
            "dti": rng.beta(2, 20, n) * 40,
            "delinq_2yrs": rng.poisson(0.15, n),
            "open_acc": rng.poisson(11, n),
            "pub_rec": rng.poisson(0.25, n),
            "revol_util": rng.beta(2, 5, n) * 100,
            "total_acc": rng.poisson(27, n),
            "issue_d": [fake.date_between("2016-01-01", "2020-12-31") for _ in range(n)],
        }
    )

    # True underlying probability (not directly observed)
    base_prob = 0.06
    prob = (
        base_prob
        + 0.15 * (df["dti"] > 25)
        + 0.10 * (df["emp_length"] < 1)
        + 0.05 * (df["revol_util"] > 80)
        + 0.04 * (df["loan_amnt"] > 40_000)
    )

    df["defaulted"] = rng.random(n) < prob.clip(0, 0.9)
    return df.astype(
        {
            "loan_amnt": "float32",
            "annual_inc": "float32",
            "dti": "float32",
            "revol_util": "float32",
            "defaulted": "int8",
        }
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--rows", type=int, default=10_000)
    p.add_argument("--out", default="synthetic_loans.csv")
    args = p.parse_args()

    df = gen_rows(args.rows)
    out_path = args.out

    if out_path.endswith(".parquet"):
        df.to_parquet(out_path, index=False)
    else:
        df.to_csv(out_path, index=False)

    print(f"📝 Generated {args.rows} rows → {out_path}")
