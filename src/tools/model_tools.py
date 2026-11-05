#!/usr/bin/env python3
"""
FRAUDNET AI — Model Service Tools
==================================
Wrapper tools interfacing between machine learning models and the investigation engine.
"""

from typing import Dict, List, Optional
import pandas as pd

from src.ml.explainability import get_global_feature_importances
from src.ml.model_manager import get_model_metadata, load_model_bundle
from src.ml.predict import predict_transaction_risk


def get_model_info() -> Dict[str, any]:
    """Retrieve active model metadata, thresholds, and performance metrics."""
    return get_model_metadata()


def get_top_global_features(top_n: int = 15) -> List[Dict[str, any]]:
    """Retrieve top-N global predictive features."""
    return get_global_feature_importances(top_n=top_n)


def score_transaction_record(df_row: pd.DataFrame) -> Dict[str, any]:
    """Score a single transaction DataFrame record."""
    return predict_transaction_risk(df_row)

