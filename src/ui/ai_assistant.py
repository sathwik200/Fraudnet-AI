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

    # API Key Configuration Banner & Live Status
    current_key = app_settings.get_groq_api_key()
    current_model = app_settings.get_groq_model()
    is_live = st.session_state.get("groq_verified_live", False)

    from src.agents.groq_client import verify_groq_connectivity, mask_api_key

    # Status Banner: GROQ LIVE vs CONFIGURED / NOT VERIFIED vs DETERMINISTIC FALLBACK
    if is_live:
        st.markdown(
            f"""
            <div class="cyber-terminal-box" style="border-left: 3px solid #00FF9C; margin-bottom:12px;">
                <span class="cyber-terminal-prompt">[SYSTEM ONLINE]</span>
                <strong>EXECUTION MODE: GROQ LIVE</strong> — Live cognitive forensic synthesis verified active via Model <code>{current_model}</code>.
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif current_key:
        st.markdown(
            f"""
            <div class="cyber-terminal-box" style="border-left: 3px solid #00F5FF; margin-bottom:12px;">
                <span class="cyber-terminal-prompt">[SYSTEM STANDBY]</span>
                <strong>EXECUTION MODE: CONFIGURED / NOT VERIFIED</strong> — API key registered ({mask_api_key(current_key)}) for Model <code>{current_model}</code>. Click verification control below to test live inference.
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div class="cyber-terminal-box" style="border-left: 3px solid #FFB547; margin-bottom:12px;">
                <span class="cyber-terminal-prompt">[SYSTEM NOTICE]</span>
                <strong>EXECUTION MODE: DETERMINISTIC FALLBACK</strong> — GROQ_API_KEY unconfigured. 
                Operating in high-precision rule-based forensic mode. Full topological analytics and supervised ML attribution remain active.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # Visible Connectivity Test Control (Un-nested, prominently rendered)
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:0.95rem; font-weight:700; color:#00F5FF; letter-spacing:0.5px; margin-bottom:6px;">
            // GROQ CLOUD LIVE VERIFICATION & MODEL HEALTH CHECK
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_btn, col_hint = st.columns([3, 2])
    with col_btn:
        test_clicked = st.button(
            "⚡ TEST LIVE GROQ CONNECTIVITY & MODEL AVAILABILITY",
            use_container_width=True,
            key="btn_live_groq_connectivity_test",
        )
    with col_hint:
        st.caption(f"Target Model: `{current_model}` | Status: **{'GROQ LIVE' if is_live else ('CONFIGURED / NOT VERIFIED' if current_key else 'DETERMINISTIC FALLBACK')}**")

    if test_clicked:
        with st.spinner(f"Testing Groq Cloud endpoint & verifying model '{current_model}'..."):
            v_res = verify_groq_connectivity()
            st.session_state["groq_verify_result"] = v_res
            if v_res.get("connected"):
                st.session_state["groq_verified_live"] = True
                st.session_state["groq_verified_model"] = v_res.get("model", current_model)
            else:
                st.session_state["groq_verified_live"] = False
        st.rerun()

    # Display Persistent Diagnostic Output Card
    verify_res = st.session_state.get("groq_verify_result")
    if verify_res:
        if verify_res.get("connected"):
            st.markdown(
                f"""
                <div style="background:rgba(0, 255, 156, 0.08); border:1px solid #00FF9C; border-radius:4px; padding:12px 16px; margin:8px 0 16px 0;">
                    <div style="font-family:'Rajdhani',sans-serif; font-weight:700; color:#00FF9C; font-size:1.05rem;">
                        ✅ LIVE GROQ API CONNECTIVITY CONFIRMED
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#FFFFFF; margin-top:4px;">
                        • <strong>Configured Model:</strong> <code>{verify_res.get('model', current_model)}</code> (Verified available on Groq Cloud)<br>
                        • <strong>Real Chat Completion:</strong> <span style="color:#00FF9C; font-weight:700;">SUCCESS (Non-empty test inference received)</span><br>
                        • <strong>System Execution State:</strong> <span style="color:#00FF9C; font-weight:700;">GROQ LIVE ACTIVE</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background:rgba(255, 49, 88, 0.08); border:1px solid #FF3158; border-radius:4px; padding:12px 16px; margin:8px 0 16px 0;">
                    <div style="font-family:'Rajdhani',sans-serif; font-weight:700; color:#FF3158; font-size:1.05rem;">
                        ⚠️ GROQ API CONNECTIVITY NOTICE
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#FFFFFF; margin-top:4px;">
                        • <strong>Configured Model:</strong> <code>{verify_res.get('model', current_model)}</code><br>
                        • <strong>Real Chat Completion:</strong> <span style="color:#FF3158;">FAILED / UNAVAILABLE</span><br>
                        • <strong>Diagnostic Message:</strong> <span style="color:#FFB547;">{verify_res.get('message', 'Unknown failure')}</span><br>
                        • <strong>Current System State:</strong> <span style="color:#FFB547; font-weight:700;">DETERMINISTIC FALLBACK (Active)</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Optional Session Key Override Drawer
    with st.expander("🔑 ADVANCED: INJECT / OVERRIDE GROQ CLOUD API KEY (OPTIONAL)"):
        c1, c2 = st.columns([3, 1])
        with c1:
            new_key = st.text_input(
                "Groq API Key:",
                value="",
                placeholder=f"Current: {mask_api_key(current_key)}",
                type="password",
                help="Key is stored securely in runtime session and never logged or exposed.",
            )
        with c2:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            if st.button("SET KEY", use_container_width=True):
                if new_key.strip():
                    os.environ["GROQ_API_KEY"] = new_key.strip()
                    app_settings.GROQ_API_KEY = new_key.strip()
                    st.session_state["groq_verify_result"] = None
                    st.session_state["groq_verified_live"] = False
                    st.success("API key registered in active session.")
                    st.rerun()

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
            if is_live:
                st.session_state["groq_verified_live"] = True
                st.session_state["groq_verified_model"] = result_state.get("model_name", current_model)

            exec_mode = "GROQ LIVE" if is_live else "DETERMINISTIC FALLBACK"
            exec_pill = "pill-operational" if is_live else "pill-amber"
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
