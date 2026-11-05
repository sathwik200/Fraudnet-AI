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
4. When evaluating AML typologies, adhere strictly to evidence:
   - High fan-in aggregation requires high fan-in ratio and verified hub concentration.
   - High fan-out distribution requires high fan-out ratio and verified disbursement.
   - 1-in / 1-out transfers are simple sequential transfers; do not claim layering without off-chain proof.
   - If topological evidence is ambiguous or low-degree, you MUST explicitly state: "Insufficient evidence to determine transaction typology."
5. Distinguish between Ground Truth labels and ML Model Predictions. Emphasize that dataset labels are historical research classifications from the Elliptic dataset and do not independently establish criminal guilt.
6. Provide responsible compliance recommendations: recommend enhanced human analyst review and independent blockchain verification. NEVER recommend automated freezing of funds or automated SAR filings.
"""

def build_investigation_prompt(
    query: str,
    tx_id: str,
    profile: Dict[str, Any],
    graph_context: Dict[str, Any],
    ml_prediction: Dict[str, Any],
) -> str:
    """Construct an investigation prompt integrating all forensic evidence."""
    pred_count = graph_context.get("direct_predecessors_count", len(graph_context.get("predecessors", [])))
    succ_count = graph_context.get("direct_successors_count", len(graph_context.get("successors", [])))
    metrics = profile.get("graph_metrics", {})

    prompt = f"""INVESTIGATION REQUEST:
User Question / Directive: {query}
Target Transaction ID: {tx_id}

--- EVIDENCE DOSSIER ---

1. TRANSACTION PROFILE:
- Time Step: {profile.get('time_step', 'Unknown')} (Temporal Partition)
- Ground Truth Label: {profile.get('ground_truth_label', 'Unknown')} (Historical Elliptic Research Label)
- Global In-Degree: {metrics.get('in_degree', profile.get('in_degree', 'N/A'))}
- Global Out-Degree: {metrics.get('out_degree', profile.get('out_degree', 'N/A'))}
- Total Degree: {metrics.get('total_degree', profile.get('degree', 'N/A'))}
- PageRank Score: {metrics.get('pagerank', profile.get('pagerank', 'N/A'))}
- Community ID: {metrics.get('community_id', profile.get('community_id', 'N/A'))}
- Aggregation Hub: {metrics.get('is_aggregation_hub', False)}
- Distribution Hub: {metrics.get('is_distribution_hub', False)}

2. GRAPH TOPOLOGY CONTEXT:
- Global Direct Predecessors (In-flow): {pred_count}
- Global Direct Successors (Out-flow): {succ_count}
- Bounded Subgraph Rendered Nodes: {len(graph_context.get('nodes', []))}
- Bounded Subgraph Rendered Edges: {len(graph_context.get('edges', []))}
- Exploration Horizon: {graph_context.get('hops', 1)} hop(s)
- Direct Predecessor IDs (Sample): {graph_context.get('direct_predecessors_sample', graph_context.get('predecessors', []))[:5]}
- Direct Successor IDs (Sample): {graph_context.get('direct_successors_sample', graph_context.get('successors', []))[:5]}

3. SUPERVISED ML RISK PREDICTION:
- Predicted Label: {ml_prediction.get('predicted_label', 'Unknown')}
- Illicit Probability: {ml_prediction.get('illicit_probability', 0.0):.4f} ({ml_prediction.get('illicit_probability', 0.0) * 100:.1f}%)
- Risk Category: {ml_prediction.get('risk_category', 'Unknown')}
- Attribution Methodology: Standardized Feature Deviation (Z-score) × Model Gini Impurity Importance
- Top Risk-Elevating Drivers:
{json.dumps(ml_prediction.get('top_risk_elevating', profile.get('explainability', {}).get('top_risk_elevating', [])), indent=2)}
- Top Risk-Mitigating Drivers:
{json.dumps(ml_prediction.get('top_risk_mitigating', profile.get('explainability', {}).get('top_risk_mitigating', [])), indent=2)}

--- INSTRUCTIONS FOR INVESTIGATOR ---
Provide a comprehensive, professional Forensic Investigation Report structured with:
- ## 1. Executive Summary & Risk Rating
- ## 2. Network Topology & Cash Flow Dynamics (Distinguish global partition degrees from bounded ego-subgraph metrics)
- ## 3. Machine Learning Attribution & Feature Anomalies
- ## 4. AML Typology Assessment (Assign a typology ONLY if supported by concrete graph observations; otherwise state 'Insufficient evidence to determine transaction typology')
- ## 5. Responsible Compliance Recommendations (Recommend human analyst review and independent verification; no automated freezing)
"""
    return prompt


def build_general_query_prompt(query: str) -> str:
    """Prompt for general queries when no specific transaction is queried."""
    return f"""The user asked a cryptocurrency forensic intelligence question:
"{query}"

Please answer authoritatively as FRAUDNET AI, covering Bitcoin transaction networks, graph analytics (PageRank, degree distributions, community detection), machine learning for AML fraud detection, or dataset mechanics (such as the Elliptic Bitcoin dataset with 203,769 transactions across 49 time steps).
"""

