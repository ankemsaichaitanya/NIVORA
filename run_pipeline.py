"""
End-to-End Clinical Machine Learning & Explainable AI Pipeline for CKD Prediction.
Orchestrates data ingestion, cleaning, clinical regression imputation, SMOTE balancing,
Stratified 10-Fold Cross-Validation, publication plotting, SHAP XAI interpretation,
and artifact serialization.

Authors: Principal ML Engineer & Healthcare AI Researcher
Reference Literature:
  - Jawad et al. (2024): Comprehensive Clinical 6-Feature Set ('hemo', 'sc', 'al', 'htn', 'age', 'dm')
  - Moreno-Sánchez (2023): Ultra-Lean 3-Feature Set ('hemo', 'sg', 'htn')
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd
import numpy as np

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    FEATURE_MODES,
    MODE_A_FEATURES,
    MODE_B_FEATURES,
    MODEL_CONFIGS,
    RANDOM_STATE,
    REPORTS_DIR,
    PLOTS_DIR,
    MODELS_DIR,
)
from src.data_loader import get_ckd_data
from src.preprocessor import prepare_dataset, CKDPreprocessor, balance_classes_smote
from src.models import create_model, get_all_models, get_champion_models
from src.evaluator import (
    benchmark_all_models,
    plot_roc_curves_comparison,
    plot_metrics_comparison_barchart,
    plot_confusion_matrix_heatmap,
)
from src.xai import ClinicalXAIExplainer
from src.inference import CKDPredictor

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CKD_Pipeline")


def run_experiment_for_mode(
    mode_name: str,
    champion_only: bool = False,
    apply_smote: bool = True,
    export_artifacts: bool = True,
) -> Dict[str, Any]:
    """
    Executes the complete experimental pipeline for a specified clinical feature mode.
    """
    print("\n" + "=" * 80)
    print(f"  RUNNING CLINICAL CKD PIPELINE: {mode_name}")
    features = FEATURE_MODES[mode_name]
    print(f"  Feature Subset ({len(features)} attributes): {features}")
    print("=" * 80)

    # 1. Load, clean, impute, and balance dataset
    logger.info("Step 1 & 2: Loading dataset and applying Clinical Regression Imputation...")
    X_balanced, y_balanced, preprocessor = prepare_dataset(
        mode=mode_name,
        apply_smote=apply_smote,
        scale_features=False,
    )
    print(f"\n[+] Dataset Prepared: {len(X_balanced)} samples ({y_balanced.value_counts().to_dict()})")

    # 2. Select models
    if champion_only:
        models = get_champion_models()
        logger.info(f"Evaluating Primary Champion Models ({list(models.keys())})...")
    else:
        models = get_all_models()
        logger.info(f"Evaluating All Champion & Benchmark Comparison Models ({list(models.keys())})...")

    # 3. Stratified 10-Fold Cross-Validation
    logger.info("Step 3: Executing Stratified 10-Fold Cross-Validation across all folds...")
    df_benchmark, cv_results = benchmark_all_models(
        models_dict=models,
        X=X_balanced,
        y=y_balanced,
        mode_name=mode_name,
    )

    # Print clean benchmark summary table
    print("\n" + "-" * 80)
    print(f"STRATIFIED 10-FOLD CV RESULTS ({mode_name}):")
    print("-" * 80)
    display_cols = ["Model", "Accuracy", "Sensitivity", "Specificity", "Precision", "F1-Score", "ROC-AUC", "Brier Score"]
    print(df_benchmark[display_cols].to_string(index=False))
    print("-" * 80)

    # 4. Generate comparison plots
    if export_artifacts:
        logger.info("Step 4: Generating publication-grade evaluation curves and charts...")
        roc_plot_path = plot_roc_curves_comparison(cv_results, y_balanced, mode_name=mode_name)
        bar_plot_path = plot_metrics_comparison_barchart(df_benchmark, mode_name=mode_name)
        
        # Plot confusion matrix for Champion Random Forest
        rf_oof_preds = cv_results["random_forest"]["oof_predictions"]
        cm_plot_path = plot_confusion_matrix_heatmap(
            y_true=y_balanced,
            y_pred=rf_oof_preds,
            model_name="Random Forest",
            mode_name=mode_name,
        )

    # 5. Train Production Champion Models on full balanced dataset & SHAP XAI
    logger.info("Step 5: Fitting production champion models and fitting SHAP TreeExplainers...")
    champion_rf = create_model("random_forest")
    champion_rf.fit(X_balanced, y_balanced)

    champion_xgb = create_model("xgboost")
    champion_xgb.fit(X_balanced, y_balanced)

    if export_artifacts:
        logger.info("Step 6: Generating SHAP Beeswarm and Global Bar Plots...")
        xai_rf = ClinicalXAIExplainer(champion_rf, feature_names=features, model_name="Random Forest")
        xai_rf.plot_summary_beeswarm(X_balanced, mode_name=mode_name)
        xai_rf.plot_feature_importance_bar(X_balanced, mode_name=mode_name)

        xai_xgb = ClinicalXAIExplainer(champion_xgb, feature_names=features, model_name="XGBoost")
        xai_xgb.plot_summary_beeswarm(X_balanced, mode_name=mode_name)
        xai_xgb.plot_feature_importance_bar(X_balanced, mode_name=mode_name)

        # 6. Persist inference artifacts
        logger.info("Step 7: Serializing champion models and preprocessor for production deployment...")
        pred_service_rf = CKDPredictor(champion_rf, preprocessor, mode=mode_name, model_name="Random Forest")
        pred_service_rf.save_to_artifacts()

        pred_service_xgb = CKDPredictor(champion_xgb, preprocessor, mode=mode_name, model_name="XGBoost")
        pred_service_xgb.save_to_artifacts()

    print(f"\n[OK] Pipeline for {mode_name} completed successfully!")
    return {
        "mode": mode_name,
        "benchmark_table": df_benchmark,
        "cv_results": cv_results,
        "champion_rf": champion_rf,
        "champion_xgb": champion_xgb,
        "preprocessor": preprocessor,
    }


def main():
    parser = argparse.ArgumentParser(description="Production CKD Machine Learning & XAI Pipeline")
    parser.add_argument(
        "--mode",
        type=str,
        default="all",
        choices=["A", "B", "MODE_A", "MODE_B", "all"],
        help="Feature selection subset: 'A' (Jawad et al. 6 features), 'B' (Moreno-Sánchez 3 features), or 'all'",
    )
    parser.add_argument(
        "--champion-only",
        action="store_true",
        help="Evaluate only champion models (Random Forest & XGBoost) instead of full 6-model benchmark suite",
    )
    parser.add_argument(
        "--no-smote",
        action="store_true",
        help="Disable SMOTE balancing (evaluate on raw 400 instances)",
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Do not save plots and model artifacts to disk",
    )

    args = parser.parse_args()

    modes_to_run = []
    if args.mode.lower() in ["a", "mode_a"]:
        modes_to_run = ["MODE_A"]
    elif args.mode.lower() in ["b", "mode_b"]:
        modes_to_run = ["MODE_B"]
    else:
        modes_to_run = ["MODE_A", "MODE_B"]

    all_results = {}
    for m in modes_to_run:
        res = run_experiment_for_mode(
            mode_name=m,
            champion_only=args.champion_only,
            apply_smote=not args.no_smote,
            export_artifacts=not args.no_export,
        )
        all_results[m] = res

    # Print final comparative overview
    print("\n" + "=" * 90)
    print("FINAL SUMMARY: COMPARATIVE CLINICAL ARCHITECTURES")
    print("=" * 90)
    for m in modes_to_run:
        df = all_results[m]["benchmark_table"]
        rf_row = df[df["Model"] == "random_forest"].iloc[0]
        xgb_row = df[df["Model"] == "xgboost"].iloc[0]
        print(f"\nConfiguration: {m} ({len(FEATURE_MODES[m])} Features: {FEATURE_MODES[m]})")
        print(f"  Champion 1 (Random Forest): Accuracy = {rf_row['Accuracy']} | F1 = {rf_row['F1-Score']} | ROC-AUC = {rf_row['ROC-AUC']}")
        print(f"  Champion 2 (XGBoost):       Accuracy = {xgb_row['Accuracy']} | F1 = {xgb_row['F1-Score']} | ROC-AUC = {xgb_row['ROC-AUC']}")
    print("\n" + "=" * 90)
    print(f"All artifacts, reports, and plots saved to: {PROJECT_ROOT / 'artifacts'}")
    print("=" * 90)


if __name__ == "__main__":
    main()

