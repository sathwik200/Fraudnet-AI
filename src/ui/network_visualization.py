"""Interactive Cyberpunk Network Topology Explorer for FRAUDNET AI.
===================================================================
Signature visual environment for inspecting directed payment flows, multi-hop
counterparty clusters, and cash-flow vectors with glowing neon graph mechanics.
"""

from typing import Dict, List
import streamlit as st
import networkx as nx
import plotly.graph_objects as go

from src.tools.graph_tools import get_graph_instance, get_transaction_neighborhood
from src.tools.transaction_tools import get_full_transaction_profile
from src.ui.theme import CYAN, RED, GREEN, BLUE, AMBER, PURPLE, apply_cyber_theme
from src.ui.components import (
    render_command_header,
    render_cyber_metric,
)


def render_network_visualization_page():
    """Render the signature futuristic 2D Bitcoin payment graph explorer."""
    render_command_header("BITCOIN PAYMENT TOPOLOGY EXPLORER")

    st.markdown(
        """
        <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; color:#8892B0; margin-bottom:14px;">
            // MULTI-HOP DIRECTED GRAPH RECONNAISSANCE & COUNTERPARTY TRACING
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Tactical Controls Bar
    c_tx, c_hop, c_limit = st.columns([2, 1, 1])
    with c_tx:
        default_tx = st.session_state.get("active_tx_id", 230425980)
        tx_input = st.text_input(
            "FOCAL TRANSACTION IDENTIFIER:",
            value=str(default_tx),
            placeholder="ENTER TXID...",
        )
    with c_hop:
        hops = st.selectbox("EGO HORIZON (HOPS):", options=[1, 2], index=0)
    with c_limit:
        max_nodes = st.slider("NODE RENDERING BUDGET:", min_value=15, max_value=80, value=45, step=5)

    if not tx_input.strip().isdigit():
        st.warning("PLEASE SPECIFY A VALID NUMERIC TRANSACTION IDENTIFIER.")
        return

    tx_id = int(tx_input.strip())
    st.session_state["active_tx_id"] = tx_id

    with st.spinner("COMPUTING SPRING GRAPH EMBEDDING & TOPOLOGICAL VECTORS..."):
        neighborhood = get_transaction_neighborhood(tx_id, hops=hops, max_nodes=max_nodes)

    if "error" in neighborhood:
        st.error(f"❌ {neighborhood['error']}")
        return

    nodes_data = neighborhood.get("nodes", [])
    edges_data = neighborhood.get("edges", [])
    predecessors_count = neighborhood.get("direct_predecessors_count", 0)
    successors_count = neighborhood.get("direct_successors_count", 0)

    # High-Tech Telemetry KPI Cards
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_cyber_metric("FOCAL TARGET", f"tx_{tx_id}", "Ego Epicenter", color="purple", icon="🎯")
    with m2:
        render_cyber_metric("RENDERED NODES", str(len(nodes_data)), f"Within {hops}-Hop Horizon", color="cyan", icon="🕸️")
    with m3:
        render_cyber_metric("UPSTREAM INFLOWS", str(predecessors_count), "Direct Funding Inputs", color="blue", icon="📥")
    with m4:
        render_cyber_metric("DOWNSTREAM OUTFLOWS", str(successors_count), "Direct Recipient Outputs", color="green", icon="📤")

    # Construct NetworkX Subgraph for Layout Computation
    G = nx.DiGraph()
    for nd in nodes_data:
        G.add_node(nd["txId"], **nd)
    for ed in edges_data:
        G.add_edge(ed["source"], ed["target"])

    # Compute positions using spring layout with deterministic seed
    pos = nx.spring_layout(G, seed=42, k=0.55 if len(nodes_data) < 30 else 0.4, iterations=60)

    # Prepare Edge Traces with glowing cyan aesthetic
    edge_x = []
    edge_y = []
    for u, v in G.edges():
        if u in pos and v in pos:
            x0, y0 = pos[u]
            x1, y1 = pos[v]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=1.6, color="rgba(0, 245, 255, 0.4)"),
        hoverinfo="none",
        mode="lines",
        name="DIRECTED FLOW",
    )

    # Classify Nodes for Multi-Color Cyber Aesthetic
    node_x = []
    node_y = []
    node_colors = []
    node_sizes = []
    node_symbols = []
    node_hover_text = []

    for nd in nodes_data:
        nid = nd["txId"]
        if nid not in pos:
            continue
        x, y = pos[nid]
        node_x.append(x)
        node_y.append(y)

        lbl = str(nd.get("label", "unknown"))
        is_center = (nid == tx_id)
        deg = nd.get("in_degree", 0) + nd.get("out_degree", 0)

        if is_center:
            color = PURPLE
            size = 24
            symbol = "diamond"
            role_desc = "🎯 FOCAL QUERY EPICENTER"
        elif lbl == "1":
            color = RED
            size = 16 + min(deg * 2, 10)
            symbol = "circle"
            role_desc = "⚡ CONFIRMED ILLICIT (CLASS 1)"
        elif lbl == "2":
            color = GREEN
            size = 13 + min(deg * 2, 8)
            symbol = "circle"
            role_desc = "🛡️ CONFIRMED LICIT (CLASS 2)"
        else:
            color = AMBER if deg > 5 else CYAN
            size = 11 + min(deg, 8)
            symbol = "circle"
            role_desc = "⚪ UNLABELED / STREAM NODE"

        node_colors.append(color)
        node_sizes.append(size)
        node_symbols.append(symbol)

        hover_str = (
            f"<b style='color:#00F5FF;font-family:Rajdhani;'>TRANSACTION: tx_{nid}</b><br>"
            f"<b>CLASSIFICATION:</b> {role_desc}<br>"
            f"<b>TIME STEP:</b> Step #{nd.get('time_step', 'N/A')}<br>"
            f"<b>LOCAL IN-DEGREE:</b> {nd.get('in_degree', 0)} inputs<br>"
            f"<b>LOCAL OUT-DEGREE:</b> {nd.get('out_degree', 0)} outputs"
        )
        node_hover_text.append(hover_str)

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers",
        hoverinfo="text",
        text=node_hover_text,
        marker=dict(
            color=node_colors,
            size=node_sizes,
            symbol=node_symbols,
            line=dict(width=1.5, color="#FFFFFF"),
        ),
        name="TRANSACTION VERTICES",
    )

    fig = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            title=dict(
                text=f"<span style='color:#00F5FF;font-family:Rajdhani;font-weight:700;'>// TOPOLOGY GRAPH: EGO CENTER TX_{tx_id} ({hops}-HOP BOUNDED SUBGRAPH)</span>",
                x=0.01,
                y=0.97,
                font=dict(size=14),
            ),
            showlegend=False,
            hovermode="closest",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#060B12",
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            margin=dict(b=20, l=20, r=20, t=45),
            height=580,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Visual Legend Bar
    st.markdown(
        """
        <div style="background:#09121D; border:1px solid rgba(0,245,255,0.2); border-radius:4px; padding:10px 16px; margin-top:-8px; margin-bottom:16px; display:flex; justify-content:space-around; font-family:'JetBrains Mono',monospace; font-size:0.75rem;">
            <span><strong style="color:#A970FF;">◆ PURPLE:</strong> Focal Center Target</span>
            <span><strong style="color:#FF3158;">● RED:</strong> Confirmed Illicit (Class 1)</span>
            <span><strong style="color:#00FF9C;">● GREEN:</strong> Confirmed Licit (Class 2)</span>
            <span><strong style="color:#FFB547;">● AMBER:</strong> High-Degree Unknown Hub</span>
            <span><strong style="color:#00F5FF;">● CYAN:</strong> Standard Relay Node</span>
            <span><strong style="color:#00F5FF;">― CYAN GLOW:</strong> Directed Cash-Flow</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Detailed Directional Flow Breakdown
    c_inflow, c_outflow = st.columns(2)

    with c_inflow:
        st.markdown(
            f"""
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; font-weight:700; color:#168BFF; letter-spacing:1px; margin-bottom:6px;">
                // INCOMING COUNTERPARTY INFLOWS ({predecessors_count} INPUTS)
            </div>
            """,
            unsafe_allow_html=True,
        )
        preds = neighborhood.get("direct_predecessors_sample", [])
        if preds:
            df_in = pd.DataFrame([
                {
                    "Source Transaction": f"tx_{p}",
                    "Flow Vector": f"tx_{p} ➔ tx_{tx_id}",
                    "Flow Type": "Inbound Satoshis",
                }
                for p in preds
            ])
            st.dataframe(df_in, use_container_width=True, hide_index=True)
        else:
            st.caption("No inbound predecessor nodes within this temporal partition.")

    with c_outflow:
        st.markdown(
            f"""
            <div style="font-family:'Rajdhani',sans-serif; font-size:1.1rem; font-weight:700; color:#00FF9C; letter-spacing:1px; margin-bottom:6px;">
                // OUTGOING RECIPIENT DISBURSEMENTS ({successors_count} OUTPUTS)
            </div>
            """,
            unsafe_allow_html=True,
        )
        succs = neighborhood.get("direct_successors_sample", [])
        if succs:
            df_out = pd.DataFrame([
                {
                    "Destination Transaction": f"tx_{s}",
                    "Flow Vector": f"tx_{tx_id} ➔ tx_{s}",
                    "Flow Type": "Outbound Satoshis",
                }
                for s in succs
            ])
            st.dataframe(df_out, use_container_width=True, hide_index=True)
        else:
            st.caption("No outbound successor nodes within this temporal partition.")
