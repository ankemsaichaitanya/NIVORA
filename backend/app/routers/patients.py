from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import crud, schemas, models

router = APIRouter(prefix="/api/patients", tags=["Patients"])

@router.get("", response_model=List[schemas.PatientResponse])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_patients(db, skip=skip, limit=limit)

@router.post("", response_model=schemas.PatientResponse)
def add_patient(patient_in: schemas.PatientCreate, db: Session = Depends(get_db)):
    return crud.create_patient(db, patient_in)

@router.get("/{patient_id}", response_model=schemas.PatientResponse)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

@router.get("/{patient_id}/history")
def read_patient_history(patient_id: int, db: Session = Depends(get_db)):
    history = crud.get_patient_history(db, patient_id)
    if not history:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # Return formatted history including orders, reports, and review tasks
    orders_list = []
    for order in history["orders"]:
        orders_list.append({
            "id": order.id,
            "order_code": order.order_code,
            "test_name": order.test_name,
            "test_category": order.test_category,
            "ordering_doctor": order.ordering_doctor,
            "priority": order.priority,
            "status": order.status,
            "ordered_at": order.ordered_at,
            "report": {
                "id": order.report.id,
                "lab_name": order.report.lab_name,
                "received_at": order.report.received_at,
                "has_abnormal_values": order.report.has_abnormal_values,
                "has_critical_values": order.report.has_critical_values,
                "result_summary": order.report.result_summary,
                "structured_results": order.report.structured_results
            } if order.report else None,
            "review_task": {
                "id": order.review_task.id,
                "assigned_doctor": order.review_task.assigned_doctor,
                "status": order.review_task.status,
                "deadline_at": order.review_task.deadline_at,
                "reviewed_at": order.review_task.reviewed_at,
                "doctor_notes": order.review_task.doctor_notes,
                "next_action_type": order.review_task.next_action_type,
                "action_details": order.review_task.action_details,
                "action_deadline": order.review_task.action_deadline,
                "action_completed": order.review_task.action_completed,
                "action_completed_at": order.review_task.action_completed_at
            } if order.review_task else None
        })

    return {
        "patient": history["patient"],
        "orders": orders_list,
        "alerts": history["alerts"]
    }
