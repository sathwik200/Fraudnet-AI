#!/usr/bin/env python3
"""
FRAUDNET AI — Data Pipeline Tests
====================================
Automated tests for the preprocessing pipeline.
Tests verify counts, schemas, label preservation, ID alignment,
time steps, and unknown-label integrity against the actual dataset.

Run with:
    python -m pytest tests/test_data_pipeline.py -v
or:
    python tests/test_data_pipeline.py
"""

import json
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import build_feature_column_names, load_all, load_classes, load_edgelist
from src.data.validator import (
    EXPECTED_TIME_STEPS,
    VALID_CLASS_LABELS,
    validate_all,
    validate_classes,
    validate_cross_file,
    validate_edges,
    validate_features,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "elliptic"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# ---------------------------------------------------------------------------
# Expected values from dataset inspection
# ---------------------------------------------------------------------------
EXPECTED_TRANSACTIONS = 203_769
EXPECTED_EDGES = 234_355
EXPECTED_UNIQUE_NODES = 203_769
EXPECTED_ILLICIT = 4_545
EXPECTED_LICIT = 42_019
EXPECTED_UNKNOWN = 157_205
EXPECTED_NUM_COLS = 167
EXPECTED_LOCAL_FEATURES = 93
EXPECTED_AGG_FEATURES = 72


class TestColumnNames(unittest.TestCase):
    """Test column name generation."""

    def test_column_count(self):
        cols = build_feature_column_names()
        self.assertEqual(len(cols), EXPECTED_NUM_COLS)

    def test_first_two_columns(self):
        cols = build_feature_column_names()
        self.assertEqual(cols[0], "txId")
        self.assertEqual(cols[1], "time_step")

    def test_local_feature_names(self):
        cols = build_feature_column_names()
        local = [c for c in cols if c.startswith("local_feature_")]
        self.assertEqual(len(local), EXPECTED_LOCAL_FEATURES)
        self.assertEqual(local[0], "local_feature_1")
        self.assertEqual(local[-1], "local_feature_93")

    def test_agg_feature_names(self):
        cols = build_feature_column_names()
        agg = [c for c in cols if c.startswith("agg_feature_")]
        self.assertEqual(len(agg), EXPECTED_AGG_FEATURES)
        self.assertEqual(agg[0], "agg_feature_1")
        self.assertEqual(agg[-1], "agg_feature_72")

    def test_no_duplicate_names(self):
        cols = build_feature_column_names()
        self.assertEqual(len(cols), len(set(cols)))


class TestLoader(unittest.TestCase):
    """Test data loading from raw CSVs."""

    @classmethod
    def setUpClass(cls):
        """Load all data once for the test class."""
        cls.features, cls.classes, cls.edges = load_all()

    def test_features_shape(self):
        self.assertEqual(self.features.shape[0], EXPECTED_TRANSACTIONS)
        self.assertEqual(self.features.shape[1], EXPECTED_NUM_COLS)

    def test_features_no_header_contamination(self):
        """The first row should be data, not a header string."""
        first_txid = self.features["txId"].iloc[0]
        # Verify txId is numeric integer, not a string header
        self.assertTrue(
            np.issubdtype(type(first_txid), np.integer),
            f"First txId should be an integer, got {type(first_txid)}: {first_txid}"
        )

    def test_features_column_names(self):
        self.assertEqual(self.features.columns[0], "txId")
        self.assertEqual(self.features.columns[1], "time_step")
        self.assertEqual(self.features.columns[2], "local_feature_1")
        self.assertEqual(self.features.columns[-1], "agg_feature_72")

    def test_features_dtypes(self):
        self.assertTrue(pd.api.types.is_integer_dtype(self.features["txId"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.features["time_step"]))
        self.assertTrue(pd.api.types.is_float_dtype(self.features["local_feature_1"]))

    def test_classes_shape(self):
        self.assertEqual(self.classes.shape[0], EXPECTED_TRANSACTIONS)
        self.assertEqual(self.classes.shape[1], 2)

    def test_classes_columns(self):
        self.assertIn("txId", self.classes.columns)
        self.assertIn("label", self.classes.columns)

    def test_classes_label_values(self):
        actual = set(self.classes["label"].unique())
        self.assertEqual(actual, VALID_CLASS_LABELS)

    def test_edges_shape(self):
        self.assertEqual(self.edges.shape[0], EXPECTED_EDGES)
        self.assertEqual(self.edges.shape[1], 2)

    def test_edges_columns(self):
        self.assertIn("txId1", self.edges.columns)
        self.assertIn("txId2", self.edges.columns)

    def test_edges_dtypes(self):
        self.assertTrue(pd.api.types.is_integer_dtype(self.edges["txId1"]))
        self.assertTrue(pd.api.types.is_integer_dtype(self.edges["txId2"]))


class TestValidator(unittest.TestCase):
    """Test validation logic against loaded data."""

    @classmethod
    def setUpClass(cls):
        cls.features, cls.classes, cls.edges = load_all()

    def test_features_validation_passes(self):
        report = validate_features(self.features)
        self.assertTrue(report["all_passed"],
                        f"Feature validation failed: {report['checks']}")

    def test_classes_validation_passes(self):
        report = validate_classes(self.classes)
        self.assertTrue(report["all_passed"],
                        f"Classes validation failed: {report['checks']}")

    def test_edges_validation_passes(self):
        report = validate_edges(self.edges)
        self.assertTrue(report["all_passed"],
                        f"Edges validation failed: {report['checks']}")

    def test_cross_file_validation_passes(self):
        report = validate_cross_file(self.features, self.classes, self.edges)
        self.assertTrue(report["all_passed"],
                        f"Cross-file validation failed: {report['checks']}")

    def test_full_validation_passes(self):
        report, passed = validate_all(self.features, self.classes, self.edges,
                                       verbose=False)
        self.assertTrue(passed)


class TestTransactionCounts(unittest.TestCase):
    """Test exact transaction, edge, and label counts."""

    @classmethod
    def setUpClass(cls):
        cls.features, cls.classes, cls.edges = load_all()

    def test_exact_transaction_count(self):
        self.assertEqual(len(self.features), EXPECTED_TRANSACTIONS)

    def test_exact_edge_count(self):
        self.assertEqual(len(self.edges), EXPECTED_EDGES)

    def test_exact_illicit_count(self):
        count = (self.classes["label"] == "1").sum()
        self.assertEqual(count, EXPECTED_ILLICIT)

    def test_exact_licit_count(self):
        count = (self.classes["label"] == "2").sum()
        self.assertEqual(count, EXPECTED_LICIT)

    def test_exact_unknown_count(self):
        count = (self.classes["label"] == "unknown").sum()
        self.assertEqual(count, EXPECTED_UNKNOWN)

    def test_label_counts_sum(self):
        total = (EXPECTED_ILLICIT + EXPECTED_LICIT + EXPECTED_UNKNOWN)
        self.assertEqual(total, EXPECTED_TRANSACTIONS)
        self.assertEqual(len(self.classes), EXPECTED_TRANSACTIONS)

    def test_unique_transaction_ids(self):
        self.assertEqual(self.features["txId"].nunique(), EXPECTED_TRANSACTIONS)

    def test_no_duplicate_txids_features(self):
        self.assertFalse(self.features["txId"].duplicated().any())

    def test_no_duplicate_txids_classes(self):
        self.assertFalse(self.classes["txId"].duplicated().any())


class TestTimeSteps(unittest.TestCase):
    """Test time step integrity."""

    @classmethod
    def setUpClass(cls):
        cls.features, _, _ = load_all()

    def test_time_step_count(self):
        self.assertEqual(self.features["time_step"].nunique(), EXPECTED_TIME_STEPS)

    def test_time_step_range(self):
        self.assertEqual(self.features["time_step"].min(), 1)
        self.assertEqual(self.features["time_step"].max(), 49)

    def test_all_time_steps_present(self):
        expected = set(range(1, 50))
        actual = set(self.features["time_step"].unique())
        self.assertEqual(actual, expected)


class TestIDAlignment(unittest.TestCase):
    """Test that transaction IDs are consistent across files."""

    @classmethod
    def setUpClass(cls):
        cls.features, cls.classes, cls.edges = load_all()

    def test_features_classes_id_match(self):
        feat_ids = set(self.features["txId"].unique())
        cls_ids = set(self.classes["txId"].unique())
        self.assertEqual(feat_ids, cls_ids)

    def test_edge_endpoints_exist_in_features(self):
        feat_ids = set(self.features["txId"].unique())
        edge_nodes = set(self.edges["txId1"].unique()) | set(self.edges["txId2"].unique())
        orphans = edge_nodes - feat_ids
        self.assertEqual(len(orphans), 0,
                         f"Found {len(orphans)} orphan edge nodes")

    def test_unique_nodes_in_edges(self):
        edge_nodes = set(self.edges["txId1"].unique()) | set(self.edges["txId2"].unique())
        self.assertEqual(len(edge_nodes), EXPECTED_UNIQUE_NODES)


class TestUnknownLabelPreservation(unittest.TestCase):
    """Test that unknown labels are never silently converted or dropped."""

    @classmethod
    def setUpClass(cls):
        cls.features, cls.classes, cls.edges = load_all()

    def test_unknown_count_preserved(self):
        count = (self.classes["label"] == "unknown").sum()
        self.assertEqual(count, EXPECTED_UNKNOWN,
                         "Unknown labels were modified or dropped!")

    def test_unknown_not_converted_to_licit(self):
        """Specifically guard against unknown → licit conversion."""
        licit_count = (self.classes["label"] == "2").sum()
        self.assertEqual(licit_count, EXPECTED_LICIT,
                         "Licit count changed — possible unknown→licit conversion!")

    def test_no_null_labels(self):
        self.assertEqual(self.classes["label"].isna().sum(), 0)

    def test_label_column_is_string(self):
        self.assertTrue(pd.api.types.is_string_dtype(self.classes["label"]))

    def test_only_valid_labels(self):
        actual = set(self.classes["label"].unique())
        self.assertEqual(actual, {"1", "2", "unknown"})


class TestProcessedOutputs(unittest.TestCase):
    """Test the processed Parquet output files."""

    @classmethod
    def setUpClass(cls):
        """Check if processed files exist; skip if not."""
        cls.tx_path = PROCESSED_DIR / "transactions.parquet"
        cls.edge_path = PROCESSED_DIR / "edges.parquet"
        cls.summary_path = PROCESSED_DIR / "dataset_summary.json"

        if not cls.tx_path.exists():
            raise unittest.SkipTest("Processed files not found. Run preprocessor first.")

        cls.transactions = pd.read_parquet(cls.tx_path)
        cls.edges = pd.read_parquet(cls.edge_path)
        with open(cls.summary_path) as f:
            cls.summary = json.load(f)

    def test_transactions_row_count(self):
        self.assertEqual(len(self.transactions), EXPECTED_TRANSACTIONS)

    def test_transactions_has_label(self):
        self.assertIn("label", self.transactions.columns)

    def test_transactions_has_txid(self):
        self.assertIn("txId", self.transactions.columns)

    def test_transactions_has_time_step(self):
        self.assertIn("time_step", self.transactions.columns)

    def test_transactions_has_features(self):
        local = [c for c in self.transactions.columns if c.startswith("local_feature_")]
        agg = [c for c in self.transactions.columns if c.startswith("agg_feature_")]
        self.assertEqual(len(local), EXPECTED_LOCAL_FEATURES)
        self.assertEqual(len(agg), EXPECTED_AGG_FEATURES)

    def test_transactions_label_not_in_features(self):
        """Label must NOT appear among feature column names."""
        feature_cols = [c for c in self.transactions.columns
                        if c.startswith(("local_feature_", "agg_feature_"))]
        self.assertNotIn("label", feature_cols)

    def test_transactions_column_count(self):
        # txId + time_step + 93 local + 72 agg + label = 168
        self.assertEqual(len(self.transactions.columns), EXPECTED_NUM_COLS + 1)

    def test_edges_row_count(self):
        self.assertEqual(len(self.edges), EXPECTED_EDGES)

    def test_edges_columns(self):
        self.assertListEqual(list(self.edges.columns), ["txId1", "txId2"])

    def test_processed_illicit_count(self):
        count = (self.transactions["label"] == "1").sum()
        self.assertEqual(count, EXPECTED_ILLICIT)

    def test_processed_licit_count(self):
        count = (self.transactions["label"] == "2").sum()
        self.assertEqual(count, EXPECTED_LICIT)

    def test_processed_unknown_count(self):
        count = (self.transactions["label"] == "unknown").sum()
        self.assertEqual(count, EXPECTED_UNKNOWN)

    def test_processed_time_steps(self):
        self.assertEqual(self.transactions["time_step"].nunique(), EXPECTED_TIME_STEPS)

    def test_summary_json_valid(self):
        self.assertIn("transactions", self.summary)
        self.assertIn("edges", self.summary)
        self.assertIn("validation_passed", self.summary)

    def test_summary_transaction_count(self):
        self.assertEqual(
            self.summary["transactions"]["total_transactions"],
            EXPECTED_TRANSACTIONS,
        )

    def test_summary_edge_count(self):
        self.assertEqual(
            self.summary["edges"]["total_edges"],
            EXPECTED_EDGES,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
