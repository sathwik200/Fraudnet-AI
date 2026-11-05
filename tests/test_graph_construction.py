#!/usr/bin/env python3
"""
FRAUDNET AI — Graph Construction Test Suite
=============================================
Automated unit and integration tests verifying the directed Bitcoin
transaction network construction pipeline.

Testing Scope:
  1.  Correct node creation.
  2.  Correct directed edge creation.
  3.  Preservation of edge direction.
  4.  Inclusion of isolated transactions.
  5.  Preservation of transaction IDs.
  6.  Preservation of time steps.
  7.  Preservation of original labels.
  8.  Preservation of unknown labels.
  9.  Duplicate transaction ID detection.
  10. Duplicate directed edge detection.
  11. Missing edge endpoint detection.
  12. Self-loop detection.
  13. Missing node attribute detection.
  14. Graph serialization and deserialization.
  15. Graph summary generation.
  16. Full dataset artifact verification (if present on disk).

Unit tests utilize isolated synthetic datasets to remain fast and reproducible.
"""

import json
import os
import pickle
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

import networkx as nx
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.graph.build_graph import (
    build_transaction_graph,
    load_graph,
    save_graph,
    validate_source_data,
)
from src.graph.validate_graph import (
    generate_graph_summary,
    save_graph_summary,
    validate_transaction_graph,
)


