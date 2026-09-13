"""AegisClinical CDSS: Multi-Agent Clinical Decision Support System.

A zero-credit-card, 100% open-source clinical decision support application
powered by LangGraph, Synthea FHIR R4, and local SLM inference.
"""

import json
from pathlib import Path
import streamlit as st

from src.parser import parse_synthea_bundle
from src.graph import clinical_graph
from src.schemas import TriageAssessment

# Page configuration
st.set_page_config(
    page_title="AegisClinical CDSS",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Swiss Medical CSS
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    .main-header {
        padding: 1rem 0 1.5rem 0;
        border-bottom: 1px solid #e2e8f0;
        margin-bottom: 1.5rem;
    }
    .main-title {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .main-subtitle {
        font-size: 0.95rem;
        color: #64748b;
        margin-top: 0.25rem;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        background-color: #f1f5f9;
        border: 1px solid #cbd5e1;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 500;
        color: #334155;
        margin-top: 0.5rem;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        margin-right: 6px;
    }

    /* Risk Banners */
    .risk-banner {
        padding: 1.25rem 1.5rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        border: 1px solid transparent;
    }
    .risk-banner-high {
        background-color: #fef2f2;
        border-color: #fecaca;
        color: #991b1b;
    }
    .risk-banner-medium {
        background-color: #fffbeb;
        border-color: #fde68a;
        color: #92400e;
    }
    .risk-banner-low {
        background-color: #f0fdf4;
        border-color: #bbf7d0;
        color: #166534;
    }
    .risk-badge {
        font-size: 0.85rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        padding: 0.2rem 0.6rem;
        border-radius: 4px;
        display: inline-block;
        margin-bottom: 0.4rem;
    }
    .risk-badge-high { background-color: #dc2626; color: #ffffff; }
    .risk-badge-medium { background-color: #d97706; color: #ffffff; }
    .risk-badge-low { background-color: #16a34a; color: #ffffff; }

    /* Bento Cards */
    .bento-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1.25rem;
        height: 100%;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.04);
    }
    .bento-title {
        font-size: 0.95rem;
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.85rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 0.5rem;
    }

    .alert-chip {
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        margin-bottom: 0.6rem;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .alert-chip-critical {
        background-color: #fff1f2;
        border-left: 4px solid #e11d48;
        color: #881337;
    }
    .alert-chip-high {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        color: #991b1b;
    }
    .alert-chip-medium {
        background-color: #fffbeb;
        border-left: 4px solid #f59e0b;
        color: #92400e;
    }
    .alert-chip-safe {
        background-color: #f0fdf4;
        border-left: 4px solid #10b981;
        color: #065f46;
    }

    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 0.5rem;
        font-size: 0.9rem;
        color: #1e293b;
        margin-bottom: 0.4rem;
        background: #f8fafc;
        padding: 0.5rem 0.75rem;
        border-radius: 6px;
        border: 1px solid #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DATA_DIR = Path(__file__).parent / "data" / "patients"

PATIENT_PRESETS = {
    "🔴 Arthur Morales (68M) - AKI & Triple Whammy": DATA_DIR / "patient_01_high_risk.json",
    "🟡 Elena Rostova (63F) - Hyperkalemia & Dual Blockade": DATA_DIR / "patient_02_med_risk.json",
    "🟢 James Chen (45M) - Stable Baseline / Normal": DATA_DIR / "patient_03_low_risk.json",
}

# Sidebar
with st.sidebar:
    st.markdown("### 🏥 Clinical Triage Queue")
    selected_preset = st.radio(
        "Select synthetic patient case:",
        list(PATIENT_PRESETS.keys()),
        index=0,
    )

    st.markdown("---")
    st.markdown("### 📤 Custom FHIR Bundle")
    uploaded_file = st.file_uploader(
        "Upload Synthea FHIR R4 JSON",
        type=["json"],
        help="Upload any synthetic Synthea FHIR R4 JSON Bundle to evaluate.",
    )

    st.markdown("---")
    st.markdown("### ⚙️ Engine Telemetry")
    st.markdown(
        """
        - **Orchestration**: LangGraph Scatter-Gather
        - **Inference**: Local SLM (Ollama)
        - **Privacy**: 100% On-Device (Zero Cloud PHI)
        - **Parser**: Zero-Dependency Stdlib
        """
    )

# Determine data source
if uploaded_file is not None:
    try:
        source_data = json.load(uploaded_file)
        patient_data = parse_synthea_bundle(source_data)
        st.sidebar.success("Custom bundle parsed successfully")
    except Exception as e:
        st.sidebar.error(f"Error parsing uploaded JSON: {e}")
        patient_data = parse_synthea_bundle(PATIENT_PRESETS[selected_preset])
else:
    patient_data = parse_synthea_bundle(PATIENT_PRESETS[selected_preset])

# Execute LangGraph Multi-Agent Pipeline
initial_state = {
    **patient_data,
    "lab_alerts": [],
    "drug_interactions": [],
    "chronic_conditions": [],
    "triage_assessment": None,
}

with st.spinner("Multi-Agent Clinical Evaluation in progress..."):
    result = clinical_graph.invoke(initial_state)

triage: TriageAssessment = result.get("triage_assessment")
lab_alerts = result.get("lab_alerts", [])
drug_interactions = result.get("drug_interactions", [])
chronic_conditions = result.get("chronic_conditions", [])

# Header
st.markdown(
    f"""
    <div class="main-header">
        <div class="main-title">AegisClinical Decision Support System</div>
        <div class="main-subtitle">Autonomous Multi-Specialty Triage & Patient Safety Engine</div>
        <div class="status-pill">
            <span class="status-dot"></span>
            Patient ID: <strong>{result.get('patient_id')}</strong> &nbsp;|&nbsp;
            Name: <strong>{result.get('patient_name')}</strong> &nbsp;|&nbsp;
            Age: <strong>{result.get('patient_age')}</strong> &nbsp;|&nbsp;
            Gender: <strong>{str(result.get('gender', '')).title()}</strong>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Triage Risk Banner
risk_level = triage.triage_level if triage else "UNKNOWN"
badge_class = f"risk-badge-{risk_level.lower()}"
banner_class = f"risk-banner-{risk_level.lower()}"

st.markdown(
    f"""
    <div class="risk-banner {banner_class}">
        <div class="risk-badge {badge_class}">{risk_level} PRIORITY TRIAGE</div>
        <div style="font-size: 1.05rem; font-weight: 600; margin-bottom: 0.35rem;">
            {triage.summary if triage else 'No assessment available.'}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Action Items Section
if triage and triage.action_items:
    st.markdown("##### ⚡ Urgent Clinical Action Items")
    for act in triage.action_items:
        st.markdown(
            f"""
            <div class="action-item">
                <span>⚠️</span>
                <span><strong>{act}</strong></span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("<br>", unsafe_allow_html=True)

# 3-Column Evidence Bento
col1, col2, col3 = st.columns(3)

# Column 1: Lab Specialist Agent
with col1:
    st.markdown(
        """
        <div class="bento-title">
            <span>🧪</span>
            <span>Laboratory Specialist Agent</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if lab_alerts:
        for alert in lab_alerts:
            severity_class = (
                "critical"
                if alert.severity == "CRITICAL"
                else "high"
                if alert.severity == "HIGH"
                else "medium"
            )
            baseline_str = (
                f"(Baseline: {alert.baseline_value} {alert.unit})"
                if alert.baseline_value is not None
                else ""
            )
            st.markdown(
                f"""
                <div class="alert-chip alert-chip-{severity_class}">
                    <strong>{alert.name}</strong>: {alert.current_value} {alert.unit} {baseline_str}<br>
                    <span style="font-size:0.75rem; text-transform:uppercase; font-weight:700;">[{alert.alert_type}]</span>
                    <p style="margin: 0.2rem 0 0 0; font-size: 0.8rem;">{alert.clinical_significance}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="alert-chip alert-chip-safe">
                <strong>Normal Findings</strong><br>
                All analyzed laboratory analytes are within reference thresholds and baseline stability.
            </div>
            """,
            unsafe_allow_html=True,
        )

# Column 2: Pharmacology Specialist Agent
with col2:
    st.markdown(
        """
        <div class="bento-title">
            <span>💊</span>
            <span>Pharmacology Specialist Agent</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if drug_interactions:
        for ddi in drug_interactions:
            sev_class = "critical" if ddi.severity == "CONTRAINDICATED" else "medium"
            drugs_str = " + ".join(ddi.drugs)
            st.markdown(
                f"""
                <div class="alert-chip alert-chip-{sev_class}">
                    <strong>{drugs_str}</strong><br>
                    <span style="font-size:0.75rem; text-transform:uppercase; font-weight:700;">[{ddi.severity}]</span>
                    <p style="margin: 0.2rem 0 0 0; font-size: 0.8rem;">{ddi.mechanism}</p>
                    <div style="margin-top: 0.35rem; font-size: 0.78rem; font-style: italic; color: #475569;">
                        Recommendation: {ddi.recommendation}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="alert-chip alert-chip-safe">
                <strong>No Contraindications Detected</strong><br>
                Active prescription regimen shows no dangerous cross-interactions.
            </div>
            """,
            unsafe_allow_html=True,
        )

# Column 3: Medical History Specialist Agent
with col3:
    st.markdown(
        """
        <div class="bento-title">
            <span>📋</span>
            <span>Medical History Specialist Agent</span>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if chronic_conditions:
        for cond in chronic_conditions:
            st.markdown(
                f"""
                <div class="alert-chip alert-chip-medium">
                    <strong>{cond.display}</strong><br>
                    <span style="font-size:0.75rem; font-family: 'JetBrains Mono', monospace;">ICD-10: {cond.code}</span>
                    &nbsp;|&nbsp;
                    <span style="font-size:0.75rem; text-transform: uppercase;">Status: {cond.status}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.markdown(
            """
            <div class="alert-chip alert-chip-safe">
                <strong>No Chronic Comorbidities</strong><br>
                No active historical chronic condition diagnoses recorded.
            </div>
            """,
            unsafe_allow_html=True,
        )

# Full Clinical Data & State Audit Trail
st.markdown("---")
with st.expander("🔍 Clinical Graph Audit Trail & Serialized Pydantic State (Audit Transparency)"):
    # Convert Pydantic models to dicts for clean JSON view
    serializable_result = {
        "patient_id": result.get("patient_id"),
        "patient_name": result.get("patient_name"),
        "patient_age": result.get("patient_age"),
        "gender": result.get("gender"),
        "lab_alerts": [a.model_dump() for a in lab_alerts],
        "drug_interactions": [d.model_dump() for d in drug_interactions],
        "chronic_conditions": [c.model_dump() for c in chronic_conditions],
        "triage_assessment": triage.model_dump() if triage else None,
        "raw_labs_count": len(result.get("raw_labs", [])),
        "raw_medications_count": len(result.get("raw_medications", [])),
        "raw_conditions_count": len(result.get("raw_conditions", [])),
    }
    st.json(serializable_result)
