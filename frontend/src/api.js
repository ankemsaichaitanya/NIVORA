import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

export const api = {
  // Dashboard
  getStats: () => axios.get(`${API_BASE}/dashboard/stats`),
  getPendingReports: () => axios.get(`${API_BASE}/dashboard/pending-reports`),
  getOverdueTasks: () => axios.get(`${API_BASE}/dashboard/overdue-tasks`),
  getActiveFollowups: () => axios.get(`${API_BASE}/dashboard/active-followups`),

  // Patients
  getPatients: () => axios.get(`${API_BASE}/patients`),
  createPatient: (data) => axios.post(`${API_BASE}/patients`, data),
  getPatientHistory: (id) => axios.get(`${API_BASE}/patients/${id}/history`),

  // Tests & Reports
  getOrders: (status) => axios.get(`${API_BASE}/tests/orders`, { params: { status } }),
  createOrder: (data) => axios.post(`${API_BASE}/tests/orders`, data),
  receiveReport: (data) => axios.post(`${API_BASE}/tests/reports/receive`, data),
  simulateUploadReport: (formData) => axios.post(`${API_BASE}/tests/reports/upload-simulate`, formData),
  submitDoctorReview: (taskId, data) => axios.post(`${API_BASE}/tests/tasks/${taskId}/review`, data),
  completeFollowup: (taskId) => axios.post(`${API_BASE}/tests/tasks/${taskId}/complete-followup`),

  // Alerts & SLA
  getAlerts: (unresolvedOnly = false) => axios.get(`${API_BASE}/alerts`, { params: { unresolved_only: unresolvedOnly } }),
  resolveAlert: (id) => axios.post(`${API_BASE}/alerts/${id}/resolve`),
  triggerSlaCheck: () => axios.post(`${API_BASE}/alerts/trigger-sla-check`),

  // AI Assistant
  getPatientSummary: (patientId) => axios.get(`${API_BASE}/ai/patient-summary/${patientId}`),
  draftReminder: (data) => axios.post(`${API_BASE}/ai/draft-reminder`, data),
  askAI: (data) => axios.post(`${API_BASE}/ai/ask`, data),

  // CKD 1D-CNN Prediction Engine
  predictCKD: (data) => axios.post(`${API_BASE}/ckd/predict`, data),
  getCKDSamples: () => axios.get(`${API_BASE}/ckd/sample-profiles`),
  createCKDLoop: (data) => axios.post(`${API_BASE}/ckd/create-care-loop`, data)
};
