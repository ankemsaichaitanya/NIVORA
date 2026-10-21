import os
import json
from app.config import settings

# Attempt to configure Gemini API if key is available
gemini_available = False
if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_available = True
    except Exception as e:
        gemini_available = False

def summarize_patient_tasks(patient, orders, tasks, alerts) -> str:
    """
    Summarizes a patient's outstanding tasks and clinical status.
    """
    patient_context = f"Patient: {patient.first_name} {patient.last_name} (MRN: {patient.mrn}, Age/DOB: {patient.dob}).\n"
    orders_info = []
    for o in orders:
        rep_status = "Report Arrived" if o.report else "Awaiting Lab Report"
        orders_info.append(f"- Test: {o.test_name} (Priority: {o.priority}, Status: {o.status}, {rep_status})")
    
    tasks_info = []
    for t in tasks:
        tasks_info.append(f"- Doctor Task Status: {t.status}, Action: {t.next_action_type or 'None'}, Completed: {t.action_completed}")

    alerts_info = [f"- Alert: {a.severity} - {a.message} (Resolved: {a.is_resolved})" for a in alerts]

    prompt = f"""You are a clinical workflow assistant for CareLoop.
{patient_context}
Ordered Tests:
{chr(10).join(orders_info) if orders_info else 'None'}

Tasks:
{chr(10).join(tasks_info) if tasks_info else 'None'}

Active Alerts:
{chr(10).join(alerts_info) if alerts_info else 'None'}

Please provide a concise, high-priority 3-bullet clinical summary of this patient's current closed-loop status, highlight any overdue actions, and recommend the immediate next step for clinic staff.
"""

    if gemini_available:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            pass # Fall back to intelligent rule summary

    # Built-in Clinical Fallback Summary Engine
    pending_count = sum(1 for t in tasks if t.status in ["PENDING", "OVERDUE"])
    overdue_count = sum(1 for t in tasks if t.status == "OVERDUE")
    unresolved_alerts = sum(1 for a in alerts if not a.is_resolved)

    summary_lines = [
        f"• Patient {patient.first_name} {patient.last_name} currently has {len(orders)} registered diagnostic orders ({pending_count} pending doctor sign-off).",
        f"• Priority Status: {overdue_count} task(s) currently exceed the SLA turnaround threshold and require immediate clinic coordination." if overdue_count > 0 else "• Turnaround Status: All pending reports are currently within normal SLA review windows.",
        f"• Immediate Recommended Action: {'Review critical lab results and contact patient for follow-up.' if unresolved_alerts > 0 else 'Continue routine monitoring until next scheduled clinical check-in.'}"
    ]
    return "\n\n".join(summary_lines)


def draft_patient_reminder(patient, order, task, channel="SMS") -> dict:
    """
    Drafts a patient-friendly reminder regarding follow-up steps for staff approval.
    """
    action_type = task.next_action_type if task else "Review"
    action_details = task.action_details if task else "Follow-up consultation"
    doctor = order.ordering_doctor if order else "Dr. Sarah Jenkins"

    prompt = f"""You are a healthcare communications coordinator.
Draft a warm, reassuring, professional {channel} message to the patient.
Patient Name: {patient.first_name}
Doctor: {doctor}
Test Conducted: {order.test_name if order else 'Recent blood test'}
Doctor's Action/Instruction: {action_details} ({action_type})
Clinic Phone: +1 (555) 234-5678

Rules:
1. Do not use scary medical jargon.
2. Emphasize that the doctor has reviewed their results.
3. State clearly what step the patient should take (e.g. pick up prescription, schedule clinic visit).
4. Keep within 60 words for SMS/WhatsApp.
"""

    if gemini_available:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return {
                    "channel": channel,
                    "recipient": patient.phone if channel in ["SMS", "WhatsApp"] else patient.email,
                    "drafted_message": response.text.strip(),
                    "generated_by": "Gemini-1.5-Flash"
                }
        except Exception as e:
            pass

    # Built-in Clinical Template Fallback
    if action_type == "MEDICATION_CHANGE":
        msg = f"Hello {patient.first_name}, {doctor} has reviewed your {order.test_name if order else 'blood test'} results and updated your medication prescription: {action_details}. Please contact our clinic pharmacy at (555) 234-5678 to confirm."
    elif action_type == "SPECIALIST_REFERRAL":
        msg = f"Hello {patient.first_name}, {doctor} has reviewed your recent test report and recommended a follow-up consultation with a specialist ({action_details}). Please call us to help schedule your appointment."
    elif action_type == "REPEAT_TEST":
        msg = f"Hello {patient.first_name}, {doctor} recommends a follow-up test ({action_details}). Please visit the clinic lab at your earliest convenience."
    else:
        msg = f"Hello {patient.first_name}, {doctor} has reviewed your recent {order.test_name if order else 'lab test'} results and recorded instructions: {action_details}. Please reach out if you have any questions."

    return {
        "channel": channel,
        "recipient": patient.phone if channel in ["SMS", "WhatsApp"] else patient.email,
        "drafted_message": msg,
        "generated_by": "CareLoop Clinical Engine"
    }


def answer_workflow_question(question: str, context_data: dict) -> str:
    """
    Answers natural language queries about patient workflow history.
    """
    prompt = f"""You are CareLoop AI, an assistant for clinic doctors and nurses.
Answer this question using ONLY the provided clinic workflow data:
Question: {question}

Context Data:
{json.dumps(context_data, indent=2, default=str)}

Keep the answer concise (2-3 sentences max) and clinically accurate.
"""
    if gemini_available:
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt)
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            pass

    return f"Based on clinic records, there are {context_data.get('total_orders', 0)} total orders registered. The current workflow status indicates {context_data.get('pending_doctor_review', 0)} reports awaiting physician review and {context_data.get('overdue_tasks', 0)} overdue tasks requiring staff attention."
