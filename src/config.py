"""
Configuration module for the Chronic Kidney Disease (CKD) ML & XAI Pipeline.
Implements specifications from Jawad et al. (2024) and Moreno-Sánchez (2023).
"""

from pathlib import Path
from typing import Dict, List, Any

# ----------------- BASE PATHS -----------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
MODELS_DIR = ARTIFACTS_DIR / "models"
PLOTS_DIR = ARTIFACTS_DIR / "plots"
REPORTS_DIR = ARTIFACTS_DIR / "reports"

# Ensure runtime directories exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, MODELS_DIR, PLOTS_DIR, REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# ----------------- REPRODUCIBILITY SEED -----------------
RANDOM_STATE = 42

# ----------------- DATASET DEFINITION -----------------
UCI_DATASET_ID = 336  # Chronic Kidney Disease Dataset
RAW_DATA_FILE = RAW_DATA_DIR / "chronic_kidney_disease_raw.csv"
CLEANED_DATA_FILE = PROCESSED_DATA_DIR / "ckd_cleaned.csv"
IMPUTED_DATA_FILE = PROCESSED_DATA_DIR / "ckd_imputed.csv"
BALANCED_DATA_FILE = PROCESSED_DATA_DIR / "ckd_smote_balanced.csv"

TARGET_COL = "classification"
POSITIVE_CLASS = 1  # CKD
NEGATIVE_CLASS = 0  # Not-CKD

# Target instance balancing target (SMOTE)
SMOTE_TARGET_SAMPLES = 500  # 250 CKD / 250 Not-CKD

# ----------------- FEATURE SPACE DEFINITIONS -----------------
# 11 Numerical Attributes
NUMERICAL_FEATURES: List[str] = [
    "age",   # Age (years)
    "bp",    # Blood Pressure (mm/Hg)
    "bgr",   # Blood Glucose Random (mgs/dl)
    "bu",    # Blood Urea (mgs/dl)
    "sc",    # Serum Creatinine (mgs/dl)
    "sod",   # Sodium (mEq/L)
    "pot",   # Potassium (mEq/L)
    "hemo",  # Hemoglobin (gms)
    "pcv",   # Packed Cell Volume (%)
    "wbcc",  # White Blood Cell Count (cells/cumm) -> also known as 'wc'
    "rbcc",  # Red Blood Cell Count (millions/cmm) -> also known as 'rc'
]

# 3 Ordinal Attributes
ORDINAL_FEATURES: List[str] = [
    "sg",  # Specific Gravity (1.005, 1.010, 1.015, 1.020, 1.025)
    "al",  # Albumin (0, 1, 2, 3, 4, 5)
    "su",  # Sugar (0, 1, 2, 3, 4, 5)
]

# 10 Nominal Attributes
NOMINAL_FEATURES: List[str] = [
    "rbc",    # Red Blood Cells (normal, abnormal)
    "pc",     # Pus Cell (normal, abnormal)
    "pcc",    # Pus Cell Clumps (present, notpresent)
    "ba",     # Bacteria (present, notpresent)
    "htn",    # Hypertension (yes, no)
    "dm",     # Diabetes Mellitus (yes, no)
    "cad",    # Coronary Artery Disease (yes, no)
    "appet",  # Appetite (good, poor)
    "pe",     # Pedal Edema (yes, no)
    "ane",    # Anemia (yes, no)
]

ALL_INPUT_FEATURES: List[str] = NUMERICAL_FEATURES + ORDINAL_FEATURES + NOMINAL_FEATURES

# ----------------- CLINICAL FEATURE SUBSETS (PAPER MODES) -----------------
# Mode A: Comprehensive Clinical 6-Feature Set (Jawad et al., 2024)
MODE_A_FEATURES: List[str] = [
    "hemo",  # Hemoglobin (g/dL)
    "sc",    # Serum Creatinine (mg/dL)
    "al",    # Albumin (scale 0-5)
    "htn",   # Hypertension (1=yes, 0=no)
    "age",   # Age (years)
    "dm",    # Diabetes Mellitus (1=yes, 0=no)
]

# Mode B: Ultra-Lean 3-Feature Set (Moreno-Sánchez, 2023)
MODE_B_FEATURES: List[str] = [
    "hemo",  # Hemoglobin (g/dL)
    "sg",    # Specific Gravity (e.g. 1.005 - 1.025)
    "htn",   # Hypertension (1=yes, 0=no)
]

FEATURE_MODES: Dict[str, List[str]] = {
    "MODE_A": MODE_A_FEATURES,
    "MODE_B": MODE_B_FEATURES,
    "FULL": ALL_INPUT_FEATURES,
}

