from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, schemas, models
from app.ml.cnn_model import predict_ckd

router = APIRouter(prefix="/api/ckd", tags=["CKD Early Detection (1D-CNN)"])

class CKDPredictRequest(BaseModel):
    patient_id: Optional[int] = None
    age: int = 52
    gender: str = "Male"
    bp: float = 80.0
    sg: float = 1.020
    al: float = 0.0
    su: float = 0.0
    bgr: float = 110.0
    bu: float = 32.0
    sc: float = 1.1
    sod: float = 138.0
    pot: float = 4.3
    hemo: float = 14.5
    pcv: float = 44.0
    wc: float = 7500.0
    rc: float = 5.0
    htn: bool = False
    dm: bool = False

class CreateCKDLoopRequest(BaseModel):
    patient_id: int
    ordering_doctor: str = "Dr. Sarah Jenkins"
    kdigo_stage: str
    ckd_probability: float
    recommended_action: str

@router.post("/predict")
def run_ckd_prediction(payload: CKDPredictRequest):
    """
    Executes the PyTorch 1D-CNN deep learning model and clinical CKD-EPI eGFR calculation
    to assess early-stage Chronic Kidney Disease risk.
    """
    try:
        features_dict = payload.model_dump()
        result = predict_ckd(features_dict)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing 1D-CNN prediction: {str(e)}")

@router.get("/sample-profiles")
def get_sample_profiles():
    """
    Provides pre-configured clinical biomarker profiles for 1-click demonstration during viva.
    """
    return [
        {
            "id": "early_ckd",
            "title": "Early Diabetic Nephropathy (Stage 2/3a)",
            "description": "Patient with 8-year history of diabetes, elevated serum creatinine (1.6 mg/dL) and microalbuminuria.",
            "data": {
                "age": 58,
                "gender": "Male",
                "bp": 90.0,
                "sg": 1.015,
                "al": 2.0,
                "su": 1.0,
                "bgr": 168.0,
                "bu": 48.0,
                "sc": 1.6,
                "sod": 136.0,
                "pot": 4.8,
                "hemo": 11.8,
                "pcv": 36.0,
                "wc": 8200.0,
                "rc": 4.1,
                "htn": True,
                "dm": True
            }
        },
        {
            "id": "healthy",
            "title": "Normal Healthy Kidney Function (Stage 1)",
            "description": "Routine annual medical checkup with optimal biomarkers and normal eGFR (>90 mL/min).",
            "data": {
                "age": 34,
                "gender": "Female",
                "bp": 72.0,
                "sg": 1.025,
                "al": 0.0,
                "su": 0.0,
                "bgr": 92.0,
                "bu": 22.0,
                "sc": 0.75,
                "sod": 140.0,
                "pot": 4.2,
                "hemo": 14.8,
                "pcv": 44.0,
                "wc": 6800.0,
                "rc": 5.2,
                "htn": False,
                "dm": False
            }
        },
        {
            "id": "severe_ckd",
            "title": "Advanced / Late-Stage Renal Impairment (Stage 4)",
            "description": "Severe loss of renal filtration. Marked anemia, elevated blood urea (78 mg/dL) and creatinine 3.1 mg/dL.",
            "data": {
                "age": 67,
                "gender": "Female",
                "bp": 105.0,
                "sg": 1.010,
                "al": 3.0,
                "su": 2.0,
                "bgr": 210.0,
                "bu": 78.0,
                "sc": 3.1,
                "sod": 130.0,
                "pot": 5.4,
                "hemo": 8.9,
                "pcv": 27.0,
                "wc": 10500.0,
                "rc": 3.2,
                "htn": True,
                "dm": True
            }
        }
    ]

@router.post("/create-care-loop")
def create_ckd_care_loop(payload: CreateCKDLoopRequest, db: Session = Depends(get_db)):
    """
    Connects the ML prediction output into the closed-loop tracking state machine!
    Creates an urgent Renal / CKD management order with an assigned SLA and audit trail.
    """
    patient = crud.get_patient(db, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    order_in = schemas.TestOrderCreate(
        patient_id=patient.id,
        test_name="Renal Function Profile & Nephrology Staging",
        test_category="Nephrology",
        ordering_doctor=payload.ordering_doctor,
        clinical_indication=f"1D-CNN AI Flagged: {payload.kdigo_stage} (Risk: {payload.ckd_probability}%). Action: {payload.recommended_action}",
        priority="URGENT"
    )

    order = crud.create_test_order(db, order_in)

    # Immediately ingest AI finding report
    report_in = schemas.LabReportCreate(
        order_id=order.id,
        lab_name="CareLoop Deep Learning Diagnostic Engine",
        result_summary=f"1D-CNN PREDICTED CKD RISK: {payload.ckd_probability}%. KDIGO Classification: {payload.kdigo_stage}. {payload.recommended_action}",
        has_abnormal_values=True,
        has_critical_values=payload.ckd_probability >= 75.0
    )
    report = crud.receive_lab_report(db, report_in)

    return {
        "message": "CKD Early Detection Follow-up Care Loop successfully initialized!",
        "order_code": order.order_code,
        "task_id": report.review_task.id if report.review_task else None,
        "status": "PENDING_REVIEW"
    }
