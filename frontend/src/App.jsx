import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock,
  FileCode,
  FlaskConical,
  HeartPulse,
  Pill,
  ShieldAlert,
  Stethoscope,
  Upload,
  User,
  Zap,
} from 'lucide-react';

export default function App() {
  const [patients, setPatients] = useState([]);
  const [selectedId, setSelectedId] = useState('patient_01_high_risk');
  const [patientData, setPatientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAudit, setShowAudit] = useState(false);
  const [uploading, setUploading] = useState(false);

  // Fetch available synthetic patient list
  useEffect(() => {
    fetch('/api/patients')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch patient list');
        return res.json();
      })
      .then((data) => {
        setPatients(data);
        if (data.length > 0 && !selectedId) {
          setSelectedId(data[0].id);
        }
      })
      .catch((err) => setError(err.message));
  }, []);

  // Fetch evaluation when selected patient changes
  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    fetch(`/api/patients/${selectedId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Evaluation failed');
        return res.json();
      })
      .then((data) => {
        setPatientData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [selectedId]);

  // Handle custom FHIR upload
  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to upload FHIR bundle');
      }
      const data = await res.json();
      setPatientData(data);
      // Mark custom in queue
      const customPatient = {
        id: 'custom_upload_' + Date.now(),
        name: data.patient_name || 'Uploaded Patient',
        age: data.patient_age || '?',
        gender: data.gender || 'unknown',
        summary: data.triage_assessment?.triage_level + ' Risk Custom Bundle',
        priority: data.triage_assessment?.triage_level || 'MEDIUM',
      };
      setPatients((prev) => [customPatient, ...prev]);
      setSelectedId(customPatient.id);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const triage = patientData?.triage_assessment;
  const triageLevel = triage?.triage_level || 'LOW';
  const labAlerts = patientData?.lab_alerts || [];
  const drugInteractions = patientData?.drug_interactions || [];
  const chronicConditions = patientData?.chronic_conditions || [];

  return (
    <div className="app-container">
      {/* Sidebar: Patient Triage Queue */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-area">
            <div className="logo-icon">
              <Stethoscope size={20} />
            </div>
            <div className="logo-text">
              <h1>AegisClinical</h1>
              <p>Multi-Agent CDSS</p>
            </div>
          </div>
        </div>

        <div className="patient-queue">
          <div className="queue-title">Clinical Triage Queue</div>
          {patients.map((p) => {
            const isSelected = p.id === selectedId;
            return (
              <div
                key={p.id}
                className={`patient-card ${isSelected ? 'active' : ''}`}
                onClick={() => setSelectedId(p.id)}
              >
                <div className="card-header-row">
                  <span className="patient-name">{p.name}</span>
                  <span className={`priority-tag ${p.priority}`}>{p.priority}</span>
                </div>
                <div className="patient-meta">
                  Age: {p.age} &bull; {p.gender?.toUpperCase()}
                </div>
                <div className="patient-snippet">{p.summary}</div>
              </div>
            );
          })}
        </div>

        <div className="upload-area">
          <label className="upload-btn">
            <Upload size={16} />
            <span>{uploading ? 'Evaluating Bundle...' : 'Upload FHIR R4 Bundle'}</span>
            <input
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
        </div>
      </aside>

      {/* Main Viewport */}
      <main className="main-viewport">
        {/* Top bar with telemetry */}
        <header className="top-bar">
          <div className="patient-title-area">
            <h2>{loading ? 'Evaluating...' : patientData?.patient_name || 'Patient'}</h2>
            <div className="demographic-badges">
              <span className="badge-demo">
                ID: {patientData?.patient_id || 'UNKNOWN'}
              </span>
              <span className="badge-demo">
                Age: {patientData?.patient_age ?? 'N/A'}
              </span>
              <span className="badge-demo">
                Gender: {patientData?.gender ? patientData.gender.toUpperCase() : 'N/A'}
              </span>
            </div>
          </div>

          <div className="engine-pill">
            <span className="pulse-dot"></span>
            <span>LangGraph &bull; Local SLM &bull; Zero PHI Leak</span>
          </div>
        </header>

        {error && (
          <div
            style={{
              padding: '1rem',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              color: '#991b1b',
              borderRadius: '8px',
              marginBottom: '1.5rem',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {loading ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '400px',
              color: '#64748b',
              gap: '1rem',
            }}
          >
            <Activity className="animate-spin" size={32} color="#0284c7" />
            <p style={{ fontWeight: 600 }}>Executing Scatter-Gather Multi-Agent Pipeline...</p>
          </div>
        ) : (
          <>
            {/* Urgency Triage Banner */}
            <section className={`triage-banner ${triageLevel}`}>
              <div className={`priority-tag ${triageLevel}`}>
                {triageLevel === 'HIGH' && <ShieldAlert size={14} />}
                {triageLevel === 'MEDIUM' && <AlertTriangle size={14} />}
                {triageLevel === 'LOW' && <CheckCircle2 size={14} />}
                <span>{triageLevel} Priority Triage</span>
              </div>
              <div className="triage-summary-text">
                {triage?.summary || 'Clinical assessment completed.'}
              </div>
            </section>

            {/* Action Items */}
            {triage?.action_items && triage.action_items.length > 0 && (
              <section className="action-items-section">
                <div className="section-title">
                  <Zap size={16} color="#d97706" />
                  <span>Immediate Clinical Directives</span>
                </div>
                <div className="actions-grid">
                  {triage.action_items.map((action, idx) => (
                    <div key={idx} className="action-row">
                      <span style={{ color: '#ea580c', fontWeight: 800 }}>&bull;</span>
                      <span>{action}</span>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* 3-Column Evidence Bento */}
            <div className="bento-grid">
              {/* Column 1: Lab Specialist Agent */}
              <div className="bento-column">
                <div className="bento-header">
                  <div className="bento-header-title">
                    <FlaskConical size={18} color="#0284c7" />
                    <span>Laboratory Specialist</span>
                  </div>
                  <span className="bento-counter">{labAlerts.length} Alerts</span>
                </div>
                <div className="bento-content">
                  {labAlerts.length > 0 ? (
                    labAlerts.map((lab, i) => (
                      <div key={i} className={`evidence-card ${lab.severity}`}>
                        <div className="evidence-title-row">
                          <span className="evidence-name">{lab.name}</span>
                          <span className={`evidence-badge ${lab.severity}`}>
                            {lab.alert_type}
                          </span>
                        </div>
                        <div className="evidence-value-row">
                          <strong>{lab.current_value} {lab.unit}</strong>
                          {lab.baseline_value != null && (
                            <span style={{ color: '#64748b', marginLeft: '0.4rem' }}>
                              (Base: {lab.baseline_value} {lab.unit})
                            </span>
                          )}
                        </div>
                        <div className="evidence-desc">{lab.clinical_significance}</div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-state">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>All laboratory analytes stable and within reference intervals.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Column 2: Pharmacology Specialist Agent */}
              <div className="bento-column">
                <div className="bento-header">
                  <div className="bento-header-title">
                    <Pill size={18} color="#d97706" />
                    <span>Pharmacology Specialist</span>
                  </div>
                  <span className="bento-counter">{drugInteractions.length} Flags</span>
                </div>
                <div className="bento-content">
                  {drugInteractions.length > 0 ? (
                    drugInteractions.map((ddi, i) => (
                      <div key={i} className={`evidence-card ${ddi.severity}`}>
                        <div className="evidence-title-row">
                          <span className="evidence-name">{ddi.drugs.join(' + ')}</span>
                          <span className={`evidence-badge ${ddi.severity}`}>
                            {ddi.severity}
                          </span>
                        </div>
                        <div className="evidence-desc">{ddi.mechanism}</div>
                        <div className="evidence-rec">
                          Rec: {ddi.recommendation}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-state">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>No critical drug contraindications or interactions identified.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Column 3: Medical History Specialist Agent */}
              <div className="bento-column">
                <div className="bento-header">
                  <div className="bento-header-title">
                    <HeartPulse size={18} color="#8b5cf6" />
                    <span>Medical History</span>
                  </div>
                  <span className="bento-counter">{chronicConditions.length} Diagnoses</span>
                </div>
                <div className="bento-content">
                  {chronicConditions.length > 0 ? (
                    chronicConditions.map((cond, i) => (
                      <div key={i} className="evidence-card MODERATE">
                        <div className="evidence-title-row">
                          <span className="evidence-name">{cond.display}</span>
                          <span className="evidence-badge MODERATE">{cond.status}</span>
                        </div>
                        <div className="evidence-desc" style={{ fontFamily: 'var(--font-mono)' }}>
                          ICD-10: {cond.code}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-state">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>No active chronic comorbidities cataloged.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Audit Inspector */}
            <div style={{ marginTop: '1.5rem' }}>
              <button
                className="audit-drawer-btn"
                onClick={() => setShowAudit(!showAudit)}
              >
                <FileCode size={16} />
                <span>
                  {showAudit ? 'Hide Audit State Inspector' : 'Inspect Serialized Pydantic State & Audit Trail'}
                </span>
                {showAudit ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
              </button>

              {showAudit && (
                <div className="audit-container">
                  <pre>{JSON.stringify(patientData, null, 2)}</pre>
                </div>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}
