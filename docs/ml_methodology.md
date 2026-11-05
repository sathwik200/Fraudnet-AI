# FRAUDNET AI — Supervised Machine Learning Methodology

## 1. Problem Formulation & Academic Scope

Supervised detection of illicit Bitcoin transactions in the Elliptic dataset is formulated as an imbalanced, time-dependent binary classification task:

$$y_i = \begin{cases} 1 & \text{if transaction } i \text{ is confirmed illicit (Class 1)} \\ 0 & \text{if transaction } i \text{ is confirmed licit (Class 2)} \end{cases}$$

Transactions labeled as `unknown` ($n = 157,205$) are strictly excluded from the supervised loss function and evaluation ground truth, preserving 46,564 labeled transactions for model development.

---

## 2. Prevention of Temporal & Target Leakage

Standard random $k$-fold cross-validation is fundamentally flawed for financial transaction graphs because it allows models to train on future transactions and predict historical transactions.

To ensure realistic forensic evaluation, FRAUDNET AI enforces strict temporal forward validation:

```
[Time Steps 1 – 28: Historical Training]  ==>  [Time Steps 29 – 34: Validation]  ==>  [Time Steps 35 – 49: Out-of-Time Test]
        29,894 Labeled Transactions                   4,960 Labeled Transactions                    11,710 Labeled Transactions
        (2,810 Illicit / 27,084 Licit)                 (648 Illicit / 4,312 Licit)                  (1,087 Illicit / 10,623 Licit)
```

### Leakage Safeguards
1. **Target Feature Exemption:** Neither transaction IDs (`txId`), time step indices (`time_step`), nor class labels (`label`) are passed to the feature matrix $X$.
2. **Train-Only Parameter Fitting:** The median imputer (`SimpleImputer`) and standardization scaler (`StandardScaler`) in `FraudnetFeaturePipeline` are fitted exclusively on the training partition (Steps 1–28) and applied statelessly to subsequent validation and testing partitions.
3. **Temporal Graph Partitioning:** Graph centrality metrics (degrees, PageRank, community IDs) are computed within each temporal component. Because zero edges cross between time steps, no future topology leaks into past node features.

---

## 3. Supervised Model Benchmark & Comparison

Three distinct model families were implemented and benchmarked on the validation partition (Steps 29–34):

1. **Regularized Logistic Regression (L2 / Ridge Baseline):**
   - Class weight: balanced
   - Purpose: Establish linear separability baseline.
2. **Histogram-based Gradient Boosting (`HistGradientBoostingClassifier`):**
   - Max depth: 10, learning rate: 0.05, early stopping enabled.
   - Purpose: Non-linear tree boosting baseline.
3. **Balanced Random Forest (`RandomForestClassifier`):**
   - Trees: 100, max depth: 16, min samples split: 5, class weight: balanced, random state: 42.
   - Purpose: High-capacity bagging ensemble resistant to overfitting on imbalanced noisy features.

### Validation Benchmark Results

| Model Architecture | Validation PR-AUC | Validation ROC-AUC | Validation F1 (Illicit) | Precision (Illicit) | Recall (Illicit) | Selection Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Random Forest** | **0.9852** | **0.9877** | **0.8655** | 0.8521 | 0.8793 | **🏆 Selected Champion** |
| HistGradientBoosting | 0.8576 | 0.9412 | 0.7601 | 0.7240 | 0.8000 | Candidate |
| Logistic Regression | 0.6120 | 0.8763 | 0.5841 | 0.4682 | 0.7762 | Baseline |

---

## 4. Decision Threshold Tuning

Because illicit transactions account for less than 10% of labeled data, standard $0.50$ probability thresholding is suboptimal. Using `find_optimal_threshold`, the decision boundary was calibrated on the validation partition to maximize the F1-score for the minority illicit class:

$$\theta^* = \arg\max_{\theta \in [0.15, 0.85]} F_1(\theta) = \arg\max_{\theta} \frac{2 \cdot P(\theta) \cdot R(\theta)}{P(\theta) + R(\theta)}$$

- **Calibrated Decision Threshold:** $\theta^* = 0.5000$ (Random Forest probabilities are well-calibrated, yielding optimal balance at 0.50).

---

## 5. Local Risk Feature Attribution (XAI)

For every transaction scored by the model, local feature attribution is computed relative to the empirical licit distribution of that temporal partition:

$$z_{i,j} = \frac{x_{i,j} - \mu_{j,\text{licit}}}{\sigma_{j,\text{licit}} + \epsilon}$$

Features with $|z_{i,j}| \ge 2.0$ standard deviations are surfaced as primary risk-elevating (if $z > 0$ and correlated with fraud) or risk-mitigating (if $z < 0$) investigative drivers.

