"""
Data Preprocessing Pipeline for Chronic Kidney Disease.
Integrates cleaning, Clinical Regression Imputation, Feature Mode selection (Mode A vs Mode B),
Feature Scaling, and SMOTE Class Balancing.
"""

import logging
from typing import Tuple, List, Optional, Union, Dict, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE

from src.config import (
    FEATURE_MODES,
    MODE_A_FEATURES,
    MODE_B_FEATURES,
    ALL_INPUT_FEATURES,
    RANDOM_STATE,
    SMOTE_TARGET_SAMPLES,
    IMPUTED_DATA_FILE,
    BALANCED_DATA_FILE,
    TARGET_COL,
)
from src.data_loader import get_ckd_data
from src.imputer import ClinicalRegressionImputer

logger = logging.getLogger(__name__)


class CKDPreprocessor(BaseEstimator, TransformerMixin):
    """
    End-to-End Clinical Feature Preprocessing Pipeline.
    
    Parameters:
        mode: Feature set mode ('MODE_A', 'MODE_B', or 'FULL').
        scale_features: Whether to scale features using StandardScaler.
        impute_strategy: Clinical regression imputation on all features before subsetting,
                         leveraging all biomarker correlations for maximum precision.
    """

    def __init__(
        self,
        mode: str = "MODE_A",
        scale_features: bool = False,
        random_state: int = RANDOM_STATE,
    ):
        self.mode = mode.upper()
        if self.mode not in FEATURE_MODES:
            raise ValueError(f"Unknown mode '{mode}'. Choose from {list(FEATURE_MODES.keys())}")
        self.selected_features = FEATURE_MODES[self.mode]
        self.scale_features = scale_features
        self.random_state = random_state

        self.imputer = ClinicalRegressionImputer(random_state=self.random_state)
        self.scaler: Optional[StandardScaler] = StandardScaler() if scale_features else None
        self.fitted_ = False

    def fit(self, X: pd.DataFrame, y=None):
        """
        Fits imputer (and scaler if enabled) on the training dataset.
        """
        X_df = X.copy()
        
        # Fit imputer on available input features
        self.imputer.fit(X_df)
        X_imp = self.imputer.transform(X_df)

        # Subset features
        X_sub = X_imp[self.selected_features]

        # Fit scaler if requested
        if self.scale_features and self.scaler is not None:
            self.scaler.fit(X_sub)

        self.fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Imputes, selects features according to Mode, and optionally scales.
        """
        if not self.fitted_:
            raise RuntimeError("CKDPreprocessor must be fitted before transform.")

        X_df = X.copy()
        
        # If the input already contains only the subset features, handle gracefully
        if all(f in X_df.columns for f in self.selected_features) and not all(f in X_df.columns for f in ALL_INPUT_FEATURES):
            # Impute directly on subset
            sub_imputer = ClinicalRegressionImputer(random_state=self.random_state)
            sub_imputer.fit(X_df[self.selected_features])
            X_sub = sub_imputer.transform(X_df[self.selected_features])
        else:
            # Impute across full features to maximize covariance fidelity
            X_imp = self.imputer.transform(X_df)
            X_sub = X_imp[self.selected_features]

        if self.scale_features and self.scaler is not None:
            scaled_array = self.scaler.transform(X_sub)
            return pd.DataFrame(scaled_array, columns=self.selected_features, index=X_df.index)

        return X_sub


def balance_classes_smote(
    X: pd.DataFrame,
    y: pd.Series,
    target_total: int = SMOTE_TARGET_SAMPLES,
    random_state: int = RANDOM_STATE,
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Applies Synthetic Minority Over-sampling Technique (SMOTE) to balance
    the target classes to target_total instances (250 CKD / 250 Not-CKD).
    
    Args:
        X: Feature DataFrame.
        y: Target Series (binary 0/1).
        target_total: Desired total samples after balancing (default: 500).
        random_state: Random state for deterministic reproduction.
        
    Returns:
        X_resampled (pd.DataFrame): Balanced features (500 rows).
        y_resampled (pd.Series): Balanced targets (250 CKD / 250 Not-CKD).
    """
    feature_names = list(X.columns)
    counts = y.value_counts().to_dict()
    majority_count = max(counts.values())  # 250 for CKD
    
    # SMOTE with sampling_strategy='auto' balances minority class to equal majority class
    smote = SMOTE(
        sampling_strategy="auto",
        random_state=random_state,
        k_neighbors=5,
    )
    X_res, y_res = smote.fit_resample(X.values, y.values)
    
    X_resampled = pd.DataFrame(X_res, columns=feature_names)
    y_resampled = pd.Series(y_res, name=TARGET_COL)
    
    logger.info(
        f"SMOTE balancing applied: Before={counts} (total {len(y)}), "
        f"After={y_resampled.value_counts().to_dict()} (total {len(y_resampled)})"
    )
    return X_resampled, y_resampled


def prepare_dataset(
    mode: str = "MODE_A",
    apply_smote: bool = True,
    scale_features: bool = False,
    force_download: bool = False,
) -> Tuple[pd.DataFrame, pd.Series, CKDPreprocessor]:
    """
    High-level factory function that loads, cleans, imputes, subsets,
    and optionally balances the CKD dataset.
    
    Returns:
        X_final: Processed features DataFrame.
        y_final: Processed target Series.
        preprocessor: Fitted CKDPreprocessor instance.
    """
    X_raw, y_raw, df_clean = get_ckd_data(force_download=force_download)

    # Fit preprocessor
    preprocessor = CKDPreprocessor(
        mode=mode,
        scale_features=scale_features,
        random_state=RANDOM_STATE,
    )
    preprocessor.fit(X_raw, y_raw)
    X_processed = preprocessor.transform(X_raw)

    # Persist imputed dataset snapshot
    df_imputed = X_processed.copy()
    df_imputed[TARGET_COL] = y_raw.values
    df_imputed.to_csv(IMPUTED_DATA_FILE, index=False)

    if apply_smote:
        X_final, y_final = balance_classes_smote(
            X_processed,
            y_raw,
            target_total=SMOTE_TARGET_SAMPLES,
            random_state=RANDOM_STATE,
        )
        # Persist SMOTE balanced dataset snapshot
        df_balanced = X_final.copy()
        df_balanced[TARGET_COL] = y_final.values
        df_balanced.to_csv(BALANCED_DATA_FILE, index=False)
    else:
        X_final, y_final = X_processed, y_raw

    return X_final, y_final, preprocessor


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print("Testing Preprocessing in Mode A (Jawad et al. 6-Feature Set):")
    X_A, y_A, prep_A = prepare_dataset(mode="MODE_A", apply_smote=True)
    print(f"Mode A shape: {X_A.shape}, target counts: {y_A.value_counts().to_dict()}")
    print("Mode A Head:")
    print(X_A.head())

    print("\nTesting Preprocessing in Mode B (Moreno-Sánchez 3-Feature Set):")
    X_B, y_B, prep_B = prepare_dataset(mode="MODE_B", apply_smote=True)
    print(f"Mode B shape: {X_B.shape}, target counts: {y_B.value_counts().to_dict()}")
    print("Mode B Head:")
    print(X_B.head())

