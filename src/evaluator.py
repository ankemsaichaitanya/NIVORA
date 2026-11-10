"""
Cross-Validation & Evaluation Engine for CKD Classification.
Executes Stratified 10-Fold Cross-Validation, calculates comprehensive clinical metrics
(Accuracy, Sensitivity, Specificity, Precision, F1, ROC-AUC, PR-AUC, Brier Score),
and exports publication-grade benchmark tables and visualization plots.
"""

import logging
from typing import Dict, List, Tuple, Any, Optional, Union
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # Headless backend for robust plot generation
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    roc_curve,
    precision_recall_curve,
    auc,
)
from sklearn.base import clone

from src.config import (
    CV_FOLDS,
    RANDOM_STATE,
    PLOTS_DIR,
    REPORTS_DIR,
    MODEL_CONFIGS,
)

logger = logging.getLogger(__name__)


def compute_clinical_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_prob: np.ndarray,
) -> Dict[str, float]:
    """
    Computes all standard clinical validation metrics.
    Sensitivity (Recall) and Specificity are critical for renal diagnostics.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()

    accuracy = accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred, zero_division=0)
    sensitivity = recall_score(y_true, y_pred, zero_division=0)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    try:
        roc_auc = roc_auc_score(y_true, y_prob)
    except ValueError:
        roc_auc = 0.5
        
    try:
        pr_auc = average_precision_score(y_true, y_prob)
    except ValueError:
        pr_auc = 0.0

    brier = brier_score_loss(y_true, y_prob)

    return {
        "accuracy": float(accuracy),
        "sensitivity": float(sensitivity),
        "specificity": float(specificity),
        "precision": float(precision),
        "f1_score": float(f1),
        "roc_auc": float(roc_auc),
        "pr_auc": float(pr_auc),
        "brier_score": float(brier),
        "tp": int(tp),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
    }


def evaluate_model_cv(
    model: Any,
    X: Union[pd.DataFrame, np.ndarray],
    y: Union[pd.Series, np.ndarray],
    n_splits: int = CV_FOLDS,
    random_state: int = RANDOM_STATE,
) -> Dict[str, Any]:
    """
    Executes Stratified 10-Fold Cross-Validation on a model.
    Records fold-by-fold metrics, out-of-fold probabilities, and overall summary statistics.
    """
    X_mat = X.values if isinstance(X, pd.DataFrame) else np.array(X)
    y_vec = y.values if isinstance(y, pd.Series) else np.array(y)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    
    fold_metrics: List[Dict[str, float]] = []
    oof_predictions = np.zeros(len(y_vec), dtype=int)
    oof_probabilities = np.zeros(len(y_vec), dtype=float)

    tprs = []
    base_fpr = np.linspace(0, 1, 101)

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(X_mat, y_vec)):
        X_train, y_train = X_mat[train_idx], y_vec[train_idx]
        X_val, y_val = X_mat[val_idx], y_vec[val_idx]

        # Clone estimator for fresh fold training
        fold_model = clone(model)
        fold_model.fit(X_train, y_train)

        # Predict classes and positive class probabilities
        val_pred = fold_model.predict(X_val)
        if hasattr(fold_model, "predict_proba"):
            val_prob = fold_model.predict_proba(X_val)[:, 1]
        elif hasattr(fold_model, "decision_function"):
            raw_scores = fold_model.decision_function(X_val)
            val_prob = 1.0 / (1.0 + np.exp(-raw_scores))
        else:
            val_prob = val_pred.astype(float)

        oof_predictions[val_idx] = val_pred
        oof_probabilities[val_idx] = val_prob

        metrics = compute_clinical_metrics(y_val, val_pred, val_prob)
        fold_metrics.append(metrics)

        # ROC interpolation
        fpr, tpr, _ = roc_curve(y_val, val_prob)
        tpr_interp = np.interp(base_fpr, fpr, tpr)
        tpr_interp[0] = 0.0
        tprs.append(tpr_interp)

    # Aggregate metric summaries (mean & std)
    df_folds = pd.DataFrame(fold_metrics)
    summary_mean = df_folds.mean().to_dict()
    summary_std = df_folds.std().to_dict()

    return {
        "fold_metrics": df_folds,
        "mean_metrics": summary_mean,
        "std_metrics": summary_std,
        "oof_predictions": oof_predictions,
        "oof_probabilities": oof_probabilities,
        "base_fpr": base_fpr,
        "tprs": tprs,
    }


def benchmark_all_models(
    models_dict: Dict[str, Any],
    X: pd.DataFrame,
    y: pd.Series,
    mode_name: str = "MODE_A",
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Evaluates all candidate models across Stratified 10-Fold CV.
    Returns structured benchmark comparison DataFrame and detailed results.
    """
    logger.info(f"Running Stratified 10-Fold CV Benchmarking for {mode_name} ({len(models_dict)} models)...")
    results = {}
    table_rows = []

    for name, model in models_dict.items():
        logger.info(f"  -> Cross-validating: {name}")
        cv_res = evaluate_model_cv(model, X, y)
        results[name] = cv_res

        m = cv_res["mean_metrics"]
        s = cv_res["std_metrics"]

        table_rows.append({
            "Model": name,
            "Mode": mode_name,
            "Accuracy": f"{m['accuracy']:.4f} ± {s['accuracy']:.4f}",
            "Sensitivity": f"{m['sensitivity']:.4f} ± {s['sensitivity']:.4f}",
            "Specificity": f"{m['specificity']:.4f} ± {s['specificity']:.4f}",
            "Precision": f"{m['precision']:.4f} ± {s['precision']:.4f}",
            "F1-Score": f"{m['f1_score']:.4f} ± {s['f1_score']:.4f}",
            "ROC-AUC": f"{m['roc_auc']:.4f} ± {s['roc_auc']:.4f}",
            "PR-AUC": f"{m['pr_auc']:.4f} ± {s['pr_auc']:.4f}",
            "Brier Score": f"{m['brier_score']:.4f} ± {s['brier_score']:.4f}",
            # Raw numerical means for plotting
            "raw_acc": m["accuracy"],
            "raw_sens": m["sensitivity"],
            "raw_spec": m["specificity"],
            "raw_f1": m["f1_score"],
            "raw_auc": m["roc_auc"],
        })

    df_benchmark = pd.DataFrame(table_rows)
    
    # Save benchmark report to CSV
    csv_path = REPORTS_DIR / f"benchmark_summary_{mode_name.lower()}.csv"
    df_benchmark.to_csv(csv_path, index=False)
    logger.info(f"Benchmark summary saved to: {csv_path}")

    return df_benchmark, results


