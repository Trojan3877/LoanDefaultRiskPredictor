import streamlit as st
from llm.llama3_interface import Llama3Explainer

st.set_page_config(page_title="Loan Risk Dashboard", layout="centered")

st.title("Loan Default Risk Dashboard")

risk_score = st.slider("Predicted Risk Score", 0.0, 1.0, 0.5)

top_features = {
    "debt_ratio": st.slider("Debt Ratio", 0.0, 1.0, 0.3),
    "credit_history": st.slider("Credit History Impact", 0.0, 1.0, 0.4),
}

explainer = Llama3Explainer(enabled=False)

if st.button("Generate Explanation"):
    explanation = explainer.explain(risk_score, top_features)

    st.subheader("Model Explanation")
    st.write(explanation)

    if risk_score > 0.75:
        st.warning("⚠️ Manual review required before decision.")