class TestGraphConstructionSynthetic(unittest.TestCase):
    """Unit tests using small synthetic datasets."""

    def setUp(self):
        """Create a standard synthetic transaction dataset."""
        # Nodes: 5 transactions across 2 time steps
        # Node 101: time_step 1, label '1' (illicit)
        # Node 102: time_step 1, label '2' (licit)
        # Node 103: time_step 1, label 'unknown' (unknown)
        # Node 104: time_step 2, label '2' (licit)
        # Node 105: time_step 2, label 'unknown' (isolated transaction)
        self.synth_tx_df = pd.DataFrame({
            "txId": [101, 102, 103, 104, 105],
            "time_step": [1, 1, 1, 2, 2],
            "label": ["1", "2", "unknown", "2", "unknown"],
        })

        # Directed Edges:
        # 101 -> 102
        # 102 -> 103
        # 103 -> 104
        # (105 has no edges - isolated)
        self.synth_edges_df = pd.DataFrame({
            "txId1": [101, 102, 103],
            "txId2": [102, 103, 104],
        })

    def test_01_correct_node_creation(self):
        """Test 1: Verify all transactions are created as nodes."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertEqual(G.number_of_nodes(), 5)
        for tid in [101, 102, 103, 104, 105]:
            self.assertIn(tid, G.nodes)

    def test_02_correct_directed_edge_creation(self):
        """Test 2: Verify all specified directed edges are created."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertEqual(G.number_of_edges(), 3)
        self.assertTrue(G.has_edge(101, 102))
        self.assertTrue(G.has_edge(102, 103))
        self.assertTrue(G.has_edge(103, 104))

    def test_03_preservation_of_edge_direction(self):
        """Test 3: Verify directed edges are not reciprocal."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        # Forward edges must exist
        self.assertTrue(G.has_edge(101, 102))
        # Reverse edges must NOT exist
        self.assertFalse(G.has_edge(102, 101))
        self.assertFalse(G.has_edge(103, 102))
        self.assertFalse(G.has_edge(104, 103))

    def test_04_inclusion_of_isolated_transactions(self):
        """Test 4: Verify transactions with zero in/out edges are included."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertIn(105, G.nodes)
        self.assertEqual(G.in_degree(105), 0)
        self.assertEqual(G.out_degree(105), 0)
        isolates = list(nx.isolates(G))
        self.assertEqual(isolates, [105])

    def test_05_preservation_of_transaction_ids(self):
        """Test 5: Verify transaction ID types are exact integers without cast."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        for node in G.nodes:
            self.assertIsInstance(node, int)
            self.assertIn(node, {101, 102, 103, 104, 105})

    def test_06_preservation_of_time_steps(self):
        """Test 6: Verify time_step attributes match source records."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertEqual(G.nodes[101]["time_step"], 1)
        self.assertEqual(G.nodes[102]["time_step"], 1)
        self.assertEqual(G.nodes[103]["time_step"], 1)
        self.assertEqual(G.nodes[104]["time_step"], 2)
        self.assertEqual(G.nodes[105]["time_step"], 2)

    def test_07_preservation_of_original_labels(self):
        """Test 7: Verify original labels '1' and '2' are preserved."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertEqual(G.nodes[101]["label"], "1")
        self.assertEqual(G.nodes[102]["label"], "2")
        self.assertEqual(G.nodes[104]["label"], "2")

    def test_08_preservation_of_unknown_labels(self):
        """Test 8: Verify 'unknown' labels are preserved and not cast to licit."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        self.assertEqual(G.nodes[103]["label"], "unknown")
        self.assertEqual(G.nodes[105]["label"], "unknown")
        # Ensure 'unknown' is not converted to 0, 2, licit, or None
        self.assertNotEqual(G.nodes[103]["label"], "2")
        self.assertNotEqual(G.nodes[103]["label"], "licit")

    def test_09_duplicate_transaction_id_detection(self):
        """Test 9: Verify duplicate transaction IDs raise a ValueError."""
        dup_tx_df = pd.DataFrame({
            "txId": [101, 101, 102],  # Duplicate 101
            "time_step": [1, 1, 1],
            "label": ["1", "1", "2"],
        })
        with self.assertRaises(ValueError) as ctx:
            validate_source_data(dup_tx_df, self.synth_edges_df)
        self.assertIn("duplicate transaction ids", str(ctx.exception).lower())

    def test_10_duplicate_directed_edge_detection(self):
        """Test 10: Verify duplicate directed edges raise a ValueError."""
        dup_edges_df = pd.DataFrame({
            "txId1": [101, 101],  # Duplicate (101 -> 102)
            "txId2": [102, 102],
        })
        with self.assertRaises(ValueError) as ctx:
            validate_source_data(self.synth_tx_df, dup_edges_df)
        self.assertIn("duplicate directed edges", str(ctx.exception).lower())

    def test_11_missing_edge_endpoint_detection(self):
        """Test 11: Verify edge endpoints not in transactions table are rejected."""
        orphan_edges_df = pd.DataFrame({
            "txId1": [101, 999],  # 999 is not in transactions table
            "txId2": [102, 103],
        })
        with self.assertRaises(ValueError) as ctx:
            validate_source_data(self.synth_tx_df, orphan_edges_df)
        self.assertIn("orphan", str(ctx.exception).lower())

    def test_12_self_loop_detection(self):
        """Test 12: Verify self-loops (u == v) are detected and reported."""
        self_loop_edges_df = pd.DataFrame({
            "txId1": [101, 102, 103, 103],  # 103 -> 103 is a self-loop
            "txId2": [102, 103, 104, 103],
        })
        stats = validate_source_data(self.synth_tx_df, self_loop_edges_df)
        self.assertEqual(stats["self_loops"], 1)

        G = nx.DiGraph()
        G.add_nodes_from([
            (tid, {"time_step": ts, "label": lbl})
            for tid, ts, lbl in zip(self.synth_tx_df["txId"], self.synth_tx_df["time_step"], self.synth_tx_df["label"])
        ])
        G.add_edges_from(zip(self_loop_edges_df["txId1"], self_loop_edges_df["txId2"]))
        self.assertEqual(nx.number_of_selfloops(G), 1)

    def test_13_missing_node_attribute_detection(self):
        """Test 13: Verify validator catches nodes missing time_step or label."""
        G = nx.DiGraph()
        G.add_node(1, time_step=1)  # Missing label
        G.add_node(2, label="2")    # Missing time_step
        report, passed = validate_transaction_graph(G, verbose=False)
        self.assertFalse(passed)
        self.assertEqual(report["missing_node_attributes"], 2)

    def test_14_graph_serialization_and_deserialization(self):
        """Test 14: Verify pickle serialization preserves graph structure and attrs."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_pkl = Path(tmpdir) / "test_graph.pkl"
            save_graph(G, output_path=temp_pkl, verbose=False)
            self.assertTrue(temp_pkl.exists())

            G_loaded = load_graph(input_path=temp_pkl, verbose=False)
            self.assertEqual(G_loaded.number_of_nodes(), G.number_of_nodes())
            self.assertEqual(G_loaded.number_of_edges(), G.number_of_edges())
            self.assertEqual(G_loaded.nodes[101]["label"], "1")
            self.assertEqual(G_loaded.nodes[103]["label"], "unknown")
            self.assertEqual(G_loaded.nodes[105]["time_step"], 2)
            self.assertTrue(G_loaded.has_edge(101, 102))

    def test_15_graph_summary_generation(self):
        """Test 15: Verify graph summary structure and values."""
        G = build_transaction_graph(
            tx_df=self.synth_tx_df,
            edges_df=self.synth_edges_df,
            verbose=False,
        )
        report, passed = validate_transaction_graph(
            G, tx_df=self.synth_tx_df, edges_df=self.synth_edges_df, verbose=False
        )
        summary = generate_graph_summary(G, report)

        self.assertEqual(summary["project_name"], "FRAUDNET AI")
        self.assertEqual(summary["graph_type"], "networkx.DiGraph")
        self.assertEqual(summary["total_nodes"], 5)
        self.assertEqual(summary["total_edges"], 3)
        self.assertEqual(summary["isolated_node_count"], 1)
        self.assertIn("degree_statistics", summary)
        self.assertIn("connectivity_statistics", summary)
        self.assertEqual(summary["class_distribution"]["unknown"], 2)
        self.assertEqual(summary["class_distribution"]["licit (2)"], 2)
        self.assertEqual(summary["class_distribution"]["illicit (1)"], 1)


class TestFullDatasetGraphArtifact(unittest.TestCase):
    """Integration tests verifying the actual full dataset graph artifact."""

    @classmethod
    def setUpClass(cls):
        """Load the serialized graph artifact once for integration tests."""
        cls.graph_path = PROJECT_ROOT / "data" / "processed" / "transaction_graph.pkl"
        cls.summary_path = PROJECT_ROOT / "data" / "processed" / "graph_summary.json"

        if not cls.graph_path.exists():
            raise unittest.SkipTest("transaction_graph.pkl not found. Run build_graph first.")

        cls.G = load_graph(cls.graph_path, verbose=False)
        with open(cls.summary_path, "r", encoding="utf-8") as f:
            cls.summary = json.load(f)

    def test_exact_node_count(self):
        """Verify the graph has exactly 203,769 transaction nodes."""
        self.assertEqual(self.G.number_of_nodes(), 203_769)

    def test_exact_edge_count(self):
        """Verify the graph has exactly 234,355 directed edges."""
        self.assertEqual(self.G.number_of_edges(), 234_355)

    def test_is_digraph(self):
        """Verify graph is an instance of networkx.DiGraph."""
        self.assertIsInstance(self.G, nx.DiGraph)

    def test_no_self_loops_in_dataset(self):
        """Verify the Elliptic transaction network has zero self-loops."""
        self.assertEqual(nx.number_of_selfloops(self.G), 0)

    def test_weakly_connected_components_count(self):
        """Verify graph has exactly 49 weakly connected components (one per timestep)."""
        wcc_count = nx.number_weakly_connected_components(self.G)
        self.assertEqual(wcc_count, 49)

    def test_strongly_connected_components_count(self):
        """Verify graph has 203,769 SCCs (DAG property - zero cycles)."""
        scc_count = nx.number_strongly_connected_components(self.G)
        self.assertEqual(scc_count, 203_769)

    def test_class_distribution_in_graph(self):
        """Verify node labels match original dataset counts exactly."""
        label_counts = Counter(attrs["label"] for _, attrs in self.G.nodes(data=True))
        self.assertEqual(label_counts["1"], 4_545)
        self.assertEqual(label_counts["2"], 42_019)
        self.assertEqual(label_counts["unknown"], 157_205)

    def test_time_steps_in_graph(self):
        """Verify all 49 time steps exist in node attributes."""
        time_steps = set(attrs["time_step"] for _, attrs in self.G.nodes(data=True))
        self.assertEqual(len(time_steps), 49)
        self.assertEqual(time_steps, set(range(1, 50)))

    def test_summary_json_integrity(self):
        """Verify graph_summary.json matches graph metrics."""
        self.assertEqual(self.summary["total_nodes"], 203_769)
        self.assertEqual(self.summary["total_edges"], 234_355)
        self.assertEqual(self.summary["validation_status"], "PASSED")
        self.assertEqual(self.summary["connectivity_statistics"]["weakly_connected_components"], 49)


if __name__ == "__main__":
    unittest.main(verbosity=2)
