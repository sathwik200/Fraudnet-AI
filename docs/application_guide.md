# FRAUDNET AI — User Application Guide & Demonstration Manual

## 1. Launching the Application

Ensure the project virtual environment is active, then launch Streamlit:

```bash
/Users/sathwikm/Documents/FRAUDNET-AI/.venv/bin/streamlit run app.py
```

The application opens automatically in your browser at `http://localhost:8501`.

---

## 2. Navigating the 7 Core Pages

### Page 1: 📊 Executive Dashboard
- **Purpose:** Macro-level cryptocurrency intelligence overview.
- **Key Features:**
  - Metric cards showing 203,769 total transactions, 234,355 directed edges, and 4,545 illicit transactions.
  - Interactive Plotly chart showing transaction volume and illicit surge trends across time steps 1 to 49.
  - Donut chart depicting ground truth class distribution (Unknown vs Licit vs Illicit).
  - Graph topology summary (Louvain communities, aggregation hubs, distribution hubs).

### Page 2: 🔍 Transaction Investigation
- **Purpose:** In-depth forensic dossier on any individual transaction.
- **Workflow:**
  1. Click one of the preset quick buttons (e.g. `🔴 High-Risk Illicit #1 (230425980)`) or enter any transaction ID.
  2. View ground truth label, ML fraud probability score, and color-coded risk badge.
  3. Inspect in-degree, out-degree, PageRank, and community ID.
  4. Explore the **Risk-Elevating Drivers** table to see which features pushed the transaction into high risk.
  5. Click **Attach Transaction to Case** to link it to an active AML case.
  6. Click **Download PDF Dossier** to download an official forensic report.

### Page 3: 🕸️ Network Topology Explorer
- **Purpose:** Interactive 2D visualization of payment flows.
- **Workflow:**
  1. Select focal transaction (defaults to active transaction).
  2. Choose ego radius (1-hop or 2-hop) and node budget.
  3. Explore interactive graph:
     - Focal node in amber
     - Illicit nodes in red
     - Licit nodes in green
     - Unknown nodes in slate
  4. Hover over any node to view degrees, time step, and verified label.
  5. Inspect the incoming predecessor and outgoing successor lists below the graph.

### Page 4: 📈 Model Performance & ML
- **Purpose:** Validation benchmark and out-of-time test set evaluation.
- **Key Features:**
  - Test set metrics on steps 35–49: Illicit F1: 0.7018, PR-AUC: 0.7874, ROC-AUC: 0.9384, Accuracy: 0.9593.
  - 3-Model comparison benchmark table (Random Forest vs HistGradientBoosting vs Logistic Regression).
  - Test set Confusion Matrix heatmap ($10,229$ TN, $394$ FP, $285$ FN, $802$ TP).
  - Top 12 Global Feature Importances bar chart.
  - Temporal validation methodology documentation.

### Page 5: 🤖 AI Forensic Assistant
- **Purpose:** Conversational investigations powered by LangGraph and Groq Cloud.
- **Workflow:**
  1. Click quick prompt or enter question: `Investigate transaction 230425980`.
  2. Expand **Autonomous Graph Execution Steps** to observe intermediate tool calls (entity extraction, profile fetch, ego graph, ML inference).
  3. Review comprehensive Markdown investigation report with typologies and compliance recommendations.
  4. *Note:* If Groq API key is not present, deterministic fallback generates the report algorithmically.

### Page 6: 📁 Case Management
- **Purpose:** SQLite-backed audit registry for AML investigators.
- **Workflow:**
  1. **Case Registry:** View all cases, priorities, and attached transaction counts.
  2. **Open New Case:** Create a case with title, description, priority, and lead investigator.
  3. **Case Audit & Evidence:** Select a case, update status (Open, In Progress, Closed), view attached transactions, add new transactions, and log investigator notes.

### Page 7: 📄 Reports & Dossiers
- **Purpose:** Generate and download official forensic PDF reports.
- **Workflow:**
  1. Enter transaction ID and investigator name.
  2. Click **Compile & Certify Forensic Report** to build a PDF 1.4 document.
  3. Download the PDF directly.
  4. Access past generated reports in the Historical Report Vault.

---

## 3. Curated Transaction IDs for Demonstration

| Category | Transaction ID | Time Step | Ground Truth | Expected ML Risk Tier |
| :--- | :---: | :---: | :---: | :---: |
| **Confirmed Illicit** | `230425980` | Step 1 | Illicit (Class 1) | Moderate / High |
| **Confirmed Illicit** | `232438397` | Step 1 | Illicit (Class 1) | High / Critical |
| **Confirmed Licit** | `232532458` | Step 1 | Licit (Class 2) | Low |
| **Confirmed Licit** | `232819818` | Step 1 | Licit (Class 2) | Low |
| **High-Risk Unknown** | `232344069` | Step 1 | Unknown | Model Evaluated |

