import React, { useState, useEffect, useRef } from 'react';
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
  Moon,
  Pill,
  Search,
  ShieldAlert,
  ShieldCheck,
  Stethoscope,
  Sun,
  Upload,
} from 'lucide-react';

export default function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('aegis-theme') || 'light');
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

  const searchInputRef = useRef(null);

  // Sync theme with DOM attribute and local storage
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('aegis-theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  // Keyboard shortcut listener ('/' to focus search, 'c' to copy note)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
        if (e.key === 'Escape') {
          searchInputRef.current?.blur();
        }
        return;
      }
      if (e.key === '/') {
        e.preventDefault();
        searchInputRef.current?.focus();
      } else if (e.key === 'c' || e.key === 'C') {
        if (!e.metaKey && !e.ctrlKey) {
          handleCopyClinicalNote();
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [patientData]);

  // Load patient queue on initial mount
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

  // Fetch patient evaluation when selection changes
  useEffect(() => {
    if (!selectedId || selectedId.startsWith('custom_')) return;
    setCheckedDirectives({});
    setLoading(true);
    let active = true;

    fetch(`/api/patients/${selectedId}`)
      .then((res) => {
        if (!res.ok) throw new Error('Clinical evaluation failed');
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
      `AEGISCLINICAL CDSS — MULTI-AGENT TRIAGE ASSESSMENT`,
      `Patient: ${patientData.patient_name} | MRN: ${patientData.patient_id} | Age: ${patientData.patient_age} | Gender: ${patientData.gender}`,
      `Triage Priority: ${triage?.triage_level || 'UNKNOWN'}`,
      `Clinical Summary: ${triage?.summary || ''}`,
      ``,
      `LABORATORY SPECIALIST:`,
      ...(patientData.lab_alerts?.map(
        (l) => `- ${l.name}: ${l.current_value} ${l.unit} (${l.alert_type}) — ${l.clinical_significance}`
      ) || ['- Stable normal baseline.']),
      ``,
      `PHARMACOLOGY SPECIALIST:`,
      ...(patientData.drug_interactions?.map(
        (d) => `- ${d.drugs.join(' + ')} [${d.severity}]: ${d.mechanism} | Rec: ${d.recommendation}`
      ) || ['- No contraindicated combinations detected.']),
      ``,
      `ACTIVE ACTION DIRECTIVES:`,
      ...(triage?.action_items?.map((a, i) => `[${checkedDirectives[i] ? 'X' : ' '}] ${a}`) || ['- Routine outpatient monitoring.']),
    ];
    navigator.clipboard.writeText(lines.join('\n'));
    showToast('SOAP note copied to clipboard');
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

  // Patient Initials for Avatar
  const getInitials = (name) => {
    if (!name) return 'PT';
    return name
      .split(' ')
      .map((n) => n[0])
      .slice(0, 2)
      .join('')
      .toUpperCase();
  };

  // Biomarker Quick Stats
  const crLab = labAlerts.find((l) => l.name.toLowerCase().includes('creatinine'));
  const kLab = labAlerts.find((l) => l.name.toLowerCase().includes('potassium'));
  const crDelta =
    crLab && crLab.baseline_value
      ? (((crLab.current_value - crLab.baseline_value) / crLab.baseline_value) * 100).toFixed(0)
      : null;

  // Directives completed progress
  const totalDirectives = triage?.action_items?.length || 0;
  const completedDirectives = Object.values(checkedDirectives).filter(Boolean).length;
  const progressPercent = totalDirectives > 0 ? (completedDirectives / totalDirectives) * 100 : 0;

  return (
    <div className="app-container">
      {toastMessage && (
        <div className="toast-bar">
          <CheckCircle2 size={15} />
          <span>{toastMessage}</span>
        </div>
      )}

      {/* Modern Minimal Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="brand-wrap">
            <div className="brand-icon">
              <Stethoscope size={16} strokeWidth={2.2} />
            </div>
            <div className="brand-text">
              <span className="brand-title">AegisClinical</span>
              <span className="brand-subtitle">Local CDSS</span>
            </div>
          </div>
        </div>

        <div className="search-container">
          <Search size={13} className="search-icon-pos" />
          <input
            ref={searchInputRef}
            type="text"
            className="search-input-box"
            placeholder="Search patient record..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className="search-shortcut-hint">/</span>
        </div>

        <div className="queue-header-row">
          <span className="queue-label">Clinical Queue</span>
          <span className="queue-badge-count">{filteredPatients.length} active</span>
        </div>

        <div className="queue-scroll">
          {filteredPatients.map((p) => {
            const isSelected = p.id === selectedId;
            return (
              <div
                key={p.id}
                className={`patient-card-min ${isSelected ? 'active' : ''}`}
                onClick={() => selectPatient(p)}
              >
                <div className="patient-card-top">
                  <span className="patient-name-min">{p.name}</span>
                  <span className={`priority-pill ${p.priority}`}>
                    {p.priority}
                  </span>
                </div>
                <div className="patient-card-desc">{p.summary}</div>
              </div>
            );
          })}
        </div>

        <div className="sidebar-footer">
          <label className="upload-button-bar">
            <Upload size={14} />
            <span>{uploading ? 'Evaluating bundle...' : 'Upload FHIR R4 Bundle'}</span>
            <input
              type="file"
              accept=".json"
              style={{ display: 'none' }}
              onChange={handleFileUpload}
              disabled={uploading}
            />
          </label>
          <div className="sidebar-controls-row">
            <span>Press <kbd style={{ fontFamily: 'var(--font-mono)' }}>C</kbd> to copy note</span>
            <button
              className="theme-toggle-btn"
              onClick={toggleTheme}
              aria-label="Toggle Dark / Light Mode"
            >
              {theme === 'light' ? <Moon size={13} /> : <Sun size={13} />}
              <span>{theme === 'light' ? 'Dark' : 'Light'}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Viewport */}
      <main className="main-viewport">
        {/* Patient Identity Header */}
        <header className="patient-header-bar">
          <div className="patient-identity-left">
            <div className="patient-avatar-monogram">
              {getInitials(patientData?.patient_name)}
            </div>
            <div className="patient-meta-block">
              <h2>{loading ? 'Evaluating record...' : patientData?.patient_name || 'Patient Case'}</h2>
              <div className="patient-tags-strip">
                <span className="mono-badge">MRN: {patientData?.patient_id || 'UNKNOWN'}</span>
                <span>&bull;</span>
                <span>{patientData?.patient_age} yrs</span>
                <span>&bull;</span>
                <span style={{ textTransform: 'capitalize' }}>{patientData?.gender}</span>
                <span>&bull;</span>
                <span className="mono-badge">Synthea FHIR R4</span>
              </div>
            </div>
          </div>

          <div className="patient-header-actions">
            <button className="btn-pill-action" onClick={handleCopyClinicalNote}>
              <ClipboardCopy size={13} />
              <span>Copy SOAP Note</span>
            </button>
            <div className="engine-pill">
              <span className="pulse-indicator"></span>
              <span>LangGraph &bull; Ollama</span>
            </div>
          </div>
        </header>

        {error && (
          <div
            style={{
              padding: '0.85rem 1rem',
              backgroundColor: 'var(--status-high-bg)',
              border: '1px solid var(--status-high-border)',
              color: 'var(--status-high)',
              borderRadius: 'var(--radius-md)',
              marginBottom: '1.5rem',
              fontSize: '0.82rem',
              fontWeight: 500,
            }}
          >
            {error}
          </div>
        )}

        {loading ? (
          /* Shimmering Skeleton Loader */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
            <div className="skeleton-box" style={{ height: '70px', width: '100%' }}></div>
            <div className="skeleton-box" style={{ height: '110px', width: '100%' }}></div>
            <div className="skeleton-box" style={{ height: '130px', width: '100%' }}></div>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(3, 1fr)',
                gap: '1.25rem',
              }}
            >
              <div className="skeleton-box" style={{ height: '240px' }}></div>
              <div className="skeleton-box" style={{ height: '240px' }}></div>
              <div className="skeleton-box" style={{ height: '240px' }}></div>
            </div>
          </div>
        ) : (
          <>
            {/* Quick Biomarker Strip */}
            <div className="quick-metrics-row">
              <div className="metric-card">
                <span className="metric-label">Creatinine Delta</span>
                <div className="metric-value-wrap">
                  <span className="metric-value">
                    {crLab ? crLab.current_value : '--'}
                  </span>
                  <span className="metric-unit">mg/dL</span>
                  {crDelta && (
                    <span className={`metric-delta ${Number(crDelta) > 50 ? 'alert' : 'warn'}`}>
                      +{crDelta}%
                    </span>
                  )}
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Serum Potassium</span>
                <div className="metric-value-wrap">
                  <span className="metric-value">
                    {kLab ? kLab.current_value : (labAlerts.find(l => l.name.toLowerCase().includes('potassium'))?.current_value || '4.2')}
                  </span>
                  <span className="metric-unit">mEq/L</span>
                  <span className={`metric-delta ${kLab && kLab.severity === 'CRITICAL' ? 'alert' : 'normal'}`}>
                    {kLab ? kLab.alert_type : 'NORMAL'}
                  </span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Active Medications</span>
                <div className="metric-value-wrap">
                  <span className="metric-value">{patientData?.raw_medications?.length || 0}</span>
                  <span className="metric-unit">Rx orders</span>
                </div>
              </div>

              <div className="metric-card">
                <span className="metric-label">Chronic Conditions</span>
                <div className="metric-value-wrap">
                  <span className="metric-value">{chronicConditions.length}</span>
                  <span className="metric-unit">diagnoses</span>
                </div>
              </div>
            </div>

            {/* Authoritative Triage Banner */}
            <section className={`triage-hero-box ${triageLevel}`}>
              <div className="triage-hero-top">
                <div className={`triage-badge-main ${triageLevel}`}>
                  {triageLevel === 'HIGH' && <ShieldAlert size={16} strokeWidth={2.2} />}
                  {triageLevel === 'MEDIUM' && <AlertTriangle size={16} strokeWidth={2.2} />}
                  {triageLevel === 'LOW' && <ShieldCheck size={16} strokeWidth={2.2} />}
                  <span>{triageLevel} Priority Triage Protocol</span>
                </div>
                <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                  Synthesized Decision
                </span>
              </div>
              <p className="triage-hero-summary">
                {triage?.summary || 'Triage analysis completed.'}
              </p>
            </section>

            {/* Clinical Directives Checklist */}
            {triage?.action_items && triage.action_items.length > 0 && (
              <section className="directives-card">
                <div className="directives-header-row">
                  <div className="directives-header-title">
                    <Activity size={15} strokeWidth={2.2} />
                    <span>Clinical Directives & Interventions</span>
                  </div>
                  <span className="progress-summary">
                    {completedDirectives} of {totalDirectives} acknowledged
                  </span>
                </div>

                <div className="progress-bar-bg">
                  <div
                    className="progress-bar-fill"
                    style={{ width: `${progressPercent}%` }}
                  ></div>
                </div>

                <div className="directives-list">
                  {triage.action_items.map((action, idx) => {
                    const isChecked = !!checkedDirectives[idx];
                    return (
                      <div
                        key={idx}
                        className="directive-item-row"
                        onClick={() => toggleDirective(idx)}
                      >
                        <div className={`check-box-min ${isChecked ? 'checked' : ''}`}>
                          {isChecked && <Check size={11} strokeWidth={3} />}
                        </div>
                        <span
                          style={{
                            textDecoration: isChecked ? 'line-through' : 'none',
                            color: isChecked ? 'var(--text-muted)' : 'inherit',
                            lineHeight: 1.45,
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
            <div className="bento-grid">
              {/* Laboratory Specialist Column */}
              <div className="bento-column">
                <div className="bento-col-header">
                  <div className="bento-col-title">
                    <FlaskConical size={15} strokeWidth={2.2} />
                    <span>Laboratory</span>
                  </div>
                  <span className="bento-col-count">{labAlerts.length} findings</span>
                </div>
                <div className="bento-col-content">
                  {labAlerts.length > 0 ? (
                    labAlerts.map((lab, i) => (
                      <div key={i} className={`evidence-card ${lab.severity}`}>
                        <div className="evidence-card-header">
                          <span className="evidence-card-title">{lab.name}</span>
                          <span className={`evidence-tag ${lab.severity}`}>{lab.alert_type}</span>
                        </div>
                        <div className="evidence-metric-row">
                          <span>{lab.current_value} {lab.unit}</span>
                          {lab.baseline_value != null && (
                            <span style={{ color: 'var(--text-muted)', fontSize: '0.74rem' }}>
                              (Baseline: {lab.baseline_value})
                            </span>
                          )}
                        </div>
                        <p className="evidence-desc">{lab.clinical_significance}</p>
                      </div>
                    ))
                  ) : (
                    <div className="empty-placeholder">
                      <p>All laboratory analytes are within safe reference ranges.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Pharmacology Specialist Column */}
              <div className="bento-column">
                <div className="bento-col-header">
                  <div className="bento-col-title">
                    <Pill size={15} strokeWidth={2.2} />
                    <span>Pharmacology</span>
                  </div>
                  <span className="bento-col-count">{drugInteractions.length} alerts</span>
                </div>
                <div className="bento-col-content">
                  {drugInteractions.length > 0 ? (
                    drugInteractions.map((ddi, i) => (
                      <div key={i} className={`evidence-card ${ddi.severity}`}>
                        <div className="evidence-card-header">
                          <span className="evidence-card-title">{ddi.drugs.join(' + ')}</span>
                          <span className={`evidence-tag ${ddi.severity}`}>{ddi.severity}</span>
                        </div>
                        <p className="evidence-desc">{ddi.mechanism}</p>
                        <div className="evidence-rec-box">Rec: {ddi.recommendation}</div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-placeholder">
                      <p>No dangerous drug-drug or drug-disease interactions detected.</p>
                    </div>
                  )}
                </div>
              </div>

              {/* Medical History Specialist Column */}
              <div className="bento-column">
                <div className="bento-col-header">
                  <div className="bento-col-title">
                    <HeartPulse size={15} strokeWidth={2.2} />
                    <span>Medical History</span>
                  </div>
                  <span className="bento-col-count">{chronicConditions.length} active</span>
                </div>
                <div className="bento-col-content">
                  {chronicConditions.length > 0 ? (
                    chronicConditions.map((cond, i) => (
                      <div key={i} className="evidence-card">
                        <div className="evidence-card-header">
                          <span className="evidence-card-title">{cond.display}</span>
                          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.7rem', color: 'var(--text-muted)' }}>
                            {cond.code}
                          </span>
                        </div>
                        <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', textTransform: 'uppercase', fontFamily: 'var(--font-mono)' }}>
                          Clinical Status: {cond.status}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="empty-placeholder">
                      <p>No active chronic comorbidities documented.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Collapsible State Inspector */}
            <section className="audit-drawer">
              <div className="audit-drawer-controls">
                <button
                  className="btn-pill-action"
                  onClick={() => setShowAudit(!showAudit)}
                >
                  <FileCode size={13} />
                  <span>{showAudit ? 'Hide State Inspector' : 'Inspect Pydantic Graph State'}</span>
                  {showAudit ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
                </button>

                {showAudit && (
                  <button
                    className="btn-pill-action"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(patientData, null, 2));
                      showToast('Pydantic State JSON copied');
                    }}
                  >
                    <ClipboardCopy size={13} />
                    <span>Copy JSON</span>
                  </button>
                )}
              </div>

              {showAudit && (
                <pre className="audit-pre">
                  {JSON.stringify(patientData, null, 2)}
                </pre>
              )}
            </section>
          </>
        )}
      </main>
    </div>
  );
}
