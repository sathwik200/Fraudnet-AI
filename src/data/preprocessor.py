#!/usr/bin/env python3
"""
FRAUDNET AI — Data Preprocessor
==================================
Combines the three Elliptic dataset DataFrames into unified processed outputs.

Pipeline:
    1. Load raw CSVs via loader
    2. Validate via validator
    3. Merge features + class labels on txId
    4. Preserve all 203,769 transactions, 234,355 edges, 49 time steps
    5. Save to data/processed/ as Parquet + JSON summary

Design rules:
    - Never drop unknown-class transactions
    - Never convert "unknown" → "licit" or any other label
    - Never fabricate records
    - Never use labels as input features
    - No feature scaling at this stage
    - No synthetic data generation
    - Original raw files are never modified
"""

import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw" / "elliptic"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

OUTPUT_TRANSACTIONS = PROCESSED_DIR / "transactions.parquet"
OUTPUT_EDGES = PROCESSED_DIR / "edges.parquet"
OUTPUT_SUMMARY = PROCESSED_DIR / "dataset_summary.json"


# ---------------------------------------------------------------------------
# Preprocessing steps
# ---------------------------------------------------------------------------
def merge_features_and_labels(
    features_df: pd.DataFrame,
    classes_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Merge feature vectors with class labels on txId.

    The merge is an inner join, but since inspection confirmed a perfect 1:1
    match between features and classes, the result should equal the input size.
    We verify this and raise if rows are lost.
    """
    n_before = len(features_df)

    # Merge on txId
    transactions = features_df.merge(classes_df, on="txId", how="inner")

    n_after = len(transactions)
    if n_after != n_before:
        raise ValueError(
            f"Merge changed row count: {n_before:,} → {n_after:,}. "
            f"Lost {n_before - n_after:,} rows. "
            f"This indicates a features/classes ID mismatch."
        )

    # Verify label column is present and not used as a feature
    assert "label" in transactions.columns, "Missing 'label' column after merge"

    # Verify label is NOT among feature columns
    feature_cols = [c for c in transactions.columns
                    if c.startswith(("local_feature_", "agg_feature_"))]
    assert "label" not in feature_cols, "Label leaked into feature columns"

    return transactions


def validate_no_label_corruption(transactions_df: pd.DataFrame, original_classes_df: pd.DataFrame):
    """
    Verify that class labels were not silently modified during preprocessing.
    Specifically check that 'unknown' labels are preserved, not converted.
    """
    orig_dist = original_classes_df["label"].value_counts().to_dict()
    proc_dist = transactions_df["label"].value_counts().to_dict()

    for label_val in ["1", "2", "unknown"]:
        orig_count = orig_dist.get(label_val, 0)
        proc_count = proc_dist.get(label_val, 0)
        if orig_count != proc_count:
            raise ValueError(
                f"Label corruption detected for '{label_val}': "
                f"original={orig_count:,}, processed={proc_count:,}"
            )


def build_summary(
    transactions_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    validation_report: dict,
) -> dict:
    """Build a machine-readable summary of the processed dataset."""
    summary = OrderedDict()
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["pipeline"] = "FRAUDNET AI Preprocessing Pipeline v1.0"
    summary["source"] = "data/raw/elliptic/"

    # Transactions
    tx = OrderedDict()
    tx["total_transactions"] = len(transactions_df)
    tx["columns"] = list(transactions_df.columns)
    tx["num_columns"] = len(transactions_df.columns)

    feature_cols = [c for c in transactions_df.columns
                    if c.startswith(("local_feature_", "agg_feature_"))]
    tx["num_feature_columns"] = len(feature_cols)
    tx["num_local_features"] = sum(1 for c in feature_cols if c.startswith("local_feature_"))
    tx["num_agg_features"] = sum(1 for c in feature_cols if c.startswith("agg_feature_"))
    tx["unique_txIds"] = int(transactions_df["txId"].nunique())
    tx["time_steps"] = int(transactions_df["time_step"].nunique())
    tx["time_step_range"] = [int(transactions_df["time_step"].min()),
                              int(transactions_df["time_step"].max())]

    # Class distribution
    label_dist = transactions_df["label"].value_counts().to_dict()
    tx["class_distribution"] = {
        "illicit (1)": int(label_dist.get("1", 0)),
        "licit (2)": int(label_dist.get("2", 0)),
        "unknown": int(label_dist.get("unknown", 0)),
    }

    # Data types
    tx["dtypes"] = {col: str(transactions_df[col].dtype) for col in transactions_df.columns[:10]}
    tx["dtypes"]["..."] = f"({len(transactions_df.columns) - 10} more columns)"

    summary["transactions"] = tx

    # Edges
    eg = OrderedDict()
    eg["total_edges"] = len(edges_df)
    eg["columns"] = list(edges_df.columns)
    unique_edge_nodes = set(edges_df["txId1"].unique()) | set(edges_df["txId2"].unique())
    eg["unique_nodes"] = len(unique_edge_nodes)
    eg["dtypes"] = {col: str(edges_df[col].dtype) for col in edges_df.columns}
    summary["edges"] = eg

    # Output files
    summary["output_files"] = {
        "transactions": str(OUTPUT_TRANSACTIONS.relative_to(PROJECT_ROOT)),
        "edges": str(OUTPUT_EDGES.relative_to(PROJECT_ROOT)),
        "summary": str(OUTPUT_SUMMARY.relative_to(PROJECT_ROOT)),
    }

    # Validation summary
    summary["validation_passed"] = validation_report.get("all_passed", False)

    # Integrity notes
    summary["integrity_notes"] = [
        "All 'unknown' labels preserved as-is (never converted to 'licit')",
        "Labels are NOT included in feature columns",
        "No feature scaling applied",
        "No synthetic data generated",
        "No rows dropped",
        "Original raw files unmodified",
    ]

    return summary


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------
def run_pipeline(verbose: bool = True) -> dict:
    """
    Execute the full preprocessing pipeline.

    Returns the processing summary dict.
    """
    # Sibling module imports
    from src.data.loader import load_all
    from src.data.validator import validate_all

    if verbose:
        print()
        print("╔══════════════════════════════════════════════════════════════════════╗")
        print("║         FRAUDNET AI — Preprocessing Pipeline                       ║")
        print("╚══════════════════════════════════════════════════════════════════════╝")
        print()

    # --- Step 1: Load ---
    if verbose:
        print("[1/6] Loading raw dataset...")
    features_df, classes_df, edges_df = load_all()
    if verbose:
        print(f"      Features: {features_df.shape}")
        print(f"      Classes:  {classes_df.shape}")
        print(f"      Edges:    {edges_df.shape}")

    # --- Step 2: Validate ---
    if verbose:
        print("\n[2/6] Validating loaded data...")
    validation_report, all_passed = validate_all(features_df, classes_df, edges_df,
                                                  verbose=verbose)
    if not all_passed:
        print("\n⚠️  WARNING: Some validation checks failed. Proceeding with caution.\n")

    # --- Step 3: Merge features + labels ---
    if verbose:
        print("[3/6] Merging features and class labels...")
    transactions_df = merge_features_and_labels(features_df, classes_df)
    if verbose:
        print(f"      Merged transactions: {transactions_df.shape}")
        print(f"      Columns: txId, time_step, "
              f"{sum(1 for c in transactions_df.columns if c.startswith('local_feature_'))} local features, "
              f"{sum(1 for c in transactions_df.columns if c.startswith('agg_feature_'))} agg features, label")

    # --- Step 4: Verify label integrity ---
    if verbose:
        print("\n[4/6] Verifying label integrity...")
    validate_no_label_corruption(transactions_df, classes_df)
    label_dist = transactions_df["label"].value_counts()
    if verbose:
        print(f"      Illicit (1):  {label_dist.get('1', 0):>8,}")
        print(f"      Licit (2):    {label_dist.get('2', 0):>8,}")
        print(f"      Unknown:      {label_dist.get('unknown', 0):>8,}")
        print(f"      Total:        {len(transactions_df):>8,}")
        print("      ✓ Label integrity verified — no corruption detected")

    # --- Step 5: Save outputs ---
    if verbose:
        print(f"\n[5/6] Saving processed data to {PROCESSED_DIR}/...")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    transactions_df.to_parquet(OUTPUT_TRANSACTIONS, index=False, engine="pyarrow")
    edges_df.to_parquet(OUTPUT_EDGES, index=False, engine="pyarrow")
    if verbose:
        tx_size = OUTPUT_TRANSACTIONS.stat().st_size
        edge_size = OUTPUT_EDGES.stat().st_size
        print(f"      transactions.parquet: {tx_size / 1024 / 1024:.2f} MB")
        print(f"      edges.parquet:        {edge_size / 1024 / 1024:.2f} MB")

    # --- Step 6: Write summary JSON ---
    if verbose:
        print("\n[6/6] Writing dataset summary...")
    summary = build_summary(transactions_df, edges_df, validation_report)
    with open(OUTPUT_SUMMARY, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    if verbose:
        print(f"      {OUTPUT_SUMMARY}")

    if verbose:
        print()
        print("═" * 72)
        print("  PREPROCESSING COMPLETE")
        print("═" * 72)
        print(f"  Transactions: {len(transactions_df):,}")
        print(f"  Edges:        {len(edges_df):,}")
        print(f"  Time steps:   {transactions_df['time_step'].nunique()}")
        print(f"  Validation:   {'ALL PASSED ✓' if all_passed else 'ISSUES FOUND ⚠️'}")
        print("═" * 72)
        print()

    return summary


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    summary = run_pipeline(verbose=True)

