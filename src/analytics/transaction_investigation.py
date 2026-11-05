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


def compile_investigation_dossier(tx_id: int) -> Dict[str, any]:
    """
    Generate an end-to-end forensic dossier for a given transaction ID.

    Combines:
      - Core transaction profile and ground truth
      - Machine learning fraud probability and category
      - Local topological graph metrics (in/out-degree, PageRank, community)
      - Bounded 1-hop and 2-hop neighborhood structure
      - Top risk-elevating and risk-mitigating feature drivers
      - Forensic summary narrative and evidence limitations

    Raises:
        KeyError: If transaction ID does not exist in dataset.
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

    narrative_points = [
        f"Transaction {tx_id} was assigned a fraud risk score of {prob_pct:.1f}% ({risk_level} Risk Category).",
        f"Temporal slice: Time Step {profile['time_step']} (belongs to Community {metrics['community_id']}, WCC size {metrics['wcc_size']:,} transactions).",
        f"Payment topology: {in_deg} incoming inputs and {out_deg} outgoing outputs.",
    ]

    if metrics["is_aggregation_hub"]:
        narrative_points.append("Topological Role: Identified as an Aggregation Hub (unusually high fan-in concentration).")
    if metrics["is_distribution_hub"]:
        narrative_points.append("Topological Role: Identified as a Distribution Hub (unusually high fan-out disbursement).")

    if profile["ground_truth_label"] != "unknown":
        label_text = "Illicit (Class 1)" if profile["ground_truth_label"] == "1" else "Licit (Class 2)"
        narrative_points.append(f"Ground-Truth Dataset Label: Verified as {label_text} in original Elliptic labels.")
    else:
        narrative_points.append("Ground-Truth Dataset Label: Unlabeled in original dataset (classified purely by ML inference).")

    return {
        "txId": tx_id,
        "time_step": profile["time_step"],
        "ground_truth_label": profile["ground_truth_label"],
        "risk_assessment": ml,
        "graph_metrics": metrics,
        "neighborhood": neighborhood,
        "explainability": explain,
        "executive_summary": " ".join(narrative_points),
        "disclaimer": (
            "FRAUDNET AI assessments are algorithmic risk indicators designed for forensic investigation. "
            "They do not constitute automated legal proof of fraud."
        ),
    }

