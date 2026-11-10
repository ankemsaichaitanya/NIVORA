"""
Unit and Integration Test Suite for the CKD ML & XAI Pipeline.
Tests data cleaning, clinical regression imputation, SMOTE balancing,
feature modes, model architectures, eGFR calculations, and inference.
"""

import unittest
import sys
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import (
    MODE_A_FEATURES,
    MODE_B_FEATURES,
    ALL_INPUT_FEATURES,
    TARGET_COL,
)
from src.data_loader import get_ckd_data, clean_ckd_dataframe
from src.imputer import ClinicalRegressionImputer
from src.preprocessor import CKDPreprocessor, balance_classes_smote
from src.models import create_model, get_all_models
from src.clinical_engine import (
    calculate_ckd_epi_2021_egfr,
    determine_kdigo_stage,
    determine_albuminuria_stage,
)
from src.evaluator import compute_clinical_metrics


class TestCKDPipeline(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Load cleaned data once for suite
        cls.X_raw, cls.y_raw, cls.df_clean = get_ckd_data()

    def test_01_dataset_dimensions_and_target_balance(self):
        """Validates UCI CKD dataset integrity and anomaly sanitation."""
        self.assertEqual(len(self.df_clean), 400, "Dataset must contain exactly 400 samples.")
        self.assertEqual(self.X_raw.shape[1], 24, "Input feature space must be 24 attributes.")
        
        # Verify target mapping
        counts = self.y_raw.value_counts().to_dict()
        self.assertEqual(counts[1], 250, "CKD positive class count must be 250.")
        self.assertEqual(counts[0], 150, "Not-CKD negative class count must be 150.")
        self.assertEqual(self.y_raw.isna().sum(), 0, "No NaNs allowed in target variable.")

    def test_02_clinical_regression_imputer(self):
        """Tests that iterative linear regression imputer eliminates all NaNs and preserves bounds."""
        imputer = ClinicalRegressionImputer(max_iter=10)
        imputer.fit(self.X_raw)
        X_imp = imputer.transform(self.X_raw)

        # Zero missing values
        self.assertEqual(X_imp.isna().sum().sum(), 0, "All missing values must be imputed.")
        
        # Physiological boundaries
        self.assertTrue((X_imp["hemo"] >= 3.0).all() and (X_imp["hemo"] <= 20.0).all())
        self.assertTrue((X_imp["sc"] >= 0.1).all())
        self.assertTrue((X_imp["age"] >= 1.0).all())

    def test_03_smote_balancing_to_500_instances(self):
        """Tests SMOTE balancing to exact 500 total instances (250 CKD / 250 Not-CKD)."""
        imputer = ClinicalRegressionImputer(max_iter=5)
        X_imp = imputer.fit_transform(self.X_raw)
        
        X_bal, y_bal = balance_classes_smote(X_imp, self.y_raw, target_total=500)
        self.assertEqual(len(X_bal), 500, "Total balanced instances must be 500.")
        self.assertEqual(len(y_bal), 500)
        counts = y_bal.value_counts().to_dict()
        self.assertEqual(counts[1], 250, "Balanced CKD count must be 250.")
        self.assertEqual(counts[0], 250, "Balanced Not-CKD count must be 250.")

    def test_04_feature_selection_modes(self):
        """Verifies Mode A (6 features) and Mode B (3 features) subsets."""
        prep_a = CKDPreprocessor(mode="MODE_A")
        prep_a.fit(self.X_raw)
        X_a = prep_a.transform(self.X_raw)
        self.assertEqual(list(X_a.columns), MODE_A_FEATURES)
        self.assertEqual(X_a.shape[1], 6)

        prep_b = CKDPreprocessor(mode="MODE_B")
        prep_b.fit(self.X_raw)
        X_b = prep_b.transform(self.X_raw)
        self.assertEqual(list(X_b.columns), MODE_B_FEATURES)
        self.assertEqual(X_b.shape[1], 3)

    def test_05_model_hyperparameters(self):
        """Validates clinical model configurations and hyperparameter settings."""
        rf = create_model("random_forest")
        self.assertEqual(rf.n_estimators, 472)
        self.assertEqual(rf.max_depth, 14)
        self.assertEqual(rf.class_weight, "balanced")

        xgb = create_model("xgboost")
        self.assertEqual(xgb.n_estimators, 300)
        self.assertEqual(xgb.max_depth, 4)
        self.assertAlmostEqual(xgb.learning_rate, 0.05)

        all_models = get_all_models()
        self.assertEqual(len(all_models), 6, "Must configure all 6 models.")

    def test_06_ckd_epi_2021_egfr_equation(self):
        """Verifies 2021 race-free CKD-EPI eGFR calculation against clinical nephrology benchmarks."""
        # Male, age 50, creatinine 1.0 mg/dL
        egfr_m = calculate_ckd_epi_2021_egfr(serum_creatinine=1.0, age=50, gender="male")
        self.assertGreaterEqual(egfr_m, 90.0)
        stage_m = determine_kdigo_stage(egfr_m)
        self.assertEqual(stage_m["stage_code"], "G1")

        # Female, age 65, creatinine 2.4 mg/dL (Severely impaired)
        egfr_f = calculate_ckd_epi_2021_egfr(serum_creatinine=2.4, age=65, gender="female")
        self.assertLess(egfr_f, 30.0)
        stage_f = determine_kdigo_stage(egfr_f)
        self.assertIn(stage_f["stage_code"], ["G4", "G5"])

    def test_07_clinical_metrics_computation(self):
        """Verifies mathematical validity of clinical performance metrics."""
        y_true = np.array([1, 1, 1, 0, 0, 0])
        y_pred = np.array([1, 1, 0, 0, 0, 1])
        y_prob = np.array([0.9, 0.8, 0.4, 0.1, 0.2, 0.7])

        m = compute_clinical_metrics(y_true, y_pred, y_prob)
        self.assertAlmostEqual(m["accuracy"], 4 / 6)
        self.assertAlmostEqual(m["sensitivity"], 2 / 3)
        self.assertAlmostEqual(m["specificity"], 2 / 3)
        self.assertGreater(m["roc_auc"], 0.7)


if __name__ == "__main__":
    unittest.main()
