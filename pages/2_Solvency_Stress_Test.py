"""Interactive deterministic and Monte Carlo solvency testing."""

import plotly.express as px
import streamlit as st

from risk_lab.solvency import SolvencyInputs, monte_carlo_solvency, solvency_snapshot
from risk_lab.ui import PAGE_CONFIG, apply_theme, download_frame, hero


st.set_page_config(**{**PAGE_CONFIG, "page_title": "Solvency Stress · DeFi Risk Lab"})
apply_theme()
hero(
    "MODULE 02 · COLLATERAL AND LIQUIDATION",
    "DeFi Solvency Stress Test",
    "Stress a local-currency debt position against collateral drawdowns, FX moves, liquidation thresholds, and correlated Monte Carlo outcomes.",
)

with st.sidebar:
    st.header("Position")
    collateral = st.number_input("Collateral value (USD)", 1_000.0, 100_000_000.0, 150_000.0, 1_000.0)
    debt_local = st.number_input("Debt (local currency)", 1_000.0, 10_000_000_000.0, 100_000_000.0, 100_000.0)
    fx = st.number_input("FX (local per USD)", 0.01, 10_000_000.0, 1_000.0)
    liquidation_ratio = st.slider("Liquidation ratio", 1.10, 2.50, 1.50, 0.05)
    st.header("Stress assumptions")
    collateral_shock = st.slider("Expected collateral shock", -90, 30, -30) / 100
    fx_depreciation = st.slider("Expected currency depreciation", -50, 300, 40) / 100
    collateral_vol = st.slider("Collateral volatility", 5, 150, 60) / 100
    fx_vol = st.slider("FX volatility", 5, 120, 35) / 100
    simulations = st.select_slider("Monte Carlo paths", [1_000, 5_000, 10_000, 25_000], 10_000)

inputs = SolvencyInputs(collateral, debt_local, fx, liquidation_ratio, collateral_shock, fx_depreciation)
snapshot = solvency_snapshot(inputs)
paths, summary = monte_carlo_solvency(inputs, simulations, collateral_vol, fx_vol)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Stressed collateral ratio", f"{snapshot['collateral_ratio']:.2f}×")
m2.metric("Liquidation probability", f"{summary['liquidation_probability']:.1%}")
m3.metric("Insolvency probability", f"{summary['insolvency_probability']:.1%}")
m4.metric("Expected bad debt", f"${summary['expected_bad_debt_usd']:,.0f}")

left, right = st.columns([1.45, 1])
with left:
    fig = px.histogram(paths, x="collateral_ratio", nbins=80, template="plotly_dark", color_discrete_sequence=["#38bdf8"], title="Distribution of collateral ratios")
    fig.add_vline(x=1.0, line_color="#ef4444", line_dash="dash", annotation_text="Insolvency")
    fig.add_vline(x=liquidation_ratio, line_color="#f59e0b", line_dash="dash", annotation_text="Liquidation")
    st.plotly_chart(fig, width="stretch")
with right:
    st.markdown("#### Deterministic shock")
    st.write(f"Stressed debt value: **${snapshot['stressed_debt_usd']:,.0f}**")
    st.write(f"Liquidation shortfall: **${snapshot['liquidation_shortfall_usd']:,.0f}**")
    st.write(f"Bad debt: **${snapshot['bad_debt_usd']:,.0f}**")
    state = "Insolvent" if snapshot["insolvent"] else "Liquidatable" if snapshot["liquidatable"] else "Healthy"
    st.info(f"Position state: **{state}**")

st.caption("The Monte Carlo model applies correlated lognormal collateral and FX shocks. It is a transparent stress-testing approximation, not a calibrated forecasting model.")
download_frame(paths, "solvency_monte_carlo.csv")
