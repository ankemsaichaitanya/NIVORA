import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app import crud, models, schemas

router = APIRouter(prefix="/api/alerts", tags=["Alerts & SLA Engine"])

@router.get("", response_model=List[schemas.AlertResponse])
def get_alerts(unresolved_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(models.Alert)
    if unresolved_only:
        query = query.filter(models.Alert.is_resolved == False)
    return query.order_by(models.Alert.created_at.desc()).all()

@router.post("/{alert_id}/resolve")
def resolve_alert(alert_id: int, resolved_by: str = "Clinic Staff", db: Session = Depends(get_db)):
    alert = db.query(models.Alert).filter(models.Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.is_resolved = True
    alert.resolved_by = resolved_by
    alert.resolved_at = datetime.datetime.utcnow()
    db.commit()
    return {"message": "Alert marked as resolved", "alert_id": alert.id}

@router.post("/trigger-sla-check")
def trigger_sla_check(db: Session = Depends(get_db)):
    """
    Manually triggers the SLA & Overdue check (great for viva demo!)
    """
    crud.check_sla_and_generate_alerts(db)
    stats = crud.get_dashboard_stats(db)
    return {
        "message": "SLA & Overdue scan completed successfully.",
        "overdue_tasks": stats["overdue_tasks"],
        "critical_alerts": stats["critical_alerts"]
    }
