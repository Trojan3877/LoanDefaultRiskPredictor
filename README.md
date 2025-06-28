# 🏦 LoanDefaultRiskPredictor

# 🏦 LoanDefaultRiskPredictor

![Capstone](https://img.shields.io/badge/Project-Capstone-blueviolet?style=for-the-badge)
![Build](https://github.com/Trojan3877/LoanDefaultRiskPredictor/actions/workflows/ci.yml/badge.svg?style=for-the-badge)
![Coverage](https://codecov.io/gh/Trojan3877/LoanDefaultRiskPredictor/branch/main/graph/badge.svg?style=for-the-badge)
![Publish](https://github.com/Trojan3877/LoanDefaultRiskPredictor/actions/workflows/docker-publish.yml/badge.svg?style=for-the-badge)
![Container Scan](https://github.com/Trojan3877/LoanDefaultRiskPredictor/actions/workflows/container-scan.yml/badge.svg?style=for-the-badge)
![Docs](https://img.shields.io/badge/Docs-GitHub%20Pages-informational?style=for-the-badge)
![Telemetry](https://img.shields.io/badge/Telemetry-OTEL-green?style=for-the-badge)

> **LoanDefaultRiskPredictor** is a production-grade credit-risk pipeline that ingests raw loan-application data, engineers explainable features, hyper-tunes a **LightGBM** model with **Optuna**, and serves millisecond-level probability scores through a hardened **FastAPI** endpoint.  
> Containerised with **Docker→Helm→Kubernetes**, scanned by **Trivy**, and signed with **Cosign**, the stack exports AUC/F1, latency, and cost metrics to **Prometheus + Grafana** while nightly snapshots land in **Snowflake** for regulatory audit.  
> Quantifiable targets—*AUC ≥ 0.86 · F1 ≥ 0.54 · P95 latency < 25 ms · cost < $0.001/1k preds*—are enforced in CI and visualised on the live dashboard.

![Architecture](docs/flowchart.png)

![Publish](https://github.com/Trojan3877/LoanDefaultRiskPredictor/actions/workflows/docker-publish.yml/badge.svg?style=for-the-badge)

> 

![image](https://github.com/user-attachments/assets/3338576e-a835-49c8-a67d-82538962af34)
![Architecture](docs/flowchart.png)

![Project Banner](docs/LoanDefault_visual.png)


---

## 📂 File Structure (when complete)

LoanDefaultRiskPredictor/
├── src/
│ ├── data_loader.py # lazy CSV → Parquet reader
│ ├── feature_engineer.py # WOE, bucketing, one-hot
│ ├── train.py # LightGBM training + model registry
│ ├── predict_api.py # FastAPI scoring + Prom metrics
│ └── inference.py # CLI batch scorer
├── tests/ # pytest unit + integration
├── infra/
│ ├── helm/loandefault/ # chart metadata, values, templates
│ ├── ansible/blue_green.yml
│ └── otel/collector.yaml
├── scripts/synthetic_data.py # sample-data generator
├── Dockerfile # multi-stage build
├── Makefile # build, test, docker, helm
├── docs/
│ ├── flowchart.png
│ ├── openapi.json
│ ├── grafana_dashboard.json
│ └── architecture.md


## 📊 Key KPIs

| Metric | Target |
|--------|--------|
| **ROC-AUC** | ≥ 0.86 |
| **F1 Score** | ≥ 0.54 |
| **P95 Inference Latency** | &lt; 25 ms |
| **Cost / 1k Predictions** | &lt; \$0.001 |
| **Uptime (SLA)** | 99.9 % |

---
