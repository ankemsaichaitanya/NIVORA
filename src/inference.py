"""
Production Inference Service for Chronic Kidney Disease Prediction & XAI.
Provides a unified API for scoring patient biomarkers, computing eGFR / KDIGO stages,
generating local SHAP waterfall attribution, and formatting clinical diagnostic reports.
"""

import logging
from typing import Dict, Any, Union, Optional, Tuple
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

from src.config import (
    MODELS_DIR,
    FEATURE_MODES,
    MODE_A_FEATURES,
    MODE_B_FEATURES,
    RANDOM_STATE,
)
from src.clinical_engine import (
    calculate_ckd_epi_2021_egfr,
    determine_kdigo_stage,
    determine_albuminuria_stage,
    integrate_clinical_risk,
)
from src.xai import ClinicalXAIExplainer

logger = logging.getLogger(__name__)


class CKDPredictor:
    """
    Production-grade Clinical CKD Diagnostic Service.
    Wraps trained champion models with clinical risk engines and XAI.
    """

    def __init__(
        self,
        model: Any,
        preprocessor: Any,
        mode: str = "MODE_A",
        model_name: str = "Random Forest",
    ):
        self.model = model
        self.preprocessor = preprocessor
        self.mode = mode.upper()
        self.model_name = model_name
        self.feature_names = FEATURE_MODES[self.mode]
        self.explainer = ClinicalXAIExplainer(
            model=self.model,
            feature_names=self.feature_names,
            model_name=self.model_name,
        )

    @classmethod
    def load_from_artifacts(
        cls,
        model_name: str = "random_forest",
        mode: str = "MODE_A",
    ) -> "CKDPredictor":
        """
        Loads persisted model and preprocessor artifacts from disk.
        """
        clean_model_name = model_name.lower().replace(" ", "_")
        clean_mode = mode.lower()
        
        model_path = MODELS_DIR / f"{clean_model_name}_{clean_mode}.joblib"
        prep_path = MODELS_DIR / f"preprocessor_{clean_mode}.joblib"

        if not model_path.exists() or not prep_path.exists():
            raise FileNotFoundError(
                f"Artifacts not found at {model_path} or {prep_path}. "
                f"Please run the training pipeline first."
            )

        model = joblib.load(model_path)
        preprocessor = joblib.load(prep_path)
        display_name = model_name.replace("_", " ").title()

        return cls(model=model, preprocessor=preprocessor, mode=mode, model_name=display_name)

    def save_to_artifacts(self) -> Tuple[Path, Path]:
        """
        Persists current model and preprocessor to artifacts/models/.
        """
        clean_model_name = self.model_name.lower().replace(" ", "_")
        clean_mode = self.mode.lower()
        
        model_path = MODELS_DIR / f"{clean_model_name}_{clean_mode}.joblib"
        prep_path = MODELS_DIR / f"preprocessor_{clean_mode}.joblib"

        joblib.dump(self.model, model_path)
        joblib.dump(self.preprocessor, prep_path)
        logger.info(f"Saved inference model to: {model_path}")
        logger.info(f"Saved preprocessor to: {prep_path}")
        return model_path, prep_path

    def predict_patient(
        self,
        patient_data: Union[Dict[str, Any], pd.Series, pd.DataFrame],
        patient_id: str = "Patient_Case",
        generate_waterfall_plot: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes end-to-end diagnostic inference for a single patient.
        
        Returns comprehensive dictionary including:
          - Model prediction & probability
          - 2021 CKD-EPI eGFR score & KDIGO clinical stage
          - KDIGO Albuminuria stage
          - Integrated clinical risk category & urgency
          - Actionable clinical guidelines
          - Local SHAP waterfall explanation & plot path
        """
        # Convert dictionary to single-row DataFrame
        if isinstance(patient_data, dict):
            raw_df = pd.DataFrame([patient_data])
        elif isinstance(patient_data, pd.Series):
            raw_df = pd.DataFrame([patient_data.to_dict()])
        else:
            raw_df = patient_data.copy().iloc[[0]]

        # Clinical metadata extraction for eGFR
        age = float(raw_df.get("age", 55.0).iloc[0] if "age" in raw_df.columns else 55.0)
        gender = str(raw_df.get("gender", "male").iloc[0] if "gender" in raw_df.columns else "male")
        sc = float(raw_df.get("sc", 1.0).iloc[0] if "sc" in raw_df.columns else 1.0)
        al = float(raw_df.get("al", 0.0).iloc[0] if "al" in raw_df.columns else 0.0)
        htn = bool(raw_df.get("htn", 0).iloc[0] in [1, 1.0, True, "yes", "1"] if "htn" in raw_df.columns else False)
        dm = bool(raw_df.get("dm", 0).iloc[0] in [1, 1.0, True, "yes", "1"] if "dm" in raw_df.columns else False)

        # Preprocess features
        X_proc = self.preprocessor.transform(raw_df)
        
        # Ensure exact column order matching training
        X_input = X_proc[self.feature_names]

        # Model inference
        prob_array = self.model.predict_proba(X_input)[0]
        prob_not_ckd = float(prob_array[0])
        prob_ckd = float(prob_array[1])
        prediction = int(prob_ckd >= 0.50)

        # Clinical eGFR & KDIGO staging
        egfr = calculate_ckd_epi_2021_egfr(serum_creatinine=sc, age=age, gender=gender)
        kdigo_stage = determine_kdigo_stage(egfr)
        alb_stage = determine_albuminuria_stage(al)

        # Clinical Triage Integration
        triage = integrate_clinical_risk(
            ml_probability=prob_ckd,
            egfr=egfr,
            kdigo_stage=kdigo_stage,
            albumin_stage=alb_stage,
            hypertension=htn,
            diabetes=dm,
        )

        # Explainable AI (SHAP Waterfall)
        waterfall_path = None
        patient_explanation = None
        if generate_waterfall_plot:
            waterfall_path, patient_explanation = self.explainer.explain_patient_waterfall(
                patient_row=X_input.iloc[0],
                patient_id=patient_id,
                mode_name=self.mode,
            )

        return {
            "patient_id": patient_id,
            "mode": self.mode,
            "model_architecture": f"{self.model_name} (Hyperparameter-Tuned)",
            "ckd_detected": bool(prediction == 1),
            "ckd_probability": round(prob_ckd * 100, 2),
            "egfr_score": egfr,
            "kdigo_stage": kdigo_stage["stage_name"],
            "albuminuria_stage": alb_stage["name"],
            "clinical_risk_tier": triage["integrated_risk_category"],
            "clinical_urgency": triage["clinical_urgency"],
            "actionable_guidelines": triage["actionable_guidelines"],
            "features_used": {feat: float(X_input.iloc[0][feat]) for feat in self.feature_names},
            "xai_explanation": patient_explanation,
            "waterfall_plot_path": str(waterfall_path) if waterfall_path else None,
        }
