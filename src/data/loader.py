#!/usr/bin/env python3
"""
FRAUDNET AI — Data Loader
==========================
Loads the three Elliptic Bitcoin Transaction CSV files into pandas DataFrames
with correct schemas derived from the dataset inspection (Prompt 01).

Key design decisions based on inspection results:
- elliptic_txs_features.csv has NO header row → column names assigned positionally
- elliptic_txs_classes.csv HAS a header row (txId, class)
- elliptic_txs_edgelist.csv HAS a header row (txId1, txId2)
- Features file has 167 columns: txId, time_step, 93 local features, 72 aggregate features
- Class labels are: "1" (illicit), "2" (licit), "unknown"
"""

import pandas as pd
from pathlib import Path
from typing import Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "elliptic"
FEATURES_FILE = DATA_DIR / "elliptic_txs_features.csv"
CLASSES_FILE = DATA_DIR / "elliptic_txs_classes.csv"
EDGELIST_FILE = DATA_DIR / "elliptic_txs_edgelist.csv"


# ---------------------------------------------------------------------------
# Column name generation (from inspected schema)
# ---------------------------------------------------------------------------
NUM_FEATURES_COLUMNS = 167  # Total columns in features CSV
NUM_LOCAL_FEATURES = 93     # Columns 2–94
NUM_AGG_FEATURES = 72       # Columns 95–166


def build_feature_column_names() -> list:
    """
    Build the 167 column names for the headerless features CSV.

    Layout (verified by inspection):
        col 0:       txId                (integer transaction ID)
        col 1:       time_step           (integer 1–49)
        cols 2–94:   local_feature_1 … local_feature_93   (93 local features)
        cols 95–166: agg_feature_1 … agg_feature_72       (72 aggregate features)

    Total: 1 + 1 + 93 + 72 = 167 columns.
    """
    cols = ["txId", "time_step"]
    cols += [f"local_feature_{i}" for i in range(1, NUM_LOCAL_FEATURES + 1)]
    cols += [f"agg_feature_{i}" for i in range(1, NUM_AGG_FEATURES + 1)]
    assert len(cols) == NUM_FEATURES_COLUMNS, (
        f"Expected {NUM_FEATURES_COLUMNS} column names, got {len(cols)}"
    )
    return cols


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_features(path: Path = None) -> pd.DataFrame:
    """
    Load elliptic_txs_features.csv (headerless) into a DataFrame.

    Returns a DataFrame with columns:
        txId (int64), time_step (int64), local_feature_1..93 (float64),
        agg_feature_1..72 (float64)
    """
    path = path or FEATURES_FILE
    if not path.exists():
        raise FileNotFoundError(f"Features file not found: {path}")

    col_names = build_feature_column_names()

    # The features CSV has NO header row.
    df = pd.read_csv(
        path,
        header=None,           # No header in file
        names=col_names,       # Assign our column names
        dtype={"txId": "int64", "time_step": "int64"},
        low_memory=False,
    )

    return df


def load_classes(path: Path = None) -> pd.DataFrame:
    """
    Load elliptic_txs_classes.csv (has header: txId, class) into a DataFrame.

    The 'class' column contains string values: "1", "2", or "unknown".
    These are preserved as-is (no remapping to integers).
    """
    path = path or CLASSES_FILE
    if not path.exists():
        raise FileNotFoundError(f"Classes file not found: {path}")

    df = pd.read_csv(
        path,
        header=0,              # File has header row
        dtype={"txId": "int64", "class": "str"},
    )

    # Rename 'class' to 'label' to avoid Python reserved-word collision,
    # while preserving the original string values.
    df = df.rename(columns={"class": "label"})

    return df


def load_edgelist(path: Path = None) -> pd.DataFrame:
    """
    Load elliptic_txs_edgelist.csv (has header: txId1, txId2) into a DataFrame.

    Edges represent directed payment flows between transactions.
    """
    path = path or EDGELIST_FILE
    if not path.exists():
        raise FileNotFoundError(f"Edge list file not found: {path}")

    df = pd.read_csv(
        path,
        header=0,              # File has header row
        dtype={"txId1": "int64", "txId2": "int64"},
    )

    return df


def load_all(data_dir: Path = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load all three Elliptic dataset files.

    Returns:
        (features_df, classes_df, edges_df)
    """
    if data_dir is not None:
        feat_path = data_dir / "elliptic_txs_features.csv"
        cls_path = data_dir / "elliptic_txs_classes.csv"
        edge_path = data_dir / "elliptic_txs_edgelist.csv"
    else:
        feat_path = FEATURES_FILE
        cls_path = CLASSES_FILE
        edge_path = EDGELIST_FILE

    features = load_features(feat_path)
    classes = load_classes(cls_path)
    edges = load_edgelist(edge_path)

    return features, classes, edges


# ---------------------------------------------------------------------------
# Main (for standalone testing)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("Loading Elliptic dataset...")

    features, classes, edges = load_all()

    print(f"\nFeatures: {features.shape}")
    print(f"  Columns: {list(features.columns[:5])} ... {list(features.columns[-3:])}")
    print(f"  dtypes sample: txId={features['txId'].dtype}, "
          f"time_step={features['time_step'].dtype}, "
          f"local_feature_1={features['local_feature_1'].dtype}")
    print(features.head(3).to_string(max_cols=10))

    print(f"\nClasses: {classes.shape}")
    print(f"  Columns: {list(classes.columns)}")
    print(f"  Label values: {classes['label'].unique()}")
    print(classes.head(5).to_string())

    print(f"\nEdges: {edges.shape}")
    print(f"  Columns: {list(edges.columns)}")
    print(edges.head(5).to_string())

    print("\nDone.")

