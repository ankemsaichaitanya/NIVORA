"""
Clinical Decision Support & Staging Engine.
Implements the Race-Free 2021 CKD-EPI Creatinine Equation, KDIGO 2024 Glomerular Staging,
Albuminuria Classification, and Integrated Clinical Risk Stratification.
"""

import logging
from typing import Dict, Any, Optional, Union
from src.config import KDIGO_STAGES

logger = logging.getLogger(__name__)


def calculate_ckd_epi_2021_egfr(
    serum_creatinine: float,
    age: Union[int, float],
    gender: str = "male",
) -> float:
    """
    Computes Estimated Glomerular Filtration Rate (eGFR) using the official
    2021 CKD-EPI (Chronic Kidney Disease Epidemiology Collaboration) Creatinine Equation.
    
    Formula:
        eGFR = 142 * min(Scr/kappa, 1)^alpha * max(Scr/kappa, 1)^(-1.200) * 0.9938^age * (1.012 if female)
        
    Parameters:
        serum_creatinine: Serum creatinine level in mg/dL (must be > 0).
        age: Patient age in years.
        gender: Patient sex ('male', 'female', 'm', 'f').
        
    Returns:
        eGFR in mL/min/1.73 m2, rounded to 1 decimal place.
    """
    is_female = str(gender).strip().lower().startswith("f")
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    gender_factor = 1.012 if is_female else 1.0

    scr = max(0.1, float(serum_creatinine))
    age_val = max(1.0, float(age))

    scr_over_kappa = scr / kappa
    min_term = min(scr_over_kappa, 1.0) ** alpha
    max_term = max(scr_over_kappa, 1.0) ** (-1.200)
    age_term = 0.9938 ** age_val

    egfr = 142.0 * min_term * max_term * age_term * gender_factor
    return round(float(egfr), 1)


def determine_kdigo_stage(egfr: float) -> Dict[str, Any]:
    """
    Classifies eGFR into the international KDIGO GFR Staging categories (G1 to G5).
    """
    for stage_code, meta in KDIGO_STAGES.items():
        if meta["egfr_min"] <= egfr <= meta["egfr_max"]:
            return {
                "stage_code": stage_code,
                "stage_name": meta["name"],
                "risk_tier": meta["risk_level"],
                "guideline_action": meta["clinical_action"],
            }
    
    # Fallback to G5 if below 0 or extreme
    return {
        "stage_code": "G5",
        "stage_name": KDIGO_STAGES["G5"]["name"],
        "risk_tier": KDIGO_STAGES["G5"]["risk_level"],
        "guideline_action": KDIGO_STAGES["G5"]["clinical_action"],
    }


def determine_albuminuria_stage(albumin_scale: float) -> Dict[str, Any]:
    """
    Maps urine dipstick / ordinal albumin (0 to 5) to KDIGO Albuminuria categories:
        A1: Normal to mildly increased (dipstick negative / trace -> scale 0)
        A2: Moderately increased (microalbuminuria -> scale 1)
        A3: Severely increased (macroalbuminuria / nephrotic -> scale >= 2)
    """
    alb = float(albumin_scale)
    if alb <= 0:
        return {
            "stage": "A1",
            "name": "Normal to mildly increased (<30 mg/g)",
            "clinical_significance": "Intact glomerular filtration barrier.",
        }
    elif alb == 1:
        return {
            "stage": "A2",
            "name": "Moderately increased (30-300 mg/g)",
            "clinical_significance": "Microalbuminuria: early sign of glomerular vascular damage.",
        }
    else:
        return {
            "stage": "A3",
            "name": "Severely increased (>300 mg/g)",
            "clinical_significance": "Macroalbuminuria: prominent nephron injury and rapid progression risk.",
        }


def integrate_clinical_risk(
    ml_probability: float,
    egfr: float,
    kdigo_stage: Dict[str, Any],
    albumin_stage: Optional[Dict[str, Any]] = None,
    hypertension: bool = False,
    diabetes: bool = False,
) -> Dict[str, Any]:
    """
    Integrates ML model probability with KDIGO clinical staging and cardiovascular comorbidities.
    Produces an actionable clinical triage summary.
    """
    prob_pct = round(ml_probability * 100, 1)

    # Determine integrated risk level
    is_critical = egfr < 15.0 or (ml_probability >= 0.85 and egfr < 30.0)
    is_severe = egfr < 30.0 or (ml_probability >= 0.70 and egfr < 45.0)
    is_moderate = egfr < 60.0 or ml_probability >= 0.50
    is_mild = egfr < 90.0 and (ml_probability >= 0.30 or hypertension or diabetes)

    if is_critical:
        risk_category = "CRITICAL / DIALYSIS RISK"
        urgency = "IMMEDIATE NEPHROLOGY ADMISSION"
    elif is_severe:
        risk_category = "HIGH CLINICAL RISK"
        urgency = "URGENT NEPHROLOGY REFERRAL (WITHIN 2 WEEKS)"
    elif is_moderate:
        risk_category = "MODERATE CLINICAL RISK"
        urgency = "NEPHROLOGY / ENDOCRINOLOGY CONSULTATION"
    elif is_mild:
        risk_category = "MILD / PROGRESSION WATCH"
        urgency = "ROUTINE PRIMARY CARE MONITORING (EVERY 3-6 MONTHS)"
    else:
        risk_category = "LOW CLINICAL RISK"
        urgency = "ANNUAL WELLNESS SCREENING"

    # Actionable clinical recommendations
    actions = []
    if egfr < 60:
        actions.append("Initiate or optimize ACE inhibitor / ARB or SGLT2 inhibitor therapy for renal protection.")
        actions.append("Avoid nephrotoxic agents (NSAIDs, aminoglycosides, IV iodinated contrast).")
    if hypertension:
        actions.append("Target strict blood pressure control (<130/80 mmHg per KDIGO 2024 BP guidelines).")
    if diabetes:
        actions.append("Optimize glycemic control (target HbA1c < 7.0%) to retard diabetic glomerulosclerosis.")
    if albumin_stage and albumin_stage["stage"] in ["A2", "A3"]:
        actions.append("Quantify 24-hour urine protein or spot Urine Albumin-to-Creatinine Ratio (uACR).")
    if not actions:
        actions.append("Continue standard preventive lifestyle and annual kidney function monitoring.")

    return {
        "ml_probability_pct": prob_pct,
        "egfr_score": egfr,
        "kdigo_stage": kdigo_stage["stage_name"],
        "albuminuria_stage": albumin_stage["name"] if albumin_stage else "Not assessed",
        "integrated_risk_category": risk_category,
        "clinical_urgency": urgency,
        "actionable_guidelines": actions,
    }


if __name__ == "__main__":
    # Test calculations
    egfr_val = calculate_ckd_epi_2021_egfr(serum_creatinine=2.2, age=58, gender="male")
    stage = determine_kdigo_stage(egfr_val)
    alb = determine_albuminuria_stage(2)
    triage = integrate_clinical_risk(ml_probability=0.88, egfr=egfr_val, kdigo_stage=stage, albumin_stage=alb, hypertension=True, diabetes=True)

    print("Clinical Staging Test:")
    print(f"eGFR: {egfr_val} mL/min/1.73m2")
    print(f"Stage: {stage['stage_name']}")
    print(f"Triage: {triage['integrated_risk_category']}")
    print(f"Actions: {triage['actionable_guidelines']}")

