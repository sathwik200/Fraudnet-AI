# FRAUDNET AI — Multi-Step AI Agent & LangGraph Workflow

## 1. Agent Architecture & Design Objectives

The **FRAUDNET AI Autonomous Investigation Agent** is built on LangGraph to execute systematic, multi-step forensic investigations on Bitcoin transactions.

Key Engineering Principles:
1. **Tool-Assisted Evidence Gathering:** The agent never hallucinates transaction profiles or graph metrics; every metric is retrieved via deterministic internal tools.
2. **Deterministic Fallback Guarantees:** When the Groq Cloud API key is unavailable, expired, or network-blocked, the agent executes an algorithmic AML synthesis fallback with zero application disruption.
3. **Audit Trail Logging:** Every node in the execution graph appends structured observation notes to `state["notes"]`, providing complete transparency into the agent's reasoning.

---

## 2. State Machine Specification

The agent passes a strongly typed `InvestigationState` TypedDict through the pipeline:

```python
class InvestigationState(TypedDict, total=False):
    query: str                       # User prompt or question
    target_tx_id: Optional[str]      # Parsed or explicit numeric transaction ID
    extracted_entities: Dict[str, Any] # Extracted entity mapping
    transaction_profile: Optional[Dict[str, Any]] # 165 features + labels + time step
    graph_context: Optional[Dict[str, Any]]       # 1-hop / 2-hop ego subgraph
    ml_prediction: Optional[Dict[str, Any]]       # RF probability + risk tier
    notes: List[str]                 # Execution audit log
    final_report: str                # Forensic Markdown investigation dossier
    llm_used: bool                   # True if Groq LLM generated; False if deterministic
    error: Optional[str]             # Error message if node failed
```

---

## 3. Workflow Graph Topology

```mermaid
flowchart LR
    START([START]) --> E[extract_entities]
    E --> P[fetch_profile]
    P --> G[fetch_network_context]
    G --> M[fetch_prediction]
    M --> S[synthesize_forensics]
    S --> END([END])
```

### Node Descriptions:

1. **`extract_entities` Node:**
   - Parses the user's natural language input using regular expressions and heuristics.
   - Extracts numeric transaction identifiers (e.g. `230425980`) or intent.
2. **`fetch_profile` Node:**
   - Calls `src.tools.transaction_tools.get_full_transaction_profile(tx_id)`.
   - Retrieves time step, verified ground-truth label, and graph metrics from Parquet storage.
3. **`fetch_network_context` Node:**
   - Calls `src.tools.graph_tools.get_transaction_neighborhood(tx_id, hops=1, max_nodes=50)`.
   - Extracts direct upstream predecessors, direct downstream successors, and ego topology.
4. **`fetch_prediction` Node:**
   - Evaluates the transaction through the Champion Random Forest model bundle.
   - Extracts illicit probability, risk category, and local z-score feature attribution drivers.
5. **`synthesize_forensics` Node:**
   - **Mode A (Groq Online):** Calls `ChatGroq(model_name="llama-3.3-70b-versatile")` with the `SYSTEM_INVESTIGATION_PROMPT` and structured evidence dossier.
   - **Mode B (Deterministic Fallback):** Assembles a structured Markdown investigation report categorizing AML typologies (aggregation, distribution, pass-through relay), local feature drivers, and regulatory recommendations.

