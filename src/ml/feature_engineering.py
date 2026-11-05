#!/usr/bin/env python3
"""
FRAUDNET AI — Machine Learning Feature Engineering
===================================================
Prepares and normalizes transaction feature vectors for supervised fraud modeling.

Guarantees:
  1. No Target Leakage: Class labels are strictly excluded from input features X.
  2. No Identity Bias: Transaction IDs are strictly excluded from input features X.
  3. No Temporal Leakage: Preprocessing transformations (imputation, scaling)
     are fitted strictly on training slices only.
  4. Feature Provenance: Distinguishes between original 165 Elliptic features
     and safe structural graph features.
"""

from pathlib import Path
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler


ORIGINAL_LOCAL_FEATURES = [f"local_feature_{i}" for i in range(1, 94)]
ORIGINAL_AGG_FEATURES = [f"agg_feature_{i}" for i in range(1, 73)]
ORIGINAL_NUMERIC_FEATURES = ORIGINAL_LOCAL_FEATURES + ORIGINAL_AGG_FEATURES

SAFE_GRAPH_FEATURES = [
    "in_degree",
    "out_degree",
    "total_degree",
    "pagerank",
    "clustering_coeff",
]


class FraudnetFeaturePipeline:
    """
    Scikit-learn compatible feature preprocessor that imputes and standardizes features.
    Fitted exclusively on training data to prevent look-ahead leakage.
    """

    def __init__(self, include_graph_features: bool = False):
        self.include_graph_features = include_graph_features
        self.imputer = SimpleImputer(strategy="median")
        self.scaler = StandardScaler()
        self.feature_names_: List[str] = []
        self.is_fitted: bool = False

    def get_feature_columns(self) -> List[str]:
        features = list(ORIGINAL_NUMERIC_FEATURES)
        if self.include_graph_features:
            features += list(SAFE_GRAPH_FEATURES)
        return features

    def fit(self, X: pd.DataFrame, y=None):
        """Fit imputer and scaler strictly on training DataFrame."""
        cols = self.get_feature_columns()
        available_cols = [c for c in cols if c in X.columns]
        self.feature_names_ = available_cols

        X_raw = X[available_cols].values
        # Replace inf with nan for safe imputation
        X_clean = np.where(np.isinf(X_raw), np.nan, X_raw)

        X_imp = self.imputer.fit_transform(X_clean)
        self.scaler.fit(X_imp)
        self.is_fitted = True
        return self

    def transform(self, X: pd.DataFrame) -> np.ndarray:
        """Transform features using pre-fitted statistics."""
        if not self.is_fitted:
            raise RuntimeError("FraudnetFeaturePipeline must be fitted before calling transform.")
        X_raw = X[self.feature_names_].values
        X_clean = np.where(np.isinf(X_raw), np.nan, X_raw)
        X_imp = self.imputer.transform(X_clean)
        return self.scaler.transform(X_imp)

    def fit_transform(self, X: pd.DataFrame, y=None) -> np.ndarray:
        return self.fit(X, y).transform(X)


def load_raw_features_and_labels(
    transactions_path: Path,
    analytics_metrics_path: Optional[Path] = None,
    include_graph_features: bool = False,
) -> pd.DataFrame:
    """
    Load transactions DataFrame and optionally join safe graph structural features.
    """
    df = pd.read_parquet(transactions_path)

    if include_graph_features and analytics_metrics_path and analytics_metrics_path.exists():
        metrics_df = pd.read_parquet(
            analytics_metrics_path,
            columns=["txId"] + SAFE_GRAPH_FEATURES,
        )
        df = df.merge(metrics_df, on="txId", how="left")

    return df

