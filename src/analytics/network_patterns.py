#!/usr/bin/env python3
"""
FRAUDNET AI — Network Pattern Analysis Engine
==============================================
Identifies structural payment topologies in the Bitcoin transaction DAG:
  - Aggregation Hubs (High fan-in: multiple inputs converging into one transaction)
  - Distribution Hubs (High fan-out: single transaction splitting into multiple outputs)
  - Peel Chains & Relay Nodes (Linear flow passing through a transaction)
  - Dense Local Clusters (High clustering coefficient sub-topologies)

FORENSIC NOTICE:
  Topological patterns (such as high fan-in or fan-out) represent structural
  mechanisms of the Bitcoin protocol (e.g. mining pool payouts, exchange batching,
  hot-wallet consolidations). They are forensic investigative signals, not
  conclusive evidence of unlawful activity.
"""

from typing import Dict, List, Optional
import networkx as nx
import pandas as pd
import numpy as np


def detect_structural_patterns(
    metrics_df: pd.DataFrame,
    in_degree_percentile: float = 99.0,
    out_degree_percentile: float = 99.0,
) -> Dict[str, any]:
    """
    Detect structural roles and payment flow topologies based on transaction metrics.

    Args:
        metrics_df: DataFrame containing at least ['in_degree', 'out_degree', 'total_degree', 'pagerank']
        in_degree_percentile: Threshold percentile for aggregation hubs
        out_degree_percentile: Threshold percentile for distribution hubs

    Returns:
        Dict containing classified node IDs and pattern summaries.
    """
    in_thresh = np.percentile(metrics_df["in_degree"], in_degree_percentile)
    out_thresh = np.percentile(metrics_df["out_degree"], out_degree_percentile)

    # Ensure reasonable minimum thresholds
    in_thresh = max(in_thresh, 5.0)
    out_thresh = max(out_thresh, 5.0)

    # High fan-in: convergence points
    fan_in_mask = metrics_df["in_degree"] >= in_thresh
    fan_in_nodes = metrics_df[fan_in_mask].index.tolist()

    # High fan-out: distribution points
    fan_out_mask = metrics_df["out_degree"] >= out_thresh
    fan_out_nodes = metrics_df[fan_out_mask].index.tolist()

    # Dual hubs: both high in and out (relays / mixers / exchanges)
    dual_hub_mask = fan_in_mask & fan_out_mask
    dual_hub_nodes = metrics_df[dual_hub_mask].index.tolist()

    # Linear chains: in_degree == 1 and out_degree == 1 (pass-through / peel chain links)
    pass_through_mask = (metrics_df["in_degree"] == 1) & (metrics_df["out_degree"] == 1)
    pass_through_count = int(pass_through_mask.sum())

    summary = {
        "thresholds": {
            "aggregation_in_degree_threshold": float(in_thresh),
            "distribution_out_degree_threshold": float(out_thresh),
        },
        "counts": {
            "aggregation_hubs_count": len(fan_in_nodes),
            "distribution_hubs_count": len(fan_out_nodes),
            "dual_hubs_count": len(dual_hub_nodes),
            "linear_pass_through_count": pass_through_count,
        },
        "top_aggregation_hubs": metrics_df.loc[fan_in_nodes]
        .sort_values(by="in_degree", ascending=False)
        .head(10)[["in_degree", "out_degree", "pagerank"]]
        .to_dict(orient="index"),
        "top_distribution_hubs": metrics_df.loc[fan_out_nodes]
        .sort_values(by="out_degree", ascending=False)
        .head(10)[["in_degree", "out_degree", "pagerank"]]
        .to_dict(orient="index"),
        "forensic_guidance": (
            "Aggregation and distribution points are structural characteristics of payment networks "
            "(e.g., exchange sweeps, mining pool distributions, payment processors). "
            "They indicate transaction volume concentration, not confirmed illicit behavior."
        ),
    }

    return summary

