import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import DoctorDashboard from './components/DoctorDashboard';
import PatientsPage from './components/PatientsPage';
import TestsPage from './components/TestsPage';
import AlertsPage from './components/AlertsPage';
import AICopilotPage from './components/AICopilotPage';
import CKDDetectorPage from './components/CKDDetectorPage';

// Modals
import ReviewModal from './components/modals/ReviewModal';
import OrderModal from './components/modals/OrderModal';
import PatientModal from './components/modals/PatientModal';
import SimulateReportModal from './components/modals/SimulateReportModal';

import { api } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Data State
  const [stats, setStats] = useState(null);
  const [pendingReports, setPendingReports] = useState([]);
  const [followups, setFollowups] = useState([]);
  const [patients, setPatients] = useState([]);
  const [orders, setOrders] = useState([]);
  const [alerts, setAlerts] = useState([]);
  
  // Status states
  const [loading, setLoading] = useState(true);
  const [slaScanning, setSlaScanning] = useState(false);
  const [selectedPatientForAI, setSelectedPatientForAI] = useState(null);

  // Modals state
  const [reviewTask, setReviewTask] = useState(null);
  const [isOrderModalOpen, setIsOrderModalOpen] = useState(false);
  const [isPatientModalOpen, setIsPatientModalOpen] = useState(false);
  const [simulateReportOrder, setSimulateReportOrder] = useState(null);

  // Load all data from FastAPI backend
  const loadData = async () => {
    try {
      const [statsRes, pendingRes, followupsRes, patientsRes, ordersRes, alertsRes] = await Promise.all([
        api.getStats(),
        api.getPendingReports(),
        api.getActiveFollowups(),
        api.getPatients(),
        api.getOrders(),
        api.getAlerts()
      ]);

      setStats(statsRes.data);
      setPendingReports(pendingRes.data);
      setFollowups(followupsRes.data);
      setPatients(patientsRes.data);
      setOrders(ordersRes.data);
      setAlerts(alertsRes.data);
    } catch (err) {
      console.error("Error loading CareLoop data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Auto-refresh every 30 seconds to catch SLA updates in real time
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Force SLA scan
  const handleTriggerSla = async () => {
    setSlaScanning(true);
    try {
      await api.triggerSlaCheck();
      await loadData();
    } catch (err) {
      console.error("Error triggering SLA check:", err);
    } finally {
      setSlaScanning(false);
    }
  };

  // Complete Followup / Close Care Loop
  const handleCompleteFollowup = async (taskId) => {
    try {
      await api.completeFollowup(taskId);
      await loadData();
    } catch (err) {
      console.error("Error closing loop:", err);
    }
  };

  // Resolve Alert
  const handleResolveAlert = async (alertId) => {
    try {
      await api.resolveAlert(alertId);
      await loadData();
    } catch (err) {
      console.error("Error resolving alert:", err);
    }
  };

  // Transition to AI tab with selected patient
  const handleSelectPatientForAI = (patientId) => {
    setSelectedPatientForAI(patientId);
    setActiveTab('ai');
  };

  const handleOpenAIDraftFromDashboard = (item) => {
    setSelectedPatientForAI(item.patient_id);
    setActiveTab('ai');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Top Navigation */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        onOpenOrderModal={() => setIsOrderModalOpen(true)}
        onOpenPatientModal={() => setIsPatientModalOpen(true)}
        onTriggerSla={handleTriggerSla}
        slaScanning={slaScanning}
      />

      {/* Main Content Area */}
      <main style={{ flex: 1, maxWidth: '1400px', width: '100%', margin: '0 auto', padding: '28px 24px' }}>
        {loading ? (
          <div style={{ textAlign: 'center', padding: '100px 20px', color: 'var(--text-dim)' }}>
            <div style={{ fontSize: '1.2rem', fontWeight: 600, color: 'var(--text-main)', marginBottom: '8px' }}>
              Connecting to CareLoop Core Engine...
            </div>
            <div>Syncing doctor worklist, SLA timers, and patient records.</div>
          </div>
        ) : (
          <>
            {activeTab === 'dashboard' && (
              <DoctorDashboard 
                stats={stats}
                pendingReports={pendingReports}
                followups={followups}
                onReviewTask={(report) => setReviewTask(report)}
                onCompleteFollowup={handleCompleteFollowup}
                onOpenAIDraft={handleOpenAIDraftFromDashboard}
                refreshData={loadData}
              />
            )}

            {activeTab === 'patients' && (
              <PatientsPage 
                patients={patients}
                onOpenAddPatient={() => setIsPatientModalOpen(true)}
                onSelectPatientForAI={handleSelectPatientForAI}
              />
            )}

            {activeTab === 'tests' && (
              <TestsPage 
                orders={orders}
                onOpenOrderModal={() => setIsOrderModalOpen(true)}
                onOpenSimulateReport={(order) => setSimulateReportOrder(order)}
              />
            )}

            {activeTab === 'ckd' && (
              <CKDDetectorPage 
                patients={patients}
                onSuccessLoopCreated={loadData}
              />
            )}

            {activeTab === 'alerts' && (
              <AlertsPage 
                alerts={alerts}
                onResolveAlert={handleResolveAlert}
                onTriggerSla={handleTriggerSla}
                slaScanning={slaScanning}
              />
            )}

            {activeTab === 'ai' && (
              <AICopilotPage 
                patients={patients}
                selectedPatientId={selectedPatientForAI}
              />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer style={{ borderTop: '1px solid var(--border-subtle)', padding: '20px 24px', textAlign: 'center', fontSize: '0.8rem', color: 'var(--text-dim)' }}>
        CareLoop (NIVORA) • Clinical Closed-Loop Tracking System • BTech Final Year Project
      </footer>

      {/* Modals */}
      {reviewTask && (
        <ReviewModal 
          task={reviewTask}
          onClose={() => setReviewTask(null)}
          onSuccess={loadData}
        />
      )}

      {isOrderModalOpen && (
        <OrderModal 
          patients={patients}
          onClose={() => setIsOrderModalOpen(false)}
          onSuccess={loadData}
        />
      )}

      {isPatientModalOpen && (
        <PatientModal 
          onClose={() => setIsPatientModalOpen(false)}
          onSuccess={loadData}
        />
      )}

      {simulateReportOrder && (
        <SimulateReportModal 
          order={simulateReportOrder}
          onClose={() => setSimulateReportOrder(null)}
          onSuccess={loadData}
        />
      )}

    </div>
  );
}
