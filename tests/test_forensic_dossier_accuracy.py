"""
FRAUDNET AI — Forensic Dossier Accuracy & Evidence Consistency Tests
====================================================================
Verifies:
1. Network metric consistency (in/out-degree vs predecessor/successor counts).
2. Global graph metrics vs bounded ego-subgraph distinctions.
3. Strict evidence-based AML typology classification (suppression of unsupported typologies).
4. Feature attribution integrity (distinguishing missing attribution from no significant anomalies).
5. Responsible compliance recommendations (human review, no automated freezes or automatic SAR filings).
6. AI execution transparency (disclosure of deterministic fallback vs LLM mode).
7. Consistency between dossier metrics and Network Topology explorer.
"""

import unittest
from pathlib import Path
import sys

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analytics.transaction_investigation import compile_investigation_dossier
from src.analytics.typology import classify_aml_typology
from src.tools.graph_tools import get_transaction_neighborhood
from src.tools.transaction_tools import get_full_transaction_profile
from src.reports.report_generator import generate_forensic_pdf_report
from src.agents.nodes import synthesize_forensics_node
from src.agents.state import InvestigationState


class TestNetworkMetricConsistency(unittest.TestCase):
    """Test consistency of graph degrees, predecessors, and successors across components."""

    def test_degree_and_counterparty_count_consistency(self):
        """In-degree must equal predecessor count, and out-degree must equal successor count."""
        test_tx_ids = [232629023, 96564456, 232438397, 230425980]

        for tx_id in test_tx_ids:
            profile = get_full_transaction_profile(tx_id)
            neigh = get_transaction_neighborhood(tx_id, hops=1, max_nodes=50)

            in_deg = profile["graph_metrics"]["in_degree"]
            out_deg = profile["graph_metrics"]["out_degree"]

            pred_count = neigh["direct_predecessors_count"]
            succ_count = neigh["direct_successors_count"]

            self.assertEqual(
                in_deg,
                pred_count,
                f"Tx {tx_id}: in_degree ({in_deg}) != direct_predecessors_count ({pred_count})",
            )
            self.assertEqual(
                out_deg,
                succ_count,
                f"Tx {tx_id}: out_degree ({out_deg}) != direct_successors_count ({succ_count})",
            )
            self.assertEqual(len(neigh["predecessors"]), in_deg)
            self.assertEqual(len(neigh["successors"]), out_deg)

            # An out-degree of 1 must NEVER be reported alongside 0 successors
            if out_deg == 1:
                self.assertEqual(succ_count, 1)
                self.assertEqual(len(neigh["successors"]), 1)

    def test_global_vs_ego_subgraph_metrics_distinction(self):
        """Dossier must distinguish global partition metrics from bounded ego subgraph metrics."""
        tx_id = 232438397  # Large hub with in_degree=160, out_degree=1
        dossier = compile_investigation_dossier(tx_id)

        self.assertIn("global_graph_metrics", dossier)
        self.assertIn("bounded_subgraph_metrics", dossier)

        global_m = dossier["global_graph_metrics"]
        bounded_m = dossier["bounded_subgraph_metrics"]

        # Global in-degree is 160
        self.assertEqual(global_m["in_degree"], 160)
        self.assertEqual(global_m["out_degree"], 1)

        # Bounded subgraph nodes is capped (<= 30)
        self.assertLessEqual(bounded_m["rendered_nodes"], 30)
        self.assertEqual(bounded_m["hops_explored"], 1)

    def test_graph_metrics_across_ground_truth_classes(self):
        """Verify graph degrees and direct predecessor/successor counts across classes."""
        samples = {
            "illicit": 232629023,
            "licit": 232438397,
            "unknown": 230425980,
        }
        for label_type, tx_id in samples.items():
            dossier = compile_investigation_dossier(tx_id)
            gm = dossier["global_graph_metrics"]
            bm = dossier["bounded_subgraph_metrics"]

            self.assertEqual(gm["in_degree"], gm["direct_predecessors_count"])
            self.assertEqual(gm["out_degree"], gm["direct_successors_count"])
            self.assertEqual(gm["total_degree"], gm["in_degree"] + gm["out_degree"])
            self.assertEqual(bm["hops_explored"], 1)
            self.assertGreaterEqual(bm["rendered_nodes"], 1)


