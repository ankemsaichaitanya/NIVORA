import React from 'react';
import { 
  AlertTriangle, 
  Clock, 
  CheckCircle2, 
  Activity, 
  FileText, 
  ShieldAlert, 
  Stethoscope,
  Sparkles,
  Flame,
  ArrowUpRight
} from 'lucide-react';

export default function DoctorDashboard({ 
  stats, 
  pendingReports, 
  followups, 
  onReviewTask, 
  onCompleteFollowup,
  onOpenAIDraft,
  refreshData 
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Welcome Banner (Clean White with Warm Orange Glow) */}
      <div className="glass-panel" style={{ 
        padding: '24px 28px', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        background: 'linear-gradient(135deg, #fff7ed 0%, #ffffff 60%)',
        borderColor: '#fed7aa'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
            <span style={{ 
              fontSize: '0.76rem', 
              background: '#ea580c', 
              color: '#ffffff', 
              padding: '2px 8px', 
              borderRadius: '4px', 
              fontWeight: 700,
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              <Flame size={12} /> Active Physician Worklist
            </span>
            <span style={{ color: '#64748b', fontSize: '0.8rem', fontWeight: 500 }}>
              • Metro Health Clinic Closed-Loop Tracker
            </span>
          </div>
          <h1 style={{ fontSize: '1.65rem', fontWeight: 800, color: '#0f172a', letterSpacing: '-0.02em' }}>
            Diagnostic Review & Follow-up Center
          </h1>
          <p style={{ color: '#475569', fontSize: '0.9rem', marginTop: '4px' }}>
            Tracking arrived lab results, monitoring turnaround SLAs, and ensuring zero diagnostic reports are left unreviewed.
          </p>
        </div>

        {/* Loop Closed Rate Badge */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '16px', 
          background: '#ffffff', 
          padding: '14px 20px', 
          borderRadius: '12px', 
          border: '1px solid #fed7aa',
          boxShadow: '0 2px 8px rgba(249, 115, 22, 0.08)'
        }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '0.7rem', color: '#9a3412', textTransform: 'uppercase', fontWeight: 700 }}>
              Loop Closed Rate
            </div>
            <div style={{ fontSize: '1.45rem', fontWeight: 800, color: '#ea580c' }}>
              {stats?.total_orders ? Math.round((stats.closed_loops / stats.total_orders) * 100) : 0}%
            </div>
          </div>
          <div style={{ width: '1px', height: '34px', background: '#fed7aa' }}></div>
          <div style={{ fontSize: '0.75rem', color: '#64748b', maxWidth: '160px', lineHeight: '1.4' }}>
            Continuous tracking from test order to confirmed clinical follow-up.
          </div>
        </div>
      </div>

      {/* Metric Cards (Module 1 Dashboard Stats) */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        
        <div className="stat-card cyan">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 700 }}>TOTAL ORDERS</span>
            <Activity size={18} color="#0284c7" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#0f172a' }}>{stats?.total_orders || 0}</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Diagnostic tests registered</div>
        </div>

        <div className="stat-card orange">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#ea580c', fontWeight: 700 }}>PENDING REVIEW</span>
            <Clock size={18} color="#ea580c" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#ea580c' }}>{stats?.pending_doctor_review || 0}</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Arrived reports waiting for MD</div>
        </div>

        <div className="stat-card rose">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#dc2626', fontWeight: 700 }}>SLA BREACHES</span>
            <ShieldAlert size={18} color="#dc2626" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#dc2626' }}>{stats?.overdue_tasks || 0}</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Exceeded 48h turnaround SLA</div>
        </div>

        <div className="stat-card purple">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#7c3aed', fontWeight: 700 }}>ACTIVE FOLLOW-UPS</span>
            <Stethoscope size={18} color="#7c3aed" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#7c3aed' }}>{stats?.active_follow_ups || 0}</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Med adjustments & referrals</div>
        </div>

        <div className="stat-card emerald">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.8rem', color: '#059669', fontWeight: 700 }}>CARE LOOPS CLOSED</span>
            <CheckCircle2 size={18} color="#059669" />
          </div>
          <div style={{ fontSize: '2rem', fontWeight: 800, color: '#059669' }}>{stats?.closed_loops || 0}</div>
          <div style={{ fontSize: '0.75rem', color: '#64748b' }}>100% resolved & audited</div>
        </div>

      </div>

      {/* Critical Alerts Banner (If Any) */}
      {stats?.critical_alerts > 0 && (
        <div style={{ 
          background: '#fff1f2', 
          border: '1px solid #fecdd3', 
          padding: '16px 20px', 
          borderRadius: 'var(--radius-md)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          boxShadow: '0 2px 6px rgba(225, 29, 72, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
            <AlertTriangle size={24} color="#e11d48" className="animate-pulse" />
            <div>
              <div style={{ fontWeight: 800, color: '#9f1239', fontSize: '0.92rem' }}>
                {stats.critical_alerts} CRITICAL / PANIC LAB VALUE(S) FLAGGED
              </div>
              <div style={{ fontSize: '0.82rem', color: '#be123c', marginTop: '2px' }}>
                Immediate physician intervention needed. High-risk lab values require patient contact.
              </div>
            </div>
          </div>
          <span className="badge badge-critical">IMMEDIATE ATTENTION</span>
        </div>
      )}

      {/* Section 1: Pending Lab Reports (Module 1 Core) */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={19} color="#ea580c" /> Pending Lab Reports Awaiting Review
            </h2>
            <p style={{ fontSize: '0.84rem', color: '#64748b', marginTop: '2px' }}>
              Verify findings, record clinical impressions, and document the follow-up step to close the loop.
            </p>
          </div>
          <span className="badge badge-pending">
            {pendingReports?.length || 0} Awaiting Doctor Action
          </span>
        </div>

        {pendingReports?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 20px', color: '#64748b' }}>
            <CheckCircle2 size={36} color="#10b981" style={{ margin: '0 auto 12px' }} />
            <div style={{ fontWeight: 700, color: '#0f172a' }}>All Caught Up!</div>
            <div style={{ fontSize: '0.85rem' }}>No pending reports currently waiting for physician review.</div>
          </div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Diagnostic Test</th>
                  <th>Lab Findings / Summary</th>
                  <th>Assigned Physician</th>
                  <th>Turnaround SLA</th>
                  <th style={{ textAlign: 'right' }}>Action</th>
                </tr>
              </thead>
              <tbody>
                {pendingReports?.map((report) => (
                  <tr key={report.task_id} style={{ background: report.has_critical ? '#fff1f2' : undefined }}>
                    
                    {/* Patient */}
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{report.patient_name}</div>
                      <div style={{ fontSize: '0.76rem', color: '#64748b' }}>
                        {report.patient_mrn} • {report.patient_phone}
                      </div>
                    </td>

                    {/* Test */}
                    <td>
                      <div style={{ fontWeight: 600, color: '#1e293b' }}>{report.test_name}</div>
                      <div style={{ display: 'flex', gap: '6px', marginTop: '4px' }}>
                        {report.priority === 'URGENT' && <span className="badge badge-critical" style={{ fontSize: '0.64rem' }}>STAT</span>}
                        {report.has_critical && <span className="badge badge-critical" style={{ fontSize: '0.64rem' }}>PANIC VALUE</span>}
                        {report.has_abnormal && !report.has_critical && <span className="badge badge-pending" style={{ fontSize: '0.64rem' }}>ABNORMAL</span>}
                      </div>
                    </td>

                    {/* Findings */}
                    <td style={{ maxWidth: '320px' }}>
                      <div style={{ 
                        fontSize: '0.82rem', 
                        color: report.has_critical ? '#be123c' : report.has_abnormal ? '#c2410c' : '#475569',
                        fontWeight: report.has_critical || report.has_abnormal ? 600 : 400
                      }}>
                        {report.result_summary}
                      </div>
                    </td>

                    {/* Doctor */}
                    <td style={{ fontSize: '0.84rem', color: '#475569', fontWeight: 500 }}>
                      {report.assigned_doctor}
                    </td>

                    {/* SLA Status */}
                    <td>
                      {report.is_overdue ? (
                        <span className="badge badge-overdue">
                          <AlertTriangle size={12} /> OVERDUE ({Math.abs(report.hours_left)}h)
                        </span>
                      ) : (
                        <span className="badge badge-pending">
                          <Clock size={12} /> {report.hours_left}h left
                        </span>
                      )}
                    </td>

                    {/* Action */}
                    <td style={{ textAlign: 'right' }}>
                      <button 
                        onClick={() => onReviewTask(report)}
                        className="btn btn-primary"
                        style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                      >
                        <FileText size={14} /> Review & Action
                      </button>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Section 2: Active Follow-ups & Referrals (Module 1 & 4) */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Stethoscope size={19} color="#7c3aed" /> Active Follow-ups & Unresolved Referrals
            </h2>
            <p style={{ fontSize: '0.84rem', color: '#64748b', marginTop: '2px' }}>
              Ongoing patient instructions being tracked by clinic staff until verified complete.
            </p>
          </div>
          <span className="badge badge-reviewed">{followups?.length || 0} TRACKING</span>
        </div>

        {followups?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px 20px', color: '#64748b' }}>
            No active follow-ups. All ordered recommendations have reached completion!
          </div>
        ) : (
          <div className="table-container">
            <table className="custom-table">
              <thead>
                <tr>
                  <th>Patient</th>
                  <th>Originating Test</th>
                  <th>Action Category</th>
                  <th>Specific Instructions</th>
                  <th>Target Deadline</th>
                  <th style={{ textAlign: 'right' }}>Resolution & AI</th>
                </tr>
              </thead>
              <tbody>
                {followups?.map((item) => (
                  <tr key={item.task_id}>
                    
                    <td>
                      <div style={{ fontWeight: 700, color: '#0f172a' }}>{item.patient_name}</div>
                      <div style={{ fontSize: '0.74rem', color: '#64748b' }}>{item.patient_mrn}</div>
                    </td>

                    <td style={{ fontSize: '0.85rem', color: '#334155', fontWeight: 500 }}>
                      {item.test_name}
                    </td>

                    <td>
                      <span className="badge badge-reviewed" style={{ fontSize: '0.7rem' }}>
                        {item.next_action_type?.replace('_', ' ')}
                      </span>
                    </td>

                    <td style={{ maxWidth: '300px', fontSize: '0.83rem', color: '#334155' }}>
                      {item.action_details}
                    </td>

                    <td>
                      {item.is_past_due ? (
                        <span className="badge badge-overdue">
                          PAST DUE ({Math.abs(item.days_remaining)}d)
                        </span>
                      ) : (
                        <span style={{ fontSize: '0.82rem', color: '#64748b', fontWeight: 600 }}>
                          Due in {item.days_remaining} days
                        </span>
                      )}
                    </td>

                    <td style={{ textAlign: 'right' }}>
                      <div style={{ display: 'inline-flex', gap: '8px' }}>
                        <button 
                          onClick={() => onOpenAIDraft(item)}
                          className="btn btn-orange-outline"
                          title="Auto-draft WhatsApp/SMS patient reminder"
                          style={{ padding: '6px 11px', fontSize: '0.78rem' }}
                        >
                          <Sparkles size={13} color="#ea580c" /> AI Reminder
                        </button>

                        <button 
                          onClick={() => onCompleteFollowup(item.task_id)}
                          className="btn btn-success"
                          style={{ padding: '6px 13px', fontSize: '0.78rem' }}
                        >
                          <CheckCircle2 size={13} /> Complete & Close
                        </button>
                      </div>
                    </td>

                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
  );
}
