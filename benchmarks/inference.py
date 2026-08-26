"""Reproducible single-process inference benchmark; excludes HTTP and network."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import statistics
import tempfile
import time
import tracemalloc
from datetime import UTC, datetime
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

    row_record = {
        "loan_id": 999,
        "loan_amnt": 12000,
        "term": "36 months",
        "emp_length": 5,
        "home_ownership": "RENT",
        "annual_inc": 65000,
        "purpose": "debt_consolidation",
        "dti": 22,
        "delinq_2yrs": 0,
        "open_acc": 8,
        "pub_rec": 0,
        "revol_util": 48,
        "total_acc": 18,
    }
    input_sha256 = hashlib.sha256(
        json.dumps(row_record, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    with tempfile.TemporaryDirectory() as directory:
        manifest, bundle = load_bundle(build(Path(directory) / "bundle"))
        row = pd.DataFrame([row_record])

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

        memory_probe_iterations = min(iterations, 100)
        tracemalloc.start()
        for _ in range(memory_probe_iterations):
            infer()
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()

    return {
        "schema_version": 1,
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": os.getenv("SOURCE_COMMIT") or os.getenv("GITHUB_SHA", "local-uncommitted"),
        "scope": "batch=1 preprocessing plus model inference; single process; no HTTP/network",
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "not reported",
        },
        "model": {
            "model_version": manifest.model_version,
            "model_sha256": manifest.model_sha256,
            "synthetic_smoke_bundle": True,
        },
        "workload": {
            "iterations": iterations,
            "warmup": warmup,
            "synthetic_data": True,
            "input_sha256": input_sha256,
        },
        "results": {
            "latency_ms_mean": round(statistics.fmean(latencies), 3),
            "latency_ms_stdev": round(statistics.pstdev(latencies), 3),
            "latency_ms_p50": round(statistics.median(latencies), 3),
            "latency_ms_p95": round(_percentile(latencies, 0.95), 3),
            "latency_ms_p99": round(_percentile(latencies, 0.99), 3),
            "latency_ms_min": round(min(latencies), 3),
            "latency_ms_max": round(max(latencies), 3),
            "sequential_inferences_per_second": round(iterations / duration, 3),
            "peak_traced_python_memory_bytes": peak_memory,
            "memory_probe_iterations": memory_probe_iterations,
            "success_count": iterations,
            "success_rate": 1.0,
        },
        "limitations": [
            "Synthetic smoke bundle and one synthetic input",
            "Excludes HTTP, network, TLS, concurrency, and queueing",
            "Memory tracing runs separately from the latency loop to avoid instrumentation bias",
            "Does not establish LightGBM model quality or a production SLO",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--warmup", type=int, default=50)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = json.dumps(run(args.iterations, args.warmup), indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")


if __name__ == "__main__":
    main()