class TestEvidenceBasedAMLTypology(unittest.TestCase):
    """Test strict evidence-based assignment and suppression of unsupported AML typologies."""

    def test_unsupported_typology_suppressed_for_low_degree(self):
        """Low-degree or ambiguous transactions must report 'Insufficient evidence'."""
        # 0 in, 1 out: endpoint, not peeling/mixing
        res1 = classify_aml_typology(in_degree=0, out_degree=1)
        self.assertEqual(res1["typology"], "Insufficient evidence to determine transaction typology")
        self.assertFalse(res1["evidence_sufficient"])

        # 2 in, 2 out with low clustering: insufficient structural evidence
        res2 = classify_aml_typology(in_degree=2, out_degree=2, is_aggregation_hub=False)
        self.assertEqual(res2["typology"], "Insufficient evidence to determine transaction typology")
        self.assertFalse(res2["evidence_sufficient"])

    def test_point_to_point_transfer_not_labeled_layering(self):
        """1-in / 1-out transfer must be labeled Direct Point-to-Point, not layering or peeling."""
        res = classify_aml_typology(in_degree=1, out_degree=1)
        self.assertEqual(res["typology"], "Direct Point-to-Point Transfer")
        self.assertIn("insufficient structural complexity", res["compliance_note"].lower())
        self.assertNotIn("layering", res["typology"].lower())
        self.assertNotIn("peeling", res["typology"].lower())

    def test_aggregation_hub_assignment(self):
        """High fan-in concentration with hub status assigns Aggregation Hub with evidence."""
        res = classify_aml_typology(in_degree=160, out_degree=1, is_aggregation_hub=True)
        self.assertEqual(res["typology"], "High Fan-In Aggregation Hub")
        self.assertTrue(res["evidence_sufficient"])
        self.assertIn("fan-in ratio", res["supporting_observations"])

    def test_distribution_hub_assignment(self):
        """High fan-out dispersal with hub status assigns Distribution Hub with evidence."""
        res = classify_aml_typology(in_degree=1, out_degree=50, is_distribution_hub=True)
        self.assertEqual(res["typology"], "High Fan-Out Distribution Hub")
        self.assertTrue(res["evidence_sufficient"])
        self.assertIn("fan-out ratio", res["supporting_observations"])


class TestFeatureAttributionIntegrity(unittest.TestCase):
    """Test feature attribution accuracy, descriptive neutrality, and transparency."""

    def test_feature_attribution_methodology_disclosed(self):
        """Explainability payload must disclose methodology and baseline deviation status."""
        profile = get_full_transaction_profile(232629023)
        explain = profile["explainability"]

        self.assertTrue(explain.get("attribution_available"))
        self.assertIn("methodology", explain)
        self.assertIn("Z-score", explain["methodology"])
        self.assertIn("top_deviations_above", explain)
        self.assertIn("top_deviations_below", explain)
        self.assertIn("top_risk_elevating", explain)
        self.assertIn("top_risk_mitigating", explain)

    def test_descriptive_deviations_across_illicit_licit_unknown(self):
        """Deviations must be descriptive without claiming signed directional causality."""
        # 232629023 (Illicit), 232438397 (Licit), 230425980 (Unknown)
        test_txs = [232629023, 232438397, 230425980]

        for tx_id in test_txs:
            profile = get_full_transaction_profile(tx_id)
            explain = profile["explainability"]

            self.assertTrue(explain["attribution_available"])
            self.assertIn("top_deviations_above", explain)
            self.assertIn("top_deviations_below", explain)

            # Check positive deviations
            for item in explain["top_deviations_above"]:
                self.assertGreater(item["z_score"], 0)
                self.assertEqual(item["deviation_direction"], "above_baseline")
                self.assertIn("above baseline", item["explanation"].lower())
                self.assertNotIn("elevating estimated risk", item["explanation"].lower())

            # Check negative deviations
            for item in explain["top_deviations_below"]:
                self.assertLess(item["z_score"], 0)
                self.assertEqual(item["deviation_direction"], "below_baseline")
                self.assertIn("below baseline", item["explanation"].lower())
                self.assertNotIn("reducing estimated risk", item["explanation"].lower())

            # Uncertainty note must state non-causal investigative lead
            self.assertIn("deviations", explain["uncertainty_note"].lower())
            self.assertIn("human review", explain["uncertainty_note"].lower())


