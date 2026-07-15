"""Validated inference facade with health, readiness, and Prometheus telemetry."""

from __future__ import annotations

import time
from typing import Annotated

from fastapi import FastAPI, Request
from pydantic import BaseModel, ConfigDict, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

from llm.llama3_interface import Llama3Explainer

app = FastAPI(title="Loan Default Risk Predictor", version="0.2.0")
explainer = Llama3Explainer(enabled=False)

REQUESTS = Counter(
    "api_http_requests_total",
    "HTTP requests",
    ("method", "path", "status"),
)
LATENCY = Histogram(
    "api_http_request_duration_seconds",
    "HTTP request latency",
    ("method", "path"),
)


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: Annotated[float, Field(ge=0.0, le=1.0)]
    top_features: dict[str, float] = Field(default_factory=dict, max_length=50)


class PredictionResponse(BaseModel):
    risk_score: float
    explanation: str
    human_review_required: bool


@app.middleware("http")
async def observe(request: Request, call_next):
    started = time.perf_counter()
    response = await call_next(request)
    path = request.scope.get("route").path if request.scope.get("route") else request.url.path
    REQUESTS.labels(request.method, path, response.status_code).inc()
    LATENCY.labels(request.method, path).observe(time.perf_counter() - started)
    return response


@app.get("/healthz", tags=["operations"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz", tags=["operations"])
def ready() -> dict[str, str]:
    # The current facade has no mandatory external dependency.
    return {"status": "ready"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict", response_model=PredictionResponse)
def predict(payload: PredictionRequest) -> PredictionResponse:
    explanation = explainer.explain(payload.risk_score, payload.top_features)
    return PredictionResponse(
        risk_score=payload.risk_score,
        explanation=explanation,
        human_review_required=payload.risk_score > 0.75,
    )
