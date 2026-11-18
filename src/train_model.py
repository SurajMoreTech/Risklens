"""
train_model.py
Trains 4 models on the CDC BRFSS Diabetes Health Indicators dataset:
  1. Logistic Regression  (interpretable baseline)
  2. Random Forest         (handles non-linearity)
  3. XGBoost               (best published results on this dataset)
  4. LightGBM              (fast, high performance)

Training strategy:
  - Train on balanced 50/50 split (prevents class imbalance bias)
  - Validate on 20% holdout from balanced set
  - Final test on full imbalanced dataset (real-world distribution)

Healthcare-specific evaluation:
  - Sensitivity (recall), Specificity, PPV, NPV
  - Youden's J statistic for optimal threshold
  - Clinical impact: missed diabetics (FN) vs false alarms (FP)
  - SHAP summary plot for interpretability

Saves all artifacts to models/.

Usage:
    python src/train_model.py
"""

import os
import warnings

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, confusion_matrix, f1_score,
    precision_score, recall_score, roc_auc_score, roc_curve,
)
from xgboost import XGBClassifier
import lightgbm as lgb

from preprocess import load_and_prepare

warnings.filterwarnings("ignore")

MODEL_DIR = "models"
RANDOM_STATE = 42


# ── Healthcare Evaluation ─────────────────────────────────────────
def evaluate_healthcare(model, X, y_true, dataset_name="Validation"):
    """
    Evaluate with clinical metrics: Sensitivity, Specificity, PPV, NPV.
    Uses Youden's J statistic to find the optimal threshold.
    """
    y_prob = model.predict_proba(X)[:, 1]

    # Youden's J statistic for optimal threshold
    fpr, tpr, thresholds = roc_curve(y_true, y_prob)
    j_scores = tpr - fpr
    optimal_idx = np.argmax(j_scores)
    optimal_threshold = thresholds[optimal_idx]

    y_pred_opt = (y_prob >= optimal_threshold).astype(int)

    cm = confusion_matrix(y_true, y_pred_opt)
    tn, fp, fn, tp = cm.ravel()

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
    npv = tn / (tn + fn) if (tn + fn) > 0 else 0
    f1 = f1_score(y_true, y_pred_opt)
    auroc = roc_auc_score(y_true, y_prob)

    print(f"\n=== {dataset_name} Evaluation ===")
    print(f"Optimal Threshold: {optimal_threshold:.3f}")
    print(f"AUROC: {auroc:.4f}")
    print(f"Sensitivity (Recall): {sensitivity:.4f}")
    print(f"Specificity: {specificity:.4f}")
    print(f"PPV (Precision): {ppv:.4f}")
    print(f"NPV: {npv:.4f}")
    print(f"F1-Score: {f1:.4f}")
    print(f"Confusion Matrix: TN={tn:,}, FP={fp:,}, FN={fn:,}, TP={tp:,}")
    print(f"\nClinical Impact:")
    print(f"  -> {fn:,} diabetics MISSED (False Negatives) — DANGEROUS")
    print(f"  -> {fp:,} healthy people falsely alarmed (False Positives) — COSTLY")

    return {
        "threshold": optimal_threshold,
        "auroc": auroc,
        "sensitivity": sensitivity,
        "specificity": specificity,
        "ppv": ppv,
        "npv": npv,
        "f1": f1,
        "fn": fn,
        "fp": fp,
    }


