# Technical Requirements Document (TRD)
## Multi-Agent Clinical Support System

> **Standard**: Zero-Fluff Engineering Specification  
> **Runtime**: Python 3.10+, Ollama (`llama3.2:3b`), Streamlit  
> **Guiding Principle**: Simplicity First ([`GEMINI.md`](../GEMINI.md)), 100% Free & Open-Source

---

## 1. System Architecture & Data Pipeline

The system is a deterministic, pipeline-driven decision support tool:

```
[Synthea FHIR JSON]
       │
       ▼ (stdlib json parser)
[Normalized Clinical Dict]
       │
       ├──────────────────────┬──────────────────────┐
       ▼                      ▼                      ▼
  [Lab Agent]           [Pharma Agent]        [History Agent]
  • KDIGO math          • O(1) Rule Table      • Comorbidities
  • Critical Panic vals • Ollama fallback       • Onset dates
       │                      │                      │
       └──────────────────────┼──────────────────────┘
                              ▼ (LangGraph State Reducer)
                     [Lead Triage Agent]
                     • Composite Risk Scoring (HIGH/MED/LOW)
                     • 3-sentence Physician Brief
                              │
                              ▼ (Streamlit UI)
                     [Doctor Triage Screen]
```

---

## 2. Directory & Module Layout

```text
Multi-Agent Clinical Support/
├── data/
│   └── patients/               # Synthea FHIR R4 JSON sample bundles
├── src/
│   ├── __init__.py
│   ├── schemas.py              # Pydantic models & LangGraph TypedDict state
│   ├── parser.py               # Stdlib JSON patient record extractor
│   ├── rules.py                # O(1) DDI lookup table & KDIGO threshold constants
│   ├── agents.py               # Lab, Pharma, History, and Triage agent nodes
│   └── graph.py                # LangGraph StateGraph assembly & compilation
├── tests/
│   ├── test_parser.py          # Unit tests for data extraction
│   ├── test_rules.py           # Unit tests for KDIGO & DDI detection
│   └── test_graph.py           # End-to-end multi-agent pipeline test
├── app.py                      # Streamlit physician dashboard
├── requirements.txt            # Minimal dependencies
└── README.md
```

---

## 3. Pydantic Data Contracts (`src/schemas.py`)

Every agent communicates via strict, typed schemas. No free-form unparsed markdown.

```python
from typing import List, Optional, Literal, Annotated
from typing_extensions import TypedDict
from pydantic import BaseModel, Field
import operator

# --- Domain Findings ---

class LabAlert(BaseModel):
    test_name: str
    current_value: float
    unit: str
    baseline_value: Optional[float] = None
    delta_percent: Optional[float] = None
    is_abnormal: bool
    kdigo_aki_stage: Optional[Literal[1, 2, 3]] = None
    clinical_risk: str

class DrugInteraction(BaseModel):
    drug_1: str
    drug_2: str
    severity: Literal["HIGH", "MEDIUM", "LOW"]
    mechanism: str
    recommendation: str

class ChronicCondition(BaseModel):
    name: str
    onset_date: Optional[str] = None
    status: str = "active"

# --- Lead Triage Synthesis ---

class TriageAssessment(BaseModel):
    risk_level: Literal["HIGH", "MEDIUM", "LOW"]
    primary_threat: str
    executive_summary: str
    recommended_actions: List[str]

# --- LangGraph Graph State ---

class ClinicalState(TypedDict):
    patient_id: str
    patient_name: str
    raw_patient_data: dict
    
    # State reducers allow parallel agent nodes to safely append results
    lab_alerts: Annotated[List[LabAlert], operator.add]
    drug_interactions: Annotated[List[DrugInteraction], operator.add]
    chronic_conditions: Annotated[List[ChronicCondition], operator.add]
    
    # Final Coordinator output
    triage_result: Optional[TriageAssessment]
```

---

## 4. Component Technical Specifications

### 4.1 Data Parser (`src/parser.py`)
- **Input**: Raw Synthea JSON FHIR bundle (`Bundle`).
- **Processing**: Pure stdlib `json`. Traverses `entry[]` array and routes resources by `resource.resourceType`:
  - `Observation` with `category == "laboratory"` $\rightarrow$ `labs`
  - `Observation` with `category == "vital-signs"` $\rightarrow$ `vitals`
  - `MedicationRequest` $\rightarrow$ `medications`
  - `Condition` $\rightarrow$ `conditions`
- **Output**: Clean normalized Python dictionary:
  ```python
  {
      "patient_id": str,
      "name": str,
      "age": int,
      "gender": str,
      "labs": list[dict],       # name, value, unit, date
      "medications": list[dict],# name, status, authored_on
      "conditions": list[dict], # name, onset_date, status
      "vitals": list[dict]      # name, value, unit
  }
  ```
- **Error Handling**: Missing non-critical fields fallback to `None` without crashing.

### 4.2 Clinical Knowledge Base (`src/rules.py`)
- **Deterministic KDIGO AKI Check**:
  ```python
  def evaluate_kdigo_aki(baseline: float, current: float) -> Optional[int]:
      """Evaluates Acute Kidney Injury stage based on serum creatinine."""
      if baseline <= 0: return None
      ratio = current / baseline
      diff = current - baseline
      if ratio >= 3.0 or current >= 4.0: return 3
      if ratio >= 2.0: return 2
      if diff >= 0.3 or ratio >= 1.5: return 1
      return None
  ```
