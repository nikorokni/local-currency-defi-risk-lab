"""Interactive stablecoin peg recovery simulator."""

import plotly.graph_objects as go
import streamlit as st

from risk_lab.peg import PegInputs, peg_recovery_path
from risk_lab.ui import PAGE_CONFIG, apply_theme, download_frame, hero


st.set_page_config(**{**PAGE_CONFIG, "page_title": "Peg Stability · DeFi Risk Lab"})
apply_theme()
hero(
    "MODULE 03 · LIQUIDITY AND ARBITRAGE",
    "Stablecoin Peg Resilience",
    "Explore how market depth, arbitrage capacity, fees, and oracle latency determine the speed and completeness of a stablecoin's return to target.",
)

with st.sidebar:
    st.header("Market shock")
    deviation = st.slider("Initial peg deviation", -30.0, 30.0, -8.0, 0.5)
    liquidity = st.number_input("DEX liquidity (USD)", 10_000.0, 1_000_000_000.0, 5_000_000.0, 50_000.0)
    arbitrage = st.number_input("Available arbitrage capital (USD)", 0.0, 500_000_000.0, 500_000.0, 25_000.0)
    fee = st.slider("Trading and execution friction", 0.0, 3.0, 0.30, 0.05)
    delay = st.slider("Oracle / execution delay (hours)", 0.0, 24.0, 2.0, 0.5)
    horizon = st.slider("Simulation horizon (hours)", 12, 168, 72, 12)

inputs = PegInputs(deviation, liquidity, arbitrage, fee, delay, horizon)
result = peg_recovery_path(inputs)
final = result.iloc[-1]
within_one = result.loc[result["deviation_pct"].abs() <= 1.0, "hour"]
recovery_hour = float(within_one.iloc[0]) if not within_one.empty else None

m1, m2, m3, m4 = st.columns(4)
m1.metric("Initial market price", f"${1 + deviation / 100:.4f}")
m2.metric("Final market price", f"${final['stablecoin_price']:.4f}")
m3.metric("Recovered deviation", f"{final['recovered_share_pct']:.1f}%")
m4.metric("Time to ±1%", f"{recovery_hour:.0f} h" if recovery_hour is not None else "Not reached")

fig = go.Figure()
fig.add_trace(go.Scatter(x=result["hour"], y=result["stablecoin_price"], name="Market price", fill="tozeroy", line=dict(color="#22d3ee", width=3)))
fig.add_hline(y=1.0, line_color="#a78bfa", line_dash="dash", annotation_text="Target peg")
fig.add_hrect(y0=0.99, y1=1.01, fillcolor="#22c55e", opacity=0.10, line_width=0)
fig.update_layout(template="plotly_dark", title="Peg recovery path", xaxis_title="Hours", yaxis_title="Stablecoin price", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

st.markdown("#### Bottleneck reading")
capital_ratio = arbitrage / liquidity if liquidity else 0
if delay >= 8:
    st.warning("Oracle or execution latency is the dominant bottleneck in this scenario.")
elif capital_ratio < 0.05:
    st.warning("Arbitrage capital is small relative to pool liquidity, so recovery is slow.")
else:
    st.success("The scenario has enough arbitrage capacity for a comparatively fast recovery after the delay window.")

st.caption("This reduced-form model isolates recovery frictions. It does not reproduce a specific AMM invariant or guarantee executable arbitrage profits.")
download_frame(result, "peg_recovery_simulation.csv")
