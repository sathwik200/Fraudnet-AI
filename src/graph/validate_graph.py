#!/usr/bin/env python3
"""
FRAUDNET AI — Bitcoin Transaction Network Validator
=====================================================
Validates a constructed networkx.DiGraph against structural, relational,
temporal, and labeling integrity requirements.

Validation Scope:
  - Total transaction node count
  - Total directed edge count
  - Graph type verification (networkx.DiGraph)
  - Isolated node count (in-degree == 0 and out-degree == 0)
  - Zero in-degree (root/source) and zero out-degree (sink/leaf) counts
  - Self-loop detection and reporting
  - Duplicate directed edge verification
  - Node attribute completeness (time_step and label)
  - Edge endpoint integrity (no orphan nodes)
  - In-degree and out-degree statistics (min, max, mean, median, stdev)
  - Temporal distribution across 49 time steps
  - Class distribution across illicit ('1'), licit ('2'), and unknown
  - Weakly and strongly connected component counts

Summary Serialization:
  Writes structured JSON to data/processed/graph_summary.json.

CLI Usage:
  python -m src.graph.validate_graph
"""

import json
import math
import statistics
import sys
import time
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple

import networkx as nx
import pandas as pd

# ---------------------------------------------------------------------------
# Default Paths & Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DEFAULT_GRAPH_PATH = PROCESSED_DIR / "transaction_graph.pkl"
DEFAULT_SUMMARY_PATH = PROCESSED_DIR / "graph_summary.json"
DEFAULT_TRANSACTIONS_PATH = PROCESSED_DIR / "transactions.parquet"
DEFAULT_EDGES_PATH = PROCESSED_DIR / "edges.parquet"

EXPECTED_NODE_COUNT = 203_769
EXPECTED_EDGE_COUNT = 234_355
EXPECTED_TIME_STEPS = 49
VALID_LABELS = {"1", "2", "unknown"}


