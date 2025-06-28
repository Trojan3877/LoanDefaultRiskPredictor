# Contributing to LoanDefaultRiskPredictor

We’re excited to have you improving production-grade credit-risk ML!  
Follow the steps below to get productive quickly and maintain the repo’s quality bar.

---

## 1 – Local Setup

```bash
git clone https://github.com/Trojan3877/LoanDefaultRiskPredictor.git
cd LoanDefaultRiskPredictor
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
pre-commit install               # run style checks on every commit
make build && make test          # compile + run unit tests
