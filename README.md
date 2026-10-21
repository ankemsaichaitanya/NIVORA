# CareLoop (NIVORA) - Clinical Closed-Loop Tracking System

> **BTech Final Year Project**: Closed-Loop Diagnostic Management & Care Coordination System

CareLoop prevents **diagnostic loop closure failure** (where lab and diagnostic test results arrive at a clinic but are never reviewed or acted upon in time by a physician). It tracks the complete clinical lifecycle of diagnostic orders, monitors turnaround SLAs, alerts staff of overdue tasks, and verifies that the ordered next action step is fully completed.

---

## 🌟 The 5 Core Modules

1. **Module 1: Doctor Dashboard**
   - Live worklist of pending reports awaiting physician sign-off.
   - Dynamic SLA countdown timers (*e.g., "36h left" vs "OVERDUE by 18h"*).
   - Flagged abnormal findings & panic critical values (e.g. Potassium 6.4 mmol/L, Platelets 18k).
   - Upcoming follow-up tracker with 1-click care loop closure.

2. **Module 2: Patient Registry & Workflow History**
   - Patient demographics (MRN, DOB, contact, attending physician).
   - Longitudinal step-by-step audit trail visualizer (`Ordered` → `Report Arrived` → `Doctor Reviewed` → `Loop Closed`).

3. **Module 3: Test and Report Tracking**
   - Order new diagnostic tests with priority levels (`ROUTINE` vs `URGENT/STAT`).
   - Lab Report Ingestion / Simulation: Simulate normal, abnormal, or critical panic findings.

4. **Module 4: Follow-up and SLA Alerts**
   - Automated SLA rules: Routine (48h), Urgent (12h), Panic Values (2h).
   - High-urgency alert feed with staff resolution tracking.
   - On-demand "Run SLA Overdue Scan" engine button for viva presentations.

5. **Module 5: AI Clinical Assistant**
   - Synthesizes 3-bullet clinical summaries of patient tasks.
   - Generates patient-friendly SMS/WhatsApp reminders for staff approval before sending.
   - Answers natural language questions regarding clinic workflow history.

6. **Module 6: CKD Early Detection Engine (PyTorch 1D-CNN & KDIGO 2021)**
   - 1D Convolutional Neural Network trained on clinical biomarker sequences (Serum Creatinine, Blood Urea, Hemoglobin, Albumin, Blood Pressure, Glucose).
   - Clinical CKD-EPI (2021) equation calculates exact eGFR and international KDIGO stage (Stage 1 to 5).
   - Direct integration: 1-click **"Initiate CKD Follow-up Care Loop"** automatically converts deep learning risk into an urgent Nephrology diagnostic worklist item with active SLA tracking.

---

## 🚀 How to Run Locally

### 1. Backend (FastAPI)
The backend runs with an automated background SLA scheduler:
```powershell
cd backend
# Run server
uvicorn main:app --port 8000 --reload
```
* **API Server**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **Re-seed Mock Data (Optional)**:
  ```powershell
  python app/seed_data.py
  ```

### 2. Frontend (React.js + Vite)
```powershell
cd frontend
npm run dev
```
* **Web Application**: [http://localhost:5173](http://localhost:5173)

---

## ⚙️ Tech Stack
* **Frontend**: React.js (Vite), Lucide Icons, Modern Clinical Glassmorphic CSS Design System.
* **Backend**: Python FastAPI, SQLAlchemy ORM, Pydantic, APScheduler.
* **Database**: SQLite (default local) / PostgreSQL compatible.
* **AI Engine**: Google Gemini API (`google-generativeai`) with built-in clinical rule engine fallback.
