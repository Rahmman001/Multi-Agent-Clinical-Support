# AegisClinical — Project Context & System State

> **Living context document** for developers and AI agents working on AegisClinical. Keep this file updated as architecture, clinical rules, APIs, or schemas evolve.

---

## 1. System Identity & Mission

**AegisClinical** is a local, privacy-first, zero-cloud Multi-Agent Clinical Decision Support System (CDSS) for Electronic Health Record (EHR) analysis.

* **Primary Purpose**: Ingest complex Synthea FHIR R4 clinical bundles, run parallel rule-based specialist agents (Lab, Pharmacology, Medical History), and synthesize actionable physician triage recommendations using a deterministic baseline with optional local LLM (`llama3.2:3b` via Ollama).
* **Privacy Baseline**: 100% on-device processing. No external API keys, zero PHI exfiltration, full HIPAA/GDPR local compatibility.
* **License**: MIT Open Source ([LICENSE](LICENSE)).

---

## 2. System Architecture & Topology

```
                  ┌─────────────────────────────────────────┐
                  │  Synthea FHIR R4 Bundle (JSON / File)   │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │   src/parser.py (Zero-dep stdlib json)  │
                  └────────────────────┬────────────────────┘
                                       │
       ┌───────────────────────────────┼───────────────────────────────┐
       ▼                               ▼                               ▼
┌──────────────┐              ┌────────────────┐              ┌─────────────────┐
│  Lab Agent   │              │  Pharma Agent  │              │  History Agent  │
│  KDIGO AKI & │              │  DDI Matrix &  │              │  Comorbidities  │
│  Panic Labs  │              │  Renal Whammy  │              │  & Chronics     │
└──────┬───────┘              └────────┬───────┘              └────────┬────────┘
       │                               │                               │
       └───────────────────────────────┼───────────────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │      Lead Triage Coordinator Agent      │
                  │   Composite Priority & Urgency Ordering │
                  └────────────────────┬────────────────────┘
                                       │
                         ┌─────────────┴─────────────┐
                         ▼                           ▼
            ┌────────────────────────┐  ┌────────────────────────┐
            │ Deterministic Summary  │  │ Local Ollama Synthesis │
            │ (Authoritative Rule)   │  │ (llama3.2:3b Optional) │
            └────────────┬───────────┘  └────────────┬───────────┘
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │   FastAPI Engine (api.py on port 8000)  │
                  └────────────────────┬────────────────────┘
                                       │
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │  Vite React 19 GUI (frontend/ port 5173)│
                  │  Hairline Borders, Soap Export, Triage  │
                  └─────────────────────────────────────────┘
```

---

## 3. Clinical Standards & Rules Engine

All clinical evaluation is implemented in [`src/rules.py`](src/rules.py) with zero external clinical dependencies:

1. **KDIGO 2012 AKI Criteria**:
   * **Stage 1**: Creatinine increase $\ge 0.3$ mg/dL within 48h, or $\ge 1.5\times$ to $1.9\times$ baseline within 7 days.
   * **Stage 2**: Creatinine increase $2.0\times$ to $2.9\times$ baseline.
   * **Stage 3**: Creatinine increase $\ge 3.0\times$ baseline, or current creatinine $\ge 4.0$ mg/dL with acute rise $\ge 0.5$ mg/dL.
2. **Panic Lab Thresholds**:
   * Serum Potassium: Critical $<2.8$ mEq/L or $>6.0$ mEq/L (Emergent ECG directive).
   * Hemoglobin: Critical $<7.0$ g/dL (Type & crossmatch directive).
   * Platelets: Critical $<20,000$ / $\mu$L.
   * Blood Glucose: Critical $<50$ or $>450$ mg/dL.