# ----------------- CLINICAL REFERENCE RANGES & METADATA -----------------
FEATURE_METADATA: Dict[str, Dict[str, Any]] = {
    "hemo": {
        "name": "Hemoglobin",
        "unit": "g/dL",
        "normal_range": (12.0, 17.5),
        "ckd_indication": "Anemia (hemo < 12.0 g/dL) strongly associates with CKD due to reduced erythropoietin production.",
        "type": "numerical",
        "bounds": (3.0, 20.0),
    },
    "sc": {
        "name": "Serum Creatinine",
        "unit": "mg/dL",
        "normal_range": (0.6, 1.2),
        "ckd_indication": "Elevated creatinine (sc > 1.2 mg/dL) indicates reduced glomerular filtration and renal dysfunction.",
        "type": "numerical",
        "bounds": (0.1, 15.0),
    },
    "al": {
        "name": "Albumin (Proteinuria)",
        "unit": "Scale (0-5)",
        "normal_range": (0, 0),
        "ckd_indication": "Presence of albumin in urine (al >= 1) signals compromised glomerular filtration barrier.",
        "type": "ordinal",
        "bounds": (0.0, 5.0),
    },
    "htn": {
        "name": "Hypertension",
        "unit": "Binary (0=No, 1=Yes)",
        "normal_range": (0, 0),
        "ckd_indication": "Hypertension accelerates renal vascular sclerosis and is both a cause and consequence of CKD.",
        "type": "nominal",
        "bounds": (0, 1),
    },
    "age": {
        "name": "Age",
        "unit": "Years",
        "normal_range": (18, 65),
        "ckd_indication": "Renal function naturally declines with age (~1 mL/min/1.73m2/year after age 40).",
        "type": "numerical",
        "bounds": (1.0, 110.0),
    },
    "dm": {
        "name": "Diabetes Mellitus",
        "unit": "Binary (0=No, 1=Yes)",
        "normal_range": (0, 0),
        "ckd_indication": "Diabetic nephropathy is the primary global etiology for progressive chronic kidney disease.",
        "type": "nominal",
        "bounds": (0, 1),
    },
    "sg": {
        "name": "Specific Gravity",
        "unit": "Ratio",
        "normal_range": (1.015, 1.025),
        "ckd_indication": "Low urine specific gravity (sg <= 1.010) indicates tubular inability to concentrate urine (isosthenuria).",
        "type": "ordinal",
        "bounds": (1.005, 1.030),
    },
}

# ----------------- MODEL HYPERPARAMETERS -----------------
MODEL_CONFIGS: Dict[str, Dict[str, Any]] = {
    "random_forest": {
        "class_name": "RandomForestClassifier",
        "params": {
            "n_estimators": 472,
            "max_depth": 14,
            "criterion": "gini",
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
        },
        "is_champion": True,
        "description": "Champion Ensemble Model (Jawad et al., 2024)",
    },
    "xgboost": {
        "class_name": "XGBClassifier",
        "params": {
            "max_depth": 4,
            "learning_rate": 0.05,
            "n_estimators": 300,
            "eval_metric": "logloss",
            "random_state": RANDOM_STATE,
            "n_jobs": -1,
        },
        "is_champion": True,
        "description": "Champion Gradient Boosting Model",
    },
    "logistic_regression": {
        "class_name": "LogisticRegression",
        "params": {
            "penalty": "l1",
            "solver": "liblinear",
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
            "max_iter": 2000,
        },
        "is_champion": False,
        "description": "Sparse L1 Regularized Clinical Baseline",
    },
    "svm": {
        "class_name": "SVC",
        "params": {
            "kernel": "rbf",
            "probability": True,
            "C": 1.0,
            "gamma": "scale",
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
        },
        "is_champion": False,
        "description": "Non-linear Support Vector Machine (RBF Kernel)",
    },
    "adaboost": {
        "class_name": "AdaBoostClassifier",
        "params": {
            "n_estimators": 100,
            "learning_rate": 1.0,
            "random_state": RANDOM_STATE,
        },
        "is_champion": False,
        "description": "Adaptive Boosting Baseline",
    },
    "decision_tree": {
        "class_name": "DecisionTreeClassifier",
        "params": {
            "criterion": "gini",
            "max_depth": 10,
            "class_weight": "balanced",
            "random_state": RANDOM_STATE,
        },
        "is_champion": False,
        "description": "Single Interpretable Decision Tree Baseline",
    },
}

# ----------------- CROSS-VALIDATION CONFIG -----------------
CV_FOLDS = 10
CV_SHUFFLE = True

# ----------------- CLINICAL KDIGO THRESHOLDS -----------------
KDIGO_STAGES: Dict[str, Dict[str, Any]] = {
    "G1": {
        "name": "Stage 1: Normal or high kidney function",
        "egfr_min": 90.0,
        "egfr_max": float("inf"),
        "risk_level": "LOW",
        "clinical_action": "Kidney damage with normal filtration. Annual eGFR and urine albumin check; maintain lifestyle.",
    },
    "G2": {
        "name": "Stage 2: Mildly decreased kidney function",
        "egfr_min": 60.0,
        "egfr_max": 89.9,
        "risk_level": "MILD",
        "clinical_action": "Mild loss of renal function. Monitor BP, screen for microalbuminuria, control diabetes/hypertension.",
    },
    "G3a": {
        "name": "Stage 3a: Mildly to moderately decreased",
        "egfr_min": 45.0,
        "egfr_max": 59.9,
        "risk_level": "MODERATE",
        "clinical_action": "Moderate renal impairment. Consider ACEi/ARB therapy, manage cardiovascular risk factors, dietary review.",
    },
    "G3b": {
        "name": "Stage 3b: Moderately to severely decreased",
        "egfr_min": 30.0,
        "egfr_max": 44.9,
        "risk_level": "HIGH",
        "clinical_action": "Significant loss of kidney function. Consult Nephrologist, monitor electrolytes, adjust nephrotoxic drugs.",
    },
    "G4": {
        "name": "Stage 4: Severely decreased kidney function",
        "egfr_min": 15.0,
        "egfr_max": 29.9,
        "risk_level": "SEVERE",
        "clinical_action": "Severe impairment. Intensive nephrology care, manage anemia/mineral metabolism, prepare for dialysis access.",
    },
    "G5": {
        "name": "Stage 5: Kidney failure (ESRD)",
        "egfr_min": 0.0,
        "egfr_max": 14.9,
        "risk_level": "CRITICAL",
        "clinical_action": "End-stage renal disease (kidney failure). Urgent hemodialysis, peritoneal dialysis, or renal transplant evaluation.",
    },
}

