"""Workflow nodes for the FRAUDNET AI LangGraph investigation agent.
"""

import os
import re
import logging
from typing import Any, Dict, Optional

from config.settings import GROQ_API_KEY, GROQ_MODEL, GROQ_TEMPERATURE
from src.agents.state import InvestigationState
from src.agents.prompts import (
    SYSTEM_INVESTIGATION_PROMPT,
    build_investigation_prompt,
    build_general_query_prompt,
)
from src.tools.transaction_tools import get_full_transaction_profile
from src.tools.graph_tools import get_transaction_neighborhood

logger = logging.getLogger("fraudnet.agent")


def extract_entities_node(state: InvestigationState) -> Dict[str, Any]:
    """Extract transaction IDs and intent from user query."""
    query = state.get("query", "").strip()
    notes = list(state.get("notes", []))
    target_tx_id = state.get("target_tx_id")

    # If target_tx_id is not already provided, parse query
    if not target_tx_id and query:
        match = re.search(r"\b(\d{4,12})\b", query)
        if match:
            target_tx_id = match.group(1)
            notes.append(f"Parsed target transaction ID from query: {target_tx_id}")
        else:
            notes.append("No explicit transaction ID found in query. Operating in advisory mode.")

    extracted_entities = {"tx_id": target_tx_id}
    return {
        "target_tx_id": target_tx_id,
        "extracted_entities": extracted_entities,
        "notes": notes,
    }


def fetch_profile_node(state: InvestigationState) -> Dict[str, Any]:
    """Retrieve full transaction feature profile."""
    tx_id = state.get("target_tx_id")
    notes = list(state.get("notes", []))

    if not tx_id:
        return {"notes": notes}

    profile = get_full_transaction_profile(int(tx_id))
    if profile is None:
        notes.append(f"Transaction ID {tx_id} not found in the transaction registry.")
        return {
            "transaction_profile": None,
            "error": f"Transaction {tx_id} not found in Elliptic dataset.",
            "notes": notes,
        }

    notes.append(f"Successfully retrieved transaction profile for {tx_id} (Time Step: {profile.get('time_step')}).")
    return {
        "transaction_profile": profile,
        "notes": notes,
    }


def fetch_network_context_node(state: InvestigationState) -> Dict[str, Any]:
    """Extract local graph topology and ego neighborhood."""
    tx_id = state.get("target_tx_id")
    profile = state.get("transaction_profile")
    notes = list(state.get("notes", []))

    if not tx_id or profile is None:
        return {"notes": notes}

    ego = get_transaction_neighborhood(int(tx_id), hops=1, max_nodes=50)
    in_edges = ego.get("predecessors", [])
    out_edges = ego.get("successors", [])
    notes.append(
        f"Extracted 1-hop ego subgraph: {ego.get('total_nodes', len(ego.get('nodes', [])))} nodes, "
        f"{len(in_edges)} incoming inputs, {len(out_edges)} outgoing outputs."
    )
    return {
        "graph_context": ego,
        "notes": notes,
    }


def fetch_prediction_node(state: InvestigationState) -> Dict[str, Any]:
    """Extract supervised ML inference and local feature attribution from profile."""
    tx_id = state.get("target_tx_id")
    profile = state.get("transaction_profile")
    notes = list(state.get("notes", []))

    if not tx_id or profile is None:
        return {"notes": notes}

    ml_assessment = profile.get("ml_assessment", {})
    notes.append(
        f"Assigned ML risk assessment: Predicted {ml_assessment.get('predicted_label')} "
        f"with {ml_assessment.get('illicit_probability', 0.0) * 100:.1f}% illicit probability "
        f"[{ml_assessment.get('risk_category')}]."
    )
    return {
        "ml_prediction": ml_assessment,
        "notes": notes,
    }


