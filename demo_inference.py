"""
Clinical Inference & Explainable AI (XAI) Demonstration.
Tests trained champion models on diverse clinical patient archetypes,
computes 2021 CKD-EPI eGFR, assigns KDIGO stages, and outputs SHAP waterfall attributions.
"""

import json
from pathlib import Path
import pandas as pd
from src.inference import CKDPredictor

PATIENT_CASES = [
    {
        "id": "Patient_001_Severe_Diabetic_Nephropathy",
        "description": "68-year-old male with long-standing diabetes, severe anemia, and marked creatinine elevation.",
        "data": {
            "hemo": 9.8,
            "sc": 3.2,
            "al": 3.0,
            "htn": 1,
            "age": 68,
            "dm": 1,
            "sg": 1.010,
            "gender": "male",
        },
    },
    {
        "id": "Patient_002_Healthy_Adult_Control",
        "description": "36-year-old female with healthy blood pressure, intact filtration, and normal biomarkers.",
        "data": {
            "hemo": 14.2,
            "sc": 0.75,
            "al": 0.0,
            "htn": 0,
            "age": 36,
            "dm": 0,
            "sg": 1.025,
            "gender": "female",
        },
    },
    {
        "id": "Patient_003_Early_Stage_Hypertensive",
        "description": "55-year-old male with hypertension and microalbuminuria; borderline creatinine.",
        "data": {
            "hemo": 12.6,
            "sc": 1.45,
            "al": 1.0,
            "htn": 1,
            "age": 55,
            "dm": 0,
            "sg": 1.015,
            "gender": "male",
        },
    },
    {
        "id": "Patient_004_Ultra_Lean_Screening_Case",
        "description": "Point-of-care triaged patient using Mode B (Hemoglobin, Specific Gravity, Hypertension).",
        "data": {
            "hemo": 10.5,
            "sg": 1.010,
            "htn": 1,
            "age": 60,
            "gender": "male",
        },
    },
]


def run_clinical_demonstration():
    print("=" * 80)
    print("CLINICAL INFERENCE & EXPLAINABLE AI (XAI) DEMONSTRATION")
    print("=" * 80)

    # 1. Load Mode A Champion Model (Random Forest)
    print("\n[1] Initializing Mode A Champion Diagnostic Engine (Random Forest - Jawad et al.)...")
    predictor_mode_a = CKDPredictor.load_from_artifacts(model_name="random_forest", mode="MODE_A")
    
    # 2. Load Mode B Champion Model (Random Forest)
    print("[2] Initializing Mode B Champion Diagnostic Engine (Random Forest - Moreno-Sánchez)...")
    predictor_mode_b = CKDPredictor.load_from_artifacts(model_name="random_forest", mode="MODE_B")

    # Evaluate cases 1-3 on Mode A
    for case in PATIENT_CASES[:3]:
        print("\n" + "-" * 75)
        print(f"PATIENT EVALUATION: {case['id']}")
        print(f"Profile: {case['description']}")
        print("-" * 75)

        res = predictor_mode_a.predict_patient(
            patient_data=case["data"],
            patient_id=case["id"],
            generate_waterfall_plot=True,
        )

        print(f"[*] ML Diagnosis:         {'CHRONIC KIDNEY DISEASE DETECTED' if res['ckd_detected'] else 'NORMAL / NON-CKD'}")
        print(f"[*] Model Probability:    {res['ckd_probability']}%")
        print(f"[*] 2021 CKD-EPI eGFR:    {res['egfr_score']} mL/min/1.73 m2")
        print(f"[*] KDIGO GFR Stage:      {res['kdigo_stage']}")
        print(f"[*] Albuminuria Stage:    {res['albuminuria_stage']}")
        print(f"[*] Clinical Risk Tier:   {res['clinical_risk_tier']}")
        print(f"[*] Clinical Urgency:     {res['clinical_urgency']}")
        print("\nClinical Care Plan:")
        for action in res["actionable_guidelines"]:
            print(f"  • {action}")

        print(f"\n[XAI Attribution Waterfall Plot]: {res['waterfall_plot_path']}")
        if res["xai_explanation"]:
            print("\nAutomated Clinical Narrative:")
            print(res["xai_explanation"]["clinical_narrative"])

    # Evaluate case 4 on Mode B (Ultra-Lean 3 features)
    case_b = PATIENT_CASES[3]
    print("\n" + "-" * 75)
    print(f"ULTRA-LEAN POINT-OF-CARE EVALUATION (Mode B): {case_b['id']}")
    print(f"Profile: {case_b['description']}")
    print("-" * 75)

    res_b = predictor_mode_b.predict_patient(
        patient_data=case_b["data"],
        patient_id=case_b["id"],
        generate_waterfall_plot=True,
    )
    print(f"[*] ML Diagnosis:         {'CHRONIC KIDNEY DISEASE DETECTED' if res_b['ckd_detected'] else 'NORMAL / NON-CKD'}")
    print(f"[*] Model Probability:    {res_b['ckd_probability']}%")
    print(f"[*] Input Features:       {res_b['features_used']}")
    print(f"[*] Clinical Risk Tier:   {res_b['clinical_risk_tier']}")
    print(f"\n[XAI Attribution Waterfall Plot]: {res_b['waterfall_plot_path']}")
    if res_b["xai_explanation"]:
        print("\nAutomated Clinical Narrative:")
        print(res_b["xai_explanation"]["clinical_narrative"])

    print("\n" + "=" * 80)
    print("Clinical demonstration completed successfully.")
    print("=" * 80)


if __name__ == "__main__":
    run_clinical_demonstration()

