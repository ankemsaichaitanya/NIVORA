import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.database import get_db
from app import crud, models, schemas

router = APIRouter(prefix="/api/dashboard", tags=["Doctor Dashboard"])

@router.get("/stats", response_model=schemas.DashboardStats)
def get_stats(db: Session = Depends(get_db)):
    return crud.get_dashboard_stats(db)

@router.get("/pending-reports")
def get_pending_reports(db: Session = Depends(get_db)):
    """
    Module 1: Shows pending reports awaiting physician review
    """
    tasks = db.query(models.ReviewTask).filter(
        models.ReviewTask.status.in_(["PENDING", "OVERDUE"])
    ).order_by(models.ReviewTask.deadline_at.asc()).all()

    now = datetime.datetime.utcnow()
    results = []
    for t in tasks:
        order = t.order
        report = t.report
        patient = order.patient if order else None
        
        diff = (t.deadline_at - now).total_seconds()
        is_overdue = diff < 0
        hours_left = round(diff / 3600, 1)

        results.append({
            "task_id": t.id,
            "order_id": order.id if order else None,
            "order_code": order.order_code if order else "",
            "patient_id": patient.id if patient else None,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
            "patient_mrn": patient.mrn if patient else "",
            "patient_phone": patient.phone if patient else "",
            "test_name": order.test_name if order else "",
            "priority": order.priority if order else "ROUTINE",
            "assigned_doctor": t.assigned_doctor,
            "received_at": report.received_at if report else None,
            "deadline_at": t.deadline_at,
            "hours_left": hours_left,
            "is_overdue": is_overdue,
            "has_abnormal": report.has_abnormal_values if report else False,
            "has_critical": report.has_critical_values if report else False,
            "result_summary": report.result_summary if report else "No summary available",
            "structured_results": report.structured_results if report else "{}"
        })
    return results

@router.get("/overdue-tasks")
def get_overdue_tasks(db: Session = Depends(get_db)):
    """
    Module 1 & 4: Shows overdue tasks where SLA has breached
    """
    tasks = db.query(models.ReviewTask).filter(
        models.ReviewTask.status == "OVERDUE"
    ).order_by(models.ReviewTask.deadline_at.asc()).all()

    now = datetime.datetime.utcnow()
    results = []
    for t in tasks:
        order = t.order
        patient = order.patient if order else None
        hours_overdue = round((now - t.deadline_at).total_seconds() / 3600, 1)
        results.append({
            "task_id": t.id,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
            "patient_mrn": patient.mrn if patient else "",
            "test_name": order.test_name if order else "",
            "assigned_doctor": t.assigned_doctor,
            "deadline_at": t.deadline_at,
            "hours_overdue": hours_overdue,
            "has_critical": t.report.has_critical_values if t.report else False
        })
    return results

@router.get("/active-followups")
def get_active_followups(db: Session = Depends(get_db)):
    """
    Module 1: Upcoming and unresolved follow-ups/referrals
    """
    tasks = db.query(models.ReviewTask).filter(
        models.ReviewTask.status == "REVIEWED",
        models.ReviewTask.action_completed == False
    ).order_by(models.ReviewTask.action_deadline.asc()).all()

    now = datetime.datetime.utcnow()
    results = []
    for t in tasks:
        order = t.order
        patient = order.patient if order else None
        days_remaining = (t.action_deadline - now).days if t.action_deadline else 0

        results.append({
            "task_id": t.id,
            "order_id": order.id if order else None,
            "patient_id": patient.id if patient else None,
            "patient_name": f"{patient.first_name} {patient.last_name}" if patient else "Unknown",
            "patient_mrn": patient.mrn if patient else "",
            "patient_phone": patient.phone if patient else "",
            "test_name": order.test_name if order else "",
            "assigned_doctor": t.assigned_doctor,
            "next_action_type": t.next_action_type,
            "action_details": t.action_details,
            "action_deadline": t.action_deadline,
            "days_remaining": days_remaining,
            "is_past_due": days_remaining < 0,
            "reviewed_at": t.reviewed_at
        })
    return results
