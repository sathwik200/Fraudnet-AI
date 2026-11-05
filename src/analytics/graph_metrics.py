#!/usr/bin/env python3
"""
FRAUDNET AI — Graph Metrics Engine
===================================
Calculates transaction-level topological and flow indicators:
  - In-degree, Out-degree, Total degree
  - Degree centrality (in/out)
  - PageRank (directed random walk flow)
  - Weakly Connected Component ID and Component Size
  - Local clustering coefficient (on undirected projection)
"""

import time
from typing import Dict, Optional, Tuple
import networkx as nx
import pandas as pd
import numpy as np


def compute_degree_metrics(graph: nx.DiGraph) -> pd.DataFrame:
    """
    Compute in-degree, out-degree, and total degree for all nodes.

    Returns:
        pd.DataFrame with index txId and columns [in_degree, out_degree, total_degree]
    """
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())

    nodes = list(graph.nodes())
    df = pd.DataFrame(
        {
            "in_degree": [in_degrees[n] for n in nodes],
            "out_degree": [out_degrees[n] for n in nodes],
        },
        index=nodes,
    )
    df["total_degree"] = df["in_degree"] + df["out_degree"]
    df.index.name = "txId"
    return df


def compute_pagerank(
    graph: nx.DiGraph,
    alpha: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[int, float]:
    """
    Compute directed PageRank values across transactions.

    In the context of Bitcoin transaction graphs, PageRank models the flow
    of transaction value/attention across payment hops.
    """
    return nx.pagerank(graph, alpha=alpha, max_iter=max_iter, tol=tol)


def compute_wcc_membership(graph: nx.DiGraph) -> pd.DataFrame:
    """
    Assign each node to its Weakly Connected Component and compute component size.

    Returns:
        pd.DataFrame with index txId and columns [wcc_id, wcc_size]
    """
    wcc_map = {}
    size_map = {}

    wccs = list(nx.weakly_connected_components(graph))
    for comp_idx, comp_nodes in enumerate(wccs):
        comp_size = len(comp_nodes)
        for node in comp_nodes:
            wcc_map[node] = comp_idx
            size_map[node] = comp_size

    nodes = list(graph.nodes())
    df = pd.DataFrame(
        {
            "wcc_id": [wcc_map[n] for n in nodes],
            "wcc_size": [size_map[n] for n in nodes],
        },
        index=nodes,
    )
    df.index.name = "txId"
    return df


def compute_clustering_coefficients(graph: nx.DiGraph) -> Dict[int, float]:
    """
    Compute local clustering coefficients on the undirected projection.
    Reflects the degree to which a transaction's neighbours are connected.
    """
    G_undirected = graph.to_undirected(as_view=True)
    return nx.clustering(G_undirected)


def compute_all_transaction_metrics(
    graph: nx.DiGraph,
    verbose: bool = True,
) -> pd.DataFrame:
    """
    Compute a consolidated DataFrame containing all primary graph metrics.

    Columns produced:
      - txId (index)
      - in_degree (int)
      - out_degree (int)
      - total_degree (int)
      - pagerank (float64)
      - in_degree_centrality (float64)
      - out_degree_centrality (float64)
      - wcc_id (int)
      - wcc_size (int)
      - clustering_coeff (float64)
    """
    t0 = time.time()
    n_nodes = graph.number_of_nodes()

    if verbose:
        print(f"Computing degree metrics for {n_nodes:,} nodes...")
    deg_df = compute_degree_metrics(graph)

    # Degree centrality (normalized by N - 1)
    norm = max(n_nodes - 1, 1)
    deg_df["in_degree_centrality"] = deg_df["in_degree"] / norm
    deg_df["out_degree_centrality"] = deg_df["out_degree"] / norm

    if verbose:
        print("Computing PageRank...")
    pr_dict = compute_pagerank(graph)
    deg_df["pagerank"] = [pr_dict[n] for n in deg_df.index]

    if verbose:
        print("Computing WCC membership and component sizes...")
    wcc_df = compute_wcc_membership(graph)
    deg_df["wcc_id"] = wcc_df["wcc_id"]
    deg_df["wcc_size"] = wcc_df["wcc_size"]

    if verbose:
        print("Computing local clustering coefficients...")
    clust_dict = compute_clustering_coefficients(graph)
    deg_df["clustering_coeff"] = [clust_dict[n] for n in deg_df.index]

    if verbose:
        print(f"All transaction metrics computed in {time.time()-t0:.2f}s")

    return deg_df

