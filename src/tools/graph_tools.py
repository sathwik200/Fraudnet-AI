#!/usr/bin/env python3
"""
FRAUDNET AI — Graph Exploration Tools
======================================
Tools for bounded topological queries around transactions:
  - 1-hop and 2-hop directed ego neighborhoods
  - Predecessor (input) and Successor (output) exploration
  - Directed payment path tracing
  - Plotly-ready graph visualization payload generator
"""

from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import networkx as nx

from src.graph.build_graph import load_graph

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GRAPH_PATH = PROJECT_ROOT / "data" / "processed" / "transaction_graph.pkl"

_CACHED_GRAPH: Optional[nx.DiGraph] = None


def get_graph_instance() -> nx.DiGraph:
    """Retrieve shared in-memory graph instance."""
    global _CACHED_GRAPH
    if _CACHED_GRAPH is None:
        _CACHED_GRAPH = load_graph(GRAPH_PATH, verbose=False)
    return _CACHED_GRAPH


def get_transaction_neighborhood(
    tx_id: int,
    hops: int = 1,
    max_nodes: int = 60,
) -> Dict[str, any]:
    """
    Extract a bounded directed neighborhood around tx_id.

    Returns:
        Dict with center_node, predecessors, successors, nodes, edges,
        and subgraph metadata.
    """
    G = get_graph_instance()
    tx_id = int(tx_id)

    if tx_id not in G:
        return {"error": f"Transaction {tx_id} not found in graph."}

    # Direct predecessors (inputs) and successors (outputs)
    predecessors = list(G.predecessors(tx_id))
    successors = list(G.successors(tx_id))

    # Collect nodes within requested hops
    selected_nodes: Set[int] = {tx_id}
    current_frontier: Set[int] = {tx_id}

    for _ in range(hops):
        next_frontier = set()
        for node in current_frontier:
            next_frontier.update(G.predecessors(node))
            next_frontier.update(G.successors(node))
        
        selected_nodes.update(next_frontier)
        current_frontier = next_frontier
        
        if len(selected_nodes) >= max_nodes:
            break

    # Trim to max_nodes if exceeded (preserving center, predecessors, and successors)
    if len(selected_nodes) > max_nodes:
        priority_nodes = [tx_id] + predecessors[:(max_nodes // 2)] + successors[:(max_nodes // 2)]
        selected_nodes = set(priority_nodes[:max_nodes])

    # Extract directed subgraph
    subgraph = G.subgraph(selected_nodes)

    # Format nodes payload
    nodes_payload = []
    for n in subgraph.nodes():
        attrs = subgraph.nodes[n]
        nodes_payload.append({
            "txId": n,
            "is_center": (n == tx_id),
            "time_step": attrs.get("time_step"),
            "label": str(attrs.get("label", "unknown")),
            "in_degree": subgraph.in_degree(n),
            "out_degree": subgraph.out_degree(n),
        })

    # Format directed edges payload
    edges_payload = []
    for u, v in subgraph.edges():
        edges_payload.append({
            "source": u,
            "target": v,
        })

    return {
        "center_node": tx_id,
        "hops": hops,
        "direct_predecessors_count": len(predecessors),
        "direct_successors_count": len(successors),
        "direct_predecessors_sample": predecessors[:10],
        "direct_successors_sample": successors[:10],
        "total_subgraph_nodes": len(nodes_payload),
        "total_subgraph_edges": len(edges_payload),
        "nodes": nodes_payload,
        "edges": edges_payload,
    }


def find_directed_payment_path(
    source_tx: int,
    target_tx: int,
    cutoff: int = 6,
) -> Optional[List[int]]:
    """
    Find shortest directed path between two transactions.
    Returns list of transaction IDs or None if no directed path exists.
    """
    G = get_graph_instance()
    source_tx, target_tx = int(source_tx), int(target_tx)

    if source_tx not in G or target_tx not in G:
        return None

    try:
        return nx.shortest_path(G, source=source_tx, target=target_tx)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

