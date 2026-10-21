from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud, models, schemas, ai_service

router = APIRouter(prefix="/api/ai", tags=["AI Clinical Assistant"])

@router.get("/patient-summary/{patient_id}")
def get_patient_summary(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    orders = db.query(models.TestOrder).filter(models.TestOrder.patient_id == patient_id).all()
    tasks = db.query(models.ReviewTask).join(models.TestOrder).filter(models.TestOrder.patient_id == patient_id).all()
    alerts = db.query(models.Alert).filter(models.Alert.patient_id == patient_id).all()

    summary_text = ai_service.summarize_patient_tasks(patient, orders, tasks, alerts)
    return {
        "patient_id": patient.id,
        "patient_name": f"{patient.first_name} {patient.last_name}",
        "mrn": patient.mrn,
        "summary": summary_text
    }

@router.post("/draft-reminder")
def draft_reminder(payload: schemas.AIDraftReminderRequest, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, payload.patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    task = None
    order = None
    if payload.task_id:
        task = db.query(models.ReviewTask).filter(models.ReviewTask.id == payload.task_id).first()
        if task:
            order = task.order
    else:
        # Pick the most recent reviewed task
        task = db.query(models.ReviewTask).join(models.TestOrder).filter(
            models.TestOrder.patient_id == payload.patient_id
        ).order_by(models.ReviewTask.id.desc()).first()
        if task:
            order = task.order

    draft = ai_service.draft_patient_reminder(patient, order, task, channel=payload.channel or "SMS")
    return draft

@router.post("/ask")
def ask_ai(payload: schemas.AIQueryRequest, db: Session = Depends(get_db)):
    # Gather clinic context
    stats = crud.get_dashboard_stats(db)
    context_data = {
        "dashboard_stats": stats
    }
    if payload.patient_id:
        patient = crud.get_patient(db, payload.patient_id)
        if patient:
            orders = db.query(models.TestOrder).filter(models.TestOrder.patient_id == payload.patient_id).all()
            context_data["selected_patient"] = {
                "name": f"{patient.first_name} {patient.last_name}",
                "mrn": patient.mrn,
                "orders_count": len(orders),
                "orders": [{"test": o.test_name, "status": o.status} for o in orders]
            }

    answer = ai_service.answer_workflow_question(payload.question, context_data)
    return {"question": payload.question, "answer": answer}
