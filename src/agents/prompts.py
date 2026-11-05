"""Prompt templates and system guidelines for the FRAUDNET AI agent.
"""

import json
from typing import Any, Dict

SYSTEM_INVESTIGATION_PROMPT = """You are FRAUDNET AI, a senior cryptocurrency forensic investigator and Anti-Money Laundering (AML) intelligence specialist.
You analyze Bitcoin transactions from the Elliptic dataset using graph topology, supervised machine learning risk attribution, and transaction feature profiles.

When conducting investigations:
1. Maintain rigorous, forensic objectivity. Avoid speculative claims not supported by evidence.
2. Formulate your findings clearly: Executive Summary, Network Topology Analysis, ML Risk Assessment, Identified Typologies, and Recommended Action.
3. Reference concrete transaction metrics: in-degree, out-degree, PageRank, Louvain community, and local feature anomalies.
4. When classifying money-laundering behavior, consider patterns such as:
   - High fan-in aggregation (dark market consolidation)
   - High fan-out distribution (dispersal / peeling chains)
   - Pass-through layering (rapid intermediary relay)
5. Distinguish between Ground Truth labels and ML Model Predictions. Note if the ground truth is "unknown".
6. Provide concrete next steps for compliance / forensic auditors.
"""

def build_investigation_prompt(
    query: str,
    tx_id: str,
    profile: Dict[str, Any],
    graph_context: Dict[str, Any],
    ml_prediction: Dict[str, Any],
) -> str:
    """Construct an investigation prompt integrating all forensic evidence."""
    prompt = f"""INVESTIGATION REQUEST:
User Question / Directive: {query}
Target Transaction ID: {tx_id}

--- EVIDENCE DOSSIER ---

1. TRANSACTION PROFILE:
- Time Step: {profile.get('time_step', 'Unknown')}
- Ground Truth Label: {profile.get('label', 'Unknown')}
- Total Degree: {profile.get('degree', 'N/A')} (In-Degree: {profile.get('in_degree', 'N/A')}, Out-Degree: {profile.get('out_degree', 'N/A')})
- PageRank Score: {profile.get('pagerank', 'N/A')}
- Community ID: {profile.get('community_id', 'N/A')}
- Network Role: {profile.get('network_role', 'Standard')}

2. GRAPH TOPOLOGY CONTEXT:
- Total Direct Predecessors (In-flow): {len(graph_context.get('in_edges', []))}
- Total Direct Successors (Out-flow): {len(graph_context.get('out_edges', []))}
- Subgraph Node Count: {graph_context.get('node_count', 'N/A')}
- Subgraph Edge Count: {graph_context.get('edge_count', 'N/A')}
- Neighboring Transaction IDs (Sample): {graph_context.get('nodes', [])[:8]}

3. SUPERVISED ML RISK PREDICTION:
- Predicted Class: {ml_prediction.get('predicted_class', 'Unknown')}
- Illicit Probability: {ml_prediction.get('probability', 0.0):.4f} ({ml_prediction.get('probability', 0.0) * 100:.1f}%)
- Risk Category: {ml_prediction.get('risk_category', 'Unknown')}
- Top Local Risk Feature Drivers:
{json.dumps(ml_prediction.get('top_features', []), indent=2)}

--- INSTRUCTIONS FOR INVESTIGATOR ---
Provide a comprehensive, professional Forensic Investigation Report structured with:
- ## Executive Summary & Risk Rating
- ## Network Topology & Cash Flow Dynamics
- ## Machine Learning Attribution & Feature Anomalies
- ## AML Typology Assessment
- ## Actionable Recommendations for Compliance
"""
    return prompt


def build_general_query_prompt(query: str) -> str:
    """Prompt for general queries when no specific transaction is queried."""
    return f"""The user asked a cryptocurrency forensic intelligence question:
"{query}"

Please answer authoritatively as FRAUDNET AI, covering Bitcoin transaction networks, graph analytics (PageRank, degree distributions, community detection), machine learning for AML fraud detection, or dataset mechanics (such as the Elliptic Bitcoin dataset with 203,769 transactions across 49 time steps).
"""

