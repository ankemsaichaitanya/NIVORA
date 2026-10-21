import datetime
import json
import random
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from app import models, schemas
from app.config import settings

# ----------------- AUDIT LOG HELPER -----------------
def log_audit(db: Session, entity_type: str, entity_id: int, action: str, actor: str, details: str = ""):
    log_entry = models.AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        actor=actor,
        timestamp=datetime.datetime.utcnow(),
        details=details
    )
    db.add(log_entry)
    db.commit()

# ----------------- PATIENTS -----------------
def get_patients(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Patient).order_by(models.Patient.id.desc()).offset(skip).limit(limit).all()

def get_patient(db: Session, patient_id: int):
    return db.query(models.Patient).filter(models.Patient.id == patient_id).first()

def create_patient(db: Session, patient_in: schemas.PatientCreate):
    # Auto-generate MRN (Medical Record Number)
    mrn = f"MRN-{random.randint(10000, 99999)}"
    db_patient = models.Patient(
        mrn=mrn,
        first_name=patient_in.first_name,
        last_name=patient_in.last_name,
        dob=patient_in.dob,
        gender=patient_in.gender,
        phone=patient_in.phone,
        email=patient_in.email,
        primary_doctor=patient_in.primary_doctor or "Dr. Sarah Jenkins"
    )
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    log_audit(db, "PATIENT", db_patient.id, "PATIENT_REGISTERED", "FrontDesk", f"Registered {db_patient.first_name} {db_patient.last_name}")
    return db_patient

def get_patient_history(db: Session, patient_id: int):
    patient = get_patient(db, patient_id)
    if not patient:
        return None
    orders = db.query(models.TestOrder).filter(models.TestOrder.patient_id == patient_id).order_by(models.TestOrder.ordered_at.desc()).all()
    alerts = db.query(models.Alert).filter(models.Alert.patient_id == patient_id).order_by(models.Alert.created_at.desc()).all()
    return {
        "patient": patient,
        "orders": orders,
        "alerts": alerts
    }

