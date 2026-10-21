import React, { useState } from 'react';
import { 
  Bell, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  RefreshCw, 
  Info,
  ShieldCheck
} from 'lucide-react';

export default function AlertsPage({ alerts, onResolveAlert, onTriggerSla, slaScanning }) {
  const [filterUnresolved, setFilterUnresolved] = useState(false);

  const displayedAlerts = filterUnresolved 
    ? alerts?.filter(a => !a.is_resolved) 
    : alerts;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>Alerts & SLA Automation Engine</h1>
          <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
            Module 4: Identify overdue tasks, notify responsible clinic staff, and prevent patient care gaps.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setFilterUnresolved(!filterUnresolved)}
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem' }}
          >
            {filterUnresolved ? 'Show All Alerts' : 'Filter Unresolved Only'}
          </button>

          <button 
            onClick={onTriggerSla} 
            className="btn btn-primary"
            style={{ fontSize: '0.82rem' }}
          >
            <RefreshCw size={14} className={slaScanning ? 'animate-spin' : ''} />
            {slaScanning ? 'Scanning Engine...' : 'Run SLA Overdue Scan'}
          </button>
        </div>
      </div>

      {/* SLA Policy Architecture Card (Clean White with Orange Details) */}
      <div className="glass-panel" style={{ padding: '20px 24px', background: '#fff7ed', borderColor: '#fed7aa' }}>
        <h3 style={{ fontSize: '0.96rem', fontWeight: 800, color: '#c2410c', display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
          <Info size={17} color="#ea580c" /> Automated SLA Policies & Escalation Matrix
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '14px', fontSize: '0.82rem' }}>
          <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #ea580c', border: '1px solid #fed7aa', borderLeftWidth: '4px' }}>
            <div style={{ fontWeight: 800, color: '#0f172a' }}>Routine Blood Tests</div>
            <div style={{ color: '#64748b', marginTop: '4px', lineHeight: '1.4' }}>48-hour physician review SLA. If unreviewed, escalated to High Priority Alert.</div>
          </div>
          <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #d97706', border: '1px solid #fde68a', borderLeftWidth: '4px' }}>
            <div style={{ fontWeight: 800, color: '#0f172a' }}>Urgent / STAT Orders</div>
            <div style={{ color: '#64748b', marginTop: '4px', lineHeight: '1.4' }}>12-hour review deadline. Responsible doctor pinged at 6-hour halfway mark.</div>
          </div>
          <div style={{ background: '#ffffff', padding: '14px', borderRadius: '8px', borderLeft: '4px solid #e11d48', border: '1px solid #fecdd3', borderLeftWidth: '4px' }}>
            <div style={{ fontWeight: 800, color: '#0f172a' }}>Panic / Critical Lab Values</div>
            <div style={{ color: '#64748b', marginTop: '4px', lineHeight: '1.4' }}>Immediate CRITICAL Alert triggered on arrival. 2-hour physician sign-off threshold.</div>
          </div>
        </div>
      </div>

      {/* Alerts Feed */}
      <div className="glass-panel" style={{ padding: '24px' }}>
        <h2 style={{ fontSize: '1.15rem', fontWeight: 800, color: '#0f172a', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Bell size={18} color="#ea580c" /> Active Alert Stream ({displayedAlerts?.length || 0})
        </h2>

        {displayedAlerts?.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '36px', color: '#64748b' }}>
            <ShieldCheck size={36} color="#059669" style={{ margin: '0 auto 10px' }} />
            <div style={{ fontWeight: 700, color: '#0f172a' }}>No Active Alerts</div>
            <div style={{ fontSize: '0.84rem' }}>All clinical tasks are currently adhering to their respective turnaround SLAs.</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {displayedAlerts?.map(alert => (
              <div 
                key={alert.id}
                style={{
                  background: alert.is_resolved 
                    ? '#f8fafc' 
                    : alert.severity === 'CRITICAL' 
                      ? '#fff1f2' 
                      : '#fff7ed',
                  border: `1px solid ${
                    alert.is_resolved 
                      ? '#e2e8f0' 
                      : alert.severity === 'CRITICAL' 
                        ? '#fecdd3' 
                        : '#fed7aa'
                  }`,
                  borderRadius: 'var(--radius-md)',
                  padding: '16px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '16px',
                  boxShadow: 'var(--shadow-subtle)'
                }}
              >
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                  <div style={{ marginTop: '2px' }}>
                    {alert.severity === 'CRITICAL' ? (
                      <AlertTriangle size={20} color="#e11d48" />
                    ) : alert.is_resolved ? (
                      <CheckCircle2 size={20} color="#059669" />
                    ) : (
                      <Clock size={20} color="#ea580c" />
                    )}
                  </div>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                      <span className={`badge ${
                        alert.severity === 'CRITICAL' ? 'badge-critical' :
                        alert.severity === 'HIGH' ? 'badge-overdue' : 'badge-pending'
                      }`}>
                        {alert.alert_type.replace('_', ' ')}
                      </span>
                      <span style={{ fontSize: '0.74rem', color: '#64748b' }}>
                        Triggered: {new Date(alert.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div style={{ 
                      fontSize: '0.88rem', 
                      color: alert.is_resolved ? '#94a3b8' : '#0f172a', 
                      fontWeight: alert.is_resolved ? 400 : 600,
                      textDecoration: alert.is_resolved ? 'line-through' : 'none' 
                    }}>
                      {alert.message}
                    </div>
                    {alert.is_resolved && (
                      <div style={{ fontSize: '0.74rem', color: '#059669', marginTop: '4px', fontWeight: 600 }}>
                        ✓ Resolved by {alert.resolved_by} on {new Date(alert.resolved_at).toLocaleString()}
                      </div>
                    )}
                  </div>
                </div>

                <div>
                  {!alert.is_resolved ? (
                    <button 
                      onClick={() => onResolveAlert(alert.id)}
                      className="btn btn-secondary"
                      style={{ fontSize: '0.8rem', padding: '6px 14px' }}
                    >
                      <CheckCircle2 size={14} color="#059669" /> Mark Resolved
                    </button>
                  ) : (
                    <span className="badge badge-closed">RESOLVED</span>
                  )}
                </div>

              </div>
            ))}
          </div>
        )}

      </div>

    </div>
  );
}
