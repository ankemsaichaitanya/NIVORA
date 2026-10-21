import React, { useState } from 'react';
import { X, UserPlus, CheckCircle2 } from 'lucide-react';
import { api } from '../../api';

export default function PatientModal({ onClose, onSuccess }) {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [dob, setDob] = useState('1988-06-15');
  const [gender, setGender] = useState('Female');
  const [phone, setPhone] = useState('+1 (555) 345-6789');
  const [email, setEmail] = useState('');
  const [doctor, setDoctor] = useState('Dr. Sarah Jenkins');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await api.createPatient({
        first_name: firstName,
        last_name: lastName,
        dob: dob,
        gender: gender,
        phone: phone,
        email: email || `${firstName.toLowerCase()}@example.com`,
        primary_doctor: doctor
      });
      onSuccess();
      onClose();
    } catch (err) {
      console.error(err);
      alert("Error adding patient.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        
        <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#fff7ed' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserPlus size={20} color="#ea580c" />
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>Register New Patient</h2>
          </div>
          <button onClick={onClose} className="btn btn-secondary" style={{ padding: '6px' }}>
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">First Name</label>
              <input 
                type="text" 
                placeholder="e.g. Maya"
                value={firstName} 
                onChange={(e) => setFirstName(e.target.value)} 
                className="form-input" 
                required 
              />
            </div>
            <div className="form-group">
              <label className="form-label">Last Name</label>
              <input 
                type="text" 
                placeholder="e.g. Patel"
                value={lastName} 
                onChange={(e) => setLastName(e.target.value)} 
                className="form-input" 
                required 
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Date of Birth</label>
              <input 
                type="date" 
                value={dob} 
                onChange={(e) => setDob(e.target.value)} 
                className="form-input" 
                required 
              />
            </div>
            <div className="form-group">
              <label className="form-label">Gender</label>
              <select value={gender} onChange={(e) => setGender(e.target.value)} className="form-select">
                <option value="Female">Female</option>
                <option value="Male">Male</option>
                <option value="Other">Other</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Contact Phone</label>
              <input 
                type="tel" 
                value={phone} 
                onChange={(e) => setPhone(e.target.value)} 
                className="form-input" 
                required 
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input 
                type="email" 
                placeholder="e.g. maya.patel@example.com"
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                className="form-input" 
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Primary Attending Physician</label>
            <select value={doctor} onChange={(e) => setDoctor(e.target.value)} className="form-select">
              <option value="Dr. Sarah Jenkins">Dr. Sarah Jenkins (Internal Medicine)</option>
              <option value="Dr. Marcus Vance">Dr. Marcus Vance (Cardiology)</option>
              <option value="Dr. Elena Rostova">Dr. Elena Rostova (Endocrinology)</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn btn-primary">
              <CheckCircle2 size={16} /> {loading ? 'Registering...' : 'Register Patient'}
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}
