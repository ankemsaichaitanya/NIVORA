import React, { useState } from 'react';
import { 
  Users, 
  Search, 
  Plus, 
  Calendar, 
  Phone, 
  Mail, 
  ChevronRight, 
  History, 
  X,
  Sparkles,
  CheckCircle2,
  Clock
} from 'lucide-react';
import { api } from '../api';

export default function PatientsPage({ patients, onOpenAddPatient, onSelectPatientForAI }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedPatientHistory, setSelectedPatientHistory] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const filteredPatients = patients?.filter(p => 
    p.first_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.last_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.mrn.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const viewHistory = async (patientId) => {
    setLoadingHistory(true);
    try {
      const res = await api.getPatientHistory(patientId);
      setSelectedPatientHistory(res.data);
    } catch (err) {
      console.error("Error loading patient history:", err);
    } finally {
      setLoadingHistory(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>Patient Registry & History</h1>
          <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
            Maintain patient profiles, clinical orders, and longitudinal closed-loop audit trails.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          {/* Search Box */}
          <div style={{ position: 'relative', minWidth: '280px' }}>
            <Search size={16} color="#94a3b8" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
            <input 
              type="text" 
              placeholder="Search by Name or MRN..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input"
              style={{ paddingLeft: '36px', height: '40px' }}
            />
          </div>

          <button onClick={onOpenAddPatient} className="btn btn-primary" style={{ height: '40px' }}>
            <Plus size={16} /> Add Patient
          </button>
        </div>
      </div>

      {/* Patient Cards Grid (Clean White with Neat Details) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '18px' }}>
        {filteredPatients?.map(patient => (
          <div key={patient.id} className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', justifyContent: 'space-between', gap: '16px' }}>
            
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <div>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#0f172a' }}>
                    {patient.first_name} {patient.last_name}
                  </h3>
                  <span style={{ fontSize: '0.78rem', color: '#ea580c', fontFamily: 'var(--font-mono)', fontWeight: 700 }}>
                    {patient.mrn}
                  </span>
                </div>
                <span className="badge" style={{ background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0' }}>
                  {patient.gender}
                </span>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.82rem', color: '#475569', marginTop: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Calendar size={14} color="#94a3b8" />
                  <span>DOB: {patient.dob}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Phone size={14} color="#94a3b8" />
                  <span>{patient.phone}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <Mail size={14} color="#94a3b8" />
                  <span>{patient.email || 'No email on record'}</span>
                </div>
              </div>

              <div style={{ marginTop: '14px', paddingTop: '10px', borderTop: '1px solid #f1f5f9', fontSize: '0.78rem', color: '#64748b' }}>
                Attending: <span style={{ color: '#0f172a', fontWeight: 600 }}>{patient.primary_doctor}</span>
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => viewHistory(patient.id)}
                className="btn btn-secondary"
                style={{ flex: 1, justifyContent: 'center', fontSize: '0.8rem', padding: '8px 12px' }}
              >
                <History size={14} color="#ea580c" /> Workflow History
              </button>

              <button 
                onClick={() => onSelectPatientForAI(patient.id)}
                className="btn btn-orange-outline"
                title="AI Summary & Chat for this patient"
                style={{ padding: '8px 12px' }}
              >
                <Sparkles size={14} />
              </button>
            </div>

          </div>
        ))}
      </div>

      {/* Patient History Modal */}
      {selectedPatientHistory && (
        <div className="modal-overlay" onClick={() => setSelectedPatientHistory(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '750px' }}>
            
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff7ed' }}>
              <div>
                <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>
                  {selectedPatientHistory.patient.first_name} {selectedPatientHistory.patient.last_name}
                </h2>
                <div style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 600 }}>
                  {selectedPatientHistory.patient.mrn} • {selectedPatientHistory.patient.gender} • DOB: {selectedPatientHistory.patient.dob}
                </div>
              </div>
              <button onClick={() => setSelectedPatientHistory(null)} className="btn btn-secondary" style={{ padding: '6px' }}>
                <X size={18} />
              </button>
            </div>

            <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <History size={17} color="#ea580c" /> Longitudinal Workflow Timeline
              </h3>

              {selectedPatientHistory.orders?.length === 0 ? (
                <div style={{ textAlign: 'center', color: '#64748b', padding: '20px' }}>
                  No diagnostic test orders recorded for this patient yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {selectedPatientHistory.orders.map((ord) => (
                    <div key={ord.id} style={{ 
                      background: '#ffffff', 
                      border: '1px solid #e2e8f0', 
                      borderRadius: 'var(--radius-md)', 
                      padding: '16px',
                      boxShadow: 'var(--shadow-subtle)'
                    }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                        <div>
                          <span style={{ fontWeight: 800, color: '#0f172a', fontSize: '0.95rem' }}>{ord.test_name}</span>
                          <span style={{ fontSize: '0.75rem', color: '#ea580c', marginLeft: '8px', fontWeight: 600 }}>({ord.order_code})</span>
                        </div>
                        <span className={`badge ${
                          ord.status === 'CLOSED' ? 'badge-closed' :
                          ord.status === 'PENDING_REVIEW' ? 'badge-pending' :
                          ord.status === 'REVIEWED' ? 'badge-reviewed' : 'badge-ordered'
                        }`}>
                          {ord.status.replace('_', ' ')}
                        </span>
                      </div>

                      {/* Step Progress Tracker */}
                      <div style={{ 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'space-between', 
                        background: '#f8fafc', 
                        padding: '10px 14px', 
                        borderRadius: '8px', 
                        margin: '10px 0',
                        fontSize: '0.75rem',
                        border: '1px solid #e2e8f0'
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#0284c7', fontWeight: 600 }}>
                          <CheckCircle2 size={14} /> 1. Ordered
                        </div>
                        <ChevronRight size={14} color="#94a3b8" />
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: ord.report ? '#ea580c' : '#94a3b8', fontWeight: ord.report ? 700 : 500 }}>
                          {ord.report ? <CheckCircle2 size={14} /> : <Clock size={14} />} 2. Report Arrived
                        </div>
                        <ChevronRight size={14} color="#94a3b8" />
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: ord.review_task?.reviewed_at ? '#7c3aed' : '#94a3b8', fontWeight: ord.review_task?.reviewed_at ? 700 : 500 }}>
                          {ord.review_task?.reviewed_at ? <CheckCircle2 size={14} /> : <Clock size={14} />} 3. Doctor Review
                        </div>
                        <ChevronRight size={14} color="#94a3b8" />
                        <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: ord.status === 'CLOSED' ? '#059669' : '#94a3b8', fontWeight: ord.status === 'CLOSED' ? 700 : 500 }}>
                          {ord.status === 'CLOSED' ? <CheckCircle2 size={14} /> : <Clock size={14} />} 4. Loop Closed
                        </div>
                      </div>

                      {/* Report summary if present */}
                      {ord.report && (
                        <div style={{ marginTop: '8px', fontSize: '0.82rem', color: ord.report.has_critical_values ? '#be123c' : '#334155' }}>
                          <strong style={{ color: '#0f172a' }}>Lab Findings:</strong> {ord.report.result_summary}
                        </div>
                      )}

                      {/* Doctor notes if present */}
                      {ord.review_task?.doctor_notes && (
                        <div style={{ marginTop: '6px', fontSize: '0.82rem', color: '#6d28d9' }}>
                          <strong>Doctor Action ({ord.review_task.next_action_type}):</strong> {ord.review_task.action_details}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

            </div>
          </div>
        </div>
      )}

    </div>
  );
}
