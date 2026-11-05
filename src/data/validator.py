#!/usr/bin/env python3
"""
FRAUDNET AI — Data Validator
==============================
Validates the loaded Elliptic dataset DataFrames for structural integrity,
cross-file consistency, and data quality.

All checks are non-destructive: the validator never modifies the data.
It returns a structured validation report dict and prints human-readable output.
"""

import pandas as pd
from collections import OrderedDict
from typing import Dict, Tuple


# ---------------------------------------------------------------------------
# Expected constants (from dataset inspection)
# ---------------------------------------------------------------------------
EXPECTED_FEATURES_COLS = 167        # txId + time_step + 93 local + 72 aggregate
EXPECTED_FEATURE_COLS_EXCL = 165    # 93 local + 72 aggregate (pure feature columns)
EXPECTED_TIME_STEPS = 49
EXPECTED_TIME_STEP_RANGE = (1, 49)
VALID_CLASS_LABELS = {"1", "2", "unknown"}


# ---------------------------------------------------------------------------
# Individual validators
# ---------------------------------------------------------------------------
def validate_features(df: pd.DataFrame) -> Dict:
    """Validate the features DataFrame."""
    report = OrderedDict()
    report["name"] = "features"
    report["checks"] = []

    def check(name: str, passed: bool, detail: str = ""):
        report["checks"].append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        return passed

    # 1. Shape
    n_rows, n_cols = df.shape
    check("row_count_positive",
          n_rows > 0,
          f"{n_rows:,} rows")
    check("column_count",
          n_cols == EXPECTED_FEATURES_COLS,
          f"expected={EXPECTED_FEATURES_COLS}, actual={n_cols}")

    # 2. Required columns exist
    check("txId_column_exists",
          "txId" in df.columns,
          f"columns[:3] = {list(df.columns[:3])}")
    check("time_step_column_exists",
          "time_step" in df.columns,
          "")

    # 3. Unique transaction IDs
    n_unique = df["txId"].nunique()
    check("txId_unique",
          n_unique == n_rows,
          f"rows={n_rows:,}, unique_txIds={n_unique:,}, "
          f"duplicates={n_rows - n_unique:,}")

    # 4. No null txIds
    null_txids = df["txId"].isna().sum()
    check("txId_no_nulls",
          null_txids == 0,
          f"null txIds: {null_txids}")

    # 5. Time step range
    ts_min, ts_max = df["time_step"].min(), df["time_step"].max()
    n_ts = df["time_step"].nunique()
    check("time_step_range",
          ts_min == EXPECTED_TIME_STEP_RANGE[0] and ts_max == EXPECTED_TIME_STEP_RANGE[1],
          f"range=[{ts_min}, {ts_max}], unique={n_ts}")
    check("time_step_count",
          n_ts == EXPECTED_TIME_STEPS,
          f"expected={EXPECTED_TIME_STEPS}, actual={n_ts}")

    # 6. Feature columns are numeric
    feature_cols = [c for c in df.columns if c.startswith(("local_feature_", "agg_feature_"))]
    non_numeric = [c for c in feature_cols if not pd.api.types.is_numeric_dtype(df[c])]
    check("feature_columns_numeric",
          len(non_numeric) == 0,
          f"non-numeric feature cols: {non_numeric[:5]}" if non_numeric else
          f"all {len(feature_cols)} feature columns are numeric")

    # 7. Missing values in features
    feature_nulls = df[feature_cols].isna().sum().sum()
    check("feature_no_missing_values",
          feature_nulls == 0,
          f"total missing values across features: {feature_nulls}")

    # 8. Feature dimensions
    check("local_feature_count",
          sum(1 for c in df.columns if c.startswith("local_feature_")) == 93,
          f"expected 93 local features")
    check("agg_feature_count",
          sum(1 for c in df.columns if c.startswith("agg_feature_")) == 72,
          f"expected 72 aggregate features")

    report["row_count"] = n_rows
    report["col_count"] = n_cols
    report["unique_txIds"] = n_unique
    report["time_steps"] = n_ts
    report["all_passed"] = all(c["passed"] for c in report["checks"])

    return report


def validate_classes(df: pd.DataFrame) -> Dict:
    """Validate the classes DataFrame."""
    report = OrderedDict()
    report["name"] = "classes"
    report["checks"] = []

    def check(name: str, passed: bool, detail: str = ""):
        report["checks"].append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        return passed

    n_rows, n_cols = df.shape

    # 1. Shape
    check("row_count_positive",
          n_rows > 0,
          f"{n_rows:,} rows")
    check("column_count",
          n_cols == 2,
          f"expected=2 (txId, label), actual={n_cols}")

    # 2. Required columns
    check("txId_column_exists",
          "txId" in df.columns,
          f"columns = {list(df.columns)}")
    check("label_column_exists",
          "label" in df.columns,
          f"columns = {list(df.columns)}")

    # 3. Unique txIds
    n_unique = df["txId"].nunique()
    check("txId_unique",
          n_unique == n_rows,
          f"rows={n_rows:,}, unique={n_unique:,}")

    # 4. Valid class labels only
    actual_labels = set(df["label"].dropna().unique())
    unexpected = actual_labels - VALID_CLASS_LABELS
    check("valid_class_labels_only",
          len(unexpected) == 0,
          f"expected={VALID_CLASS_LABELS}, actual={actual_labels}, "
          f"unexpected={unexpected}" if unexpected else
          f"labels={actual_labels}")

    # 5. No null labels
    null_labels = df["label"].isna().sum()
    check("label_no_nulls",
          null_labels == 0,
          f"null labels: {null_labels}")

    # 6. Class distribution
    dist = df["label"].value_counts().to_dict()
    report["class_distribution"] = dist

    report["row_count"] = n_rows
    report["unique_txIds"] = n_unique
    report["all_passed"] = all(c["passed"] for c in report["checks"])

    return report


