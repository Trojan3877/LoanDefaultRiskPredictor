from llm.llama3_interface import Llama3Explainer

def test_mock_llm_explanation():
    explainer = Llama3Explainer(enabled=False)
    explanation = explainer.explain(
        risk_score=0.6,
        top_features={"income": 0.3, "debt_ratio": 0.4}
    )
    assert "default risk" in explanation.lower()