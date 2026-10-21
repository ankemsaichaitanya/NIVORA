import os
import sys
import datetime
import random

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from faker import Faker
from app.database import SessionLocal, Base, engine
from app import models, crud, schemas

fake = Faker()

TEST_TEMPLATES = [
    {
        "name": "Complete Blood Count (CBC)",
        "category": "Hematology",
        "indication": "Unexplained chronic fatigue and pale conjunctiva",
        "normal_summary": "NORMAL: Hemoglobin 14.2 g/dL, WBC 7.1 x10^3/uL, Platelets 260,000 /uL.",
        "normal_structured": '{"Hemoglobin": "14.2 g/dL", "WBC": "7.1 10^3/uL", "Platelets": "260,000 /uL"}',
        "abnormal_summary": "ABNORMAL: Microcytic anemia. Low Hemoglobin (9.4 g/dL) and Low MCV (72 fL).",
        "abnormal_structured": '{"Hemoglobin": "9.4 g/dL [LOW]", "MCV": "72 fL [LOW]", "Ferritin": "12 ng/mL [LOW]"}',
        "action_type": "MEDICATION_CHANGE",
        "action_details": "Start Oral Ferrous Sulfate 325 mg daily with Vitamin C. Retest CBC in 8 weeks."
    },
    {
        "name": "Lipid Profile (Fasting)",
        "category": "Biochemistry",
        "indication": "Annual cardiovascular risk assessment and dyslipidemia check",
        "normal_summary": "NORMAL: Total Cholesterol 185 mg/dL, LDL 95 mg/dL, HDL 55 mg/dL, Triglycerides 130 mg/dL.",
        "normal_structured": '{"Total Cholesterol": "185 mg/dL", "LDL": "95 mg/dL", "HDL": "55 mg/dL", "Triglycerides": "130 mg/dL"}',
        "abnormal_summary": "HIGH RISK: Hyperlipidemia. Markedly elevated LDL (182 mg/dL) and Total Cholesterol (264 mg/dL).",
        "abnormal_structured": '{"Total Cholesterol": "264 mg/dL [HIGH]", "LDL": "182 mg/dL [HIGH]", "HDL": "38 mg/dL [LOW]", "Triglycerides": "220 mg/dL [HIGH]"}',
        "action_type": "MEDICATION_CHANGE",
        "action_details": "Initiate Atorvastatin 20mg nightly. Dietary counseling referral sent."
    },
    {
        "name": "Glycated Hemoglobin (HbA1c)",
        "category": "Endocrinology",
        "indication": "Type 2 Diabetes Mellitus glycemic control follow-up",
        "normal_summary": "OPTIMAL: HbA1c is 5.4% (Non-diabetic range). Excellent glycemic index.",
        "normal_structured": '{"HbA1c": "5.4%", "Estimated Average Glucose": "108 mg/dL"}',
        "abnormal_summary": "POOR CONTROL: HbA1c elevated to 9.3% (Target < 7.0%). Fasting plasma glucose 210 mg/dL.",
        "abnormal_structured": '{"HbA1c": "9.3% [HIGH]", "eAG": "220 mg/dL [HIGH]"}',
        "action_type": "SPECIALIST_REFERRAL",
        "action_details": "Refer to Diabetic Educator & Endocrinologist for basal insulin titration."
    },
    {
        "name": "Thyroid Stimulating Hormone (TSH)",
        "category": "Endocrinology",
        "indication": "Cold intolerance, 6kg sudden weight gain, sluggish reflexes",
        "normal_summary": "NORMAL: Serum TSH 2.1 uIU/mL, Free T4 1.2 ng/dL.",
        "normal_structured": '{"TSH": "2.1 uIU/mL", "Free T4": "1.2 ng/dL"}',
        "abnormal_summary": "HYPOTHYROIDISM: Elevated TSH (11.4 uIU/mL) with decreased Free T4 (0.6 ng/dL).",
        "abnormal_structured": '{"TSH": "11.4 uIU/mL [HIGH]", "Free T4": "0.6 ng/dL [LOW]"}',
        "action_type": "MEDICATION_CHANGE",
        "action_details": "Prescribe Levothyroxine 50 mcg oral daily before breakfast. Repeat TSH in 6 weeks."
    },
    {
        "name": "Comprehensive Metabolic Panel (CMP)",
        "category": "Biochemistry",
        "indication": "Hypertension monitoring on ACE inhibitor",
        "normal_summary": "NORMAL: Serum Creatinine 0.9 mg/dL, eGFR > 90, Potassium 4.3 mmol/L.",
        "normal_structured": '{"Creatinine": "0.9 mg/dL", "eGFR": ">90 mL/min", "Potassium": "4.3 mmol/L"}',
        "abnormal_summary": "CRITICAL PANIC VALUE: Severe Hyperkalemia detected (Serum Potassium 6.4 mmol/L). Cardiac arrhythmia danger.",
        "abnormal_structured": '{"Potassium": "6.4 mmol/L [CRITICAL HIGH]", "Creatinine": "2.4 mg/dL [HIGH]"}',
        "action_type": "SPECIALIST_REFERRAL",
        "action_details": "IMMEDIATE ER ADMISSION for IV Calcium Gluconate and cardiac monitoring."
    }
]

