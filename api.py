"""
FastAPI Production Microservice for CKD Prediction & Explainable AI.
Exposes endpoints for clinical inference, mode switching (Mode A vs Mode B),
model switching (Random Forest vs XGBoost), SHAP XAI reports, and benchmark metrics.
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

# Ensure src is importable
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.inference import CKDPredictor
from src.config import PLOTS_DIR, REPORTS_DIR, FEATURE_MODES

app = FastAPI(
    title="NIVORA-2: Production CKD Prediction & Explainable AI API",
    version="2.0.0",
    description="State-of-the-Art Clinical ML and XAI microservice based on Jawad et al. (2024) and Moreno-Sánchez (2023).",
)

# Enable CORS for full-stack frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache loaded predictors
_predictors: Dict[str, CKDPredictor] = {}


def get_predictor(model_name: str = "random_forest", mode: str = "MODE_A") -> CKDPredictor:
    key = f"{model_name.lower()}_{mode.upper()}"
    if key not in _predictors:
        _predictors[key] = CKDPredictor.load_from_artifacts(model_name=model_name, mode=mode)
    return _predictors[key]


# Pydantic schemas
class PatientInputSchema(BaseModel):
    patient_id: Optional[str] = Field(default="Patient_Case_001", description="Unique clinical patient identifier")
    age: float = Field(default=55.0, ge=1.0, le=115.0, description="Patient age in years")
    gender: str = Field(default="male", description="Patient biological sex ('male' or 'female')")
    hemo: float = Field(default=13.5, ge=3.0, le=22.0, description="Hemoglobin (g/dL)")
    sc: float = Field(default=1.1, ge=0.1, le=20.0, description="Serum Creatinine (mg/dL)")
    al: float = Field(default=0.0, ge=0.0, le=5.0, description="Urine Albumin (0 to 5 ordinal dipstick scale)")
    htn: int = Field(default=0, ge=0, le=1, description="Hypertension (1=Yes, 0=No)")
    dm: int = Field(default=0, ge=0, le=1, description="Diabetes Mellitus (1=Yes, 0=No)")
    sg: float = Field(default=1.020, ge=1.000, le=1.040, description="Urine Specific Gravity (Mode B parameter)")
    mode: str = Field(default="MODE_A", description="Feature set: 'MODE_A' (Jawad et al. 6 features) or 'MODE_B' (Moreno-Sánchez 3 features)")
    model_choice: str = Field(default="random_forest", description="Champion model: 'random_forest' or 'xgboost'")


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    """
    Interactive Clinical Decision Support & XAI Web Dashboard.
    """
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>NIVORA-2 | Clinical CKD Prediction & Explainable AI Console</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <style>
    body { background-color: #f4f6f9; font-family: 'Segoe UI', system-ui, sans-serif; }
    .card { border-radius: 12px; border: none; box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
    .badge-stage { font-size: 0.95rem; padding: 0.4em 0.8em; }
    .metric-value { font-size: 2.2rem; font-weight: 700; }
    .risk-critical { color: #dc3545; }
    .risk-high { color: #fd7e14; }
    .risk-moderate { color: #ffc107; }
    .risk-low { color: #198754; }
  </style>
</head>
<body class="py-4">
  <div class="container">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <div>
        <h2 class="fw-bold mb-1"><i class="fa-solid fa-notes-medical text-primary me-2"></i>NIVORA-2 Clinical Diagnostic Console</h2>
        <p class="text-muted mb-0">Explainable AI (XAI) & KDIGO 2024 Decision Support for Chronic Kidney Disease</p>
      </div>
      <div>
        <span class="badge bg-success-subtle text-success border border-success px-3 py-2">
          <i class="fa-solid fa-circle-check me-1"></i> Random Forest & XGBoost Champion Models (99.0% Accuracy)
        </span>
      </div>
    </div>

    <!-- Quick Load Archetypes -->
    <div class="card mb-4 p-3 bg-white">
      <div class="d-flex align-items-center flex-wrap gap-2">
        <span class="fw-semibold me-2"><i class="fa-solid fa-bolt text-warning me-1"></i>Quick Load Cases:</span>
        <button class="btn btn-outline-danger btn-sm" onclick="loadCase('severe')">Case 1: Severe Diabetic Nephropathy (G4)</button>
        <button class="btn btn-outline-success btn-sm" onclick="loadCase('healthy')">Case 2: Healthy Adult Control (G1)</button>
        <button class="btn btn-outline-warning btn-sm" onclick="loadCase('early')">Case 3: Early-Stage Hypertensive (G3a)</button>
        <button class="btn btn-outline-info btn-sm" onclick="loadCase('lean')">Case 4: Ultra-Lean Point-of-Care (Mode B)</button>
      </div>
    </div>

    <div class="row g-4">
      <!-- Input Biomarkers -->
      <div class="col-lg-5">
        <div class="card p-4 bg-white h-100">
          <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="fa-solid fa-sliders text-primary me-2"></i>Patient Clinical Parameters</h5>
          
          <div class="row g-2 mb-3">
            <div class="col-md-6">
              <label class="form-label small fw-semibold">Feature Mode</label>
              <select id="mode" class="form-select form-select-sm" onchange="toggleModeFields()">
                <option value="MODE_A" selected>Mode A (Jawad et al. 6-Feature Set)</option>
                <option value="MODE_B">Mode B (Moreno-Sánchez 3-Feature Set)</option>
              </select>
            </div>
            <div class="col-md-6">
              <label class="form-label small fw-semibold">Champion Model</label>
              <select id="model_choice" class="form-select form-select-sm">
                <option value="random_forest" selected>Random Forest (472 Trees, Depth 14)</option>
                <option value="xgboost">XGBoost (300 Trees, Depth 4)</option>
              </select>
            </div>
          </div>

          <div class="row g-2 mb-3">
            <div class="col-6">
              <label class="form-label small fw-semibold">Patient Age (Years)</label>
              <input type="number" id="age" class="form-control form-control-sm" value="65">
            </div>
            <div class="col-6">
              <label class="form-label small fw-semibold">Biological Sex</label>
              <select id="gender" class="form-select form-select-sm">
                <option value="male" selected>Male</option>
                <option value="female">Female</option>
              </select>
            </div>
          </div>

          <div class="mb-3">
            <label class="form-label small fw-semibold">Hemoglobin (g/dL) <span class="text-muted">(Normal: 12.0 - 17.5)</span></label>
            <input type="number" step="0.1" id="hemo" class="form-control form-control-sm" value="9.8">
          </div>

          <div id="mode_a_fields">
            <div class="mb-3">
              <label class="form-label small fw-semibold">Serum Creatinine (mg/dL) <span class="text-muted">(Normal: 0.6 - 1.2)</span></label>
              <input type="number" step="0.05" id="sc" class="form-control form-control-sm" value="3.2">
            </div>

            <div class="mb-3">
              <label class="form-label small fw-semibold">Albuminuria (Urine Dipstick Scale 0 - 5)</label>
              <select id="al" class="form-select form-select-sm">
                <option value="0">0 - None / Trace (Normal)</option>
                <option value="1">1 - Microalbuminuria (30-300 mg/g)</option>
                <option value="2">2 - Macroalbuminuria (>300 mg/g)</option>
                <option value="3" selected>3 - Severe Macroalbuminuria</option>
                <option value="4">4 - Nephrotic Range</option>
              </select>
            </div>

            <div class="row g-2 mb-3">
              <div class="col-6">
                <label class="form-label small fw-semibold">Hypertension</label>
                <select id="htn" class="form-select form-select-sm">
                  <option value="1" selected>Yes (Present)</option>
                  <option value="0">No (Absent)</option>
                </select>
              </div>
              <div class="col-6">
                <label class="form-label small fw-semibold">Diabetes Mellitus</label>
                <select id="dm" class="form-select form-select-sm">
                  <option value="1" selected>Yes (Present)</option>
                  <option value="0">No (Absent)</option>
                </select>
              </div>
            </div>
          </div>

          <div id="mode_b_fields" style="display:none;">
            <div class="mb-3">
              <label class="form-label small fw-semibold">Urine Specific Gravity <span class="text-muted">(Normal: 1.015 - 1.025)</span></label>
              <input type="number" step="0.005" id="sg" class="form-control form-control-sm" value="1.010">
            </div>
            <div class="mb-3">
              <label class="form-label small fw-semibold">Hypertension</label>
              <select id="htn_b" class="form-select form-select-sm">
                <option value="1" selected>Yes (Present)</option>
                <option value="0">No (Absent)</option>
              </select>
            </div>
          </div>

          <button class="btn btn-primary w-100 fw-bold mt-2 py-2" onclick="evaluatePatient()">
            <i class="fa-solid fa-stethoscope me-1"></i> Run Diagnostic Evaluation
          </button>
        </div>
      </div>

      <!-- Results & Staging Panel -->
      <div class="col-lg-7">
        <div class="card p-4 bg-white mb-4">
          <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="fa-solid fa-heart-pulse text-danger me-2"></i>Diagnostic Assessment & Staging</h5>

          <div class="row g-3 text-center mb-3">
            <div class="col-md-4">
              <div class="p-3 bg-light rounded-3">
                <div class="text-muted small fw-semibold">ML CKD Probability</div>
                <div id="prob_display" class="metric-value risk-critical">--%</div>
                <div id="diagnosis_badge" class="badge bg-danger mt-1">Pending</div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="p-3 bg-light rounded-3">
                <div class="text-muted small fw-semibold">2021 CKD-EPI eGFR</div>
                <div id="egfr_display" class="metric-value">--</div>
                <div class="text-muted small">mL/min/1.73 m²</div>
              </div>
            </div>
            <div class="col-md-4">
              <div class="p-3 bg-light rounded-3">
                <div class="text-muted small fw-semibold">KDIGO Glomerular Stage</div>
                <div id="kdigo_display" class="fw-bold text-dark mt-2">--</div>
                <div id="triage_badge" class="badge bg-warning text-dark mt-2">--</div>
              </div>
            </div>
          </div>

          <div class="mb-3">
            <h6 class="fw-bold text-secondary mb-2"><i class="fa-solid fa-clipboard-list me-1"></i>Clinical Care Directives:</h6>
            <ul id="guidelines_list" class="list-group list-group-flush small">
              <li class="list-group-item text-muted">Awaiting diagnostic execution...</li>
            </ul>
          </div>
        </div>

        <!-- Explainable AI Panel -->
        <div class="card p-4 bg-white">
          <h5 class="fw-bold mb-3 border-bottom pb-2"><i class="fa-solid fa-brain text-info me-2"></i>Explainable AI (SHAP Waterfall Attribution)</h5>
          
          <div id="xai_narrative" class="alert alert-light border small text-dark mb-3" style="white-space: pre-line;">
            Click 'Run Diagnostic Evaluation' to generate patient-specific decision attribution.
          </div>

          <div class="text-center">
            <img id="waterfall_img" src="" alt="SHAP Waterfall" class="img-fluid rounded border shadow-sm" style="display:none; max-height: 420px;">
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    function toggleModeFields() {
      const mode = document.getElementById('mode').value;
      if (mode === 'MODE_B') {
        document.getElementById('mode_a_fields').style.display = 'none';
        document.getElementById('mode_b_fields').style.display = 'block';
      } else {
        document.getElementById('mode_a_fields').style.display = 'block';
        document.getElementById('mode_b_fields').style.display = 'none';
      }
    }

    function loadCase(type) {
      if (type === 'severe') {
        document.getElementById('mode').value = 'MODE_A';
        toggleModeFields();
        document.getElementById('age').value = 68;
        document.getElementById('gender').value = 'male';
        document.getElementById('hemo').value = 9.8;
        document.getElementById('sc').value = 3.2;
        document.getElementById('al').value = 3;
        document.getElementById('htn').value = 1;
        document.getElementById('dm').value = 1;
      } else if (type === 'healthy') {
        document.getElementById('mode').value = 'MODE_A';
        toggleModeFields();
        document.getElementById('age').value = 36;
        document.getElementById('gender').value = 'female';
        document.getElementById('hemo').value = 14.5;
        document.getElementById('sc').value = 0.75;
        document.getElementById('al').value = 0;
        document.getElementById('htn').value = 0;
        document.getElementById('dm').value = 0;
      } else if (type === 'early') {
        document.getElementById('mode').value = 'MODE_A';
        toggleModeFields();
        document.getElementById('age').value = 55;
        document.getElementById('gender').value = 'male';
        document.getElementById('hemo').value = 12.6;
        document.getElementById('sc').value = 1.45;
        document.getElementById('al').value = 1;
        document.getElementById('htn').value = 1;
        document.getElementById('dm').value = 0;
      } else if (type === 'lean') {
        document.getElementById('mode').value = 'MODE_B';
        toggleModeFields();
        document.getElementById('hemo').value = 10.5;
        document.getElementById('sg').value = 1.010;
        document.getElementById('htn_b').value = 1;
      }
      evaluatePatient();
    }

    async function evaluatePatient() {
      const mode = document.getElementById('mode').value;
      const model = document.getElementById('model_choice').value;
      const age = parseFloat(document.getElementById('age').value);
      const gender = document.getElementById('gender').value;
      const hemo = parseFloat(document.getElementById('hemo').value);
      
      const payload = {
        patient_id: "Patient_Live_Assessment",
        mode: mode,
        model_choice: model,
        age: age,
        gender: gender,
        hemo: hemo,
        sc: parseFloat(document.getElementById('sc').value || 1.0),
        al: parseFloat(document.getElementById('al').value || 0.0),
        htn: mode === 'MODE_B' ? parseInt(document.getElementById('htn_b').value) : parseInt(document.getElementById('htn').value),
        dm: parseInt(document.getElementById('dm').value || 0),
        sg: parseFloat(document.getElementById('sg').value || 1.020)
      };

      try {
        const resp = await fetch('/api/predict', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        const data = await resp.json();

        // Update displays
        document.getElementById('prob_display').innerText = data.ckd_probability + '%';
        document.getElementById('prob_display').className = 'metric-value ' + (data.ckd_probability > 50 ? 'risk-critical' : 'risk-low');
        document.getElementById('diagnosis_badge').innerText = data.ckd_detected ? 'CKD POSITIVE' : 'NORMAL / NEGATIVE';
        document.getElementById('diagnosis_badge').className = 'badge ' + (data.ckd_detected ? 'bg-danger' : 'bg-success') + ' mt-1';
        
        document.getElementById('egfr_display').innerText = data.egfr_score;
        document.getElementById('kdigo_display').innerText = data.kdigo_stage;
        document.getElementById('triage_badge').innerText = data.clinical_risk_tier;

        // Care Plan
        const listEl = document.getElementById('guidelines_list');
        listEl.innerHTML = '';
        data.actionable_guidelines.forEach(act => {
          const li = document.createElement('li');
          li.className = 'list-group-item';
          li.innerHTML = '<i class="fa-solid fa-angle-right text-primary me-2"></i>' + act;
          listEl.appendChild(li);
        });

        // XAI Narrative & Plot
        if (data.xai_explanation) {
          document.getElementById('xai_narrative').innerText = data.xai_explanation.clinical_narrative;
        }
        if (data.waterfall_plot_path) {
          const filename = data.waterfall_plot_path.split(/\\\\|\\//).pop();
          const imgEl = document.getElementById('waterfall_img');
          imgEl.src = '/api/plots/' + filename + '?t=' + new Date().getTime();
          imgEl.style.display = 'inline-block';
        }
      } catch (err) {
        alert('Diagnostic execution error: ' + err.message);
      }
    }

    // Initialize on load
    window.onload = () => evaluatePatient();
  </script>
</body>
</html>
"""
    return html_content


