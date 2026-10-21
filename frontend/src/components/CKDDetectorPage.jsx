import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  Cpu, 
  AlertTriangle, 
  CheckCircle2, 
  Stethoscope, 
  ArrowRight, 
  Zap, 
  Info,
  Layers,
  HeartPulse,
  Sparkles
} from 'lucide-react';
import { api } from '../api';

export default function CKDDetectorPage({ patients, onSuccessLoopCreated }) {
  const [selectedPatientId, setSelectedPatientId] = useState(patients?.[0]?.id || '');
  const [sampleProfiles, setSampleProfiles] = useState([]);
  
  // Biomarkers Form State
  const [formData, setFormData] = useState({
    age: 56,
    gender: 'Male',
    bp: 90.0,
    sg: 1.015,
    al: 2.0,
    su: 1.0,
    bgr: 165.0,
    bu: 48.0,
    sc: 1.6,
    sod: 136.0,
    pot: 4.8,
    hemo: 11.5,
    pcv: 36.0,
    wc: 8200.0,
    rc: 4.1,
    htn: true,
    dm: true
  });

  const [loading, setLoading] = useState(false);
  const [prediction, setPrediction] = useState(null);
  const [creatingLoop, setCreatingLoop] = useState(false);
  const [loopSuccessMsg, setLoopSuccessMsg] = useState('');

  // Load sample profiles
  useEffect(() => {
    api.getCKDSamples()
      .then(res => setSampleProfiles(res.data))
      .catch(err => console.error("Error loading sample profiles:", err));
  }, []);

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : (type === 'number' ? parseFloat(value) || 0 : value)
    }));
  };

  const loadPreset = (profile) => {
    setFormData(prev => ({
      ...prev,
      ...profile.data
    }));
    setPrediction(null);
    setLoopSuccessMsg('');
  };

  const handlePredict = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setLoopSuccessMsg('');
    try {
      const res = await api.predictCKD(formData);
      setPrediction(res.data);
    } catch (err) {
      console.error("Prediction error:", err);
      alert("Error calculating CKD prediction.");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCareLoop = async () => {
    if (!selectedPatientId || !prediction) return;
    setCreatingLoop(true);
    try {
      const res = await api.createCKDLoop({
        patient_id: parseInt(selectedPatientId),
        ordering_doctor: "Dr. Sarah Jenkins",
        kdigo_stage: prediction.kdigo_stage,
        ckd_probability: prediction.ckd_probability,
        recommended_action: prediction.recommendation
      });
      setLoopSuccessMsg(`Care Loop Initialized! Order #${res.data.order_code} logged with active review SLA.`);
      if (onSuccessLoopCreated) onSuccessLoopCreated();
    } catch (err) {
      console.error(err);
      alert("Error initializing Care Loop.");
    } finally {
      setCreatingLoop(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
      
      {/* Header Banner */}
      <div className="glass-panel" style={{ 
        padding: '24px 28px', 
        background: 'linear-gradient(135deg, #fff7ed 0%, #ffffff 65%)',
        borderColor: '#fed7aa'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
          <span className="badge" style={{ background: '#ea580c', color: '#ffffff', fontWeight: 800 }}>
            <Cpu size={13} /> 1D-CNN Deep Learning
          </span>
          <span style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 700 }}>
            KDIGO 2021 Clinical Classification
          </span>
        </div>
        <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
          Early Chronic Kidney Disease (CKD) Detection Engine
        </h1>
        <p style={{ color: '#475569', fontSize: '0.9rem', marginTop: '4px', maxWidth: '850px' }}>
          Uses a 1D Convolutional Neural Network (PyTorch) trained on blood and urine biomarker sequences combined with the international CKD-EPI filtration equation to catch renal damage before irreversible stage progression.
        </p>
      </div>

      {/* Preset Profiles */}
      <div>
        <div style={{ fontSize: '0.82rem', fontWeight: 800, color: '#64748b', textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.04em' }}>
          Quick 1-Click Clinical Demonstration Cases
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          {sampleProfiles.map(p => (
            <div 
              key={p.id}
              onClick={() => loadPreset(p)}
              style={{
                background: '#ffffff',
                border: '1px solid #e2e8f0',
                borderRadius: 'var(--radius-md)',
                padding: '14px 18px',
                cursor: 'pointer',
                boxShadow: 'var(--shadow-subtle)',
                transition: 'all 0.18s ease'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = '#ea580c';
                e.currentTarget.style.transform = 'translateY(-2px)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = '#e2e8f0';
                e.currentTarget.style.transform = 'translateY(0)';
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                <span style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.88rem' }}>{p.title}</span>
                <span style={{ fontSize: '0.72rem', color: '#ea580c', fontWeight: 700 }}>Load & Test →</span>
              </div>
              <div style={{ fontSize: '0.78rem', color: '#64748b', lineHeight: '1.4' }}>
                {p.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Main Form and Output Layout */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: '24px' }}>
        
        {/* Left: Input Biomarkers */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="#ea580c" /> Patient Biomarker Profile
          </h2>

          <form onSubmit={handlePredict} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            
            {/* Select Target Patient */}
            <div className="form-group">
              <label className="form-label">Link Assessment to Patient Record</label>
              <select 
                value={selectedPatientId} 
                onChange={(e) => setSelectedPatientId(e.target.value)}
                className="form-select"
              >
                {patients?.map(p => (
                  <option key={p.id} value={p.id}>
                    {p.first_name} {p.last_name} ({p.mrn})
                  </option>
                ))}
              </select>
            </div>

            {/* Core Renal Markers */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Serum Creatinine (mg/dL)</label>
                <input 
                  type="number" 
                  step="0.05"
                  name="sc"
                  value={formData.sc} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Blood Urea / BUN (mg/dL)</label>
                <input 
                  type="number" 
                  step="0.5"
                  name="bu"
                  value={formData.bu} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>
            </div>

            {/* Blood & Protein */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Hemoglobin (g/dL)</label>
                <input 
                  type="number" 
                  step="0.1"
                  name="hemo"
                  value={formData.hemo} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Urine Albumin (0 - 4)</label>
                <select name="al" value={formData.al} onChange={handleInputChange} className="form-select">
                  <option value={0}>0 (Negative / Trace)</option>
                  <option value={1}>1+ (Microalbuminuria)</option>
                  <option value={2}>2+ (Moderate Proteinuria)</option>
                  <option value={3}>3+ (Heavy Proteinuria)</option>
                  <option value={4}>4+ (Nephrotic Range)</option>
                </select>
              </div>
            </div>

            {/* Pressure & Sugar */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Blood Pressure (Diastolic)</label>
                <input 
                  type="number" 
                  name="bp"
                  value={formData.bp} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Fasting Glucose (mg/dL)</label>
                <input 
                  type="number" 
                  name="bgr"
                  value={formData.bgr} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>
            </div>

            {/* Demographics & History */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
              <div className="form-group">
                <label className="form-label">Patient Age</label>
                <input 
                  type="number" 
                  name="age"
                  value={formData.age} 
                  onChange={handleInputChange} 
                  className="form-input" 
                  required 
                />
              </div>

              <div className="form-group">
                <label className="form-label">Gender</label>
                <select name="gender" value={formData.gender} onChange={handleInputChange} className="form-select">
                  <option value="Male">Male</option>
                  <option value="Female">Female</option>
                </select>
              </div>
            </div>

            {/* Comorbidities */}
            <div style={{ display: 'flex', gap: '20px', padding: '10px 0' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.86rem', color: '#0f172a', fontWeight: 600 }}>
                <input 
                  type="checkbox" 
                  name="dm" 
                  checked={formData.dm} 
                  onChange={handleInputChange} 
                  style={{ accentColor: '#ea580c', width: '16px', height: '16px' }}
                />
                Diabetes Mellitus History
              </label>

              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '0.86rem', color: '#0f172a', fontWeight: 600 }}>
                <input 
                  type="checkbox" 
                  name="htn" 
                  checked={formData.htn} 
                  onChange={handleInputChange} 
                  style={{ accentColor: '#ea580c', width: '16px', height: '16px' }}
                />
                Hypertension History
              </label>
            </div>

            <button 
              type="submit" 
              disabled={loading}
              className="btn btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '12px', marginTop: '6px' }}
            >
              <Cpu size={17} /> {loading ? 'Running 1D-CNN Inference...' : 'Execute 1D-CNN CKD Risk Analysis'}
            </button>

          </form>
        </div>

        {/* Right: Prediction Output & CareLoop Action */}
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
          
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <HeartPulse size={18} color="#ea580c" /> Neural Network Assessment & Staging
            </h2>

            {!prediction ? (
              <div style={{ textAlign: 'center', padding: '60px 20px', color: '#64748b' }}>
                <Cpu size={42} color="#cbd5e1" style={{ margin: '0 auto 14px' }} />
                <div style={{ fontWeight: 700, color: '#0f172a', fontSize: '1rem' }}>No Analysis Performed Yet</div>
                <div style={{ fontSize: '0.84rem', marginTop: '4px' }}>
                  Select a sample profile above or enter patient biomarkers and click "Execute 1D-CNN CKD Risk Analysis".
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
                
                {/* Probability & Risk Score Card */}
                <div style={{ 
                  background: prediction.risk_tier === 'HIGH RISK' ? '#fff1f2' : prediction.risk_tier === 'MODERATE RISK' ? '#fff7ed' : '#ecfdf5',
                  border: `1px solid ${prediction.risk_tier === 'HIGH RISK' ? '#fecdd3' : prediction.risk_tier === 'MODERATE RISK' ? '#fed7aa' : '#a7f3d0'}`,
                  borderRadius: 'var(--radius-md)',
                  padding: '18px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div>
                    <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', fontWeight: 800, color: prediction.risk_tier === 'HIGH RISK' ? '#be123c' : prediction.risk_tier === 'MODERATE RISK' ? '#c2410c' : '#047857' }}>
                      1D-CNN Disease Probability
                    </div>
                    <div style={{ fontSize: '2.2rem', fontWeight: 800, color: prediction.risk_tier === 'HIGH RISK' ? '#9f1239' : prediction.risk_tier === 'MODERATE RISK' ? '#9a3412' : '#065f46' }}>
                      {prediction.ckd_probability}%
                    </div>
                    <div style={{ fontSize: '0.78rem', color: '#64748b' }}>
                      Model: {prediction.model_architecture}
                    </div>
                  </div>

                  <span className={`badge ${
                    prediction.risk_tier === 'HIGH RISK' ? 'badge-critical' :
                    prediction.risk_tier === 'MODERATE RISK' ? 'badge-pending' : 'badge-closed'
                  }`} style={{ fontSize: '0.82rem', padding: '6px 14px' }}>
                    {prediction.risk_tier}
                  </span>
                </div>

                {/* Filtration & Staging Matrix */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                      eGFR (CKD-EPI 2021)
                    </div>
                    <div style={{ fontSize: '1.5rem', fontWeight: 800, color: prediction.egfr_score < 60 ? '#ea580c' : '#059669', marginTop: '2px' }}>
                      {prediction.egfr_score} <span style={{ fontSize: '0.75rem', fontWeight: 600 }}>mL/min/1.73m²</span>
                    </div>
                  </div>

                  <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: '0.72rem', color: '#64748b', fontWeight: 800, textTransform: 'uppercase' }}>
                      Clinical Urgency
                    </div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a', marginTop: '6px' }}>
                      {prediction.clinical_urgency}
                    </div>
                  </div>
                </div>

                {/* KDIGO Stage & Action Guidance */}
                <div style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '8px', padding: '16px' }}>
                  <div style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.92rem', marginBottom: '4px' }}>
                    {prediction.kdigo_stage}
                  </div>
                  <div style={{ fontSize: '0.84rem', color: '#475569', lineHeight: '1.5' }}>
                    {prediction.recommendation}
                  </div>
                </div>

                {/* Success Notification */}
                {loopSuccessMsg && (
                  <div style={{ background: '#ecfdf5', border: '1px solid #a7f3d0', padding: '12px 16px', borderRadius: '8px', color: '#047857', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <CheckCircle2 size={16} />
                    {loopSuccessMsg}
                  </div>
                )}

              </div>
            )}
          </div>

          {/* Closed Loop Initiation CTA */}
          {prediction && (
            <div style={{ marginTop: '20px', paddingTop: '16px', borderTop: '1px solid #e2e8f0' }}>
              <button 
                onClick={handleCreateCareLoop} 
                disabled={creatingLoop}
                className="btn btn-primary"
                style={{ width: '100%', justifyContent: 'center', padding: '12px' }}
              >
                <Sparkles size={16} /> 
                {creatingLoop ? 'Initializing Care Loop...' : 'Initiate CKD Follow-up Care Loop in Database'}
              </button>
              <div style={{ fontSize: '0.75rem', color: '#64748b', textAlign: 'center', marginTop: '6px' }}>
                Automatically logs a Nephrology diagnostic order, assigns a review SLA, and starts follow-up tracking.
              </div>
            </div>
          )}

        </div>

      </div>

    </div>
  );
}