# ----------------- TEST ORDERS -----------------
def create_test_order(db: Session, order_in: schemas.TestOrderCreate):
    order_code = f"ORD-{random.randint(1000, 9999)}"
    db_order = models.TestOrder(
        order_code=order_code,
        patient_id=order_in.patient_id,
        test_name=order_in.test_name,
        test_category=order_in.test_category or "Hematology",
        ordering_doctor=order_in.ordering_doctor,
        clinical_indication=order_in.clinical_indication,
        priority=order_in.priority or "ROUTINE",
        status="ORDERED",
        ordered_at=datetime.datetime.utcnow()
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    log_audit(db, "ORDER", db_order.id, "ORDER_CREATED", db_order.ordering_doctor, f"Ordered {db_order.test_name} for patient ID {db_order.patient_id}")
    return db_order

def get_test_orders(db: Session, status: str = None):
    query = db.query(models.TestOrder)
    if status:
        query = query.filter(models.TestOrder.status == status)
    return query.order_by(models.TestOrder.ordered_at.desc()).all()

# ----------------- REPORT ARRIVAL & TASK CREATION -----------------
def receive_lab_report(db: Session, report_in: schemas.LabReportCreate):
    order = db.query(models.TestOrder).filter(models.TestOrder.id == report_in.order_id).first()
    if not order:
        raise ValueError(f"Order with ID {report_in.order_id} not found")

    now = datetime.datetime.utcnow()

    # Create lab report
    db_report = models.LabReport(
        order_id=order.id,
        patient_id=order.patient_id,
        lab_name=report_in.lab_name or "Metro Pathology Laboratory",
        received_at=now,
        has_abnormal_values=report_in.has_abnormal_values,
        has_critical_values=report_in.has_critical_values,
        result_summary=report_in.result_summary,
        structured_results=report_in.structured_results,
        file_name=f"lab_report_{order.order_code}.pdf"
    )
    db.add(db_report)

    # Determine SLA deadline based on priority and critical values
    if report_in.has_critical_values:
        hours = 2 # 2 hours for critical panic values
    elif order.priority == "URGENT":
        hours = settings.SLA_URGENT_HOURS
    else:
        hours = settings.SLA_ROUTINE_HOURS

    deadline = now + datetime.timedelta(hours=hours)

    # Create review task for the ordering doctor
    db_task = models.ReviewTask(
        order_id=order.id,
        report_id=None, # will link after report flush
        assigned_doctor=order.ordering_doctor,
        status="PENDING",
        deadline_at=deadline
    )
    db.add(db_task)
    
    # Update order status
    order.status = "PENDING_REVIEW"
    db.commit()
    db.refresh(db_report)
    db.refresh(db_task)
    db_task.report_id = db_report.id
    db.commit()

    log_audit(db, "REPORT", db_report.id, "REPORT_ARRIVED", "LabInterface", f"Report arrived for {order.test_name}. SLA deadline: {deadline.strftime('%Y-%m-%d %H:%M')}")

    # If critical values detected, trigger an instant Critical Alert!
    if report_in.has_critical_values:
        alert = models.Alert(
            task_id=db_task.id,
            patient_id=order.patient_id,
            alert_type="CRITICAL_VALUE",
            severity="CRITICAL",
            message=f"CRITICAL LAB VALUE ALERT: {order.test_name} for Patient ID {order.patient_id} contains critical out-of-range values. Requires immediate doctor review!",
            created_at=now
        )
        db.add(alert)
        db.commit()
        log_audit(db, "ALERT", alert.id, "CRITICAL_ALERT_TRIGGERED", "System", alert.message)

    return db_report

# ----------------- DOCTOR REVIEW & NEXT STEP -----------------
def submit_doctor_review(db: Session, task_id: int, review_in: schemas.ReviewActionSubmit, doctor_name: str = "Dr. Sarah Jenkins"):
    task = db.query(models.ReviewTask).filter(models.ReviewTask.id == task_id).first()
    if not task:
        raise ValueError("Review task not found")

    now = datetime.datetime.utcnow()
    task.doctor_notes = review_in.doctor_notes
    task.next_action_type = review_in.next_action_type
    task.action_details = review_in.action_details
    task.reviewed_at = now
    
    days = review_in.action_deadline_days or 7
    task.action_deadline = now + datetime.timedelta(days=days)

    if review_in.next_action_type == "ROUTINE_OK":
        # If no follow-up needed, close the loop immediately!
        task.action_completed = True
        task.action_completed_at = now
        task.status = "CLOSED"
        task.order.status = "CLOSED"
        log_audit(db, "TASK", task.id, "LOOP_CLOSED", doctor_name, "Doctor reviewed and cleared patient with routine advice. Loop closed.")
    else:
        # Requires ongoing tracking of the follow-up step
        task.status = "REVIEWED"
        task.order.status = "REVIEWED"
        log_audit(db, "TASK", task.id, "DOCTOR_REVIEWED", doctor_name, f"Recorded next action: {review_in.next_action_type} - '{review_in.action_details}'")

    db.commit()
    db.refresh(task)
    return task

# ----------------- CLOSE FOLLOW-UP STEP (LOOP CLOSURE) -----------------
def complete_follow_up(db: Session, task_id: int, completed_by: str = "Nurse Coordinator"):
    task = db.query(models.ReviewTask).filter(models.ReviewTask.id == task_id).first()
    if not task:
        raise ValueError("Task not found")

    now = datetime.datetime.utcnow()
    task.action_completed = True
    task.action_completed_at = now
    task.status = "CLOSED"
    task.order.status = "CLOSED"

    # Also resolve any pending alerts on this task
    for alert in task.alerts:
        if not alert.is_resolved:
            alert.is_resolved = True
            alert.resolved_by = completed_by
            alert.resolved_at = now

    db.commit()
    db.refresh(task)
    log_audit(db, "TASK", task.id, "LOOP_CLOSED", completed_by, f"Follow-up completed ({task.next_action_type}). Care loop successfully closed.")
    return task

# ----------------- SLA & OVERDUE ENGINE -----------------
def check_sla_and_generate_alerts(db: Session):
    now = datetime.datetime.utcnow()
    
    # 1. Check pending review tasks that breached deadline
    overdue_tasks = db.query(models.ReviewTask).filter(
        models.ReviewTask.status == "PENDING",
        models.ReviewTask.deadline_at < now
    ).all()

    for task in overdue_tasks:
        task.status = "OVERDUE"
        # Check if alert already exists for this task
        existing = db.query(models.Alert).filter(
            models.Alert.task_id == task.id,
            models.Alert.alert_type == "SLA_BREACH",
            models.Alert.is_resolved == False
        ).first()

        if not existing:
            order = task.order
            alert = models.Alert(
                task_id=task.id,
                patient_id=order.patient_id,
                alert_type="SLA_BREACH",
                severity="HIGH",
                message=f"OVERDUE REPORT ALERT: {order.test_name} for Patient #{order.patient_id} has exceeded the review SLA deadline. Responsible: {task.assigned_doctor}",
                created_at=now
            )
            db.add(alert)
            log_audit(db, "ALERT", task.id, "SLA_BREACH_TRIGGERED", "AutomationEngine", alert.message)

    # 2. Check follow-ups where action_deadline < now and not completed
    overdue_followups = db.query(models.ReviewTask).filter(
        models.ReviewTask.status == "REVIEWED",
        models.ReviewTask.action_completed == False,
        models.ReviewTask.action_deadline < now
    ).all()

    for task in overdue_followups:
        existing = db.query(models.Alert).filter(
            models.Alert.task_id == task.id,
            models.Alert.alert_type == "FOLLOWUP_OVERDUE",
            models.Alert.is_resolved == False
        ).first()

        if not existing:
            order = task.order
            alert = models.Alert(
                task_id=task.id,
                patient_id=order.patient_id,
                alert_type="FOLLOWUP_OVERDUE",
                severity="HIGH",
                message=f"UNRESOLVED FOLLOW-UP: Action '{task.next_action_type}' for Patient #{order.patient_id} was due on {task.action_deadline.strftime('%Y-%m-%d')} and has not been closed.",
                created_at=now
            )
            db.add(alert)
            log_audit(db, "ALERT", task.id, "FOLLOWUP_OVERDUE_TRIGGERED", "AutomationEngine", alert.message)

    db.commit()

# ----------------- DASHBOARD STATS -----------------
def get_dashboard_stats(db: Session):
    total_orders = db.query(models.TestOrder).count()
    pending_reports = db.query(models.TestOrder).filter(models.TestOrder.status == "ORDERED").count()
    pending_doctor_review = db.query(models.ReviewTask).filter(models.ReviewTask.status == "PENDING").count()
    overdue_tasks = db.query(models.ReviewTask).filter(models.ReviewTask.status == "OVERDUE").count()
    active_follow_ups = db.query(models.ReviewTask).filter(
        models.ReviewTask.status == "REVIEWED",
        models.ReviewTask.action_completed == False
    ).count()
    closed_loops = db.query(models.ReviewTask).filter(models.ReviewTask.status == "CLOSED").count()
    critical_alerts = db.query(models.Alert).filter(
        models.Alert.severity == "CRITICAL",
        models.Alert.is_resolved == False
    ).count()

    return {
        "total_orders": total_orders,
        "pending_reports": pending_reports,
        "pending_doctor_review": pending_doctor_review,
        "overdue_tasks": overdue_tasks,
        "active_follow_ups": active_follow_ups,
        "closed_loops": closed_loops,
        "critical_alerts": critical_alerts
    }
