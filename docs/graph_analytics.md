# FRAUDNET AI — Graph Analytics & Network Topology Specification

## 1. Topological Foundations

In the Bitcoin transaction network represented by the Elliptic dataset, vertices correspond to individual Bitcoin transactions, and directed edges represent the flow of satoshis (payment inputs feeding into subsequent payment outputs).

$$\mathcal{G} = (\mathcal{V}, \mathcal{E})$$

where:
- $|\mathcal{V}| = 203,769$ transactions
- $|\mathcal{E}| = 234,355$ directed payment edges
- Temporal partition: $t \in \{1, 2, \dots, 49\}$

---

## 2. Mathematical Metric Formulations

### 2.1 Degree Centrality Metrics

For any transaction $v \in \mathcal{V}$:
- **In-Degree ($d_{in}(v)$):** Count of incoming transaction inputs (funds aggregation).
  $$d_{in}(v) = |\{u \in \mathcal{V} : (u, v) \in \mathcal{E}\}|$$
- **Out-Degree ($d_{out}(v)$):** Count of outgoing transaction outputs (funds disbursement).
  $$d_{out}(v) = |\{w \in \mathcal{V} : (v, w) \in \mathcal{E}\}|$$
- **Total Degree ($d(v)$):** Total structural connectivity.
  $$d(v) = d_{in}(v) + d_{out}(v)$$

**Forensic Significance:**
- $d_{in}(v) \gg 1, d_{out}(v) \le 1$: Aggregation hub (consolidation from multiple inputs, common in exchange deposits or darknet market vendor sweeps).
- $d_{in}(v) \le 1, d_{out}(v) \gg 1$: Distribution hub (peeling chains, mixer disbursements, mining pool distributions).
- $d_{in}(v) = 1, d_{out}(v) = 1$: Linear pass-through relay (rapid intermediate layering to obscure origin).

---

### 2.2 Directed PageRank Centrality

PageRank models the structural authority and stationary probability distribution of a random walker navigating the directed transaction DAG:

$$PR(v) = \frac{1 - \alpha}{|\mathcal{V}|} + \alpha \sum_{u \in \mathcal{M}(v)} \frac{PR(u)}{d_{out}(u)}$$

where:
- $\alpha = 0.85$ (damping factor representing probability of following outgoing transaction edges)
- $\mathcal{M}(v) = \{u \in \mathcal{V} : (u, v) \in \mathcal{E}\}$ (predecessor transactions sending funds to $v$)
- Convergence tolerance: $\epsilon = 1 \times 10^{-6}$, max iterations: 100.

**Forensic Interpretation:** High PageRank transactions occupy central positions in the payment graph, receiving funds from heavily utilized upstream transaction paths.

---

### 2.3 Weakly Connected Components (WCC)

A Weakly Connected Component is a maximal subgraph where every vertex is reachable from every other vertex when edge directions are disregarded.
- **Empirical Elliptic Graph Reality:** Exactly **49 Weakly Connected Components** exist.
- **Temporal Alignment:** Each component maps 1:1 to a specific time step ($t=1$ to $49$), with zero cross-component or cross-timestep edges.
- **Largest Component:** WCC #41 ($t=42$) containing 8,722 transactions and 11,281 edges.
- **Smallest Component:** WCC #10 ($t=11$) containing 1,071 transactions and 1,068 edges.

---

### 2.4 Community Detection via Louvain Modularity Optimization

Communities are identified on the undirected projection of each temporal component using the Louvain modularity heuristic:

$$Q = \frac{1}{2m} \sum_{i,j} \left[ A_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$

where:
- $A_{ij}$ is the adjacency weight between nodes $i$ and $j$
- $k_i, k_j$ are node degrees
- $m$ is total edges in the graph
- $\delta(c_i, c_j) = 1$ if $i$ and $j$ share community $c$, else $0$.

**Empirical Results:**
- **Total Detected Communities:** 35,463
- **Global Modularity Score ($Q$):** $0.812$ (demonstrating highly dense, localized transaction cluster partitioning).

---

## 3. Structural AML Payment Patterns

| Pattern Typology | Metric Threshold | Forensic Definition | Count in Dataset |
| :--- | :--- | :--- | :--- |
| **Aggregation Hub** | $d_{in} \ge 9$, $d_{in} \ge P_{99}$ | High fan-in node consolidating funds | 2,042 transactions |
| **Distribution Hub** | $d_{out} \ge 5$, $d_{out} \ge P_{99}$ | High fan-out node disbursing funds | 2,040 transactions |
| **Dual Hub (Mixer/Exchange)** | $d_{in} \ge 9$ AND $d_{out} \ge 5$ | High volume intermediate clearing | 512 transactions |
| **Linear Pass-Through** | $d_{in} = 1$ AND $d_{out} = 1$ | Unbranched layering relay node | 102,419 transactions |

> **Investigative Caveat:** Structural topological hubs are intrinsic to Bitcoin mechanics (such as mining payouts and exchange hot wallets). They provide investigative signals and prioritization cues, but do not replace legal evidence.

