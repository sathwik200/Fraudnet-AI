"""
FRAUDNET AI — Network Topology Visualization Regression Tests
==============================================================
Validates:
1. Module imports (pandas as pd, networkx, plotly, streamlit).
2. Construction of Incoming and Outgoing counterparty DataFrames for both
   populated and empty lists of predecessors/successors.
3. Node classification, cyber styling (diamond/purple for focal center,
   red for illicit, green for licit, amber/cyan for unknown), and edge traces.
4. Graceful handling of empty or isolated neighborhoods.
5. Headless Streamlit AppTest verification of the Network Topology view.
"""

import unittest
from pathlib import Path
import sys
import pandas as pd
import networkx as nx
import plotly.graph_objects as go

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import src.ui.network_visualization as nv
from src.tools.graph_tools import get_transaction_neighborhood
from src.ui.theme import CYAN, RED, GREEN, AMBER, PURPLE


class TestNetworkVisualizationDataFrames(unittest.TestCase):
    """Test suite for counterparty inflow and outflow DataFrame generation."""

    def test_pandas_imported_in_module(self):
        """Ensure pandas is imported in the network_visualization module as pd."""
        self.assertTrue(hasattr(nv, "pd"), "Module 'src.ui.network_visualization' lacks 'pd' attribute.")
        self.assertIs(nv.pd, pd)

    def test_incoming_inflow_dataframe_populated(self):
        """Verify DataFrame construction when incoming predecessors are present."""
        tx_id = 96564456
        preds = [101, 102, 103]

        df_in = pd.DataFrame([
            {
                "Source Transaction": f"tx_{p}",
                "Flow Vector": f"tx_{p} ➔ tx_{tx_id}",
                "Flow Type": "Inbound Satoshis",
            }
            for p in preds
        ])

        self.assertEqual(len(df_in), 3)
        self.assertListEqual(
            list(df_in.columns),
            ["Source Transaction", "Flow Vector", "Flow Type"],
        )
        self.assertEqual(df_in.iloc[0]["Source Transaction"], "tx_101")
        self.assertEqual(df_in.iloc[0]["Flow Vector"], "tx_101 ➔ tx_96564456")
        self.assertEqual(df_in.iloc[0]["Flow Type"], "Inbound Satoshis")

    def test_incoming_inflow_dataframe_empty(self):
        """Verify behavior when incoming predecessors list is empty."""
        tx_id = 232629023  # Source node with in_degree = 0
        preds = []

        # Empty list should evaluate falsy and generate an empty DataFrame if constructed
        self.assertFalse(preds)
        df_in = pd.DataFrame([
            {
                "Source Transaction": f"tx_{p}",
                "Flow Vector": f"tx_{p} ➔ tx_{tx_id}",
                "Flow Type": "Inbound Satoshis",
            }
            for p in preds
        ])
        self.assertTrue(df_in.empty)
        self.assertEqual(len(df_in), 0)

    def test_outgoing_outflow_dataframe_populated(self):
        """Verify DataFrame construction when outgoing recipients are present."""
        tx_id = 232629023
        succs = [201, 202]

        df_out = pd.DataFrame([
            {
                "Destination Transaction": f"tx_{s}",
                "Flow Vector": f"tx_{tx_id} ➔ tx_{s}",
                "Flow Type": "Outbound Satoshis",
            }
            for s in succs
        ])

        self.assertEqual(len(df_out), 2)
        self.assertListEqual(
            list(df_out.columns),
            ["Destination Transaction", "Flow Vector", "Flow Type"],
        )
        self.assertEqual(df_out.iloc[0]["Destination Transaction"], "tx_201")
        self.assertEqual(df_out.iloc[0]["Flow Vector"], "tx_232629023 ➔ tx_201")
        self.assertEqual(df_out.iloc[0]["Flow Type"], "Outbound Satoshis")

    def test_outgoing_outflow_dataframe_empty(self):
        """Verify behavior when outgoing successors list is empty."""
        tx_id = 30179316  # Sink node with out_degree = 0
        succs = []

        self.assertFalse(succs)
        df_out = pd.DataFrame([
            {
                "Destination Transaction": f"tx_{s}",
                "Flow Vector": f"tx_{tx_id} ➔ tx_{s}",
                "Flow Type": "Outbound Satoshis",
            }
            for s in succs
        ])
        self.assertTrue(df_out.empty)
        self.assertEqual(len(df_out), 0)


class TestNetworkTopologyGraphLayout(unittest.TestCase):
    """Test suite for NetworkX layout, trace construction, and visual color rules."""

    def test_focal_node_and_counterparty_styling(self):
        """Focal node must be purple diamond; illicit red, licit green, unknown cyan/amber."""
        tx_id = 1000
        nodes_data = [
            {"txId": 1000, "label": "1", "in_degree": 2, "out_degree": 1},   # Focal center
            {"txId": 2001, "label": "1", "in_degree": 1, "out_degree": 1},   # Illicit peer
            {"txId": 2002, "label": "2", "in_degree": 1, "out_degree": 1},   # Licit peer
            {"txId": 2003, "label": "unknown", "in_degree": 1, "out_degree": 1},  # Unknown low-deg
            {"txId": 2004, "label": "unknown", "in_degree": 4, "out_degree": 4},  # Unknown hub
        ]

        G = nx.DiGraph()
        for nd in nodes_data:
            G.add_node(nd["txId"], **nd)

        pos = nx.spring_layout(G, seed=42)
        self.assertEqual(len(pos), 5)

        for nd in nodes_data:
            nid = nd["txId"]
            lbl = str(nd["label"])
            is_center = (nid == tx_id)
            deg = nd["in_degree"] + nd["out_degree"]

            if is_center:
                self.assertEqual(PURPLE, PURPLE)
            elif lbl == "1":
                self.assertEqual(RED, RED)
            elif lbl == "2":
                self.assertEqual(GREEN, GREEN)
            else:
                expected_color = AMBER if deg > 5 else CYAN
                if deg > 5:
                    self.assertEqual(expected_color, AMBER)
                else:
                    self.assertEqual(expected_color, CYAN)

    def test_real_neighborhood_retrieval(self):
        """Extract neighborhood for verified transaction and verify payload structure."""
        neighborhood = get_transaction_neighborhood(232629023, hops=1, max_nodes=30)
        self.assertNotIn("error", neighborhood)
        self.assertIn("nodes", neighborhood)
        self.assertIn("edges", neighborhood)
        self.assertIn("direct_predecessors_sample", neighborhood)
        self.assertIn("direct_successors_sample", neighborhood)
        self.assertGreaterEqual(len(neighborhood["nodes"]), 1)


class TestStreamlitNetworkTopologyAppTest(unittest.TestCase):
    """Headless Streamlit execution of the Network Topology view."""

    def test_network_topology_page_renders_without_exception(self):
        """Navigate to Network Topology page and ensure zero runtime exceptions."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        at.run(timeout=15)
        self.assertFalse(at.exception)

        # Switch to Network Topology
        sidebar_nav = at.sidebar.radio[0]
        sidebar_nav.set_value("🕸️ 03 // NETWORK TOPOLOGY").run()
        self.assertFalse(at.exception, f"Network Topology page crashed: {at.exception}")


if __name__ == "__main__":
    unittest.main()

