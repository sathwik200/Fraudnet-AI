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
    Generate local feature attribution and investigative justification for a transaction.

    Args:
        transaction_row: Row containing transaction features.
        model_bundle: Optional preloaded model bundle.
        top_n: Number of primary drivers to return.

    Returns:
        Structured explanation dict with top contributors, direction, and narrative summary.
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

    # Transformed (imputed and standardized) feature values
    X_vec = pipeline.transform(df_row)[0]

    # Model importance weights
    if hasattr(clf, "feature_importances_"):
        global_weights = clf.feature_importances_
    elif hasattr(clf, "coef_"):
        global_weights = np.abs(clf.coef_[0])
    else:
        global_weights = np.ones(len(feature_names)) / len(feature_names)

    # Local contribution proxy: product of global importance and standardized deviation
    local_impact = X_vec * global_weights

    # Positive impact pushes score towards illicit (1); negative towards licit (0)
    top_illicit_indices = np.argsort(local_impact)[::-1][:top_n]
    top_licit_indices = np.argsort(local_impact)[:top_n]

    drivers = []
    for idx in top_illicit_indices:
        feat = feature_names[idx]
        z_score = float(X_vec[idx])
        impact = float(local_impact[idx])
        drivers.append({
            "feature": feat,
            "z_score": round(z_score, 2),
            "impact_direction": "increases_risk",
            "impact_score": round(impact, 4),
            "explanation": f"{feat} is {abs(z_score):.1f} std devs {'above' if z_score > 0 else 'below'} normal, elevating estimated risk.",
        })

    for idx in top_licit_indices:
        feat = feature_names[idx]
        z_score = float(X_vec[idx])
        impact = float(local_impact[idx])
        drivers.append({
            "feature": feat,
            "z_score": round(z_score, 2),
            "impact_direction": "decreases_risk",
            "impact_score": round(impact, 4),
            "explanation": f"{feat} aligns closely with baseline licit behavior, reducing estimated risk.",
        })

    narrative = (
        f"Top {len(top_illicit_indices)} risk-elevating indicators and top {len(top_licit_indices)} "
        "mitigating indicators derived from standardized feature deviations and model weights."
    )

    return {
        "top_drivers": drivers,
        "narrative": narrative,
        "uncertainty_note": (
            "Model predictions reflect statistical associations with labeled training examples. "
            "They must be verified against blockchain explorers, transaction metadata, and human investigative review."
        ),
    }

