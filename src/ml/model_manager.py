#!/usr/bin/env python3
"""
FRAUDNET AI — Model Manager
============================
Handles safe loading, version tracking, and caching of trained fraud-risk model artifacts.
"""

from pathlib import Path
from typing import Dict, Optional
import joblib

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL_PATH = PROJECT_ROOT / "models" / "fraudnet_model_v1.joblib"

_CACHED_MODEL_BUNDLE = None


def load_model_bundle(
    model_path: Optional[Path] = None,
    use_cache: bool = True,
) -> Dict[str, any]:
    """
    Load the trained model bundle from disk.

    Returns:
        dict containing 'model', 'feature_pipeline', 'feature_names',
        'optimal_threshold', 'test_evaluation', 'version', etc.
    """
    global _CACHED_MODEL_BUNDLE
    path = Path(model_path) if model_path else DEFAULT_MODEL_PATH

    if use_cache and _CACHED_MODEL_BUNDLE is not None:
        return _CACHED_MODEL_BUNDLE

    if not path.exists():
        raise FileNotFoundError(
            f"Trained model artifact not found at {path}. "
            "Please run 'python -m src.ml.train' to build and save the model."
        )

    bundle = joblib.load(path)
    if not isinstance(bundle, dict) or "model" not in bundle:
        raise ValueError(f"Corrupt or invalid model bundle at {path}")

    if use_cache:
        _CACHED_MODEL_BUNDLE = bundle

    return bundle


def get_model_metadata(model_path: Optional[Path] = None) -> Dict[str, any]:
    """Retrieve metadata without returning model object."""
    bundle = load_model_bundle(model_path)
    return {
        "model_name": bundle.get("model_name"),
        "version": bundle.get("version"),
        "optimal_threshold": bundle.get("optimal_threshold"),
        "training_timestamp": bundle.get("training_timestamp"),
        "test_metrics": bundle.get("test_evaluation", {}).get("metrics", {}),
        "feature_count": len(bundle.get("feature_names", [])),
    }