def validate_edges(df: pd.DataFrame) -> Dict:
    """Validate the edgelist DataFrame."""
    report = OrderedDict()
    report["name"] = "edgelist"
    report["checks"] = []

    def check(name: str, passed: bool, detail: str = ""):
        report["checks"].append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        return passed

    n_rows, n_cols = df.shape

    # 1. Shape
    check("row_count_positive",
          n_rows > 0,
          f"{n_rows:,} edges")
    check("column_count",
          n_cols == 2,
          f"expected=2 (txId1, txId2), actual={n_cols}")

    # 2. Required columns
    check("txId1_column_exists",
          "txId1" in df.columns,
          f"columns = {list(df.columns)}")
    check("txId2_column_exists",
          "txId2" in df.columns,
          f"columns = {list(df.columns)}")

    # 3. No null endpoints
    null1 = df["txId1"].isna().sum()
    null2 = df["txId2"].isna().sum()
    check("no_null_endpoints",
          null1 == 0 and null2 == 0,
          f"null txId1={null1}, null txId2={null2}")

    # 4. No self-loops
    self_loops = (df["txId1"] == df["txId2"]).sum()
    check("no_self_loops",
          self_loops == 0,
          f"self-loops: {self_loops}")

    report["edge_count"] = n_rows
    unique_nodes = set(df["txId1"].unique()) | set(df["txId2"].unique())
    report["unique_nodes_in_edges"] = len(unique_nodes)
    report["all_passed"] = all(c["passed"] for c in report["checks"])

    return report


# ---------------------------------------------------------------------------
# Cross-file validation
# ---------------------------------------------------------------------------
def validate_cross_file(
    features_df: pd.DataFrame,
    classes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
) -> Dict:
    """Validate consistency across the three DataFrames."""
    report = OrderedDict()
    report["name"] = "cross_file_consistency"
    report["checks"] = []

    def check(name: str, passed: bool, detail: str = ""):
        report["checks"].append({
            "check": name,
            "passed": passed,
            "detail": detail,
        })
        return passed

    feat_ids = set(features_df["txId"].unique())
    cls_ids = set(classes_df["txId"].unique())

    # 1. Features ↔ Classes ID alignment
    in_feat_not_cls = feat_ids - cls_ids
    in_cls_not_feat = cls_ids - feat_ids
    check("features_classes_id_match",
          len(in_feat_not_cls) == 0 and len(in_cls_not_feat) == 0,
          f"in_features_not_classes={len(in_feat_not_cls)}, "
          f"in_classes_not_features={len(in_cls_not_feat)}")

    # 2. Same row count
    check("features_classes_same_count",
          len(features_df) == len(classes_df),
          f"features={len(features_df):,}, classes={len(classes_df):,}")

    # 3. Edge endpoints exist in features
    edge_nodes = set(edges_df["txId1"].unique()) | set(edges_df["txId2"].unique())
    orphan_nodes = edge_nodes - feat_ids
    check("edge_endpoints_in_features",
          len(orphan_nodes) == 0,
          f"edge unique nodes={len(edge_nodes):,}, "
          f"orphan nodes={len(orphan_nodes)}")

    report["features_tx_count"] = len(feat_ids)
    report["classes_tx_count"] = len(cls_ids)
    report["edge_unique_nodes"] = len(edge_nodes)
    report["orphan_edge_nodes"] = len(orphan_nodes)
    report["all_passed"] = all(c["passed"] for c in report["checks"])

    return report


# ---------------------------------------------------------------------------
# Full validation
# ---------------------------------------------------------------------------
def validate_all(
    features_df: pd.DataFrame,
    classes_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    verbose: bool = True,
) -> Tuple[Dict, bool]:
    """
    Run all validation checks.

    Returns:
        (full_report_dict, all_passed_bool)
    """
    feat_report = validate_features(features_df)
    cls_report = validate_classes(classes_df)
    edge_report = validate_edges(edges_df)
    cross_report = validate_cross_file(features_df, classes_df, edges_df)

    full_report = OrderedDict()
    full_report["features"] = feat_report
    full_report["classes"] = cls_report
    full_report["edgelist"] = edge_report
    full_report["cross_file"] = cross_report

    all_passed = all(r["all_passed"] for r in full_report.values())
    full_report["all_passed"] = all_passed

    if verbose:
        print_report(full_report)

    return full_report, all_passed


def print_report(report: Dict):
    """Print a human-readable validation report."""
    total_checks = 0
    total_passed = 0

    for section_key in ["features", "classes", "edgelist", "cross_file"]:
        section = report[section_key]
        print(f"\n{'='*60}")
        print(f"  VALIDATION: {section['name']}")
        print(f"{'='*60}")
        for c in section["checks"]:
            status = "✓ PASS" if c["passed"] else "✗ FAIL"
            print(f"  {status}  {c['check']}")
            if c["detail"]:
                print(f"           {c['detail']}")
            total_checks += 1
            if c["passed"]:
                total_passed += 1

    print(f"\n{'='*60}")
    print(f"  SUMMARY: {total_passed}/{total_checks} checks passed")
    all_ok = "ALL PASSED ✓" if report["all_passed"] else "SOME FAILED ✗"
    print(f"  {all_ok}")
    print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Main (for standalone testing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from src.data.loader import load_all

    print("Loading dataset...")
    features, classes, edges = load_all()

    print("Running validation...")
    report, passed = validate_all(features, classes, edges)

    if not passed:
        print("WARNING: Some validation checks failed!")
    else:
        print("All validation checks passed.")