# ---------------------------------------------------------------------------
# Graph Validation Engine
# ---------------------------------------------------------------------------
def validate_transaction_graph(
    graph: nx.DiGraph,
    tx_df: Optional[pd.DataFrame] = None,
    edges_df: Optional[pd.DataFrame] = None,
    verbose: bool = True,
) -> Tuple[Dict, bool]:
    """
    Perform a complete structural and semantic audit of a transaction network.

    Args:
        graph: networkx.DiGraph instance to audit.
        tx_df: Optional transactions DataFrame for ground-truth comparison.
        edges_df: Optional edges DataFrame for ground-truth comparison.
        verbose: If True, prints formatted validation output.

    Returns:
        (validation_report_dict, all_passed_bool)
    """
    t_start = time.time()
    report = OrderedDict()
    checks = []

    def log_check(name: str, passed: bool, detail: str = "") -> bool:
        checks.append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        return passed

    # 1. Type validation
    is_digraph = isinstance(graph, nx.DiGraph)
    log_check(
        "is_directed_graph",
        is_digraph,
        f"type={type(graph).__name__}",
    )
    if not is_digraph:
        report["checks"] = checks
        report["all_passed"] = False
        return report, False

    num_nodes = graph.number_of_nodes()
    num_edges = graph.number_of_edges()

    # 2. Node count
    expected_nodes = len(tx_df) if tx_df is not None else EXPECTED_NODE_COUNT
    log_check(
        "node_count_matches",
        num_nodes == expected_nodes,
        f"actual={num_nodes:,}, expected={expected_nodes:,}",
    )

    # 3. Edge count
    expected_edges = len(edges_df) if edges_df is not None else EXPECTED_EDGE_COUNT
    log_check(
        "edge_count_matches",
        num_edges == expected_edges,
        f"actual={num_edges:,}, expected={expected_edges:,}",
    )

    # 4. Node attribute verification
    missing_attrs = 0
    invalid_labels = 0
    time_step_dist = Counter()
    label_dist = Counter()

    for node_id, attrs in graph.nodes(data=True):
        if "time_step" not in attrs or "label" not in attrs:
            missing_attrs += 1
            continue
        ts = attrs["time_step"]
        lbl = str(attrs["label"])
        time_step_dist[ts] += 1
        label_dist[lbl] += 1
        if lbl not in VALID_LABELS:
            invalid_labels += 1

    log_check(
        "node_attributes_complete",
        missing_attrs == 0,
        f"missing attributes count={missing_attrs}",
    )
    log_check(
        "valid_class_labels_only",
        invalid_labels == 0,
        f"invalid labels count={invalid_labels}",
    )

    # 5. Temporal distribution
    unique_ts = len(time_step_dist)
    min_ts = min(time_step_dist.keys()) if time_step_dist else 0
    max_ts = max(time_step_dist.keys()) if time_step_dist else 0
    log_check(
        "time_step_count_matches",
        unique_ts == EXPECTED_TIME_STEPS,
        f"unique time steps={unique_ts}, range=[{min_ts}, {max_ts}]",
    )

    # 6. Self-loops
    self_loops_count = nx.number_of_selfloops(graph)
    log_check(
        "self_loops_reported",
        True,  # Informational check
        f"self-loops count={self_loops_count}",
    )

    # 7. Degree statistics
    in_degrees = [d for _, d in graph.in_degree()]
    out_degrees = [d for _, d in graph.out_degree()]

    in_min = min(in_degrees) if in_degrees else 0
    in_max = max(in_degrees) if in_degrees else 0
    in_avg = (sum(in_degrees) / len(in_degrees)) if in_degrees else 0.0
    in_med = statistics.median(in_degrees) if in_degrees else 0.0
    in_stdev = statistics.stdev(in_degrees) if len(in_degrees) > 1 else 0.0

    out_min = min(out_degrees) if out_degrees else 0
    out_max = max(out_degrees) if out_degrees else 0
    out_avg = (sum(out_degrees) / len(out_degrees)) if out_degrees else 0.0
    out_med = statistics.median(out_degrees) if out_degrees else 0.0
    out_stdev = statistics.stdev(out_degrees) if len(out_degrees) > 1 else 0.0

    zero_in_count = sum(1 for d in in_degrees if d == 0)
    zero_out_count = sum(1 for d in out_degrees if d == 0)
    isolated_nodes_count = sum(1 for _ in nx.isolates(graph))

    log_check(
        "degree_conservation",
        sum(in_degrees) == sum(out_degrees) == num_edges,
        f"total in={sum(in_degrees):,}, total out={sum(out_degrees):,}, edges={num_edges:,}",
    )

    # 8. Connectivity Analysis
    # Weakly connected components (each timestep form isolated subgraphs in Elliptic)
    wcc_count = nx.number_weakly_connected_components(graph)
    largest_wcc_size = len(max(nx.weakly_connected_components(graph), key=len)) if num_nodes > 0 else 0
    scc_count = nx.number_strongly_connected_components(graph)

    log_check(
        "connectivity_analyzed",
        wcc_count > 0,
        f"WCC count={wcc_count}, largest WCC={largest_wcc_size:,}, SCC count={scc_count:,}",
    )

    # 9. Duplicate source edges (if edges_df provided)
    duplicate_edges = 0
    if edges_df is not None:
        duplicate_edges = int(edges_df.duplicated(subset=["txId1", "txId2"]).sum())
        log_check(
            "no_duplicate_source_edges",
            duplicate_edges == 0,
            f"duplicate edges in source={duplicate_edges}",
        )

    # 10. Orphan edge endpoints
    # Check that all source and target endpoints belong to graph.nodes
    orphan_endpoints = 0
    if edges_df is not None:
        node_set = set(graph.nodes)
        src_orphans = set(edges_df["txId1"]) - node_set
        dst_orphans = set(edges_df["txId2"]) - node_set
        orphan_endpoints = len(src_orphans | dst_orphans)
        log_check(
            "no_orphan_edge_endpoints",
            orphan_endpoints == 0,
            f"orphan edge endpoints={orphan_endpoints}",
        )

    all_passed = all(c["passed"] for c in checks)

    # Compile structured report
    report["num_nodes"] = num_nodes
    report["num_edges"] = num_edges
    report["is_digraph"] = is_digraph
    report["isolated_nodes"] = isolated_nodes_count
    report["zero_in_degree_nodes"] = zero_in_count
    report["zero_out_degree_nodes"] = zero_out_count
    report["self_loops"] = self_loops_count
    report["duplicate_edges"] = duplicate_edges
    report["missing_node_attributes"] = missing_attrs
    report["orphan_endpoints"] = orphan_endpoints
    report["time_step_distribution"] = dict(sorted(time_step_dist.items()))
    report["class_distribution"] = {
        "illicit (1)": label_dist.get("1", 0),
        "licit (2)": label_dist.get("2", 0),
        "unknown": label_dist.get("unknown", 0),
    }
    report["degree_statistics"] = {
        "in_degree": {
            "min": in_min,
            "max": in_max,
            "mean": round(in_avg, 4),
            "median": in_med,
            "stdev": round(in_stdev, 4),
            "zero_in_degree_count": zero_in_count,
        },
        "out_degree": {
            "min": out_min,
            "max": out_max,
            "mean": round(out_avg, 4),
            "median": out_med,
            "stdev": round(out_stdev, 4),
            "zero_out_degree_count": zero_out_count,
        },
    }
    report["connectivity"] = {
        "weakly_connected_components": wcc_count,
        "largest_wcc_size": largest_wcc_size,
        "strongly_connected_components": scc_count,
    }
    report["checks"] = checks
    report["all_passed"] = all_passed
    report["elapsed_seconds"] = round(time.time() - t_start, 3)

    if verbose:
        print_validation_report(report)

    return report, all_passed


