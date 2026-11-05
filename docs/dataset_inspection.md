# FRAUDNET AI — Dataset Inspection Report
> **Generated:** 2026-11-05 10:29:02 UTC  
> **Dataset:** Elliptic Bitcoin Transaction Dataset  
> **Location:** `data/raw/elliptic/`

---

## 1. Dataset Overview

The Elliptic dataset maps Bitcoin transactions on the blockchain to a graph network where nodes represent transactions and directed edges represent payment flows. Each transaction has 166 features (94 local + 72 aggregate neighbourhood features) and a class label: **illicit (1)**, **licit (2)**, or **unknown**.

| File | Size | Lines | Columns | Has Header |
| --- | --- | --- | --- | --- |
| `elliptic_txs_features.csv` | 657.73 MB | 203,769 | 167 | False |
| `elliptic_txs_classes.csv` | 3.15 MB | 203,770 | 2 | True |
| `elliptic_txs_edgelist.csv` | 4.26 MB | 234,356 | 2 | True |

## 2. File: `elliptic_txs_features.csv`

- **Size:** 657.73 MB (689,683,771 bytes)
- **MD5:** `9fb9dc51d9d1329f540cb6f83730f4a1`
- **Delimiter:** comma
- **Has header row:** False
- **Total lines:** 203,769
- **Data rows:** 203,769
- **Columns:** 167
- **Unique transaction IDs:** 203,769
- **Duplicate tx IDs:** 0
- **Unique time steps:** 49
- **Time step range:** ['1', '49']
- **Malformed rows:** 0
- **Missing values (sampled 5000 rows):** none
- **Non-numeric feature columns:** none

### Schema (inferred — no header in file)

The file contains **no header row**. Columns are positionally defined:

| Index | Inferred Name | Data Type | Notes |
| --- | --- | --- | --- |
| 0 | txId | integer | Transaction ID |
| 1 | time_step | integer | Time step (1–49) |
| 2–94 | local_feature_1 … local_feature_93 | float64 | 93 local transaction features |
| 95–166 | agg_feature_1 … agg_feature_72 | float64 | 72 aggregate neighbourhood features |

### Sample Rows (first 3, first 10 columns)

| col_0 | col_1 | col_2 | col_3 | col_4 | col_5 | col_6 | col_7 | col_8 | col_9 | … |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 230425980 | 1 | -0.1714692896288031 | -0.18466755143291433 | -1.2013688016765636 | -0.12196959975910057 | -0.04387454791734898 | -0.11300200928476244 | -0.06158379407303222 | -0.16209679981659642 | … |
| 5530458 | 1 | -0.17148421069432254 | -0.18466755143291433 | -1.2013688016765636 | -0.12196959975910057 | -0.04387454791734898 | -0.11300200928476244 | -0.06158379407303222 | -0.16211206626677477 | … |
| 232022460 | 1 | -0.17210694047251704 | -0.18466755143291433 | -1.2013688016765636 | -0.12196959975910057 | -0.04387454791734898 | -0.11300200928476244 | -0.06158379407303222 | -0.16274921065307707 | … |

### Time Step Distribution

| Time Step | Transaction Count |
| --- | --- |
| 1 | 7,880 |
| 2 | 4,544 |
| 3 | 6,621 |
| 4 | 5,693 |
| 5 | 6,803 |
| 6 | 4,328 |
| 7 | 6,048 |
| 8 | 4,457 |
| 9 | 4,996 |
| 10 | 6,727 |
| 11 | 4,296 |
| 12 | 2,047 |
| 13 | 4,528 |
| 14 | 2,022 |
| 15 | 3,639 |
| 16 | 2,975 |
| 17 | 3,385 |
| 18 | 1,976 |
| 19 | 3,506 |
| 20 | 4,291 |
| 21 | 3,537 |
| 22 | 5,894 |
| 23 | 4,165 |
| 24 | 4,592 |
| 25 | 2,314 |
| 26 | 2,523 |
| 27 | 1,089 |
| 28 | 1,653 |
| 29 | 4,275 |
| 30 | 2,483 |
| 31 | 2,816 |
| 32 | 4,525 |
| 33 | 3,151 |
| 34 | 2,486 |
| 35 | 5,507 |
| 36 | 6,393 |
| 37 | 3,306 |
| 38 | 2,891 |
| 39 | 2,760 |
| 40 | 4,481 |
| 41 | 5,342 |
| 42 | 7,140 |
| 43 | 5,063 |
| 44 | 4,975 |
| 45 | 5,598 |
| 46 | 3,519 |
| 47 | 5,121 |
| 48 | 2,954 |
| 49 | 2,454 |

