"""FRAUDNET AI — Cyber Intelligence Command Centre
===================================================
AI-Powered Cryptocurrency Transaction Forensics & Threat Intelligence
Engineered on the Elliptic Bitcoin Transaction Dataset.
"""

import streamlit as st

# Streamlit Page Configuration — must be first call
st.set_page_config(
    page_title="FRAUDNET AI // CYBER COMMAND CENTRE",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

import os
from config.settings import GROQ_API_KEY, GROQ_MODEL, get_groq_api_key, get_groq_model
from src.ui.styles import apply_custom_styles
from src.ui.dashboard import render_dashboard_page
from src.ui.transaction_search import render_transaction_search_page
from src.ui.network_visualization import render_network_visualization_page
from src.ui.model_dashboard import render_model_dashboard_page
from src.ui.ai_assistant import render_ai_assistant_page
from src.ui.case_management import render_case_management_page
from src.ui.report_viewer import render_report_viewer_page


def main():
    """Main command centre application orchestrator."""
    # Inject futuristic cybersecurity command centre CSS
    apply_custom_styles()

    # Sidebar: Cyber Operations Desk
    with st.sidebar:
        st.markdown(
            """
            <div class="cyber-sidebar-logo">
                <div class="cyber-sidebar-icon">🛡️</div>
                <div>
                    <div class="cyber-sidebar-title">FRAUDNET AI</div>
                </div>
            </div>
            <div class="cyber-sidebar-sub">
                <span class="pulse-dot dot-cyan"></span>
                <span>CYBER INTELLIGENCE COMMAND</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        nav_options = [
            "⚡ 01 // COMMAND DASHBOARD",
            "🔍 02 // TRANSACTION FORENSICS",
            "🕸️ 03 // NETWORK TOPOLOGY",
            "🧠 04 // MACHINE LEARNING",
            "🤖 05 // AI INVESTIGATION AGENT",
            "📁 06 // CASE OPERATIONS",
            "📄 07 // REPORT VAULT",
        ]

        selected_nav = st.radio("OPERATIONAL MODULE", nav_options, index=0)

        st.markdown("---")
        st.markdown(
            "<span style='font-family:\"JetBrains Mono\",monospace; font-size:0.75rem; color:#00F5FF; font-weight:700;'>// SYSTEM TELEMETRY</span>",
            unsafe_allow_html=True,
        )

        active_key = get_groq_api_key()
        active_model = get_groq_model()
        has_groq = bool(active_key)
        llm_label = f"<span class='active'>READY [{active_model[:12]}]</span>" if has_groq else "<span style='color:#FFB547;'>OFFLINE (DETERMINISTIC)</span>"

        st.markdown(
            f"""
            <div class="cyber-telemetry-box">
                <div><strong>CORE ENGINE:</strong> <span class="active">ACTIVE NOMINAL</span></div>
                <div><strong>MODEL:</strong> <span>RandomForest v1.0</span></div>
                <div><strong>GRAPH:</strong> <span>203,769 Vertices</span></div>
                <div><strong>EDGES:</strong> <span>234,355 Flows</span></div>
                <div><strong>TOPOLOGY:</strong> <span>49 Temporal WCC</span></div>
                <div><strong>AI AGENT:</strong> {llm_label}</div>
                <div><strong>DATABASE:</strong> <span class="active">SQLite Connected</span></div>
                <div><strong>SECURITY:</strong> <span style="color:#00FF9C;">ENCRYPTED LOCAL</span></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("---")
        st.markdown(
            "<span style='font-family:\"JetBrains Mono\",monospace; font-size:0.75rem; color:#00F5FF; font-weight:700;'>// TARGET PRESETS</span>",
            unsafe_allow_html=True,
        )

        col_b1, col_b2 = st.columns(2)
        if col_b1.button("🔴 ILLICIT #1", key="sb_preset_illicit_1", use_container_width=True):
            st.session_state["active_tx_id"] = 232629023
            st.session_state["tx_search_input_val"] = "232629023"
            st.rerun()
        if col_b2.button("🟢 LICIT #1", key="sb_preset_licit_1", use_container_width=True):
            st.session_state["active_tx_id"] = 232438397
            st.session_state["tx_search_input_val"] = "232438397"
            st.rerun()

        if col_b1.button("🔴 PEELING", key="sb_preset_peeling", use_container_width=True):
            st.session_state["active_tx_id"] = 96564456
            st.session_state["tx_search_input_val"] = "96564456"
            st.rerun()
        if col_b2.button("⚪ UNKNOWN", key="sb_preset_unknown", use_container_width=True):
            st.session_state["active_tx_id"] = 230425980
            st.session_state["tx_search_input_val"] = "230425980"
            st.rerun()

        st.markdown(
            """
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem; color:#495670; margin-top:20px; text-align:center;">
                FRAUDNET AI // v2.4.0-CYBER<br>
                CLASSIFIED ACADEMIC RESEARCH 2026
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Route to selected command page
    if "01 // COMMAND DASHBOARD" in selected_nav:
        render_dashboard_page()
    elif "02 // TRANSACTION FORENSICS" in selected_nav:
        render_transaction_search_page()
    elif "03 // NETWORK TOPOLOGY" in selected_nav:
        render_network_visualization_page()
    elif "04 // MACHINE LEARNING" in selected_nav:
        render_model_dashboard_page()
    elif "05 // AI INVESTIGATION AGENT" in selected_nav:
        render_ai_assistant_page()
    elif "06 // CASE OPERATIONS" in selected_nav:
        render_case_management_page()
    elif "07 // REPORT VAULT" in selected_nav:
        render_report_viewer_page()


if __name__ == "__main__":
    main()
