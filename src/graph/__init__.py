"""
FRAUDNET AI — Graph Module
===========================
Provides pipeline tools for constructing, serializing, and validating the
directed Bitcoin transaction network using NetworkX.
"""

__all__ = [
    "build_transaction_graph",
    "build_and_save_pipeline",
    "load_graph",
    "save_graph",
    "validate_source_data",
    "validate_transaction_graph",
    "generate_graph_summary",
    "save_graph_summary",
]


def __getattr__(name: str):
    if name in {
        "build_transaction_graph",
        "build_and_save_pipeline",
        "load_graph",
        "save_graph",
        "validate_source_data",
    }:
        from . import build_graph
        return getattr(build_graph, name)
    elif name in {
        "validate_transaction_graph",
        "generate_graph_summary",
        "save_graph_summary",
    }:
        from . import validate_graph
        return getattr(validate_graph, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
