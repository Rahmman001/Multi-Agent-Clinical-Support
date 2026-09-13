# Clinical Design System: Multi-Agent Triage Dashboard

> **Design Standard**: `design-taste-frontend` + `impeccable`  
> **Target Audience**: Emergency & attending physicians, hospital triage nurses, clinical system architects  
> **Philosophy**: Precision clinical ergonomics, zero AI fluff, high legibility under high cognitive load

---

## 0. Brief Inference & Design Read

> **Design Read:**  
> *"Reading this as: Clinical Decision Support & Physician Triage Dashboard for healthcare professionals, with an impeccable Swiss medical / precision engineering visual language, leaning toward Tailwind CSS + Geist/Geist Mono + WCAG AAA accessible clinical tokens."*

### The Three Dials Configuration

| Dial | Level | Implementation Rationale |
| :--- | :---: | :--- |
| **`DESIGN_VARIANCE`** | **`6`** | Disciplined, structured bento grid with asymmetric evidence sizing; predictable enough for fast clinical scanning, distinct enough to avoid symmetrical grid fatigue. |
| **`MOTION_INTENSITY`** | **`4`** | Restrained & functional. Subtle status pulses, smooth accordion reveals, instant filter updates. **Zero** theatrical animations or distractions in critical healthcare environments. |
| **`VISUAL_DENSITY`** | **`7`** | Cockpit-level information density. Compact numeric lab tables, tabular numerical alignment, and tight card borders without visual noise or claustrophobia. |

---

## 1. Clinical Visual Philosophy & Anti-Slop Discipline

### What Makes Typical AI Clinical Demos Look Amateur
- **AI Purple Gradients**: Decorative pastel/violet meshes that scream "generic tech demo" rather than medical software.
- **Unearned Confidence Meters**: Vague radial progress bars showing "94% Confidence" without clinical backing.
- **Monolithic Text Paragraphs**: Large walls of unformatted text that force busy clinicians to read 500 words just to find one lab abnormal.
- **Missing Line-Item Provenance**: Diagnoses presented without citing the exact lab test, date, or contraindication mechanism.

### The "Calm Cockpit" Standard
1. **Scannability in Under 5 Seconds**: A clinician glancing at the screen must immediately understand:
   - The patient's risk tier (**HIGH / MEDIUM / LOW**).
   - The primary lethal threat (e.g., *Creatinine +45% AKI* or *Triple Whammy DDI*).
   - The three immediate recommended clinical actions.
2. **Dual-Encoding for Safety**: Every risk state is encoded via **Color + Icon + Explicit Text** (e.g., Red + Octagon Warning + "CRITICAL AKI STAGE 1"). Color alone is never used to convey meaning.
3. **Tabular Numeric Precision**: All bloodwork, dosages, and vital signs are formatted in fixed-width tabular monospace typography to ensure decimal alignment.

---

## 2. Color Palette & Medical Tokens

The palette is tuned for long hospital shifts (dark and crisp clinical light themes) with high-contrast, WCAG AAA compliant semantic status tokens.

### 2.1 Surfaces & Neutrals
- **Canvas Base (`#090A0F`)**: Deepest midnight obsidian for dark mode; clean alabaster (`#F8FAFC`) in light mode.
- **Surface Elevation 1 (`#11131A`)**: Card and container background; subtle 1px whisper border.
- **Surface Elevation 2 (`#1A1D27`)**: Nested sub-panels (e.g., specific lab rows, code chips).
- **Whisper Border (`rgba(255, 255, 255, 0.08)`)**: Crisp architectural separation without heavy dark outlines.
- **Text Primary (`#F1F5F9`)**: Slate-100 high-legibility text (contrast ratio > 12:1).
- **Text Secondary (`#94A3B8`)**: Slate-400 for units, timestamps, and reference intervals.
- **Text Tertiary (`#64748B`)**: Slate-500 for captions, metadata, and inactive elements.

### 2.2 Clinical Severity Alert Tokens

| Severity | Hex Accent | Background Fill | Border | Icon & Badge Meaning |
| :--- | :--- | :--- | :--- | :--- |
| 🔴 **HIGH (Emergency / Stage 2+ AKI / Major DDI)** | `#EF4444` (Crimson) | `rgba(239, 68, 68, 0.12)` | `rgba(239, 68, 68, 0.35)` | Immediate action required; acute organ distress or lethal contraindication. |
| 🟡 **MEDIUM (Urgent / Trend Warning)** | `#F59E0B` (Amber) | `rgba(245, 158, 11, 0.12)` | `rgba(245, 158, 11, 0.35)` | Subacute abnormality; lab delta trending upward or moderate interaction. |
| 🟢 **LOW (Stable / Controlled)** | `#10B981` (Emerald) | `rgba(16, 185, 129, 0.12)` | `rgba(16, 185, 129, 0.35)` | Normal reference ranges, baseline chronic conditions well-managed. |
| 🔵 **CLINICAL ACCENT (Information / Telemetry)** | `#0284C7` (Sky-600) | `rgba(2, 132, 199, 0.12)` | `rgba(2, 132, 199, 0.30)` | Active agent execution, system status, metadata filters. |

