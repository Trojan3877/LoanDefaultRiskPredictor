from benchmarks.inference import run


def test_benchmark_contract():
    result = run(iterations=3, warmup=1)
    assert result["workload"]["synthetic_data"] is True
    assert result["results"]["latency_ms_p99"] > 0
