import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

# Patient Schemas
class PatientBase(BaseModel):
    first_name: str
    last_name: str
    dob: str
    gender: str
    phone: str
    email: Optional[str] = None
    primary_doctor: Optional[str] = "Dr. Sarah Jenkins"

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    id: int
    mrn: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

# Test Order Schemas
class TestOrderCreate(BaseModel):
    patient_id: int
    test_name: str
    test_category: Optional[str] = "Hematology"
    ordering_doctor: str
    clinical_indication: Optional[str] = None
    priority: Optional[str] = "ROUTINE"

class TestOrderResponse(BaseModel):
    id: int
    order_code: str
    patient_id: int
    test_name: str
    test_category: str
    ordering_doctor: str
    clinical_indication: Optional[str]
    priority: str
    status: str
    ordered_at: datetime.datetime

    class Config:
        from_attributes = True

# Lab Report Schemas
class LabReportCreate(BaseModel):
    order_id: int
    lab_name: Optional[str] = "Metro Pathology Laboratory"
    result_summary: str
    structured_results: Optional[str] = None
    has_abnormal_values: bool = False
    has_critical_values: bool = False

class LabReportResponse(BaseModel):
    id: int
    order_id: int
    patient_id: int
    lab_name: str
    received_at: datetime.datetime
    has_abnormal_values: bool
    has_critical_values: bool
    result_summary: Optional[str]
    structured_results: Optional[str]

    class Config:
        from_attributes = True

# Doctor Review Schemas
class ReviewActionSubmit(BaseModel):
    doctor_notes: str
    next_action_type: str # MEDICATION_CHANGE, SPECIALIST_REFERRAL, REPEAT_TEST, ROUTINE_OK
    action_details: str
    action_deadline_days: Optional[int] = 7

class ReviewTaskResponse(BaseModel):
    id: int
    order_id: int
    report_id: Optional[int]
    assigned_doctor: str
    status: str
    deadline_at: datetime.datetime
    reviewed_at: Optional[datetime.datetime]
    doctor_notes: Optional[str]
    next_action_type: Optional[str]
    action_details: Optional[str]
    action_deadline: Optional[datetime.datetime]
    action_completed: bool

    class Config:
        from_attributes = True

# Alert Schemas
class AlertResponse(BaseModel):
    id: int
    task_id: Optional[int]
    patient_id: int
    alert_type: str
    severity: str
    message: str
    created_at: datetime.datetime
    is_resolved: bool
    resolved_by: Optional[str]
    resolved_at: Optional[datetime.datetime]

    class Config:
        from_attributes = True

# Dashboard Stats Schema
class DashboardStats(BaseModel):
    total_orders: int
    pending_reports: int
    pending_doctor_review: int
    overdue_tasks: int
    active_follow_ups: int
    closed_loops: int
    critical_alerts: int

# AI Request/Response Schemas
class AIQueryRequest(BaseModel):
    patient_id: Optional[int] = None
    question: str

class AIDraftReminderRequest(BaseModel):
    patient_id: int
    task_id: Optional[int] = None
    channel: Optional[str] = "SMS" # SMS or WhatsApp or Email
