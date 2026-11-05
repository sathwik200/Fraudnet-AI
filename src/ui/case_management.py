"""Case Management & Intelligence Operations for FRAUDNET AI.
============================================================
SQLite-backed AML case registry, suspect transaction evidence logs,
and chronological compliance investigator audit trails.
"""

from typing import Optional
import streamlit as st
import pandas as pd

from src.database.case_repository import CaseRepository
from src.tools.transaction_tools import get_full_transaction_profile
from src.ui.theme import CYAN, RED, GREEN, BLUE, AMBER, PURPLE
from src.ui.components import (
    render_command_header,
    render_cyber_metric,
)


def render_case_management_page():
    """Render the Cyberpunk Case Management Operations interface."""
    render_command_header("AML CASE MANAGEMENT // INTELLIGENCE OPERATIONS")

    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; color:#8892B0; margin-bottom:14px;">
            // PERMANENT SQLITE INCIDENT REGISTRY & SUSPECT EVIDENCE LEDGER
        </div>
        """,
        unsafe_allow_html=True,
    )

    repo = CaseRepository()

    t_reg, t_create, t_audit = st.tabs(
        ["📋 CASE REGISTRY VAULT", "➕ INITIALIZE NEW CASE", "🔍 EVIDENCE AUDIT & LOGS"]
    )

    # -------------------------------------------------------------------------
    # TAB 1: CASE REGISTRY VAULT
    # -------------------------------------------------------------------------
    with t_reg:
        cases = repo.list_cases()
        if not cases:
            st.info("NO ACTIVE FORENSIC CASES IN DATABASE. INITIALIZE A NEW CASE TO BEGIN TRACKING EVIDENCE.")
        else:
            case_data = []
            for c in cases:
                txs = repo.get_case_transactions(c["id"])
                case_data.append({
                    "Case ID": f"CASE-{c['id']:04d}",
                    "Incident Title": c["title"],
                    "Status": c["status"],
                    "Priority Tier": c["priority"],
                    "Attached Evidence": f"{len(txs)} Transactions",
                    "Last Updated": c["updated_at"][:19],
                    "raw_id": c["id"],
                })

            df_cases = pd.DataFrame(case_data)
            st.dataframe(df_cases.drop(columns=["raw_id"]), use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # TAB 2: INITIALIZE NEW CASE
    # -------------------------------------------------------------------------
    with t_create:
        st.markdown(
            """
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:8px;">
                // OPEN NEW COMPLIANCE INVESTIGATION FILE
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("create_cyber_case_form"):
            c_title = st.text_input("Incident Designation / Case Title:", placeholder="e.g., Mixing Pool Layering Ring Step 21")
            c1, c2 = st.columns(2)
            with c1:
                c_priority = st.selectbox("Threat Priority Tier:", ["Critical", "High", "Medium", "Low"], index=1)
            with c2:
                c_investigator = st.text_input("Lead Investigating Officer:", value="Sathwik M (Senior Intelligence Analyst)")
            c_desc = st.text_area("Forensic Hypothesis & Investigative Scope:", placeholder="Document suspected dark market consolidation or structured fan-out flows...")

            submitted = st.form_submit_button("🚀 INITIALIZE INCIDENT CASE")
            if submitted:
                if not c_title.strip():
                    st.error("INCIDENT DESIGNATION TITLE CANNOT BE EMPTY.")
                else:
                    new_id = repo.create_case(
                        title=c_title.strip(),
                        description=c_desc.strip(),
                        priority=c_priority,
                    )
                    repo.add_note(new_id, f"Case opened by {c_investigator.strip()}.", author=c_investigator.strip())
                    st.success(f"CASE-{new_id:04d} INITIALIZED SUCCESSFULLY IN SQLITE DATABASE.")
                    st.rerun()

    # -------------------------------------------------------------------------
    # TAB 3: EVIDENCE AUDIT & LOGS
    # -------------------------------------------------------------------------
    with t_audit:
        cases = repo.list_cases()
        if not cases:
            st.info("NO CASES REGISTERED YET.")
            return

        case_options = {f"CASE-{c['id']:04d} — {c['title']} [{c['status']}]": c["id"] for c in cases}
        selected_case_label = st.selectbox("Select Target Case File:", list(case_options.keys()))
        selected_case_id = case_options[selected_case_label]
        case_obj = repo.get_case(selected_case_id)

        if case_obj:
            # Case Header Card
            status_color = "#00FF9C" if case_obj["status"] == "Closed" else ("#FF3158" if case_obj["priority"] == "Critical" else "#00F5FF")

            st.markdown(
                f"""
                <div class="cyber-card" style="border-left: 3px solid {status_color}; margin-bottom:16px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-family:'JetBrains Mono',monospace; font-size:0.75rem; color:#8892B0;">INCIDENT DOSSIER</span>
                            <div style="font-family:'Chakra Petch',sans-serif; font-size:1.5rem; font-weight:700; color:#FFFFFF;">
                                CASE-{case_obj['id']:04d}: {case_obj['title']}
                            </div>
                        </div>
                        <div class="cyber-status-pill pill-cyan">
                            <span>{case_obj['priority']} PRIORITY</span>
                        </div>
                    </div>
                    <div style="font-family:'Rajdhani',sans-serif; font-size:0.95rem; color:#8892B0; margin-top:6px;">
                        {case_obj['description'] or 'No investigative hypothesis documented.'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Status Updater and Danger Zone
            c_stat, c_del = st.columns([2, 1])
            with c_stat:
                current_statuses = ["Open", "In Progress", "Under Review", "Closed"]
                idx_status = current_statuses.index(case_obj["status"]) if case_obj["status"] in current_statuses else 0
                new_status = st.selectbox("Update Incident Status:", current_statuses, index=idx_status)
                if new_status != case_obj["status"]:
                    repo.update_case(case_obj["id"], status=new_status)
                    st.success(f"Status updated to {new_status}.")
                    st.rerun()

            with c_del:
                st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ DELETE CASE FILE", use_container_width=True):
                    repo.delete_case(case_obj["id"])
                    st.success("Case file and linked evidence purged.")
                    st.rerun()

            st.markdown("---")

            # Attached Transactions Evidence
            st.markdown(
                """
                <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#00F5FF; letter-spacing:1px; margin-bottom:6px;">
                    // ATTACHED TRANSACTION EVIDENCE
                </div>
                """,
                unsafe_allow_html=True,
            )

            attached_txs = repo.get_case_transactions(case_obj["id"])
            if attached_txs:
                tx_rows = []
                for t in attached_txs:
                    tx_rows.append({
                        "Transaction ID": f"tx_{t['tx_id']}",
                        "Assigned Risk Tier": t["risk_category"],
                        "Illicit Score": f"{t['risk_score'] * 100:.1f}%",
                        "Investigator Notes": t["notes"] or "Direct evidence link",
                        "Attached At": t["added_at"][:19],
                        "raw_tx": t["tx_id"],
                    })
                df_txs = pd.DataFrame(tx_rows)
                st.dataframe(df_txs.drop(columns=["raw_tx"]), use_container_width=True, hide_index=True)

                # Detach transaction action
                with st.expander("🗑️ DETACH TRANSACTION FROM CASE FILE"):
                    tx_to_remove = st.selectbox("Select Transaction to Detach:", [t["tx_id"] for t in attached_txs])
                    if st.button("CONFIRM DETACH"):
                        repo.remove_transaction_from_case(case_obj["id"], tx_to_remove)
                        st.success(f"Transaction tx_{tx_to_remove} detached.")
                        st.rerun()
            else:
                st.caption("No cryptocurrency transactions attached to this incident file yet.")

            # Quick Attach Transaction Form
            with st.expander("➕ ATTACH TRANSACTION IDENTIFIER"):
                c_tid, c_tnote = st.columns([1, 2])
                with c_tid:
                    add_tx = st.text_input("Target txId:")
                with c_tnote:
                    add_note_text = st.text_input("Evidence Annotation:", value="Identified in layering chain")
                if st.button("ATTACH TO DOSSIER"):
                    if add_tx.strip().isdigit():
                        tid = int(add_tx.strip())
                        prof = get_full_transaction_profile(tid)
                        if prof:
                            ml = prof["ml_assessment"]
                            repo.add_transaction_to_case(
                                case_id=case_obj["id"],
                                tx_id=tid,
                                risk_score=ml["illicit_probability"],
                                risk_category=ml["risk_category"],
                                notes=add_note_text.strip(),
                            )
                            st.success(f"Transaction tx_{tid} linked.")
                            st.rerun()
                        else:
                            st.error(f"Transaction tx_{tid} not found in Elliptic dataset.")
                    else:
                        st.warning("Please specify a valid numeric transaction ID.")

            # Chronological Investigator Notes
            st.markdown("---")
            st.markdown(
                """
                <div style="font-family:'Rajdhani',sans-serif; font-size:1.15rem; font-weight:700; color:#FFB547; letter-spacing:1px; margin-bottom:6px;">
                    // CHRONOLOGICAL INVESTIGATOR LOGS
                </div>
                """,
                unsafe_allow_html=True,
            )

            notes = repo.get_case_notes(case_obj["id"])
            if notes:
                for n in notes:
                    st.markdown(
                        f"""
                        <div class="cyber-terminal-box" style="margin-bottom:8px;">
                            <span class="cyber-terminal-prompt">[{n['author'].upper()} // {n['created_at'][:19]}]</span>
                            {n['note_text']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.caption("No log entries recorded yet.")

            with st.form("add_case_log_form"):
                new_note_content = st.text_area("Append Investigation Note / Subpoena Record:")
                note_author_name = st.text_input("Officer Signature:", value="Sathwik M")
                if st.form_submit_button("POST NOTE"):
                    if new_note_content.strip():
                        repo.add_note(case_obj["id"], new_note_content.strip(), author=note_author_name.strip())
                        st.success("Note logged.")
                        st.rerun()
