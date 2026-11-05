"""
FRAUDNET AI — Analytics Package
================================
Modules for transaction-level metrics, centrality measures, community detection,
network flow patterns, and temporal analysis.
"""

__all__ = [
    "compute_degree_metrics",
    "compute_pagerank",
    "compute_wcc_membership",
    "compute_clustering_coefficients",
    "compute_all_transaction_metrics",
    "get_top_k_transactions_by_metric",
    "compute_ego_betweenness",
    "compute_approximate_betweenness_for_candidates",
    "detect_communities_louvain",
    "detect_structural_patterns",
    "compute_temporal_summary",
    "run_analytics_pipeline",
]


def __getattr__(name: str):
    if name in {
        "compute_degree_metrics",
        "compute_pagerank",
        "compute_wcc_membership",
        "compute_clustering_coefficients",
        "compute_all_transaction_metrics",
    }:
        from . import graph_metrics
        return getattr(graph_metrics, name)
    elif name in {
        "get_top_k_transactions_by_metric",
        "compute_ego_betweenness",
        "compute_approximate_betweenness_for_candidates",
    }:
        from . import centrality
        return getattr(centrality, name)
    elif name in {"detect_communities_louvain"}:
        from . import community_detection
        return getattr(community_detection, name)
    elif name in {"detect_structural_patterns"}:
        from . import network_patterns
        return getattr(network_patterns, name)
    elif name in {"compute_temporal_summary"}:
        from . import temporal_analysis
        return getattr(temporal_analysis, name)
    elif name in {"run_analytics_pipeline"}:
        from . import analytics_pipeline
        return getattr(analytics_pipeline, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
