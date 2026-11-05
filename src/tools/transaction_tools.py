#!/usr/bin/env python3
"""
FRAUDNET AI — Transaction Data Tools
=====================================
Tools for fast transaction lookup, profile aggregation, and sample retrieval.
Integrates raw features, graph metrics, ML risk predictions, and explainability.
"""

from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd

from src.ml.explainability import explain_transaction_prediction
from src.ml.predict import predict_transaction_risk

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "processed"
TRANSACTIONS_PATH = DATA_DIR / "transactions.parquet"
ANALYTICS_METRICS_PATH = DATA_DIR / "analytics" / "transaction_metrics.parquet"

# In-memory lookup cache to optimize repeated queries
_TRANSACTION_CACHE: Dict[int, Dict[str, any]] = {}


def get_transaction_record(tx_id: int) -> Optional[pd.DataFrame]:
    """
    Retrieve single transaction record from Parquet by txId.
    Returns 1-row DataFrame or None if not found.
    """
    tx_id = int(tx_id)
    try:
        df = pd.read_parquet(TRANSACTIONS_PATH, filters=[("txId", "==", tx_id)])
        if df.empty:
            return None
        return df
    except Exception:
        return None


def get_transaction_metrics_record(tx_id: int) -> Optional[Dict[str, any]]:
    """Retrieve precomputed graph metrics for txId."""
    tx_id = int(tx_id)
    if not ANALYTICS_METRICS_PATH.exists():
        return None
    try:
        df = pd.read_parquet(ANALYTICS_METRICS_PATH, filters=[("txId", "==", tx_id)])
        if df.empty:
            return None
        return df.iloc[0].to_dict()
    except Exception:
        return None


def get_full_transaction_profile(tx_id: int, use_cache: bool = True) -> Optional[Dict[str, any]]:
    """
    Retrieve complete forensic dossier for a transaction:
      1. Metadata (txId, time_step, ground_truth_label)
      2. Graph topological metrics (degrees, PageRank, community, WCC size, hub status)
      3. Machine learning prediction (risk score, category, threshold)
      4. Key explainability drivers (top risk-elevating and risk-mitigating features)
    """
    tx_id = int(tx_id)
    if use_cache and tx_id in _TRANSACTION_CACHE:
        return _TRANSACTION_CACHE[tx_id]

    df_tx = get_transaction_record(tx_id)
    if df_tx is None or df_tx.empty:
        return None

    # Retrieve graph metrics
    metrics = get_transaction_metrics_record(tx_id) or {}

    # Merge graph metrics into transaction row if available for ML prediction
    df_combined = df_tx.copy()
    for k, v in metrics.items():
        if k not in df_combined.columns and k != "txId":
            df_combined[k] = v

    # Machine learning prediction
    ml_pred = predict_transaction_risk(df_combined)

    # Explainability
    explanation = explain_transaction_prediction(df_combined, top_n=5)

    profile = {
        "txId": tx_id,
        "time_step": int(df_tx["time_step"].iloc[0]),
        "ground_truth_label": str(df_tx["label"].iloc[0]),
        "ml_assessment": ml_pred,
        "graph_metrics": {
            "in_degree": int(metrics.get("in_degree", 0)),
            "out_degree": int(metrics.get("out_degree", 0)),
            "total_degree": int(metrics.get("total_degree", 0)),
            "pagerank": float(metrics.get("pagerank", 0.0)),
            "clustering_coeff": float(metrics.get("clustering_coeff", 0.0)),
            "wcc_id": int(metrics.get("wcc_id", 0)),
            "wcc_size": int(metrics.get("wcc_size", 0)),
            "community_id": int(metrics.get("community_id", 0)),
            "is_aggregation_hub": bool(metrics.get("is_aggregation_hub", False)),
            "is_distribution_hub": bool(metrics.get("is_distribution_hub", False)),
        },
        "explainability": explanation,
        "feature_sample": {
            col: round(float(df_tx[col].iloc[0]), 4)
            for col in list(df_tx.columns)[2:12]  # first 10 local features
        },
    }

    if use_cache:
        _TRANSACTION_CACHE[tx_id] = profile

    return profile


def get_sample_transactions(class_label: Optional[str] = None, count: int = 5) -> List[int]:
    """Retrieve sample transaction IDs for testing or demonstration."""
    filters = [("label", "==", class_label)] if class_label else None
    df = pd.read_parquet(TRANSACTIONS_PATH, columns=["txId"], filters=filters)
    return df["txId"].head(count).tolist()

