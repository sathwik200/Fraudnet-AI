#!/usr/bin/env python3
"""
FRAUDNET AI — Bitcoin Transaction Network Builder
===================================================
Constructs a directed Bitcoin transaction network (networkx.DiGraph) from
processed Parquet datasets:
  - data/processed/transactions.parquet
  - data/processed/edges.parquet

Design Principles:
  - Every Bitcoin transaction becomes a node in a networkx.DiGraph.
  - Every payment relationship becomes a directed edge (txId1 -> txId2).
  - Isolated transactions (no inputs or outputs) are strictly preserved.
  - Original transaction IDs (int64), time steps (int64), and labels (str)
    are preserved as node metadata.
  - All 165 numerical features remain stored in Parquet to keep the graph
    memory-efficient and lightweight.
  - No artificial edges or connections across time steps are created.
  - Class labels are never used as numerical graph features.
  - Duplicate directed edges in the source trigger validation failure.
  - The graph artifact is saved to data/processed/transaction_graph.pkl
    via pickle serialization with safe loading guidelines.

CLI Usage:
  python -m src.graph.build_graph
"""

import os
import pickle
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

import networkx as nx
import pandas as pd

# ---------------------------------------------------------------------------
# Default Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_TRANSACTIONS_PATH = PROCESSED_DIR / "transactions.parquet"
DEFAULT_EDGES_PATH = PROCESSED_DIR / "edges.parquet"
DEFAULT_GRAPH_OUTPUT_PATH = PROCESSED_DIR / "transaction_graph.pkl"
DEFAULT_SUMMARY_OUTPUT_PATH = PROCESSED_DIR / "graph_summary.json"


# ---------------------------------------------------------------------------
# Source Data Validation
# ---------------------------------------------------------------------------
def validate_source_data(
    tx_df: pd.DataFrame,
    edges_df: pd.DataFrame,
) -> Dict[str, any]:
    """
    Validate transaction and edge DataFrames prior to graph construction.

    Performs strict assertions:
      1. Required columns presence.
      2. No missing/null values in transaction IDs, time steps, or labels.
      3. No duplicate transaction IDs.
      4. No missing/null values in edge endpoints.
      5. No duplicate directed edges in the source edge list.
      6. No orphan edge endpoints (endpoints must exist in transactions).
      7. Detection and logging of any self-loops.

    Raises:
        ValueError: If duplicate txIds, duplicate edges, orphan endpoints,
                    or missing columns are discovered.

    Returns:
        Dict with validation metrics.
    """
    # 1. Required columns
    required_tx_cols = {"txId", "time_step", "label"}
    missing_tx_cols = required_tx_cols - set(tx_df.columns)
    if missing_tx_cols:
        raise ValueError(f"transactions DataFrame missing required columns: {missing_tx_cols}")

    required_edge_cols = {"txId1", "txId2"}
    missing_edge_cols = required_edge_cols - set(edges_df.columns)
    if missing_edge_cols:
        raise ValueError(f"edges DataFrame missing required columns: {missing_edge_cols}")

    # 2. Null checks
    null_tx = tx_df["txId"].isna().sum()
    if null_tx > 0:
        raise ValueError(f"Found {null_tx} null transaction IDs in transactions table")

    null_ts = tx_df["time_step"].isna().sum()
    if null_ts > 0:
        raise ValueError(f"Found {null_ts} null time_step values in transactions table")

    null_lbl = tx_df["label"].isna().sum()
    if null_lbl > 0:
        raise ValueError(f"Found {null_lbl} null labels in transactions table")

    null_src = edges_df["txId1"].isna().sum()
    null_dst = edges_df["txId2"].isna().sum()
    if null_src > 0 or null_dst > 0:
        raise ValueError(
            f"Found null edge endpoints: {null_src} in txId1, {null_dst} in txId2"
        )

    # 3. Duplicate transaction IDs
    duplicate_txids = tx_df["txId"].duplicated().sum()
    if duplicate_txids > 0:
        raise ValueError(
            f"Validation failed: Found {duplicate_txids:,} duplicate transaction IDs in transactions table"
        )

    # 4. Duplicate directed edges
    duplicate_edges = edges_df.duplicated(subset=["txId1", "txId2"]).sum()
    if duplicate_edges > 0:
        raise ValueError(
            f"Validation failed: Found {duplicate_edges:,} duplicate directed edges in source edge list. "
            f"Duplicate edges must not be silently treated as unique relationships."
        )

    # 5. Orphan edge endpoints
    tx_id_set = set(tx_df["txId"])
    src_orphans = set(edges_df["txId1"]) - tx_id_set
    dst_orphans = set(edges_df["txId2"]) - tx_id_set
    total_orphans = src_orphans | dst_orphans
    if total_orphans:
        sample_orphans = list(total_orphans)[:5]
        raise ValueError(
            f"Validation failed: Found {len(total_orphans):,} orphan edge endpoints not present "
            f"in transactions table. Sample: {sample_orphans}"
        )

    # 6. Self-loops detection
    self_loops_count = int((edges_df["txId1"] == edges_df["txId2"]).sum())

    return {
        "num_transactions": len(tx_df),
        "num_edges": len(edges_df),
        "duplicate_txids": int(duplicate_txids),
        "duplicate_edges": int(duplicate_edges),
        "orphan_endpoints": len(total_orphans),
        "self_loops": self_loops_count,
        "status": "VALID",
    }


