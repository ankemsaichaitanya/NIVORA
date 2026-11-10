"""
Explainable AI (XAI) Engine for Chronic Kidney Disease Diagnostics.
Provides TreeExplainer SHAP interpretations, global beeswarm and bar importance plots,
individual patient waterfall plots, and automated clinical natural language rationale.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import shap

from src.config import (
    PLOTS_DIR,
    REPORTS_DIR,
    FEATURE_METADATA,
    TARGET_COL,
)

logger = logging.getLogger(__name__)


class ClinicalXAIExplainer:
    """
    Explainable AI (XAI) Explainer for Tree-based CKD Champion Models
    (Random Forest & XGBoost).
    """

    def __init__(self, model: Any, feature_names: List[str], model_name: str = "Random Forest"):
        self.model = model
        self.feature_names = feature_names
        self.model_name = model_name
        self.explainer = shap.TreeExplainer(model)

    def get_shap_values(self, X: pd.DataFrame) -> shap.Explanation:
        """
        Calculates SHAP values for the positive class (CKD = 1).
        Handles differences in explanation dimensions between RandomForest and XGBoost.
        """
        X_df = X[self.feature_names] if isinstance(X, pd.DataFrame) else pd.DataFrame(X, columns=self.feature_names)
        raw_exp = self.explainer(X_df)

        # RandomForest outputs (samples, features, classes) -> slice for class 1 (CKD)
        if len(raw_exp.shape) == 3 and raw_exp.shape[2] == 2:
            return raw_exp[:, :, 1]
        
        return raw_exp

    def plot_summary_beeswarm(
        self,
        X: pd.DataFrame,
        mode_name: str = "MODE_A",
        save_path: Optional[Path] = None,
        max_display: int = 10,
    ) -> Path:
        """
        Generates and persists publication-ready SHAP summary beeswarm plot.
        Visualizes both feature importance and the directional impact of biomarkers.
        """
        if save_path is None:
            save_path = PLOTS_DIR / f"shap_beeswarm_{self.model_name.lower().replace(' ', '_')}_{mode_name.lower()}.png"

        shap_values = self.get_shap_values(X)

        plt.figure(figsize=(9, 6), dpi=300)
        shap.plots.beeswarm(shap_values, max_display=max_display, show=False)
        plt.title(
            f"SHAP Biomarker Impact (Beeswarm) - {self.model_name} ({mode_name})\n"
            f"Feature Value (Red=High, Blue=Low) vs. Effect on CKD Probability",
            fontsize=11,
            fontweight="bold",
            pad=14,
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"SHAP beeswarm plot saved to: {save_path}")
        return save_path

    def plot_feature_importance_bar(
        self,
        X: pd.DataFrame,
        mode_name: str = "MODE_A",
        save_path: Optional[Path] = None,
        max_display: int = 10,
    ) -> Path:
        """
        Generates global feature importance bar plot ranked by mean |SHAP value|.
        """
        if save_path is None:
            save_path = PLOTS_DIR / f"shap_bar_{self.model_name.lower().replace(' ', '_')}_{mode_name.lower()}.png"

        shap_values = self.get_shap_values(X)

        plt.figure(figsize=(9, 5), dpi=300)
        shap.plots.bar(shap_values, max_display=max_display, show=False)
        plt.title(
            f"Global Biomarker Importance (Mean |SHAP|) - {self.model_name} ({mode_name})",
            fontsize=12,
            fontweight="bold",
            pad=12,
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        logger.info(f"SHAP bar plot saved to: {save_path}")
        return save_path

    def explain_patient_waterfall(
        self,
        patient_row: pd.Series,
        patient_id: str = "Patient_Case",
        mode_name: str = "MODE_A",
        save_path: Optional[Path] = None,
    ) -> Tuple[Path, Dict[str, Any]]:
        """
        Generates local waterfall plot and quantitative feature breakdown for an individual patient.
        """
        if save_path is None:
            clean_id = patient_id.lower().replace(" ", "_")
            save_path = PLOTS_DIR / f"shap_waterfall_{clean_id}_{mode_name.lower()}.png"

        # Ensure single-row DataFrame with correct column ordering
        if isinstance(patient_row, pd.Series):
            df_pt = pd.DataFrame([patient_row[self.feature_names].to_dict()])
        else:
            df_pt = patient_row[self.feature_names].copy()

        shap_exp = self.get_shap_values(df_pt)
        single_exp = shap_exp[0]

        # Extract values for clinical text generation
        feature_contributions = []
        for i, feat in enumerate(self.feature_names):
            val = float(df_pt.iloc[0][feat])
            shap_val = float(single_exp.values[i])
            feature_contributions.append({
                "feature": feat,
                "display_name": FEATURE_METADATA.get(feat, {}).get("name", feat),
                "patient_value": val,
                "unit": FEATURE_METADATA.get(feat, {}).get("unit", ""),
                "shap_impact": shap_val,
                "pushes_risk": shap_val > 0,
            })

        # Sort by absolute SHAP impact
        feature_contributions.sort(key=lambda x: abs(x["shap_impact"]), reverse=True)

        # Generate waterfall plot
        plt.figure(figsize=(8, 6), dpi=300)
        shap.plots.waterfall(single_exp, show=False)
        plt.title(
            f"Patient Decision Attribution: {patient_id}\n{self.model_name} ({mode_name})",
            fontsize=11,
            fontweight="bold",
            pad=14,
        )
        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        plt.close()

        # Build clinical narrative
        clinical_narrative = self._generate_clinical_narrative(feature_contributions, single_exp.base_values)

        patient_explanation = {
            "patient_id": patient_id,
            "base_value": float(single_exp.base_values),
            "predicted_output": float(single_exp.values.sum() + single_exp.base_values),
            "contributions": feature_contributions,
            "clinical_narrative": clinical_narrative,
            "plot_path": str(save_path),
        }

        logger.info(f"Waterfall plot and XAI explanation generated for {patient_id}: {save_path}")
        return save_path, patient_explanation

    def _generate_clinical_narrative(
        self,
        contributions: List[Dict[str, Any]],
        base_value: float,
    ) -> str:
        """
        Translates mathematical SHAP values into an intuitive, actionable
        clinical diagnostic rationale for physicians.
        """
        risk_drivers = [c for c in contributions if c["pushes_risk"] and abs(c["shap_impact"]) > 0.01]
        protective_factors = [c for c in contributions if not c["pushes_risk"] and abs(c["shap_impact"]) > 0.01]

        narrative_lines = []
        narrative_lines.append(f"Model Population Base Value: {base_value:+.2f}")
        
        if risk_drivers:
            narrative_lines.append("\n[+] Primary Biomarkers Elevating CKD Risk:")
            for c in risk_drivers[:4]:
                meta = FEATURE_METADATA.get(c["feature"], {})
                ref_str = f" (Ref: {meta.get('normal_range', 'N/A')} {c['unit']})" if "normal_range" in meta else ""
                narrative_lines.append(
                    f"  - {c['display_name']}: {c['patient_value']} {c['unit']}{ref_str} "
                    f"-> Contributes {c['shap_impact']:+.3f} log-odds toward CKD."
                )
                if "ckd_indication" in meta:
                    narrative_lines.append(f"    Clinical Context: {meta['ckd_indication']}")

        if protective_factors:
            narrative_lines.append("\n[-] Biomarkers Providing Renal Protection / Lowering Risk:")
            for c in protective_factors[:3]:
                meta = FEATURE_METADATA.get(c["feature"], {})
                ref_str = f" (Ref: {meta.get('normal_range', 'N/A')} {c['unit']})" if "normal_range" in meta else ""
                narrative_lines.append(
                    f"  - {c['display_name']}: {c['patient_value']} {c['unit']}{ref_str} "
                    f"-> Contributes {c['shap_impact']:+.3f} log-odds toward Normal Renal Status."
                )

        return "\n".join(narrative_lines)

