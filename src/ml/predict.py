#!/usr/bin/env python3
"""
FRAUDNET AI — Prediction Engine
================================
Inference service scoring Bitcoin transactions for fraud risk:
  - Generates illicit class probability p in [0, 1]
  - Applies calibrated decision threshold
  - Assigns standardized risk categories:
      * Low      : p < 0.25
      * Moderate : 0.25 <= p < 0.50
      * High     : 0.50 <= p < 0.75
      * Critical : p >= 0.75
  - Preserves ground-truth dataset labels separately (ground-truth unknown remains unknown)
"""

from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd
from src.ml.model_manager import load_model_bundle


def assign_risk_category(probability: float) -> str:
    """
    Map probability score to standardized risk categories.
    """
    if probability >= 0.75:
        return "Critical"
    elif probability >= 0.50:
        return "High"
    elif probability >= 0.25:
        return "Moderate"
    else:
        return "Low"


def predict_transaction_risk(
    transaction_row: Union[pd.Series, pd.DataFrame, Dict],
    model_bundle: Optional[Dict] = None,
) -> Dict[str, any]:
    """
    Score a single transaction record for illicit fraud risk.

    Args:
        transaction_row: Single transaction as Series, dict, or 1-row DataFrame.
        model_bundle: Optional preloaded bundle. If None, loads from default cache.

    Returns:
        Structured prediction dictionary with risk score, category, and metadata.
    """
    bundle = model_bundle or load_model_bundle()
    clf = bundle["model"]
    pipeline = bundle["feature_pipeline"]
    threshold = bundle.get("optimal_threshold", 0.5)
    version = bundle.get("version", "1.0.0")

    # Format input as 1-row DataFrame
    if isinstance(transaction_row, dict):
        df_row = pd.DataFrame([transaction_row])
    elif isinstance(transaction_row, pd.Series):
        df_row = pd.DataFrame([transaction_row])
    else:
        df_row = transaction_row.copy()

    tx_id = int(df_row["txId"].iloc[0]) if "txId" in df_row.columns else None
    ground_truth = str(df_row["label"].iloc[0]) if "label" in df_row.columns else "unknown"

    # Transform features using pre-fitted pipeline
    X_vec = pipeline.transform(df_row)

    # Predict probability for class 1 (illicit)
    if hasattr(clf, "predict_proba"):
        prob = float(clf.predict_proba(X_vec)[0, 1])
    else:
        prob = float(clf.predict(X_vec)[0])

    is_illicit_pred = bool(prob >= threshold)
    risk_cat = assign_risk_category(prob)

    return {
        "txId": tx_id,
        "illicit_probability": round(prob, 4),
        "predicted_label": "illicit" if is_illicit_pred else "licit",
        "predicted_class_id": 1 if is_illicit_pred else 2,
        "is_predicted_illicit": is_illicit_pred,
        "decision_threshold": round(threshold, 4),
        "risk_category": risk_cat,
        "ground_truth_label": ground_truth,
        "model_version": version,
        "model_name": bundle.get("model_name", "RandomForest"),
    }