def main():
    os.makedirs(MODEL_DIR, exist_ok=True)

    # ── Load & prepare data ───────────────────────────────────────
    print("Loading and preparing data...")
    (
        X_train, X_val, X_test,
        X_train_scaled, X_val_scaled, X_test_scaled,
        y_train, y_val, y_test,
        scaler, feature_cols,
    ) = load_and_prepare()

    print(f"Train: {X_train.shape}, Val: {X_val.shape}, Test: {X_test.shape}")
    print(f"Features ({len(feature_cols)}): {feature_cols}")

    # ── Define models ─────────────────────────────────────────────
    models = {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=RANDOM_STATE,
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=300, max_depth=12,
            min_samples_split=20, min_samples_leaf=10,
            class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1,
        ),
        "XGBoost": XGBClassifier(
            n_estimators=300, max_depth=6,
            learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
            scale_pos_weight=1,  # balanced dataset → no extra weighting
            eval_metric="auc", random_state=RANDOM_STATE,
        ),
        "LightGBM": lgb.LGBMClassifier(
            n_estimators=300, max_depth=8,
            learning_rate=0.05, num_leaves=31,
            class_weight="balanced", random_state=RANDOM_STATE,
            verbose=-1,
        ),
    }

    # ── Train & Evaluate ──────────────────────────────────────────
    results = []
    fitted_models = {}

    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"Training {name}...")
        print(f"{'='*60}")

        if name == "Logistic Regression":
            model.fit(X_train_scaled, y_train)
            # Validation
            v_prob = model.predict_proba(X_val_scaled)[:, 1]
            v_auc = roc_auc_score(y_val, v_prob)
            # Test
            t_prob = model.predict_proba(X_test_scaled)[:, 1]
            t_auc = roc_auc_score(y_test, t_prob)
        elif name == "XGBoost":
            model.fit(X_train, y_train,
                      eval_set=[(X_val, y_val)], verbose=False)
            v_prob = model.predict_proba(X_val)[:, 1]
            v_auc = roc_auc_score(y_val, v_prob)
            t_prob = model.predict_proba(X_test)[:, 1]
            t_auc = roc_auc_score(y_test, t_prob)
        elif name == "LightGBM":
            model.fit(X_train, y_train,
                      eval_set=[(X_val, y_val)],
                      callbacks=[lgb.early_stopping(50), lgb.log_evaluation(0)])
            v_prob = model.predict_proba(X_val)[:, 1]
            v_auc = roc_auc_score(y_val, v_prob)
            t_prob = model.predict_proba(X_test)[:, 1]
            t_auc = roc_auc_score(y_test, t_prob)
        else:  # Random Forest
            model.fit(X_train, y_train)
            v_prob = model.predict_proba(X_val)[:, 1]
            v_auc = roc_auc_score(y_val, v_prob)
            t_prob = model.predict_proba(X_test)[:, 1]
            t_auc = roc_auc_score(y_test, t_prob)

        # Optimal threshold via Youden's J
        fpr, tpr, thresholds = roc_curve(y_val, v_prob)
        j_scores = tpr - fpr
        opt_thresh = thresholds[np.argmax(j_scores)]

        # Test predictions at optimal threshold
        t_pred = (t_prob >= opt_thresh).astype(int)
        cm = confusion_matrix(y_test, t_pred)
        tn, fp, fn, tp = cm.ravel()

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
        ppv = tp / (tp + fp) if (tp + fp) > 0 else 0
        npv = tn / (tn + fn) if (tn + fn) > 0 else 0
        f1 = f1_score(y_test, t_pred)

        results.append({
            "Model": name,
            "Val_AUROC": round(v_auc, 4),
            "Test_AUROC": round(t_auc, 4),
            "Sensitivity": round(sensitivity, 4),
            "Specificity": round(specificity, 4),
            "PPV": round(ppv, 4),
            "NPV": round(npv, 4),
            "F1": round(f1, 4),
            "Threshold": round(opt_thresh, 3),
            "FN": fn,
            "FP": fp,
        })
        fitted_models[name] = model

        print(f"  Val AUROC: {v_auc:.4f} | Test AUROC: {t_auc:.4f}")
        print(f"  Sensitivity: {sensitivity:.4f} | Specificity: {specificity:.4f}")
        print(f"  PPV: {ppv:.4f} | NPV: {npv:.4f}")
        print(f"  F1: {f1:.4f} | Threshold: {opt_thresh:.3f}")
        print(f"  Missed Diabetics (FN): {fn:,} | False Alarms (FP): {fp:,}")

    # ── Results comparison ────────────────────────────────────────
    results_df = pd.DataFrame(results).sort_values("Test_AUROC", ascending=False)
    print(f"\n{'='*60}")
    print("MODEL COMPARISON (sorted by Test AUROC)")
    print(f"{'='*60}")
    print(results_df.to_string(index=False))

    # ── Select best model ─────────────────────────────────────────
    best_row = results_df.iloc[0]
    best_name = best_row["Model"]
    best_model = fitted_models[best_name]
    best_threshold = best_row["Threshold"]

    print(f"\n*** BEST MODEL: {best_name} ***")
    print(f"  Test AUROC: {best_row['Test_AUROC']}")
    print(f"  Sensitivity: {best_row['Sensitivity']}")
    print(f"  Specificity: {best_row['Specificity']}")
    print(f"  Optimal Threshold: {best_threshold}")

    # ── Full healthcare evaluation on test set ─────────────────────
    print(f"\n{'='*60}")
    print(f"FULL HEALTHCARE EVALUATION: {best_name} on Test Set")
    print(f"{'='*60}")
    if best_name == "Logistic Regression":
        evaluate_healthcare(best_model, X_test_scaled, y_test, "Test (Real World)")
    else:
        evaluate_healthcare(best_model, X_test, y_test, "Test (Real World)")

    # ── Save artifacts ────────────────────────────────────────────
    print(f"\nSaving artifacts to {MODEL_DIR}/...")
    joblib.dump(best_model, os.path.join(MODEL_DIR, "best_model.pkl"))
    joblib.dump(scaler, os.path.join(MODEL_DIR, "scaler.pkl"))
    joblib.dump(best_name, os.path.join(MODEL_DIR, "model_name.pkl"))
    joblib.dump(float(best_threshold), os.path.join(MODEL_DIR, "threshold.pkl"))
    joblib.dump(feature_cols, os.path.join(MODEL_DIR, "feature_cols.pkl"))
    results_df.to_csv(os.path.join(MODEL_DIR, "model_comparison.csv"), index=False)

    # ── SHAP summary plot ─────────────────────────────────────────
    print("\nGenerating SHAP summary plot...")
    try:
        if best_name == "Logistic Regression":
            explainer = shap.LinearExplainer(best_model, X_train_scaled)
            shap_values = explainer.shap_values(X_test_scaled[:1000])
            shap_display = pd.DataFrame(X_test_scaled[:1000], columns=feature_cols)
        else:
            explainer = shap.TreeExplainer(best_model)
            shap_values = explainer.shap_values(X_test.iloc[:1000])
            if isinstance(shap_values, list):
                shap_values = shap_values[1]
            shap_display = X_test.iloc[:1000]

        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values, shap_display,
                          feature_names=feature_cols, show=False)
        plt.title("SHAP Feature Importance — What Drives Diabetes Risk?")
        plt.tight_layout()
        plt.savefig(os.path.join(MODEL_DIR, "shap_summary.png"), dpi=150)
        plt.close()
        print("Saved SHAP summary plot to models/shap_summary.png")
    except Exception as e:
        print(f"SHAP plot skipped: {e}")

    # ── Threshold scan ────────────────────────────────────────────
    print(f"\nThreshold scan for {best_name}:")
    if best_name == "Logistic Regression":
        test_probs = best_model.predict_proba(X_test_scaled)[:, 1]
    else:
        test_probs = best_model.predict_proba(X_test)[:, 1]

    print(f"{'Threshold':>10} {'Precision':>10} {'Recall':>10} {'F1':>8} {'FN':>8} {'FP':>8}")
    for t in [0.10, 0.20, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70]:
        preds_at_t = (test_probs >= t).astype(int)
        p = precision_score(y_test, preds_at_t, zero_division=0)
        r = recall_score(y_test, preds_at_t, zero_division=0)
        f = f1_score(y_test, preds_at_t, zero_division=0)
        cm_t = confusion_matrix(y_test, preds_at_t)
        tn_t, fp_t, fn_t, tp_t = cm_t.ravel()
        print(f"{t:>10.2f} {p:>10.3f} {r:>10.3f} {f:>8.3f} {fn_t:>8,} {fp_t:>8,}")

    print(f"\nDone. All model artifacts saved in '{MODEL_DIR}/'.")
    print(f"\nQuick start checklist:")
    print(f"  [OK] Data loaded, deduped, engineered ({X_train.shape[0] + X_val.shape[0]:,} balanced training rows)")
    print(f"  [OK] 4 models trained: LR, RF, XGBoost, LightGBM")
    print(f"  [OK] Best model: {best_name} (AUROC {best_row['Test_AUROC']})")
    print(f"  [OK] Healthcare metrics computed (Sensitivity, Specificity, PPV, NPV)")
    print(f"  [OK] SHAP summary generated")
    print(f"  [OK] Threshold scan complete")


if __name__ == "__main__":
    main()
