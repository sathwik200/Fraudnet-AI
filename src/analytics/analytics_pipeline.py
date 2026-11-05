#!/usr/bin/env python3
"""
FRAUDNET AI — Graph Analytics Pipeline
=======================================
Orchestrates end-to-end network analysis, community detection, temporal
aggregation, and structural pattern mining.

Outputs generated under data/processed/analytics/:
  - transaction_metrics.parquet : Node-level metrics (degrees, PageRank, communities)
  - temporal_summary.json      : 49-step time series indicators
  - network_patterns.json      : Aggregation/distribution hubs and structural roles
  - community_summary.json     : Louvain community breakdowns and class ratios

CLI Usage:
  python -m src.analytics.analytics_pipeline [--force]
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

from src.analytics.centrality import get_top_k_transactions_by_metric
from src.analytics.community_detection import detect_communities_louvain
from src.analytics.graph_metrics import compute_all_transaction_metrics
from src.analytics.network_patterns import detect_structural_patterns
from src.analytics.temporal_analysis import compute_temporal_summary
from src.graph.build_graph import load_graph

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
ANALYTICS_DIR = DATA_DIR / "analytics"

GRAPH_PATH = DATA_DIR / "transaction_graph.pkl"
OUTPUT_METRICS_PARQUET = ANALYTICS_DIR / "transaction_metrics.parquet"
OUTPUT_TEMPORAL_JSON = ANALYTICS_DIR / "temporal_summary.json"
OUTPUT_PATTERNS_JSON = ANALYTICS_DIR / "network_patterns.json"
OUTPUT_COMMUNITY_JSON = ANALYTICS_DIR / "community_summary.json"


def run_analytics_pipeline(
    graph_path: Path = GRAPH_PATH,
    output_dir: Path = ANALYTICS_DIR,
    force_recompute: bool = False,
    verbose: bool = True,
) -> Dict[str, any]:
    """
    Execute graph analytics pipeline and persist results to disk.
    If cached artifacts exist and force_recompute is False, loads and returns them.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check cache
    artifacts_exist = (
        OUTPUT_METRICS_PARQUET.exists()
        and OUTPUT_TEMPORAL_JSON.exists()
        and OUTPUT_PATTERNS_JSON.exists()
        and OUTPUT_COMMUNITY_JSON.exists()
    )

    if artifacts_exist and not force_recompute:
        if verbose:
            print(f"Loading cached analytics from {output_dir}...")
        metrics_df = pd.read_parquet(OUTPUT_METRICS_PARQUET)
        with open(OUTPUT_TEMPORAL_JSON) as f:
            temporal_data = json.load(f)
        with open(OUTPUT_PATTERNS_JSON) as f:
            patterns_data = json.load(f)
        with open(OUTPUT_COMMUNITY_JSON) as f:
            community_data = json.load(f)

        return {
            "metrics_df": metrics_df,
            "temporal_data": temporal_data,
            "patterns_data": patterns_data,
            "community_data": community_data,
            "from_cache": True,
        }

    t_total = time.time()
    if verbose:
        print("\n" + "=" * 72)
        print("  FRAUDNET AI — GRAPH ANALYTICS & NETWORK INTELLIGENCE ENGINE")
        print("=" * 72)

    # 1. Load Graph
    if verbose:
        print(f"[1/5] Loading graph from {graph_path}...")
    graph = load_graph(graph_path, verbose=False)
    if verbose:
        print(f"      Loaded {graph.number_of_nodes():,} nodes and {graph.number_of_edges():,} directed edges.")

    # 2. Transaction-Level Metrics
    if verbose:
        print("[2/5] Computing degrees, PageRank, and WCC metrics...")
    metrics_df = compute_all_transaction_metrics(graph, verbose=verbose)

    # 3. Community Detection (Louvain)
    if verbose:
        print("[3/5] Performing Louvain community detection...")
    node_to_comm, community_summaries = detect_communities_louvain(graph, verbose=verbose)
    metrics_df["community_id"] = [node_to_comm[n] for n in metrics_df.index]

    # 4. Network Pattern Detection
    if verbose:
        print("[4/5] Identifying network payment patterns (hubs, aggregation/distribution)...")
    patterns_data = detect_structural_patterns(metrics_df)

    # Flag top hubs in the metrics table for fast lookup
    in_thresh = patterns_data["thresholds"]["aggregation_in_degree_threshold"]
    out_thresh = patterns_data["thresholds"]["distribution_out_degree_threshold"]
    metrics_df["is_aggregation_hub"] = metrics_df["in_degree"] >= in_thresh
    metrics_df["is_distribution_hub"] = metrics_df["out_degree"] >= out_thresh

    # 5. Temporal Analysis
    if verbose:
        print("[5/5] Analyzing historical activity across 49 time steps...")
    temporal_data = compute_temporal_summary(graph, metrics_df)

    # 6. Save Artifacts
    if verbose:
        print("\nSaving analytics outputs to disk...")

    # Save transaction metrics table (reset index so txId is an explicit column)
    metrics_to_save = metrics_df.reset_index()
    metrics_to_save.to_parquet(OUTPUT_METRICS_PARQUET, index=False, engine="pyarrow")
    if verbose:
        size_mb = OUTPUT_METRICS_PARQUET.stat().st_size / (1024 * 1024)
        print(f"  ✓ {OUTPUT_METRICS_PARQUET.name} ({size_mb:.2f} MB)")

    with open(OUTPUT_TEMPORAL_JSON, "w") as f:
        json.dump(temporal_data, f, indent=2)
    if verbose:
        print(f"  ✓ {OUTPUT_TEMPORAL_JSON.name}")

    with open(OUTPUT_PATTERNS_JSON, "w") as f:
        json.dump(patterns_data, f, indent=2)
    if verbose:
        print(f"  ✓ {OUTPUT_PATTERNS_JSON.name}")

    with open(OUTPUT_COMMUNITY_JSON, "w") as f:
        json.dump(community_summaries, f, indent=2)
    if verbose:
        print(f"  ✓ {OUTPUT_COMMUNITY_JSON.name}")

    elapsed_total = time.time() - t_total
    if verbose:
        print("\n" + "=" * 72)
        print(f"  GRAPH ANALYTICS COMPLETE — Elapsed time: {elapsed_total:.2f}s")
        print("=" * 72 + "\n")

    return {
        "metrics_df": metrics_df,
        "temporal_data": temporal_data,
        "patterns_data": patterns_data,
        "community_data": community_summaries,
        "from_cache": False,
    }


def main():
    parser = argparse.ArgumentParser(description="FRAUDNET AI Graph Analytics Pipeline")
    parser.add_argument("--force", action="store_true", help="Force recomputation of cached analytics")
    args = parser.parse_args()

    run_analytics_pipeline(force_recompute=args.force, verbose=True)


if __name__ == "__main__":
    main()