DOCTORS = ["Dr. Sarah Jenkins (Internal Medicine)", "Dr. Marcus Vance (Cardiology)", "Dr. Elena Rostova (Endocrinology)"]

def seed():
    print("Recreating database schema...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    now = datetime.datetime.utcnow()

    print("Seeding Patients and CareLoop Closed-Loop Workflows...")

    # 1. Seed 12 Patients
    patients = []
    for i in range(12):
        gender = "Male" if i % 2 == 0 else "Female"
        first_name = fake.first_name_male() if gender == "Male" else fake.first_name_female()
        last_name = fake.last_name()
        dob_year = random.randint(1955, 2002)
        dob = f"{dob_year}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
        
        p = models.Patient(
            mrn=f"MRN-{10420 + i}",
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone=f"+1 (555) {random.randint(200, 999)}-{random.randint(1000, 9999)}",
            email=f"{first_name.lower()}.{last_name.lower()}@example.com",
            primary_doctor=random.choice(DOCTORS),
            created_at=now - datetime.timedelta(days=random.randint(5, 30))
        )
        db.add(p)
        patients.append(p)

    db.commit()
    for p in patients:
        db.refresh(p)

    # Scenarios for demo:
    # 1. Order newly placed (awaiting lab sample/report arrival)
    # 2. Report arrived & Pending Review (within normal SLA)
    # 3. Report arrived & OVERDUE (past 48h SLA) -> triggers high-severity alert
    # 4. Critical Value Report (Potassium 6.4) -> triggers CRITICAL panic alert
    # 5. Doctor reviewed & Follow-up in progress (e.g. statin adjustment due in 7 days)
    # 6. Doctor reviewed & Follow-up OVERDUE (due 3 days ago, patient hasn't come back)
    # 7. Closed loop (routine normal report reviewed and closed)

    scenarios = [
        # (patient_idx, template_idx, scenario_type)
        (0, 0, "NEW_ORDER"),
        (1, 1, "PENDING_NORMAL"),
        (2, 2, "PENDING_NORMAL"),
        (3, 1, "OVERDUE_SLA"),
        (4, 4, "CRITICAL_VALUE"),
        (5, 0, "ACTIVE_FOLLOWUP"),
        (6, 3, "OVERDUE_FOLLOWUP"),
        (7, 2, "CLOSED_LOOP"),
        (8, 0, "CLOSED_LOOP"),
        (9, 1, "PENDING_NORMAL"),
        (10, 3, "ACTIVE_FOLLOWUP"),
        (11, 4, "NEW_ORDER"),
    ]

    for p_idx, t_idx, sc_type in scenarios:
        patient = patients[p_idx]
        tmpl = TEST_TEMPLATES[t_idx]
        doc = patient.primary_doctor

        if sc_type == "NEW_ORDER":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="ORDERED",
                ordered_at=now - datetime.timedelta(hours=4)
            )
            db.add(order)
            db.commit()

        elif sc_type == "PENDING_NORMAL":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="PENDING_REVIEW",
                ordered_at=now - datetime.timedelta(hours=20)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Metro Pathology & Diagnostic Center",
                received_at=now - datetime.timedelta(hours=6),
                has_abnormal_values=True,
                has_critical_values=False,
                result_summary=tmpl["abnormal_summary"],
                structured_results=tmpl["abnormal_structured"],
                file_name=f"report_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="PENDING",
                deadline_at=now + datetime.timedelta(hours=42) # 42 hours remaining
            )
            db.add(task)
            db.commit()

        elif sc_type == "OVERDUE_SLA":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="PENDING_REVIEW",
                ordered_at=now - datetime.timedelta(days=4)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Metro Pathology & Diagnostic Center",
                received_at=now - datetime.timedelta(days=3),
                has_abnormal_values=True,
                has_critical_values=False,
                result_summary=tmpl["abnormal_summary"],
                structured_results=tmpl["abnormal_structured"],
                file_name=f"report_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="OVERDUE",
                deadline_at=now - datetime.timedelta(hours=18) # 18 hours overdue!
            )
            db.add(task)
            db.commit()

            alert = models.Alert(
                task_id=task.id,
                patient_id=patient.id,
                alert_type="SLA_BREACH",
                severity="HIGH",
                message=f"OVERDUE REPORT ALERT: {order.test_name} for Patient {patient.first_name} {patient.last_name} has exceeded the 48h review SLA. Assigned: {doc}",
                created_at=now - datetime.timedelta(hours=18),
                is_resolved=False
            )
            db.add(alert)
            db.commit()

        elif sc_type == "CRITICAL_VALUE":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication="Acute fatigue & irregular heartbeat",
                priority="URGENT",
                status="PENDING_REVIEW",
                ordered_at=now - datetime.timedelta(hours=3)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Apex Clinical Diagnostics (STAT Lab)",
                received_at=now - datetime.timedelta(hours=1),
                has_abnormal_values=True,
                has_critical_values=True,
                result_summary=tmpl["abnormal_summary"],
                structured_results=tmpl["abnormal_structured"],
                file_name=f"report_CRITICAL_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="PENDING",
                deadline_at=now + datetime.timedelta(hours=1) # 1 hour left on critical SLA
            )
            db.add(task)
            db.commit()

            alert = models.Alert(
                task_id=task.id,
                patient_id=patient.id,
                alert_type="CRITICAL_VALUE",
                severity="CRITICAL",
                message=f"CRITICAL VALUE ALERT: {tmpl['name']} for Patient {patient.first_name} {patient.last_name} (MRN: {patient.mrn}) reports Potassium 6.4 mmol/L [CRITICAL HIGH]. Immediate intervention required!",
                created_at=now - datetime.timedelta(hours=1),
                is_resolved=False
            )
            db.add(alert)
            db.commit()

        elif sc_type == "ACTIVE_FOLLOWUP":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="REVIEWED",
                ordered_at=now - datetime.timedelta(days=3)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Metro Pathology Laboratory",
                received_at=now - datetime.timedelta(days=2),
                has_abnormal_values=True,
                has_critical_values=False,
                result_summary=tmpl["abnormal_summary"],
                structured_results=tmpl["abnormal_structured"],
                file_name=f"report_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="REVIEWED",
                deadline_at=now - datetime.timedelta(days=1),
                reviewed_at=now - datetime.timedelta(days=1),
                doctor_notes=f"Reviewed abnormal lab findings. Prescribed targeted therapy.",
                next_action_type=tmpl["action_type"],
                action_details=tmpl["action_details"],
                action_deadline=now + datetime.timedelta(days=7),
                action_completed=False
            )
            db.add(task)
            db.commit()

        elif sc_type == "OVERDUE_FOLLOWUP":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="REVIEWED",
                ordered_at=now - datetime.timedelta(days=12)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Metro Pathology Laboratory",
                received_at=now - datetime.timedelta(days=11),
                has_abnormal_values=True,
                has_critical_values=False,
                result_summary=tmpl["abnormal_summary"],
                structured_results=tmpl["abnormal_structured"],
                file_name=f"report_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="REVIEWED",
                deadline_at=now - datetime.timedelta(days=10),
                reviewed_at=now - datetime.timedelta(days=10),
                doctor_notes="Patient notified of dosage adjustment. Scheduled return check-up.",
                next_action_type=tmpl["action_type"],
                action_details=tmpl["action_details"],
                action_deadline=now - datetime.timedelta(days=2), # Due 2 days ago!
                action_completed=False
            )
            db.add(task)
            db.commit()

            alert = models.Alert(
                task_id=task.id,
                patient_id=patient.id,
                alert_type="FOLLOWUP_OVERDUE",
                severity="HIGH",
                message=f"UNRESOLVED FOLLOW-UP: {tmpl['action_type']} for Patient {patient.first_name} {patient.last_name} was due on {(now - datetime.timedelta(days=2)).strftime('%b %d')} and has not been closed.",
                created_at=now - datetime.timedelta(days=2),
                is_resolved=False
            )
            db.add(alert)
            db.commit()

        elif sc_type == "CLOSED_LOOP":
            order = models.TestOrder(
                order_code=f"ORD-{random.randint(1000, 9999)}",
                patient_id=patient.id,
                test_name=tmpl["name"],
                test_category=tmpl["category"],
                ordering_doctor=doc,
                clinical_indication=tmpl["indication"],
                priority="ROUTINE",
                status="CLOSED",
                ordered_at=now - datetime.timedelta(days=8)
            )
            db.add(order)
            db.commit()

            report = models.LabReport(
                order_id=order.id,
                patient_id=patient.id,
                lab_name="Metro Pathology Laboratory",
                received_at=now - datetime.timedelta(days=7),
                has_abnormal_values=False,
                has_critical_values=False,
                result_summary=tmpl["normal_summary"],
                structured_results=tmpl["normal_structured"],
                file_name=f"report_{order.order_code}.pdf"
            )
            db.add(report)
            db.commit()

            task = models.ReviewTask(
                order_id=order.id,
                report_id=report.id,
                assigned_doctor=doc,
                status="CLOSED",
                deadline_at=now - datetime.timedelta(days=5),
                reviewed_at=now - datetime.timedelta(days=6),
                doctor_notes="Normal test results. Patient advised to maintain current lifestyle regimen.",
                next_action_type="ROUTINE_OK",
                action_details="Routine check complete. Follow up next year.",
                action_deadline=now - datetime.timedelta(days=6),
                action_completed=True,
                action_completed_at=now - datetime.timedelta(days=6)
            )
            db.add(task)
            db.commit()

    db.close()
    print("Database successfully seeded with realistic clinical closed-loop data!")

if __name__ == "__main__":
    seed()