# ---------------------------------------------------------------------------
# Human-Readable Formatter
# ---------------------------------------------------------------------------
def print_validation_report(report: Dict):
    """Print a clean ASCII summary of graph validation results."""
    print("=" * 72)
    print("  FRAUDNET AI — GRAPH VALIDATION AUDIT REPORT")
    print("=" * 72)

    total = len(report["checks"])
    passed = sum(1 for c in report["checks"] if c["passed"])

    for c in report["checks"]:
        mark = "✓ PASS" if c["passed"] else "✗ FAIL"
        print(f"  {mark:<8} {c['check']:<28} | {c['detail']}")

    print("-" * 72)
    print(f"  OVERALL RESULT: {passed}/{total} checks passed "
          f"({'ALL PASSED ✓' if report['all_passed'] else 'FAILURES DETECTED ✗'})")
    print("-" * 72)
    print(f"  Nodes:                   {report['num_nodes']:,}")
    print(f"  Directed Edges:          {report['num_edges']:,}")
    print(f"  Isolated Nodes:          {report['isolated_nodes']:,}")
    print(f"  Zero In-Degree Nodes:    {report['zero_in_degree_nodes']:,} (source transactions)")
    print(f"  Zero Out-Degree Nodes:   {report['zero_out_degree_nodes']:,} (sink transactions)")
    print(f"  Self-Loops:              {report['self_loops']}")
    print(f"  Weakly Connected Comps:  {report['connectivity']['weakly_connected_components']}")
    print(f"  Largest Component Size:  {report['connectivity']['largest_wcc_size']:,}")
    print(f"  Strongly Connected Comps:{report['connectivity']['strongly_connected_components']:,}")
    print(f"  Max In-Degree:           {report['degree_statistics']['in_degree']['max']}")
    print(f"  Avg In-Degree:           {report['degree_statistics']['in_degree']['mean']}")
    print(f"  Max Out-Degree:          {report['degree_statistics']['out_degree']['max']}")
    print(f"  Avg Out-Degree:          {report['degree_statistics']['out_degree']['mean']}")
    print()
    print("  Class Distribution:")
    for lbl, count in report["class_distribution"].items():
        pct = (count / report["num_nodes"] * 100) if report["num_nodes"] > 0 else 0
        print(f"    - {lbl:<15}: {count:>8,} ({pct:.2f}%)")
    print("=" * 72)


