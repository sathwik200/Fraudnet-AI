#!/usr/bin/env python3
"""
FRAUDNET AI — Explainable AI (XAI) Engine
==========================================
Provides forensic explanations for machine learning fraud predictions:
  - Global model feature importances
  - Local feature attribution per transaction (z-score weighted impact)
  - Plain-English investigative summaries
  - Transparent documentation of model limitations and uncertainty

FORENSIC DISCLAIMER:
  Model explanations identify features that statistically influenced the
  classifier's risk score. Statistical deviations and graph characteristics
  are investigative leads, not legal proof of fraud or illicit activity.
"""

from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from src.ml.model_manager import load_model_bundle


def get_global_feature_importances(
    model_bundle: Optional[Dict] = None,
    top_n: int = 20,
) -> List[Dict[str, any]]:
    """
    Retrieve top-N global feature importances from the trained model.
    """
    bundle = model_bundle or load_model_bundle()
    clf = bundle["model"]
    feature_names = bundle["feature_names"]

    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        importances = np.abs(clf.coef_[0])
    else:
        importances = np.ones(len(feature_names)) / len(feature_names)

    sorted_indices = np.argsort(importances)[::-1][:top_n]

    results = []
    for rank, idx in enumerate(sorted_indices, 1):
        feat = feature_names[idx]
        val = float(importances[idx])
        results.append({
            "rank": rank,
            "feature": feat,
            "importance": round(val, 4),
            "category": "local" if feat.startswith("local_") else ("graph" if feat in {"in_degree", "out_degree", "total_degree", "pagerank", "clustering_coeff"} else "aggregate"),
        })

    return results


