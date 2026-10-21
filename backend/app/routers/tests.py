from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app import crud, schemas, models

router = APIRouter(prefix="/api/tests", tags=["Tests & Reports"])

@router.get("/orders")
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    orders = crud.get_test_orders(db, status=status)
    results = []
    for o in orders:
        results.append({
            "id": o.id,
            "order_code": o.order_code,
            "patient_id": o.patient_id,
            "patient_name": f"{o.patient.first_name} {o.patient.last_name}" if o.patient else "Unknown",
            "patient_mrn": o.patient.mrn if o.patient else "",
            "test_name": o.test_name,
            "test_category": o.test_category,
            "ordering_doctor": o.ordering_doctor,
            "clinical_indication": o.clinical_indication,
            "priority": o.priority,
            "status": o.status,
            "ordered_at": o.ordered_at,
            "report_id": o.report.id if o.report else None,
            "review_task_id": o.review_task.id if o.review_task else None,
            "task_status": o.review_task.status if o.review_task else None,
            "has_abnormal": o.report.has_abnormal_values if o.report else False,
            "has_critical": o.report.has_critical_values if o.report else False
        })
    return results

@router.post("/orders", response_model=schemas.TestOrderResponse)
def create_order(order_in: schemas.TestOrderCreate, db: Session = Depends(get_db)):
    return crud.create_test_order(db, order_in)

@router.post("/reports/receive")
def receive_report(report_in: schemas.LabReportCreate, db: Session = Depends(get_db)):
    try:
        report = crud.receive_lab_report(db, report_in)
        return {
            "message": "Report received and Doctor Review Task generated with active SLA timer.",
            "report_id": report.id,
            "task_id": report.review_task.id if report.review_task else None,
            "status": "PENDING_REVIEW"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reports/upload-simulate")
async def upload_simulate_report(
    order_id: int = Form(...),
    test_type: str = Form("Complete Blood Count (CBC)"),
    has_abnormal: bool = Form(False),
    has_critical: bool = Form(False),
    db: Session = Depends(get_db)
):
    """
    Simulates lab PDF arrival or manual upload for an order.
    """
    if has_critical:
        summary = "CRITICAL: Severe thrombocytopenia detected (Platelets: 18,000/uL). Immediate physician notification required."
        structured = '{"Platelets": "18,000 /uL [CRITICAL LOW]", "Hemoglobin": "7.8 g/dL [LOW]", "WBC": "14.2 10^3/uL [HIGH]"}'
    elif has_abnormal:
        summary = "ABNORMAL: Elevated Total Cholesterol (248 mg/dL) and elevated LDL (165 mg/dL). Triglycerides borderline high."
        structured = '{"Total Cholesterol": "248 mg/dL [HIGH]", "LDL": "165 mg/dL [HIGH]", "HDL": "42 mg/dL", "Triglycerides": "190 mg/dL"}'
    else:
        summary = "NORMAL: All analyzed parameters within standard clinical reference intervals."
        structured = '{"Hemoglobin": "14.5 g/dL", "WBC": "6.8 10^3/uL", "Platelets": "240,000 /uL", "Glucose (Fasting)": "92 mg/dL"}'

    report_create = schemas.LabReportCreate(
        order_id=order_id,
        lab_name="Metro Pathology & Diagnostic Center",
        result_summary=summary,
        structured_results=structured,
        has_abnormal_values=has_abnormal,
        has_critical_values=has_critical
    )
    return receive_report(report_create, db)

@router.post("/tasks/{task_id}/review")
def review_task(task_id: int, review_in: schemas.ReviewActionSubmit, db: Session = Depends(get_db)):
    try:
        task = crud.submit_doctor_review(db, task_id, review_in)
        return {
            "message": "Doctor review recorded. Next step is being tracked.",
            "task_id": task.id,
            "status": task.status,
            "next_action": task.next_action_type,
            "action_deadline": task.action_deadline,
            "is_closed": task.action_completed
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tasks/{task_id}/complete-followup")
def complete_task_followup(task_id: int, db: Session = Depends(get_db)):
    try:
        task = crud.complete_follow_up(db, task_id)
        return {
            "message": "Follow-up step completed. Care loop successfully closed!",
            "task_id": task.id,
            "status": "CLOSED"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
