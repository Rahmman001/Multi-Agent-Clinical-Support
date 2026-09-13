# Deep Research: Multi-Agent Clinical Decision Support Systems (CDSS)

> **Comprehensive research report on multi-agent clinical architectures, open EHR standards (Synthea FHIR), clinical safety rules (DDI & KDIGO lab deltas), and zero-cost local execution via LangGraph + Ollama.**

---

## 1. Academic & Clinical Foundations

### 1.1 The "Monolithic Prompt" Pathology in Clinical AI
Recent clinical AI research (e.g., *Nature Digital Medicine 2023*, *Medprompt / Microsoft Research 2024*, and *AgentMD 2024*) reveals that submitting multi-page Electronic Health Records into a single LLM prompt suffers from three distinct failure modes:
1. **Context Smearing (Needle-in-a-Haystack Problem)**: Crucial micro-signals (e.g., a serum creatinine increase from 0.9 to 1.5 mg/dL over 48 hours buried across 6 pages of lab tables) are drowned out by repetitive clinical boilerplate (family history, billing codes, routine vitals).
2. **Hallucinated Cross-Referencing**: Single-turn models frequently invent hypothetical drug interactions or attribute a lab anomaly to a disease the patient does not possess.
3. **Lack of Verifiable Provenance**: Clinicians cannot trust black-box paragraphs without explicit line-item evidence citing specific test dates, exact dosages, and published clinical guidelines.

### 1.2 The Multi-Agent Advantage (Decomposition & Specialization)
By dividing clinical evaluation into domain-specialized agents:
- **Token Efficiency**: Each agent receives only the partitioned slice of data relevant to its specialty (Lab Agent receives only `Observation` lab resources; Pharma Agent receives only `MedicationRequest` entries).
- **Domain Focus**: Each agent executes a tailored prompt with domain-specific few-shot examples and strict Pydantic schemas.
- **Explainability**: The final triage card provides three discrete evidence pillars (Labs, Medications, Comorbidities) before computing the composite risk score.

---

## 2. Dataset: Synthea FHIR R4 Specification

