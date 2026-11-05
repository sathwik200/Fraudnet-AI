"""Transaction Forensic Analysis Terminal for FRAUDNET AI.
==========================================================
Interactive forensic inspection terminal providing deep structural attribution,
directed neighbor cash-flows, and supervised ML threat indicators for any transaction.
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

from src.tools.transaction_tools import get_full_transaction_profile
from src.tools.graph_tools import get_transaction_neighborhood
from src.reports.report_generator import generate_forensic_pdf_report
from src.database.case_repository import CaseRepository
from src.ui.theme import CYAN, RED, GREEN, BLUE, AMBER, PURPLE, apply_cyber_theme
from src.ui.styles import get_risk_badge_html
from src.ui.components import (
    render_command_header,
    render_cyber_metric,
    render_risk_gauge_hud,
)

SAMPLE_TARGETS = {
    "🔴 ILLICIT AGGREGATION #1": 232629023,
    "🔴 ILLICIT PEELING CHAIN #2": 96564456,
    "🟢 VERIFIED LICIT PAYMENT #1": 232438397,
    "🟢 VERIFIED LICIT PAYMENT #2": 232029206,
    "⚪ AMBIGUOUS UNKNOWN STREAM": 230425980,
}


def render_transaction_search_page():
    """Render the forensic analysis workstation."""
    render_command_header("TRANSACTION FORENSIC ANALYSIS TERMINAL")

    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; color:#8892B0; margin-bottom:14px;">
            // SURVEILLANCE TARGET LOOKUP & DEEP FORENSIC ATTRIBUTION
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Initialize active target if not in state
    if "active_tx_id" not in st.session_state:
        st.session_state["active_tx_id"] = 232629023

    # Quick Target Presets
    st.markdown(
        "<span style='font-family:\"JetBrains Mono\",monospace; font-size:0.75rem; color:#00F5FF; font-weight:700;'>QUICK TARGET PRESETS:</span>",
        unsafe_allow_html=True,
    )
    cols = st.columns(len(SAMPLE_TARGETS))
    for idx, (label, tx_val) in enumerate(SAMPLE_TARGETS.items()):
        if cols[idx].button(label, key=f"target_preset_btn_{idx}", use_container_width=True):
            st.session_state["active_tx_id"] = tx_val
            st.session_state["tx_search_input_val"] = str(tx_val)
            st.rerun()

    # Search Bar
    st.markdown(
        """
        <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#00FF9C; margin-top:10px; margin-bottom:-10px;">
            [TERMINAL//QUERY] ENTER BITCOIN TRANSACTION IDENTIFIER (txId):
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Sync text input widget key with active_tx_id
    if "tx_search_input_val" not in st.session_state:
        st.session_state["tx_search_input_val"] = str(st.session_state["active_tx_id"])
    elif st.session_state["tx_search_input_val"].isdigit() and int(st.session_state["tx_search_input_val"]) != st.session_state["active_tx_id"]:
        # Reconcile if active_tx_id changed externally (e.g. from sidebar preset)
        st.session_state["tx_search_input_val"] = str(st.session_state["active_tx_id"])

    def on_tx_search_change():
        val = st.session_state.get("tx_search_input_val", "").strip()
        if val.isdigit():
            st.session_state["active_tx_id"] = int(val)

    tx_input = st.text_input(
        "Enter Transaction ID:",
        key="tx_search_input_val",
        label_visibility="collapsed",
        placeholder="ENTER TRANSACTION HASH / ID...",
        on_change=on_tx_search_change,
    )

    clean_input = tx_input.strip()
    if not clean_input.isdigit():
        st.warning("PLEASE SPECIFY A VALID NUMERIC BITCOIN TRANSACTION IDENTIFIER.")
        return

    tx_id = int(clean_input)
    st.session_state["active_tx_id"] = tx_id

    # Retrieve Profile
    with st.spinner("QUERYING ELLIPTIC BLOCKCHAIN REGISTRY & RUNNING ML ATTRIBUTION..."):
        profile = get_full_transaction_profile(tx_id)

    if profile is None:
        st.error(f"❌ TARGET TRANSACTION `{tx_id}` NOT FOUND IN COMPILED PARQUET REGISTRY.")
        return

    ml = profile["ml_assessment"]
    metrics = profile["graph_metrics"]
    explain = profile["explainability"]

    # -------------------------------------------------------------------------
    # FORENSIC DOSSIER HEADER & RISK GAUGE
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)

    c_meta, c_gauge = st.columns([1.1, 1.3])

    with c_meta:
        gt_label = profile["ground_truth_label"]
        gt_color = RED if gt_label == "1" else (GREEN if gt_label == "2" else "#8892B0")
        gt_text = "CONFIRMED ILLICIT (CLASS 1)" if gt_label == "1" else ("CONFIRMED LICIT (CLASS 2)" if gt_label == "2" else "UNLABELED UNKNOWN STREAM")

        st.markdown(
            f"""
            <div class="cyber-card" style="height:100%;">
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#00F5FF; letter-spacing:1px; margin-bottom:4px;">
                    // TARGET FORENSIC PROFILE
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:1.6rem; font-weight:700; color:#FFFFFF; margin-bottom:8px;">
                    tx_{tx_id}
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; line-height:1.7;">
                    <div><span style="color:#8892B0;">GROUND TRUTH:</span> <strong style="color:{gt_color};">{gt_text}</strong></div>
                    <div><span style="color:#8892B0;">TEMPORAL STEP:</span> <strong style="color:#E6F1FF;">Time Step #{profile['time_step']}</strong></div>
                    <div><span style="color:#8892B0;">LOUVAIN CLUSTER:</span> <strong style="color:#168BFF;">Community #{metrics['community_id']}</strong></div>
                    <div><span style="color:#8892B0;">WCC COMPONENT:</span> <strong style="color:#A970FF;">Component #{metrics['wcc_id']} ({metrics['wcc_size']:,} txs)</strong></div>
                    <div><span style="color:#8892B0;">STRUCTURAL ROLE:</span> <strong style="color:#00FF9C;">{"Aggregation Hub" if metrics['is_aggregation_hub'] else ("Distribution Hub" if metrics['is_distribution_hub'] else "Standard Relay")}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_gauge:
        render_risk_gauge_hud(
            probability=ml["illicit_probability"],
            risk_category=ml["risk_category"],
        )

    # -------------------------------------------------------------------------
    # TOPOLOGICAL METRIC CARDS ROW
    # -------------------------------------------------------------------------
    t1, t2, t3, t4, t5 = st.columns(5)
    with t1:
        render_cyber_metric("IN-DEGREE (INPUTS)", str(metrics["in_degree"]), "Incoming Fund Sources", color="cyan", icon="📥")
    with t2:
        render_cyber_metric("OUT-DEGREE (OUTPUTS)", str(metrics["out_degree"]), "Disbursement Branches", color="blue", icon="📤")
    with t3:
        render_cyber_metric("TOTAL DEGREE", str(metrics["total_degree"]), "Local Connectivity", color="purple", icon="🔗")
    with t4:
        render_cyber_metric("PAGERANK SCORE", f"{metrics['pagerank']:.6f}", "Graph Flow Centrality", color="amber", icon="⚡")
    with t5:
        render_cyber_metric("CLUSTERING COEFF", f"{metrics['clustering_coeff']:.4f}", "Local Triadic Density", color="green", icon="🕸️")

    st.markdown("<div style='margin-bottom:12px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # FORENSIC FEATURE ATTRIBUTION & Z-SCORE VISUALIZATION
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.2rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:8px;">
            // LOCAL FEATURE DEVIATIONS // EMPIRICAL LICIT BASELINE COMPARISON
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("ℹ️ Local feature deviations compare observed values against the empirical licit training baseline (|z| score). Standardized deviations describe statistical variance and do not represent signed causal risk attribution.")

    tab_elev, tab_mit, tab_flows = st.tabs(
        ["📈 POSITIVE BASELINE DEVIATIONS", "📉 NEGATIVE BASELINE DEVIATIONS", "🔄 COUNTERPARTY CASH-FLOWS"]
    )

    with tab_elev:
        elevating = explain.get("top_deviations_above", explain.get("top_risk_elevating", []))
        if elevating:
            df_elev = pd.DataFrame(elevating)
            fig_elev = px.bar(
                df_elev,
                x="z_score",
                y="feature",
                orientation="h",
                color="z_score",
                color_continuous_scale=[[0, "#FFB547"], [1, "#FF3158"]],
                labels={"z_score": "Standard Deviations (Z-Score)", "feature": "Feature"},
                hover_data=["value", "explanation"],
            )
            fig_elev.update_layout(
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
            )
            apply_cyber_theme(fig_elev, height=260, show_legend=False)
            st.plotly_chart(fig_elev, use_container_width=True)

            st.dataframe(
                df_elev[["feature", "value", "z_score", "explanation"]].rename(
                    columns={
                        "feature": "Feature Identifier",
                        "value": "Observed Value",
                        "z_score": "Baseline Deviation (Z)",
                        "explanation": "Descriptive Finding",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("NO POSITIVE STATISTICAL ANOMALIES DETECTED FOR THIS TRANSACTION (|z| < 1.5).")

    with tab_mit:
        mitigating = explain.get("top_deviations_below", explain.get("top_risk_mitigating", []))
        if mitigating:
            df_mit = pd.DataFrame(mitigating)
            fig_mit = px.bar(
                df_mit,
                x="z_score",
                y="feature",
                orientation="h",
                color="z_score",
                color_continuous_scale=[[0, "#00FF9C"], [1, "#168BFF"]],
                labels={"z_score": "Standard Deviations (Z-Score)", "feature": "Feature"},
                hover_data=["value", "explanation"],
            )
            fig_mit.update_layout(
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
            )
            apply_cyber_theme(fig_mit, height=260, show_legend=False)
            st.plotly_chart(fig_mit, use_container_width=True)

            st.dataframe(
                df_mit[["feature", "value", "z_score", "explanation"]].rename(
                    columns={
                        "feature": "Feature Identifier",
                        "value": "Observed Value",
                        "z_score": "Baseline Deviation (Z)",
                        "explanation": "Descriptive Finding",
                    }
                ),
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("NO NEGATIVE STATISTICAL ANOMALIES DETECTED FOR THIS TRANSACTION (|z| < 1.5).")

    with tab_flows:
        neigh = get_transaction_neighborhood(tx_id, hops=1, max_nodes=40)
        c_in, c_out = st.columns(2)
        with c_in:
            st.markdown(f"**📥 Immediate Predecessors ({neigh.get('direct_predecessors_count', 0)} Inputs):**")
            preds = neigh.get("direct_predecessors_sample", [])
            if preds:
                df_in = pd.DataFrame([{"Incoming TxID": f"tx_{p}", "Flow Vector": f"tx_{p} ➔ tx_{tx_id}"} for p in preds])
                st.dataframe(df_in, use_container_width=True, hide_index=True)
            else:
                st.caption("No incoming edges in local graph partition.")

        with c_out:
            st.markdown(f"**📤 Immediate Successors ({neigh.get('direct_successors_count', 0)} Outputs):**")
            succs = neigh.get("direct_successors_sample", [])
            if succs:
                df_out = pd.DataFrame([{"Outgoing TxID": f"tx_{s}", "Flow Vector": f"tx_{tx_id} ➔ tx_{s}"} for s in succs])
                st.dataframe(df_out, use_container_width=True, hide_index=True)
            else:
                st.caption("No outgoing edges in local graph partition.")

    # -------------------------------------------------------------------------
    # OPERATIONAL ACTIONS: CASE MANAGEMENT & PDF EXPORT
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    c_act1, c_act2 = st.columns(2)

    with c_act1:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:8px;">
                // CASE OPERATIONS // ATTACH SUSPECT TRANSACTION
            </div>
            """,
            unsafe_allow_html=True,
        )
        repo = CaseRepository()
        open_cases = repo.list_cases(status="Open")
        case_options = {f"#{c['id']} — {c['title']} ({c['priority']})": c['id'] for c in open_cases}

        if case_options:
            selected_case_name = st.selectbox("Select Target Active Case:", list(case_options.keys()))
            notes_input = st.text_input("Investigator Annotation / Hypothesis:", value=f"Target tx_{tx_id} flagged with {ml['risk_category']} risk tier.")
            if st.button("➕ ATTACH TO SELECTED CASE", use_container_width=True):
                target_case_id = case_options[selected_case_name]
                repo.add_transaction_to_case(
                    case_id=target_case_id,
                    tx_id=tx_id,
                    risk_score=ml["illicit_probability"],
                    risk_category=ml["risk_category"],
                    notes=notes_input,
                )
                st.success(f"TX_{tx_id} SUCCESSFULLY ATTACHED TO CASE #{target_case_id}.")
        else:
            st.info("NO ACTIVE OPEN CASES IN DATABASE. CREATE A CASE IN CASE MANAGEMENT TAB FIRST.")

    with c_act2:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00FF9C; letter-spacing:1px; margin-bottom:8px;">
                // CERTIFIED FORENSIC DOSSIER // PDF GENERATION
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            "Compile an official, tamper-evident PDF 1.4 forensic report containing all network metrics and feature attributions."
        )

        try:
            pdf_path = generate_forensic_pdf_report(tx_id)
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            st.download_button(
                label=f"⬇️ EXPORT FORENSIC PDF DOSSIER (TX_{tx_id}.PDF)",
                data=pdf_bytes,
                file_name=f"FRAUDNET_DOSSIER_TX_{tx_id}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.error(f"Error compiling PDF dossier: {exc}")
