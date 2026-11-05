#!/usr/bin/env python3
"""
FRAUDNET AI — Time-Aware Chronological Data Splitter
=====================================================
Implements temporal data partitioning across the 49 time steps to prevent
future-to-past information leakage.

Splitting Strategy:
  - Training Period:   Time steps 1 to 28 (Historical baseline)
  - Validation Period: Time steps 29 to 34 (Hyperparameter & model selection)
  - Full Train Period: Time steps 1 to 34 (Combined for final test evaluation)
  - Testing Period:    Time steps 35 to 49 (Held-out future transactions)

Unknown transactions are excluded from supervised labeled training and evaluation.
"""

from typing import Dict, Tuple
import pandas as pd


# Default temporal boundaries
TRAIN_MAX_STEP = 28
VAL_MAX_STEP = 34
TEST_START_STEP = 35


def filter_labeled_transactions(df: pd.DataFrame) -> pd.DataFrame:
    """Filter DataFrame to only transactions with confirmed ground-truth label ('1' or '2')."""
    return df[df["label"].isin(["1", "2"])].copy()


def create_chronological_splits(
    df: pd.DataFrame,
    train_max_step: int = TRAIN_MAX_STEP,
    val_max_step: int = VAL_MAX_STEP,
    test_start_step: int = TEST_START_STEP,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split labeled transactions into strictly chronological partitions.

    Returns:
        (train_df, val_df, full_train_df, test_df)
    """
    labeled_df = filter_labeled_transactions(df)

    # Encode binary target: 1 = Illicit, 0 = Licit
    labeled_df["target"] = (labeled_df["label"] == "1").astype(int)

    train_mask = labeled_df["time_step"] <= train_max_step
    val_mask = (labeled_df["time_step"] > train_max_step) & (labeled_df["time_step"] <= val_max_step)
    full_train_mask = labeled_df["time_step"] <= val_max_step
    test_mask = labeled_df["time_step"] >= test_start_step

    train_df = labeled_df[train_mask].copy()
    val_df = labeled_df[val_mask].copy()
    full_train_df = labeled_df[full_train_mask].copy()
    test_df = labeled_df[test_mask].copy()

    # Sanity verification: assert both classes present in each split
    for name, split in [("train", train_df), ("val", val_df), ("test", test_df)]:
        n_illicit = int((split["target"] == 1).sum())
        n_licit = int((split["target"] == 0).sum())
        if n_illicit == 0 or n_licit == 0:
            raise ValueError(
                f"Class availability check failed in split '{name}': illicit={n_illicit}, licit={n_licit}."
            )

    return train_df, val_df, full_train_df, test_df


def get_split_statistics(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> Dict[str, any]:
    """Return dictionary of counts, ratios, and time-step ranges for each split."""
    def stats(sub_df, name):
        total = len(sub_df)
        illicit = int((sub_df["target"] == 1).sum())
        licit = int((sub_df["target"] == 0).sum())
        return {
            "name": name,
            "total_samples": total,
            "illicit_count": illicit,
            "licit_count": licit,
            "illicit_ratio": round(illicit / total, 4) if total else 0.0,
            "min_time_step": int(sub_df["time_step"].min()),
            "max_time_step": int(sub_df["time_step"].max()),
        }

    return {
        "train": stats(train_df, "Training (Steps 1-28)"),
        "validation": stats(val_df, "Validation (Steps 29-34)"),
        "test": stats(test_df, "Testing (Steps 35-49)"),
    }

