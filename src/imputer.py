"""
Clinical Regression Imputation Engine.
Implements the clinical regression strategy:
  1. Identifies complete observed pairs and multivariable relationships.
  2. Imputes continuous and ordinal clinical variables using an Iterative Linear Regression Imputer (MICE).
  3. Imputes nominal/categorical variables using the empirical mode.
  4. Enforces physiological boundary constraints to preserve clinical validity.
  5. Implements a scikit-learn compatible BaseEstimator / TransformerMixin avoiding data leakage.
"""

import logging
from typing import List, Dict, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, SimpleImputer
from sklearn.linear_model import LinearRegression

from src.config import (
    NUMERICAL_FEATURES,
    ORDINAL_FEATURES,
    NOMINAL_FEATURES,
    FEATURE_METADATA,
    RANDOM_STATE,
)

logger = logging.getLogger(__name__)


# Default physiological boundaries for medical safety clipping
PHYSIOLOGICAL_BOUNDS = {
    "hemo": (3.0, 20.0),      # Hemoglobin (g/dL)
    "sc": (0.1, 18.0),        # Serum Creatinine (mg/dL)
    "al": (0.0, 5.0),         # Urine Albumin
    "sg": (1.005, 1.030),     # Urine Specific Gravity
    "su": (0.0, 5.0),         # Urine Sugar
    "age": (1.0, 110.0),      # Age in years
    "bp": (40.0, 220.0),      # Blood Pressure (mm/Hg)
    "bgr": (40.0, 500.0),     # Blood Glucose Random (mg/dL)
    "bu": (5.0, 250.0),       # Blood Urea (mg/dL)
    "sod": (100.0, 175.0),    # Sodium (mEq/L)
    "pot": (1.5, 10.0),       # Potassium (mEq/L)
    "pcv": (10.0, 60.0),      # Packed Cell Volume (%)
    "wbcc": (1000.0, 30000.0),# White Blood Cell Count
    "rbcc": (1.0, 8.5),       # Red Blood Cell Count
}


class ClinicalRegressionImputer(BaseEstimator, TransformerMixin):
    """
    Production-grade Clinical Regression Imputer designed to avoid data leakage
    while preserving physiological correlations across kidney biomarkers.
    
    Attributes:
        continuous_imputer: IterativeImputer fitted with LinearRegression estimator.
        categorical_modes: Dictionary storing precomputed mode for nominal features.
        feature_names: List of feature names seen during fit.
    """

    def __init__(
        self,
        max_iter: int = 25,
        random_state: int = RANDOM_STATE,
        enforce_bounds: bool = True,
    ):
        self.max_iter = max_iter
        self.random_state = random_state
        self.enforce_bounds = enforce_bounds

        self.continuous_imputer: Optional[IterativeImputer] = None
        self.categorical_modes: Dict[str, float] = {}
        self.feature_names: List[str] = []
        self.continuous_cols: List[str] = []
        self.categorical_cols: List[str] = []

    def fit(self, X: Union[pd.DataFrame, np.ndarray], y=None):
        """
        Fits the imputer on observed training cases.
        Learns multivariate regression equations strictly from training data.
        """
        if isinstance(X, np.ndarray):
            X_df = pd.DataFrame(X, columns=[f"col_{i}" for i in range(X.shape[1])])
        else:
            X_df = X.copy()

        self.feature_names = list(X_df.columns)

        # Segregate continuous/ordinal vs categorical features
        all_continuous = set(NUMERICAL_FEATURES + ORDINAL_FEATURES)
        self.continuous_cols = [c for c in self.feature_names if c in all_continuous]
        self.categorical_cols = [c for c in self.feature_names if c not in all_continuous]

        # 1. Fit categorical mode imputer on training data
        self.categorical_modes = {}
        for col in self.categorical_cols:
            mode_series = X_df[col].dropna().mode()
            if not mode_series.empty:
                self.categorical_modes[col] = float(mode_series.iloc[0])
            else:
                self.categorical_modes[col] = 0.0

        # 2. Fit iterative linear regression imputer for continuous variables
        if self.continuous_cols:
            self.continuous_imputer = IterativeImputer(
                estimator=LinearRegression(),
                max_iter=self.max_iter,
                random_state=self.random_state,
                initial_strategy="median",
                imputation_order="ascending",
                skip_complete=True,
            )
            # Fit on the continuous columns of the training set
            self.continuous_imputer.fit(X_df[self.continuous_cols])

        return self

    def transform(self, X: Union[pd.DataFrame, np.ndarray]) -> pd.DataFrame:
        """
        Applies learned multivariate regression equations and categorical modes
        to impute missing values in unseen inference/validation data.
        """
        if isinstance(X, np.ndarray):
            X_df = pd.DataFrame(X, columns=self.feature_names)
        else:
            X_df = X.copy()

        # Check feature consistency
        missing_cols = set(self.feature_names) - set(X_df.columns)
        if missing_cols:
            raise ValueError(f"Missing columns in input: {missing_cols}")

        # 1. Impute categorical columns with learned modes
        for col in self.categorical_cols:
            if col in X_df.columns:
                mode_val = self.categorical_modes.get(col, 0.0)
                X_df[col] = X_df[col].fillna(mode_val)

        # 2. Impute continuous/ordinal columns with Iterative Linear Regression
        if self.continuous_cols and self.continuous_imputer is not None:
            imputed_array = self.continuous_imputer.transform(X_df[self.continuous_cols])
            X_df[self.continuous_cols] = imputed_array

        # 3. Enforce physiological bounds & ordinal rounding if enabled
        if self.enforce_bounds:
            for col in self.continuous_cols:
                if col in PHYSIOLOGICAL_BOUNDS:
                    lower, upper = PHYSIOLOGICAL_BOUNDS[col]
                    X_df[col] = X_df[col].clip(lower=lower, upper=upper)

            # Round specific discrete ordinal features
            if "al" in X_df.columns:
                X_df["al"] = X_df["al"].round().clip(0, 5)
            if "su" in X_df.columns:
                X_df["su"] = X_df["su"].round().clip(0, 5)

        return X_df[self.feature_names]


if __name__ == "__main__":
    from src.data_loader import get_ckd_data
    
    logging.basicConfig(level=logging.INFO)
    X, y, df = get_ckd_data()
    print("Pre-imputation missing count in X:")
    print(X.isna().sum()[X.isna().sum() > 0])

    imputer = ClinicalRegressionImputer()
    imputer.fit(X)
    X_imputed = imputer.transform(X)

    print("\nPost-imputation missing count in X:")
    print(X_imputed.isna().sum().sum())
    print("\nSample imputed rows (Mode A features):")
    print(X_imputed[["hemo", "sc", "al", "htn", "age", "dm"]].head())

