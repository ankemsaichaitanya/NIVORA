"""
Data ingestion and cleaning module for the UCI Chronic Kidney Disease (CKD) dataset.
Handles anomaly cleaning, whitespace/hidden-tab stripping, missing symbol replacement,
and column data type restoration.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import pandas as pd
from ucimlrepo import fetch_ucirepo

from src.config import (
    UCI_DATASET_ID,
    RAW_DATA_FILE,
    CLEANED_DATA_FILE,
    TARGET_COL,
    NUMERICAL_FEATURES,
    ORDINAL_FEATURES,
    NOMINAL_FEATURES,
    ALL_INPUT_FEATURES,
)

logger = logging.getLogger(__name__)


def load_raw_dataset(force_download: bool = False) -> pd.DataFrame:
    """
    Fetches the raw UCI CKD dataset (ID: 336) via ucimlrepo or loads from cached CSV.
    
    Args:
        force_download: If True, forces redownloading from UCI repository.
        
    Returns:
        pd.DataFrame containing raw features and target.
    """
    if RAW_DATA_FILE.exists() and not force_download:
        logger.info(f"Loading raw dataset from local cache: {RAW_DATA_FILE}")
        df = pd.read_csv(RAW_DATA_FILE)
        return df

    logger.info(f"Fetching Chronic Kidney Disease dataset from UCI Machine Learning Repository (ID: {UCI_DATASET_ID})...")
    ckd = fetch_ucirepo(id=UCI_DATASET_ID)
    
    features = ckd.data.features.copy()
    targets = ckd.data.targets.copy()
    
    # Target column might be named 'class' in ucimlrepo
    target_name = targets.columns[0]
    features[TARGET_COL] = targets[target_name]
    
    # Save raw snapshot
    RAW_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    features.to_csv(RAW_DATA_FILE, index=False)
    logger.info(f"Raw dataset cached to: {RAW_DATA_FILE} (Shape: {features.shape})")
    return features


def clean_ckd_dataframe(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Executes systematic clinical data sanitation:
      1. Strips hidden tabs ('\\t'), whitespace, and special characters from column names and cell strings.
      2. Replaces '?', 'nan', 'null', and empty strings with np.nan.
      3. Cleans target column 'classification': fixes 'ckd\\t' -> 'ckd', maps 'ckd' -> 1, 'notckd' -> 0.
      4. Normalizes column name aliases ('wc' <-> 'wbcc', 'rc' <-> 'rbcc').
      5. Casts misclassified numerical attributes to float64 ('pcv', 'wbcc', 'rbcc', etc.).
      6. Normalizes nominal features ('\\tno', ' yes', etc.) into clean canonical lowercase representations.

    Args:
        df_raw: Raw DataFrame from UCI.

    Returns:
        pd.DataFrame: Sanitized dataset with 400 rows and 25 columns (24 features + target).
    """
    df = df_raw.copy()

    # 1. Clean column headers
    df.columns = [str(col).strip().replace("\t", "").lower() for col in df.columns]

    # Normalize aliases if present
    rename_dict = {}
    if "class" in df.columns and TARGET_COL not in df.columns:
        rename_dict["class"] = TARGET_COL
    if "wc" in df.columns and "wbcc" not in df.columns:
        rename_dict["wc"] = "wbcc"
    if "rc" in df.columns and "rbcc" not in df.columns:
        rename_dict["rc"] = "rbcc"
    if rename_dict:
        df = df.rename(columns=rename_dict)

    # 2. Cell string cleaning: strip whitespace, remove tabs, replace question marks
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            # Strip whitespace and tabs
            cleaned_series = (
                df[col]
                .astype(str)
                .str.replace("\t", "", regex=False)
                .str.strip()
                .str.lower()
            )
            # Replace placeholder markers
            cleaned_series = cleaned_series.replace(
                {
                    "?": np.nan,
                    "nan": np.nan,
                    "none": np.nan,
                    "null": np.nan,
                    "": np.nan,
                }
            )
            df[col] = cleaned_series

    # 3. Clean and map target variable 'classification'
    if TARGET_COL in df.columns:
        # Clean 'ckd\t' -> 'ckd', map to binary integer
        df[TARGET_COL] = df[TARGET_COL].astype(str).str.replace("\t", "", regex=False).str.strip().str.lower()
        target_mapping = {"ckd": 1, "notckd": 0}
        df[TARGET_COL] = df[TARGET_COL].map(target_mapping)
        # Verify no NaN in target
        if df[TARGET_COL].isna().any():
            raise ValueError(f"Unmapped target values found: {df_raw[TARGET_COL].unique()}")

    # 4. Cast numerical columns to float64
    for num_col in NUMERICAL_FEATURES:
        if num_col in df.columns:
            df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    # 5. Cast ordinal columns to float64
    for ord_col in ORDINAL_FEATURES:
        if ord_col in df.columns:
            df[ord_col] = pd.to_numeric(df[ord_col], errors="coerce")

    # 6. Normalize nominal categorical values
    for nom_col in NOMINAL_FEATURES:
        if nom_col in df.columns:
            # Map canonical binary values
            if nom_col in ["htn", "dm", "cad", "pe", "ane"]:
                df[nom_col] = df[nom_col].replace(
                    {"yes": 1.0, "no": 0.0}
                )
                df[nom_col] = pd.to_numeric(df[nom_col], errors="coerce")
            elif nom_col in ["rbc", "pc"]:
                df[nom_col] = df[nom_col].replace(
                    {"normal": 0.0, "abnormal": 1.0}
                )
                df[nom_col] = pd.to_numeric(df[nom_col], errors="coerce")
            elif nom_col in ["pcc", "ba"]:
                df[nom_col] = df[nom_col].replace(
                    {"notpresent": 0.0, "present": 1.0}
                )
                df[nom_col] = pd.to_numeric(df[nom_col], errors="coerce")
            elif nom_col == "appet":
                df[nom_col] = df[nom_col].replace(
                    {"good": 0.0, "poor": 1.0}
                )
                df[nom_col] = pd.to_numeric(df[nom_col], errors="coerce")

    logger.info(
        f"Cleaned dataset successfully: {len(df)} samples, "
        f"Target distribution: {df[TARGET_COL].value_counts().to_dict()}"
    )

    # Persist clean CSV
    CLEANED_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEANED_DATA_FILE, index=False)
    return df


def get_ckd_data(
    force_download: bool = False,
) -> Tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """
    Primary accessor returning features X, target y, and combined clean DataFrame.
    
    Returns:
        X: pd.DataFrame of 24 features
        y: pd.Series of binary targets (1=CKD, 0=Not-CKD)
        df_clean: Combined pd.DataFrame
    """
    df_raw = load_raw_dataset(force_download=force_download)
    df_clean = clean_ckd_dataframe(df_raw)

    feature_cols = [c for c in df_clean.columns if c != TARGET_COL]
    X = df_clean[feature_cols].copy()
    y = df_clean[TARGET_COL].copy().astype(int)

    return X, y, df_clean


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    X, y, df = get_ckd_data()
    print("=" * 60)
    print("CKD DATA LOADER SUMMARY:")
    print("=" * 60)
    print(f"X shape: {X.shape}")
    print(f"y shape: {y.shape}")
    print(f"Target counts: {y.value_counts().to_dict()} (1: CKD, 0: Not-CKD)")
    print(f"Cleaned Features: {list(X.columns)}")
    print(f"Null counts in Mode A features:")
    for f in ["hemo", "sc", "al", "htn", "age", "dm"]:
        print(f"  - {f}: {X[f].isna().sum()} missing")
    print("=" * 60)

