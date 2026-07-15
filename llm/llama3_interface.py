"""Deterministic explanation facade; external LLM calls are disabled by default."""

from __future__ import annotations


class Llama3Explainer:
    def __init__(self, model_name: str = "llama3", enabled: bool = False) -> None:
        self.model_name = model_name
        self.enabled = enabled

    def explain(self, risk_score: float, top_features: dict[str, float]) -> str:
        if not self.enabled:
            return self._mock_explanation(risk_score, top_features)

        prompt = self._build_prompt(risk_score, top_features)
        return f"[LLM OUTPUT PLACEHOLDER] {prompt}"

    @staticmethod
    def _build_prompt(risk_score: float, top_features: dict[str, float]) -> str:
        return (
            f"Explain a loan default risk score of {risk_score:.2f} "
            f"based on the following features: {top_features}. "
            "Use neutral, compliance-friendly language."
        )

    @staticmethod
    def _mock_explanation(risk_score: float, top_features: dict[str, float]) -> str:
        drivers = ", ".join(top_features)
        return (
            f"The predicted default risk is {risk_score:.2f}. "
            f"Key contributing factors include: {drivers}. "
            "This explanation is generated for decision support only "
            "and does not replace human judgment."
        )
