import os
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    brier_score_loss,
    balanced_accuracy_score,
    confusion_matrix,
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    roc_curve,
    precision_recall_curve
)
from sklearn.calibration import calibration_curve

def find_optimal_threshold(y_true: np.ndarray, y_probs: np.ndarray) -> Tuple[float, float]:
    """Find classification probability threshold that maximizes F1 score."""
    thresholds = np.linspace(0.01, 0.99, 100)
    best_thresh = 0.5
    best_f1 = 0.0
    
    for t in thresholds:
        preds = (y_probs >= t).astype(int)
        if np.sum(preds) == 0:
            continue
        score = f1_score(y_true, preds, zero_division=0)
        if score > best_f1:
            best_f1 = score
            best_thresh = float(t)
            
    return best_thresh, best_f1


def evaluate_binary_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray,
    threshold: float = 0.5
) -> Dict[str, Any]:
    """Calculate comprehensive classification metrics."""
    if hasattr(model, "predict_proba"):
        y_prob = model.predict_proba(X)[:, 1]
    else:
        # Decision function fallback
        df_vals = model.decision_function(X)
        y_prob = 1.0 / (1.0 + np.exp(-df_vals))
        
    y_pred = (y_prob >= threshold).astype(int)
    
    # Metrics
    roc_auc = float(roc_auc_score(y, y_prob)) if len(np.unique(y)) > 1 else np.nan
    pr_auc = float(average_precision_score(y, y_prob)) if len(np.unique(y)) > 1 else np.nan
    f1 = float(f1_score(y, y_pred, zero_division=0))
    prec = float(precision_score(y, y_pred, zero_division=0))
    rec = float(recall_score(y, y_pred, zero_division=0))
    brier = float(brier_score_loss(y, y_prob))
    bal_acc = float(balanced_accuracy_score(y, y_pred)) if len(np.unique(y)) > 1 else np.nan
    
    cm = confusion_matrix(y, y_pred).tolist()
    
    return {
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "f1": f1,
        "precision": prec,
        "recall": rec,
        "brier_score": brier,
        "balanced_accuracy": bal_acc,
        "threshold": threshold,
        "confusion_matrix": cm,
        "y_prob": y_prob
    }


def evaluate_regressor_model(
    model: Any,
    X: np.ndarray,
    y: np.ndarray
) -> Dict[str, float]:
    """Calculate regression metrics for readiness prediction."""
    valid_mask = ~np.isnan(y)
    X_v = X[valid_mask]
    y_v = y[valid_mask]
    
    preds = model.predict(X_v)
    
    rmse = float(np.sqrt(mean_squared_error(y_v, preds)))
    mae = float(mean_absolute_error(y_v, preds))
    r2 = float(r2_score(y_v, preds))
    
    return {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "predictions": preds
    }


def run_model_comparison(pipeline_artifacts: Dict[str, Any]) -> pd.DataFrame:
    """Evaluate all trained models across Validation and Test partitions."""
    models = pipeline_artifacts["models"]
    
    X_val = pipeline_artifacts["X_val"]
    X_val_scaled = pipeline_artifacts["X_val_scaled"]
    y_val = pipeline_artifacts["y_val"]
    
    X_test = pipeline_artifacts["X_test"]
    X_test_scaled = pipeline_artifacts["X_test_scaled"]
    y_test = pipeline_artifacts["y_test"]
    
    records = []
    
    print("\n" + "="*70)
    print("MODEL PERFORMANCE COMPARISON (Temporal Validation & Test Splits)")
    print("="*70)
    
    for name, model in models.items():
        is_linear = "Logistic" in name
        val_X = X_val_scaled if is_linear else X_val
        test_X = X_test_scaled if is_linear else X_test
        
        # 1. Validation evaluation & threshold optimization
        val_probs = model.predict_proba(val_X)[:, 1]
        best_thresh, _ = find_optimal_threshold(y_val, val_probs)
        
        val_metrics = evaluate_binary_model(model, val_X, y_val, threshold=best_thresh)
        
        # 2. Test evaluation using threshold determined on validation set
        test_metrics = evaluate_binary_model(model, test_X, y_test, threshold=best_thresh)
        
        records.append({
            "model": name,
            "split": "Validation",
            "pr_auc": val_metrics["pr_auc"],
            "roc_auc": val_metrics["roc_auc"],
            "f1": val_metrics["f1"],
            "recall": val_metrics["recall"],
            "precision": val_metrics["precision"],
            "brier_score": val_metrics["brier_score"],
            "optimal_threshold": best_thresh
        })
        
        records.append({
            "model": name,
            "split": "Test",
            "pr_auc": test_metrics["pr_auc"],
            "roc_auc": test_metrics["roc_auc"],
            "f1": test_metrics["f1"],
            "recall": test_metrics["recall"],
            "precision": test_metrics["precision"],
            "brier_score": test_metrics["brier_score"],
            "optimal_threshold": best_thresh
        })
        
        print(f"\nModel: {name}")
        print(f"  [Validation] PR-AUC: {val_metrics['pr_auc']:.4f} | ROC-AUC: {val_metrics['roc_auc']:.4f} | Recall: {val_metrics['recall']:.3f} | Prec: {val_metrics['precision']:.3f} | F1: {val_metrics['f1']:.3f}")
        print(f"  [Test]       PR-AUC: {test_metrics['pr_auc']:.4f} | ROC-AUC: {test_metrics['roc_auc']:.4f} | Recall: {test_metrics['recall']:.3f} | Prec: {test_metrics['precision']:.3f} | F1: {test_metrics['f1']:.3f}")
        
    res_df = pd.DataFrame(records)
    os.makedirs("results/metrics", exist_ok=True)
    res_df.to_csv("results/metrics/model_comparison.csv", index=False)
    print("\nSaved model comparison table to results/metrics/model_comparison.csv.")
    
    return res_df


if __name__ == "__main__":
    from src.train import run_full_training_pipeline
    artifacts = run_full_training_pipeline()
    run_model_comparison(artifacts)
