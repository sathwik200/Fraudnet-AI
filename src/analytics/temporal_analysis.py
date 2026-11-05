#!/usr/bin/env python3
"""
FRAUDNET AI — Temporal Network Analysis Engine
===============================================
Computes historical evolution and trends across the 49 two-week time steps:
  - Node counts and class balance (illicit, licit, unknown) over time
  - Edge density and graph volume per time step
  - Mean/Max in-degree and out-degree evolution
  - Illicit transaction concentration across chronological periods
"""

from collections import Counter
from typing import Dict, List, Optional
import networkx as nx
import pandas as pd


def compute_temporal_summary(
    graph: nx.DiGraph,
    metrics_df: Optional[pd.DataFrame] = None,
) -> Dict[str, any]:
    """
    Generate comprehensive time-series metrics across all 49 time steps.

    Returns:
        Dict mapping time step strings to detailed topological and class metrics.
    """
    # Group nodes by time step
    ts_nodes = {}
    for node, attrs in graph.nodes(data=True):
        ts = attrs.get("time_step", 1)
        ts_nodes.setdefault(ts, []).append(node)

    timeline = []
    for ts in sorted(ts_nodes.keys()):
        nodes = ts_nodes[ts]
        subgraph = graph.subgraph(nodes)

        # Class counts
        labels = [str(graph.nodes[n].get("label", "unknown")) for n in nodes]
        l_counts = Counter(labels)

        # In/out degrees in this time step
        in_degs = [d for _, d in subgraph.in_degree()]
        out_degs = [d for _, d in subgraph.out_degree()]

        illicit_cnt = l_counts.get("1", 0)
        licit_cnt = l_counts.get("2", 0)
        unknown_cnt = l_counts.get("unknown", 0)
        total_cnt = len(nodes)
        labeled_cnt = illicit_cnt + licit_cnt
        illicit_ratio_labeled = (illicit_cnt / labeled_cnt) if labeled_cnt > 0 else 0.0

        timeline.append({
            "time_step": int(ts),
            "total_transactions": total_cnt,
            "total_edges": subgraph.number_of_edges(),
            "illicit_count": illicit_cnt,
            "licit_count": licit_cnt,
            "unknown_count": unknown_cnt,
            "labeled_count": labeled_cnt,
            "illicit_ratio_of_labeled": round(illicit_ratio_labeled, 4),
            "max_in_degree": max(in_degs) if in_degs else 0,
            "max_out_degree": max(out_degs) if out_degs else 0,
            "avg_in_degree": round(sum(in_degs) / total_cnt, 4) if total_cnt else 0,
        })

    summary = {
        "num_time_steps": len(timeline),
        "timeline": timeline,
        "peak_transaction_timestep": max(timeline, key=lambda x: x["total_transactions"])["time_step"],
        "peak_illicit_timestep": max(timeline, key=lambda x: x["illicit_count"])["time_step"],
    }

    return summary

