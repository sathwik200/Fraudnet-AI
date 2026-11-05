"""Unit tests for Graph Analytics Module (Module A)."""

import json
from pathlib import Path
import pytest
import pandas as pd
import networkx as nx

from config.settings import (
    TRANSACTION_METRICS_PATH,
    TEMPORAL_SUMMARY_PATH,
    NETWORK_PATTERNS_PATH,
    COMMUNITY_SUMMARY_PATH,
)
from src.analytics.graph_metrics import compute_degree_metrics
from src.analytics.network_patterns import detect_structural_patterns


def test_transaction_metrics_artifact_exists():
    """Verify that transaction_metrics.parquet exists and has required schema."""
    assert TRANSACTION_METRICS_PATH.exists(), f"Missing {TRANSACTION_METRICS_PATH}"
    df = pd.read_parquet(TRANSACTION_METRICS_PATH)
    assert len(df) == 203769
    expected_cols = {
        "txId", "in_degree", "out_degree", "total_degree",
        "pagerank", "clustering_coeff", "wcc_id", "wcc_size",
        "community_id", "is_aggregation_hub", "is_distribution_hub"
    }
    assert expected_cols.issubset(set(df.columns))


def test_temporal_summary_artifact():
    """Verify that temporal_summary.json exists and covers all 49 time steps."""
    assert TEMPORAL_SUMMARY_PATH.exists()
    with open(TEMPORAL_SUMMARY_PATH, "r") as f:
        data = json.load(f)
    assert data["num_time_steps"] == 49
    assert "timeline" in data
    assert len(data["timeline"]) == 49
    first_step = data["timeline"][0]
    assert first_step["time_step"] == 1
    assert "total_transactions" in first_step
    assert "illicit_count" in first_step


def test_network_patterns_artifact():
    """Verify that network_patterns.json contains valid hub counts."""
    assert NETWORK_PATTERNS_PATH.exists()
    with open(NETWORK_PATTERNS_PATH, "r") as f:
        data = json.load(f)
    assert "counts" in data
    assert "aggregation_hubs_count" in data["counts"]
    assert "distribution_hubs_count" in data["counts"]
    assert data["counts"]["aggregation_hubs_count"] > 0
    assert data["counts"]["distribution_hubs_count"] > 0


def test_community_summary_artifact():
    """Verify community summary structure."""
    assert COMMUNITY_SUMMARY_PATH.exists()
    with open(COMMUNITY_SUMMARY_PATH, "r") as f:
        data = json.load(f)
    assert isinstance(data, list)
    assert len(data) > 0
    first = data[0]
    assert "community_id" in first
    assert "size" in first
    assert first["size"] > 0


def test_compute_degree_metrics_synthetic():
    """Test degree metrics calculation on a controlled directed graph."""
    G = nx.DiGraph()
    G.add_edges_from([(1, 2), (1, 3), (2, 3), (4, 3)])
    df = compute_degree_metrics(G)
    assert len(df) == 4
    # Node 1: in=0, out=2, total=2
    row1 = df.loc[1]
    assert row1["in_degree"] == 0
    assert row1["out_degree"] == 2
    assert row1["total_degree"] == 2

    # Node 3: in=3, out=0, total=3
    row3 = df.loc[3]
    assert row3["in_degree"] == 3
    assert row3["out_degree"] == 0
    assert row3["total_degree"] == 3


def test_identify_hub_patterns_synthetic():
    """Test hub pattern detection with synthetic metrics."""
    df = pd.DataFrame(
        {
            "in_degree": [10, 0, 1, 1],
            "out_degree": [0, 10, 1, 1],
            "total_degree": [10, 10, 2, 2],
            "pagerank": [0.01, 0.01, 0.001, 0.001],
        },
        index=[1, 2, 3, 4],
    )
    res = detect_structural_patterns(df, in_degree_percentile=50.0, out_degree_percentile=50.0)
    assert "counts" in res
    assert res["counts"]["aggregation_hubs_count"] == 1
    assert res["counts"]["distribution_hubs_count"] == 1