# ---------------------------------------------------------------------------
# Graph Construction
# ---------------------------------------------------------------------------
def build_transaction_graph(
    transactions_path: Optional[Path] = None,
    edges_path: Optional[Path] = None,
    tx_df: Optional[pd.DataFrame] = None,
    edges_df: Optional[pd.DataFrame] = None,
    verbose: bool = True,
) -> nx.DiGraph:
    """
    Construct a networkx.DiGraph representing the Bitcoin transaction network.

    Args:
        transactions_path: Path to transactions.parquet. Defaults to standard project path.
        edges_path: Path to edges.parquet. Defaults to standard project path.
        tx_df: Optional in-memory transactions DataFrame (avoids reading from disk).
        edges_df: Optional in-memory edges DataFrame (avoids reading from disk).
        verbose: If True, prints build milestones and timing.

    Returns:
        nx.DiGraph containing all transaction nodes and directed edges.
    """
    tx_path = Path(transactions_path) if transactions_path else DEFAULT_TRANSACTIONS_PATH
    edge_path = Path(edges_path) if edges_path else DEFAULT_EDGES_PATH

    t_start = time.time()

    # Load DataFrames if not supplied
    if tx_df is None:
        if not tx_path.exists():
            raise FileNotFoundError(f"Transactions Parquet file not found: {tx_path}")
        if verbose:
            print(f"[1/4] Loading transaction metadata from {tx_path}...")
        # Load only metadata columns required for the graph structure
        tx_df = pd.read_parquet(tx_path, columns=["txId", "time_step", "label"])

    if edges_df is None:
        if not edge_path.exists():
            raise FileNotFoundError(f"Edges Parquet file not found: {edge_path}")
        if verbose:
            print(f"[2/4] Loading edge list from {edge_path}...")
        edges_df = pd.read_parquet(edge_path, columns=["txId1", "txId2"])

    # Strict pre-construction validation
    if verbose:
        print("[3/4] Validating source data integrity...")
    val_stats = validate_source_data(tx_df, edges_df)
    if verbose:
        print(f"      Source validated: {val_stats['num_transactions']:,} transactions, "
              f"{val_stats['num_edges']:,} edges, "
              f"self-loops: {val_stats['self_loops']}, duplicate edges: {val_stats['duplicate_edges']}")

    # Instantiate directed graph
    if verbose:
        print("[4/4] Constructing networkx.DiGraph...")
    G = nx.DiGraph()

    # Step A: Add all nodes with attributes (including isolated transactions)
    # Node keys retain exact integer representation
    node_tuples = [
        (int(tid), {"time_step": int(ts), "label": str(lbl)})
        for tid, ts, lbl in zip(tx_df["txId"], tx_df["time_step"], tx_df["label"])
    ]
    G.add_nodes_from(node_tuples)

    # Step B: Add all directed edges (txId1 -> txId2)
    edge_tuples = [
        (int(src), int(dst))
        for src, dst in zip(edges_df["txId1"], edges_df["txId2"])
    ]
    G.add_edges_from(edge_tuples)

    # Post-construction sanity assertions
    if G.number_of_nodes() != len(tx_df):
        raise RuntimeError(
            f"Node count mismatch: graph has {G.number_of_nodes():,} nodes, "
            f"expected {len(tx_df):,}"
        )
    if G.number_of_edges() != len(edges_df):
        raise RuntimeError(
            f"Edge count mismatch: graph has {G.number_of_edges():,} edges, "
            f"expected {len(edges_df):,}"
        )

    t_elapsed = time.time() - t_start
    if verbose:
        print(f"      Graph constructed in {t_elapsed:.2f}s: "
              f"{G.number_of_nodes():,} nodes, {G.number_of_edges():,} directed edges.")

    return G