def plot_roc_curves_comparison(
    results_dict: Dict[str, Any],
    y_true: pd.Series,
    mode_name: str = "MODE_A",
    save_path: Optional[Path] = None,
) -> Path:
    """
    Generates high-resolution ROC curve comparison across models.
    """
    if save_path is None:
        save_path = PLOTS_DIR / f"roc_curves_{mode_name.lower()}.png"

    plt.figure(figsize=(9, 7), dpi=300)
    plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")

    colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b"]
    
    for idx, (name, cv_res) in enumerate(results_dict.items()):
        oof_probs = cv_res["oof_probabilities"]
        fpr, tpr, _ = roc_curve(y_true, oof_probs)
        roc_auc = auc(fpr, tpr)
        
        is_champ = MODEL_CONFIGS.get(name, {}).get("is_champion", False)
        lw = 2.5 if is_champ else 1.5
        label_prefix = "[CHAMPION] " if is_champ else ""
        plt.plot(
            fpr,
            tpr,
            color=colors[idx % len(colors)],
            lw=lw,
            label=f"{label_prefix}{name.replace('_', ' ').title()} (AUC = {roc_auc:.4f})",
        )

    plt.plot([0, 1], [0, 1], "k--", lw=1.2, label="Random Chance (AUC = 0.5000)")
    plt.xlim([-0.02, 1.02])
    plt.ylim([-0.02, 1.02])
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=12, fontweight="bold")
    plt.ylabel("True Positive Rate (Sensitivity / Recall)", fontsize=12, fontweight="bold")
    plt.title(f"ROC Curves - Stratified 10-Fold CV ({mode_name})", fontsize=14, fontweight="bold", pad=12)
    plt.legend(loc="lower right", fontsize=10, frameon=True)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

    logger.info(f"ROC curves comparison saved to: {save_path}")
    return save_path


def plot_metrics_comparison_barchart(
    df_benchmark: pd.DataFrame,
    mode_name: str = "MODE_A",
    save_path: Optional[Path] = None,
) -> Path:
    """
    Plots multi-metric grouped bar chart comparing all models.
    """
    if save_path is None:
        save_path = PLOTS_DIR / f"metrics_barchart_{mode_name.lower()}.png"

    plot_df = df_benchmark[["Model", "raw_acc", "raw_sens", "raw_spec", "raw_f1", "raw_auc"]].copy()
    plot_df.columns = ["Model", "Accuracy", "Sensitivity", "Specificity", "F1-Score", "ROC-AUC"]
    plot_df["Model"] = plot_df["Model"].str.replace("_", " ").str.title()
    
    melted_df = plot_df.melt(id_vars=["Model"], var_name="Metric", value_name="Score")

    plt.figure(figsize=(11, 6), dpi=300)
    sns.set_theme(style="whitegrid")
    
    palette = sns.color_palette("muted")
    ax = sns.barplot(
        data=melted_df,
        x="Model",
        y="Score",
        hue="Metric",
        palette=palette,
    )

    plt.title(f"Clinical Performance Benchmarking across Models ({mode_name})", fontsize=13, fontweight="bold", pad=12)
    plt.xlabel("Classification Algorithm", fontsize=11, fontweight="bold")
    plt.ylabel("Cross-Validation Score", fontsize=11, fontweight="bold")
    plt.ylim([0.80, 1.02])  # Highlighting upper performance tiers
    plt.legend(loc="lower right", frameon=True)
    plt.xticks(rotation=15, ha="right")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

    logger.info(f"Metrics barchart saved to: {save_path}")
    return save_path


def plot_confusion_matrix_heatmap(
    y_true: pd.Series,
    y_pred: np.ndarray,
    model_name: str = "Random Forest",
    mode_name: str = "MODE_A",
    save_path: Optional[Path] = None,
) -> Path:
    """
    Generates clinical confusion matrix with sensitivity, specificity, and misclassification counts.
    """
    if save_path is None:
        save_path = PLOTS_DIR / f"confusion_matrix_{model_name.lower().replace(' ', '_')}_{mode_name.lower()}.png"

    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    
    plt.figure(figsize=(6, 5), dpi=300)
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        cbar=False,
        xticklabels=["Not-CKD (0)", "CKD (1)"],
        yticklabels=["Not-CKD (0)", "CKD (1)"],
        annot_kws={"size": 14, "fontweight": "bold"},
    )
    plt.title(f"Confusion Matrix: {model_name} ({mode_name})\nStratified 10-Fold CV Pooled", fontsize=12, fontweight="bold")
    plt.xlabel("Predicted Clinical Label", fontsize=11, fontweight="bold")
    plt.ylabel("Actual Clinical Diagnosis", fontsize=11, fontweight="bold")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()

    logger.info(f"Confusion matrix saved to: {save_path}")
    return save_path
