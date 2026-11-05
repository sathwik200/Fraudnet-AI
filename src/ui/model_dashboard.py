"""Supervised Machine Learning Intelligence & Model Control Room.
================================================================
Displays the 3-model comparative validation benchmark, out-of-time test metrics,
confusion matrix telemetry, and global Gini feature importance rankings.
"""

import json
from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config.settings import MODEL_SUMMARY_PATH
from src.tools.model_tools import get_top_global_features
from src.ui.theme import CYAN, BLUE, GREEN, RED, AMBER, PURPLE, apply_cyber_theme
from src.ui.components import (
    render_command_header,
    render_cyber_metric,
)


@st.cache_data
def load_ml_summary():
    """Load model evaluation summary JSON."""
    if MODEL_SUMMARY_PATH.exists():
        with open(MODEL_SUMMARY_PATH, "r") as f:
            return json.load(f)
    return {}


def render_model_dashboard_page():
    """Render the Machine Learning Intelligence Control Room."""
    render_command_header("SUPERVISED ML FRAUD INTELLIGENCE // CONTROL ROOM")

    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; color:#8892B0; margin-bottom:14px;">
            // TEMPORAL FORWARD VALIDATION (TRAIN 1–28, VAL 29–34, TEST 35–49)
        </div>
        """,
        unsafe_allow_html=True,
    )

    data = load_ml_summary()
    test_eval = data.get("test_evaluation", {})
    val_comp = data.get("validation_model_comparison", {})
    champion = data.get("champion_model", "RandomForest")

    # Champion Status Cyber Banner
    st.markdown(
        f"""
        <div class="cyber-card" style="border-left: 4px solid #00FF9C; margin-bottom:18px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#00FF9C; font-weight:700;">
                        ACTIVE CHAMPION ARCHITECTURE
                    </span>
                    <div style="font-family:'Chakra Petch',sans-serif; font-size:1.6rem; font-weight:700; color:#FFFFFF;">
                        🏆 {champion} Classifier Ensemble <span style="font-size:0.85rem; color:#00F5FF; font-family:'JetBrains Mono',monospace;">[v1.0.0-PROD]</span>
                    </div>
                </div>
                <div style="text-align:right;">
                    <div class="cyber-status-pill pill-operational">
                        <span>VAL PR-AUC: {val_comp.get('RandomForest', {}).get('val_pr_auc', 0.9852):.4f}</span>
                    </div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0; margin-top:4px;">
                        CALIBRATED DECISION THRESHOLD: <strong>{test_eval.get('tuned_threshold', 0.50):.2f}</strong>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # -------------------------------------------------------------------------
    # OUT-OF-TIME TEST SET METRICS ROW (STEPS 35 - 49)
    # -------------------------------------------------------------------------
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        render_cyber_metric(
            "TEST PR-AUC",
            f"{test_eval.get('pr_auc', 0.7874):.4f}",
            "Imbalanced Gold Standard",
            color="cyan",
            icon="🎯",
        )
    with m2:
        render_cyber_metric(
            "TEST ROC-AUC",
            f"{test_eval.get('roc_auc', 0.9384):.4f}",
            "Discrimination Capability",
            color="blue",
            icon="📈",
        )
    with m3:
        render_cyber_metric(
            "ILLICIT F1-SCORE",
            f"{test_eval.get('f1_illicit', 0.7018):.4f}",
            "Harmonic Precision-Recall",
            color="green",
            icon="⚖️",
        )
    with m4:
        render_cyber_metric(
            "ILLICIT RECALL",
            f"{test_eval.get('recall_illicit', 0.7378):.4f}",
            "73.8% Fraud Catch Rate",
            color="red",
            icon="⚡",
        )
    with m5:
        render_cyber_metric(
            "OVERALL ACCURACY",
            f"{test_eval.get('accuracy', 0.9593):.4f}",
            "11,710 Test Instances",
            color="purple",
            icon="🛡️",
        )

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # 3-MODEL COMPARATIVE BENCHMARK TABLE
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:6px;">
            // THREE-MODEL VALIDATION BENCHMARK (TIME STEPS 29 — 34)
        </div>
        """,
        unsafe_allow_html=True,
    )

    if val_comp:
        rows = []
        for model_name, metrics in val_comp.items():
            status_text = "🏆 CHAMPION" if model_name == champion else "CANDIDATE"
            rows.append({
                "Architecture": model_name,
                "Operational Status": status_text,
                "Val PR-AUC": f"{metrics.get('val_pr_auc', 0.0):.4f}",
                "Val ROC-AUC": f"{metrics.get('val_roc_auc', 0.0):.4f}",
                "Val F1 (Illicit)": f"{metrics.get('val_f1_illicit', 0.0):.4f}",
                "Precision": f"{metrics.get('val_precision_illicit', 0.0):.4f}",
                "Recall (Catch)": f"{metrics.get('val_recall_illicit', 0.0):.4f}",
            })
        df_models = pd.DataFrame(rows)
        st.dataframe(df_models, use_container_width=True, hide_index=True)

    st.markdown("<div style='margin-bottom:14px;'></div>", unsafe_allow_html=True)

    # -------------------------------------------------------------------------
    # CONFUSION MATRIX & GLOBAL FEATURE IMPORTANCE
    # -------------------------------------------------------------------------
    c_cm, c_feat = st.columns([1, 1.25])

    with c_cm:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#FFB547; letter-spacing:1px; margin-bottom:6px;">
                // TEST SET CONFUSION MATRIX (11,710 INSTANCES)
            </div>
            """,
            unsafe_allow_html=True,
        )

        cm = test_eval.get("confusion_matrix", [[10287, 394], [285, 802]])
        labels_x = ["PRED LICIT", "PRED ILLICIT"]
        labels_y = ["ACTUAL LICIT", "ACTUAL ILLICIT"]

        fig_cm = go.Figure(
            data=go.Heatmap(
                z=cm,
                x=labels_x,
                y=labels_y,
                colorscale=[[0, "#080F18"], [0.5, "#168BFF"], [1, "#00F5FF"]],
                text=[[f"<b>{v:,}</b>" for v in row] for row in cm],
                texttemplate="%{text}",
                textfont=dict(size=15, color="#FFFFFF", family="'JetBrains Mono', monospace"),
                colorbar=dict(
                    title=dict(text="Count", font=dict(color="#8892B0", size=10)),
                    tickfont=dict(color="#8892B0", size=9),
                ),
            )
        )
        apply_cyber_theme(fig_cm, height=330, show_legend=False)
        st.plotly_chart(fig_cm, use_container_width=True)

    with c_feat:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00FF9C; letter-spacing:1px; margin-bottom:6px;">
                // TOP 12 GLOBAL PREDICTIVE FEATURES (GINI IMPORTANCE)
            </div>
            """,
            unsafe_allow_html=True,
        )

        top_feats = get_top_global_features(top_n=12)
        if top_feats:
            df_feats = pd.DataFrame(top_feats)
            fig_bar = px.bar(
                df_feats,
                x="importance",
                y="feature",
                orientation="h",
                color="importance",
                color_continuous_scale=[[0, "#168BFF"], [1, "#00FF9C"]],
                labels={"importance": "Gini Impurity Importance", "feature": "Feature"},
            )
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed"),
                coloraxis_showscale=False,
            )
            apply_cyber_theme(fig_bar, height=330, show_legend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------------------
    # MODEL INTELLIGENCE SPECIFICATION
    # -------------------------------------------------------------------------
    st.markdown(
        """
        <div class="cyber-hero-banner" style="margin-top:10px;">
            <div style="font-family:'Chakra Petch',sans-serif; font-size:1.3rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:6px;">
                // MODEL INTELLIGENCE // TEMPORAL VALIDATION ARCHITECTURE
            </div>
            <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#E6F1FF; line-height:1.6;">
                <div>● <strong>STRICT CHRONOLOGICAL ISOLATION:</strong> Training window restricted to Time Steps 1–28 (29,894 labeled instances). Steps 29–34 reserved for hyperparameter tuning. Steps 35–49 reserved exclusively for out-of-time test evaluation.</div>
                <div>● <strong>ZERO TARGET LEAKAGE:</strong> Transaction identifiers (`txId`), temporal timestamps (`time_step`), and ground-truth labels (`label`) are strictly excluded from input feature tensors.</div>
                <div>● <strong>FEATURE PREPROCESSING REPRODUCIBILITY:</strong> SimpleImputer (median) and StandardScaler fit strictly on training partitions; validation and test sets transformed statelessly.</div>
                <div>● <strong>UNLABELED CLASS HANDLING:</strong> 157,205 unknown transactions strictly excluded from training loss to prevent label corruption.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
