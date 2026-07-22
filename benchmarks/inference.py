"""Reproducible single-process inference benchmark; excludes HTTP and network."""

from __future__ import annotations

import argparse
import json
import math
import platform
import statistics
import tempfile
import time
from pathlib import Path

import pandas as pd

from api.inference_api import _score
from scripts.build_smoke_bundle import build
from src.artifacts import load_bundle


def _percentile(values: list[float], fraction: float) -> float:
    return sorted(values)[max(0, math.ceil(len(values) * fraction) - 1)]


def run(iterations: int = 500, warmup: int = 50) -> dict:
    if iterations < 1 or warmup < 0:
        raise ValueError("iterations must be positive and warmup non-negative")
    with tempfile.TemporaryDirectory() as directory:
        _, bundle = load_bundle(build(Path(directory) / "bundle"))
        row = pd.DataFrame(
            [{"loan_id": 999, "loan_amnt": 12000, "term": "36 months", "emp_length": 5,
              "home_ownership": "RENT", "annual_inc": 65000, "purpose": "debt_consolidation",
              "dti": 22, "delinq_2yrs": 0, "open_acc": 8, "pub_rec": 0,
              "revol_util": 48, "total_acc": 18}]
        )
        def infer() -> float:
            return _score(bundle["model"], bundle["feature_engineer"].transform(row))
        for _ in range(warmup):
            infer()
        latencies: list[float] = []
        started = time.perf_counter()
        for _ in range(iterations):
            call_started = time.perf_counter()
            infer()
            latencies.append((time.perf_counter() - call_started) * 1000)
        duration = time.perf_counter() - started
    return {
        "scope": "batch=1 preprocessing plus model inference; single process; no HTTP/network",
        "environment": {"python": platform.python_version(), "platform": platform.platform(), "processor": platform.processor() or "not reported"},
        "workload": {"iterations": iterations, "warmup": warmup, "synthetic_data": True},
        "results": {
            "latency_ms_mean": round(statistics.fmean(latencies), 3),
            "latency_ms_p50": round(statistics.median(latencies), 3),
            "latency_ms_p95": round(_percentile(latencies, 0.95), 3),
            "latency_ms_p99": round(_percentile(latencies, 0.99), 3),
            "sequential_inferences_per_second": round(iterations / duration, 3),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--warmup", type=int, default=50)
    args = parser.parse_args()
    print(json.dumps(run(args.iterations, args.warmup), indent=2))


if __name__ == "__main__":
    main()
