"""Unit tests for lightweight Synthea FHIR bundle parser."""

from pathlib import Path
from src.parser import parse_synthea_bundle

DATA_DIR = Path(__file__).parent.parent / "data" / "patients"


def test_parse_patient_01_high_risk():
    patient_file = DATA_DIR / "patient_01_high_risk.json"
    assert patient_file.exists()

    data = parse_synthea_bundle(patient_file)

    assert data["patient_id"] == "patient-01"
    assert "Arthur Morales" in data["patient_name"]
    assert data["gender"] == "male"
    assert data["patient_age"] is not None and data["patient_age"] >= 60

    # Labs check
    labs = data["raw_labs"]
    assert len(labs) == 3
    creatinine_labs = [l for l in labs if "creatinine" in l["name"].lower()]
    assert len(creatinine_labs) == 2
    # Ensure sorted chronologically (baseline 1.0, current 2.4)
    assert creatinine_labs[0]["value"] == 1.0
    assert creatinine_labs[1]["value"] == 2.4

    # Medications check
    meds = data["raw_medications"]
    assert len(meds) == 3
    med_names = [m["name"].lower() for m in meds]
    assert any("lisinopril" in m for m in med_names)
    assert any("furosemide" in m for m in med_names)
    assert any("ibuprofen" in m for m in med_names)

    # Conditions check
    conds = data["raw_conditions"]
    assert len(conds) == 2
    assert any(c["code"] == "I10" for c in conds)
    assert any(c["code"] == "E11.9" for c in conds)


def test_parse_patient_02_med_risk():
    patient_file = DATA_DIR / "patient_02_med_risk.json"
    assert patient_file.exists()

    data = parse_synthea_bundle(patient_file)
    assert data["patient_id"] == "patient-02"
    assert "Elena Rostova" in data["patient_name"]
    assert data["gender"] == "female"

    labs = data["raw_labs"]
    k_lab = next((l for l in labs if "potassium" in l["name"].lower()), None)
    assert k_lab is not None
    assert k_lab["value"] == 5.4


def test_parse_patient_03_low_risk():
    patient_file = DATA_DIR / "patient_03_low_risk.json"
    assert patient_file.exists()

    data = parse_synthea_bundle(patient_file)
    assert data["patient_id"] == "patient-03"
    assert "James Chen" in data["patient_name"]

    meds = data["raw_medications"]
    assert len(meds) == 2
    med_names = [m["name"].lower() for m in meds]
    assert any("metformin" in m for m in med_names)
    assert any("atorvastatin" in m for m in med_names)
