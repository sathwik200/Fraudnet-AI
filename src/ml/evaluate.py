#!/usr/bin/env python3
"""
FRAUDNET AI — Model Evaluation Suite
=====================================
Computes comprehensive fraud detection metrics:
  - Illicit Class Precision, Recall, and F1-score
  - Precision-Recall AUC (Average Precision score)
  - Receiver Operating Characteristic AUC (ROC-AUC)
  - Confusion Matrix (TN, FP, FN, TP)
  - Optimal Decision Threshold Tuning (maximizing F1 on validation data)
  - Forensic Error Analysis (False Positives and False Negatives)
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


def find_optimal_threshold(
    y_true: np.ndarray,
    y_scores: np.ndarray,
    num_thresholds: int = 100,
) -> Tuple[float, float]:
    """
    Find probability decision threshold that maximizes illicit F1-score.

    Returns:
        (best_threshold, best_f1)
    """
    precisions, recalls, thresholds = precision_recall_curve(y_true, y_scores)
    
    # Avoid division by zero
    f1_scores = np.where(
        (precisions + recalls) > 0,
        2 * (precisions * recalls) / (precisions + recalls),
        0.0,
    )

    best_idx = np.argmax(f1_scores[:-1]) if len(f1_scores) > 1 else 0
    best_threshold = float(thresholds[best_idx]) if len(thresholds) > best_idx else 0.5
    best_f1 = float(f1_scores[best_idx])

    # Bound threshold to reasonable range [0.15, 0.85]
    best_threshold = float(np.clip(best_threshold, 0.15, 0.85))

    return round(best_threshold, 4), round(best_f1, 4)


def evaluate_binary_model(
    model,
    X: np.ndarray,
    y_true: np.ndarray,
    threshold: float = 0.5,
    model_name: str = "Model",
) -> Dict[str, any]:
    """
    Compute full evaluation metrics for a model on a given dataset partition.

    Args:
        model: Fitted classifier with predict_proba
        X: Feature matrix
        y_true: Ground truth binary target (1 = illicit, 0 = licit)
        threshold: Decision threshold for positive classification
        model_name: Human-readable identifier

    Returns:
        Dict with metrics, confusion matrix, ROC/PR curves
    """
    # Predict probabilities for positive class (illicit = 1)
    if hasattr(model, "predict_proba"):
        y_scores = model.predict_proba(X)[:, 1]
    elif hasattr(model, "decision_function"):
        df_scores = model.decision_function(X)
        y_scores = 1.0 / (1.0 + np.exp(-df_scores))
    else:
        y_scores = model.predict(X).astype(float)

    # Apply decision threshold
    y_pred = (y_scores >= threshold).astype(int)

    # Core metrics for positive class (1 = illicit)
    p_illicit = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    r_illicit = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    f1_illicit = f1_score(y_true, y_pred, pos_label=1, zero_division=0)

    # Core metrics for licit class (0 = licit)
    p_licit = precision_score(y_true, y_pred, pos_label=0, zero_division=0)
    r_licit = recall_score(y_true, y_pred, pos_label=0, zero_division=0)
    f1_licit = f1_score(y_true, y_pred, pos_label=0, zero_division=0)

    # Overall metrics
    acc = accuracy_score(y_true, y_pred)
    f1_macro = f1_score(y_true, y_pred, average="macro", zero_division=0)
    
    try:
        roc_auc = roc_auc_score(y_true, y_scores)
    except Exception:
        roc_auc = 0.5

    try:
        pr_auc = average_precision_score(y_true, y_scores)
    except Exception:
        pr_auc = 0.0

    # Confusion matrix: tn, fp, fn, tp
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()

    # ROC curve points (sampled for serialization)
    fpr, tpr, _ = roc_curve(y_true, y_scores)
    pr_p, pr_r, _ = precision_recall_curve(y_true, y_scores)

    # Downsample curve arrays to at most 100 points for clean JSON storage
    step = max(len(fpr) // 100, 1)
    roc_points = [{"fpr": round(float(f), 4), "tpr": round(float(t), 4)} for f, t in zip(fpr[::step], tpr[::step])]
    
    step_pr = max(len(pr_p) // 100, 1)
    pr_points = [{"precision": round(float(p), 4), "recall": round(float(r), 4)} for p, r in zip(pr_p[::step_pr], pr_r[::step_pr])]

    return {
        "model_name": model_name,
        "threshold": round(float(threshold), 4),
        "metrics": {
            "precision_illicit": round(float(p_illicit), 4),
            "recall_illicit": round(float(r_illicit), 4),
            "f1_illicit": round(float(f1_illicit), 4),
            "precision_licit": round(float(p_licit), 4),
            "recall_licit": round(float(r_licit), 4),
            "f1_licit": round(float(f1_licit), 4),
            "f1_macro": round(float(f1_macro), 4),
            "accuracy": round(float(acc), 4),
            "roc_auc": round(float(roc_auc), 4),
            "pr_auc": round(float(pr_auc), 4),
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp),
        },
        "error_analysis": {
            "false_positive_rate": round(float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0, 4),
            "false_negative_rate": round(float(fn / (fn + tp)) if (fn + tp) > 0 else 0.0, 4),
            "total_tested": int(len(y_true)),
        },
        "roc_curve": roc_points,
        "pr_curve": pr_points,
    }