### 2.3 Banned Color Habits
- **NO** purple/magenta/violet gradients.
- **NO** uncalibrated neon highlights (`#00FF00` or `#FF0000`).
- **NO** low-contrast gray text on dark backgrounds (must meet WCAG AA minimum 4.5:1).

---

## 3. Typography Hierarchy

Medical typography demands strict separation between narrative text and clinical measurements.

```
Display:           Geist Sans / Plus Jakarta Sans (600 / 700 weight, -0.025em tracking)
Body:              Geist Sans / Plus Jakarta Sans (400 weight, 1.55 leading)
Clinical / Labs:   Geist Mono / JetBrains Mono (500 weight, tabular-nums)
```

### Type Scale & Encoding

| Token | Size / Line-Height | Font Family | Usage |
| :--- | :--- | :--- | :--- |
| **`text-triage-hero`** | `2.25rem (36px) / 1.15` | Sans 700 | Patient Name & Triage Risk Banner |
| **`text-section-title`**| `1.125rem (18px) / 1.3` | Sans 600 | Domain Agent Card Headers (`Lab Findings`, `Drug Interactions`) |
| **`text-metric-value`** | `1.5rem (24px) / 1.2`  | **Mono 600**| Quantitative values (`1.92 mg/dL`, `45% Delta`, `142/90 mmHg`) |
| **`text-body-regular`** | `0.9375rem (15px) / 1.55`| Sans 400 | Executive Clinical Summary, mechanism explanations |
| **`text-metadata`**     | `0.8125rem (13px) / 1.4`| **Mono 400**| LOINC / RxNorm codes, timestamps, normal reference ranges |

---

## 4. Layout Architecture: The Tri-Agent Bento Canvas

The dashboard is organized into three distinct visual regions:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│  CLINICAL SUPPORT OS  •  Ollama Local Model: llama3.2:3b  •  Active Pipeline: ONLINE    │
├───────────────────┬────────────────────────────────────────────────────────────────────┤
│ PATIENT QUEUE     │ PATIENT HEADER: John Doe, 68M  •  MRN: #849204  •  [ 🔴 HIGH RISK ] │
│ ───────────────── │ ────────────────────────────────────────────────────────────────── │
│ 🔴 Doe, John      │ EXECUTIVE SUMMARY:                                                 │
│    AKI Stage 1    │ Patient presents with a 45% serum creatinine spike over 48h while  │
│    Triple Whammy  │ concurrently prescribed Lisinopril, Furosemide, and OTC Ibuprofen. │
│                   ├──────────────────────────────────┬─────────────────────────────────┤
│ 🟡 Smith, Sarah   │ 🔬 LAB AGENT CARD (40% width)    │ 💊 PHARMA AGENT CARD (60% width)│
│    Hypokalemia    │ • Creatinine: 1.9 mg/dL (▲ 45%)  │ ⚠️ TRIPLE WHAMMY DETECTED       │
│                   │ • eGFR: 32 mL/min (▼ 18)         │ • Lisinopril 20mg + Furosemide  │
│ 🟢 Patel, Amit    │ • Potassium: 5.6 mEq/L (HIGH)    │   40mg + Ibuprofen 400mg        │
│    Controlled T2D ├──────────────────────────────────┴─────────────────────────────────┤
│                   │ 📋 HISTORY AGENT CARD: Chronic Conditions                          │
│                   │ • Type 2 Diabetes (Onset: 2017)  • Essential Hypertension (2014)   │
│                   ├────────────────────────────────────────────────────────────────────┤
│                   │ ▾ RAW PROVENANCE & AGENT TRACE (Collapsible JSON Schema)           │
└───────────────────┴────────────────────────────────────────────────────────────────────┘
```

### 4.1 Component Specifications

#### 1. Patient Queue (Left Rail — 280px Fixed)
- Sort controls: `Risk Severity (Default)` | `Time of Arrival` | `Alphabetical`.
- Patient Row Item:
  - Left edge 3px vertical accent strip matching severity color.
  - Patient Name, Age, Biological Sex, and Primary Risk Badge.
  - Hover state: `-1px translateY`, background shifts to `Surface Elevation 2`.
  - Active state: Distinct 1px border ring in Clinical Accent.

#### 2. Clinical Header & Triage Badge (Top Banner)
- Patient Demographics: Name, MRN, Age/Gender, Admission Date.
- Triage Score Badge:
  - Giant pill: `18px font-weight 700`, uppercase, with pulsing radar dot on High Risk.
  - Clear rationale text underneath: *"Criteria met: KDIGO AKI Stage 1 delta + concurrent nephrotoxic prescription triad."*

#### 3. Domain Evidence Bento Cards
- **Card 1: Laboratory Findings (Lab Agent)**
  - Structured comparative table: `Test Name`, `Baseline`, `Current`, `Delta %`, `Status`.
  - Jump indicator: Subtle badge (`▲ +45% in 48h`) highlighted in red if meeting KDIGO AKI criteria.
  - Reference interval pill: `[Normal: 0.7 - 1.2 mg/dL]`.
- **Card 2: Pharmaceutical Interactions (Pharma Agent)**
  - Drug interaction alert box with mechanism callout:
    - *Afferent arteriole constriction (NSAID) + Efferent arteriole dilation (ACEi) + Volume depletion (Diuretic).*
  - Pill list of all active medications with dosage and administration route.
- **Card 3: Comorbidity Context (History Agent)**
  - Clean chronological tag cloud of active conditions (SNOMED-CT mapped).
  - Risk multipliers surfaced: e.g., *"Pre-existing Type 2 Diabetes elevates acute renal vulnerability."*

#### 4. Collapsible Provenance Drawer
- Accordion header: `Inspect Agent Reasoning & Pydantic Validation (3 Nodes Checked)`.
- Code container displaying sanitized, typed JSON payload from LangGraph execution.
- Copy button for export to clinical notes.

---

## 5. Streamlit-Native Layout & Ergonomics (Zero-Hack Architecture)

Rather than fighting Streamlit's virtual DOM with fragile injected JavaScript listeners, the interface uses **native Streamlit primitives styled with clean CSS tokens**:

```python
# Minimalist, bulletproof Streamlit layout
import streamlit as st

