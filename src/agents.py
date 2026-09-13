"""Specialized clinical agents and Lead Triage Coordinator node implementations."""

import json
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.error

from src.rules import (
    evaluate_kdigo_aki,
    evaluate_lab_panic_values,
    evaluate_drug_interactions,
)
from src.schemas import (
    LabAlert,
    DrugInteraction,
    ChronicCondition,
    TriageAssessment,
)

OLLAMA_ENDPOINT = "http://localhost:11434/api/generate"
PREFERRED_MODELS = ["llama3.2:3b", "gemma3:270m"]


def query_local_ollama(
    prompt: str,
    system_prompt: str = "You are an expert clinical decision support assistant.",
    model: Optional[str] = None,
    timeout_secs: float = 8.0,
) -> Optional[str]:
    """Query local Ollama instance with zero external dependencies and graceful fallback."""
    candidate_models = [model] if model else PREFERRED_MODELS

    for cand_model in candidate_models:
        payload = {
            "model": cand_model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }
        try:
            req = urllib.request.Request(
                OLLAMA_ENDPOINT,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=timeout_secs) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result.get("response", "").strip()
        except Exception:
            continue

    return None


def lab_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Lab Specialist Agent: Detects KDIGO AKI stages, panic lab values, and out-of-range analytes."""
    raw_labs = state.get("raw_labs", [])
    alerts: List[LabAlert] = []

    # 1. Evaluate Creatinine & KDIGO AKI staging
    cr_labs = [l for l in raw_labs if "creatinine" in l.get("name", "").lower()]
    if cr_labs:
        # Labs are chronologically sorted in parser
        if len(cr_labs) >= 2:
            baseline_lab = cr_labs[0]
            current_lab = cr_labs[-1]
            baseline_val = baseline_lab.get("value")
            current_val = current_lab.get("value")
        else:
            current_lab = cr_labs[0]
            baseline_val = None
            current_val = current_lab.get("value")

        aki_eval = evaluate_kdigo_aki(baseline_val, current_val)
        if aki_eval:
            alert_type, severity, significance = aki_eval
            alerts.append(
                LabAlert(
                    name=current_lab.get("name", "Serum Creatinine"),
                    current_value=current_val,
                    baseline_value=baseline_val,
                    unit=current_lab.get("unit", "mg/dL"),
                    alert_type=alert_type,
                    severity=severity,
                    clinical_significance=significance,
                )
            )

    # 2. Evaluate other labs for Panic Values and abnormal reference ranges
    for lab in raw_labs:
        name = lab.get("name", "")
        if "creatinine" in name.lower():
            continue  # Already handled above

        val = lab.get("value", 0.0)
        unit = lab.get("unit", "")
        ref_low = lab.get("reference_low")
        ref_high = lab.get("reference_high")

        # Check critical panic thresholds first
        panic_eval = evaluate_lab_panic_values(name, val, unit)
        if panic_eval:
            alert_type, severity, significance = panic_eval
            alerts.append(
                LabAlert(
                    name=name,
                    current_value=val,
                    baseline_value=None,
                    unit=unit,
                    alert_type=alert_type,
                    severity=severity,
                    clinical_significance=significance,
                )
            )
        elif ref_high is not None and val > ref_high:
            alerts.append(
                LabAlert(
                    name=name,
                    current_value=val,
                    baseline_value=None,
                    unit=unit,
                    alert_type="ELEVATED",
                    severity="MODERATE",
                    clinical_significance=f"{name} is elevated at {val} {unit} (Reference high: {ref_high} {unit}).",
                )
            )
        elif ref_low is not None and val < ref_low:
            alerts.append(
                LabAlert(
                    name=name,
                    current_value=val,
                    baseline_value=None,
                    unit=unit,
                    alert_type="LOW",
                    severity="MODERATE",
                    clinical_significance=f"{name} is below normal at {val} {unit} (Reference low: {ref_low} {unit}).",
                )
            )

    return {"lab_alerts": alerts}


def pharma_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Pharmacology Specialist Agent: Evaluates dangerous drug-drug and drug-disease contraindications."""
    raw_meds = state.get("raw_medications", [])
    med_names = [m.get("name", "") for m in raw_meds if m.get("name")]

    # 1. Deterministic O(1) Rule Table check
    interactions = evaluate_drug_interactions(med_names)

    # 2. Drug-Disease cross-reference: If patient has acute kidney injury or chronic kidney disease
    has_renal_issue = False
    for cond in state.get("raw_conditions", []):
        text = (cond.get("display") or "").lower()
        if "kidney" in text or "renal" in text:
            has_renal_issue = True
            break

    # If NSAID is present alongside renal impairment and wasn't already caught in Triple Whammy
    if has_renal_issue and not any("Triple Whammy" in i.mechanism for i in interactions):
        for med in med_names:
            if any(nsaid in med.lower() for nsaid in ["ibuprofen", "naproxen", "meloxicam", "ketorolac"]):
                interactions.append(
                    DrugInteraction(
                        drugs=[med],
                        severity="MAJOR",
                        mechanism="NSAID inhibits renal prostaglandins, reducing renal blood flow and exacerbating preexisting renal impairment.",
                        recommendation=f"Consider discontinuing {med} in the presence of compromised renal function.",
                    )
                )
                break

    return {"drug_interactions": interactions}