### 2.1 What is Synthea?
[Synthea](https://synthetichealth.github.io/synthea/) is an open-source synthetic patient generator developed with the Massachusetts Department of Public Health and MITRE. It outputs 100% realistic patient records modeling the complete medical history of simulated patients from birth to present day, completely devoid of protected health information (PHI) or HIPAA liability.

### 2.2 FHIR R4 Bundle Structure for Clinical Agents
A Synthea patient export is formatted as a FHIR Bundle JSON (`resourceType: "Bundle"`). The key resources to parse for each agent:

| Agent | Target FHIR Resource | Key Fields Extracted | Example Clinical Code |
| :--- | :--- | :--- | :--- |
| **Lab Agent** | `Observation` (`category="laboratory"`) | `code.coding.display`, `valueQuantity.value`, `valueQuantity.unit`, `effectiveDateTime`, `referenceRange` | LOINC `2160-0` (Creatinine), LOINC `2823-3` (Potassium) |
| **Pharma Agent** | `MedicationRequest` | `medicationCodeableConcept.coding.display`, `dosageInstruction`, `authoredOn`, `status` | RxNorm `197361` (Amlodipine), RxNorm `314076` (Lisinopril) |
| **History Agent**| `Condition` | `code.coding.display`, `clinicalStatus`, `onsetDateTime`, `verificationStatus` | SNOMED-CT `44054006` (Type 2 Diabetes), SNOMED-CT `38341003` (Hypertension) |
| **Vitals Filter** | `Observation` (`category="vital-signs"`) | Blood Pressure (`85354-9`), Heart Rate (`8867-4`), SpO2 (`2708-6`) | Vitals snapshot for acute instability |

### 2.3 Official Synthea Sample Repositories
Pre-generated synthetic FHIR bundles can be downloaded directly from:
- **FHIR R4 Bundles**: `https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/synthea_sample_data_fhir_r4_nov2021.zip`
- **CSV Format**: `https://raw.githubusercontent.com/synthetichealth/synthea-sample-data/main/downloads/synthea_sample_data_csv_nov2021.zip`

---

## 3. Clinical Safety Rules: Lab Deltas & Drug Contraindications

To give the multi-agent system true clinical utility, the agents must be grounded in established clinical criteria:

### 3.1 Acute Kidney Injury (KDIGO Criteria for Lab Agent)
According to the **KDIGO (Kidney Disease: Improving Global Outcomes)** clinical practice guidelines:
* **Stage 1 AKI**:
  - Serum Creatinine increase by $\ge 0.3\text{ mg/dL}$ within 48 hours, OR
  - Serum Creatinine increase to $\ge 1.5\text{ to }1.9\times$ baseline within prior 7 days.
* **Stage 2 AKI**: Serum Creatinine $2.0\text{ to }2.9\times$ baseline.
* **Stage 3 AKI**: Serum Creatinine $\ge 3.0\times$ baseline or serum creatinine $\ge 4.0\text{ mg/dL}$.

### 3.2 Critical Lab Thresholds (CLIA / Hospital Panic Values)
* **Potassium ($K^+$)**:
  - Critical Hyperkalemia: $> 5.5\text{ mEq/L}$ (severe risk of cardiac arrhythmias, peaked T-waves).
  - Critical Hypokalemia: $< 3.0\text{ mEq/L}$ (risk of ventricular ectopy, muscle paralysis).
* **Hemoglobin ($Hb$)**:
  - Critical Anemia: $< 7.0\text{ g/dL}$ (standard hospital transfusion trigger).
* **White Blood Cell (WBC)**:
  - Leukocytosis: $> 12,000/\mu\text{L}$ (indicator of active systemic infection/sepsis when paired with fever).
* **Glucose**:
  - Hypoglycemia: $< 54\text{ mg/dL}$ (neuroglycopenic risk, emergency).
  - Hyperglycemia: $> 350\text{ mg/dL}$ (DKA/HHS alert).

### 3.3 High-Risk Drug-Drug Interactions (Pharma Agent)
The Pharma Agent focuses on major, documented contraindications:
1. **The "Triple Whammy" (Renal Disaster)**:
   - **Combination**: ACE Inhibitor (e.g., Lisinopril) or ARB (Losartan) + Diuretic (e.g., Hydrochlorothiazide/Furosemide) + NSAID (e.g., Ibuprofen/Naproxen).
   - **Mechanism**: NSAIDs constrict afferent arteriole; ACE inhibitors dilate efferent arteriole; Diuretics reduce intravascular volume. Result: acute glomerular perfusion collapse and severe AKI.
2. **Major Hemorrhagic Bleeding Risk**:
   - **Combination**: Anticoagulant (Warfarin / Apixaban / Rivaroxaban) + NSAID (Ibuprofen) or Antiplatelet (Aspirin / Clopidogrel).
   - **Severity**: Critical. Massive increase in upper GI bleeds.
3. **Severe Hyperkalemia Risk**:
   - **Combination**: Potassium-sparing diuretic (Spironolactone) + ACE Inhibitor (Lisinopril) + Potassium supplement.
   - **Severity**: High risk of sudden cardiac arrest.
4. **Serotonin Syndrome**:
   - **Combination**: SSRI (Sertraline / Fluoxetine) + Tramadol or Linezolid or MAOI.

---

## 4. Multi-Agent Orchestration with LangGraph

### 4.1 Scatter-Gather (Parallel Fan-out / Fan-in) Topology
Rather than running agents sequentially (which is slow and accumulates context drift), LangGraph executes the three specialized domain extractors concurrently:

```python
from typing import Annotated, List, Optional
from typing_extensions import TypedDict
import operator
from langgraph.graph import StateGraph, START, END

# Structured Findings
class LabAlert(BaseModel):
    test_name: str
    current_value: float
    unit: str
    is_abnormal: bool
    kdigo_aki_stage: Optional[int] = None
    clinical_risk: str

class DrugInteraction(BaseModel):
    drug_1: str
    drug_2: str
    severity: str  # "MAJOR", "MODERATE", "MINOR"
    clinical_mechanism: str

class ChronicCondition(BaseModel):
    condition_name: str
    onset_date: str
    active: bool

# Graph State
class ClinicalState(TypedDict):
    patient_raw_json: dict
    patient_id: str
    patient_name: str
    
    # State Reducers allow parallel agents to safely populate their lists
    lab_alerts: Annotated[List[LabAlert], operator.add]
    drug_interactions: Annotated[List[DrugInteraction], operator.add]
    chronic_conditions: Annotated[List[ChronicCondition], operator.add]
    
    # Lead Triage outputs
    triage_score: str  # "HIGH", "MEDIUM", "LOW"
    executive_summary: str
    immediate_actions: List[str]
```

### 4.2 Graph Construction
```python
builder = StateGraph(ClinicalState)

# Add domain worker nodes
builder.add_node("lab_agent", run_lab_agent)
builder.add_node("pharma_agent", run_pharma_agent)
builder.add_node("history_agent", run_history_agent)

# Add triage coordinator node
builder.add_node("triage_coordinator", run_triage_coordinator)

# Parallel Fan-out from START
builder.add_edge(START, "lab_agent")
builder.add_edge(START, "pharma_agent")
builder.add_edge(START, "history_agent")

# Fan-in to Triage Coordinator
builder.add_edge("lab_agent", "triage_coordinator")
builder.add_edge("pharma_agent", "triage_coordinator")
builder.add_edge("history_agent", "triage_coordinator")

builder.add_edge("triage_coordinator", END)

clinical_graph = builder.compile()
```

---

## 5. Zero-Cost Inference Optimization (Ollama on Mac)

### 5.1 Recommended Free Local Models
Running local SLMs via Ollama avoids all API costs and subscription fees:
1. **`llama3.2:3b`** (2.0 GB RAM):
   - Ultra-fast on Apple Silicon (~45 tokens/sec).
   - Excellent instruction-following for JSON schema extraction.
   - Recommended for Lab Agent and History Agent.
2. **`qwen2.5:7b`** or **`qwen2.5:3b`**:
   - Superior reasoning on clinical tables and mathematical comparisons (delta percentages).
   - Recommended for Lead Triage Coordinator.

### 5.2 Deterministic JSON Enforcement with Ollama
To prevent markdown fences (````json ... ````) and malformed responses:
```python
from langchain_community.llms import Ollama
from langchain_core.output_parsers import JsonOutputParser

# Using Ollama with explicit format="json"
llm = Ollama(
    model="llama3.2:3b",
    format="json",
    temperature=0.0  # Zero temperature for deterministic clinical extraction
)
```

---

## 6. Doctor Dashboard UX & Triage Standards

### 6.1 Manchester & ESI Triage Adaptation
Emergency departments categorize patients using the **Emergency Severity Index (ESI)** (Levels 1 to 5) or the **Manchester Triage System (MTS)**:
- **HIGH (Red)**: Immediate threat. Criteria: Stage 2/3 AKI delta, critical hyperkalemia ($>5.5$), or lethal drug-drug interaction (e.g., Triple Whammy with rising creatinine).
- **MEDIUM (Amber/Yellow)**: Urgent/Subacute. Criteria: Single moderate lab abnormal without acute delta, moderate drug interaction requiring monitoring, or chronic disease flare.
- **LOW (Green)**: Stable / Routine. Criteria: Normal labs, stable medication regimen, chronic conditions well-managed.

### 6.2 Streamlit Layout Pattern
- **Top Metrics Bar**: Total Patients Screened, High-Risk Count, Median Agent Processing Latency.
- **Left Sidebar**: Patient Queue ordered by Risk Severity (`🔴 HIGH` at top, followed by `🟡 MEDIUM`, then `🟢 LOW`).
- **Main View**:
  - Triage Banner with Emergency Severity Badge.
  - Three-Column Evidence Card:
    - Column 1: Lab Anomalies (with delta percentage indicator).
    - Column 2: Medication Conflicts (with contraindication mechanism).
    - Column 3: Chronic History (comorbidity context).
  - Executive Clinical Summary (3 sentences for the physician).
  - Collapsible Raw JSON Data Inspector.

---

## 7. Recommended Implementation Roadmap

1. **Phase 1: Synthea Ingestion Engine (`src/ingestion/`)**
   - Download sample Synthea FHIR R4 patients.
   - Write deterministic Python parser extracting `Observation`, `MedicationRequest`, and `Condition`.
2. **Phase 2: Domain Extractors & Pydantic Schemas (`src/agents/`)**
   - Build `LabAgent` with KDIGO AKI detection logic.
   - Build `PharmaAgent` with local drug interaction rules dictionary + LLM fallback.
   - Build `HistoryAgent` for chronic disease classification.
3. **Phase 3: LangGraph Workflow (`src/graph/`)**
   - Implement StateGraph scatter-gather pipeline.
   - Build `TriageCoordinator` computing composite risk score and summary.
4. **Phase 4: Streamlit Dashboard (`src/ui/`)**
   - Interactive local clinical dashboard on `http://localhost:8501`.