def synthesize_forensics_node(state: InvestigationState) -> Dict[str, Any]:
    """Synthesize evidence via Groq LLM or deterministic fallback."""
    query = state.get("query", "")
    tx_id = state.get("target_tx_id")
    profile = state.get("transaction_profile")
    graph_context = state.get("graph_context") or {}
    ml_prediction = state.get("ml_prediction") or {}
    notes = list(state.get("notes", []))

    llm_used = False
    final_report = ""

    # Check for active Groq API key from environment, settings, or Streamlit secrets
    active_key = os.getenv("GROQ_API_KEY", "") or GROQ_API_KEY
    if not active_key:
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                active_key = str(st.secrets["GROQ_API_KEY"])
        except Exception:
            pass

    # Attempt LLM generation if Groq API key is present
    if active_key and active_key.strip():
        try:
            from langchain_groq import ChatGroq
            from langchain_core.messages import HumanMessage, SystemMessage

            llm = ChatGroq(
                groq_api_key=active_key.strip(),
                model_name=GROQ_MODEL,
                temperature=GROQ_TEMPERATURE,
            )

            if tx_id and profile:
                prompt_content = build_investigation_prompt(
                    query=query,
                    tx_id=str(tx_id),
                    profile=profile,
                    graph_context=graph_context,
                    ml_prediction=ml_prediction,
                )
            else:
                prompt_content = build_general_query_prompt(query)

            messages = [
                SystemMessage(content=SYSTEM_INVESTIGATION_PROMPT),
                HumanMessage(content=prompt_content),
            ]

            response = llm.invoke(messages)
            final_report = str(response.content)
            llm_used = True
            notes.append(f"Investigation report generated using Groq LLM ({GROQ_MODEL}).")
        except Exception as exc:
            logger.warning(f"Groq LLM call failed ({exc}); falling back to deterministic synthesizer.")
            notes.append(f"Groq API call unavailable ({exc}). Using deterministic forensic engine.")

    # Deterministic fallback when LLM was not used
    if not llm_used:
        if tx_id and profile:
            prob = ml_prediction.get("illicit_probability", 0.0)
            risk_cat = ml_prediction.get("risk_category", "Unknown")
            pred_class = ml_prediction.get("predicted_label", "Unknown")
            gt_label = profile.get("ground_truth_label", "unknown")
            metrics = profile.get("graph_metrics", {})
            in_deg = metrics.get("in_degree", 0)
            out_deg = metrics.get("out_degree", 0)
            pagerank = metrics.get("pagerank", 0.0)
            comm_id = metrics.get("community_id", -1)
            time_step = profile.get("time_step", "N/A")
            explain = profile.get("explainability", {})
            top_elevating = explain.get("top_risk_elevating", [])
            top_mitigating = explain.get("top_risk_mitigating", [])

            # Typology classification
            if in_deg >= 5 and out_deg <= 1:
                typology = "High Fan-In Aggregation (Layering / Dark Market consolidation)"
            elif out_deg >= 5 and in_deg <= 1:
                typology = "High Fan-Out Distribution (Dispersal / Peeling Chain)"
            elif in_deg == 1 and out_deg == 1:
                typology = "Linear Pass-Through Relay (Intermediate Layering)"
            else:
                typology = "Standard Mesh Flow / Arbitrage"

            feat_bullets = ""
            for f in top_elevating[:4]:
                feat_bullets += f"- **[ELEVATING] {f.get('feature')}**: value={f.get('value')}, z-score={f.get('z_score', 0):+.2f} ({f.get('reason', '')})\n"
            for f in top_mitigating[:2]:
                feat_bullets += f"- **[MITIGATING] {f.get('feature')}**: value={f.get('value')}, z-score={f.get('z_score', 0):+.2f} ({f.get('reason', '')})\n"

            predecessors = graph_context.get("predecessors", [])
            successors = graph_context.get("successors", [])

            final_report = f"""# Forensic Investigation Dossier: Transaction `{tx_id}`

> **Generated by FRAUDNET AI Automated Forensic Engine (Deterministic Fallback)**

---

## 1. Executive Summary & Risk Rating
- **Target Transaction:** `{tx_id}`
- **Time Step:** `{time_step}` (Temporal Partition)
- **Ground Truth Classification:** `{gt_label.upper()}`
- **Supervised ML Assessment:** `{str(pred_class).upper()}` (Illicit Probability: **{prob * 100:.2f}%**)
- **Assigned Risk Tier:** **{risk_cat.upper()}**

**Forensic Evaluation:**
Transaction `{tx_id}` exhibits an illicit probability score of **{prob:.4f}**, placing it in the **{risk_cat}** risk band. In the historical record, its verified ground-truth label is `{gt_label}`.

---

## 2. Network Topology & Cash Flow Dynamics
- **In-Degree (Incoming Inputs):** `{in_deg}`
- **Out-Degree (Outgoing Outputs):** `{out_deg}`
- **Total Degree Connectivity:** `{in_deg + out_deg}`
- **PageRank Centrality Score:** `{pagerank:.8f}`
- **Louvain Community Cluster:** `Community #{comm_id}`
- **Direct Upstream Predecessors:** `{len(predecessors)}`
- **Direct Downstream Successors:** `{len(successors)}`

**Topology Interpretation:**
The transaction acts as a node within Community #{comm_id}. With {in_deg} input streams and {out_deg} output paths, the structural pattern aligns with `{typology}`.

---

## 3. Machine Learning Attribution & Feature Anomalies
The Random Forest supervised fraud detection ensemble identified the following primary feature drivers deviating from the licit baseline:

{feat_bullets if feat_bullets else "- No significant local feature anomalies detected."}

---

## 4. AML Typology & Behavior Identification
- **Identified Typology:** {typology}
- **Structural Anomaly Status:** {"Identified Hub Node" if (metrics.get('is_aggregation_hub') or metrics.get('is_distribution_hub')) else "Standard Node"}
- **Ego Subgraph Horizon:** {len(graph_context.get('nodes', []))} related addresses within 1-hop neighborhood.

---

## 5. Actionable Recommendations for Compliance
1. **Immediate Action:** {"Flag address for enhanced SAR filing and freeze counterparty hops." if risk_cat in ("Critical", "High") else "Maintain on standard automated monitoring register."}
2. **Upstream Investigation:** Audit source transactions {predecessors[:3]} for mixing service or darknet origin.
3. **Downstream Trace:** Verify destination nodes {successors[:3]} against known exchange deposit addresses.
4. **Audit Trail:** Log this forensic assessment with case ID and compliance officer timestamp.
"""
        else:
            final_report = f"""# FRAUDNET AI Forensic Intelligence Assistant

Welcome to the FRAUDNET AI Cryptocurrency Forensic Investigation Platform.

### How to use this assistant:
- **Transaction Lookup:** Enter any Bitcoin transaction ID from the Elliptic dataset (e.g., `230425980`, `232438397`, `232532458`).
- **Graph Topology:** Ask about incoming and outgoing cash flows, PageRank centrality, and Louvain community clusters.
- **ML Fraud Attribution:** View model-predicted illicit probability and local feature anomaly drivers.
- **Case Management:** Create cases and attach suspicious transactions for compliance reporting.

To investigate a transaction immediately, enter:
`Investigate transaction 230425980`
"""

    return {
        "final_report": final_report,
        "llm_used": llm_used,
        "notes": notes,
    }
