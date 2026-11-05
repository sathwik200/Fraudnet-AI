#!/usr/bin/env python3
"""
FRAUDNET AI — Elliptic Dataset Inspector
=========================================
Performs a complete initial inspection of the three Elliptic Bitcoin
transaction CSV files without modifying them.

Output artefacts
----------------
* stdout   — human-readable inspection report
* data/dataset_summary.json — machine-readable summary
* docs/dataset_inspection.md — detailed Markdown report
"""

import csv
import json
import os
import sys
import hashlib
from collections import Counter, OrderedDict
from pathlib import Path
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "raw" / "elliptic"
FEATURES_FILE = DATA_DIR / "elliptic_txs_features.csv"
CLASSES_FILE = DATA_DIR / "elliptic_txs_classes.csv"
EDGELIST_FILE = DATA_DIR / "elliptic_txs_edgelist.csv"

OUTPUT_JSON = PROJECT_ROOT / "data" / "dataset_summary.json"
OUTPUT_MD = PROJECT_ROOT / "docs" / "dataset_inspection.md"


def file_size_human(size_bytes: int) -> str:
    """Return a human-readable file size string."""
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} TB"


def md5_hash(path: Path, chunk_size: int = 1 << 20) -> str:
    """Compute MD5 hash of a file for integrity tracking."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def detect_delimiter(path: Path, n_lines: int = 5) -> str:
    """Sniff the delimiter from the first few lines."""
    with open(path, "r", newline="") as f:
        sample = "".join(f.readline() for _ in range(n_lines))
    try:
        dialect = csv.Sniffer().sniff(sample)
        return dialect.delimiter
    except csv.Error:
        return ","


def detect_header(path: Path, delimiter: str) -> bool:
    """Heuristic: a header row has non-numeric first fields."""
    with open(path, "r", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        first_row = next(reader)
    # If ANY field in the first row is purely non-numeric text, likely a header
    non_numeric = 0
    for v in first_row:
        try:
            float(v)
        except ValueError:
            non_numeric += 1
    return non_numeric > 0


def count_lines(path: Path) -> int:
    """Fast line count without loading entire file into memory."""
    count = 0
    with open(path, "rb") as f:
        while True:
            buf = f.read(1 << 20)
            if not buf:
                break
            count += buf.count(b"\n")
    return count


def read_sample_rows(path: Path, delimiter: str, has_header: bool,
                     n: int = 5) -> tuple:
    """Return (header_or_None, list_of_rows[:n])."""
    rows = []
    header = None
    with open(path, "r", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        if has_header:
            header = next(reader)
        for i, row in enumerate(reader):
            if i >= n:
                break
            rows.append(row)
    return header, rows


def inspect_column_widths(path: Path, delimiter: str, has_header: bool,
                          sample_size: int = 1000) -> list:
    """Check that all rows have the same number of columns."""
    widths = Counter()
    with open(path, "r", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        if has_header:
            next(reader)
        for i, row in enumerate(reader):
            widths[len(row)] += 1
            if i >= sample_size - 1:
                break
    return widths.most_common()


def full_column_width_check(path: Path, delimiter: str, has_header: bool) -> Counter:
    """Full scan for column width distribution."""
    widths = Counter()
    with open(path, "r", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        if has_header:
            next(reader)
        for row in reader:
            widths[len(row)] += 1
    return widths


# ---------------------------------------------------------------------------
# INSPECTION: Features file
# ---------------------------------------------------------------------------
def inspect_features():
    """Inspect elliptic_txs_features.csv."""
    print("=" * 72)
    print("INSPECTING: elliptic_txs_features.csv")
    print("=" * 72)

    info = {}
    p = FEATURES_FILE
    info["file"] = p.name
    info["exists"] = p.exists()
    if not p.exists():
        print("  FILE NOT FOUND!")
        return info

    info["size_bytes"] = p.stat().st_size
    info["size_human"] = file_size_human(p.stat().st_size)
    info["md5"] = md5_hash(p)
    info["delimiter"] = detect_delimiter(p)
    info["has_header"] = detect_header(p, info["delimiter"])

    total_lines = count_lines(p)
    info["total_lines"] = total_lines
    info["data_rows"] = total_lines - (1 if info["has_header"] else 0)

    header, sample = read_sample_rows(p, info["delimiter"], info["has_header"], n=5)
    info["num_columns"] = len(sample[0]) if sample else 0
    info["header"] = header
    info["sample_rows"] = sample[:3]  # keep just 3 for JSON

    # Full column-width check
    col_widths = full_column_width_check(p, info["delimiter"], info["has_header"])
    info["column_width_distribution"] = dict(col_widths.most_common())
    malformed = {k: v for k, v in col_widths.items() if k != info["num_columns"]}
    info["malformed_rows_count"] = sum(malformed.values()) if malformed else 0

    # Extract transaction IDs (col 0) and time steps (col 1) in a single pass
    tx_ids = []
    time_steps = Counter()
    missing_values_per_col = Counter()  # track cols with empty strings
    col_has_non_numeric = set()
    duplicate_check = set()
    duplicates = []

    with open(p, "r", newline="") as f:
        reader = csv.reader(f, delimiter=info["delimiter"])
        if info["has_header"]:
            next(reader)
        for row_idx, row in enumerate(reader):
            if len(row) < 2:
                continue
            txid = row[0]
            ts = row[1]
            tx_ids.append(txid)
            time_steps[ts] += 1
            if txid in duplicate_check:
                duplicates.append(txid)
            else:
                duplicate_check.add(txid)

            # Check for missing/empty values (sample first 5000 rows for speed)
            if row_idx < 5000:
                for ci, val in enumerate(row):
                    if val.strip() == "":
                        missing_values_per_col[ci] += 1
                    if ci >= 2:
                        try:
                            float(val)
                        except ValueError:
                            col_has_non_numeric.add(ci)

    info["num_transactions"] = len(tx_ids)
    info["num_unique_tx_ids"] = len(duplicate_check)
    info["duplicate_tx_ids_count"] = len(duplicates)
    info["duplicate_tx_id_examples"] = duplicates[:10]

    # Time steps
    sorted_ts = sorted(time_steps.keys(), key=lambda x: int(x) if x.lstrip('-').isdigit() else x)
    info["num_unique_time_steps"] = len(sorted_ts)
    info["time_step_range"] = [sorted_ts[0], sorted_ts[-1]] if sorted_ts else []
    info["time_step_distribution"] = {k: time_steps[k] for k in sorted_ts}

    # Missing values
    info["missing_values_sampled_5000"] = dict(missing_values_per_col) if missing_values_per_col else "none"
    info["non_numeric_feature_columns"] = sorted(col_has_non_numeric) if col_has_non_numeric else "none"

    # Inferred schema
    schema = []
    schema.append({"col_index": 0, "inferred_name": "txId", "type": "integer (transaction ID)"})
    schema.append({"col_index": 1, "inferred_name": "time_step", "type": "integer"})
    for i in range(2, info["num_columns"]):
        label = f"local_feature_{i-1}" if i < 95 else f"aggregate_feature_{i-94}"
        schema.append({"col_index": i, "inferred_name": label, "type": "float64"})
    info["inferred_schema"] = schema[:5] + ["..."] + schema[-3:]  # truncated for readability

    # Print summary
    print(f"  Size:             {info['size_human']} ({info['size_bytes']} bytes)")
    print(f"  MD5:              {info['md5']}")
    print(f"  Delimiter:        comma (',')")
    print(f"  Has header:       {info['has_header']}")
    print(f"  Total lines:      {info['total_lines']}")
    print(f"  Data rows:        {info['data_rows']}")
    print(f"  Columns:          {info['num_columns']}")
    print(f"  Transactions:     {info['num_transactions']}")
    print(f"  Unique tx IDs:    {info['num_unique_tx_ids']}")
    print(f"  Duplicate tx IDs: {info['duplicate_tx_ids_count']}")
    print(f"  Time steps:       {info['num_unique_time_steps']}  range [{info['time_step_range'][0]}..{info['time_step_range'][1]}]")
    print(f"  Col-width issues: {info['malformed_rows_count']}")
    print(f"  Missing vals (sample): {info['missing_values_sampled_5000']}")
    print(f"  Non-numeric feat cols: {info['non_numeric_feature_columns']}")
    print()

    return info, set(tx_ids)


# ---------------------------------------------------------------------------
# INSPECTION: Classes file
# ---------------------------------------------------------------------------
def inspect_classes():
    """Inspect elliptic_txs_classes.csv."""
    print("=" * 72)
    print("INSPECTING: elliptic_txs_classes.csv")
    print("=" * 72)

    info = {}
    p = CLASSES_FILE
    info["file"] = p.name
    info["exists"] = p.exists()
    if not p.exists():
        print("  FILE NOT FOUND!")
        return info, set()

    info["size_bytes"] = p.stat().st_size
    info["size_human"] = file_size_human(p.stat().st_size)
    info["md5"] = md5_hash(p)
    info["delimiter"] = detect_delimiter(p)
    info["has_header"] = detect_header(p, info["delimiter"])

    total_lines = count_lines(p)
    info["total_lines"] = total_lines
    info["data_rows"] = total_lines - (1 if info["has_header"] else 0)

    header, sample = read_sample_rows(p, info["delimiter"], info["has_header"], n=5)
    info["num_columns"] = len(header) if header else (len(sample[0]) if sample else 0)
    info["header"] = header
    info["sample_rows"] = sample[:5]

    # Full scan
    class_dist = Counter()
    tx_ids = []
    duplicate_check = set()
    duplicates = []
    unexpected_classes = []

    with open(p, "r", newline="") as f:
        reader = csv.reader(f, delimiter=info["delimiter"])
        if info["has_header"]:
            next(reader)
        for row_idx, row in enumerate(reader):
            if len(row) < 2:
                unexpected_classes.append({"row": row_idx + 2, "content": row})
                continue
            txid = row[0]
            cls = row[1]
            tx_ids.append(txid)
            class_dist[cls] += 1
            if txid in duplicate_check:
                duplicates.append(txid)
            else:
                duplicate_check.add(txid)
            # Check for unexpected class values
            if cls not in ("1", "2", "unknown"):
                unexpected_classes.append({"row": row_idx + 2, "txId": txid, "class": cls})

    info["num_transactions"] = len(tx_ids)
    info["num_unique_tx_ids"] = len(duplicate_check)
    info["duplicate_tx_ids_count"] = len(duplicates)
    info["duplicate_tx_id_examples"] = duplicates[:10]

    # Class distribution
    # In the Elliptic dataset: 1 = illicit, 2 = licit, "unknown" = unknown
    info["class_distribution"] = dict(class_dist.most_common())
    info["class_label_mapping"] = {
        "1": "illicit",
        "2": "licit",
        "unknown": "unknown"
    }
    info["unexpected_class_values"] = unexpected_classes[:20] if unexpected_classes else "none"

    # Print summary
    print(f"  Size:             {info['size_human']} ({info['size_bytes']} bytes)")
    print(f"  MD5:              {info['md5']}")
    print(f"  Delimiter:        comma (',')")
    print(f"  Has header:       {info['has_header']}")
    print(f"  Header:           {info['header']}")
    print(f"  Total lines:      {info['total_lines']}")
    print(f"  Data rows:        {info['data_rows']}")
    print(f"  Columns:          {info['num_columns']}")
    print(f"  Transactions:     {info['num_transactions']}")
    print(f"  Unique tx IDs:    {info['num_unique_tx_ids']}")
    print(f"  Duplicate tx IDs: {info['duplicate_tx_ids_count']}")
    print()
    print("  Class distribution:")
    for cls, cnt in class_dist.most_common():
        label = info["class_label_mapping"].get(cls, "???")
        print(f"    {cls:>10s} ({label:>8s}): {cnt:>8,d}")
    print()
    print(f"  Unexpected class values: {info['unexpected_class_values']}")
    print()

    return info, set(tx_ids)


# ---------------------------------------------------------------------------
# INSPECTION: Edge-list file
# ---------------------------------------------------------------------------
def inspect_edgelist(features_tx_set: set):
    """Inspect elliptic_txs_edgelist.csv."""
    print("=" * 72)
    print("INSPECTING: elliptic_txs_edgelist.csv")
    print("=" * 72)

    info = {}
    p = EDGELIST_FILE
    info["file"] = p.name
    info["exists"] = p.exists()
    if not p.exists():
        print("  FILE NOT FOUND!")
        return info

    info["size_bytes"] = p.stat().st_size
    info["size_human"] = file_size_human(p.stat().st_size)
    info["md5"] = md5_hash(p)
    info["delimiter"] = detect_delimiter(p)
    info["has_header"] = detect_header(p, info["delimiter"])

    total_lines = count_lines(p)
    info["total_lines"] = total_lines
    info["data_rows"] = total_lines - (1 if info["has_header"] else 0)

    header, sample = read_sample_rows(p, info["delimiter"], info["has_header"], n=5)
    info["num_columns"] = len(header) if header else (len(sample[0]) if sample else 0)
    info["header"] = header
    info["sample_rows"] = sample[:5]

    # Full scan
    edge_count = 0
    unique_nodes = set()
    malformed_rows = []
    missing_in_features_src = set()
    missing_in_features_dst = set()

    with open(p, "r", newline="") as f:
        reader = csv.reader(f, delimiter=info["delimiter"])
        if info["has_header"]:
            next(reader)
        for row_idx, row in enumerate(reader):
            if len(row) != 2:
                malformed_rows.append({"row": row_idx + 2, "content": row})
                continue
            src, dst = row[0].strip(), row[1].strip()
            edge_count += 1
            unique_nodes.add(src)
            unique_nodes.add(dst)

            if features_tx_set and src not in features_tx_set:
                missing_in_features_src.add(src)
            if features_tx_set and dst not in features_tx_set:
                missing_in_features_dst.add(dst)

    info["num_edges"] = edge_count
    info["num_unique_nodes"] = len(unique_nodes)
    info["malformed_rows_count"] = len(malformed_rows)
    info["malformed_row_examples"] = malformed_rows[:10]

    # Cross-reference with features
    all_missing = missing_in_features_src | missing_in_features_dst
    info["edge_nodes_missing_from_features"] = len(all_missing)
    info["missing_node_examples"] = sorted(list(all_missing))[:20]

    # Print summary
    print(f"  Size:             {info['size_human']} ({info['size_bytes']} bytes)")
    print(f"  MD5:              {info['md5']}")
    print(f"  Delimiter:        comma (',')")
    print(f"  Has header:       {info['has_header']}")
    print(f"  Header:           {info['header']}")
    print(f"  Total lines:      {info['total_lines']}")
    print(f"  Data rows:        {info['data_rows']}")
    print(f"  Columns:          {info['num_columns']}")
    print(f"  Edges:            {edge_count:,d}")
    print(f"  Unique nodes:     {len(unique_nodes):,d}")
    print(f"  Malformed rows:   {len(malformed_rows)}")
    print(f"  Edge nodes NOT in features file: {len(all_missing)}")
    if all_missing:
        print(f"    Examples: {sorted(list(all_missing))[:10]}")
    print()

    return info


# ---------------------------------------------------------------------------
# Cross-file consistency
# ---------------------------------------------------------------------------
def cross_file_consistency(features_tx: set, classes_tx: set):
    """Check ID consistency between features and classes files."""
    print("=" * 72)
    print("CROSS-FILE CONSISTENCY CHECK")
    print("=" * 72)

    info = {}
    in_features_not_classes = features_tx - classes_tx
    in_classes_not_features = classes_tx - features_tx

    info["features_tx_count"] = len(features_tx)
    info["classes_tx_count"] = len(classes_tx)
    info["in_features_not_in_classes"] = len(in_features_not_classes)
    info["in_classes_not_in_features"] = len(in_classes_not_features)
    info["ids_match_perfectly"] = (len(in_features_not_classes) == 0 and
                                    len(in_classes_not_features) == 0)
    info["examples_features_not_classes"] = sorted(list(in_features_not_classes))[:10]
    info["examples_classes_not_features"] = sorted(list(in_classes_not_features))[:10]

    print(f"  Features tx IDs: {len(features_tx):,d}")
    print(f"  Classes  tx IDs: {len(classes_tx):,d}")
    print(f"  In features but NOT in classes: {len(in_features_not_classes)}")
    print(f"  In classes but NOT in features: {len(in_classes_not_features)}")
    print(f"  Perfect match: {info['ids_match_perfectly']}")
    print()

    return info


# ---------------------------------------------------------------------------
# Reference comparison
# ---------------------------------------------------------------------------
def reference_comparison(feat_info, cls_info, edge_info):
    """Compare actual figures against commonly reported Elliptic stats."""
    print("=" * 72)
    print("REFERENCE COMPARISON (commonly reported Elliptic figures)")
    print("=" * 72)

    ref = {
        "transaction_nodes": 203769,
        "edges": 234355,
        "time_steps": 49,
        "features": 166,
        "illicit": 4545,
        "licit": 42019,
        "unknown": 157205,
    }

    comparison = {}
    actual_nodes = feat_info.get("num_transactions", "?")
    actual_edges = edge_info.get("num_edges", "?")
    actual_ts = feat_info.get("num_unique_time_steps", "?")
    actual_feat = feat_info.get("num_columns", "?")
    if isinstance(actual_feat, int):
        actual_feat_count = actual_feat - 1  # subtract txId column; time_step is feature col 1
    else:
        actual_feat_count = "?"

    cd = cls_info.get("class_distribution", {})
    actual_illicit = cd.get("1", "?")
    actual_licit = cd.get("2", "?")
    actual_unknown = cd.get("unknown", "?")

    items = [
        ("Transaction nodes", ref["transaction_nodes"], actual_nodes),
        ("Edges", ref["edges"], actual_edges),
        ("Time steps", ref["time_steps"], actual_ts),
        ("Feature columns (excl txId)", ref["features"], actual_feat_count),
        ("Illicit (class=1)", ref["illicit"], actual_illicit),
        ("Licit (class=2)", ref["licit"], actual_licit),
        ("Unknown", ref["unknown"], actual_unknown),
    ]

    for label, expected, actual in items:
        match = "✓" if expected == actual else "✗"
        comparison[label] = {"expected": expected, "actual": actual, "match": expected == actual}
        print(f"  {match} {label:.<40s} expected={expected:<10}  actual={actual}")

    print()
    return comparison


# ---------------------------------------------------------------------------
# Generate Markdown report
# ---------------------------------------------------------------------------
def generate_markdown(feat_info, cls_info, edge_info, cross_info, ref_info):
    """Write docs/dataset_inspection.md."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def fmt_sample_table(header, rows, max_cols=10):
        """Format a small markdown table, truncating wide rows."""
        if not rows:
            return "_No sample rows available._\n"
        ncols = len(rows[0])
        show = min(ncols, max_cols)
        ellipsis = " | …" if ncols > max_cols else ""

        lines = []
        if header:
            lines.append("| " + " | ".join(header[:show]) + ellipsis + " |")
            lines.append("| " + " | ".join(["---"] * show) + (" | ---" if ncols > max_cols else "") + " |")
        else:
            labels = [f"col_{i}" for i in range(show)]
            lines.append("| " + " | ".join(labels) + ellipsis + " |")
            lines.append("| " + " | ".join(["---"] * show) + (" | ---" if ncols > max_cols else "") + " |")

        for row in rows[:5]:
            vals = [str(v)[:20] for v in row[:show]]
            lines.append("| " + " | ".join(vals) + ellipsis + " |")
        return "\n".join(lines) + "\n"

    md = []
    md.append("# FRAUDNET AI — Dataset Inspection Report\n")
    md.append(f"> **Generated:** {ts}  \n")
    md.append(f"> **Dataset:** Elliptic Bitcoin Transaction Dataset  \n")
    md.append(f"> **Location:** `data/raw/elliptic/`\n\n")
    md.append("---\n\n")

    # Overview
    md.append("## 1. Dataset Overview\n\n")
    md.append("The Elliptic dataset maps Bitcoin transactions on the blockchain to a ")
    md.append("graph network where nodes represent transactions and directed edges represent ")
    md.append("payment flows. Each transaction has 166 features (94 local + 72 aggregate neighbourhood features) ")
    md.append("and a class label: **illicit (1)**, **licit (2)**, or **unknown**.\n\n")
    md.append("| File | Size | Lines | Columns | Has Header |\n")
    md.append("| --- | --- | --- | --- | --- |\n")
    for fi in [feat_info, cls_info, edge_info]:
        md.append(f"| `{fi['file']}` | {fi['size_human']} | {fi['total_lines']:,} | {fi['num_columns']} | {fi['has_header']} |\n")
    md.append("\n")

    # Features
    md.append("## 2. File: `elliptic_txs_features.csv`\n\n")
    md.append(f"- **Size:** {feat_info['size_human']} ({feat_info['size_bytes']:,} bytes)\n")
    md.append(f"- **MD5:** `{feat_info['md5']}`\n")
    md.append(f"- **Delimiter:** comma\n")
    md.append(f"- **Has header row:** {feat_info['has_header']}\n")
    md.append(f"- **Total lines:** {feat_info['total_lines']:,}\n")
    md.append(f"- **Data rows:** {feat_info['data_rows']:,}\n")
    md.append(f"- **Columns:** {feat_info['num_columns']}\n")
    md.append(f"- **Unique transaction IDs:** {feat_info['num_unique_tx_ids']:,}\n")
    md.append(f"- **Duplicate tx IDs:** {feat_info['duplicate_tx_ids_count']}\n")
    md.append(f"- **Unique time steps:** {feat_info['num_unique_time_steps']}\n")
    md.append(f"- **Time step range:** {feat_info['time_step_range']}\n")
    md.append(f"- **Malformed rows:** {feat_info['malformed_rows_count']}\n")
    md.append(f"- **Missing values (sampled 5000 rows):** {feat_info['missing_values_sampled_5000']}\n")
    md.append(f"- **Non-numeric feature columns:** {feat_info['non_numeric_feature_columns']}\n\n")

    md.append("### Schema (inferred — no header in file)\n\n")
    md.append("The file contains **no header row**. Columns are positionally defined:\n\n")
    md.append("| Index | Inferred Name | Data Type | Notes |\n")
    md.append("| --- | --- | --- | --- |\n")
    md.append("| 0 | txId | integer | Transaction ID |\n")
    md.append("| 1 | time_step | integer | Time step (1–49) |\n")
    md.append("| 2–94 | local_feature_1 … local_feature_93 | float64 | 93 local transaction features |\n")
    md.append("| 95–166 | agg_feature_1 … agg_feature_72 | float64 | 72 aggregate neighbourhood features |\n\n")

    md.append("### Sample Rows (first 3, first 10 columns)\n\n")
    md.append(fmt_sample_table(None, feat_info.get("sample_rows", []), max_cols=10))
    md.append("\n")

    md.append("### Time Step Distribution\n\n")
    md.append("| Time Step | Transaction Count |\n")
    md.append("| --- | --- |\n")
    tsd = feat_info.get("time_step_distribution", {})
    for ts_key in sorted(tsd.keys(), key=lambda x: int(x)):
        md.append(f"| {ts_key} | {tsd[ts_key]:,} |\n")
    md.append("\n")

    # Classes
    md.append("## 3. File: `elliptic_txs_classes.csv`\n\n")
    md.append(f"- **Size:** {cls_info['size_human']} ({cls_info['size_bytes']:,} bytes)\n")
    md.append(f"- **MD5:** `{cls_info['md5']}`\n")
    md.append(f"- **Delimiter:** comma\n")
    md.append(f"- **Has header row:** {cls_info['has_header']}\n")
    md.append(f"- **Header:** `{cls_info['header']}`\n")
    md.append(f"- **Total lines:** {cls_info['total_lines']:,}\n")
    md.append(f"- **Data rows:** {cls_info['data_rows']:,}\n")
    md.append(f"- **Columns:** {cls_info['num_columns']}\n")
    md.append(f"- **Unique tx IDs:** {cls_info['num_unique_tx_ids']:,}\n")
    md.append(f"- **Duplicate tx IDs:** {cls_info['duplicate_tx_ids_count']}\n")
    md.append(f"- **Unexpected class values:** {cls_info['unexpected_class_values']}\n\n")

    md.append("### Class Distribution\n\n")
    md.append("| Class | Label | Count | Percentage |\n")
    md.append("| --- | --- | --- | --- |\n")
    total_cls = sum(cls_info["class_distribution"].values())
    for cls_val, cnt in sorted(cls_info["class_distribution"].items(),
                                key=lambda x: -x[1]):
        label = cls_info["class_label_mapping"].get(cls_val, "???")
        pct = cnt / total_cls * 100 if total_cls > 0 else 0
        md.append(f"| {cls_val} | {label} | {cnt:,} | {pct:.2f}% |\n")
    md.append(f"| **Total** | | **{total_cls:,}** | **100%** |\n")
    md.append("\n")

    md.append("### Sample Rows\n\n")
    md.append(fmt_sample_table(cls_info.get("header"), cls_info.get("sample_rows", []), max_cols=5))
    md.append("\n")

    # Edge list
    md.append("## 4. File: `elliptic_txs_edgelist.csv`\n\n")
    md.append(f"- **Size:** {edge_info['size_human']} ({edge_info['size_bytes']:,} bytes)\n")
    md.append(f"- **MD5:** `{edge_info['md5']}`\n")
    md.append(f"- **Delimiter:** comma\n")
    md.append(f"- **Has header row:** {edge_info['has_header']}\n")
    md.append(f"- **Header:** `{edge_info['header']}`\n")
    md.append(f"- **Total lines:** {edge_info['total_lines']:,}\n")
    md.append(f"- **Data rows:** {edge_info['data_rows']:,}\n")
    md.append(f"- **Columns:** {edge_info['num_columns']}\n")
    md.append(f"- **Edges:** {edge_info['num_edges']:,}\n")
    md.append(f"- **Unique nodes in edge list:** {edge_info['num_unique_nodes']:,}\n")
    md.append(f"- **Malformed rows:** {edge_info['malformed_rows_count']}\n")
    md.append(f"- **Edge nodes missing from features file:** {edge_info['edge_nodes_missing_from_features']}\n\n")

    md.append("### Sample Rows\n\n")
    md.append(fmt_sample_table(edge_info.get("header"), edge_info.get("sample_rows", []), max_cols=5))
    md.append("\n")

    # Cross-file
    md.append("## 5. Cross-File Consistency\n\n")
    md.append(f"- Features file tx IDs: **{cross_info['features_tx_count']:,}**\n")
    md.append(f"- Classes file tx IDs: **{cross_info['classes_tx_count']:,}**\n")
    md.append(f"- In features but NOT in classes: **{cross_info['in_features_not_in_classes']}**\n")
    md.append(f"- In classes but NOT in features: **{cross_info['in_classes_not_in_features']}**\n")
    md.append(f"- **Perfect 1:1 match:** {cross_info['ids_match_perfectly']}\n\n")
    if cross_info["in_features_not_in_classes"] > 0:
        md.append(f"Examples of IDs in features but not classes: `{cross_info['examples_features_not_classes']}`\n\n")
    if cross_info["in_classes_not_in_features"] > 0:
        md.append(f"Examples of IDs in classes but not features: `{cross_info['examples_classes_not_features']}`\n\n")

    # Reference comparison
    md.append("## 6. Reference Comparison\n\n")
    md.append("Comparison with commonly reported Elliptic dataset statistics:\n\n")
    md.append("| Metric | Expected | Actual | Match |\n")
    md.append("| --- | --- | --- | --- |\n")
    for label, vals in ref_info.items():
        m = "✅" if vals["match"] else "❌"
        md.append(f"| {label} | {vals['expected']} | {vals['actual']} | {m} |\n")
    md.append("\n")

    # Data quality summary
    md.append("## 7. Data Quality Summary\n\n")
    issues = []
    if feat_info["malformed_rows_count"] > 0:
        issues.append(f"- ⚠️ Features file has {feat_info['malformed_rows_count']} malformed rows")
    if feat_info["duplicate_tx_ids_count"] > 0:
        issues.append(f"- ⚠️ Features file has {feat_info['duplicate_tx_ids_count']} duplicate tx IDs")
    if cls_info["duplicate_tx_ids_count"] > 0:
        issues.append(f"- ⚠️ Classes file has {cls_info['duplicate_tx_ids_count']} duplicate tx IDs")
    if edge_info["malformed_rows_count"] > 0:
        issues.append(f"- ⚠️ Edge list has {edge_info['malformed_rows_count']} malformed rows")
    if edge_info["edge_nodes_missing_from_features"] > 0:
        issues.append(f"- ⚠️ {edge_info['edge_nodes_missing_from_features']} edge endpoints not found in features file")
    if not cross_info["ids_match_perfectly"]:
        issues.append("- ⚠️ Transaction ID sets do not match perfectly between features and classes files")
    if cls_info["unexpected_class_values"] != "none":
        issues.append(f"- ⚠️ Unexpected class values found: {cls_info['unexpected_class_values']}")
    if feat_info["missing_values_sampled_5000"] != "none":
        issues.append(f"- ⚠️ Missing values detected in sampled rows")

    if issues:
        md.append("### Issues Found\n\n")
        md.append("\n".join(issues) + "\n\n")
    else:
        md.append("✅ **No data quality issues detected.** The dataset is clean and consistent.\n\n")

    # Final summary
    md.append("## 8. Final Inspection Summary\n\n")
    md.append("| Item | Value |\n")
    md.append("| --- | --- |\n")
    md.append(f"| Total transaction nodes | {feat_info['num_transactions']:,} |\n")
    md.append(f"| Total edges | {edge_info['num_edges']:,} |\n")
    md.append(f"| Unique nodes in edges | {edge_info['num_unique_nodes']:,} |\n")
    md.append(f"| Time steps | {feat_info['num_unique_time_steps']} |\n")
    md.append(f"| Feature columns (incl txId + time_step) | {feat_info['num_columns']} |\n")
    total_cls = sum(cls_info["class_distribution"].values())
    md.append(f"| Illicit transactions | {cls_info['class_distribution'].get('1', 0):,} |\n")
    md.append(f"| Licit transactions | {cls_info['class_distribution'].get('2', 0):,} |\n")
    md.append(f"| Unknown transactions | {cls_info['class_distribution'].get('unknown', 0):,} |\n")
    md.append(f"| Features–Classes ID match | {'Yes' if cross_info['ids_match_perfectly'] else 'No'} |\n")
    md.append(f"| Orphan edge nodes | {edge_info['edge_nodes_missing_from_features']} |\n")
    md.append(f"| Duplicate tx IDs (features) | {feat_info['duplicate_tx_ids_count']} |\n")
    md.append(f"| Duplicate tx IDs (classes) | {cls_info['duplicate_tx_ids_count']} |\n")
    md.append("\n")
    md.append("---\n\n")
    md.append(f"*Report generated by `src/data/inspect_dataset.py` on {ts}*\n")

    OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_MD, "w") as f:
        f.write("".join(md))
    print(f"Markdown report written to: {OUTPUT_MD}")


