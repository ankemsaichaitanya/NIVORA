import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    mrn = Column(String(50), unique=True, index=True) # Medical Record Number e.g. MRN-10293
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    dob = Column(String(20), nullable=False)
    gender = Column(String(20), nullable=False)
    phone = Column(String(30), nullable=False)
    email = Column(String(100), nullable=True)
    primary_doctor = Column(String(100), default="Dr. Sarah Jenkins")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    orders = relationship("TestOrder", back_populates="patient", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="patient", cascade="all, delete-orphan")


class TestOrder(Base):
    __tablename__ = "test_orders"

    id = Column(Integer, primary_key=True, index=True)
    order_code = Column(String(50), unique=True, index=True) # e.g. ORD-8472
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    test_name = Column(String(150), nullable=False) # e.g. Complete Blood Count (CBC), Lipid Panel
    test_category = Column(String(100), default="Hematology")
    ordering_doctor = Column(String(100), nullable=False)
    clinical_indication = Column(Text, nullable=True) # e.g. Fatigue, routine diabetic screen
    priority = Column(String(20), default="ROUTINE") # ROUTINE or URGENT
    status = Column(String(50), default="ORDERED") # ORDERED, REPORT_ARRIVED, PENDING_REVIEW, REVIEWED, CLOSED
    ordered_at = Column(DateTime, default=datetime.datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="orders")
    report = relationship("LabReport", back_populates="order", uselist=False, cascade="all, delete-orphan")
    review_task = relationship("ReviewTask", back_populates="order", uselist=False, cascade="all, delete-orphan")


class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("test_orders.id"), nullable=False, unique=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    lab_name = Column(String(150), default="Metro Pathology Laboratory")
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    has_abnormal_values = Column(Boolean, default=False)
    has_critical_values = Column(Boolean, default=False)
    result_summary = Column(Text, nullable=True)
    structured_results = Column(Text, nullable=True) # JSON string of parameters & ranges
    file_name = Column(String(255), nullable=True)

    # Relationships
    order = relationship("TestOrder", back_populates="report")
    review_task = relationship("ReviewTask", back_populates="report", uselist=False)


class ReviewTask(Base):
    __tablename__ = "review_tasks"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("test_orders.id"), nullable=False, unique=True)
    report_id = Column(Integer, ForeignKey("lab_reports.id"), nullable=True)
    assigned_doctor = Column(String(100), nullable=False)
    status = Column(String(50), default="PENDING") # PENDING, OVERDUE, REVIEWED, CLOSED
    deadline_at = Column(DateTime, nullable=False)
    reviewed_at = Column(DateTime, nullable=True)
    
    # Doctor Review Action
    doctor_notes = Column(Text, nullable=True)
    next_action_type = Column(String(100), nullable=True) # MEDICATION_CHANGE, SPECIALIST_REFERRAL, REPEAT_TEST, ROUTINE_OK
    action_details = Column(Text, nullable=True)
    action_deadline = Column(DateTime, nullable=True) # Follow-up due date
    action_completed = Column(Boolean, default=False)
    action_completed_at = Column(DateTime, nullable=True)

    # Relationships
    order = relationship("TestOrder", back_populates="review_task")
    report = relationship("LabReport", back_populates="review_task")
    alerts = relationship("Alert", back_populates="task", cascade="all, delete-orphan")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("review_tasks.id"), nullable=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    alert_type = Column(String(50), nullable=False) # SLA_BREACH, CRITICAL_VALUE, FOLLOWUP_OVERDUE
    severity = Column(String(20), default="MEDIUM") # LOW, MEDIUM, HIGH, CRITICAL
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(String(100), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    task = relationship("ReviewTask", back_populates="alerts")
    patient = relationship("Patient", back_populates="alerts")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False) # ORDER, REPORT, TASK, ALERT
    entity_id = Column(Integer, nullable=False)
    action = Column(String(100), nullable=False) # e.g. "ORDER_CREATED", "REPORT_ARRIVED", "DOCTOR_REVIEWED", "SLA_BREACH_ALERT"
    actor = Column(String(100), default="System")
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    details = Column(Text, nullable=True)
