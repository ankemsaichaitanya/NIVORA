import React, { useState } from 'react';
import { X, FlaskConical, CheckCircle2 } from 'lucide-react';
import { api } from '../../api';

export default function OrderModal({ patients, onClose, onSuccess }) {
  const [patientId, setPatientId] = useState(patients?.[0]?.id || '');
  const [testName, setTestName] = useState('Complete Blood Count (CBC)');
  const [category, setCategory] = useState('Hematology');
  const [doctor, setDoctor] = useState('Dr. Sarah Jenkins');
  const [priority, setPriority] = useState('ROUTINE');
  const [indication, setIndication] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!patientId) {
      alert("Please select a patient.");
      return;
    }
    setLoading(true);
    try {
      await api.createOrder({
        patient_id: parseInt(patientId),
        test_name: testName,
        test_category: category,
        ordering_doctor: doctor,
        priority: priority,
        clinical_indication: indication || "Diagnostic assessment"
      });
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      alert("Error placing order.");
    } finally {
      setLoading(false);
    }
  };

  const handleTestChange = (e) => {
    const name = e.target.value;
    setTestName(name);
    if (name.includes('CBC') || name.includes('Blood')) setCategory('Hematology');
    else if (name.includes('Lipid') || name.includes('Metabolic')) setCategory('Biochemistry');
    else if (name.includes('TSH') || name.includes('HbA1c')) setCategory('Endocrinology');
    else if (name.includes('Troponin')) setCategory('Cardiology');
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff7ed' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FlaskConical size={20} color="#ea580c" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>Order Diagnostic Blood Test</h2>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div className="form-group">
            <label className="form-label">Select Patient</label>
            <select 
              value={patientId} 
              onChange={(e) => setPatientId(e.target.value)} 
              className="form-select"
              required
            >
              {patients?.map(p => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Diagnostic Test</label>
              <select value={testName} onChange={handleTestChange} className="form-select">
                <option value="Complete Blood Count (CBC)">Complete Blood Count (CBC)</option>
                <option value="Lipid Profile (Fasting)">Lipid Profile (Fasting)</option>
                <option value="Glycated Hemoglobin (HbA1c)">Glycated Hemoglobin (HbA1c)</option>
                <option value="Thyroid Stimulating Hormone (TSH)">Thyroid Panel (TSH)</option>
                <option value="Comprehensive Metabolic Panel (CMP)">Comprehensive Metabolic (CMP)</option>
                <option value="Cardiac Troponin I (STAT)">Cardiac Troponin I (STAT)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Priority Level</label>
              <select value={priority} onChange={(e) => setPriority(e.target.value)} className="form-select">
                <option value="ROUTINE">Routine (48h SLA)</option>
                <option value="URGENT">Urgent / STAT (12h SLA)</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Ordering Physician</label>
            <select value={doctor} onChange={(e) => setDoctor(e.target.value)} className="form-select">
              <option value="Dr. Sarah Jenkins">Dr. Sarah Jenkins (Internal Medicine)</option>
              <option value="Dr. Marcus Vance">Dr. Marcus Vance (Cardiology)</option>
              <option value="Dr. Elena Rostova">Dr. Elena Rostova (Endocrinology)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Clinical Indication / Reason for Test</label>
            <input 
              type="text"
              placeholder="e.g. Fatigue, elevated blood pressure, routine diabetic screening"
              value={indication}
              onChange={(e) => setIndication(e.target.value)}
              className="form-input"
              required
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              <CheckCircle2 size={16} /> {loading ? 'Placing Order...' : 'Submit Order to Lab'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