3. **Deterministic Pharmacology Interactions ($O(1)$ Hash Table)**:
   * **Triple Whammy**: ACE-Inhibitor/ARB + Diuretic + NSAID (Fatal prerenal AKI risk).
   * **Dual RAAS Blockade**: ACE-Inhibitor + ARB (Hyperkalemia and hypotension contraindication).
   * **Potassium Spironolactone + ACEI/ARB**: Severe hyperkalemia contraindication.
   * **NSAID in Renal Impairment**: Drug-disease contraindication.

---

## 4. Codebase Directory Map

```
.
├── api.py                  # FastAPI server providing /api/patients, /api/upload, and static mount
├── app.py                  # Streamlit prototype (legacy fallback)
├── start.sh                # 1-click execution script (venv + dependencies + frontend build + server)
├── CONTEXT.md              # Project reference and system state (this file)
├── README.md               # User & open-source documentation
├── requirements.txt        # Python dependencies (fastapi, uvicorn, langgraph, pydantic, pytest)
├── src/
│   ├── schemas.py          # Pydantic v2 data models & ClinicalGraphState TypedDict with reducers
│   ├── rules.py            # Mathematical KDIGO & DDI clinical rules engine
│   ├── parser.py           # Synthea FHIR R4 Bundle parser using stdlib json
│   ├── agents.py           # Lab, Pharma, History, and Lead Triage agents + Ollama client
│   └── graph.py            # LangGraph scatter-gather compilation
├── frontend/
│   ├── package.json        # React 19, Vite, Lucide-React
│   ├── src/
│   │   ├── App.jsx         # Minimalist clinical console, queue, directives, and SOAP copy
│   │   └── index.css       # Clean clinical design tokens (Inter, zinc borders, quiet pips)
│   └── dist/               # Production build served directly by FastAPI
├── data/patients/          # Synthetic test cases:
│   ├── patient_01_high_risk.json  # Stage 2 AKI + Triple Whammy (Arthur Morales)
│   ├── patient_02_med_risk.json   # Hyperkalemia + Dual RAAS Blockade (Elena Rostova)
│   └── patient_03_low_risk.json   # Stable Baseline (James Chen)
└── tests/
    ├── test_rules.py       # Clinical rule unit tests
    ├── test_parser.py      # FHIR bundle parsing tests
    ├── test_graph.py       # End-to-end LangGraph evaluation tests
    └── test_api.py         # FastAPI endpoint & payload size tests
```

---

## 5. Developer Runbook & Common Commands

### 1. One-Click Launch
```bash
./start.sh
```
Runs venv initialization, installs dependencies, builds frontend, checks Ollama, and starts `http://localhost:8000`.

### 2. Running Test Suite
```bash
.venv/bin/pytest tests/ -v
```
All 17 tests verify rule staging, parser edge cases, graph state accumulation, and API upload limits.

### 3. Frontend Development
```bash
cd frontend && npm run dev
```
Runs Vite dev server on `http://localhost:5173` with proxy to backend on port 8000.

### 4. Rebuilding Frontend
```bash
npm --prefix frontend run build
```

---

## 6. Key Design Decisions & Guarantees

* **Ponytail Discipline**: Minimum code that works. No speculative abstraction layers. Native Starlette threadpools used for synchronous graph execution instead of unnecessary manual worker pools.
* **Deterministic Priority**: LLM outputs never override safety rules. If Ollama is offline or generates invalid output, the system seamlessly falls back to the deterministic clinical summary.
* **Urgency Ordering**: Emergent cardiac/electrolyte directives always precede routine monitoring.
* **Client-side State Hygiene**: Directives checklist resets between patient records; custom uploads bypass remote GET lookups to prevent 404 races.
* **Clinical UI System**: Hairline zinc borders (`1px solid #e2e8f0` / `#27272a`), surgical Dark/Light theme toggle, zero-layout-shift skeleton loaders, dynamic acute biomarker strip (creatinine delta %, potassium alerts), directives completion progress bar, and keyboard shortcuts (`/` search focus, `C` SOAP note copy).
