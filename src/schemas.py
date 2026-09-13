"""Clinical data contracts and LangGraph state schemas."""

import operator
from typing import Annotated, Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LabAlert(BaseModel):
    """Clinical laboratory alert representing an abnormal or critical value."""

    name: str = Field(..., description="Name of the laboratory analyte")
    current_value: float = Field(..., description="Most recent lab value")
    baseline_value: Optional[float] = Field(
        None, description="Prior baseline lab value if available"
    )
    unit: str = Field(..., description="Measurement unit (e.g. mg/dL, mEq/L)")
    alert_type: str = Field(
        ...,
        description="Clinical classification (e.g. KDIGO_AKI_STAGE_2, PANIC_VALUE, ELEVATED)",
    )
    severity: str = Field(
        ..., description="Severity level: CRITICAL, HIGH, MODERATE, LOW, NORMAL"
    )
    clinical_significance: str = Field(
        ..., description="Clinical explanation and physiologic impact"
    )


class DrugInteraction(BaseModel):
    """Identified drug-drug or drug-disease contraindication or interaction."""

    drugs: List[str] = Field(..., description="List of implicated medications")
    severity: str = Field(
        ...,
        description="Severity: CONTRAINDICATED, MAJOR, MODERATE, MINOR",
    )
    mechanism: str = Field(..., description="Pharmacological interaction mechanism")
    recommendation: str = Field(
        ..., description="Actionable clinical recommendation for the physician"
    )


class ChronicCondition(BaseModel):
    """Patient chronic comorbidity."""

    code: str = Field(..., description="Diagnosis code (e.g. ICD-10 or SNOMED)")
    display: str = Field(..., description="Human-readable diagnosis name")
    status: str = Field(default="active", description="Clinical status of condition")


class TriageAssessment(BaseModel):
    """Lead coordinator unified clinical assessment."""

    triage_level: str = Field(
        ..., description="Overall risk priority: HIGH, MEDIUM, LOW"
    )
    summary: str = Field(
        ..., description="Concise multi-agent synthesized summary for the physician"
    )
    action_items: List[str] = Field(
        default_factory=list,
        description="Ranked immediate clinical interventions",
    )


from typing import TypedDict


class ClinicalGraphState(TypedDict):
    """LangGraph execution state with parallel reducers."""

    patient_id: str
    patient_name: str
    patient_age: Optional[int]
    gender: Optional[str]
    raw_labs: List[Dict[str, Any]]
    raw_medications: List[Dict[str, Any]]
    raw_conditions: List[Dict[str, Any]]

    # Annotated lists enable parallel LangGraph scatter-gather reducers
    lab_alerts: Annotated[List[LabAlert], operator.add]
    drug_interactions: Annotated[List[DrugInteraction], operator.add]
    chronic_conditions: Annotated[List[ChronicCondition], operator.add]
    triage_assessment: Optional[TriageAssessment]


class ClinicalState(BaseModel):
    """Serialized clinical state container."""

    patient_id: str
    patient_name: str
    patient_age: Optional[int] = None
    gender: Optional[str] = None
    raw_labs: List[Dict[str, Any]] = Field(default_factory=list)
    raw_medications: List[Dict[str, Any]] = Field(default_factory=list)
    raw_conditions: List[Dict[str, Any]] = Field(default_factory=list)
    lab_alerts: List[LabAlert] = Field(default_factory=list)
    drug_interactions: List[DrugInteraction] = Field(default_factory=list)
    chronic_conditions: List[ChronicCondition] = Field(default_factory=list)
    triage_assessment: Optional[TriageAssessment] = None
