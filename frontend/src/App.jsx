import React, { useState, useEffect } from 'react';
import {
  Activity,
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
  Stethoscope,
  Upload,
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

  const selectPatient = (p) => {
    setSelectedId(p.id);
    setCheckedDirectives({});
    if (p.evaluatedData) {
      setPatientData(p.evaluatedData);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!selectedId || selectedId.startsWith('custom_')) return;
    setCheckedDirectives({});
    setLoading(true);
    let active = true;

    fetch(`/api/patients/${selectedId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Evaluation failed');
        return res.json();
      })
      .then((data) => {
        if (!active) return;
        setPatientData(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!active) return;
        setError(err.message);
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [selectedId]);

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
        summary: `Custom Bundle (${data.triage_assessment?.triage_level || 'EVAL'})`,
        priority: data.triage_assessment?.triage_level || 'MEDIUM',
        evaluatedData: data,
      };
      setPatients((prev) => [customPatient, ...prev]);
      setSelectedId(customPatient.id);
      setCheckedDirectives({});
      showToast('Custom FHIR R4 Bundle evaluated');
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  };

  const showToast = (msg) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  const toggleDirective = (idx) => {
    setCheckedDirectives((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const handleCopyClinicalNote = () => {
    if (!patientData) return;
    const triage = patientData.triage_assessment;
    const lines = [
      `AEGISCLINICAL CDSS — TRIAGE ASSESSMENT`,
      `Patient: ${patientData.patient_name} | MRN: ${patientData.patient_id} | Age: ${patientData.patient_age} | Gender: ${patientData.gender}`,
      `Triage Level: ${triage?.triage_level || 'UNKNOWN'}`,
      `Summary: ${triage?.summary || ''}`,
      ``,
      `LABORATORY SPECIALIST:`,
      ...(patientData.lab_alerts?.map(
        (l) => `- ${l.name}: ${l.current_value} ${l.unit} (${l.alert_type}) — ${l.clinical_significance}`
      ) || ['- Stable normal baseline.']),
      ``,
      `PHARMACOLOGY SPECIALIST:`,
      ...(patientData.drug_interactions?.map(
        (d) => `- ${d.drugs.join(' + ')} [${d.severity}]: ${d.mechanism} | Rec: ${d.recommendation}`
      ) || ['- No contraindicated drug combinations.']),
      ``,
      `ACTION DIRECTIVES:`,
      ...(triage?.action_items?.map((a) => `[ ] ${a}`) || ['- Routine care.']),
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    showToast('Clinical Note copied to clipboard');
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
      {toastMessage && (
        <div className="toast-min">
          <CheckCircle2 size={15} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Minimal Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand-minimal">
            <div className="brand-icon-min">
              <Stethoscope size={16} strokeWidth={2.2} />
            </div>
            <span className="brand-name">AegisClinical</span>
          </div>
        </div>

        <div className="search-wrap">
          <Search size={13} className="search-icon" />
          <input
            type="text"
            className="search-input-min"
            placeholder="Search patients..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="queue-header">
          <span className="queue-title">Queue</span>
          <span className="queue-title">{filteredPatients.length}</span>
        </div>

        <div className="queue-items">
          {filteredPatients.map((p) => {
            const isSelected = p.id === selectedId;
            return (
              <div
                key={p.id}
                className={`patient-row ${isSelected ? 'active' : ''}`}
                onClick={() => selectPatient(p)}
              >
                <div className="p-row-top">
                  <span className="p-name">{p.name}</span>
                  <span className="p-status-pip">
                    <span className={`pip-dot ${p.priority}`}></span>
                    <span>{p.priority}</span>
                  </span>
                </div>
                <div className="p-sub">{p.summary}</div>
              </div>
            );
          })}
        </div>

        <div className="sidebar-bottom">
          <label className="upload-button-min">
            <Upload size={14} />
            <span>{uploading ? 'Parsing...' : 'Upload FHIR R4 Bundle'}</span>
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
        <header className="top-identity-bar">
          <div className="identity-left">
            <h2>{loading ? 'Evaluating...' : patientData?.patient_name || 'Patient'}</h2>
            <div className="identity-tags">
              <span className="tag-mono">MRN: {patientData?.patient_id || 'UNKNOWN'}</span>
              <span>&bull;</span>
              <span>{patientData?.patient_age} years old</span>
              <span>&bull;</span>
              <span style={{ textTransform: 'capitalize' }}>{patientData?.gender}</span>
              <span>&bull;</span>
              <span className="tag-mono">FHIR R4</span>
            </div>
          </div>

          <div className="identity-actions">
            <button className="btn-minimal" onClick={handleCopyClinicalNote}>
              <ClipboardCopy size={13} />
              <span>Copy Note</span>
            </button>
            <div className="system-pill">
              <span className="sys-dot"></span>
              <span>LangGraph &bull; Ollama</span>
            </div>
          </div>
        </header>

        {error && (
          <div
            style={{
              padding: '0.85rem 1rem',
              backgroundColor: '#fff1f2',
              border: '1px solid #fecdd3',
              color: '#9f1239',
              borderRadius: '6px',
              marginBottom: '1.5rem',
              fontSize: '0.82rem',
            }}
          >
            {error}
          </div>
        )}

        {loading ? (
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '360px',
              color: '#71717a',
              gap: '0.75rem',
            }}
          >
            <Activity className="animate-spin" size={28} strokeWidth={1.8} color="#18181b" />
            <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>
              Evaluating clinical record...
            </span>
          </div>
        ) : (
          <>
            {/* Triage Callout */}
            <section className="triage-callout">
              <div className="triage-callout-header">
                <span className={`triage-pill-clean ${triageLevel}`}>
                  <span className={`pip-dot ${triageLevel}`}></span>
                  <span>{triageLevel} Priority Triage</span>
                </span>
              </div>
              <div className="triage-summary">
                {triage?.summary || 'Assessment completed.'}
              </div>
            </section>

            {/* Directives Checklist */}
            {triage?.action_items && triage.action_items.length > 0 && (
              <section className="directives-block">
                <div className="block-label">Clinical Directives</div>
                <div className="directives-wrap">
                  {triage.action_items.map((action, idx) => {
                    const isChecked = !!checkedDirectives[idx];
                    return (
                      <div
                        key={idx}
                        className="directive-row"
                        onClick={() => toggleDirective(idx)}
                      >
                        <div className={`check-box ${isChecked ? 'checked' : ''}`}>
                          {isChecked && <Check size={11} strokeWidth={3} />}
                        </div>
                        <span
                          style={{
                            textDecoration: isChecked ? 'line-through' : 'none',
                            color: isChecked ? '#a1a1aa' : 'inherit',
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

            {/* 3-Column Evidence Bento */}
            <div className="evidence-grid">
              {/* Lab Specialist */}
              <div className="evidence-col">
                <div className="col-header">
                  <div className="col-header-title">
                    <FlaskConical size={15} strokeWidth={2} />
                    <span>Laboratory</span>
                  </div>
                  <span className="col-badge">{labAlerts.length}</span>
                </div>
                <div className="col-body">
                  {labAlerts.length > 0 ? (
                    labAlerts.map((lab, i) => (
                      <div key={i} className={`item-card ${lab.severity}`}>
                        <div className="item-title-row">
                          <span className="item-title">{lab.name}</span>
                          <span className={`item-pill ${lab.severity}`}>{lab.alert_type}</span>
                        </div>
                        <div className="item-values">
                          <span>{lab.current_value} {lab.unit}</span>
                          {lab.baseline_value != null && (
                            <span style={{ color: '#71717a', marginLeft: '0.4rem', fontSize: '0.76rem' }}>
                              (Base: {lab.baseline_value})
                            </span>
                          )}
                        </div>
                        <div className="item-subtext">{lab.clinical_significance}</div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-clean">
                      <p>All analytes within normal limits.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Pharmacology Specialist */}
              <div className="evidence-col">
                <div className="col-header">
                  <div className="col-header-title">
                    <Pill size={15} strokeWidth={2} />
                    <span>Pharmacology</span>
                  </div>
                  <span className="col-badge">{drugInteractions.length}</span>
                </div>
                <div className="col-body">
                  {drugInteractions.length > 0 ? (
                    drugInteractions.map((ddi, i) => (
                      <div key={i} className={`item-card ${ddi.severity}`}>
                        <div className="item-title-row">
                          <span className="item-title">{ddi.drugs.join(' + ')}</span>
                          <span className={`item-pill ${ddi.severity}`}>{ddi.severity}</span>
                        </div>
                        <div className="item-subtext">{ddi.mechanism}</div>
                        <div className="item-rec">Rec: {ddi.recommendation}</div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-clean">
                      <p>No contraindications detected.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Medical History */}
              <div className="evidence-col">
                <div className="col-header">
                  <div className="col-header-title">
                    <HeartPulse size={15} strokeWidth={2} />
                    <span>Medical History</span>
                  </div>
                  <span className="col-badge">{chronicConditions.length}</span>
                </div>
                <div className="col-body">
                  {chronicConditions.length > 0 ? (
                    chronicConditions.map((cond, i) => (
                      <div key={i} className="item-card">
                        <div className="item-title-row">
                          <span className="item-title">{cond.display}</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.72rem', color: '#71717a' }}>
                            {cond.code}
                          </span>
                        </div>
                        <div className="item-subtext" style={{ textTransform: 'uppercase', fontSize: '0.7rem' }}>
                          Status: {cond.status}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-clean">
                      <p>No active chronic comorbidities.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Minimal Audit Bar */}
            <section className="audit-bar-min">
              <button
                className="btn-minimal"
                onClick={() => setShowAudit(!showAudit)}
              >
                <FileCode size={13} />
                <span>{showAudit ? 'Hide State Inspector' : 'Inspect Pydantic State'}</span>
                {showAudit ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
              </button>

              {showAudit && (
                <button
                  className="btn-minimal"
                  onClick={() => {
                    navigator.clipboard.writeText(JSON.stringify(patientData, null, 2));
                    showToast('State JSON copied to clipboard');
                  }}
                >
                  <ClipboardCopy size={13} />
                  <span>Copy JSON</span>
                </button>
              )}
            </section>

            {showAudit && (
              <div className="audit-viewer-min">
                <pre>{JSON.stringify(patientData, null, 2)}</pre>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
