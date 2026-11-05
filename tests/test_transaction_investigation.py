"""Unit tests for Transaction Investigation and Tools (Module D)."""

import pytest

from src.tools.transaction_tools import (
    get_transaction_record,
    get_full_transaction_profile,
    get_sample_transactions,
)
from src.tools.graph_tools import get_transaction_neighborhood
from src.analytics.transaction_investigation import compile_investigation_dossier


def test_get_sample_transactions():
    """Verify retrieval of sample transaction IDs."""
    illicit_samples = get_sample_transactions(class_label="1", count=3)
    assert len(illicit_samples) == 3
    assert all(isinstance(x, (int, float)) for x in illicit_samples)

    licit_samples = get_sample_transactions(class_label="2", count=3)
    assert len(licit_samples) == 3


def test_get_full_transaction_profile():
    """Verify full transaction profile compilation on real sample transaction."""
    tx_id = 230425980
    profile = get_full_transaction_profile(tx_id)

    assert profile is not None
    assert profile["txId"] == tx_id
    assert "time_step" in profile
    assert "ground_truth_label" in profile
    assert "graph_metrics" in profile
    assert "ml_assessment" in profile
    assert "explainability" in profile

    # Verify graph metrics structure
    gm = profile["graph_metrics"]
    assert "in_degree" in gm
    assert "out_degree" in gm
    assert "pagerank" in gm
    assert "community_id" in gm


def test_get_transaction_neighborhood():
    """Verify directed neighborhood extraction."""
    tx_id = 230425980
    neigh = get_transaction_neighborhood(tx_id, hops=1, max_nodes=20)

    assert "nodes" in neigh
    assert "edges" in neigh
    assert "direct_predecessors_sample" in neigh
    assert "direct_successors_sample" in neigh
    assert any(n["txId"] == tx_id for n in neigh["nodes"])


def test_compile_investigation_dossier():
    """Verify end-to-end investigation dossier compilation."""
    tx_id = 230425980
    dossier = compile_investigation_dossier(tx_id)

    assert "txId" in dossier
    assert "time_step" in dossier
    assert "risk_assessment" in dossier
    assert "graph_metrics" in dossier
    assert "executive_summary" in dossier
    assert isinstance(dossier["executive_summary"], str)
    assert len(dossier["executive_summary"]) > 0


def test_nonexistent_transaction_handling():
    """Verify proper handling when querying an invalid transaction ID."""
    invalid_tx = 99999999999
    profile = get_full_transaction_profile(invalid_tx)
    assert profile is None

    neigh = get_transaction_neighborhood(invalid_tx)
    assert "error" in neigh

    with pytest.raises(KeyError):
        compile_investigation_dossier(invalid_tx)
