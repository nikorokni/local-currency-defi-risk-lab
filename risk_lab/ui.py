"""Shared Streamlit presentation helpers."""

import streamlit as st


PAGE_CONFIG = {
    "page_title": "Local-Currency DeFi Risk Lab",
    "page_icon": "◈",
    "layout": "wide",
    "initial_sidebar_state": "expanded",
}


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at 85% 5%, #172554 0%, #07111f 36%, #050a12 100%);
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1830 0%, #070d18 100%);
            border-right: 1px solid rgba(96, 165, 250, 0.18);
        }
        .hero {
            padding: 2.2rem 2.4rem;
            border-radius: 24px;
            background: linear-gradient(125deg, rgba(14,165,233,.18), rgba(124,58,237,.16));
            border: 1px solid rgba(125,211,252,.25);
            box-shadow: 0 24px 60px rgba(0,0,0,.28);
            margin-bottom: 1.3rem;
        }
        .hero h1 { margin: 0; color: #f8fafc; font-size: 2.55rem; }
        .hero p { color: #cbd5e1; font-size: 1.08rem; max-width: 850px; }
        .eyebrow { color: #67e8f9; letter-spacing: .18em; font-size: .78rem; font-weight: 700; }
        .module-card {
            min-height: 190px;
            padding: 1.25rem;
            border-radius: 18px;
            background: rgba(15, 23, 42, .72);
            border: 1px solid rgba(148, 163, 184, .18);
        }
        .module-card h3 { color: #e2e8f0; margin-top: .25rem; }
        .module-card p { color: #94a3b8; }
        [data-testid="stMetric"] {
            background: rgba(15, 23, 42, .64);
            border: 1px solid rgba(96, 165, 250, .18);
            padding: .8rem 1rem;
            border-radius: 14px;
        }
        .caption { color: #94a3b8; font-size: .88rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(eyebrow: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <section class="hero">
          <div class="eyebrow">{eyebrow}</div>
          <h1>{title}</h1>
          <p>{body}</p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def download_frame(frame, filename: str, label: str = "Download simulation CSV") -> None:
    st.download_button(
        label,
        data=frame.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
        width="stretch",
    )
