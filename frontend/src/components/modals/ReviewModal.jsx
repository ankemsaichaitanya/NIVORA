import React, { useState } from 'react';
import { X, CheckCircle2, AlertTriangle, FileText } from 'lucide-react';
import { api } from '../../api';

export default function ReviewModal({ task, onClose, onSuccess }) {
  const [notes, setNotes] = useState('');
  const [actionType, setActionType] = useState('MEDICATION_CHANGE');
  const [actionDetails, setActionDetails] = useState('');
  const [deadlineDays, setDeadlineDays] = useState(7);
  const [loading, setLoading] = useState(false);

  if (!task) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.submitDoctorReview(task.task_id, {
        doctor_notes: notes || "Physician verified lab values and recorded plan.",
        next_action_type: actionType,
        action_details: actionDetails || (actionType === 'ROUTINE_OK' ? 'Routine clearance - loop closed.' : 'Scheduled follow-up.'),
        action_deadline_days: parseInt(deadlineDays)
      });
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      alert("Error submitting review. Please check console.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        {/* Header */}
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff7ed' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>Physician Report Sign-Off</h2>
            <div style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 600 }}>
              Patient: {task.patient_name} ({task.patient_mrn}) • Test: {task.test_name}
            </div>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        {/* Lab Findings Callout */}
        <div style={{ padding: '18px 24px', background: task.has_critical ? '#fff1f2' : '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            {task.has_critical ? <AlertTriangle size={18} color="#e11d48" /> : <FileText size={18} color="#ea580c" />}
            <span style={{ fontWeight: 800, color: task.has_critical ? '#9f1239' : '#0f172a', fontSize: '0.9rem' }}>
              Laboratory Findings & Summary
            </span>
          </div>
          <p style={{ fontSize: '0.86rem', color: task.has_critical ? '#be123c' : '#334155', lineHeight: '1.5' }}>
            {task.result_summary}
          </p>
        </div>

        {/* Review Form */}
        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div className="form-group">
            <label className="form-label">Doctor Clinical Impression & Assessment</label>
            <textarea 
              rows={3}
              placeholder="e.g. Findings indicate mild microcytic anemia secondary to iron deficiency..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              className="form-textarea"
              required
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Mandated Next Action Step</label>
              <select 
                value={actionType} 
                onChange={(e) => setActionType(e.target.value)}
                className="form-select"
              >
                <option value="MEDICATION_CHANGE">Adjust Medication / Prescription</option>
                <option value="SPECIALIST_REFERRAL">Specialist Physician Referral</option>
                <option value="REPEAT_TEST">Order Repeat Diagnostic Test</option>
                <option value="ROUTINE_OK">Routine Clearance (Close Loop Immediately)</option>
              </select>
            </div>

            {actionType !== 'ROUTINE_OK' && (
              <div className="form-group">
                <label className="form-label">Follow-up SLA Timeframe (Days)</label>
                <input 
                  type="number"
                  min="1"
                  max="90"
                  value={deadlineDays}
                  onChange={(e) => setDeadlineDays(e.target.value)}
                  className="form-input"
                  required
                />
              </div>
            )}
          </div>

          {actionType !== 'ROUTINE_OK' && (
            <div className="form-group">
              <label className="form-label">Action Details for Clinic Staff & Patient</label>
              <input 
                type="text"
                placeholder="e.g. Start Ferrous Sulfate 325mg daily, repeat CBC in 60 days"
                value={actionDetails}
                onChange={(e) => setActionDetails(e.target.value)}
                className="form-input"
                required
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              <CheckCircle2 size={16} /> {loading ? 'Submitting...' : 'Sign Off & Track Next Step'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
