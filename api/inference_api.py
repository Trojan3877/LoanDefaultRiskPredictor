from fastapi import FastAPI
from llm.llama3_interface import Llama3Explainer

app = FastAPI()
explainer = Llama3Explainer(enabled=False)

@app.post("/predict")
def predict(payload: dict):
    """
    payload example:
    {
      "risk_score": 0.68,
      "top_features": {"debt_ratio": 0.42, "credit_history": 0.31}
    }
    """
    risk_score = payload["risk_score"]
    top_features = payload["top_features"]

    explanation = explainer.explain(risk_score, top_features)

    return {
        "risk_score": risk_score,
        "explanation": explanation,
        "human_review_required": risk_score > 0.75
    }