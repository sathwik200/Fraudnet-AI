# FRAUDNET AI — Cyberpunk UI Redesign & Visual Transformation Report

**Project:** FRAUDNET AI: AI-Powered Cryptocurrency Forensics & Threat Intelligence  
**Document:** Extreme Cyberpunk UI Redesign & Command Centre Architecture  
**Date:** November 5, 2026  
**Status:** Successfully Implemented, Tested (109/109 Tests Passing), and Verified  

---

## 1. Executive Summary & Design Vision

The FRAUDNET AI user interface has undergone a complete visual transformation from a traditional dashboard into an **advanced, futuristic Cyber Intelligence Command Centre**. 

Inspired by high-assurance cybersecurity operations centers (SOCs), military intelligence terminals, and sci-fi holographic tactical displays, the redesign delivers a visually arresting, high-contrast dark environment without compromising the underlying mathematical rigour, dataset integrity, or ML inference performance.

---

## 2. Core Color System & Aesthetic Foundations

The design strictly implements the unified Cyberpunk Color System:

| Color Role | Hex Code | Visual Application |
| :--- | :--- | :--- |
| **Abyss Base** | `#05080D` | Main application background with subtle fine-cyan matrix grid |
| **Deep Cyber Navy** | `#080F18` | Core container background and Plotly plot foundations |
| **Operations Panel** | `#0C1520` | Secondary HUD panels and elevated card surfaces |
| **Surface Accent** | `#111D2A` | Interactive metric tiles and hover state elevations |
| **Neon Cyan** | `#00F5FF` | Primary cyber intelligence lines, glowing borders, active telemetry |
| **Electric Blue** | `#168BFF` | Data flow vectors, secondary metric highlights, directed edges |
| **Cyber Green** | `#00FF9C` | Verified licit classifications, system nominal status indicators |
| **Threat Red** | `#FF3158` | Confirmed illicit classifications, critical risk alerts, alarm dots |
| **Warning Amber** | `#FFB547` | High-risk warning tiers, high-degree unknown hub highlights |
| **Focal Purple** | `#A970FF` | Center focal query transactions, ego origin markers |

---

## 3. Architecture & New UI Components

To maintain clean separation of concerns and avoid brittle inline styling, the design system was structured into three dedicated modules:

### 3.1 `src/ui/theme.py`
- Houses all primary and secondary color constants.
- Exports `apply_cyber_theme()` and `get_cyber_layout_dict()` for Plotly visualizations, enforcing transparent backgrounds, monospaced typography, and cyber-grid line aesthetics.

### 3.2 `src/ui/styles.py`
- Ingests Google Fonts (`Rajdhani`, `JetBrains Mono`, `Chakra Petch`).
- Injects full CSS reset: Obsidian background with cyan coordinate matrix grid (`36px × 36px`).
- Custom scrollbar with glowing cyan thumb.
- Futuristic radio buttons and tab navigation with top neon border highlights.
- Keyframe animations: `@keyframes pulseGlow` for live operational indicator lights.
- Cut-corner HUD brackets (`.cyber-card::before`, `.cyber-card::after`).

### 3.3 `src/ui/components.py`
- `render_command_header(module_title)`: Top HUD command header featuring live UTC time, `SYSTEM NOMINAL` status badge, active model descriptor, and Groq/Deterministic mode pill.
- `render_hero_banner(title, subtitle, quote, telemetry)`: Futuristic command hero banner with corner tech brackets.
- `render_cyber_metric(title, value, subtitle, color, icon)`: Metric cards with customized neon accents and glow shadows.
- `render_risk_gauge_hud(probability, risk_category)`: Cyberpunk risk meter HUD with illuminated progress bar and standardized threat tier badges.
- `render_terminal_prompt(command, output)`: Monospaced terminal emulator container.

---

## 4. Detailed Screen & Page Redesign Breakdown

