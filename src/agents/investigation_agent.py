"""LangGraph multi-step investigation agent for FRAUDNET AI.
"""

import logging
from typing import Optional

from langgraph.graph import StateGraph, START, END

from src.agents.state import InvestigationState
from src.agents.nodes import (
    extract_entities_node,
    fetch_profile_node,
    fetch_network_context_node,
    fetch_prediction_node,
    synthesize_forensics_node,
)

logger = logging.getLogger("fraudnet.agent")

_COMPILED_GRAPH = None


def create_investigation_graph():
    """Build and compile the multi-step investigation LangGraph workflow."""
    workflow = StateGraph(InvestigationState)

    # Register workflow nodes
    workflow.add_node("extract_entities", extract_entities_node)
    workflow.add_node("fetch_profile", fetch_profile_node)
    workflow.add_node("fetch_network_context", fetch_network_context_node)
    workflow.add_node("fetch_prediction", fetch_prediction_node)
    workflow.add_node("synthesize_forensics", synthesize_forensics_node)

    # Establish linear forensic execution flow
    workflow.add_edge(START, "extract_entities")
    workflow.add_edge("extract_entities", "fetch_profile")
    workflow.add_edge("fetch_profile", "fetch_network_context")
    workflow.add_edge("fetch_network_context", "fetch_prediction")
    workflow.add_edge("fetch_prediction", "synthesize_forensics")
    workflow.add_edge("synthesize_forensics", END)

    return workflow.compile()


def get_investigation_graph():
    """Get or lazily build the cached investigation graph."""
    global _COMPILED_GRAPH
    if _COMPILED_GRAPH is None:
        _COMPILED_GRAPH = create_investigation_graph()
    return _COMPILED_GRAPH


def run_investigation(query: str, tx_id: Optional[str] = None) -> InvestigationState:
    """Execute the full investigation workflow on a query or specific transaction ID.

    Parameters
    ----------
    query : str
        User's prompt or investigation question.
    tx_id : Optional[str]
        Optional explicit transaction ID.

    Returns
    -------
    InvestigationState
        Final state containing extracted entities, profiles, ML risk, and synthesized report.
    """
    graph = get_investigation_graph()

    initial_state: InvestigationState = {
        "query": query,
        "target_tx_id": str(tx_id) if tx_id is not None else None,
        "extracted_entities": {},
        "notes": [],
        "final_report": "",
        "llm_used": False,
        "error": None,
    }

    final_state = graph.invoke(initial_state)
    return final_state

