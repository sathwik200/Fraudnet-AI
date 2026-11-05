"""Unit tests for Supervised Machine Learning Pipeline (Module B & C)."""

from pathlib import Path
import pytest
import numpy as np
import pandas as pd

from config.settings import CHAMPION_MODEL_PATH, MODEL_SUMMARY_PATH
from src.ml.feature_engineering import FraudnetFeaturePipeline
from src.ml.data_split import create_chronological_splits
from src.ml.evaluate import evaluate_binary_model, find_optimal_threshold
from src.ml.model_manager import load_model_bundle, get_model_metadata
from src.ml.predict import predict_transaction_risk


def test_model_bundle_file_exists():
    """Verify champion model artifact and metadata exist."""
    assert CHAMPION_MODEL_PATH.exists()
    assert MODEL_SUMMARY_PATH.exists()


def test_load_model_bundle():
    """Verify loading champion model bundle."""
    bundle = load_model_bundle(CHAMPION_MODEL_PATH)
    assert "model" in bundle
    assert "feature_pipeline" in bundle
    assert "optimal_threshold" in bundle
    assert "test_evaluation" in bundle
    assert hasattr(bundle["model"], "predict_proba")


def test_evaluate_binary_model_synthetic():
    """Verify metric calculations for balanced synthetic predictions."""
    class DummyModel:
        def predict_proba(self, X):
            return np.array([[0.9, 0.1], [0.8, 0.2], [0.2, 0.8], [0.1, 0.9]])

    X_dummy = np.zeros((4, 2))
    y_true = np.array([0, 0, 1, 1])
    res = evaluate_binary_model(DummyModel(), X_dummy, y_true, threshold=0.5)

    assert "metrics" in res
    assert "f1_illicit" in res["metrics"]
    assert "precision_illicit" in res["metrics"]
    assert "recall_illicit" in res["metrics"]
    assert "pr_auc" in res["metrics"]
    assert "roc_auc" in res["metrics"]
    assert res["metrics"]["f1_illicit"] == 1.0
    assert res["metrics"]["roc_auc"] == 1.0


def test_find_optimal_threshold():
    """Verify threshold optimization finds highest F1 threshold."""
    y_true = np.array([0, 0, 1, 1, 1])
    y_prob = np.array([0.1, 0.4, 0.6, 0.8, 0.9])
    best_th, best_f1 = find_optimal_threshold(y_true, y_prob)
    assert 0.4 <= best_th <= 0.65
    assert best_f1 > 0.8


def test_feature_pipeline_fit_transform():
    """Test FraudnetFeaturePipeline on sample synthetic features."""
    df = pd.DataFrame({
        "txId": [101, 102, 103],
        "time_step": [1, 1, 2],
        "label": ["1", "2", "unknown"],
        "local_feature_1": [1.0, 2.0, 3.0],
        "local_feature_2": [10.0, 20.0, 30.0],
    })
    pipeline = FraudnetFeaturePipeline()
    X = pipeline.fit_transform(df)
    assert isinstance(X, np.ndarray)
    assert X.shape == (3, 2)
    # Target columns txId, time_step, label should not be in features
    assert "txId" not in pipeline.feature_names_
    assert "label" not in pipeline.feature_names_


def test_predict_transaction_risk():
    """Test scoring a transaction record with model bundle."""
    bundle = load_model_bundle(CHAMPION_MODEL_PATH)
    pipeline = bundle["feature_pipeline"]

    # Create dummy dataframe matching feature requirements
    data = {"txId": [999999], "time_step": [1], "label": ["unknown"]}
    for feat in pipeline.feature_names_:
        data[feat] = [0.0]

    df_sample = pd.DataFrame(data)
    result = predict_transaction_risk(df_sample, bundle)

    assert "illicit_probability" in result
    assert "predicted_label" in result
    assert "risk_category" in result
    assert 0.0 <= result["illicit_probability"] <= 1.0
    assert result["risk_category"] in {"Critical", "High", "Moderate", "Low"}
