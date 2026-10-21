import React, { useState } from 'react';
import { X, Upload } from 'lucide-react';
import { api } from '../../api';

export default function SimulateReportModal({ order, onClose, onSuccess }) {
  const [resultType, setResultType] = useState('NORMAL'); // NORMAL, ABNORMAL, CRITICAL
  const [loading, setLoading] = useState(false);

  if (!order) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData();
    formData.append('order_id', order.id);
    formData.append('test_type', order.test_name);
    formData.append('has_abnormal', resultType !== 'NORMAL');
    formData.append('has_critical', resultType === 'CRITICAL');

    try {
      await api.simulateUploadReport(formData);
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      alert("Error ingesting report.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff7ed' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Upload size={20} color="#ea580c" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>Ingest / Receive Diagnostic Report</h2>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '8px', fontSize: '0.86rem', border: '1px solid #e2e8f0' }}>
            <div>Order: <strong style={{ color: '#ea580c' }}>{order.order_code}</strong> ({order.test_name})</div>
            <div style={{ marginTop: '4px' }}>Patient: <strong style={{ color: '#0f172a' }}>{order.patient_name}</strong> ({order.patient_mrn})</div>
          </div>

          <div className="form-group">
            <label className="form-label">Simulate Diagnostic Lab Result</label>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '6px' }}>
              
              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px', 
                borderRadius: '8px', 
                background: resultType === 'NORMAL' ? '#ecfdf5' : '#ffffff',
                border: `1px solid ${resultType === 'NORMAL' ? '#a7f3d0' : '#e2e8f0'}`,
                cursor: 'pointer'
              }}>
                <input 
                  type="radio" 
                  name="resType" 
                  value="NORMAL" 
                  checked={resultType === 'NORMAL'} 
                  onChange={() => setResultType('NORMAL')} 
                />
                <div>
                  <div style={{ fontWeight: 700, color: '#047857' }}>Normal / Negative Findings</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>All parameters within standard clinical reference limits (Routine 48h review).</div>
                </div>
              </label>

              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px', 
                borderRadius: '8px', 
                background: resultType === 'ABNORMAL' ? '#fff7ed' : '#ffffff',
                border: `1px solid ${resultType === 'ABNORMAL' ? '#fed7aa' : '#e2e8f0'}`,
                cursor: 'pointer'
              }}>
                <input 
                  type="radio" 
                  name="resType" 
                  value="ABNORMAL" 
                  checked={resultType === 'ABNORMAL'} 
                  onChange={() => setResultType('ABNORMAL')} 
                />
                <div>
                  <div style={{ fontWeight: 700, color: '#c2410c' }}>Abnormal Lab Result</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Flagged out-of-range values (e.g. High Lipids, Anemia, Elevated HbA1c).</div>
                </div>
              </label>

              <label style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '12px', 
                padding: '12px', 
                borderRadius: '8px', 
                background: resultType === 'CRITICAL' ? '#fff1f2' : '#ffffff',
                border: `1px solid ${resultType === 'CRITICAL' ? '#fecdd3' : '#e2e8f0'}`,
                cursor: 'pointer'
              }}>
                <input 
                  type="radio" 
                  name="resType" 
                  value="CRITICAL" 
                  checked={resultType === 'CRITICAL'} 
                  onChange={() => setResultType('CRITICAL')} 
                />
                <div>
                  <div style={{ fontWeight: 700, color: '#be123c' }}>Panic / Critical Lab Value</div>
                  <div style={{ fontSize: '0.78rem', color: '#64748b' }}>Life-threatening out-of-range (e.g. Critical Thrombocytopenia, Potassium 6.4). Triggers instant Alert!</div>
                </div>
              </label>

            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              <Upload size={16} /> {loading ? 'Ingesting...' : 'Ingest Report & Start SLA'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
