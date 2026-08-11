"""Interactive inflation-driven debt erosion simulator."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from risk_lab.debt_erosion import DebtErosionInputs, debt_erosion_path
from risk_lab.ui import PAGE_CONFIG, apply_theme, download_frame, hero


st.set_page_config(**{**PAGE_CONFIG, "page_title": "Debt Erosion · DeFi Risk Lab"})
apply_theme()
hero(
    "MODULE 01 · INFLATION AND FX",
    "Inflation-Driven Debt Erosion",
    "Estimate how a local-currency loan changes in USD terms after interest, currency depreciation, and returns on the asset purchased with the loan proceeds.",
)

scenarios = pd.read_csv("data/country_scenarios.csv")
with st.sidebar:
    st.header("Scenario controls")
    selected = st.selectbox("Country scenario", scenarios["country"].tolist())
    row = scenarios.loc[scenarios["country"] == selected].iloc[0]
    principal = st.number_input("Loan principal (local currency)", 1_000.0, 1_000_000_000.0, 1_000_000.0, 10_000.0)
    fx = st.number_input("Initial FX (local per USD)", 0.01, 10_000_000.0, float(row["fx_local_per_usd"]), format="%.2f")
    depreciation = st.slider("Annual currency depreciation", 0, 300, int(row["depreciation_pct"])) / 100
    loan_rate = st.slider("Annual loan rate", 0, 200, int(row["loan_rate_pct"])) / 100
    asset_return = st.slider("Annual USD asset return", -50, 150, 0) / 100
    horizon = st.slider("Horizon (years)", 0.25, 5.0, 1.0, 0.25)

inputs = DebtErosionInputs(
    principal_local=principal,
    initial_fx_local_per_usd=fx,
    annual_depreciation=depreciation,
    annual_loan_rate=loan_rate,
    asset_annual_return=asset_return,
    horizon_years=horizon,
)
result = debt_erosion_path(inputs)
final = result.iloc[-1]
initial_usd = principal / fx

m1, m2, m3, m4 = st.columns(4)
m1.metric("Initial proceeds", f"${initial_usd:,.0f}")
m2.metric("USD repayment", f"${final['debt_usd']:,.0f}")
m3.metric("Final equity", f"${final['equity_usd']:,.0f}")
m4.metric("Strategy ROI", f"{final['roi_pct']:,.1f}%")

fig = go.Figure()
fig.add_trace(go.Scatter(x=result["year"], y=result["asset_usd"], name="USD asset value", line=dict(color="#22d3ee", width=3)))
fig.add_trace(go.Scatter(x=result["year"], y=result["debt_usd"], name="Debt value in USD", line=dict(color="#f97316", width=3)))
fig.add_trace(go.Scatter(x=result["year"], y=result["equity_usd"], name="Borrower equity", line=dict(color="#a78bfa", width=3, dash="dot")))
fig.update_layout(template="plotly_dark", title="Asset, debt, and equity path", xaxis_title="Years", yaxis_title="USD", hovermode="x unified", legend=dict(orientation="h"))
st.plotly_chart(fig, width="stretch")

st.markdown(
    """
    **Interpretation.** Currency depreciation raises the local-currency units required to buy one USD. If depreciation outpaces the loan interest rate, the USD value of repayment can fall even while the nominal local debt grows. Asset returns are modelled separately so the debt effect is not confused with investment performance.
    """
)
download_frame(result, "debt_erosion_simulation.csv")
