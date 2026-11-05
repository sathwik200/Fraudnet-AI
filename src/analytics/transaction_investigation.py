#!/usr/bin/env python3
"""
FRAUDNET AI — Transaction Investigation Engine
================================================
Synthesizes graph analytics, machine learning predictions, and feature attributions
into an integrated forensic investigation dossier for any queried transaction.
"""

from typing import Dict, Optional
from src.tools.graph_tools import get_transaction_neighborhood
from src.tools.transaction_tools import get_full_transaction_profile
from src.analytics.typology import classify_aml_typology


def compile_investigation_dossier(tx_id: int) -> Dict[str, any]:
    """
    Generate an end-to-end forensic dossier for a given transaction ID.

    Combines:
      - Core transaction profile and ground truth
      - Machine learning fraud probability and category
      - Local topological graph metrics (in/out-degree, PageRank, community)
      - Bounded 1-hop neighborhood structure
      - Evidence-based AML typology classification
      - Top risk-elevating and risk-mitigating feature drivers
      - Forensic summary narrative, responsible compliance guidance, and evidence limitations
    """
    tx_id = int(tx_id)
    profile = get_full_transaction_profile(tx_id)
    if profile is None:
        raise KeyError(f"Transaction ID {tx_id} not found in the Elliptic dataset.")

    neighborhood = get_transaction_neighborhood(tx_id, hops=1, max_nodes=30)

    ml = profile["ml_assessment"]
    metrics = profile["graph_metrics"]
    explain = profile["explainability"]

    # Synthesize plain-English findings
    risk_level = ml["risk_category"]
    prob_pct = ml["illicit_probability"] * 100
    in_deg = metrics["in_degree"]
    out_deg = metrics["out_degree"]

    # Evidence-based AML typology evaluation
    typology_info = classify_aml_typology(
        in_degree=in_deg,
        out_degree=out_deg,
        is_aggregation_hub=metrics.get("is_aggregation_hub", False),
        is_distribution_hub=metrics.get("is_distribution_hub", False),
        clustering_coeff=metrics.get("clustering_coeff", 0.0),
    )

    narrative_points = [
        f"Transaction {tx_id} was assigned a fraud risk score of {prob_pct:.1f}% ({risk_level} Risk Category).",
        f"Temporal slice: Time Step {profile['time_step']} (belongs to Community {metrics['community_id']}, WCC size {metrics['wcc_size']:,} transactions).",
        f"Payment topology: {in_deg} incoming inputs and {out_deg} outgoing outputs.",
        f"Topological Typology: {typology_info['typology']}. {typology_info['supporting_observations']}",
    ]

    if profile["ground_truth_label"] != "unknown":
        label_text = "Illicit (Class 1)" if profile["ground_truth_label"] == "1" else "Licit (Class 2)"
        narrative_points.append(f"Ground-Truth Dataset Label: Verified as {label_text} in historical Elliptic research labels.")
    else:
        narrative_points.append("Ground-Truth Dataset Label: Unlabeled in original dataset (classified purely by ML inference).")

    return {
        "txId": tx_id,
        "time_step": profile["time_step"],
        "ground_truth_label": profile["ground_truth_label"],
        "risk_assessment": ml,
        "graph_metrics": metrics,
        "global_graph_metrics": {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": metrics.get("total_degree", in_deg + out_deg),
            "direct_predecessors_count": in_deg,
            "direct_successors_count": out_deg,
            "pagerank": metrics.get("pagerank", 0.0),
            "community_id": metrics.get("community_id", 0),
            "wcc_size": metrics.get("wcc_size", 0),
        },
        "bounded_subgraph_metrics": {
            "rendered_nodes": len(neighborhood.get("nodes", [])),
            "rendered_edges": len(neighborhood.get("edges", [])),
            "hops_explored": neighborhood.get("hops", 1),
            "direct_predecessors_count": neighborhood.get("direct_predecessors_count", in_deg),
            "direct_successors_count": neighborhood.get("direct_successors_count", out_deg),
        },
        "typology_assessment": typology_info,
        "neighborhood": neighborhood,
        "explainability": explain,
        "execution_mode": "Deterministic Rule-Based Forensic Engine",
        "llm_used": False,
        "compliance_recommendations": [
            "Human Review Required: Algorithmic risk scores and research labels serve as exploratory leads and must not trigger automated asset freezes or filings.",
            "Enhanced Due Diligence (EDD): For high/critical risk transactions, initiate independent manual verification of counterparties across block explorers and licensed VASPs.",
            "Corroboration: Ground-truth classifications reflect historical academic research datasets (Elliptic) and do not independently establish unlawful conduct.",
        ],
        "executive_summary": " ".join(narrative_points),
        "disclaimer": (
            "ACADEMIC & FORENSIC DISCLAIMER: FRAUDNET AI assessments represent statistical "
            "and topological risk estimations derived from the Elliptic Bitcoin dataset. "
            "High fan-in or high risk scores do not constitute automated legal proof of fraud. "
            "All investigative findings must be corroborated with blockchain ledger data and human expertise."
        ),
    }

