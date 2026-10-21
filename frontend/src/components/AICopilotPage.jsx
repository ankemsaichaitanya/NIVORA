import React, { useState } from 'react';
import { 
  Bot, 
  Sparkles, 
  Send, 
  Check, 
  Copy, 
  Smartphone, 
  FileText
} from 'lucide-react';
import { api } from '../api';

export default function AICopilotPage({ patients, selectedPatientId }) {
  const [patientId, setPatientId] = useState(selectedPatientId || (patients?.[0]?.id || ''));
  const [channel, setChannel] = useState('WhatsApp');
  
  // State for Summary
  const [summary, setSummary] = useState('');
  const [loadingSummary, setLoadingSummary] = useState(false);

  // State for Draft Reminder
  const [reminderDraft, setReminderDraft] = useState(null);
  const [loadingDraft, setLoadingDraft] = useState(false);
  const [draftCopied, setDraftCopied] = useState(false);

  // State for Workflow Q&A
  const [question, setQuestion] = useState('');
  const [chatLog, setChatLog] = useState([
    {
      role: 'assistant',
      text: 'Hello Doctor! I am CareLoop AI. Ask me anything about current pending reports, SLA breaches, or specific patient task statuses.'
    }
  ]);
  const [loadingChat, setLoadingChat] = useState(false);

  // 1. Generate Summary
  const handleGenerateSummary = async () => {
    if (!patientId) return;
    setLoadingSummary(true);
    try {
      const res = await api.getPatientSummary(patientId);
      setSummary(res.data.summary);
    } catch (err) {
      console.error(err);
      setSummary('Failed to retrieve summary.');
    } finally {
      setLoadingSummary(false);
    }
  };

  // 2. Draft Reminder
  const handleDraftReminder = async () => {
    if (!patientId) return;
    setLoadingDraft(true);
    setDraftCopied(false);
    try {
      const res = await api.draftReminder({
        patient_id: parseInt(patientId),
        channel: channel
      });
      setReminderDraft(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDraft(false);
    }
  };

  // 3. Q&A Ask
  const handleAskQuestion = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    const userText = question;
    setChatLog(prev => [...prev, { role: 'user', text: userText }]);
    setQuestion('');
    setLoadingChat(true);

    try {
      const res = await api.askAI({
        patient_id: patientId ? parseInt(patientId) : null,
        question: userText
      });
      setChatLog(prev => [...prev, { role: 'assistant', text: res.data.answer }]);
    } catch (err) {
      setChatLog(prev => [...prev, { role: 'assistant', text: 'Sorry, I encountered an error retrieving workflow records.' }]);
    } finally {
      setLoadingChat(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setDraftCopied(true);
    setTimeout(() => setDraftCopied(false), 2500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '26px' }}>
      
      {/* Top Header */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
          <span className="badge" style={{ background: '#fff7ed', color: '#c2410c', border: '1px solid #fed7aa' }}>
            Module 5: Clinical Assistant
          </span>
          <span style={{ fontSize: '0.8rem', color: '#64748b', fontWeight: 500 }}>
            • Human-in-the-Loop Safe Communication
          </span>
        </div>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#0f172a' }}>AI Workflow & Reminder Assistant</h1>
        <p style={{ color: '#64748b', fontSize: '0.88rem' }}>
          Summarize patient closed-loop milestones, draft verified patient notifications for staff approval, and query longitudinal clinic history.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '22px' }}>
        
        {/* Left Column: Patient Task Summarizer & Message Drafter */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '22px' }}>
          
          {/* Patient Selector */}
          <div className="glass-panel" style={{ padding: '22px' }}>
            <label className="form-label">Select Patient to Focus On</label>
            <select 
              value={patientId} 
              onChange={(e) => {
                setPatientId(e.target.value);
                setSummary('');
                setReminderDraft(null);
              }}
              className="form-select"
              style={{ marginTop: '6px' }}
            >
              {patients?.map(p => (
                <option key={p.id} value={p.id}>
                  {p.first_name} {p.last_name} ({p.mrn})
                </option>
              ))}
            </select>

            <div style={{ display: 'flex', gap: '10px', marginTop: '14px' }}>
              <button 
                onClick={handleGenerateSummary} 
                disabled={loadingSummary}
                className="btn btn-primary"
                style={{ flex: 1, justifyContent: 'center' }}
              >
                <Sparkles size={16} /> {loadingSummary ? 'Synthesizing...' : 'Summarize Patient Tasks'}
              </button>
            </div>

            {/* Summary Box (Clean White with Orange Accent) */}
            {summary && (
              <div style={{ 
                marginTop: '16px', 
                background: '#fff7ed', 
                border: '1px solid #fed7aa', 
                borderLeft: '4px solid #ea580c',
                borderRadius: 'var(--radius-sm)', 
                padding: '16px',
                fontSize: '0.86rem',
                color: '#334155',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap'
              }}>
                <div style={{ fontWeight: 800, color: '#9a3412', marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <FileText size={15} color="#ea580c" /> Executive Clinical Summary
                </div>
                {summary}
              </div>
            )}
          </div>

          {/* Patient Reminder Drafter for Staff Approval */}
          <div className="glass-panel" style={{ padding: '22px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Smartphone size={17} color="#ea580c" /> Draft Patient Notification
              </h3>
              <div style={{ display: 'flex', gap: '6px' }}>
                {['WhatsApp', 'SMS', 'Email'].map(ch => (
                  <button 
                    key={ch}
                    onClick={() => setChannel(ch)}
                    className="btn"
                    style={{ 
                      padding: '4px 10px', 
                      fontSize: '0.74rem',
                      fontWeight: 700,
                      background: channel === ch ? 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' : '#f8fafc',
                      color: channel === ch ? '#ffffff' : '#64748b',
                      border: channel === ch ? 'none' : '1px solid #e2e8f0'
                    }}
                  >
                    {ch}
                  </button>
                ))}
              </div>
            </div>

            <p style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '14px' }}>
              Generates an easy-to-understand notification based on doctor instructions. Requires clinic staff approval before sending.
            </p>

            <button 
              onClick={handleDraftReminder} 
              disabled={loadingDraft}
              className="btn btn-orange-outline"
              style={{ width: '100%', justifyContent: 'center' }}
            >
              <Sparkles size={15} color="#ea580c" /> {loadingDraft ? 'Drafting...' : `Draft ${channel} Message`}
            </button>

            {reminderDraft && (
              <div style={{ 
                marginTop: '16px', 
                background: '#ffffff', 
                border: '1px solid #fed7aa', 
                borderRadius: 'var(--radius-sm)', 
                padding: '16px',
                boxShadow: 'var(--shadow-subtle)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px', fontSize: '0.78rem', color: '#64748b' }}>
                  <span>Recipient: <strong style={{ color: '#0f172a' }}>{reminderDraft.recipient}</strong></span>
                  <span className="badge badge-pending" style={{ fontSize: '0.68rem' }}>
                    Awaiting Staff Sign-off
                  </span>
                </div>

                <div style={{ 
                  background: '#f8fafc', 
                  padding: '12px', 
                  borderRadius: '6px', 
                  fontSize: '0.86rem', 
                  color: '#0f172a',
                  borderLeft: '4px solid #10b981',
                  border: '1px solid #e2e8f0',
                  borderLeftWidth: '4px',
                  marginBottom: '12px',
                  lineHeight: '1.5'
                }}>
                  "{reminderDraft.drafted_message}"
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                    Generated via {reminderDraft.generated_by}
                  </span>
                  
                  <button 
                    onClick={() => copyToClipboard(reminderDraft.drafted_message)}
                    className="btn btn-success"
                    style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                  >
                    {draftCopied ? <Check size={14} /> : <Copy size={14} />}
                    {draftCopied ? 'Approved & Copied!' : 'Approve & Copy'}
                  </button>
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Right Column: Workflow Q&A Assistant */}
        <div className="glass-panel" style={{ padding: '22px', display: 'flex', flexDirection: 'column', height: '620px' }}>
          
          <div style={{ marginBottom: '14px' }}>
            <h3 style={{ fontSize: '1rem', fontWeight: 800, color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot size={18} color="#ea580c" /> Workflow Q&A Copilot
            </h3>
            <p style={{ fontSize: '0.8rem', color: '#64748b' }}>
              Ask questions about clinic turnaround times, SLA overdue rates, or specific test orders.
            </p>
          </div>

          {/* Quick Prompts */}
          <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '8px', marginBottom: '12px' }}>
            {[
              "Which tasks are currently overdue?",
              "Are there any critical panic values?",
              "Summarize today's closed-loop rate"
            ].map(promptText => (
              <button 
                key={promptText}
                onClick={() => setQuestion(promptText)}
                className="btn btn-secondary"
                style={{ padding: '4px 10px', fontSize: '0.72rem', whiteSpace: 'nowrap' }}
              >
                {promptText}
              </button>
            ))}
          </div>

          {/* Chat History Box (Clean White / Light Slate) */}
          <div style={{ 
            flex: 1, 
            overflowY: 'auto', 
            background: '#f8fafc', 
            border: '1px solid #e2e8f0', 
            borderRadius: 'var(--radius-sm)', 
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            {chatLog.map((msg, index) => (
              <div 
                key={index}
                style={{
                  alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start',
                  maxWidth: '85%',
                  background: msg.role === 'user' ? 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)' : '#ffffff',
                  color: msg.role === 'user' ? '#ffffff' : '#0f172a',
                  border: msg.role === 'user' ? 'none' : '1px solid #e2e8f0',
                  boxShadow: 'var(--shadow-subtle)',
                  padding: '10px 14px',
                  borderRadius: msg.role === 'user' ? '14px 14px 2px 14px' : '14px 14px 14px 2px',
                  fontSize: '0.86rem',
                  lineHeight: '1.5'
                }}
              >
                {msg.text}
              </div>
            ))}
            {loadingChat && (
              <div style={{ alignSelf: 'flex-start', color: '#ea580c', fontSize: '0.8rem', fontStyle: 'italic', fontWeight: 500 }}>
                CareLoop Assistant is consulting clinic records...
              </div>
            )}
          </div>

          {/* Input Form */}
          <form onSubmit={handleAskQuestion} style={{ display: 'flex', gap: '8px', marginTop: '14px' }}>
            <input 
              type="text"
              placeholder="Ask about patient status or SLA records..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="form-input"
              style={{ flex: 1, height: '42px' }}
            />
            <button type="submit" disabled={loadingChat || !question.trim()} className="btn btn-primary" style={{ height: '42px', padding: '0 16px' }}>
              <Send size={16} />
            </button>
          </form>

        </div>

      </div>

    </div>
  );
}