- **High-Risk DDI Lookup Dictionary ($O(1)$)**:
  - Table mapping normalized drug pairs to severity & mechanisms:
    - `('lisinopril', 'furosemide', 'ibuprofen')` $\rightarrow$ Triple Whammy (High Risk, AKI)
    - `('warfarin', 'ibuprofen')` $\rightarrow$ Major GI Hemorrhage (High Risk)
    - `('spironolactone', 'lisinopril')` $\rightarrow$ Lethal Hyperkalemia (High Risk)

### 4.3 Domain Agents (`src/agents.py`)
1. **`lab_agent_node(state)`**:
   - Evaluates creatinine deltas using `evaluate_kdigo_aki`.
   - Flags critical panic values ($K^+ > 5.5$, $Hb < 7.0$).
   - Invokes local Ollama (`llama3.2:3b`) only if unstructured lab notes require clinical interpretation.
   - Appends `List[LabAlert]` to `state["lab_alerts"]`.
2. **`pharma_agent_node(state)`**:
   - Cross-references active medications against `DDI_RULES`.
   - Uses local Ollama to check any unmapped prescription combinations with strict JSON mode.
   - Appends `List[DrugInteraction]` to `state["drug_interactions"]`.
3. **`history_agent_node(state)`**:
   - Filters active chronic conditions (Diabetes, CKD, Hypertension).
   - Appends `List[ChronicCondition]` to `state["chronic_conditions"]`.
4. **`triage_coordinator_node(state)`**:
   - Computes composite risk level:
     - **HIGH**: Stage 2/3 AKI, $K^+ > 5.5$, OR any High-Risk DDI.
     - **MEDIUM**: Stage 1 AKI delta, single abnormal lab without delta, or Moderate DDI.
     - **LOW**: All labs within reference range, zero dangerous interactions.
   - Formulates concise 3-sentence summary and populates `state["triage_result"]`.

### 4.4 LangGraph Pipeline (`src/graph.py`)
```python
from langgraph.graph import StateGraph, START, END

def create_clinical_graph():
    builder = StateGraph(ClinicalState)
    builder.add_node("lab_agent", lab_agent_node)
    builder.add_node("pharma_agent", pharma_agent_node)
    builder.add_node("history_agent", history_agent_node)
    builder.add_node("triage_coordinator", triage_coordinator_node)
    
    # Scatter (Parallel Fan-out)
    builder.add_edge(START, "lab_agent")
    builder.add_edge(START, "pharma_agent")
    builder.add_edge(START, "history_agent")
    
    # Gather (Fan-in)
    builder.add_edge("lab_agent", "triage_coordinator")
    builder.add_edge("pharma_agent", "triage_coordinator")
    builder.add_edge("history_agent", "triage_coordinator")
    
    builder.add_edge("triage_coordinator", END)
    return builder.compile()
```

### 4.5 Streamlit User Interface (`app.py`)
- **Single-process execution**: `streamlit run app.py`.
- **Controls**:
  - `st.sidebar.radio` for patient list (ranked High $\rightarrow$ Low).
  - Main panel displays Patient Demographics + Triage Badge.
  - 3-column layout (`st.columns([4, 4, 3])`):
    - Col 1: Labs table with delta indicators.
    - Col 2: Drug interaction alert cards.
    - Col 3: Chronic conditions list.
  - Collapsible `st.expander` showing the Pydantic-validated JSON dictionary.

---

## 5. Local Inference Engine Contract (Ollama)

- **API Endpoint**: `http://localhost:11434/api/generate`
- **Default Model**: `llama3.2:3b`
- **Parameters**:
  - `temperature`: `0.0`
  - `format`: `"json"`
  - `timeout`: `15` seconds
- **Fallback / Mock Mode**: If Ollama is not running, the system gracefully falls back to deterministic rule extraction, guaranteeing zero demo crashes.

---

## 6. Minimal Dependencies (`requirements.txt`)

```text
langgraph>=0.2.0
langchain-community>=0.2.0
pydantic>=2.7.0
streamlit>=1.35.0
pandas>=2.0.0
pytest>=8.0.0
```

Zero heavy frontend toolchains. Zero cloud SDKs.

---

## 7. Verification Plan & Test Strategy

| Target | Test File | Success Criteria |
| :--- | :--- | :--- |
| **Synthea Parser** | `tests/test_parser.py` | Correctly extracts $\ge 1$ lab, medication, and condition from sample JSON without exceptions. |
| **KDIGO AKI Rules** | `tests/test_rules.py` | Creatinine jumping from 1.0 to 1.5 mg/dL triggers Stage 1 AKI flag. |
| **DDI Rules** | `tests/test_rules.py` | Ingesting `[lisinopril, furosemide, ibuprofen]` triggers High-Risk Triple Whammy alert. |
| **Full Graph** | `tests/test_graph.py` | StateGraph runs to `END` and returns `TriageAssessment` with non-empty fields. |
| **Streamlit App** | Terminal launch | `streamlit run app.py` starts without syntax errors or runtime exceptions. |