### 4.1 Global Application Shell (`app.py`)
- **Cyber Sidebar:** Styled with glowing cyan emblem `🛡️ FRAUDNET AI`, pulse indicator, and monospaced module navigation (`01 // COMMAND DASHBOARD`, `02 // TRANSACTION FORENSICS`, etc.).
- **System Telemetry Module:** Displays live engine health, model version (`RandomForest v1.0`), graph scale (203k vertices, 234k flows, 49 WCCs), and encryption status.
- **Target Presets:** One-click tactical quick-pick buttons for immediate evaluation.

### 4.2 Page 1: Executive Dashboard (`src/ui/dashboard.py`)
- **Hero Command Section:** Prominent title, mission directive, and live network telemetry strip.
- **6 Futuristic Metric Tiles:** Total Transactions (203,769), Directed Edges (234,355), Illicit Labeled (4,545), Licit Labeled (42,019), Unknown Pool (157,205), and Active Time Steps (49).
- **Temporal Surveillance Chart:** Plotly area chart with cyan glow for overall transaction volume and red diamond markers for illicit surges.
- **Donut Chart:** Cyber composition breakdown distinguishing unknown pool, licit, and illicit transactions.
- **Threat Intelligence & Model Status Panel:** Live test-set metrics (PR-AUC: 0.7874, ROC-AUC: 0.9384, Illicit F1: 0.7018, Recall: 0.7378).
- **Topological Surveillance Audit Terminal:** Live terminal logging 49 WCC components, 2,042 aggregation hubs, 2,040 distribution hubs, and Louvain modularity stats.

### 4.3 Page 2: Transaction Forensics Terminal (`src/ui/transaction_search.py`)
- **Monospaced Target Query Bar:** Prominent search bar with placeholder `ENTER TRANSACTION HASH / ID...`.
- **Target Profile Card:** Monospaced identifiers, ground-truth label in red/green/slate, Louvain community cluster, and WCC component.
- **Risk Assessment HUD:** Illuminated risk gauge displaying continuous illicit probability percentage, calibrated threshold mark (0.50), and tier badge.
- **Topological KPI Tiles:** In-degree, out-degree, total degree, PageRank, and clustering coefficient.
- **Feature Attribution Panels:** Plotly horizontal bar charts and dataframes displaying Z-score deviations for risk-elevating and risk-mitigating features.
- **Counterparty Flows:** Tabular predecessor inputs and successor outputs with directional vectors (`tx_X ➔ tx_Y`).
- **Tactical Actions:** Direct attachment to SQLite cases and instant PDF dossier download.

### 4.4 Page 3: Network Topology Explorer (`src/ui/network_visualization.py`)
- **Signature Visual Feature:** Interactive 2D graph canvas with NetworkX spring layout and Plotly WebGL rendering.
- **Color Encoding:**
  - `PURPLE Diamond`: Center focal query transaction (`txId`).
  - `RED Circle`: Confirmed illicit transactions (Class 1).
  - `GREEN Circle`: Confirmed licit transactions (Class 2).
  - `AMBER Circle`: High-degree unknown hub nodes.
  - `CYAN Circle`: Standard relay nodes.
  - `CYAN GLOW Line`: Directed payment cash-flow vectors.
- **HUD Legend:** Clean monospaced legend bar below canvas explaining color mappings.
- **Flow Ledgers:** Formatted tables of incoming fund sources and outgoing recipient disbursements.

### 4.5 Page 4: Machine Learning Intelligence (`src/ui/model_dashboard.py`)
- **Champion Architecture Card:** Random Forest Classifier [v1.0.0-PROD] banner with validation PR-AUC (0.9852) and calibrated decision threshold (0.50).
- **Out-of-Time Test Set Metrics:** PR-AUC (0.7874), ROC-AUC (0.9384), Illicit F1 (0.7018), Recall (0.7378), Accuracy (0.9593).
- **3-Model Comparison Benchmark:** Cyber-styled comparative table contrasting Random Forest against HistGradientBoosting and Logistic Regression.
- **Confusion Matrix Heatmap:** Custom cyber blue-to-cyan heatmap displaying 10,229 TN, 394 FP, 285 FN, and 802 TP.
- **Global Gini Feature Importance:** Horizontal bar chart highlighting the top 12 predictive features (e.g. `local_feature_1`, `local_feature_2`, `agg_feature_1`).
- **Model Intelligence Specification:** Full documentation of temporal split boundaries and zero-leakage safeguards.

