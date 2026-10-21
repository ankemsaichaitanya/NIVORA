import os
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from sklearn.preprocessing import StandardScaler
import joblib

# Path for saving model weights & scaler
MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(MODEL_DIR, "ckd_cnn.pth")
SCALER_PATH = os.path.join(MODEL_DIR, "ckd_scaler.joblib")

# ----------------- 1D-CNN ARCHITECTURE FOR TABULAR BIOMARKERS -----------------
class CKDConvNet(nn.Module):
    """
    1D Convolutional Neural Network designed to extract multi-feature interaction
    patterns across clinical blood and urine biomarkers for Chronic Kidney Disease detection.
    """
    def __init__(self, num_features=16):
        super(CKDConvNet, self).__init__()
        # Input shape: (Batch, 1, 16)
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=32, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm1d(32)
        self.relu = nn.ReLU()
        
        self.conv2 = nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm1d(64)
        self.pool1 = nn.MaxPool1d(kernel_size=2) # 16 -> 8
        
        self.conv3 = nn.Conv1d(in_channels=64, out_channels=128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm1d(128)
        self.pool2 = nn.AdaptiveAvgPool1d(1) # -> (Batch, 128, 1)
        
        self.fc1 = nn.Linear(128, 64)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(64, 2) # [prob_no_ckd, prob_ckd]

    def forward(self, x):
        # x is (Batch, 16) -> reshape to (Batch, 1, 16)
        if x.dim() == 2:
            x = x.unsqueeze(1)
            
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(self.relu(self.bn2(self.conv2(x))))
        x = self.pool2(self.relu(self.bn3(self.conv3(x))))
        
        x = x.view(x.size(0), -1) # Flatten (Batch, 128)
        x = self.relu(self.fc1(x))
        x = self.dropout(x)
        out = self.fc2(x)
        return out


# ----------------- CLINICAL eGFR (CKD-EPI) EQUATION -----------------
def calculate_egfr(serum_creatinine: float, age: int, gender: str) -> dict:
    """
    Calculates Estimated Glomerular Filtration Rate (eGFR) using the standard
    CKD-EPI (2021) equation and assigns the international KDIGO Clinical Stage.
    """
    is_female = gender.lower().startswith('f')
    kappa = 0.7 if is_female else 0.9
    alpha = -0.241 if is_female else -0.302
    gender_factor = 1.012 if is_female else 1.0

    scr = max(0.1, float(serum_creatinine))
    scr_kappa = scr / kappa
    
    egfr = 142 * (min(scr_kappa, 1.0) ** alpha) * (max(scr_kappa, 1.0) ** -1.200) * (0.9938 ** age) * gender_factor
    egfr = round(float(egfr), 1)

    # KDIGO Staging
    if egfr >= 90:
        stage = "Stage 1 (Normal / High Kidney Function)"
        clinical_risk = "LOW"
        recommendation = "Normal filtration. Routine annual monitoring."
    elif egfr >= 60:
        stage = "Stage 2 (Mildly Decreased Function)"
        clinical_risk = "MILD"
        recommendation = "Kidney damage with mild loss of kidney function. Screen for microalbuminuria."
    elif egfr >= 45:
        stage = "Stage 3a (Mild to Moderately Decreased Function)"
        clinical_risk = "MODERATE"
        recommendation = "Significant loss of function. Manage blood pressure, dietary sodium, and medication review."
    elif egfr >= 30:
        stage = "Stage 3b (Moderately to Severely Decreased)"
        clinical_risk = "HIGH"
        recommendation = "High risk of progression. Schedule Nephrology consultation and adjust nephrotoxic drugs."
    elif egfr >= 15:
        stage = "Stage 4 (Severely Decreased Function)"
        clinical_risk = "SEVERE"
        recommendation = "Severe loss of kidney function. Prepare for kidney replacement therapy or dialysis education."
    else:
        stage = "Stage 5 (Kidney Failure / End-Stage Renal Disease)"
        clinical_risk = "CRITICAL"
        recommendation = "Kidney failure. Immediate nephrological admission for dialysis or transplant evaluation."

    return {
        "egfr": egfr,
        "kdigo_stage": stage,
        "clinical_risk": clinical_risk,
        "clinical_recommendation": recommendation
    }


# ----------------- TRAIN AND INITIALIZE 1D-CNN WEIGHTS -----------------
def generate_synthetic_ckd_dataset(n_samples=1000):
    """
    Generates realistic clinical distribution modeled on the UCI Chronic Kidney Disease benchmark.
    Features: [age, bp, sg, al, su, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm]
    """
    np.random.seed(42)
    # Healthy distributions (label = 0)
    n_healthy = n_samples // 2
    age_h = np.random.normal(45, 12, n_healthy).clip(18, 85)
    bp_h = np.random.normal(75, 8, n_healthy).clip(60, 95)
    sg_h = np.random.choice([1.020, 1.025], n_healthy)
    al_h = np.zeros(n_healthy)
    su_h = np.zeros(n_healthy)
    bgr_h = np.random.normal(105, 15, n_healthy).clip(70, 140)
    bu_h = np.random.normal(28, 8, n_healthy).clip(10, 45)
    sc_h = np.random.normal(0.9, 0.2, n_healthy).clip(0.5, 1.2)
    sod_h = np.random.normal(138, 3, n_healthy).clip(135, 145)
    pot_h = np.random.normal(4.3, 0.4, n_healthy).clip(3.5, 5.0)
    hemo_h = np.random.normal(15.0, 1.2, n_healthy).clip(13.0, 18.0)
    pcv_h = np.random.normal(45, 4, n_healthy).clip(38, 54)
    wc_h = np.random.normal(7200, 1500, n_healthy).clip(4500, 11000)
    rc_h = np.random.normal(5.2, 0.5, n_healthy).clip(4.2, 6.5)
    htn_h = np.random.choice([0, 1], n_healthy, p=[0.85, 0.15])
    dm_h = np.random.choice([0, 1], n_healthy, p=[0.90, 0.10])

    X_healthy = np.column_stack([age_h, bp_h, sg_h, al_h, su_h, bgr_h, bu_h, sc_h, sod_h, pot_h, hemo_h, pcv_h, wc_h, rc_h, htn_h, dm_h])
    y_healthy = np.zeros(n_healthy)

    # CKD distributions (label = 1)
    n_ckd = n_samples - n_healthy
    age_c = np.random.normal(58, 14, n_ckd).clip(25, 90)
    bp_c = np.random.normal(92, 14, n_ckd).clip(70, 140)
    sg_c = np.random.choice([1.005, 1.010, 1.015], n_ckd)
    al_c = np.random.choice([1, 2, 3, 4], n_ckd, p=[0.4, 0.3, 0.2, 0.1])
    su_c = np.random.choice([0, 1, 2, 3], n_ckd, p=[0.5, 0.2, 0.2, 0.1])
    bgr_c = np.random.normal(160, 45, n_ckd).clip(100, 350)
    bu_c = np.random.normal(68, 28, n_ckd).clip(40, 180)
    sc_c = np.random.normal(2.6, 1.2, n_ckd).clip(1.3, 8.5)
    sod_c = np.random.normal(132, 6, n_ckd).clip(115, 142)
    pot_c = np.random.normal(4.9, 0.8, n_ckd).clip(3.8, 7.2)
    hemo_c = np.random.normal(10.2, 1.8, n_ckd).clip(6.0, 13.0) # Anemia common in CKD
    pcv_c = np.random.normal(31, 6, n_ckd).clip(18, 40)
    wc_c = np.random.normal(9500, 2500, n_ckd).clip(5000, 18000)
    rc_c = np.random.normal(3.6, 0.7, n_ckd).clip(2.0, 4.8)
    htn_c = np.random.choice([0, 1], n_ckd, p=[0.25, 0.75])
    dm_c = np.random.choice([0, 1], n_ckd, p=[0.35, 0.65])

    X_ckd = np.column_stack([age_c, bp_c, sg_c, al_c, su_c, bgr_c, bu_c, sc_c, sod_c, pot_c, hemo_c, pcv_c, wc_c, rc_c, htn_c, dm_c])
    y_ckd = np.ones(n_ckd)

    X = np.vstack([X_healthy, X_ckd])
    y = np.concatenate([y_healthy, y_ckd])

    indices = np.arange(len(X))
    np.random.shuffle(indices)
    return X[indices], y[indices]


def train_and_save_model():
    """Trains the 1D-CNN and persists the PyTorch weights and standard scaler."""
    print("Training 1D-CNN on Chronic Kidney Disease Clinical Distribution...")
    X, y = generate_synthetic_ckd_dataset(n_samples=1200)
    
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    joblib.dump(scaler, SCALER_PATH)

    # Convert to PyTorch tensors
    X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
    y_tensor = torch.tensor(y, dtype=torch.long)

    model = CKDConvNet(num_features=16)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.003, weight_decay=1e-4)

    model.train()
    epochs = 40
    batch_size = 32
    n_batches = len(X) // batch_size

    for epoch in range(epochs):
        permutation = torch.randperm(X_tensor.size()[0])
        for i in range(0, X_tensor.size()[0], batch_size):
            indices = permutation[i:i + batch_size]
            batch_x, batch_y = X_tensor[indices], y_tensor[indices]

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

    # Save model weights
    torch.save(model.state_dict(), MODEL_PATH)
    print(f"1D-CNN Model trained and saved successfully at {MODEL_PATH}")
    return model, scaler


