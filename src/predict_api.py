"""
predict_api.py
──────────────────────────────────────────────────────────────────────────────
Exposes a REST endpoint for real-time default-probability scoring.

Endpoints
─────────
GET  /                 → {"status": "ok"}
POST /predict          → JSON payload → {"prob": 0.012, "default": false}
GET  /metrics          → Prometheus exposition format

Design
──────
• Loads the **joblib bundle** produced by `train.py` (model + FeatureEngineer).
• Prometheus `Summary` tracks P95 latency; `Counter` counts predictions.
• Optional OpenTelemetry tracing when `OTEL_EXPORTER_OTLP_ENDPOINT` set.
• Ready to be containerised—listens on 0.0.0.0:8000 by default.
"""

from __future__ import annotations

import os
import pathlib
import time
from typing import List

import joblib
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from prometheus_client import Counter, Summary, CONTENT_TYPE_LATEST, generate_latest

# ── Optional OTEL tracing ───────────────────────────────────────────────────
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

    OTEL_ENABLED = bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
except ImportError:
    OTEL_ENABLED = False

# ── Load artefacts (model + FeatureEngineer) ────────────────────────────────
MODEL_PATH = os.getenv("MODEL_PATH", "models/latest.joblib")
if not pathlib.Path(MODEL_PATH).exists():
    raise RuntimeError(f"Model artefact not found at {MODEL_PATH}. Run train.py first.")

bundle = joblib.load(MODEL_PATH)
model = bundle["model"]
feature_engineer = bundle["feature_engineer"]

# ── Prometheus metrics ──────────────────────────────────────────────────────
PRED_LATENCY = Summary("predict_latency_seconds", "Latency of /predict endpoint")
PRED_COUNT = Counter("predictions_total", "Number of predictions served")

# ── FastAPI setup ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Loan Default Risk Predictor",
    version="0.1.0",
    docs_url="/docs",
)

if OTEL_ENABLED:
    tp = TracerProvider()
    tp.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")))
    )
    FastAPIInstrumentor.instrument_app(app, tracer_provider=tp)

# ── Pydantic request/response schemas ───────────────────────────────────────
class LoanRow(BaseModel):
    loan_id: int
    loan_amnt: float
    term: str
    emp_length: float
    home_ownership: str
    annual_inc: float
    purpose: str
    dti: float
    delinq_2yrs: int
    open_acc: int
    pub_rec: int
    revol_util: float
    total_acc: int
    issue_d: str  # ISO date


class Prediction(BaseModel):
    prob: float
    defaulted: bool


# ── Routes ──────────────────────────────────────────────────────────────────
@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/predict", response_model=Prediction)
@PRED_LATENCY.time()
def predict(row: LoanRow):
    try:
        df = feature_engineer.transform(row.model_dump(exclude_none=True, by_alias=False).copy() | {"defaulted": 0})
        prob: float = float(model.predict(df)[0])
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Input error: {e}")

    PRED_COUNT.inc()
    return {"prob": round(prob, 4), "defaulted": prob >= 0.5}


@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ── Local run ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("predict_api:app", host="0.0.0.0", port=8000, reload=False)