### 4.6 Page 5: AI Investigation Agent Console (`src/ui/ai_assistant.py`)
- **AI Console Header:** Live operational status and Groq Cloud LLM / Deterministic engine pill.
- **Tactical Quick Prompts:** 4 one-click prompts for immediate transaction audits and AML pattern explanations.
- **Chat Conversation Panel:** High-contrast user and AI bubbles with monospaced transaction hashes.
- **Autonomous Reasoning Chain Drawer:** Expandable telemetry breakdown showing intermediate LangGraph steps (`[STEP 01]`, `[STEP 02]`, etc.).
- **Deterministic Fallback:** Clean informational notice when running offline without external cloud credentials.

### 4.7 Page 6: Case Operations (`src/ui/case_management.py`)
- **Case Registry Vault:** Incident ledger tracking Case IDs (`CASE-0001`), priorities, status, and attached transaction counts.
- **Initialize Case Form:** Form for opening new investigations with threat priority tiers and investigator signatures.
- **Evidence Audit & Logs:** Selected case detail view with status changer, transaction detach actions, and chronological terminal-style investigator logs.

### 4.8 Page 7: Report Vault (`src/ui/report_viewer.py`)
- **Instant Dossier Compiler:** On-demand PDF compiler generating court-ready PDF 1.4 documents.
- **Historical Report Vault:** Table of certified archived reports with timestamp, target transaction ID, and instant download buttons.

---

## 5. Strict Functionality Preservation

Throughout the visual transformation, the underlying system architecture remained untouched:
- **Zero Dataset Modifications:** Original CSVs and Parquet files (`transactions.parquet`, `edges.parquet`) were strictly untouched.
- **Zero Graph Alterations:** The 203,769-node, 234,355-edge directed DAG in `data/processed/transaction_graph.pkl` was preserved.
- **Zero ML Re-training:** The champion Random Forest model bundle (`models/fraudnet_model_v1.joblib`) was preserved without modification.
- **Zero Database Schema Changes:** SQLite tables (`cases`, `case_transactions`, `investigation_notes`, `report_history`) remain fully compatible.
- **Zero Test Weakening:** All existing test files and assertions remain intact.

---

## 6. Test Suite Verification (109 / 109 Passed)

Executed with the project interpreter:
```bash
/Users/sathwikm/Documents/FRAUDNET-AI/.venv/bin/python -m pytest tests/ -v
```

**Results:**
- `tests/test_data_pipeline.py`: **56 / 56 PASSED**
- `tests/test_graph_construction.py`: **24 / 24 PASSED**
- `tests/test_graph_analytics.py`: **6 / 6 PASSED**
- `tests/test_ml_pipeline.py`: **6 / 6 PASSED**
- `tests/test_transaction_investigation.py`: **5 / 5 PASSED**
- `tests/test_database.py`: **6 / 6 PASSED**
- `tests/test_report_generator.py`: **2 / 2 PASSED**
- `tests/test_investigation_agent.py`: **4 / 4 PASSED**
- **TOTAL: 109 / 109 PASSED (100% Pass Rate in 8.57 seconds)**

---

## 7. Known Limitations & Operating Notes

1. **Local Font Fallbacks:** Google Web Fonts (`Rajdhani`, `JetBrains Mono`, `Chakra Petch`) are fetched from Google Fonts CDN. In offline environments without external internet access, the design falls back to standard system monospaced and sans-serif fonts (`SF Mono`, `Consolas`, `Menlo`, `-apple-system`).
2. **Bounded Subgraph Rendering:** Network Explorer limits rendering to 15–80 nodes (1-hop or 2-hop radius) to maintain 60 FPS performance on standard laptop hardware, preventing browser crashes on the 203,769-node global graph.

