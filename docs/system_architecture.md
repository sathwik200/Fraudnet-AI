# FRAUDNET AI — System Architecture Specification

## 1. Executive Architecture Overview

**FRAUDNET AI** is an end-to-end cryptocurrency forensic intelligence and anti-money laundering (AML) analytics platform. The system operates on the Elliptic Bitcoin transaction dataset comprising **203,769 transactions** and **234,355 directed payment edges** spanning **49 discrete two-week time steps**.

The platform couples high-performance topological graph analysis, supervised machine learning with strict chronological validation, explainable AI (XAI) feature attribution, an autonomous multi-step LangGraph agent with deterministic fallback, SQLite case management, pure-Python PDF dossier rendering, and an interactive multi-page Streamlit portal.

---

## 2. Multi-Tiered System Architecture

```mermaid
flowchart TD
    subgraph DataLayer [Data Ingestion & Pipeline Tier]
        RAW[Raw Elliptic CSVs: Features, Classes, Edgelist] --> LOADER[Data Loader & Schema Validator]
        LOADER --> PARQUET[Parquet Storage: transactions.parquet & edges.parquet]
    end

    subgraph GraphLayer [Graph Analytics & Topological Tier]
        PARQUET --> G_BUILD[DiGraph Construction & Verification]
        G_BUILD --> G_METRICS[Degree Centrality, PageRank, WCC, Louvain Communities]
        G_METRICS --> G_PATTERNS[Hub Detection: High Fan-In / Fan-Out / Peel Chains]
        G_PATTERNS --> METRICS_PQ[transaction_metrics.parquet & summaries]
    end

    subgraph MLLayer [Machine Learning & Attribution Tier]
        PARQUET --> SPLIT[Strict Chronological Splitter: Train 1-28, Val 29-34, Test 35-49]
        SPLIT --> FEAT_PIPE[FraudnetFeaturePipeline: Train-Fitted Imputation & Scaling]
        FEAT_PIPE --> TRAIN[Model Comparison: LogisticRegression, HistGradientBoosting, RandomForest]
        TRAIN --> MODEL_BUNDLE[models/fraudnet_model_v1.joblib: Champion RF]
        MODEL_BUNDLE --> XAI[Explainability Engine: Local Deviations & Z-Scores]
    end

    subgraph AgentLayer [Autonomous AI & Forensic Tools Tier]
        G_PATTERNS --> TOOLS[Forensic Tools: Transaction, Graph & Model Services]
        XAI --> TOOLS
        TOOLS --> LANGGRAPH[LangGraph Multi-Step StateGraph Agent]
        LANGGRAPH --> GROQ[Groq Cloud LLM / Deterministic Fallback Engine]
    end

    subgraph PersistenceLayer [Persistence & Audit Tier]
        SQLITE[(SQLite Database: cases, case_transactions, notes, report_history)]
        PDF_GEN[PurePDFDocument 1.4 Binary Dossier Generator]
    end

    subgraph UILayer [Streamlit Portal Interface]
        STREAMLIT[Streamlit Multi-Page Web Application: app.py]
        STREAMLIT --> P1[Executive Dashboard]
        STREAMLIT --> P2[Transaction Investigation]
        STREAMLIT --> P3[Network Topology Explorer]
        STREAMLIT --> P4[Model Performance & ML]
        STREAMLIT --> P5[AI Forensic Assistant]
        STREAMLIT --> P6[Case Management]
        STREAMLIT --> P7[Reports & Archives]
    end

    TOOLS --> STREAMLIT
    LANGGRAPH --> STREAMLIT
    SQLITE <--> STREAMLIT
    PDF_GEN <--> STREAMLIT
```

---

## 3. Component Breakdown

### 3.1 Data Ingestion & Preprocessing Tier
- **Location:** `src/data/`
- **Modules:** `loader.py`, `validator.py`, `preprocessor.py`
- **Output:** `data/processed/transactions.parquet` (203,769 rows × 168 columns) and `data/processed/edges.parquet` (234,355 directed edges).
- **Integrity Guarantees:** Zero fabricated records, preservation of all 157,205 unlabeled ("unknown") transactions, headerless CSV handling, zero cross-column data contamination.

### 3.2 Topological Graph Construction Tier
- **Location:** `src/graph/`
- **Modules:** `build_graph.py`, `export_graph.py`
- **Artifact:** `data/processed/transaction_graph.pkl` (NetworkX `DiGraph`, 203,769 nodes, 234,355 directed edges).
- **Topological Integrity:** Strictly verified acyclic DAG across 49 weakly connected components with exactly zero cross-timestep edges.

### 3.3 Graph Analytics & Network Pattern Engine
- **Location:** `src/analytics/`
- **Modules:** `graph_metrics.py`, `centrality.py`, `community_detection.py`, `network_patterns.py`, `temporal_analysis.py`, `analytics_pipeline.py`
- **Output:** `data/processed/analytics/transaction_metrics.parquet` (203,769 rows × 11 metrics), `temporal_summary.json`, `network_patterns.json`, `community_summary.json`.
- **Topological Indicators:** In-degree, out-degree, total degree, PageRank ($\alpha=0.85$), Louvain community assignment ($Q=0.812$), clustering coefficient, WCC membership, and 99th percentile aggregation and distribution hub detection.

### 3.4 Supervised ML Fraud Risk Detection Tier
- **Location:** `src/ml/`
- **Modules:** `feature_engineering.py`, `data_split.py`, `train.py`, `evaluate.py`, `predict.py`, `explainability.py`, `model_manager.py`
- **Champion Artifact:** `models/fraudnet_model_v1.joblib` (Random Forest, 100 trees, max depth 16, balanced class weights).
- **Validation Discipline:** Strict temporal partitions (Train 1–28, Val 29–34, Test 35–49). Imputer and standard scaler fitted strictly on the training partition.

### 3.5 AI Investigation Agent & Tool Services
- **Location:** `src/agents/`, `src/tools/`
- **Agent Architecture:** Compiled LangGraph `StateGraph` running through `extract_entities` $\rightarrow$ `fetch_profile` $\rightarrow$ `fetch_network_context` $\rightarrow$ `fetch_prediction` $\rightarrow$ `synthesize_forensics`.
- **Groq Integration:** Interfaced with Groq Cloud SDK (`openai/gpt-oss-120b`). When `GROQ_API_KEY` is not present or API connectivity fails, transitions seamlessly to deterministic algorithmic AML synthesis without interruption.

### 3.6 Persistence & Forensic Reporting
- **Location:** `src/database/`, `src/reports/`
- **Database:** Thread-safe SQLite relational database (`data/runtime/fraudnet.db`) storing `cases`, `case_transactions`, `investigation_notes`, and `report_history`.
- **Forensic PDF Generator:** Custom `PurePDFDocument` generating compliant PDF 1.4 binary documents with zero external dependencies (no C-extensions required).

### 3.7 Interactive Streamlit Portal
- **Location:** `app.py`, `src/ui/`
- **Pages:**
  1. Executive Intelligence Dashboard
  2. Transaction Forensic Dossier
  3. Bitcoin Payment Network Explorer
  4. Supervised ML Fraud Detection Engine
  5. AI Forensic Intelligence Assistant
  6. AML Investigation Case Management
  7. Forensic Intelligence Reports & Archives