def explain_transaction_prediction(
    transaction_row: Union[pd.Series, pd.DataFrame, Dict],
    model_bundle: Optional[Dict] = None,
    top_n: int = 5,
) -> Dict[str, any]:
    """
    Generate descriptive local feature deviations from empirical licit baseline for a transaction.

    EXPLAINABILITY & ATTRIBUTION METHODOLOGY NOTE:
    The supervised classifier utilizes a Random Forest whose feature importances reflect global
    Gini impurity reduction across tree splits. Gini importances are strictly non-negative and
    global; multiplying them by local signed Z-scores does not constitute a mathematically sound
    local directional Shapley or TreeSHAP contribution.
    
    Consequently, local feature behavior is reported descriptively as standardized baseline
    deviations (Z-scores) comparing the transaction to the training licit class distribution.
    Features with elevated positive or negative deviations are presented transparently without
    assigning speculative directional causality.

    Args:
        transaction_row: Row containing transaction features.
        model_bundle: Optional preloaded model bundle.
        top_n: Number of primary deviations to return.

    Returns:
        Structured explanation dict with descriptive baseline deviations and narrative summary.
    """
    bundle = model_bundle or load_model_bundle()
    clf = bundle["model"]
    pipeline = bundle["feature_pipeline"]
    feature_names = bundle["feature_names"]

    # Format input as 1-row DataFrame
    if isinstance(transaction_row, dict):
        df_row = pd.DataFrame([transaction_row])
    elif isinstance(transaction_row, pd.Series):
        df_row = pd.DataFrame([transaction_row])
    else:
        df_row = transaction_row.copy()

    # Transformed (imputed and standardized) feature values (Z-scores)
    X_vec = pipeline.transform(df_row)[0]

    # Global model importance weights (for reference ranking)
    if hasattr(clf, "feature_importances_"):
        global_weights = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        global_weights = np.abs(clf.coef_[0])
    else:
        global_weights = np.ones(len(feature_names)) / len(feature_names)

    # Sort deviations:
    # 1. Highest positive deviations above baseline (z > 0)
    # 2. Lowest negative deviations below baseline (z < 0)
    # 3. Overall largest absolute deviations (|z|)
    pos_indices = [i for i in range(len(feature_names)) if X_vec[i] > 0]
    neg_indices = [i for i in range(len(feature_names)) if X_vec[i] < 0]
    all_indices = list(range(len(feature_names)))

    sorted_pos = sorted(pos_indices, key=lambda i: X_vec[i], reverse=True)[:top_n]
    sorted_neg = sorted(neg_indices, key=lambda i: X_vec[i])[:top_n]
    sorted_all = sorted(all_indices, key=lambda i: abs(X_vec[i]), reverse=True)[: top_n * 2]

    top_deviations_above = []
    for idx in sorted_pos:
        feat = feature_names[idx]
        z_score = float(X_vec[idx])
        val = round(float(df_row[feat].iloc[0]), 4) if feat in df_row else 0.0
        g_imp = round(float(global_weights[idx]), 4)
        item = {
            "feature": feat,
            "value": val,
            "z_score": round(z_score, 2),
            "abs_z_score": round(abs(z_score), 2),
            "deviation_direction": "above_baseline",
            "global_importance": g_imp,
            "impact_direction": "above_baseline",
            "reason": f"{feat} is {abs(z_score):.2f} standard deviations above the empirical licit baseline (observed: {val}).",
            "explanation": f"{feat} is {abs(z_score):.2f} std devs above baseline (value: {val}).",
        }
        top_deviations_above.append(item)

    top_deviations_below = []
    for idx in sorted_neg:
        feat = feature_names[idx]
        z_score = float(X_vec[idx])
        val = round(float(df_row[feat].iloc[0]), 4) if feat in df_row else 0.0
        g_imp = round(float(global_weights[idx]), 4)
        item = {
            "feature": feat,
            "value": val,
            "z_score": round(z_score, 2),
            "abs_z_score": round(abs(z_score), 2),
            "deviation_direction": "below_baseline",
            "global_importance": g_imp,
            "impact_direction": "below_baseline",
            "reason": f"{feat} is {abs(z_score):.2f} standard deviations below the empirical licit baseline (observed: {val}).",
            "explanation": f"{feat} is {abs(z_score):.2f} std devs below baseline (value: {val}).",
        }
        top_deviations_below.append(item)

    top_deviations = []
    for idx in sorted_all:
        feat = feature_names[idx]
        z_score = float(X_vec[idx])
        val = round(float(df_row[feat].iloc[0]), 4) if feat in df_row else 0.0
        g_imp = round(float(global_weights[idx]), 4)
        direction = "above_baseline" if z_score >= 0 else "below_baseline"
        item = {
            "feature": feat,
            "value": val,
            "z_score": round(z_score, 2),
            "abs_z_score": round(abs(z_score), 2),
            "deviation_direction": direction,
            "global_importance": g_imp,
            "impact_direction": direction,
            "reason": f"{feat} is {abs(z_score):.2f} standard deviations {'above' if z_score >= 0 else 'below'} baseline (observed: {val}).",
            "explanation": f"{feat} is {abs(z_score):.2f} std devs {'above' if z_score >= 0 else 'below'} baseline (value: {val}).",
        }
        top_deviations.append(item)

    has_sig = any(abs(d["z_score"]) >= 1.5 for d in top_deviations)
    narrative = (
        f"Local feature deviations from empirical licit baseline. "
        f"{'Observed significant statistical deviations (|z| >= 1.5).' if has_sig else 'No extreme statistical outliers detected against licit baseline (|z| < 1.5).'}"
    )

    return {
        "attribution_available": True,
        "methodology": "Standardized Feature Baseline Deviation (Z-score profiling; Gini importance reference)",
        "has_significant_anomalies": has_sig,
        "top_deviations": top_deviations[:top_n],
        "top_deviations_above": top_deviations_above,
        "top_deviations_below": top_deviations_below,
        "top_drivers": top_deviations[:top_n],
        "top_risk_elevating": top_deviations_above,
        "top_risk_mitigating": top_deviations_below,
        "narrative": narrative,
        "uncertainty_note": (
            "Statistical deviations describe empirical variance from the training baseline distribution. "
            "In the absence of local Shapley tree values, deviations are reported descriptively and do "
            "not assign directional causality or legal proof of wrongdoing. All findings require human review."
        ),
    }

