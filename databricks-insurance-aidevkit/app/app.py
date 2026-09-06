"""Insurance AI Dev Kit — Databricks App.

A Streamlit front-end for claims teams that ties the kit's assets together:

1. **Fraud triage** — score a claim against the fraud Model Serving endpoint.
2. **Policy Q&A** — ask the Mosaic AI agent a coverage question.
3. **Portfolio KPIs** — read the gold loss-ratio table over a SQL Warehouse.

Runs on Databricks Apps; it authenticates as the App's service principal via
the Databricks SDK. Every backend call degrades gracefully so the App still
renders before the jobs/endpoints have been deployed.
"""
from __future__ import annotations

import os

import pandas as pd
import streamlit as st

CATALOG = os.environ.get("INSURANCE_CATALOG", "insurance_dev")
SCHEMA = os.environ.get("INSURANCE_SCHEMA", "lakehouse")
FRAUD_ENDPOINT = os.environ.get("FRAUD_SERVING_ENDPOINT", "fraud-detection-dev")
AGENT_ENDPOINT = os.environ.get("AGENT_SERVING_ENDPOINT", "policy-qa-agent-dev")
WAREHOUSE_ID = os.environ.get("SQL_WAREHOUSE_ID", "")

st.set_page_config(page_title="Insurance AI Dev Kit", page_icon="🏛️", layout="wide")


# --------------------------------------------------------------------------- #
# Databricks clients (lazy + cached so a missing dep never blanks the page)
# --------------------------------------------------------------------------- #
@st.cache_resource
def _workspace():
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient()


def risk_band(prob: float) -> str:
    """Mirror of src/ml/fraud_detection/features.py — SIU triage bands."""
    if prob >= 0.75:
        return "HIGH"
    if prob >= 0.40:
        return "MEDIUM"
    return "LOW"


def score_claim(features: dict) -> float | None:
    """Query the fraud Model Serving endpoint; None if unavailable."""
    try:
        resp = _workspace().serving_endpoints.query(
            name=FRAUD_ENDPOINT,
            dataframe_records=[features],
        )
        pred = resp.predictions[0]
        # Endpoint may return a probability or a {"1": p} style mapping.
        if isinstance(pred, dict):
            return float(pred.get("1", list(pred.values())[-1]))
        return float(pred)
    except Exception as exc:  # noqa: BLE001 - surfaced to the user below
        st.session_state["fraud_error"] = str(exc)
        return None


def ask_agent(question: str) -> str | None:
    try:
        resp = _workspace().serving_endpoints.query(
            name=AGENT_ENDPOINT,
            messages=[{"role": "user", "content": question}],
        )
        choice = resp.choices[0]
        return choice.message.content if choice.message else str(resp.as_dict())
    except Exception as exc:  # noqa: BLE001
        st.session_state["agent_error"] = str(exc)
        return None


@st.cache_data(ttl=300)
def load_kpis() -> pd.DataFrame | None:
    if not WAREHOUSE_ID:
        return None
    try:
        from databricks import sql
        from databricks.sdk.core import Config

        cfg = Config()
        with sql.connect(
            server_hostname=cfg.host,
            http_path=f"/sql/1.0/warehouses/{WAREHOUSE_ID}",
            credentials_provider=lambda: cfg.authenticate,
        ) as conn:
            return pd.read_sql(
                f"""
                SELECT claim_type, region, claim_count, total_incurred,
                       loss_ratio, fraud_rate
                FROM {CATALOG}.{SCHEMA}.gold_portfolio_kpis
                ORDER BY loss_ratio DESC
                """,
                conn,
            )
    except Exception as exc:  # noqa: BLE001
        st.session_state["kpi_error"] = str(exc)
        return None


# --------------------------------------------------------------------------- #
# UI
# --------------------------------------------------------------------------- #
st.title("🏛️ Insurance AI Dev Kit")
st.caption(f"Catalog `{CATALOG}.{SCHEMA}` · fraud `{FRAUD_ENDPOINT}` · agent `{AGENT_ENDPOINT}`")

triage_tab, qa_tab, kpi_tab = st.tabs(["🚦 Fraud triage", "💬 Policy Q&A", "📊 Portfolio KPIs"])

with triage_tab:
    st.subheader("Score a claim for fraud risk")
    c1, c2, c3 = st.columns(3)
    claim_amount = c1.number_input("Claim amount ($)", min_value=0.0, value=27500.0, step=500.0)
    coverage = c2.number_input("Coverage amount ($)", min_value=0.0, value=100000.0, step=1000.0)
    premium = c3.number_input("Annual premium ($)", min_value=0.0, value=1200.0, step=50.0)
    c4, c5 = st.columns(2)
    days_to_report = c4.number_input("Days to report", min_value=0, value=40, step=1)
    tenure = c5.number_input("Customer tenure (years)", min_value=0.0, value=0.5, step=0.5)

    if st.button("Score claim", type="primary"):
        features = {
            "claim_amount": claim_amount,
            "days_to_report": days_to_report,
            "amount_to_coverage_ratio": round(claim_amount / coverage, 4) if coverage else 0.0,
            "claim_to_premium_ratio": round(claim_amount / premium, 4) if premium else 0.0,
            "is_new_customer": int(tenure < 1.0),
            "high_value_claim": int(claim_amount >= 25_000),
        }
        prob = score_claim(features)
        if prob is None:
            st.warning(
                "Serving endpoint not reachable yet — deploy "
                "`fraud_detection_training` first. Error: "
                + st.session_state.get("fraud_error", "unknown")
            )
        else:
            band = risk_band(prob)
            color = {"HIGH": "🔴", "MEDIUM": "🟠", "LOW": "🟢"}[band]
            st.metric("Fraud probability", f"{prob:.1%}")
            st.subheader(f"{color} Triage band: {band}")
            st.json(features, expanded=False)

with qa_tab:
    st.subheader("Ask the policy assistant")
    question = st.text_input("Question", value="Does comprehensive auto cover hail damage?")
    if st.button("Ask", type="primary"):
        answer = ask_agent(question)
        if answer is None:
            st.warning(
                "Agent endpoint not reachable yet — deploy `policy_qa_agent` first. "
                "Error: " + st.session_state.get("agent_error", "unknown")
            )
        else:
            st.markdown(answer)

with kpi_tab:
    st.subheader("Loss ratio & fraud rate by product / region")
    kpis = load_kpis()
    if kpis is None or kpis.empty:
        st.info(
            "No KPI data yet. Set `warehouse_id` in databricks.yml and run "
            "`claims_ingestion` so the gold tables exist."
        )
        if "kpi_error" in st.session_state:
            st.caption("Detail: " + st.session_state["kpi_error"])
    else:
        st.dataframe(kpis, use_container_width=True)
        st.bar_chart(kpis.set_index("claim_type")["loss_ratio"])
