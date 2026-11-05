"""State definition for FRAUDNET AI LangGraph investigation agent.
"""

from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class InvestigationState(TypedDict, total=False):
    """Workflow state passed through the LangGraph investigation agent."""
    query: str
    target_tx_id: Optional[str]
    extracted_entities: Dict[str, Any]
    transaction_profile: Optional[Dict[str, Any]]
    graph_context: Optional[Dict[str, Any]]
    ml_prediction: Optional[Dict[str, Any]]
    notes: List[str]
    final_report: str
    llm_used: bool
    error: Optional[str]