# ---------------------------------------------------------------------------
# Summary JSON Generation
# ---------------------------------------------------------------------------
def generate_graph_summary(
    graph: nx.DiGraph,
    validation_report: Dict,
) -> Dict:
    """
    Produce the canonical machine-readable JSON structure for graph_summary.json.
    """
    summary = OrderedDict()
    summary["project_name"] = "FRAUDNET AI"
    summary["graph_type"] = "networkx.DiGraph"
    summary["dataset_source"] = (
        "data/processed/transactions.parquet, data/processed/edges.parquet"
    )
    summary["total_nodes"] = validation_report["num_nodes"]
    summary["total_edges"] = validation_report["num_edges"]
    summary["time_step_distribution"] = validation_report["time_step_distribution"]
    summary["class_distribution"] = validation_report["class_distribution"]
    summary["degree_statistics"] = validation_report["degree_statistics"]
    summary["connectivity_statistics"] = validation_report["connectivity"]
    summary["isolated_node_count"] = validation_report["isolated_nodes"]
    summary["self_loop_count"] = validation_report["self_loops"]
    summary["duplicate_edge_count"] = validation_report["duplicate_edges"]
    summary["validation_status"] = "PASSED" if validation_report["all_passed"] else "FAILED"
    summary["build_timestamp"] = datetime.now(timezone.utc).isoformat()
    summary["python_version"] = sys.version.split()[0]
    summary["networkx_version"] = nx.__version__

    return summary


def save_graph_summary(
    summary: Dict,
    output_path: Optional[Path] = None,
    verbose: bool = True,
) -> Path:
    """Save graph summary dictionary to JSON file."""
    path = Path(output_path) if output_path else DEFAULT_SUMMARY_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    if verbose:
        print(f"Graph summary saved to {path}")

    return path


# ---------------------------------------------------------------------------
# CLI Entry Point
# ---------------------------------------------------------------------------
def main():
    """CLI execution for python -m src.graph.validate_graph"""
    from src.graph.build_graph import load_graph

    print("\n" + "=" * 72)
    print("  FRAUDNET AI — GRAPH ARTIFACT VALIDATOR")
    print("=" * 72)

    if not DEFAULT_GRAPH_PATH.exists():
        print(f"ERROR: Graph artifact not found at {DEFAULT_GRAPH_PATH}.", file=sys.stderr)
        print("Run 'python -m src.graph.build_graph' first to construct the graph.", file=sys.stderr)
        sys.exit(1)

    print(f"Loading graph from {DEFAULT_GRAPH_PATH}...")
    G = load_graph(DEFAULT_GRAPH_PATH, verbose=False)

    # Optional: load reference Parquet if available for cross-checking
    tx_df = None
    edges_df = None
    if DEFAULT_TRANSACTIONS_PATH.exists():
        tx_df = pd.read_parquet(DEFAULT_TRANSACTIONS_PATH, columns=["txId", "time_step", "label"])
    if DEFAULT_EDGES_PATH.exists():
        edges_df = pd.read_parquet(DEFAULT_EDGES_PATH, columns=["txId1", "txId2"])

    report, passed = validate_transaction_graph(G, tx_df=tx_df, edges_df=edges_df, verbose=True)

    # Update summary JSON
    summary = generate_graph_summary(G, report)
    save_graph_summary(summary, verbose=True)

    if not passed:
        print("\nVALIDATION FAILED!", file=sys.stderr)
        sys.exit(1)
    else:
        print("\nGRAPH VALIDATION SUCCESSFUL — ALL INTEGRITY CHECKS PASSED.\n")


if __name__ == "__main__":
    main()

