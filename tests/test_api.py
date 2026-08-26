import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.inference_api import _score, create_app
from tests.helpers import create_test_bundle, valid_request


def test_model_backed_api_and_operations(tmp_path):
    app = create_app(bundle_path=create_test_bundle(tmp_path / "bundle"), api_key="secret")
    with TestClient(app) as client:
        assert client.get("/healthz").json() == {"status": "ok"}
        assert client.get("/readyz").json() == {"status": "ready", "model_version": "test-v1"}
        assert client.post("/predict", json=valid_request()).status_code == 401
        response = client.post(
            "/predict",
            json=valid_request(),
            headers={"X-API-Key": "secret", "X-Request-ID": "request-123"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert 0 <= payload["risk_probability"] <= 1
        assert payload["request_id"] == "request-123"
        assert payload["model_version"] == "test-v1"
        assert len(payload["reason_codes"]) == 3
        feedback = client.post(
            "/feedback",
            json={
                "request_id": "request-123",
                "outcome": "reviewed",
                "observed_at": "2026-07-22T00:00:00Z",
            },
            headers={"X-API-Key": "secret"},
        )
        assert feedback.status_code == 202
        assert "loan_risk_predictions_total" in client.get("/metrics").text


def test_readiness_fails_without_verified_model(tmp_path):
    with TestClient(create_app(bundle_path=tmp_path / "missing")) as client:
        assert client.get("/healthz").status_code == 200
        assert client.get("/readyz").status_code == 503
        assert client.post("/predict", json=valid_request()).status_code == 503


def test_malformed_model_output_is_sanitized(tmp_path, monkeypatch):
    def malformed_score(*_args):
        raise IndexError("missing class probability")

    monkeypatch.setattr("api.inference_api._score", malformed_score)
    app = create_app(bundle_path=create_test_bundle(tmp_path / "bundle"))
    with TestClient(app) as client:
        response = client.post("/predict", json=valid_request())

    assert response.status_code == 503
    assert response.json() == {"detail": "Model scoring unavailable"}


def test_score_rejects_out_of_range_probability():
    class InvalidProbabilityModel:
        def predict(self, _frame):
            return [1.2]

    with pytest.raises(ValueError, match=r"outside \[0, 1\]"):
        _score(InvalidProbabilityModel(), pd.DataFrame([{"feature": 1}]))


def test_request_contract_rejects_invalid_and_extra_values(tmp_path):
    app = create_app(bundle_path=create_test_bundle(tmp_path / "bundle"))
    bad = {**valid_request(), "dti": -1, "borrower_name": "must-not-be-accepted"}
    with TestClient(app) as client:
        assert client.post("/predict", json=bad).status_code == 422


def test_feedback_requires_a_timezone_aware_timestamp(tmp_path):
    app = create_app(bundle_path=create_test_bundle(tmp_path / "bundle"))
    with TestClient(app) as client:
        response = client.post(
            "/feedback",
            json={
                "request_id": "request-123",
                "outcome": "reviewed",
                "observed_at": "not-a-timestamp",
            },
        )

    assert response.status_code == 422


def test_production_requires_authentication_and_model(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("LOAN_RISK_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="LOAN_RISK_API_KEY"), TestClient(
        create_app(bundle_path=tmp_path / "missing")
    ):
        pass
