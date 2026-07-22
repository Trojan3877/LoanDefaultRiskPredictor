# Contributing

```bash
git clone https://github.com/CoreyLeath-code/LoanDefaultRiskPredictor.git
cd LoanDefaultRiskPredictor
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -r requirements/dev.txt
ruff check api src evaluation tests scripts benchmarks
pytest --cov --cov-fail-under=75
```

Do not commit borrower data, credentials, model bundles, outputs, or local environments. Changes to data, features, artifacts, serving, thresholds, metrics, or reason codes require focused tests and an update to the model/governance documentation. Benchmark claims must state dataset, cohort, commit, environment, protocol, uncertainty, and limitations.

Security issues belong in private vulnerability reporting, not public issues.