## 3. File: `elliptic_txs_classes.csv`

- **Size:** 3.15 MB (3,305,144 bytes)
- **MD5:** `7ad28a0fd7d0075684708bfba9e78e72`
- **Delimiter:** comma
- **Has header row:** True
- **Header:** `['txId', 'class']`
- **Total lines:** 203,770
- **Data rows:** 203,769
- **Columns:** 2
- **Unique tx IDs:** 203,769
- **Duplicate tx IDs:** 0
- **Unexpected class values:** none

### Class Distribution

| Class | Label | Count | Percentage |
| --- | --- | --- | --- |
| unknown | unknown | 157,205 | 77.15% |
| 2 | licit | 42,019 | 20.62% |
| 1 | illicit | 4,545 | 2.23% |
| **Total** | | **203,769** | **100%** |

### Sample Rows

| txId | class |
| --- | --- |
| 230425980 | unknown |
| 5530458 | unknown |
| 232022460 | unknown |
| 232438397 | 2 |
| 230460314 | unknown |

## 4. File: `elliptic_txs_edgelist.csv`

- **Size:** 4.26 MB (4,470,584 bytes)
- **MD5:** `ae69bde1407c9320c0124a557693a479`
- **Delimiter:** comma
- **Has header row:** True
- **Header:** `['txId1', 'txId2']`
- **Total lines:** 234,356
- **Data rows:** 234,355
- **Columns:** 2
- **Edges:** 234,355
- **Unique nodes in edge list:** 203,769
- **Malformed rows:** 0
- **Edge nodes missing from features file:** 0

### Sample Rows

| txId1 | txId2 |
| --- | --- |
| 230425980 | 5530458 |
| 232022460 | 232438397 |
| 230460314 | 230459870 |
| 230333930 | 230595899 |
| 232013274 | 232029206 |

## 5. Cross-File Consistency

- Features file tx IDs: **203,769**
- Classes file tx IDs: **203,769**
- In features but NOT in classes: **0**
- In classes but NOT in features: **0**
- **Perfect 1:1 match:** True

## 6. Reference Comparison

Comparison with commonly reported Elliptic dataset statistics:

| Metric | Expected | Actual | Match |
| --- | --- | --- | --- |
| Transaction nodes | 203769 | 203769 | ✅ |
| Edges | 234355 | 234355 | ✅ |
| Time steps | 49 | 49 | ✅ |
| Feature columns (excl txId) | 166 | 166 | ✅ |
| Illicit (class=1) | 4545 | 4545 | ✅ |
| Licit (class=2) | 42019 | 42019 | ✅ |
| Unknown | 157205 | 157205 | ✅ |

## 7. Data Quality Summary

✅ **No data quality issues detected.** The dataset is clean and consistent.

## 8. Final Inspection Summary

| Item | Value |
| --- | --- |
| Total transaction nodes | 203,769 |
| Total edges | 234,355 |
| Unique nodes in edges | 203,769 |
| Time steps | 49 |
| Feature columns (incl txId + time_step) | 167 |
| Illicit transactions | 4,545 |
| Licit transactions | 42,019 |
| Unknown transactions | 157,205 |
| Features–Classes ID match | Yes |
| Orphan edge nodes | 0 |
| Duplicate tx IDs (features) | 0 |
| Duplicate tx IDs (classes) | 0 |

---

*Report generated by `src/data/inspect_dataset.py` on 2026-11-05 10:29:02 UTC*
