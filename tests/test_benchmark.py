from benchmarks.inference import run


def test_benchmark_contract():
    result = run(iterations=3, warmup=1)
    assert result["schema_version"] == 1
    assert result["workload"]["synthetic_data"] is True
    assert len(result["workload"]["input_sha256"]) == 64
    assert len(result["model"]["model_sha256"]) == 64
    assert result["results"]["latency_ms_p99"] > 0
    assert result["results"]["success_count"] == 3
    assert result["results"]["success_rate"] == 1.0
    assert result["results"]["peak_traced_python_memory_bytes"] >= 0
