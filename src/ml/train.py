#!/usr/bin/env python3
"""
FRAUDNET AI — Model Training and Selection Pipeline
====================================================
Trains, compares, and evaluates multiple fraud detection classifiers using
chronological splits on the Elliptic Bitcoin dataset:

Models Evaluated:
  1. Balanced Logistic Regression (Linear baseline)
  2. Balanced Random Forest (Non-linear ensemble baseline)
  3. Balanced Histogram Gradient Boosting (Gradient-boosted decision trees)

Key Integrity Enforcements:
  - Strict temporal train (1-28), val (29-34), test (35-49) splits.
  - Preprocessing pipeline (imputation + scaling) fitted strictly on training data.
  - Unknown labels strictly excluded from training and supervised metrics.
  - Model selection guided by validation PR-AUC / illicit F1-score.
  - Final evaluation conducted on the untouched chronological test set.
"""

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression

from src.ml.data_split import create_chronological_splits, get_split_statistics
from src.ml.evaluate import evaluate_binary_model, find_optimal_threshold
from src.ml.feature_engineering import (
    FraudnetFeaturePipeline,
    load_raw_features_and_labels,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
TRANSACTIONS_PATH = DATA_DIR / "transactions.parquet"
ANALYTICS_METRICS_PATH = DATA_DIR / "analytics" / "transaction_metrics.parquet"
MODELS_DIR = PROJECT_ROOT / "models"
MODEL_BUNDLE_PATH = MODELS_DIR / "fraudnet_model_v1.joblib"
METRICS_SUMMARY_PATH = MODELS_DIR / "model_evaluation_summary.json"


def train_and_evaluate_all_models(
    transactions_path: Path = TRANSACTIONS_PATH,
    analytics_path: Optional[Path] = ANALYTICS_METRICS_PATH,
    include_graph_features: bool = True,
    output_model_path: Path = MODEL_BUNDLE_PATH,
    output_metrics_path: Path = METRICS_SUMMARY_PATH,
    verbose: bool = True,
) -> Dict[str, any]:
    """
    Execute full model training, cross-model comparison, and evaluation pipeline.
    """
    t_start = time.time()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    if verbose:
        print("\n" + "=" * 72)
        print("  FRAUDNET AI — SUPERVISED FRAUD-RISK MODELING PIPELINE")
        print("=" * 72)

    # 1. Load data
    if verbose:
        print("[1/6] Loading processed transactions and safe graph features...")
    df = load_raw_features_and_labels(
        transactions_path=transactions_path,
        analytics_metrics_path=analytics_path,
        include_graph_features=include_graph_features,
    )
    if verbose:
        print(f"      Total records: {len(df):,}, columns: {len(df.columns)}")

    # 2. Chronological data splits
    if verbose:
        print("[2/6] Generating chronological train/val/test splits...")
    train_df, val_df, full_train_df, test_df = create_chronological_splits(df)
    split_stats = get_split_statistics(train_df, val_df, test_df)

    if verbose:
        print(f"      Training set (TS 1..28):   {len(train_df):,} samples ({split_stats['train']['illicit_count']:,} illicit)")
        print(f"      Validation set (TS 29..34): {len(val_df):,} samples ({split_stats['validation']['illicit_count']:,} illicit)")
        print(f"      Test set (TS 35..49):       {len(test_df):,} samples ({split_stats['test']['illicit_count']:,} illicit)")

    # 3. Fit Preprocessing Pipeline strictly on Training data
    if verbose:
        print("[3/6] Fitting preprocessor strictly on training slice (no future leakage)...")
    preprocessor = FraudnetFeaturePipeline(include_graph_features=include_graph_features)
    preprocessor.fit(train_df)

    X_train = preprocessor.transform(train_df)
    y_train = train_df["target"].values

    X_val = preprocessor.transform(val_df)
    y_val = val_df["target"].values

    X_test = preprocessor.transform(test_df)
    y_test = test_df["target"].values

    if verbose:
        print(f"      Feature dimensions: {X_train.shape[1]} features")

    # 4. Define candidate models
    candidates = {
        "LogisticRegression": LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=42,
            solver="lbfgs",
        ),
        "RandomForest": RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            max_depth=16,
            random_state=42,
            n_jobs=-1,
        ),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            class_weight="balanced",
            max_iter=150,
            learning_rate=0.1,
            random_state=42,
        ),
    }

    # 5. Train and validate candidates
    if verbose:
        print("\n[4/6] Training and tuning candidate models...")

    model_evaluations = {}
    best_candidate_name = None
    best_candidate_prauc = -1.0
    best_threshold = 0.5

    for name, clf in candidates.items():
        t0 = time.time()
        clf.fit(X_train, y_train)
        fit_time = time.time() - t0

        # Evaluate on Validation set to tune decision threshold
        y_val_scores = clf.predict_proba(X_val)[:, 1]
        opt_thresh, opt_f1 = find_optimal_threshold(y_val, y_val_scores)

        val_eval = evaluate_binary_model(
            clf, X_val, y_val, threshold=opt_thresh, model_name=name
        )
        val_eval["training_time_seconds"] = round(fit_time, 2)

        # Track PR-AUC for candidate selection
        val_prauc = val_eval["metrics"]["pr_auc"]
        model_evaluations[name] = val_eval

        if verbose:
            m = val_eval["metrics"]
            print(f"      {name:<22}: Val PR-AUC={m['pr_auc']:.4f}, Illicit F1={m['f1_illicit']:.4f}, "
                  f"Recall={m['recall_illicit']:.4f}, Prec={m['precision_illicit']:.4f} (Thresh: {opt_thresh}) [{fit_time:.2f}s]")

        if val_prauc > best_candidate_prauc:
            best_candidate_prauc = val_prauc
            best_candidate_name = name
            best_threshold = opt_thresh

    if verbose:
        print(f"\n      Selected Champion Model: '{best_candidate_name}' based on Validation PR-AUC ({best_candidate_prauc:.4f})")

    # 6. Final Model Retraining on Full Train (TS 1..34) & Test Evaluation (TS 35..49)
    if verbose:
        print("\n[5/6] Retraining selected model on combined historical period (TS 1..34)...")

    # Fit preprocessor on full train
    full_preprocessor = FraudnetFeaturePipeline(include_graph_features=include_graph_features)
    full_preprocessor.fit(full_train_df)

    X_full_train = full_preprocessor.transform(full_train_df)
    y_full_train = full_train_df["target"].values
    X_final_test = full_preprocessor.transform(test_df)
    y_final_test = test_df["target"].values

    # Clone and fit selected champion model
    if best_candidate_name == "RandomForest":
        champion_clf = RandomForestClassifier(
            n_estimators=100, class_weight="balanced", max_depth=16, random_state=42, n_jobs=-1
        )
    elif best_candidate_name == "HistGradientBoosting":
        champion_clf = HistGradientBoostingClassifier(
            class_weight="balanced", max_iter=150, learning_rate=0.1, random_state=42
        )
    else:
        champion_clf = LogisticRegression(
            class_weight="balanced", max_iter=1000, random_state=42, solver="lbfgs"
        )

    t0 = time.time()
    champion_clf.fit(X_full_train, y_full_train)
    retrain_time = time.time() - t0

    # Final untouched Test Evaluation
    if verbose:
        print("[6/6] Evaluating champion model on untouched future Test Set (TS 35..49)...")
    final_test_eval = evaluate_binary_model(
        champion_clf,
        X_final_test,
        y_final_test,
        threshold=best_threshold,
        model_name=best_candidate_name,
    )
    final_test_eval["training_time_seconds"] = round(retrain_time, 2)

    if verbose:
        tm = final_test_eval["metrics"]
        cm = final_test_eval["confusion_matrix"]
        print("-" * 72)
        print(f"  CHAMPION MODEL TEST RESULTS ({best_candidate_name} @ Threshold {best_threshold}):")
        print(f"    - Illicit F1-Score:     {tm['f1_illicit']:.4f}")
        print(f"    - Illicit Precision:    {tm['precision_illicit']:.4f}")
        print(f"    - Illicit Recall:       {tm['recall_illicit']:.4f}")
        print(f"    - PR-AUC (Avg Prec):    {tm['pr_auc']:.4f}")
        print(f"    - ROC-AUC:              {tm['roc_auc']:.4f}")
        print(f"    - Accuracy:             {tm['accuracy']:.4f}")
        print(f"    - Confusion Matrix:     TP={cm['true_positives']}, FP={cm['false_positives']}, "
              f"FN={cm['false_negatives']}, TN={cm['true_negatives']}")
        print("-" * 72)

    # 7. Model Bundle Persistence
    model_bundle = {
        "model": champion_clf,
        "model_name": best_candidate_name,
        "feature_pipeline": full_preprocessor,
        "feature_names": full_preprocessor.feature_names_,
        "optimal_threshold": best_threshold,
        "test_evaluation": final_test_eval,
        "candidate_validation_evaluations": model_evaluations,
        "split_statistics": split_stats,
        "training_timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "python_version": "3.13.1",
    }

    joblib.dump(model_bundle, output_model_path)
    if verbose:
        size_mb = output_model_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved model bundle: {output_model_path} ({size_mb:.2f} MB)")

    # Save metrics summary JSON
    summary_data = {
        "project": "FRAUDNET AI",
        "selected_model": best_candidate_name,
        "decision_threshold": best_threshold,
        "training_timestamp": model_bundle["training_timestamp"],
        "splits": split_stats,
        "candidate_validation_comparison": {
            name: ev["metrics"] for name, ev in model_evaluations.items()
        },
        "test_metrics": final_test_eval["metrics"],
        "confusion_matrix": final_test_eval["confusion_matrix"],
        "error_analysis": final_test_eval["error_analysis"],
        "roc_curve": final_test_eval["roc_curve"],
        "pr_curve": final_test_eval["pr_curve"],
    }

    with open(output_metrics_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    if verbose:
        print(f"  ✓ Saved metrics summary: {output_metrics_path}")

    total_time = time.time() - t_start
    if verbose:
        print(f"\nModel training and evaluation finished in {total_time:.2f}s.\n")

    return summary_data


def main():
    train_and_evaluate_all_models(verbose=True)


if __name__ == "__main__":
    main()
