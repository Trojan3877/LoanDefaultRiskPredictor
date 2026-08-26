# Benchmark Protocol

## Purpose

`benchmarks/inference.py` measures one narrow engineering path: batch-1 feature transformation plus local model inference in a single Python process using the deterministic synthetic smoke bundle. It is designed to make plumbing/performance observations reproducible enough to compare like-for-like CI runs.

It does **not** measure HTTP/network/TLS overhead, concurrency, queueing, multi-worker behavior, representative LightGBM performance, model quality, production capacity, availability, or an SLO.

## Canonical CI command

```bash
python -m benchmarks.inference \
  --iterations 1000 \
  --warmup 100 \
  --output outputs/ci-inference-benchmark.json
```

## Evidence schema

The JSON record contains:

- schema version and UTC generation timestamp;
- source Git commit (`GITHUB_SHA` in CI);
- Python, OS/platform, and processor string;
- synthetic smoke model version and SHA-256;
- synthetic input SHA-256;
- warmup and measured iteration counts;
- latency mean, population standard deviation, p50, p95, p99, minimum, and maximum;
- sequential inferences per second;
- peak traced Python memory during the measured loop;
- success count and success rate;
- explicit benchmark limitations.

## Comparison rules

Only compare observations when the important experimental conditions are compatible. At minimum retain:

1. source commit;
2. benchmark JSON artifact;
3. Python/platform information;
4. model checksum and model version;
5. input checksum;
6. warmup and sample counts.

A change in the model bundle, feature transformation, input, host class, Python version, or benchmark implementation can invalidate a direct comparison.

## Interpretation

The benchmark is a **microbenchmark**, not a service load test. A high sequential inference rate cannot be converted into API requests/second because the measured loop excludes request parsing, authentication, rate limiting, serialization, transport, concurrency contention, and infrastructure behavior.

Before defining a latency SLO or capacity target, run target-image HTTP and concurrency tests against representative infrastructure and an approved model bundle. Record workload shape, concurrency, duration, warmup, failures, host/container resources, and percentile latency.
