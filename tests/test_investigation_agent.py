"""Unit tests for LangGraph AI Investigation Agent (Module E)."""

import pytest

from src.agents.investigation_agent import (
    create_investigation_graph,
    run_investigation,
)


def test_create_investigation_graph():
    """Verify compilation of the LangGraph workflow."""
    graph = create_investigation_graph()
    assert graph is not None
    assert hasattr(graph, "invoke")


def test_run_investigation_with_explicit_tx():
    """Verify executing investigation with explicit transaction ID."""
    tx_id = 230425980
    result = run_investigation(query="Audit this transaction", tx_id=str(tx_id))

    assert result is not None
    assert result["target_tx_id"] == str(tx_id)
    assert result["transaction_profile"] is not None
    assert result["graph_context"] is not None
    assert result["ml_prediction"] is not None
    assert len(result["notes"]) >= 3
    assert "final_report" in result
    assert "Forensic Investigation Dossier" in result["final_report"] or "Executive Summary" in result["final_report"]


def test_run_investigation_parses_tx_from_query():
    """Verify parsing transaction ID from natural language query."""
    query = "Investigate suspicious Bitcoin transaction 230425980 immediately"
    result = run_investigation(query=query)

    assert result["target_tx_id"] == "230425980"
    assert result["transaction_profile"] is not None
    assert "final_report" in result


def test_run_investigation_general_query():
    """Verify agent response for general inquiries without transaction ID."""
    query = "How does FRAUDNET AI detect fraud in Bitcoin transactions?"
    result = run_investigation(query=query)

    assert result is not None
    assert result.get("target_tx_id") is None
    assert "final_report" in result
    assert len(result["final_report"]) > 100

