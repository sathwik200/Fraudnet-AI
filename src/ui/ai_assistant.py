"""Cyberpunk AI Forensic Investigation Console for FRAUDNET AI.
============================================================
Autonomous multi-step LangGraph reasoning console interfacing with Groq Cloud LLM
and deterministic algorithmic AML synthesis fallback.
"""

import os
import streamlit as st

import config.settings as app_settings
from src.agents.investigation_agent import run_investigation
from src.ui.components import render_command_header


def render_ai_assistant_page():
    """Render the Cyberpunk AI Investigation Terminal."""
    render_command_header("AI FORENSIC INVESTIGATION TERMINAL")

    st.markdown(
        """
        <div class="cyber-hero-banner" style="padding:16px 20px; margin-bottom:16px;">
            <div style="font-family:'Chakra Petch',sans-serif; font-size:1.4rem; font-weight:700; color:#FFFFFF;">
                🤖 FRAUDNET INTELLIGENCE AGENT // AUTONOMOUS REASONING CONSOLE
            </div>
            <div style="font-family:'Rajdhani',sans-serif; font-size:0.95rem; font-weight:600; color:#00F5FF; letter-spacing:0.8px;">
                AI-POWERED CRYPTOCURRENCY TRANSACTION INVESTIGATION CO-PILOT
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0; margin-top:4px;">
                Orchestrates multi-node LangGraph execution: Entity Extraction ➔ Feature Profile ➔ Ego Subgraph ➔ ML Attribution ➔ Forensic Synthesis.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # API Key Configuration Banner & Drawer
    current_key = os.getenv("GROQ_API_KEY", "") or app_settings.GROQ_API_KEY
    if not current_key.strip():
        st.markdown(
            """
            <div class="cyber-terminal-box" style="border-left: 3px solid #FFB547; margin-bottom:14px;">
                <span class="cyber-terminal-prompt">[SYSTEM NOTICE]</span>
                <strong>GROQ CLOUD API KEY UNCONFIGURED:</strong> Operating in high-precision <strong>DETERMINISTIC FORENSIC ENGINE MODE</strong>. 
                Full topological analytics and supervised ML attribution remain active.
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.expander("🔑 CONFIGURE / INJECT GROQ CLOUD API KEY (OPTIONAL)"):
            new_key = st.text_input(
                "Enter Groq API Key (e.g., gsk_...):",
                type="password",
                help="Obtain key from https://console.groq.com",
            )
            if st.button("AUTHENTICATE GROQ LLM"):
                if new_key.strip():
                    os.environ["GROQ_API_KEY"] = new_key.strip()
                    app_settings.GROQ_API_KEY = new_key.strip()
                    st.success("AUTHENTICATED: Groq Cloud LLM online.")
                    st.rerun()
    else:
        st.markdown(
            f"""
            <div class="cyber-terminal-box" style="border-left: 3px solid #00FF9C; margin-bottom:14px;">
                <span class="cyber-terminal-prompt">[SYSTEM ONLINE]</span>
                <strong>GROQ CLOUD LLM ACTIVE:</strong> Model <code>{app_settings.GROQ_MODEL}</code> connected for live cognitive synthesis.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Initialize chat history
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = [
            {
                "role": "assistant",
                "content": (
                    "**[FRAUDNET AGENT ONLINE]** Forensic co-pilot initialized. "
                    "I can audit any Bitcoin transaction ID from the Elliptic dataset (e.g., `Investigate transaction 230425980`), "
                    "trace payment flows, or explain machine learning fraud risk scores."
                ),
            }
        ]

    # Tactical Quick Prompt Suggestions
    st.markdown(
        "<span style='font-family:\"JetBrains Mono\",monospace; font-size:0.75rem; color:#00F5FF; font-weight:700;'>TACTICAL INVESTIGATION PROMPTS:</span>",
        unsafe_allow_html=True,
    )
    q1, q2, q3, q4 = st.columns(4)
    preset_query = None
    if q1.button("🔍 AUDIT TX 230425980", use_container_width=True):
        preset_query = "Investigate transaction 230425980 and assess illicit risk"
    if q2.button("🔍 AUDIT TX 232438397", use_container_width=True):
        preset_query = "Perform forensic risk analysis on transaction 232438397"
    if q3.button("🛡️ AUDIT TX 232532458", use_container_width=True):
        preset_query = "Analyze transaction 232532458 and determine counterparty risk"
    if q4.button("⚡ AGGREGATION PATTERNS", use_container_width=True):
        preset_query = "Explain how high fan-in aggregation hubs indicate money laundering in Bitcoin"

    # Display Chat History with Cyberpunk Card Styling
    for msg in st.session_state["chat_messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # User Input Field
    user_input = st.chat_input("Enter transaction ID or investigative question...")
    query_to_run = preset_query if preset_query else user_input

    if query_to_run:
        # Append User Message
        st.session_state["chat_messages"].append({"role": "user", "content": query_to_run})
        with st.chat_message("user"):
            st.markdown(query_to_run)

        # Run Multi-Step LangGraph Agent
        with st.chat_message("assistant"):
            with st.spinner("EXECUTING LANGGRAPH STATE MACHINE // RETRIEVING TOPOLOGY & ML EVIDENCE..."):
                result_state = run_investigation(query_to_run)

            # Execution Step Telemetry
            notes = result_state.get("notes", [])
            if notes:
                with st.expander("🔍 AUTONOMOUS LANGGRAPH REASONING CHAIN & EVIDENCE STEPS"):
                    for idx, n in enumerate(notes, 1):
                        st.markdown(
                            f"<div style='font-family:\"JetBrains Mono\",monospace; font-size:0.78rem; color:#00F5FF; padding:3px 0;'>"
                            f"<strong>[STEP 0{idx}]</strong> {n}</div>",
                            unsafe_allow_html=True,
                        )

            final_report = result_state.get("final_report", "NO REPORT GENERATED.")
            st.markdown(final_report)

            # Persist in session state
            st.session_state["chat_messages"].append(
                {"role": "assistant", "content": final_report}
            )
