"""
FRAUDNET AI — Machine Learning Package
=======================================
Supervised fraud detection models, chronological data splits, evaluation metrics,
and explainability engines.
"""

__all__ = [
    "FraudnetFeaturePipeline",
    "load_raw_features_and_labels",
    "ORIGINAL_NUMERIC_FEATURES",
    "SAFE_GRAPH_FEATURES",
    "create_chronological_splits",
    "get_split_statistics",
    "filter_labeled_transactions",
    "evaluate_binary_model",
    "find_optimal_threshold",
    "load_model_bundle",
    "get_model_metadata",
    "predict_transaction_risk",
    "assign_risk_category",
    "get_global_feature_importances",
    "explain_transaction_prediction",
    "train_and_evaluate_all_models",
]


def __getattr__(name: str):
    if name in {
        "FraudnetFeaturePipeline",
        "load_raw_features_and_labels",
        "ORIGINAL_NUMERIC_FEATURES",
        "SAFE_GRAPH_FEATURES",
    }:
        from . import feature_engineering
        return getattr(feature_engineering, name)
    elif name in {
        "create_chronological_splits",
        "get_split_statistics",
        "filter_labeled_transactions",
    }:
        from . import data_split
        return getattr(data_split, name)
    elif name in {"evaluate_binary_model", "find_optimal_threshold"}:
        from . import evaluate
        return getattr(evaluate, name)
    elif name in {"load_model_bundle", "get_model_metadata"}:
        from . import model_manager
        return getattr(model_manager, name)
    elif name in {"predict_transaction_risk", "assign_risk_category"}:
        from . import predict
        return getattr(predict, name)
    elif name in {"get_global_feature_importances", "explain_transaction_prediction"}:
        from . import explainability
        return getattr(explainability, name)
    elif name in {"train_and_evaluate_all_models"}:
        from . import train
        return getattr(train, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
