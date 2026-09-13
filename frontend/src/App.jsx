import React, { useState, useEffect } from 'react';
import {
  Activity,
  AlertTriangle,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  ClipboardCopy,
  FileCode,
  FlaskConical,
  HeartPulse,
  Pill,
  Search,
  ShieldAlert,
  Stethoscope,
  Upload,
  User,
  Zap,
} from 'lucide-react';

export default function App() {
  const [patients, setPatients] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState('patient_01_high_risk');
  const [patientData, setPatientData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAudit, setShowAudit] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [checkedDirectives, setCheckedDirectives] = useState({});
  const [toastMessage, setToastMessage] = useState(null);

  // Fetch initial synthetic patient cases
  useEffect(() => {
    fetch('/api/patients')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load patient queue');
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

  // Fetch evaluation when patient changes
  useEffect(() => {
    if (!selectedId) return;
    setLoading(true);
    fetch(`/api/patients/${selectedId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Multi-agent clinical evaluation failed');
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
        throw new Error(errData.detail || 'Failed to parse uploaded FHIR bundle');
      }
      const data = await res.json();
      setPatientData(data);

      const customPatient = {
        id: 'custom_' + Date.now(),
        name: data.patient_name || 'Uploaded Patient',
        age: data.patient_age ?? '?',
        gender: data.gender || 'unknown',
        summary: `${data.triage_assessment?.triage_level || 'EVALUATED'} Priority (Custom Bundle)`,
        priority: data.triage_assessment?.triage_level || 'MEDIUM',
      };
      setPatients((prev) => [customPatient, ...prev]);
      setSelectedId(customPatient.id);
      showToast('Custom FHIR R4 Bundle evaluated successfully');
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const toggleDirective = (idx) => {
    setCheckedDirectives((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  // Copy synthesized EHR note
  const handleCopyClinicalNote = () => {
    if (!patientData) return;
    const triage = patientData.triage_assessment;
    const lines = [
      `=== AEGISCLINICAL CDSS MULTI-AGENT TRIAGE NOTE ===`,
      `Patient: ${patientData.patient_name} (ID: ${patientData.patient_id}, Age: ${patientData.patient_age}, Gender: ${patientData.gender})`,
      `Triage Level: ${triage?.triage_level || 'UNKNOWN'} PRIORITY`,
      `Lead Assessment: ${triage?.summary || ''}`,
      ``,
      `[LABORATORY SPECIALIST FINDINGS]`,
      ...(patientData.lab_alerts?.map(
        (l) => `- ${l.name}: ${l.current_value} ${l.unit} [${l.alert_type}] - ${l.clinical_significance}`
      ) || ['- No acute laboratory alerts.']),
      ``,
      `[PHARMACOLOGY SPECIALIST FINDINGS]`,
      ...(patientData.drug_interactions?.map(
        (d) => `- ${d.drugs.join(' + ')} [${d.severity}]: ${d.mechanism}. Rec: ${d.recommendation}`
      ) || ['- No contraindicated drug combinations identified.']),
      ``,
      `[CLINICAL ACTION PLAN]`,
      ...(triage?.action_items?.map((a) => `[ ] ${a}`) || ['- Routine care.']),
      `==================================================`,
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    showToast('Clinical Triage Note copied to clipboard for EHR');
  };

  const filteredPatients = patients.filter((p) => {
    const q = searchQuery.toLowerCase();
    return (
      p.name.toLowerCase().includes(q) ||
      p.priority.toLowerCase().includes(q) ||
      (p.summary && p.summary.toLowerCase().includes(q))
    );
  });

  const triage = patientData?.triage_assessment;
  const triageLevel = triage?.triage_level || 'LOW';
  const labAlerts = patientData?.lab_alerts || [];
  const drugInteractions = patientData?.drug_interactions || [];
  const chronicConditions = patientData?.chronic_conditions || [];

  return (
    <div className="app-container">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="toast-notice">
          <CheckCircle2 size={16} color="#38bdf8" />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Sidebar: Patient Triage Queue */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-row">
            <div className="brand-group">
              <div className="brand-icon">
                <Stethoscope size={22} />
              </div>
              <div>
                <div className="brand-title">AegisClinical</div>
                <div className="brand-subtitle">Multi-Agent Decision Support</div>
              </div>
            </div>
          </div>
        </div>

        {/* Search / Filter */}
        <div className="search-box">
          <Search size={14} className="search-icon-pos" />
          <input
            type="text"
            className="search-input"
            placeholder="Search patient, risk, or condition..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        {/* Queue List */}
        <div className="patient-queue">
          <div className="queue-label-row">
            <span className="queue-label">Clinical Triage Queue</span>
            <span className="queue-count">{filteredPatients.length} Cases</span>
          </div>

          {filteredPatients.map((p) => {
            const isSelected = p.id === selectedId;
            return (
              <div
                key={p.id}
                className={`patient-card ${isSelected ? 'active' : ''}`}
                onClick={() => setSelectedId(p.id)}
              >
                <div className="card-top">
                  <span className="p-name">{p.name}</span>
                  <span className={`p-tag ${p.priority}`}>{p.priority}</span>
                </div>
                <div className="p-meta-line">
                  <span>{p.age}y</span>
                  <span>&bull;</span>
                  <span>{p.gender?.toUpperCase()}</span>
                </div>
                <div className="p-snippet">{p.summary}</div>
              </div>
            );
          })}
        </div>

        {/* Upload Custom FHIR */}
        <div className="sidebar-footer">
          <label className="upload-card-btn">
            <Upload size={15} />
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
        {/* Hospital Header */}
        <header className="hospital-header">
          <div className="patient-identity">
            <h2>{loading ? 'Evaluating Record...' : patientData?.patient_name || 'Patient'}</h2>
            <div className="identity-badges">
              <span className="chip mono">
                MRN: {patientData?.patient_id || 'UNKNOWN'}
              </span>
              <span className="chip">
                Age: {patientData?.patient_age ?? 'N/A'}
              </span>
              <span className="chip">
                Gender: {patientData?.gender ? patientData.gender.toUpperCase() : 'N/A'}
              </span>
              <span className="chip mono">
                Standard: FHIR R4 JSON
              </span>
            </div>
          </div>

          <div className="header-actions">
            <button className="copy-ehr-btn" onClick={handleCopyClinicalNote}>
              <ClipboardCopy size={15} />
              <span>Copy EHR Note</span>
            </button>
            <div className="engine-telemetry-badge">
              <span className="pulse-led"></span>
              <span>LangGraph Scatter-Gather &bull; Local Ollama</span>
            </div>
          </div>
        </header>

        {error && (
          <div
            style={{
              padding: '1rem',
              backgroundColor: '#fff1f2',
              border: '1px solid #fecdd3',
              color: '#9f1239',
              borderRadius: '8px',
              marginBottom: '1.5rem',
              fontSize: '0.88rem',
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
              height: '420px',
              color: '#64748b',
              gap: '1rem',
            }}
          >
            <Activity className="animate-spin" size={36} color="#0284c7" />
            <p style={{ fontWeight: 700, fontSize: '0.95rem' }}>
              Executing Parallel Multi-Agent Clinical Evaluation...
            </p>
          </div>
        ) : (
          <>
            {/* Master Triage Urgency Banner */}
            <section className={`master-banner ${triageLevel}`}>
              <div className="banner-top-row">
                <span className={`banner-pill ${triageLevel}`}>
                  {triageLevel === 'HIGH' && <ShieldAlert size={15} />}
                  {triageLevel === 'MEDIUM' && <AlertTriangle size={15} />}
                  {triageLevel === 'LOW' && <CheckCircle2 size={15} />}
                  <span>{triageLevel} Priority Triage</span>
                </span>
                <span className={`banner-headline ${triageLevel}`}>
                  {triageLevel === 'HIGH' && 'Emergent Clinical Intervention Required'}
                  {triageLevel === 'MEDIUM' && 'Urgent Clinical Review & Monitoring'}
                  {triageLevel === 'LOW' && 'Stable Baseline / Routine Management'}
                </span>
              </div>
              <div className="banner-narrative">
                {triage?.summary || 'Multi-agent clinical synthesis completed.'}
              </div>
            </section>

            {/* Interactive Clinical Directives */}
            {triage?.action_items && triage.action_items.length > 0 && (
              <section className="directives-card">
                <div className="directives-header">
                  <Zap size={16} color="#d97706" />
                  <span>Immediate Attending Physician Orders</span>
                </div>
                <div className="directives-list">
                  {triage.action_items.map((action, idx) => {
                    const isChecked = !!checkedDirectives[idx];
                    return (
                      <div
                        key={idx}
                        className="directive-item"
                        onClick={() => toggleDirective(idx)}
                        style={{ cursor: 'pointer', userSelect: 'none' }}
                      >
                        <div
                          style={{
                            width: '18px',
                            height: '18px',
                            borderRadius: '4px',
                            border: isChecked ? '1px solid #16a34a' : '1.5px solid #cbd5e1',
                            backgroundColor: isChecked ? '#16a34a' : '#fff',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: '#fff',
                            flexShrink: 0,
                            marginTop: '2px',
                          }}
                        >
                          {isChecked && <Check size={12} strokeWidth={3} />}
                        </div>
                        <span
                          style={{
                            textDecoration: isChecked ? 'line-through' : 'none',
                            color: isChecked ? '#94a3b8' : '#0f172a',
                          }}
                        >
                          {action}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
            )}

            {/* 3-Column Evidence Bento Grid */}
            <div className="bento-3col">
              {/* Column 1: Laboratory Specialist Agent */}
              <div className="bento-card">
                <div className="bento-card-header">
                  <div className="bento-header-left">
                    <FlaskConical size={18} color="#0284c7" />
                    <h3>Laboratory Specialist</h3>
                  </div>
                  <span className="badge-count">{labAlerts.length} Alerts</span>
                </div>
                <div className="bento-body">
                  {labAlerts.length > 0 ? (
                    labAlerts.map((lab, i) => {
                      const isCreatinine = lab.name.toLowerCase().includes('creatinine');
                      const percentDelta =
                        lab.baseline_value && lab.baseline_value > 0
                          ? Math.round(((lab.current_value - lab.baseline_value) / lab.baseline_value) * 100)
                          : null;

                      return (
                        <div key={i} className={`lab-delta-card ${lab.severity}`}>
                          <div className="lab-card-title">
                            <span className="lab-analyte-name">{lab.name}</span>
                            <span className={`lab-kdigo-badge ${lab.severity}`}>
                              {lab.alert_type}
                            </span>
                          </div>

                          <div className="delta-compare-row">
                            <span className="delta-current">
                              {lab.current_value} <span style={{ fontSize: '0.8rem', fontWeight: 500 }}>{lab.unit}</span>
                            </span>
                            {lab.baseline_value != null && (
                              <span className="delta-baseline">
                                Baseline: {lab.baseline_value} {lab.unit}
                              </span>
                            )}
                            {percentDelta !== null && percentDelta > 0 && (
                              <span className="delta-percent-pill">
                                +{percentDelta}%
                              </span>
                            )}
                          </div>

                          <div className="lab-sig-text">{lab.clinical_significance}</div>
                        </div>
                      );
                    })
                  ) : (
                    <div className="bento-empty">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>All laboratory analytes stable and within normal baseline.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Column 2: Pharmacology Specialist Agent */}
              <div className="bento-card">
                <div className="bento-card-header">
                  <div className="bento-header-left">
                    <Pill size={18} color="#ea580c" />
                    <h3>Pharmacology Specialist</h3>
                  </div>
                  <span className="badge-count">{drugInteractions.length} Flags</span>
                </div>
                <div className="bento-body">
                  {drugInteractions.length > 0 ? (
                    drugInteractions.map((ddi, i) => (
                      <div key={i} className={`pharma-alert-card ${ddi.severity}`}>
                        <div className="lab-card-title">
                          <span className="pharma-drugs-line">
                            {ddi.drugs.join(' + ')}
                          </span>
                          <span className={`lab-kdigo-badge ${ddi.severity === 'CONTRAINDICATED' ? 'CRITICAL' : 'HIGH'}`}>
                            {ddi.severity}
                          </span>
                        </div>

                        <div className="pharma-mechanism-box">
                          <strong>Mechanism:</strong> {ddi.mechanism}
                        </div>

                        <div className="pharma-rec-box">
                          <span>💡</span>
                          <span>{ddi.recommendation}</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="bento-empty">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>No critical drug contraindications or interactions identified.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Column 3: Medical History Specialist Agent */}
              <div className="bento-card">
                <div className="bento-card-header">
                  <div className="bento-header-left">
                    <HeartPulse size={18} color="#6366f1" />
                    <h3>Medical History</h3>
                  </div>
                  <span className="badge-count">{chronicConditions.length} Diagnoses</span>
                </div>
                <div className="bento-body">
                  {chronicConditions.length > 0 ? (
                    chronicConditions.map((cond, i) => (
                      <div key={i} className="history-item-card">
                        <div>
                          <div className="history-name">{cond.display}</div>
                          <div style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', marginTop: '2px' }}>
                            Status: {cond.status}
                          </div>
                        </div>
                        <span className="history-code">{cond.code}</span>
                      </div>
                    ))
                  ) : (
                    <div className="bento-empty">
                      <CheckCircle2 size={32} color="#10b981" />
                      <p>No active chronic comorbidities recorded in medical history.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Audit State Drawer */}
            <div style={{ marginTop: '1rem' }}>
              <div className="audit-bar">
                <button
                  className="audit-toggle-btn"
                  onClick={() => setShowAudit(!showAudit)}
                >
                  <FileCode size={16} />
                  <span>
                    {showAudit ? 'Hide Clinical Graph State Inspector' : 'Inspect Full Serialized Pydantic State & Audit Trail'}
                  </span>
                  {showAudit ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {showAudit && (
                  <button
                    className="chip"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(patientData, null, 2));
                      showToast('Audit JSON copied to clipboard');
                    }}
                  >
                    <ClipboardCopy size={13} />
                    <span>Copy JSON</span>
                  </button>
                )}
              </div>

              {showAudit && (
                <div className="audit-viewer">
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
