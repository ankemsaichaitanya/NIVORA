import React from 'react';
import { 
  Activity, 
  Users, 
  FlaskConical, 
  Bell, 
  Bot, 
  Cpu,
  Plus, 
  RefreshCw
} from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onOpenOrderModal, onOpenPatientModal, onTriggerSla, slaScanning }) {
  const navItems = [
    { id: 'dashboard', label: 'Doctor Dashboard', icon: Activity },
    { id: 'patients', label: 'Patients', icon: Users },
    { id: 'tests', label: 'Test & Reports', icon: FlaskConical },
    { id: 'ckd', label: 'CKD AI Detector', icon: Cpu, isSpecial: true },
    { id: 'alerts', label: 'Alerts & SLA', icon: Bell },
    { id: 'ai', label: 'AI Assistant', icon: Bot, isAi: true }
  ];

  return (
    <header className="glass-nav" style={{ position: 'sticky', top: 0, zIndex: 100 }}>
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '12px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '16px' }}>
        
        {/* Brand with Medical Orange Accent */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ 
            width: '40px', 
            height: '40px', 
            borderRadius: '10px', 
            background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
            display: 'flex', 
            alignItems: 'center', 
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(249, 115, 22, 0.3)'
          }}>
            <Activity size={22} color="#ffffff" />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '1.25rem', fontWeight: 800, letterSpacing: '-0.02em', color: '#0f172a' }}>CareLoop</span>
              <span style={{ fontSize: '0.72rem', background: '#fff7ed', color: '#ea580c', border: '1px solid #fed7aa', padding: '2px 8px', borderRadius: '4px', fontWeight: 700 }}>
                NIVORA
              </span>
            </div>
            <div style={{ fontSize: '0.74rem', color: '#64748b', fontWeight: 500 }}>
              Clinical Closed-Loop Diagnostic Tracking
            </div>
          </div>
        </div>

        {/* Navigation Tabs (Clean Pill Group) */}
        <nav style={{ 
          display: 'flex', 
          gap: '4px', 
          background: '#f1f5f9', 
          padding: '4px', 
          borderRadius: '12px', 
          border: '1px solid #e2e8f0' 
        }}>
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button 
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className="btn"
                style={{ 
                  padding: '7px 14px', 
                  fontSize: '0.82rem',
                  background: isActive 
                    ? item.isAi ? 'linear-gradient(135deg, #f97316 0%, #8b5cf6 100%)' : 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)'
                    : 'transparent',
                  color: isActive ? '#ffffff' : '#475569',
                  boxShadow: isActive ? '0 2px 8px rgba(249, 115, 22, 0.25)' : 'none',
                  border: 'none',
                  borderRadius: '8px'
                }}
              >
                <Icon size={15} color={isActive ? '#ffffff' : (item.isAi ? '#ea580c' : '#64748b')} /> 
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button 
            onClick={onTriggerSla} 
            className="btn btn-secondary" 
            title="Force immediate check of SLA deadlines"
            style={{ fontSize: '0.8rem', padding: '7px 12px' }}
          >
            <RefreshCw size={13} color="#ea580c" className={slaScanning ? 'animate-spin' : ''} />
            {slaScanning ? 'Scanning...' : 'SLA Scan'}
          </button>

          <button 
            onClick={onOpenPatientModal} 
            className="btn btn-secondary"
            style={{ fontSize: '0.82rem', padding: '7px 13px' }}
          >
            <Plus size={14} color="#0f172a" /> Add Patient
          </button>

          <button 
            onClick={onOpenOrderModal} 
            className="btn btn-primary"
            style={{ fontSize: '0.82rem', padding: '7px 14px' }}
          >
            <Plus size={14} /> Order Blood Test
          </button>
        </div>

      </div>
    </header>
  );
}
