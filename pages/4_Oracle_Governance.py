"""Interactive oracle latency and governance response simulator."""

import plotly.graph_objects as go
import streamlit as st

from risk_lab.governance import GovernanceInputs, governance_oracle_path
from risk_lab.ui import PAGE_CONFIG, apply_theme, download_frame, hero


st.set_page_config(**{**PAGE_CONFIG, "page_title": "Oracle & Governance · DeFi Risk Lab"})
apply_theme()
hero(
    "MODULE 04 · AUTOMATED RISK CONTROL",
    "Oracle Latency & Adaptive Governance",
    "Simulate the gap between true and reported collateral prices, then observe how an automated policy changes debt ceilings and liquidation requirements.",
)

with st.sidebar:
    st.header("Shock and oracle")
    price = st.number_input("Initial collateral price (USD)", 1.0, 1_000_000.0, 2_500.0, 50.0)
    shock = st.slider("Collateral shock", -90, 20, -35)
    delay = st.slider("Oracle delay (steps)", 0, 16, 4)
    smoothing = st.slider("Oracle update weight", 0.05, 1.0, 0.35, 0.05)
    st.header("Risk policy")
    ceiling = st.number_input("Initial debt ceiling (USD)", 100_000.0, 10_000_000_000.0, 50_000_000.0, 100_000.0)
    ratio = st.slider("Initial liquidation ratio", 1.10, 2.50, 1.50, 0.05)
    aggressiveness = st.slider("Policy aggressiveness", 0.0, 1.0, 0.65, 0.05)
    steps = st.slider("Simulation steps", 24, 120, 48, 12)

inputs = GovernanceInputs(price, shock, delay, smoothing, ceiling, ratio, aggressiveness, steps)
result, summary = governance_oracle_path(inputs)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Maximum oracle error", f"{summary['max_pricing_error_pct']:.1f}%")
m2.metric("Peak unprotected exposure", f"${summary['peak_unprotected_exposure_usd']:,.0f}")
m3.metric("Final debt ceiling", f"${summary['final_debt_ceiling_usd']:,.0f}")
m4.metric("Peak risk score", f"{summary['peak_risk_score']:.0f}/100")

price_fig = go.Figure()
price_fig.add_trace(go.Scatter(x=result["step"], y=result["true_price"], name="True price", line=dict(color="#22d3ee", width=3)))
price_fig.add_trace(go.Scatter(x=result["step"], y=result["oracle_price"], name="Oracle price", line=dict(color="#f97316", width=3, dash="dot")))
price_fig.update_layout(template="plotly_dark", title="True price versus delayed oracle", xaxis_title="Step", yaxis_title="USD", hovermode="x unified")

policy_fig = go.Figure()
policy_fig.add_trace(go.Scatter(x=result["step"], y=result["debt_ceiling_usd"], name="Debt ceiling", line=dict(color="#a78bfa", width=3)))
policy_fig.add_trace(go.Scatter(x=result["step"], y=result["unprotected_exposure_usd"], name="Unprotected exposure", fill="tozeroy", line=dict(color="#ef4444", width=2)))
policy_fig.update_layout(template="plotly_dark", title="Automated risk response", xaxis_title="Step", yaxis_title="USD", hovermode="x unified")

left, right = st.columns(2)
left.plotly_chart(price_fig, width="stretch")
right.plotly_chart(policy_fig, width="stretch")

if summary["max_pricing_error_pct"] > 20:
    st.error("The oracle temporarily diverges materially from the true price. Faster updates or a more robust multi-oracle design should be tested.")
else:
    st.success("Oracle error remains contained under the selected latency and smoothing assumptions.")

st.caption("The governance controller is intentionally transparent: it gradually lowers the debt ceiling and raises the liquidation ratio as the reported drawdown increases.")
download_frame(result, "oracle_governance_simulation.csv")