# ----------------- INFERENCE SERVICE -----------------
_model = None
_scaler = None

def get_loaded_model_and_scaler():
    global _model, _scaler
    if _model is None or _scaler is None:
        if not os.path.exists(MODEL_PATH) or not os.path.exists(SCALER_PATH):
            _model, _scaler = train_and_save_model()
        else:
            _model = CKDConvNet(num_features=16)
            _model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
            _model.eval()
            _scaler = joblib.load(SCALER_PATH)
    return _model, _scaler


def predict_ckd(features_dict: dict) -> dict:
    """
    Takes patient clinical features, executes 1D-CNN model inference,
    calculates clinical eGFR & KDIGO staging, and outputs risk assessment.
    """
    model, scaler = get_loaded_model_and_scaler()
    model.eval()

    # Order of features: [age, bp, sg, al, su, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm]
    age = float(features_dict.get('age', 52))
    bp = float(features_dict.get('bp', 80))
    sg = float(features_dict.get('sg', 1.020))
    al = float(features_dict.get('al', 0))
    su = float(features_dict.get('su', 0))
    bgr = float(features_dict.get('bgr', 110))
    bu = float(features_dict.get('bu', 32))
    sc = float(features_dict.get('sc', 1.1))
    sod = float(features_dict.get('sod', 138))
    pot = float(features_dict.get('pot', 4.3))
    hemo = float(features_dict.get('hemo', 14.5))
    pcv = float(features_dict.get('pcv', 44))
    wc = float(features_dict.get('wc', 7500))
    rc = float(features_dict.get('rc', 5.0))
    htn = 1.0 if features_dict.get('htn', False) else 0.0
    dm = 1.0 if features_dict.get('dm', False) else 0.0
    gender = features_dict.get('gender', 'Male')

    raw_features = np.array([[age, bp, sg, al, su, bgr, bu, sc, sod, pot, hemo, pcv, wc, rc, htn, dm]])
    scaled_features = scaler.transform(raw_features)
    tensor_input = torch.tensor(scaled_features, dtype=torch.float32)

    with torch.no_grad():
        logits = model(tensor_input)
        probs = torch.softmax(logits, dim=1).numpy()[0]
        prob_no_ckd = float(probs[0])
        prob_ckd = float(probs[1])

    # Calculate clinical eGFR & KDIGO stage
    egfr_res = calculate_egfr(serum_creatinine=sc, age=int(age), gender=gender)

    is_high_risk = prob_ckd >= 0.50 or egfr_res["egfr"] < 60

    risk_label = "HIGH RISK" if prob_ckd >= 0.70 else "MODERATE RISK" if prob_ckd >= 0.40 else "LOW RISK"

    return {
        "ckd_detected": bool(is_high_risk),
        "ckd_probability": round(prob_ckd * 100, 1),
        "risk_tier": risk_label,
        "model_architecture": "1D-Convolutional Neural Network (PyTorch 1D-CNN)",
        "egfr_score": egfr_res["egfr"],
        "kdigo_stage": egfr_res["kdigo_stage"],
        "clinical_urgency": egfr_res["clinical_risk"],
        "recommendation": egfr_res["clinical_recommendation"],
        "key_biomarkers": {
            "Serum Creatinine": f"{sc} mg/dL",
            "Blood Urea": f"{bu} mg/dL",
            "Hemoglobin": f"{hemo} g/dL",
            "Albumin": f"{int(al)} (Scale 0-4)",
            "Blood Pressure": f"{int(bp)} mm/Hg"
        }
    }