st.set_page_config(page_title="Clinical Triage OS", layout="wide", initial_sidebar_state="expanded")

# Left Rail: 1-line native patient queue with instant arrow-key navigation
patient_id = st.sidebar.radio(
    "Patient Triage Queue",
    options=patient_list,
    format_func=lambda p: f"{p['risk_emoji']} {p['name']} ({p['summary_tag']})"
)

# Top Hero: Status Banner
st.markdown(f"<div class='triage-banner {patient['risk_class']}'>{patient['risk_badge']} {patient['risk_label']}</div>", unsafe_allow_html=True)

# 3-Column Bento Evidence Cards
col1, col2, col3 = st.columns([4, 4, 3])
with col1:
    st.subheader("🔬 Lab Anomalies")
    st.dataframe(patient['lab_df'], use_container_width=True)
with col2:
    st.subheader("💊 Drug Interactions")
    st.markdown(patient['ddi_html'], unsafe_allow_html=True)
with col3:
    st.subheader("📋 Comorbidities")
    st.write(patient['chronic_conditions'])

# Collapsible Raw Provenance: Native st.expander
with st.expander("🔍 Inspect Verified JSON State"):
    st.json(patient['raw_state'])
```

---

## 6. Accessibility & Safety Guardrails (WCAG 2.1 AAA)

1. **Dual-Encoding for Safety**: Every alert state is encoded via **Symbol + Color + Text Label**:
   - `▲ HIGH RISK`: `#EF4444` + Triangle badge
   - `◆ MEDIUM RISK`: `#F59E0B` + Diamond badge
   - `● LOW RISK`: `#10B981` + Circle badge
2. **Native Keyboard Accessibility**:
   - Up/Down arrows navigate the patient queue in `st.sidebar.radio`.
   - Enter/Space toggles `st.expander` provenance drawers natively.
3. **High Contrast Typography**:
   - Text on dark cards maintains $>12:1$ contrast ratio.
   - Tabular monospace numbers (`Geist Mono` or system `ui-monospace`) prevent decimal misalignment in lab values.

---

## 7. Implementation Checklist for Streamlit

- [x] Lock to single Python runtime (Streamlit on `localhost:8501`).
- [x] Use `st.sidebar.radio` for the triage queue with instant arrow-key navigation.
- [x] Inject clinical color tokens via a single concise `<style>` block.
- [x] Format lab test values using tabular monospace.
- [x] Use `st.expander` for collapsible Pydantic JSON provenance.