class TestResponsibleComplianceGuidance(unittest.TestCase):
    """Test compliance recommendations for safety, human review, and legal disclaimers."""

    def test_dossier_compliance_safety(self):
        """Dossier compliance recommendations must not contain automated freeze instructions."""
        dossier = compile_investigation_dossier(232629023)
        recs = dossier["compliance_recommendations"]

        combined_text = " ".join(recs).lower()
        self.assertNotIn("freeze counterparty", combined_text)
        self.assertNotIn("automated sar filing", combined_text)
        self.assertIn("human review", combined_text)
        self.assertIn("research dataset", combined_text)

    def test_agent_fallback_compliance_safety(self):
        """Agent deterministic fallback report must prioritize human review over automated action."""
        state: InvestigationState = {
            "query": "Investigate transaction 232629023",
            "target_tx_id": "232629023",
            "transaction_profile": get_full_transaction_profile(232629023),
            "graph_context": get_transaction_neighborhood(232629023, hops=1, max_nodes=30),
            "ml_prediction": {"illicit_probability": 0.99, "risk_category": "Critical", "predicted_label": "1"},
            "notes": [],
        }

        # Force deterministic fallback by removing GROQ_API_KEY from environment temporarily
        import os
        old_key = os.environ.get("GROQ_API_KEY")
        if "GROQ_API_KEY" in os.environ:
            del os.environ["GROQ_API_KEY"]

        try:
            result = synthesize_forensics_node(state)
            report = result["final_report"]

            self.assertFalse(result["llm_used"])
            self.assertIn("Deterministic Rule-Based Forensic Engine", report)
            self.assertNotIn("freeze counterparty hops", report.lower())
            self.assertNotIn("flag address for enhanced sar", report.lower())
            self.assertIn("human review", report.lower())
            self.assertIn("academic research", report.lower())
            self.assertIn("do not initiate automated asset freezes", report.lower())
        finally:
            if old_key is not None:
                os.environ["GROQ_API_KEY"] = old_key


class TestDossierAndNetworkExplorerConsistency(unittest.TestCase):
    """Test consistency between compiled investigation dossier and network topology explorer."""

    def test_dossier_matches_network_explorer(self):
        """Dossier and network neighborhood must agree on target ID, time step, and direct degrees."""
        tx_id = 96564456
        dossier = compile_investigation_dossier(tx_id)
        neigh = get_transaction_neighborhood(tx_id, hops=1, max_nodes=50)

        self.assertEqual(dossier["txId"], neigh["center_node"])
        self.assertEqual(
            dossier["graph_metrics"]["in_degree"],
            neigh["direct_predecessors_count"],
        )
        self.assertEqual(
            dossier["graph_metrics"]["out_degree"],
            neigh["direct_successors_count"],
        )

    def test_pdf_dossier_compilation_with_new_schema(self):
        """PDF generation must successfully render the enriched, compliant dossier schema."""
        tx_id = 232629023
        pdf_path = generate_forensic_pdf_report(tx_id=tx_id, generated_by="AUDITOR-TEST")
        self.assertTrue(pdf_path.exists())
        self.assertGreater(pdf_path.stat().st_size, 4500)


if __name__ == "__main__":
    unittest.main()
