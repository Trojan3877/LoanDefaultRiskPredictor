"""Single supported, model-backed FastAPI application."""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

import pandas as pd
from fastapi import FastAPI, Header, HTTPException, Request, status
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from starlette.responses import Response

from api.controls import SlidingWindowRateLimiter, valid_api_key
from api.schemas import FeedbackRequest, LoanRequest, PredictionResponse
from src.artifacts import ModelManifest, load_bundle

LOGGER = logging.getLogger("loan_risk.audit")
REQUESTS = Counter("loan_risk_requests_total", "Requests", ("route", "status"))
LATENCY = Histogram("loan_risk_request_duration_seconds", "Request latency", ("route",))
PREDICTIONS = Counter("loan_risk_predictions_total", "Predictions", ("review", "model_version"))
FEEDBACK = Counter("loan_risk_feedback_total", "Outcome feedback", ("outcome", "model_version"))
IN_FLIGHT = Gauge("loan_risk_in_flight", "In-flight model requests")


def _score(model: Any, frame: pd.DataFrame) -> float:
    if hasattr(model, "predict_proba"):
        return float(model.predict_proba(frame)[0, 1])
    return float(model.predict(frame)[0])


def _reason_codes(raw: LoanRequest) -> list[str]:
    """Deterministic, reviewable placeholders; policy owners must approve production mapping."""

    candidates = {
        "HIGH_DEBT_TO_INCOME": raw.dti,
        "HIGH_REVOLVING_UTILIZATION": raw.revol_util,
        "RECENT_DELINQUENCY": float(raw.delinq_2yrs > 0) * 100,
        "HIGH_LOAN_TO_INCOME": raw.loan_amnt / raw.annual_inc * 100,
    }
    return [
        name for name, _ in sorted(candidates.items(), key=lambda item: item[1], reverse=True)[:3]
    ]


def create_app(
    *,
    bundle_path: str | Path | None = None,
    api_key: str | None = None,
    requests_per_minute: int = 120,
    max_concurrency: int = 8,
) -> FastAPI:
    configured_source = (
        bundle_path if bundle_path is not None else os.getenv("MODEL_BUNDLE_PATH", "models/current")
    )
    configured_path = Path(configured_source)
    expected_key = api_key if api_key is not None else os.getenv("LOAN_RISK_API_KEY")
    limiter = SlidingWindowRateLimiter(requests_per_minute)
    admission = BoundedSemaphore(max_concurrency)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.manifest = None
        application.state.payload = None
        application.state.load_error = None
        production = os.getenv("ENVIRONMENT", "development") == "production"
        if production and expected_key is None:
            raise RuntimeError("Production requires LOAN_RISK_API_KEY")
        try:
            manifest, payload = load_bundle(configured_path)
            application.state.manifest = manifest
            application.state.payload = payload
        except (FileNotFoundError, ValueError, OSError) as exc:
            application.state.load_error = str(exc)
            if production:
                raise RuntimeError(f"Production model failed verification: {exc}") from exc
        yield

    application = FastAPI(
        title="Loan Default Risk Predictor",
        version="1.0.0",
        lifespan=lifespan,
        description="Model-backed research API. Not an automated lending decision system.",
    )

    @application.middleware("http")
    async def observe(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        started = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", request.url.path)
        REQUESTS.labels(route, response.status_code).inc()
        LATENCY.labels(route).observe(time.perf_counter() - started)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    def authorize(request: Request, supplied_key: str | None) -> None:
        client = request.client.host if request.client else "unknown"
        if not valid_api_key(expected_key, supplied_key):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
        if not limiter.allow(client):
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Rate limit exceeded")

    @application.get("/healthz", tags=["operations"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/readyz", tags=["operations"])
    def ready(request: Request) -> dict[str, str]:
        manifest: ModelManifest | None = request.app.state.manifest
        if manifest is None:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Verified model unavailable")
        return {"status": "ready", "model_version": manifest.model_version}

    @application.get("/metrics", include_in_schema=False)
    def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @application.post("/predict", response_model=PredictionResponse)
    def predict(
        payload: LoanRequest,
        request: Request,
        x_api_key: str | None = Header(default=None),
        x_request_id: str | None = Header(default=None),
    ) -> PredictionResponse:
        authorize(request, x_api_key)
        manifest: ModelManifest | None = request.app.state.manifest
        bundle: dict[str, Any] | None = request.app.state.payload
        if manifest is None or bundle is None:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Verified model unavailable")
        if not admission.acquire(blocking=False):
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Inference capacity exhausted")
        IN_FLIGHT.inc()
        try:
            raw = pd.DataFrame([payload.model_dump()])
            transformed = bundle["feature_engineer"].transform(raw)
            probability = min(1.0, max(0.0, _score(bundle["model"], transformed)))
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY, "Feature transformation failed"
            ) from exc
        finally:
            IN_FLIGHT.dec()
            admission.release()
        request_id = x_request_id or str(uuid.uuid4())
        review = probability >= manifest.threshold
        PREDICTIONS.labels(str(review).lower(), manifest.model_version).inc()
        LOGGER.info(
            json.dumps(
                {
                    "event": "risk_prediction",
                    "request_id": request_id,
                    "model_version": manifest.model_version,
                    "policy_version": manifest.policy_version,
                    "review_recommended": review,
                }
            )
        )
        return PredictionResponse(
            request_id=request_id,
            risk_probability=round(probability, 6),
            review_recommended=review,
            reason_codes=_reason_codes(payload),
            model_version=manifest.model_version,
            policy_version=manifest.policy_version,
        )

    @application.post("/feedback", status_code=status.HTTP_202_ACCEPTED)
    def feedback(
        payload: FeedbackRequest,
        request: Request,
        x_api_key: str | None = Header(default=None),
    ) -> dict[str, str]:
        authorize(request, x_api_key)
        manifest: ModelManifest | None = request.app.state.manifest
        if manifest is None:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Verified model unavailable")
        FEEDBACK.labels(payload.outcome, manifest.model_version).inc()
        LOGGER.info(
            json.dumps(
                {
                    "event": "outcome_feedback",
                    "request_id": payload.request_id,
                    "model_version": manifest.model_version,
                    "outcome": payload.outcome,
                    "observed_at": payload.observed_at,
                }
            )
        )
        return {"status": "accepted"}

    return application


app = create_app()
