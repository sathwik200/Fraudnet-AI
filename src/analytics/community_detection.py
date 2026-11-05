#!/usr/bin/env python3
"""
FRAUDNET AI — Community Detection Engine
=========================================
Implements graph clustering and community detection for Bitcoin transactions.

Methodology:
  Bitcoin transaction networks are Directed Acyclic Graphs (DAGs). Standard
  modularity optimization (e.g. Louvain) operates on an undirected projection
  view of the graph to cluster densely interconnected transaction groups
  (e.g., related wallets, peel chains, payment clusters).

  Directionality is strictly preserved in the underlying networkx.DiGraph artifact.
"""

import time
from collections import Counter
from typing import Dict, List, Tuple
import networkx as nx
import pandas as pd


def detect_communities_louvain(
    graph: nx.DiGraph,
    seed: int = 42,
    resolution: float = 1.0,
    verbose: bool = True,
) -> Tuple[Dict[int, int], List[Dict]]:
    """
    Detect transaction communities using Louvain modularity optimization
    on the undirected projection view of the graph.

    Args:
        graph: Authoritative networkx.DiGraph
        seed: Random seed for reproducibility
        resolution: Louvain resolution parameter
        verbose: Log timing and metrics

    Returns:
        (node_to_community_dict, community_summary_list)
    """
    t0 = time.time()
    if verbose:
        print(f"Projecting {graph.number_of_nodes():,} nodes to undirected view for community detection...")
    
    # Create lightweight undirected view (no edge copying)
    G_undirected = graph.to_undirected(as_view=True)

    if verbose:
        print("Running Louvain community detection...")
    communities = nx.community.louvain_communities(
        G_undirected,
        seed=seed,
        resolution=resolution,
    )

    elapsed = time.time() - t0
    num_communities = len(communities)
    if verbose:
        print(f"Discovered {num_communities:,} communities in {elapsed:.2f}s")

    # Map each node to its community ID (ranked by size descending)
    sorted_communities = sorted(communities, key=len, reverse=True)
    node_to_community = {}
    community_summaries = []

    for comm_id, members in enumerate(sorted_communities):
        size = len(members)
        for n in members:
            node_to_community[n] = comm_id

        # Class breakdown inside community
        labels = [str(graph.nodes[n].get("label", "unknown")) for n in members]
        label_counts = Counter(labels)
        time_steps = [graph.nodes[n].get("time_step") for n in members if "time_step" in graph.nodes[n]]
        ts_min = min(time_steps) if time_steps else None
        ts_max = max(time_steps) if time_steps else None

        community_summaries.append({
            "community_id": comm_id,
            "size": size,
            "min_time_step": ts_min,
            "max_time_step": ts_max,
            "illicit_count": label_counts.get("1", 0),
            "licit_count": label_counts.get("2", 0),
            "unknown_count": label_counts.get("unknown", 0),
        })

    return node_to_community, community_summaries

