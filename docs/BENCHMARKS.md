# Benchmark Protocol

Run `python -m benchmarks.inference --iterations 300 --warmup 30` on an idle host. Record commit, Python/OS/CPU, workload, warmup, sample count, and raw JSON. The benchmark measures batch-1 feature transformation plus local model inference only.

The 2026-07-22 reference observation was mean 4.248 ms, p50 4.239 ms, p95 4.328 ms, p99 4.676 ms, and 235.396 sequential inferences/s on Python 3.12.13, Windows 11 build 26200, AMD64 Family 25 Model 97.

Synthetic data and the logistic smoke model prove reproducibility and plumbing. They do not measure production LightGBM quality, HTTP capacity, concurrent throughput, availability, or an SLO. Run production-candidate load tests in the target image/infrastructure with a representative verified bundle.
