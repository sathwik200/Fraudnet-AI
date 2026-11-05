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
    current_key = app_settings.get_groq_api_key()
    current_model = app_settings.get_groq_model()

    from src.agents.groq_client import verify_groq_connectivity, mask_api_key

    if not current_key:
        st.markdown(
            """
            <div class="cyber-terminal-box" style="border-left: 3px solid #FFB547; margin-bottom:14px;">
                <span class="cyber-terminal-prompt">[SYSTEM NOTICE]</span>
                <strong>EXECUTION MODE: DETERMINISTIC FALLBACK</strong> — GROQ_API_KEY unconfigured. 
                Operating in high-precision rule-based forensic mode. Full topological analytics and supervised ML attribution remain active.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="cyber-terminal-box" style="border-left: 3px solid #00F5FF; margin-bottom:14px;">
                <span class="cyber-terminal-prompt">[SYSTEM READY]</span>
                <strong>GROQ API KEY CONFIGURED ({mask_api_key(current_key)}):</strong> Target Model: <code>{current_model}</code>. 
                Execution mode will report <strong>GROQ LIVE</strong> only upon verified successful completion.
            </div>
            """,
            unsafe_allow_html=True,
        )

    with st.expander("🔑 CONFIGURE / VERIFY GROQ CLOUD API"):
        c1, c2 = st.columns([3, 1])
        with c1:
            new_key = st.text_input(
                "Groq API Key:",
                value="",
                placeholder=f"Current: {mask_api_key(current_key)}",
                type="password",
                help="Key is securely stored in session/environment and never exposed or logged.",
            )
        with c2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("SET KEY", use_container_width=True):
                if new_key.strip():
                    os.environ["GROQ_API_KEY"] = new_key.strip()
                    app_settings.GROQ_API_KEY = new_key.strip()
                    st.success("API key registered in active session.")
                    st.rerun()

        st.caption(f"Configured Model: `{current_model}` (from `GROQ_MODEL` or default `openai/gpt-oss-120b`)")
        if st.button("⚡ TEST LIVE GROQ CONNECTIVITY & MODEL AVAILABILITY"):
            with st.spinner("Pinging Groq models endpoint & verifying completion..."):
                verify_res = verify_groq_connectivity()
            if verify_res.get("connected"):
                st.success(f"✅ {verify_res.get('message')}")
            else:
                st.warning(f"⚠️ {verify_res.get('message')}")

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
            if "investigation_cache" not in st.session_state:
                st.session_state["investigation_cache"] = {}

            if query_to_run in st.session_state["investigation_cache"]:
                result_state = st.session_state["investigation_cache"][query_to_run]
            else:
                with st.spinner("EXECUTING LANGGRAPH STATE MACHINE // RETRIEVING TOPOLOGY & ML EVIDENCE..."):
                    result_state = run_investigation(query_to_run)
                st.session_state["investigation_cache"][query_to_run] = result_state

            # Execution Mode Indicator Banner
            is_live = result_state.get("llm_used", False)
            exec_mode = "GROQ LIVE" if is_live else "DETERMINISTIC FALLBACK"
            exec_pill = "pill-cyan" if is_live else "pill-amber"
            model_info = f" ({result_state.get('model_name', current_model)})" if is_live else ""

            st.markdown(
                f"""
                <div style="margin-bottom:10px;">
                    <span class="cyber-status-pill {exec_pill}" style="font-size:0.75rem; padding:4px 10px; font-weight:700;">
                        {'⚡' if is_live else '🛡️'} EXECUTION MODE: {exec_mode}{model_info}
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )

            fallback_reason = result_state.get("fallback_reason")
            if not is_live and fallback_reason and fallback_reason != "GROQ_API_KEY unconfigured":
                st.markdown(
                    f"""
                    <div class="cyber-terminal-box" style="border-left: 3px solid #FF3158; margin-bottom:10px; font-size:0.8rem; padding:8px 12px;">
                        <span class="cyber-terminal-prompt">[NOTICE]</span>
                        Groq inference unavailable ({fallback_reason}). High-precision deterministic fallback engaged.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

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
