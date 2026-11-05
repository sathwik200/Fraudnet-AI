#!/usr/bin/env python3
"""
FRAUDNET AI — Centrality Analysis Engine
=========================================
Computes transaction centrality metrics and top-k rankings:
  - Degree centrality (in-degree, out-degree, total)
  - PageRank distribution and hub rankings
  - Approximate betweenness centrality for selected subgraphs/ego networks
"""

import time
from typing import Dict, List, Optional, Tuple
import networkx as nx
import pandas as pd


def get_top_k_transactions_by_metric(
    metrics_df: pd.DataFrame,
    metric_name: str,
    k: int = 20,
    ascending: bool = False,
) -> pd.DataFrame:
    """
    Retrieve top-k transactions ranked by a specific graph metric.
    """
    if metric_name not in metrics_df.columns:
        raise ValueError(f"Metric '{metric_name}' not found in metrics DataFrame.")
    return metrics_df.sort_values(by=metric_name, ascending=ascending).head(k)


def compute_ego_betweenness(
    graph: nx.DiGraph,
    center_node: int,
    radius: int = 1,
) -> Dict[int, float]:
    """
    Compute exact betweenness centrality on the local ego subgraph around a node.

    Computational Note:
      All-pairs betweenness on the full 203,769-node graph has O(V*E) complexity,
      which would require multiple hours of compute. Computing betweenness on the
      bounded ego subgraph provides accurate local bridging scores in < 0.05 seconds.
    """
    ego_nodes = nx.ego_graph(graph, center_node, radius=radius, undirected=True)
    return nx.betweenness_centrality(ego_nodes, normalized=True)


def compute_approximate_betweenness_for_candidates(
    graph: nx.DiGraph,
    candidate_nodes: List[int],
    k_samples: int = 100,
    seed: int = 42,
) -> Dict[int, float]:
    """
    Compute sampled betweenness centrality using k random pivots.
    """
    sub_nodes = set(candidate_nodes)
    # Use NetworkX sampled betweenness
    bc = nx.betweenness_centrality(graph, k=min(k_samples, graph.number_of_nodes()), seed=seed)
    return {n: bc.get(n, 0.0) for n in candidate_nodes}

