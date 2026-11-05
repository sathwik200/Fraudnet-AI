"""Forensic Dossier Generator and Report Vault Interface.
======================================================
Compiles official PDF 1.4 forensic dossiers and provides permanent archival
access to certified intelligence reports.
"""

from pathlib import Path
import streamlit as st
import pandas as pd

from src.database.case_repository import CaseRepository
from src.reports.report_generator import generate_forensic_pdf_report
from src.ui.theme import CYAN, RED, GREEN, BLUE, AMBER, PURPLE
from src.ui.components import (
    render_command_header,
    render_cyber_metric,
)


def render_report_viewer_page():
    """Render the Cyberpunk Report Generator and Vault interface."""
    render_command_header("FORENSIC INTELLIGENCE REPORTS & VAULT")

    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; color:#8892B0; margin-bottom:14px;">
            // COURT-READY CERTIFIED PDF DOSSIERS & HISTORICAL AUDIT ARCHIVE
        </div>
        """,
        unsafe_allow_html=True,
    )

    repo = CaseRepository()

    t_gen, t_vault = st.tabs(["⚡ INSTANT DOSSIER COMPILER", "🗄️ HISTORICAL REPORT VAULT"])

    with t_gen:
        st.markdown(
            """
            <div class="cyber-card" style="margin-bottom:16px;">
                <div style="font-family:'Rajdhani',sans-serif; font-size:1.2rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:8px;">
                    // ON-DEMAND FORENSIC PDF COMPILER
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem; color:#8892B0; line-height:1.5;">
                    Generates a standards-compliant PDF 1.4 intelligence dossier containing target identification,
                    supervised ML fraud scores, color-coded risk badges, PageRank centrality, and full XAI feature attributions.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_tx, c_cert = st.columns([1.5, 1])
        with c_tx:
            default_tx = st.session_state.get("active_tx_id", 232629023)
            if "report_tx_input_val" not in st.session_state or st.session_state.get("report_last_active") != default_tx:
                st.session_state["report_tx_input_val"] = str(default_tx)
                st.session_state["report_last_active"] = default_tx

            def on_report_input_change():
                val = st.session_state.get("report_tx_input_val", "").strip()
                if val.isdigit():
                    st.session_state["active_tx_id"] = int(val)
                    st.session_state["report_last_active"] = int(val)

            tx_input = st.text_input(
                "Target Transaction Identifier (txId):",
                key="report_tx_input_val",
                on_change=on_report_input_change,
            )
        with c_cert:
            author_input = st.text_input("Certifying Officer Signature:", value="Sathwik M (Senior AML Auditor)")

        if st.button("🚀 COMPILE & CERTIFY FORENSIC DOSSIER", use_container_width=True):
            if tx_input.strip().isdigit():
                tx_id = int(tx_input.strip())
                try:
                    with st.spinner("COMPILING FORENSIC EVIDENCE & RENDERING PDF 1.4 BYTESTREAM..."):
                        pdf_path = generate_forensic_pdf_report(tx_id, generated_by=author_input)

                    file_size_kb = pdf_path.stat().st_size / 1024

                    # Record in SQLite history
                    repo.record_report(
                        report_title=f"Forensic Intelligence Dossier: Tx {tx_id}",
                        file_path=str(pdf_path),
                        tx_id=tx_id,
                    )

                    st.success(f"✅ DOSSIER CERTIFIED AND GENERATED SUCCESSFULLY ({file_size_kb:.1f} KB).")

                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()

                    st.download_button(
                        label=f"⬇️ DOWNLOAD DOSSIER (TX_{tx_id}.PDF)",
                        data=pdf_bytes,
                        file_name=f"FRAUDNET_DOSSIER_TX_{tx_id}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as exc:
                    st.error(f"Error compiling forensic report: {exc}")
            else:
                st.warning("Please specify a valid numeric transaction ID.")

    with t_vault:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00FF9C; letter-spacing:1px; margin-bottom:8px;">
                // CERTIFIED REPORT VAULT & AUDIT LOG
            </div>
            """,
            unsafe_allow_html=True,
        )

        records = repo.list_reports()
        if not records:
            st.info("NO HISTORICAL REPORTS CURRENTLY RECORDED IN VAULT.")
        else:
            rec_rows = []
            for r in records:
                p = Path(r["file_path"])
                sz_str = f"{p.stat().st_size / 1024:.1f} KB" if p.exists() else "Archived"
                rec_rows.append({
                    "Report ID": f"REP-{r['id']:04d}",
                    "Report Title": r["report_title"],
                    "Target Transaction": f"tx_{r['tx_id']}" if r.get("tx_id") else "Multi-Tx Case",
                    "Generated Timestamp": r["created_at"][:19],
                    "File Size": sz_str,
                    "file_path": r["file_path"],
                })

            df_recs = pd.DataFrame(rec_rows)
            st.dataframe(df_recs.drop(columns=["file_path"]), use_container_width=True, hide_index=True)

            st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
            sel_rep = st.selectbox("Select Archived Dossier to Download:", [r["Report ID"] for r in rec_rows])
            matched = next((r for r in rec_rows if r["Report ID"] == sel_rep), None)
            if matched:
                target_p = Path(matched["file_path"])
                if target_p.exists():
                    with open(target_p, "rb") as f:
                        arch_data = f.read()
                    st.download_button(
                        label=f"⬇️ DOWNLOAD ARCHIVED {target_p.name}",
                        data=arch_data,
                        file_name=target_p.name,
                        mime="application/pdf",
                    )
                else:
                    st.warning("Archived dossier binary not located on local disk.")
