# LoanDefaultRiskPredictor • Makefile
# -----------------------------------------------------------
# Simplifies common tasks: build, test, Docker, Helm deploy
# -----------------------------------------------------------

IMAGE        ?= ghcr.io/coreyleath-code/loandefaultriskpredictor:dev
CHART        ?= infra/helm/loandefault
NAMESPACE    ?= loandefault
MODEL_PATH   ?= models/current

.PHONY: build
build:
	@echo "🔧 Building virtualenv & compiling feature engineer"
	python -m pip install -r requirements/dev.txt
	python -m compileall api/ src/ evaluation/

.PHONY: test
test: build
	@echo "🧪 Running pytest with coverage"
	pytest --cov --cov-fail-under=75

.PHONY: train
train: build
	@echo "🧠 Training LightGBM model"
	python -m src.train --uri data/synthetic_loans.csv --trials 20 --output $(MODEL_PATH)

.PHONY: api
api: build
	@echo "🚀 Launching FastAPI on http://0.0.0.0:8000"
	uvicorn api.inference_api:app --reload --port 8000

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