# ---------------------------------------------------------------------------
# Serialization & Deserialization
# ---------------------------------------------------------------------------
def save_graph(
    graph: nx.DiGraph,
    output_path: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    """
    Serialize the constructed graph to disk using pickle.

    SAFETY NOTICE:
      Python's pickle module is used here to serialize a complex networkx.DiGraph
      data structure with node attributes. Only unpickle files created directly
      by this verified project pipeline. Do not load pickle files from untrusted
      external sources.

    Args:
        graph: The networkx.DiGraph to serialize.
        output_path: Target path. Defaults to data/processed/transaction_graph.pkl.
        verbose: If True, prints file path and size.

    Returns:
        Path where the graph was written.
    """
    path = Path(output_path) if output_path else DEFAULT_GRAPH_OUTPUT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    with open(path, "wb") as f:
        pickle.dump(graph, f, protocol=pickle.HIGHEST_PROTOCOL)

    size_mb = path.stat().st_size / (1024 * 1024)
    if verbose:
        print(f"Graph serialized to {path} ({size_mb:.2f} MB in {time.time()-t0:.2f}s)")

    return path


def load_graph(
    input_path: Optional[Path] = None,
    verbose: bool = True,
) -> nx.DiGraph:
    """
    Safely load a serialized networkx.DiGraph from disk.

    Args:
        input_path: Path to pickle file. Defaults to data/processed/transaction_graph.pkl.
        verbose: If True, prints load statistics.

    Returns:
        Deserialized networkx.DiGraph.
    """
    path = Path(input_path) if input_path else DEFAULT_GRAPH_OUTPUT_PATH
    if not path.exists():
        raise FileNotFoundError(f"Serialized graph file not found: {path}")

    t0 = time.time()
    with open(path, "rb") as f:
        G = pickle.load(f)

    if not isinstance(G, nx.DiGraph):
        raise TypeError(f"Expected networkx.DiGraph instance, got {type(G)}")

    if verbose:
        print(f"Graph loaded from {path} in {time.time()-t0:.2f}s: "
              f"{G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges.")

    return G


# ---------------------------------------------------------------------------
# End-to-End Build and Validate Pipeline
# ---------------------------------------------------------------------------
def build_and_save_pipeline(
    transactions_path: Optional[Path] = None,
    edges_path: Optional[Path] = None,
    graph_output_path: Optional[Path] = None,
    summary_output_path: Optional[Path] = None,
    verbose: bool = True,
) -> Tuple[nx.DiGraph, Dict]:
    """
    Execute the complete graph construction, validation, and serialization pipeline.

    Steps:
      1. Load metadata and edges.
      2. Validate source records.
      3. Construct networkx.DiGraph.
      4. Validate graph properties and compute metrics via validate_graph.
      5. Serialize graph to transaction_graph.pkl.
      6. Write graph summary JSON.

    Returns:
        (constructed_graph, summary_dict)
    """
    # Import validation module here to avoid circular imports
    from src.graph.validate_graph import (
        generate_graph_summary,
        save_graph_summary,
        validate_transaction_graph,
    )

    if verbose:
        print("\n" + "=" * 72)
        print("  FRAUDNET AI — PHASE 2: BITCOIN TRANSACTION NETWORK BUILDER")
        print("=" * 72)

    # Build graph
    G = build_transaction_graph(
        transactions_path=transactions_path,
        edges_path=edges_path,
        verbose=verbose,
    )

    # Validate graph
    if verbose:
        print("\n[Validating Graph]")
    val_report, passed = validate_transaction_graph(G, verbose=verbose)
    if not passed:
        raise RuntimeError("Graph validation failed after construction. Halting pipeline.")

    # Save graph artifact
    if verbose:
        print("\n[Serializing Graph Artifact]")
    graph_path = save_graph(G, output_path=graph_output_path, verbose=verbose)

    # Generate and save summary
    if verbose:
        print("\n[Generating Graph Summary]")
    summary = generate_graph_summary(G, val_report)
    save_graph_summary(summary, output_path=summary_output_path, verbose=verbose)

    if verbose:
        print("\n" + "=" * 72)
        print("  GRAPH CONSTRUCTION & VALIDATION COMPLETE — ALL CHECKS PASSED")
        print("=" * 72 + "\n")

    return G, summary


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    """CLI execution for python -m src.graph.build_graph"""
    try:
        build_and_save_pipeline(verbose=True)
    except Exception as e:
        print(f"\nERROR during graph construction: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

