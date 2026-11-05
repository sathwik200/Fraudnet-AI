# FRAUDNET AI — Environment & Processed Data Verification Report

> **Platform:** FRAUDNET AI (Cryptocurrency Transaction Investigation Platform)  
> **Verification Date:** 2026-11-05  
> **Phase:** Pre-Graph Construction & Baseline Check  
> **Overall Status:** Processed Data **PASSED** (100%) | Environment **PARTIALLY READY** (Core libraries present; ML/LLM packages pending installation)

---

## 1. Environment Verification

### 1.1 Python Interpreter & Virtual Environment

| Metric | Details | Status |
| :--- | :--- | :---: |
| **Active Python Binary** | `/usr/local/bin/python3` | ✅ Active |
| **Python Version** | `Python 3.14.4` (Clang 17.0.0, 64-bit) | ✅ Supported |
| **Virtual Environment (`.venv`)** | Present on disk at `/Users/sathwikm/Documents/FRAUDNET-AI/.venv` (Python 3.9.6 stub). However, the shell session is currently running using the system Python 3.14.4 interpreter (`VIRTUAL_ENV` variable is unset). | ⚠️ Inactive in current session |
| **Pip Version** | `pip 26.0.1` | ✅ Active |

---

### 1.2 Package Inventory (Audited List)

The 13 required dependencies were inspected directly in the active Python runtime without modifying any files or installing new packages.

| Package | Category | Status | Installed Version | Notes |
| :--- | :--- | :---: | :---: | :--- |
| `pandas` | Data Processing | **INSTALLED** | `2.3.3` | Used for tabular manipulation |
| `numpy` | Numerical Computing | **INSTALLED** | `2.5.4` | Array computing backend |
| `pyarrow` | Storage / Parquet | **INSTALLED** | `23.0.1` | Parquet serialization engine |
| `networkx` | Graph Algorithms | **INSTALLED** | `3.7` | Graph construction & centrality analysis |
| `scikit-learn` | Machine Learning | **MISSING** | — | Required for baselines (Random Forest, Logistic Regression) |
| `scipy` | Scientific Computing | **MISSING** | — | Dependency for advanced sparse matrix ops & scientific algorithms |
| `plotly` | Visualization | **INSTALLED** | `7.1.0` | Interactive graph & metric plotting |
| `streamlit` | UI / Dashboard | **INSTALLED** | `1.55.0` | Investigation portal application frontend |
| `python-dotenv` | Configuration | **INSTALLED** | `1.2.2` | `.env` environment variable management |
| `groq` | LLM SDK | **MISSING** | — | High-speed LLM inference API client |
| `langchain-groq` | Agent Framework | **MISSING** | — | LangChain integration for Groq models |
| `langgraph` | Agent Workflows | **INSTALLED** | `1.1.3` | Multi-agent state graph orchestration |
| `pytest` | Testing Framework | **INSTALLED** | `9.1.1` | Automated testing suite |

#### Summary of Environment Check
- **Installed Packages (9/13):** `pandas`, `numpy`, `pyarrow`, `networkx`, `plotly`, `streamlit`, `python-dotenv`, `langgraph`, `pytest`.
- **Missing Packages (4/13):** `scikit-learn`, `scipy`, `groq`, `langchain-groq`.
- *Action item for future phase:* Install missing packages before initiating Machine Learning training and Agent orchestration phases (no installation performed during this verification task as instructed).

---

## 2. Processed Dataset Verification

The files generated during the preprocessing stage were audited to verify completeness, relational fidelity, and schema consistency.

### 2.1 File Inventory

| File Path | Format | Size | Records | Integrity / Health |
| :--- | :---: | :---: | :---: | :---: |
| `data/processed/transactions.parquet` | Apache Parquet (Snappy) | 90.16 MB | 203,769 | ✅ Intact |
| `data/processed/edges.parquet` | Apache Parquet (Snappy) | 2.34 MB | 234,355 | ✅ Intact |
| `data/processed/dataset_summary.json` | JSON | 5.7 KB | N/A | ✅ Intact |

---

### 2.2 Deep Validation Matrix

| Verification Check | Target / Expected Value | Actual Value | Match |
| :--- | :--- | :--- | :---: |
| **Transaction Record Count** | `203,769` | `203,769` | ✅ |
| **Unique Transaction IDs** | `203,769` (0 duplicates) | `203,769` (0 duplicates) | ✅ |
| **Edge Record Count** | `234,355` | `234,355` | ✅ |
| **Edge Endpoints (`txId1`, `txId2`)** | `['txId1', 'txId2']` | `['txId1', 'txId2']` | ✅ |
| **Orphan Edge Endpoints** | `0` (all endpoints exist in transactions) | `0` (src orphans: 0, dst orphans: 0) | ✅ |
| **Temporal Discretization** | `49` discrete time steps | `49` time steps (range: `[1, 49]`) | ✅ |
| **Local Feature Dimensions** | `93` columns (`local_feature_1`..`93`) | `93` columns | ✅ |
| **Aggregate Feature Dimensions** | `72` columns (`agg_feature_1`..`72`) | `72` columns | ✅ |
| **Total Numeric Features** | `165` columns | `165` columns | ✅ |
| **Total Transaction Columns** | `168` (`txId`, `time_step`, 165 feats, `label`) | `168` columns | ✅ |
| **Label Leakage Prevention** | `label` isolated from numeric features | `label` not in feature sets | ✅ |
| **Missing / Null Values** | `0` null values across all columns | `0` null values | ✅ |
| **Class Label: Illicit (`1`)** | `4,545` (2.23%) | `4,545` (2.23%) | ✅ |
| **Class Label: Licit (`2`)** | `42,019` (20.62%) | `42,019` (20.62%) | ✅ |
| **Class Label: Unknown** | `157,205` (77.15%) | `157,205` (77.15%) | ✅ |
| **Unknown Label Invariance** | Unchanged (never converted to licit/0) | Exact preservation confirmed | ✅ |

---

## 3. Discovered Inconsistencies & Errors

1. **No Data Inconsistencies:** The processed dataset exhibits 100% adherence to the Elliptic specification. Zero orphan edges, zero nulls, and zero duplicate nodes were found.
2. **Virtual Environment Inactive:** A virtual environment directory exists (`.venv`), but commands run in standard system Python (`/usr/local/bin/python3`). While the core data processing and graph libraries are installed, activating or updating `.venv` should be aligned prior to package installations.
3. **Missing ML & Agent Dependencies:** `scikit-learn`, `scipy`, `groq`, and `langchain-groq` are not yet installed in the active environment. They will need to be installed in subsequent steps when ML model training and agent building begin.

---

## 4. Verification Verdict

- **Environment Verification:** **PARTIALLY READY** (9 installed, 4 missing; data & graph tooling operational).
- **Processed Data Verification:** **PASSED** (100% compliant across all 16 integrity metrics).
- Ready to proceed to graph construction when directed.