def history_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Medical History Specialist Agent: Extracts chronic comorbidities and prior diagnoses."""
    raw_conditions = state.get("raw_conditions", [])
    chronic_list: List[ChronicCondition] = []

    for cond in raw_conditions:
        chronic_list.append(
            ChronicCondition(
                code=cond.get("code", "UNKNOWN"),
                display=cond.get("display", "Unspecified Condition"),
                status=cond.get("status", "active"),
            )
        )

    return {"chronic_conditions": chronic_list}


def triage_coordinator_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Lead Triage Coordinator Agent: Synthesizes cross-specialty evidence into a unified assessment."""
    lab_alerts: List[LabAlert] = state.get("lab_alerts", [])
    drug_interactions: List[DrugInteraction] = state.get("drug_interactions", [])
    chronic_conditions: List[ChronicCondition] = state.get("chronic_conditions", [])
    patient_name = state.get("patient_name", "The patient")

    # 1. Determine Composite Triage Priority
    has_critical_lab = any(a.severity == "CRITICAL" for a in lab_alerts)
    has_contraindicated_ddi = any(d.severity == "CONTRAINDICATED" for d in drug_interactions)
    has_stage2_or_3_aki = any("STAGE_2" in a.alert_type or "STAGE_3" in a.alert_type for a in lab_alerts)

    has_high_lab = any(a.severity == "HIGH" for a in lab_alerts)
    has_major_ddi = any(d.severity == "MAJOR" for d in drug_interactions)
    has_stage1_aki = any("STAGE_1" in a.alert_type for a in lab_alerts)

    if has_critical_lab or has_contraindicated_ddi or has_stage2_or_3_aki:
        triage_level = "HIGH"
    elif has_high_lab or has_major_ddi or has_stage1_aki:
        triage_level = "MEDIUM"
    else:
        triage_level = "LOW"

    # 2. Formulate Action Items
    action_items: List[str] = []

    # Add DDI recommendations
    for ddi in drug_interactions:
        if ddi.severity in ("CONTRAINDICATED", "MAJOR"):
            action_items.append(f"MEDICATION ALERT: {ddi.recommendation}")

    # Add Lab alerts
    for lab in lab_alerts:
        if lab.severity in ("CRITICAL", "HIGH"):
            if "KDIGO" in lab.alert_type:
                action_items.append(f"RENAL MONITORING: Repeat serum creatinine and BUN within 24-48h; check daily urine output.")
            elif "potassium" in lab.name.lower():
                action_items.append(f"ELECTROLYTE ALERT: Order emergent 12-lead ECG to evaluate for peaked T waves / arrhythmias.")
            elif "hemoglobin" in lab.name.lower():
                action_items.append(f"HEMATOLOGY ALERT: Type and crossmatch; evaluate for active hemorrhage.")

    if not action_items:
        action_items.append("Continue current outpatient management; routine follow-up recommended.")

    # 3. Formulate Clinician Summary (Deterministic baseline + Optional Ollama synthesis)
    summary_parts = []
    if triage_level == "HIGH":
        summary_parts.append(
            f"URGENT CLINICAL ALERT for {patient_name}: High-priority clinical intervention required."
        )
    elif triage_level == "MEDIUM":
        summary_parts.append(
            f"MODERATE RISK ASSESSMENT for {patient_name}: Close clinical monitoring recommended."
        )
    else:
        summary_parts.append(
            f"ROUTINE STABLE ASSESSMENT for {patient_name}: Normal vital findings and stable baseline."
        )

    if lab_alerts:
        alert_desc = "; ".join(a.clinical_significance for a in lab_alerts)
        summary_parts.append(f"Lab findings: {alert_desc}")

    if drug_interactions:
        ddi_desc = "; ".join(f"{', '.join(d.drugs)} ({d.severity}): {d.mechanism}" for d in drug_interactions)
        summary_parts.append(f"Pharmacological risk: {ddi_desc}")

    if chronic_conditions:
        comorbidities = ", ".join(c.display for c in chronic_conditions)
        summary_parts.append(f"Active comorbidities: {comorbidities}.")

    deterministic_summary = " ".join(summary_parts)

    # Optional local Ollama polish
    llm_prompt = f"""Summarize this clinical triage assessment for a physician in 2 concise sentences:
Patient: {patient_name}
Triage Level: {triage_level}
Findings: {deterministic_summary}
Action Items: {'; '.join(action_items)}"""

    llm_summary = query_local_ollama(llm_prompt, timeout_secs=5.0)
    final_summary = llm_summary if llm_summary and len(llm_summary) > 20 else deterministic_summary

    assessment = TriageAssessment(
        triage_level=triage_level,
        summary=final_summary,
        action_items=action_items[:4],  # Top 4 most critical actions
    )

    return {"triage_assessment": assessment}
