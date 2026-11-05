"""
FRAUDNET AI — Transaction Forensics Presets & State Verification Tests
======================================================================
Validates that:
1. All Quick Target Presets in SAMPLE_TARGETS map to authentic transactions in the processed dataset.
2. Ground truth labels strictly match their semantic names:
   - Illicit presets resolve to label '1' with high ML illicit probability.
   - Licit presets resolve to label '2' with low ML illicit probability.
   - Unknown presets resolve to label 'unknown'.
3. Every preset supports full forensic profiling, graph neighborhood extraction,
   explainability attribution, and PDF report compilation.
4. Session-state preset switching and input sanitization logic behave deterministically.
"""

import unittest
from pathlib import Path
import sys
import pyarrow.parquet as pq

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ui.transaction_search import SAMPLE_TARGETS
from src.tools.transaction_tools import get_full_transaction_profile
from src.tools.graph_tools import get_transaction_neighborhood
from src.reports.report_generator import generate_forensic_pdf_report


class TestTransactionSearchPresets(unittest.TestCase):
    """Test suite for forensic search presets and dataset ground-truth integrity."""

    @classmethod
    def setUpClass(cls):
        """Load transactions parquet table once for rapid ground truth lookup."""
        cls.parquet_path = PROJECT_ROOT / "data" / "processed" / "transactions.parquet"
        cls.assertTrue(cls.parquet_path.exists(), f"Processed transactions file not found at {cls.parquet_path}")

        table = pq.read_table(str(cls.parquet_path), columns=["txId", "label", "time_step"])
        cls.df_tx = table.to_pandas().set_index("txId")

    def test_presets_exist_in_dataset(self):
        """All configured sample preset transactions must exist in transactions.parquet."""
        self.assertGreaterEqual(len(SAMPLE_TARGETS), 5, "Expected at least 5 target presets.")

        for label, tx_id in SAMPLE_TARGETS.items():
            self.assertIn(
                tx_id,
                self.df_tx.index,
                f"Preset '{label}' with txId {tx_id} is missing from transactions.parquet!",
            )

    def test_preset_ground_truth_semantics(self):
        """Illicit presets must have label '1', licit '2', and unknown 'unknown'."""
        for label, tx_id in SAMPLE_TARGETS.items():
            row = self.df_tx.loc[tx_id]
            actual_label = str(row["label"])

            if "ILLICIT" in label:
                self.assertEqual(
                    actual_label,
                    "1",
                    f"Illicit preset '{label}' (txId {tx_id}) has actual label '{actual_label}', expected '1'.",
                )
            elif "LICIT" in label:
                self.assertEqual(
                    actual_label,
                    "2",
                    f"Licit preset '{label}' (txId {tx_id}) has actual label '{actual_label}', expected '2'.",
                )
            elif "UNKNOWN" in label:
                self.assertEqual(
                    actual_label,
                    "unknown",
                    f"Unknown preset '{label}' (txId {tx_id}) has actual label '{actual_label}', expected 'unknown'.",
                )

    def test_preset_full_profile_and_ml_risk(self):
        """Each preset must return a full profile with coherent ML assessment and graph metrics."""
        for label, tx_id in SAMPLE_TARGETS.items():
            profile = get_full_transaction_profile(tx_id)
            self.assertIsNotNone(profile, f"get_full_transaction_profile returned None for txId {tx_id}")

            self.assertEqual(profile["txId"], tx_id)
            self.assertIn("ml_assessment", profile)
            self.assertIn("graph_metrics", profile)
            self.assertIn("explainability", profile)

            ml = profile["ml_assessment"]
            prob = ml["illicit_probability"]

            if "ILLICIT" in label:
                self.assertGreaterEqual(
                    prob,
                    0.80,
                    f"Illicit preset '{label}' ({tx_id}) expected high illicit probability >= 0.80, got {prob}",
                )
                self.assertIn(ml["risk_category"], ["Critical", "High"])
            elif "LICIT" in label:
                self.assertLessEqual(
                    prob,
                    0.20,
                    f"Licit preset '{label}' ({tx_id}) expected low illicit probability <= 0.20, got {prob}",
                )
                self.assertEqual(ml["risk_category"], "Low")

    def test_preset_graph_neighborhood_extraction(self):
        """Each preset must extract an ego network neighborhood without errors."""
        for label, tx_id in SAMPLE_TARGETS.items():
            neigh = get_transaction_neighborhood(tx_id, hops=1, max_nodes=25)
            self.assertIsInstance(neigh, dict)
            self.assertIn("nodes", neigh)
            self.assertIn("edges", neigh)
            self.assertGreater(len(neigh["nodes"]), 0, f"No ego nodes extracted for {label} ({tx_id})")

    def test_preset_pdf_report_compilation(self):
        """Each preset must compile a pure-Python forensic PDF report exceeding 4 KB."""
        for label, tx_id in SAMPLE_TARGETS.items():
            pdf_path = generate_forensic_pdf_report(tx_id=tx_id, generated_by="TEST-PRESET-AUDITOR")
            self.assertTrue(pdf_path.exists())
            self.assertGreater(
                pdf_path.stat().st_size,
                4000,
                f"PDF report for {label} ({tx_id}) suspiciously small ({pdf_path.stat().st_size} bytes)",
            )


class TestSessionStatePresetSwitching(unittest.TestCase):
    """Test state update simulation for Streamlit preset button interaction."""

    def test_preset_selection_updates_both_states(self):
        """Simulate clicking a preset button: active_tx_id and input value must both update."""
        fake_session_state = {
            "active_tx_id": 230425980,
            "tx_search_input_val": "230425980",
        }

        # User clicks "ILLICIT AGGREGATION #1" (232629023)
        clicked_tx = SAMPLE_TARGETS["🔴 ILLICIT AGGREGATION #1"]
        fake_session_state["active_tx_id"] = clicked_tx
        fake_session_state["tx_search_input_val"] = str(clicked_tx)

        self.assertEqual(fake_session_state["active_tx_id"], 232629023)
        self.assertEqual(fake_session_state["tx_search_input_val"], "232629023")

    def test_manual_input_entry_validation(self):
        """Simulate manual numeric typing and pressing enter."""
        raw_valid = " 96564456 \n"
        clean = raw_valid.strip()
        self.assertTrue(clean.isdigit())
        self.assertEqual(int(clean), 96564456)

        raw_invalid = "0xBAD123"
        self.assertFalse(raw_invalid.strip().isdigit())

    def test_streamlit_apptest_preset_click(self):
        """End-to-end Streamlit interaction test using AppTest."""
        from streamlit.testing.v1 import AppTest

        at = AppTest.from_file(str(PROJECT_ROOT / "app.py"))
        at.run(timeout=15)
        self.assertFalse(at.exception)

        # Navigate to Transaction Forensics page
        sidebar_nav = at.sidebar.radio[0]
        sidebar_nav.set_value("🔍 02 // TRANSACTION FORENSICS").run()
        self.assertFalse(at.exception)

        # Find the PEELING preset button
        btn_peeling = None
        for b in at.button:
            if "PEELING" in b.label:
                btn_peeling = b
                break

        self.assertIsNotNone(btn_peeling, "Peeling preset button not found in page")
        btn_peeling.click().run()
        self.assertFalse(at.exception)

        # Verify that clicking the button updated the active text input value
        self.assertEqual(at.text_input[0].value, "96564456")


if __name__ == "__main__":
    unittest.main()
