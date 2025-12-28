class Llama3Explainer:
    def __init__(self, model_name="llama3", enabled=False):
        """
        enabled=False by default to avoid accidental live LLM calls.
        """
        self.model_name = model_name
        self.enabled = enabled

    def explain(self, risk_score: float, top_features: dict) -> str:
        if not self.enabled:
            return self._mock_explanation(risk_score, top_features)

        # Placeholder for MCP / real LLaMA-3 call
        prompt = self._build_prompt(risk_score, top_features)
        return f"[LLM OUTPUT PLACEHOLDER] {prompt}"

    def _build_prompt(self, risk_score, top_features):
        return (
            f"Explain a loan default risk score of {risk_score:.2f} "
            f"based on the following features: {top_features}. "
            "Use neutral, compliance-friendly language."
        )

    def _mock_explanation(self, risk_score, top_features):
        drivers = ", ".join(top_features.keys())
        return (
            f"The predicted default risk is {risk_score:.2f}. "
            f"Key contributing factors include: {drivers}. "
            "This explanation is generated for decision support only "
            "and does not replace human judgment."
        )