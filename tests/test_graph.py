"""End-to-end integration tests for multi-agent LangGraph clinical pipeline."""

from pathlib import Path
from src.parser import parse_synthea_bundle
from src.graph import clinical_graph

DATA_DIR = Path(__file__).parent.parent / "data" / "patients"


def test_patient_01_high_risk_e2e():
    patient_file = DATA_DIR / "patient_01_high_risk.json"
    parsed_data = parse_synthea_bundle(patient_file)

    # Prepare initial state for LangGraph
    initial_state = {
        **parsed_data,
        "lab_alerts": [],
        "drug_interactions": [],
        "chronic_conditions": [],
        "triage_assessment": None,
    }

    result = clinical_graph.invoke(initial_state)

    # 1. Verify parallel agent contributions
    assert len(result["lab_alerts"]) >= 1
    aki_alert = next((a for a in result["lab_alerts"] if "KDIGO" in a.alert_type), None)
    assert aki_alert is not None
    assert aki_alert.alert_type == "KDIGO_AKI_STAGE_2"
    assert aki_alert.severity == "HIGH"

    assert len(result["drug_interactions"]) >= 1
    triple_whammy = next(
        (d for d in result["drug_interactions"] if "Triple Whammy" in d.mechanism), None
    )
    assert triple_whammy is not None
    assert triple_whammy.severity == "CONTRAINDICATED"

    assert len(result["chronic_conditions"]) == 2

    # 2. Verify coordinator synthesis
    assessment = result["triage_assessment"]
    assert assessment is not None
    assert assessment.triage_level == "HIGH"
    assert len(assessment.action_items) > 0
    assert any("NSAID" in act or "MEDICATION" in act for act in assessment.action_items)


def test_patient_02_med_risk_e2e():
    patient_file = DATA_DIR / "patient_02_med_risk.json"
    parsed_data = parse_synthea_bundle(patient_file)

    initial_state = {
        **parsed_data,
        "lab_alerts": [],
        "drug_interactions": [],
        "chronic_conditions": [],
        "triage_assessment": None,
    }

    result = clinical_graph.invoke(initial_state)

    # Verify hyperkalemia and major interaction
    assessment = result["triage_assessment"]
    assert assessment is not None
    assert assessment.triage_level == "MEDIUM"

    k_alert = next((a for a in result["lab_alerts"] if "potassium" in a.name.lower()), None)
    assert k_alert is not None
    assert k_alert.severity == "HIGH"


def test_patient_03_low_risk_e2e():
    patient_file = DATA_DIR / "patient_03_low_risk.json"
    parsed_data = parse_synthea_bundle(patient_file)

    initial_state = {
        **parsed_data,
        "lab_alerts": [],
        "drug_interactions": [],
        "chronic_conditions": [],
        "triage_assessment": None,
    }

    result = clinical_graph.invoke(initial_state)

    assessment = result["triage_assessment"]
    assert assessment is not None
    assert assessment.triage_level == "LOW"
    assert len(result["drug_interactions"]) == 0