# ---------------------------------------------------------------------------
# Generate JSON summary
# ---------------------------------------------------------------------------
def generate_json(feat_info, cls_info, edge_info, cross_info, ref_info):
    """Write data/dataset_summary.json."""
    summary = OrderedDict()
    summary["generated_at"] = datetime.now(timezone.utc).isoformat()
    summary["dataset"] = "Elliptic Bitcoin Transaction Dataset"
    summary["location"] = "data/raw/elliptic/"

    summary["files"] = {
        "features": feat_info,
        "classes": cls_info,
        "edgelist": edge_info,
    }
    summary["cross_file_consistency"] = cross_info
    summary["reference_comparison"] = ref_info

    # Clean up sets / non-serializable types
    def sanitize(obj):
        if isinstance(obj, set):
            return sorted(list(obj))
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(i) for i in obj]
        return obj

    summary = sanitize(summary)

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(summary, f, indent=2, default=str)
    print(f"JSON summary written to: {OUTPUT_JSON}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print()
    print("╔══════════════════════════════════════════════════════════════════════╗")
    print("║           FRAUDNET AI — Elliptic Dataset Inspection                ║")
    print("╚══════════════════════════════════════════════════════════════════════╝")
    print()

    # 1. Verify existence
    print("Checking file existence...")
    all_exist = True
    for fp in [FEATURES_FILE, CLASSES_FILE, EDGELIST_FILE]:
        status = "✓ FOUND" if fp.exists() else "✗ MISSING"
        print(f"  {status}: {fp.name}  ({fp})")
        if not fp.exists():
            all_exist = False
    print()

    if not all_exist:
        print("ERROR: One or more dataset files are missing. Aborting.")
        sys.exit(1)

    # 2. Inspect each file
    feat_info, features_tx_set = inspect_features()
    cls_info, classes_tx_set = inspect_classes()
    edge_info = inspect_edgelist(features_tx_set)

    # 3. Cross-file consistency
    cross_info = cross_file_consistency(features_tx_set, classes_tx_set)

    # 4. Reference comparison
    ref_info = reference_comparison(feat_info, cls_info, edge_info)

    # 5. Generate outputs
    print("=" * 72)
    print("GENERATING OUTPUT FILES")
    print("=" * 72)
    generate_markdown(feat_info, cls_info, edge_info, cross_info, ref_info)
    generate_json(feat_info, cls_info, edge_info, cross_info, ref_info)

    print()
    print("═" * 72)
    print("  INSPECTION COMPLETE")
    print("═" * 72)
    print()


if __name__ == "__main__":
    main()

