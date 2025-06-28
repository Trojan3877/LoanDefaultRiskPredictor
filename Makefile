# LoanDefaultRiskPredictor • Makefile
# -----------------------------------------------------------
# Simplifies common tasks: build, test, Docker, Helm deploy
# -----------------------------------------------------------

IMAGE        ?= trojan3877/loandefaultriskpredictor:dev
CHART        ?= infra/helm/loandefault
NAMESPACE    ?= loandefault
MODEL_PATH   ?= models/latest.joblib

.PHONY: build
build:
	@echo "🔧 Building virtualenv & compiling feature engineer"
	python -m pip install -r requirements.txt
	python -m compileall src/

.PHONY: test
test: build
	@echo "🧪 Running pytest with coverage"
	coverage run -m pytest -q
	coverage report -m

.PHONY: train
train: build
	@echo "🧠 Training LightGBM model"
	python src/train.py --uri data/synthetic_loans.csv --trials 40 --output $(MODEL_PATH)

.PHONY: api
api: build
	@echo "🚀 Launching FastAPI on http://0.0.0.0:8000"
	uvicorn src.predict_api:app --reload --port 8000

.PHONY: docker
docker:
	@echo "🐳 Building Docker image → $(IMAGE)"
	docker build -t $(IMAGE) .

.PHONY: helm-up
helm-up:
	@echo "⛴  Deploying via Helm"
	helm upgrade --install loandefault $(CHART) \
		--namespace $(NAMESPACE) --create-namespace \
		--set image.repository=$(IMAGE%:*),image.tag=$(IMAGE#*:),image.pullPolicy=IfNotPresent

.PHONY: helm-down
helm-down:
	helm uninstall loandefault -n $(NAMESPACE) || true

.PHONY: clean
clean:
	rm -rf __pycache__ .pytest_cache .coverage htmlcov models/*.joblib
