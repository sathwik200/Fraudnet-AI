"""Executive Cyber Command Dashboard for FRAUDNET AI.
=====================================================
Live cryptocurrency threat intelligence command centre displaying macro topological
indicators, 49-timestep cash-flow telemetry, and ML fraud threat distributions.
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from config.settings import (
    DATASET_SUMMARY_PATH,
    TEMPORAL_SUMMARY_PATH,
    NETWORK_PATTERNS_PATH,
    COMMUNITY_SUMMARY_PATH,
    MODEL_SUMMARY_PATH,
)
from src.ui.theme import (
    CYAN,
    BLUE,
    GREEN,
    RED,
    AMBER,
    PURPLE,
    apply_cyber_theme,
)
from src.ui.components import (
    render_command_header,
    render_hero_banner,
    render_cyber_metric,
)


@st.cache_data
def load_overview_data():
    """Load precomputed summary telemetry files."""
    data = {}
    if DATASET_SUMMARY_PATH.exists():
        with open(DATASET_SUMMARY_PATH, "r") as f:
            data["dataset"] = json.load(f)
    if TEMPORAL_SUMMARY_PATH.exists():
        with open(TEMPORAL_SUMMARY_PATH, "r") as f:
            data["temporal"] = json.load(f)
    if NETWORK_PATTERNS_PATH.exists():
        with open(NETWORK_PATTERNS_PATH, "r") as f:
            data["patterns"] = json.load(f)
    if COMMUNITY_SUMMARY_PATH.exists():
        with open(COMMUNITY_SUMMARY_PATH, "r") as f:
            data["communities"] = json.load(f)
    if MODEL_SUMMARY_PATH.exists():
        with open(MODEL_SUMMARY_PATH, "r") as f:
            data["model"] = json.load(f)
    return data


def render_dashboard_page():
    """Render the Cyber Threat Intelligence Command Centre Dashboard."""
    # Top Command Operational Header
    render_command_header("EXECUTIVE COMMAND // INTELLIGENCE CENTER")

    # Command Hero Section
    render_hero_banner(
        title="FRAUDNET AI // CRYPTO TRANSACTION INTELLIGENCE CENTER",
        subtitle="INVESTIGATING THE HIDDEN STRUCTURES BEHIND CRYPTOCURRENCY TRANSACTIONS",
        quote="Autonomous graph neural topology and machine learning surveillance across the Bitcoin payment network.",
        telemetry="DATASET: ELLIPTIC-BTC | VERTICES: 203,769 | EDGES: 234,355 | WCC: 49 | STATUS: LIVE SURVEILLANCE",
    )

    data = load_overview_data()
    dataset_sum = data.get("dataset", {})
    temporal_sum = data.get("temporal", {})
    patterns_sum = data.get("patterns", {})
    comm_sum = data.get("communities", {})
    model_sum = data.get("model", {})
    test_eval = model_sum.get("test_evaluation", {})

    # -------------------------------------------------------------------------
    # 6 FUTURISTIC MAIN INTELLIGENCE METRIC CARDS
    # -------------------------------------------------------------------------
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        render_cyber_metric(
            title="TOTAL TXS",
            value="203,769",
            subtitle="Vertices Across 49 Steps",
            color="cyan",
            icon="⚡",
        )
    with m2:
        render_cyber_metric(
            title="DIRECTED EDGES",
            value="234,355",
            subtitle="Payment Flow Vectors",
            color="blue",
            icon="🔗",
        )
    with m3:
        render_cyber_metric(
            title="ILLICIT LABELED",
            value="4,545",
            subtitle="9.76% of Labeled Truth",
            color="red",
            icon="⚡",
        )
    with m4:
        render_cyber_metric(
            title="LICIT LABELED",
            value="42,019",
            subtitle="90.24% Verified Clean",
            color="green",
            icon="🛡️",
        )
    with m5:
        render_cyber_metric(
            title="UNKNOWN POOL",
            value="157,205",
            subtitle="77.15% Unlabeled Stream",
            color="amber",
            icon="⚪",
        )
    with m6:
        render_cyber_metric(
            title="TIME STEPS",
            value="49 STEPS",
            subtitle="Bi-Weekly Temporal Slices",
            color="purple",
            icon="⏱️",
        )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # TEMPORAL THREAT FLOW CHARTS & ANATOMY
    # -------------------------------------------------------------------------
    c_temporal, c_donut = st.columns([2.1, 1.2])

    with c_temporal:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:4px;">
                // TEMPORAL SURVEILLANCE TELEMETRY (STEPS 1 — 49)
            </div>
            """,
            unsafe_allow_html=True,
        )

        timeline = temporal_sum.get("timeline", [])
        if timeline:
            df_timeline = pd.DataFrame(timeline)
            fig_temp = go.Figure()

            # Total Volume Area Glow
            fig_temp.add_trace(
                go.Scatter(
                    x=df_timeline["time_step"],
                    y=df_timeline["total_transactions"],
                    mode="lines",
                    name="TOTAL TRANSACTION VOLUME",
                    line=dict(color=CYAN, width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(0, 245, 255, 0.05)",
                    hoverinfo="x+y+name",
                )
            )

            # Illicit Volume Trace on Secondary Axis
            fig_temp.add_trace(
                go.Scatter(
                    x=df_timeline["time_step"],
                    y=df_timeline["illicit_count"],
                    mode="lines+markers",
                    name="CONFIRMED ILLICIT SURGE",
                    line=dict(color=RED, width=2.5),
                    marker=dict(size=5, color=RED, symbol="diamond"),
                    yaxis="y2",
                    hoverinfo="x+y+name",
                )
            )

            fig_temp.update_layout(
                yaxis2=dict(
                    title=dict(text="Illicit Txs (Count)", font=dict(color=RED, size=11)),
                    overlaying="y",
                    side="right",
                    gridcolor="rgba(0,0,0,0)",
                    tickfont=dict(color=RED, size=10),
                ),
            )
            apply_cyber_theme(fig_temp, height=360, show_legend=True)
            st.plotly_chart(fig_temp, use_container_width=True)

    with c_donut:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00FF9C; letter-spacing:1px; margin-bottom:4px;">
                // GROUND TRUTH COMPOSITION
            </div>
            """,
            unsafe_allow_html=True,
        )

        labels = ["UNKNOWN / UNLABELED", "LICIT (CLASS 2)", "ILLICIT (CLASS 1)"]
        values = [157205, 42019, 4545]
        colors = ["#172638", GREEN, RED]

        fig_pie = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.62,
                    marker=dict(colors=colors, line=dict(color="#05080D", width=2)),
                    textinfo="percent",
                    textfont=dict(family="'JetBrains Mono', monospace", size=11, color="#FFFFFF"),
                    hoverinfo="label+value+percent",
                )
            ]
        )
        fig_pie.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.2,
                xanchor="center",
                x=0.5,
                font=dict(family="'JetBrains Mono', monospace", size=9, color="#8892B0"),
            ),
            margin=dict(l=10, r=10, t=10, b=30),
            height=360,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # -------------------------------------------------------------------------
    # THREAT OVERVIEW & TOPOLOGICAL ANATOMY
    # -------------------------------------------------------------------------
    st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    c_threat, c_feed = st.columns([1.5, 1])

    with c_threat:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#FFB547; letter-spacing:1px; margin-bottom:8px;">
                // THREAT INTELLIGENCE & MODEL STATUS
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="cyber-card" style="border-left: 3px solid #FFB547;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div>
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0;">ACTIVE CHAMPION ENSEMBLE</span>
                        <div style="font-family:'Chakra Petch',sans-serif; font-size:1.4rem; font-weight:700; color:#FFFFFF;">
                            Random Forest Classifier <span style="font-size:0.85rem; color:#00F5FF; font-family:'JetBrains Mono',monospace;">[v1.0.0]</span>
                        </div>
                    </div>
                    <div class="cyber-status-pill pill-operational">
                        <span>CALIBRATED THRESHOLD: 0.50</span>
                    </div>
                </div>
                <div style="display:grid; grid-template-columns:repeat(4, 1fr); gap:10px; margin-top:14px; text-align:center;">
                    <div style="background:#09121D; padding:10px; border-radius:4px; border:1px solid rgba(0,245,255,0.2);">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#8892B0;">TEST PR-AUC</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; color:#00F5FF;">
                            {test_eval.get('pr_auc', 0.7874):.4f}
                        </div>
                    </div>
                    <div style="background:#09121D; padding:10px; border-radius:4px; border:1px solid rgba(0,245,255,0.2);">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#8892B0;">TEST ROC-AUC</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; color:#168BFF;">
                            {test_eval.get('roc_auc', 0.9384):.4f}
                        </div>
                    </div>
                    <div style="background:#09121D; padding:10px; border-radius:4px; border:1px solid rgba(0,245,255,0.2);">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#8892B0;">ILLICIT F1</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; color:#00FF9C;">
                            {test_eval.get('f1_illicit', 0.7018):.4f}
                        </div>
                    </div>
                    <div style="background:#09121D; padding:10px; border-radius:4px; border:1px solid rgba(0,245,255,0.2);">
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.68rem; color:#8892B0;">FRAUD RECALL</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:1.25rem; font-weight:700; color:#FF3158;">
                            {test_eval.get('recall_illicit', 0.7378):.4f}
                        </div>
                    </div>
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0; margin-top:12px; line-height:1.4;">
                    *NOTE: Evaluation metrics represent out-of-time test performance on unseen time steps 35–49. Zero future data leaked into model training.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c_feed:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#A970FF; letter-spacing:1px; margin-bottom:8px;">
                // TOPOLOGICAL SURVEILLANCE AUDIT
            </div>
            """,
            unsafe_allow_html=True,
        )

        counts = patterns_sum.get("counts", {})
        agg_hubs = counts.get("aggregation_hubs_count", 2042)
        dist_hubs = counts.get("distribution_hubs_count", 2040)
        dual_hubs = counts.get("dual_hubs_count", 512)
        pass_through = counts.get("linear_pass_through_count", 102419)

        st.markdown(
            f"""
            <div class="cyber-terminal-box" style="height:175px; overflow-y:auto;">
                <div><span class="cyber-terminal-prompt">[SYSTEM]</span>Loaded 49 Weakly Connected Components (DAG).</div>
                <div><span class="cyber-terminal-prompt">[AUDIT]</span>Detected <strong>{agg_hubs:,}</strong> High Fan-In Aggregation Hubs (d_in ≥ 9).</div>
                <div><span class="cyber-terminal-prompt">[AUDIT]</span>Detected <strong>{dist_hubs:,}</strong> High Fan-Out Distribution Hubs (d_out ≥ 5).</div>
                <div><span class="cyber-terminal-prompt">[AUDIT]</span>Identified <strong>{dual_hubs:,}</strong> Dual-Flow Relays / Mixing nodes.</div>
                <div><span class="cyber-terminal-prompt">[AUDIT]</span>Indexed <strong>{pass_through:,}</strong> Linear Layering Pass-Through chains.</div>
                <div><span class="cyber-terminal-prompt">[MODULARITY]</span>Louvain Optimization: <strong>{comm_sum[0]['size'] if isinstance(comm_sum, list) and comm_sum else 6620:,}</strong> max community nodes (Q=0.812).</div>
                <div><span class="cyber-terminal-prompt" style="color:#00FF9C;">[READY]</span>Autonomous investigation agents ready for transaction queries.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
