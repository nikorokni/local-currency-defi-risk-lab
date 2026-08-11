"""Landing page for the Local-Currency DeFi Risk Lab."""

import streamlit as st

from risk_lab.ui import PAGE_CONFIG, apply_theme, hero


st.set_page_config(**PAGE_CONFIG)
apply_theme()

hero(
    "OPEN RESEARCH TOOLKIT · PYTHON + STREAMLIT",
    "Local-Currency DeFi Risk Lab",
    "An interactive laboratory for testing how inflation, currency depreciation, collateral shocks, liquidity constraints, oracle latency, and governance rules interact in local-currency DeFi systems.",
)

st.markdown("### Four connected risk layers")
columns = st.columns(4)
cards = [
    (
        "01",
        "Debt Erosion",
        "Compare local debt growth with FX depreciation and the USD value of converted loan proceeds.",
    ),
    (
        "02",
        "Solvency Stress",
        "Measure liquidation and bad-debt risk under joint collateral and currency shocks.",
    ),
    (
        "03",
        "Peg Stability",
        "Explore how liquidity, arbitrage capital, fees, and oracle delays shape peg recovery.",
    ),
    (
        "04",
        "Oracle & Governance",
        "Test delayed price signals and automated debt-ceiling and liquidation-ratio responses.",
    ),
]
for column, (number, title, text) in zip(columns, cards):
    with column:
        st.markdown(
            f'<div class="module-card"><div class="eyebrow">MODULE {number}</div><h3>{title}</h3><p>{text}</p></div>',
            unsafe_allow_html=True,
        )

st.markdown("### Research workflow")
left, right = st.columns([1.25, 1])
with left:
    st.markdown(
        """
        1. **Set a baseline** using one of the included country scenarios.
        2. **Change assumptions** through the controls in each module.
        3. **Compare paths and tail risks** using interactive Plotly charts.
        4. **Export the simulation** as CSV for notebooks, papers, or robustness checks.

        The models are transparent reduced-form research tools. Every equation is implemented in the `risk_lab/` package and tested independently from the interface.
        """
    )
with right:
    st.info(
        "This lab is designed for scenario analysis and research communication. It is not financial advice, a price oracle, or a production risk engine."
    )
    st.markdown(
        "**Start here:** choose a simulation page from the sidebar. Each module contains its own assumptions, metrics, chart, and downloadable results."
    )

st.markdown("### Model map")
st.code(
    "Inflation & FX → Debt value → Protocol solvency → Market peg → Oracle signal → Governance response",
    language=None,
)

st.caption(
    "Built as a companion implementation for the local-currency DeFi research series by Niko Rokni Lamouki and collaborators."
)
