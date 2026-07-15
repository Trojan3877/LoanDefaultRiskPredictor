from fastapi.testclient import TestClient

from api.inference_api import app


client = TestClient(app)


def test_operations_endpoints():
    assert client.get("/healthz").json() == {"status": "ok"}
    assert client.get("/readyz").json() == {"status": "ready"}
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "api_http_requests_total" in metrics.text


def test_predict_contract():
    response = client.post(
        "/predict",
        json={"risk_score": 0.8, "top_features": {"dti": 0.4}},
    )
    assert response.status_code == 200
    assert response.json()["human_review_required"] is True


def test_predict_rejects_invalid_probability_and_extra_fields():
    response = client.post(
        "/predict",
        json={"risk_score": 1.2, "top_features": {}, "borrower_name": "not allowed"},
    )
    assert response.status_code == 422