@app.get("/")
def root():
    return {
        "service": "NIVORA-2 CKD ML & XAI Engine",
        "status": "ONLINE",
        "version": "2.0.0",
        "clinical_standards": ["KDIGO 2024", "2021 Race-Free CKD-EPI"],
        "modes_available": {
            "MODE_A": "Comprehensive Clinical 6-Feature Set (Jawad et al., 2024): hemo, sc, al, htn, age, dm",
            "MODE_B": "Ultra-Lean 3-Feature Set (Moreno-Sánchez, 2023): hemo, sg, htn",
        },
        "docs_url": "/docs",
    }


@app.post("/api/predict")
def predict_ckd(payload: PatientInputSchema):
    """
    Executes end-to-end CKD diagnostic inference, 2021 CKD-EPI eGFR calculation,
    KDIGO 2024 clinical staging, and SHAP decision attribution.
    """
    try:
        predictor = get_predictor(model_name=payload.model_choice, mode=payload.mode)
        patient_dict = payload.model_dump()
        result = predictor.predict_patient(
            patient_data=patient_dict,
            patient_id=payload.patient_id or "Patient_Case",
            generate_waterfall_plot=True,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Diagnostic inference error: {str(e)}")


@app.get("/api/benchmark-report")
def get_benchmark_report(mode: str = Query(default="MODE_A", enum=["MODE_A", "MODE_B"])):
    """
    Returns the Stratified 10-Fold Cross-Validation benchmark table for all 6 models.
    """
    csv_file = REPORTS_DIR / f"benchmark_summary_{mode.lower()}.csv"
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="Benchmark report not found. Run pipeline first.")
    
    import pandas as pd
    df = pd.read_csv(csv_file)
    return {
        "mode": mode,
        "validation_strategy": "Stratified 10-Fold Cross-Validation (500 Instances, Balanced)",
        "models": df.to_dict(orient="records"),
    }


@app.get("/api/sample-patients")
def get_sample_patients():
    """
    Returns diverse clinical patient profiles for testing and demonstration.
    """
    from demo_inference import PATIENT_CASES
    return PATIENT_CASES


@app.get("/api/plots/{plot_filename}")
def get_plot_image(plot_filename: str):
    """
    Serves generated publication figures (ROC curves, SHAP beeswarm, patient waterfalls).
    """
    file_path = PLOTS_DIR / plot_filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Plot '{plot_filename}' not found.")
    return FileResponse(file_path, media_type="image/png")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)
