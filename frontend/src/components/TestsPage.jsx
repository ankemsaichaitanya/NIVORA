import React, { useState } from 'react';
import { 
  FlaskConical, 
  Plus, 
  Upload, 
  CheckCircle2, 
  Clock, 
  Search,
  FileCheck
} from 'lucide-react';

export default function TestsPage({ 
  orders, 
  onOpenOrderModal, 
  onOpenSimulateReport 
}) {
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  const filteredOrders = orders?.filter(o => {
    const matchesStatus = filterStatus === 'ALL' || o.status === filterStatus;
    const matchesSearch = 
      o.patient_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.test_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      o.order_code?.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesStatus && matchesSearch;
  });

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '14px' }}>
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>Diagnostic Test & Report Tracking</h1>
          <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
            Module 3: Record ordered tests, simulate incoming reports, track physician review status and follow-ups.
          </p>
        </div>

        <button onClick={onOpenOrderModal} className="btn btn-primary">
          <Plus size={16} /> Order New Blood Test
        </button>
      </div>

      {/* Filter and Search Bar (Clean White Card) */}
      <div className="glass-panel" style={{ padding: '14px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        
        {/* Status Pill Filters */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['ALL', 'ORDERED', 'PENDING_REVIEW', 'REVIEWED', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => setFilterStatus(st)}
              className="btn"
              style={{
                padding: '6px 14px',
                fontSize: '0.8rem',
                fontWeight: 700,
                background: filterStatus === st ? 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' : '#f8fafc',
                color: filterStatus === st ? '#ffffff' : '#475569',
                borderColor: filterStatus === st ? '#ea580c' : '#e2e8f0',
                boxShadow: filterStatus === st ? '0 2px 6px rgba(249, 115, 22, 0.25)' : 'none'
              }}
            >
              {st === 'ALL' ? 'All Orders' : st.replace('_', ' ')}
            </button>
          ))}
        </div>

        {/* Search */}
        <div style={{ position: 'relative', minWidth: '260px' }}>
          <Search size={15} color="#94a3b8" style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)' }} />
          <input 
            type="text"
            placeholder="Search test or patient..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="form-input"
            style={{ paddingLeft: '32px', height: '36px', fontSize: '0.84rem' }}
          />
        </div>

      </div>

      {/* Orders Table */}
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div className="table-container">
          <table className="custom-table">
            <thead>
              <tr>
                <th>Order Code</th>
                <th>Patient</th>
                <th>Test & Category</th>
                <th>Ordering Physician</th>
                <th>Workflow Status</th>
                <th>Report Arrival</th>
                <th style={{ textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredOrders?.map(order => (
                <tr key={order.id}>
                  
                  {/* Order Code */}
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700, color: '#ea580c', fontSize: '0.84rem' }}>
                    {order.order_code}
                  </td>

                  {/* Patient */}
                  <td>
                    <div style={{ fontWeight: 700, color: '#0f172a' }}>{order.patient_name}</div>
                    <div style={{ fontSize: '0.74rem', color: '#64748b' }}>{order.patient_mrn}</div>
                  </td>

                  {/* Test Name */}
                  <td>
                    <div style={{ fontWeight: 600, color: '#1e293b' }}>{order.test_name}</div>
                    <div style={{ fontSize: '0.74rem', color: '#64748b' }}>{order.test_category}</div>
                  </td>

                  {/* Doctor */}
                  <td style={{ fontSize: '0.82rem', color: '#475569', fontWeight: 500 }}>
                    {order.ordering_doctor}
                  </td>

                  {/* Workflow Status Badge */}
                  <td>
                    <span className={`badge ${
                      order.status === 'CLOSED' ? 'badge-closed' :
                      order.status === 'REVIEWED' ? 'badge-reviewed' :
                      order.status === 'PENDING_REVIEW' ? 'badge-pending' : 'badge-ordered'
                    }`}>
                      {order.status.replace('_', ' ')}
                    </span>
                  </td>

                  {/* Report Status */}
                  <td>
                    {order.report_id ? (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <FileCheck size={15} color="#059669" />
                        <span style={{ fontSize: '0.8rem', color: '#047857', fontWeight: 600 }}>Report Arrived</span>
                        {order.has_critical && <span className="badge badge-critical" style={{ fontSize: '0.62rem' }}>CRITICAL</span>}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Clock size={15} color="#d97706" />
                        <span style={{ fontSize: '0.8rem', color: '#b45309', fontWeight: 600 }}>Awaiting Lab</span>
                      </div>
                    )}
                  </td>

                  {/* Actions */}
                  <td style={{ textAlign: 'right' }}>
                    {!order.report_id ? (
                      <button 
                        onClick={() => onOpenSimulateReport(order)}
                        className="btn btn-orange-outline"
                        style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                        title="Simulate receiving lab results for this order"
                      >
                        <Upload size={13} /> Receive Report
                      </button>
                    ) : (
                      <span style={{ fontSize: '0.78rem', color: '#94a3b8', fontWeight: 500 }}>Report Ingested</span>
                    )}
                  </td>

                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
